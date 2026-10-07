"""Notifications: in-app (Notification Log, also shows in the Desk bell) + phone push through
Frappe Cloud's push relay when "Enable Push Notification Relay" is on."""
import frappe
from frappe.utils import get_fullname, get_url, getdate, today

PUSH_PROJECT = "hrms"  # the project Frappe HR uses on the relay (custom names are rejected)
APP_ROUTE = "/KayanickCRM"
ROUTES = {"KC Visit": "/visits/", "KC Case": "/case/"}
REMINDER_PREFIX = "Good morning! You have"


def _ours(user, **extra):
    """Only this app's notifications: linked to a visit/case, or the daily reminder."""
    filters = {"for_user": user, **extra}
    or_filters = [["document_type", "in", list(ROUTES)], ["subject", "like", REMINDER_PREFIX + "%"]]
    return filters, or_filters


def unread(user):
    filters, or_filters = _ours(user, read=0)
    return len(frappe.get_all("Notification Log", filters=filters, or_filters=or_filters, pluck="name"))


def notify(user, subject, doctype=None, name=None, from_user=None, title=None, body=None):
    """subject: the in-app line; title/body: what the phone shows (defaults to the app name + subject)."""
    if not user or user in ("Guest", "Administrator"):
        return
    frappe.get_doc({
        "doctype": "Notification Log", "for_user": user, "type": "Alert", "subject": subject,
        "document_type": doctype, "document_name": name, "from_user": from_user,
    }).insert(ignore_permissions=True)
    _push(user, body or subject, APP_ROUTE + (ROUTES.get(doctype, "/") + name if doctype and name else ""),
          title=title, tag=name)


def _push(user, body, route, title=None, tag=None):
    """Returns the relay's answer ({"success": .., "message": ..}); failures go to the Error Log."""
    try:
        from frappe.push_notification import PushNotification

        push = PushNotification(PUSH_PROJECT)
        if not push.is_enabled():
            return {"success": False, "message": "Push Notification Relay is disabled"}
        # same call as send_notification_to_user, but keeps the relay's message for diagnosis
        res = push._send_post_request("notification_relay.api.send_notification.user", {
            "user_id": user, "title": title or "Kayanick CRM", "body": frappe.utils.strip_html(body)[:1000],
            "data": frappe.as_json({"click_action": get_url(route), "title": title or "Kayanick CRM",
                                    "body": frappe.utils.strip_html(body)[:1000], "tag": tag or ""}),
        })
        if not res.get("success"):
            frappe.log_error(title="Kayanick push notification failed", message=frappe.as_json(res))
        return res
    except Exception:
        frappe.log_error(title="Kayanick push notification failed")
        return {"success": False, "message": frappe.get_traceback().splitlines()[-1]}


@frappe.whitelist(methods=["POST"])
def test_push():
    """Sends a test push to the current user and returns what the relay said."""
    return _push(frappe.session.user, "Push is working", APP_ROUTE + "/notifications", title="🔔 Test notification")


def managers_of_employee(employee):
    """Users of everyone above this employee in Reports To (his manager, the manager's manager, ...)."""
    if not employee:
        return set()
    node = frappe.db.get_value("Employee", employee, ["lft", "rgt", "user_id"], as_dict=True)
    if not node or not node.lft:
        return set()
    users = frappe.get_all("Employee", filters={"lft": ["<", node.lft], "rgt": [">", node.rgt], "status": "Active",
                                                "user_id": ["is", "set"]}, pluck="user_id")
    out = {u for u in users if u}
    out.discard(node.user_id)
    return out


def managers_of(user):
    from kayanick_crm.perms import employee_of

    out = managers_of_employee(employee_of(user))
    out.discard(user)
    return out


# ---- document events (queued, so saving stays fast) ----

def visit_created(doc, method=None):
    if doc.visit_outcome == "Positive" or doc.order_expected:
        frappe.enqueue("kayanick_crm.notify._visit_to_managers", name=doc.name, enqueue_after_commit=True)


def case_created(doc, method=None):
    frappe.enqueue("kayanick_crm.notify._case_to_managers", name=doc.name, enqueue_after_commit=True)


def _visit_to_managers(name):
    from kayanick_crm.mobile import doctors_text
    from kayanick_crm.perms import user_of

    v = frappe.get_doc("KC Visit", name)
    what = "an order expected" if v.order_expected else "a positive visit"
    rep = v.employee_name or get_fullname(v.owner)
    doctor = doctors_text(v)
    msg = "{0} logged {1} at {2}".format(rep, what, v.hospital)
    title = "🛒 Order expected" if v.order_expected else "🟢 Positive visit"
    body = " · ".join(x for x in (rep, v.hospital, doctor) if x)
    for m in managers_of_employee(v.employee):
        notify(m, msg, "KC Visit", v.name, user_of(v.employee) or v.owner, title=title, body=body)


def _hm(t):
    """'14:30:00' or timedelta -> '2:30 PM'"""
    from frappe.utils import format_time
    try:
        return format_time(t, "h:mm a")
    except Exception:
        return str(t)[:5]


def _case_to_managers(name):
    from kayanick_crm.mobile import doctors_text

    c = frappe.get_doc("KC Case", name)
    attended = c.status == "Attended"
    at = (" " + _hm(c.case_time)) if c.case_time else ""
    when = "" if attended else " for " + getdate(c.case_date).strftime("%d %b") + at
    doctor = doctors_text(c)
    rep = get_fullname(c.owner)
    msg = "{0} added a case{1}: {2}{3}".format(rep, when, c.hospital, " / " + doctor if doctor else "")
    title = "🩺 New case" if attended else "📅 Planned case · " + getdate(c.case_date).strftime("%d %b") + at
    body = " · ".join(x for x in (rep, c.hospital, doctor) if x)
    for m in managers_of(c.owner):
        notify(m, msg, "KC Case", c.name, c.owner, title=title, body=body)


def _case_cancelled_to_managers(name):
    from kayanick_crm.mobile import doctors_text

    c = frappe.get_doc("KC Case", name)
    rows = [r for r in c.log if r.action == "Cancelled"]
    if not rows:
        return
    row = rows[-1]
    by = get_fullname(row.done_by)
    doctor = doctors_text(c)
    msg = "{0} cancelled a case: {1}{2}".format(by, c.hospital, " / " + doctor if doctor else "")
    title = "❌ Case cancelled · " + getdate(c.case_date).strftime("%d %b")
    body = " · ".join(x for x in (by, c.hospital, row.reason) if x)
    for m in (managers_of(c.owner) | {c.owner}) - {row.done_by}:
        notify(m, msg, "KC Case", c.name, row.done_by, title=title, body=body)


# ---- daily reminder (scheduler) ----

def morning_reminder():
    """Each rep: his follow-ups due (same rule as the Today screen) and the planned cases he created that are
    due today or overdue."""
    from kayanick_crm.mobile import open_follow_ups, recent_visits

    day = getdate(today())
    by_employee = {}
    for v in recent_visits(["name", "hospital", "next_visit_date", "employee"], as_user=False):
        if v.employee:
            by_employee.setdefault(v.employee, []).append(v)
    users = dict(frappe.get_all("Employee", filters={"name": ["in", list(by_employee) or [""]]},
                                fields=["name", "user_id"], as_list=True))
    follow_ups = {}
    for employee, visits in by_employee.items():
        n = sum(1 for v, _d in open_follow_ups(visits) if v.next_visit_date and getdate(v.next_visit_date) <= day)
        if n and users.get(employee):
            follow_ups[users[employee]] = follow_ups.get(users[employee], 0) + n
    today_cases, overdue_cases = {}, {}
    for c in frappe.get_all("KC Case", filters={"status": "Planned", "case_date": ["<=", day]},
                            fields=["owner", "case_date"], limit_page_length=0):
        bucket = today_cases if getdate(c.case_date) == day else overdue_cases
        bucket[c.owner] = bucket.get(c.owner, 0) + 1

    for rep in set(follow_ups) | set(today_cases) | set(overdue_cases):
        if not rep or rep in ("Administrator", "Guest") or not frappe.db.get_value("User", rep, "enabled"):
            continue
        parts = []
        n = follow_ups.get(rep)
        if n:
            parts.append("{0} follow-up{1}".format(n, "" if n == 1 else "s"))
        n = today_cases.get(rep)
        if n:
            parts.append("{0} case{1} today".format(n, "" if n == 1 else "s"))
        n = overdue_cases.get(rep)
        if n:
            parts.append("{0} overdue case{1}".format(n, "" if n == 1 else "s"))
        if parts:
            notify(rep, REMINDER_PREFIX + " " + ", ".join(parts) + ".",
                   title="☀️ Good morning", body="Today: " + ", ".join(parts))


# ---- mobile API ----

@frappe.whitelist()
def get_push_config():
    """Firebase web config + VAPID key from the relay, fetched server-side (no browser CORS issues)."""
    cached = frappe.cache.get_value("kc_push_config")
    if cached:
        return cached
    import requests

    relay = (frappe.conf.get("push_relay_server_url") or "").rstrip("/")
    if not relay:
        frappe.throw("Push relay is not configured on this site")
    try:
        r = requests.get(relay + "/api/method/notification_relay.api.get_config",
                         params={"project_name": PUSH_PROJECT}, timeout=15)
    except Exception as e:
        frappe.throw("Push relay is not reachable: {0}".format(e))
    if not r.ok:
        frappe.throw("Push relay {0} returned {1} for project '{2}'".format(relay, r.status_code, PUSH_PROJECT))
    j = r.json()
    body = j.get("message") or j
    config = body.get("config") or {}
    out = {"config": config, "vapid": body.get("vapid_public_key") or config.get("vapid_public_key")}
    if not out["vapid"]:
        frappe.throw("Push relay did not return a VAPID key")
    frappe.cache.set_value("kc_push_config", out, expires_in_sec=86400)
    return out


@frappe.whitelist()
def get_notifications():
    filters, or_filters = _ours(frappe.session.user)
    rows = frappe.get_all("Notification Log", filters=filters, or_filters=or_filters,
                          fields=["name", "subject", "document_type", "document_name", "read", "creation", "from_user"],
                          order_by="creation desc", limit_page_length=50)
    for r in rows:
        r["route"] = ROUTES.get(r.document_type, "/") + r.document_name if r.document_type in ROUTES and r.document_name else ""
        r["subject"] = frappe.utils.strip_html(r.subject or "")
    return rows


@frappe.whitelist()
def unread_count():
    return unread(frappe.session.user)


@frappe.whitelist(methods=["POST"])
def mark_read(name=None):
    filters, or_filters = _ours(frappe.session.user, read=0)
    if name:
        filters["name"] = name
    for n in frappe.get_all("Notification Log", filters=filters, or_filters=or_filters, pluck="name"):
        frappe.db.set_value("Notification Log", n, "read", 1, update_modified=False)
    return "ok"
