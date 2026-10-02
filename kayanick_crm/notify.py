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


def managers_of(user):
    """Sales Managers above the user in the Sales Person tree."""
    employees = frappe.get_all("Employee", filters={"user_id": user}, pluck="name")
    if not employees:
        return set()
    out = set()
    for node in frappe.get_all("Sales Person", filters={"employee": ["in", employees]}, fields=["lft", "rgt"]):
        above = frappe.get_all("Sales Person", filters={"lft": ["<", node.lft], "rgt": [">", node.rgt],
                                                        "enabled": 1, "employee": ["is", "set"]}, pluck="employee")
        if above:
            users = frappe.get_all("Employee", filters={"name": ["in", above]}, pluck="user_id")
            out |= {u for u in users if u and "Sales Manager" in frappe.get_roles(u)}
    out.discard(user)
    return out


# ---- document events (queued, so saving stays fast) ----

def visit_created(doc, method=None):
    if doc.visit_outcome == "Positive" or doc.order_expected:
        frappe.enqueue("kayanick_crm.notify._visit_to_managers", name=doc.name, enqueue_after_commit=True)


def case_created(doc, method=None):
    frappe.enqueue("kayanick_crm.notify._case_to_managers", name=doc.name, enqueue_after_commit=True)


def _visit_to_managers(name):
    v = frappe.get_doc("KC Visit", name)
    what = "an order expected" if v.order_expected else "a positive visit"
    rep = get_fullname(v.sales_rep)
    doctor = frappe.db.get_value("KC Doctor", v.doctor, "doctor_name") if v.doctor else ""
    msg = "{0} logged {1} at {2}".format(rep, what, v.hospital)
    title = "🛒 Order expected" if v.order_expected else "🟢 Positive visit"
    body = " · ".join(x for x in (rep, v.hospital, doctor) if x)
    for m in managers_of(v.sales_rep):
        notify(m, msg, "KC Visit", v.name, v.sales_rep, title=title, body=body)


def _hm(t):
    """'14:30:00' or timedelta -> '2:30 PM'"""
    from frappe.utils import format_time
    try:
        return format_time(t, "h:mm a")
    except Exception:
        return str(t)[:5]


def _case_to_managers(name):
    c = frappe.get_doc("KC Case", name)
    at = (" " + _hm(c.case_time)) if c.case_time else ""
    when = "" if c.attended else " for " + getdate(c.case_date).strftime("%d %b") + at
    doctor = frappe.db.get_value("KC Doctor", c.doctor, "doctor_name") if c.doctor else ""
    rep = get_fullname(c.sales_rep)
    msg = "{0} added a case{1}: {2}{3}".format(rep, when, c.hospital, " / " + doctor if doctor else "")
    title = "📅 Planned case · " + getdate(c.case_date).strftime("%d %b") + at if not c.attended else "🩺 New case"
    body = " · ".join(x for x in (rep, c.hospital, doctor) if x)
    for m in managers_of(c.sales_rep):
        notify(m, msg, "KC Case", c.name, c.sales_rep, title=title, body=body)


# ---- daily reminder (scheduler) ----

def morning_reminder():
    day = getdate(today())
    reps = set(frappe.get_all("KC Visit", filters={"next_visit_date": ["<=", day]}, pluck="sales_rep", distinct=True))
    reps |= set(frappe.get_all("KC Case", filters={"attended": 0, "case_date": ["<=", day]}, pluck="sales_rep", distinct=True))
    for rep in reps:
        if not rep or not frappe.db.get_value("User", rep, "enabled"):
            continue
        follow_ups = _due_follow_ups(rep, day)
        today_cases = frappe.db.count("KC Case", {"sales_rep": rep, "attended": 0, "case_date": day})
        overdue_cases = frappe.db.count("KC Case", {"sales_rep": rep, "attended": 0, "case_date": ["<", day]})
        parts = []
        if follow_ups:
            parts.append("{0} follow-up{1}".format(follow_ups, "" if follow_ups == 1 else "s"))
        if today_cases:
            parts.append("{0} case{1} today".format(today_cases, "" if today_cases == 1 else "s"))
        if overdue_cases:
            parts.append("{0} overdue case{1}".format(overdue_cases, "" if overdue_cases == 1 else "s"))
        if parts:
            notify(rep, REMINDER_PREFIX + " " + ", ".join(parts) + ".",
                   title="☀️ Good morning", body="Today: " + ", ".join(parts))


def _due_follow_ups(rep, day):
    # latest visit per hospital + doctor decides the follow-up (same rule as the Today screen)
    seen, due = set(), 0
    for v in frappe.get_all("KC Visit", filters={"sales_rep": rep}, fields=["hospital", "doctor", "next_visit_date"],
                            order_by="visit_date desc, creation desc", limit_page_length=500):
        key = (v.hospital, v.doctor or "")
        if key in seen:
            continue
        seen.add(key)
        if v.next_visit_date and getdate(v.next_visit_date) <= day:
            due += 1
    return due


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
