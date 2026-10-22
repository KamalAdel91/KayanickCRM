"""Notifications: in-app (Notification Log, also shows in the Desk bell) + phone push through
Frappe Cloud's push relay when "Enable Push Notification Relay" is on.

Who gets what. "Sees" is the app's one rule (perms.py). Whoever caused the event is left out, and a user who turned
notifications off (Notification Settings) gets none.

    Positive visit / order expected   a visit is logged               everyone who sees the visit
    New case (planned or attended)    a case is added                 everyone who sees the case
    Case cancelled                    a planned case is cancelled     everyone who sees the case
    Payment received / cancelled      a Payment Entry from a          everyone who sees the customer
                                      customer is submitted / cancelled
    Invoice overdue                   daily at 8:00                   everyone who sees the customer
    Good morning                      daily at 8:00                   each rep: their follow-ups and planned cases
    Overdue debt this week            Sundays at 8:00                 each app user: the customers they see
"""
from urllib.parse import quote

import frappe
from frappe.utils import add_days, get_fullname, get_url, getdate, today

from kayanick_crm.perms import app_users

PUSH_PROJECT = "hrms"  # the project Frappe HR uses on the relay (custom names are rejected)
APP_ROUTE = "/KayanickCRM"
ROUTES = {"KC Visit": "/visits/", "KC Case": "/case/", "Customer": "/debts/"}
REMINDER_PREFIX = "Good morning! You have"
DEBT_DIGEST_PREFIX = "Overdue debt:"


def _ours(user, **extra):
    """Only this app's notifications: linked to a visit, case or customer, or the morning / weekly digests."""
    filters = {"for_user": user, **extra}
    or_filters = [["document_type", "in", list(ROUTES)], ["subject", "like", REMINDER_PREFIX + "%"],
                  ["subject", "like", DEBT_DIGEST_PREFIX + "%"]]
    return filters, or_filters


def unread(user):
    filters, or_filters = _ours(user, read=0)
    return len(frappe.get_all("Notification Log", filters=filters, or_filters=or_filters, pluck="name"))


def _route(doctype, name, subject=""):
    """Where a notification opens in the app."""
    if doctype in ROUTES and name:
        return ROUTES[doctype] + quote(name, safe="")
    if (subject or "").startswith(DEBT_DIGEST_PREFIX):
        return "/debts"
    return ""


def notify(user, subject, doctype=None, name=None, from_user=None, title=None, body=None):
    """subject: the in-app line; title/body: what the phone shows (defaults to the app name + subject)."""
    from frappe.desk.doctype.notification_settings.notification_settings import is_notifications_enabled

    if not user or user in ("Guest", "Administrator") or not is_notifications_enabled(user):
        return
    frappe.get_doc({
        "doctype": "Notification Log", "for_user": user, "type": "Alert", "subject": subject,
        "document_type": doctype, "document_name": name, "from_user": from_user,
    }).insert(ignore_permissions=True)
    _push(user, body or subject, APP_ROUTE + (_route(doctype, name, subject) or "/"), title=title, tag=name)


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


def readers(doctype, name):
    """App users who can open this record under Frappe's permissions (roles, User Permissions, shares)."""
    doc = frappe.get_doc(doctype, name)
    return {u for u in app_users() if frappe.has_permission(doctype, "read", doc=doc, user=u)}


def debt_viewers():
    """{user: the customers whose debt the user sees in the app, None for all} (debt_api.visible_customers)."""
    from kayanick_crm.debt_api import visible_customers

    return {u: visible_customers(u)[0] for u in app_users()}


def customer_readers(customer, viewers=None):
    """App users who see this customer's debt in the app."""
    viewers = debt_viewers() if viewers is None else viewers
    return {u for u, customers in viewers.items() if customers is None or customer in customers}


# ---- document events (queued, so saving stays fast) ----

def visit_created(doc, method=None):
    if doc.visit_outcome == "Positive" or doc.order_expected:
        frappe.enqueue("kayanick_crm.notify._visit_to_readers", name=doc.name, enqueue_after_commit=True)


def case_created(doc, method=None):
    frappe.enqueue("kayanick_crm.notify._case_to_readers", name=doc.name, enqueue_after_commit=True)


def _visit_to_readers(name):
    from kayanick_crm.mobile import doctors_text
    from kayanick_crm.perms import user_of

    v = frappe.get_doc("KC Visit", name)
    what = "an order expected" if v.order_expected else "a positive visit"
    rep = v.employee_name or get_fullname(v.owner)
    doctor = doctors_text(v)
    msg = "{0} logged {1} at {2}".format(rep, what, v.hospital)
    title = "🛒 Order expected" if v.order_expected else "🟢 Positive visit"
    body = " · ".join(x for x in (rep, v.hospital, doctor) if x)
    by = user_of(v.employee) or v.owner
    for u in readers("KC Visit", v.name) - {by, v.owner}:
        notify(u, msg, "KC Visit", v.name, by, title=title, body=body)


def _hm(t):
    """'14:30:00' or timedelta -> '2:30 PM'"""
    from frappe.utils import format_time
    try:
        return format_time(t, "h:mm a")
    except Exception:
        return str(t)[:5]


def _case_to_readers(name):
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
    for u in readers("KC Case", c.name) - {c.owner}:
        notify(u, msg, "KC Case", c.name, c.owner, title=title, body=body)


def _case_cancelled_to_readers(name):
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
    for u in readers("KC Case", c.name) - {row.done_by}:
        notify(u, msg, "KC Case", c.name, row.done_by, title=title, body=body)


# the previous release queued jobs under these names: kept so a job waiting during a deploy still runs
_visit_to_managers = _visit_to_readers
_case_to_managers = _case_to_readers
_case_cancelled_to_managers = _case_cancelled_to_readers


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


# ---- customer debt ----

WEEKLY_DEBT_DAY = 6  # Sunday (Monday is 0), the first day of the work week


def _money(amount, currency):
    return "{0:,.0f} {1}".format(amount or 0, currency).strip()


def payment_received(doc, method=None):
    if doc.party_type == "Customer" and doc.payment_type == "Receive":
        frappe.enqueue("kayanick_crm.notify._payment_to_readers", name=doc.name, enqueue_after_commit=True)


def payment_cancelled(doc, method=None):
    if doc.party_type == "Customer" and doc.payment_type == "Receive":
        frappe.enqueue("kayanick_crm.notify._payment_to_readers", name=doc.name, cancelled=True,
                       enqueue_after_commit=True)


def _payment_to_readers(name, cancelled=False):
    """Everyone who sees the customer's debt in the app hears about a payment received, or cancelled."""
    pe = frappe.get_doc("Payment Entry", name)
    customer = pe.party_name or pe.party
    amount = _money(pe.paid_amount, pe.paid_from_account_currency)
    what = "Payment cancelled" if cancelled else "Payment received"
    title = "↩️ Payment cancelled" if cancelled else "💵 Payment received"
    for u in customer_readers(pe.party) - {pe.modified_by}:
        notify(u, "{0} from {1}: {2}".format(what, customer, amount), "Customer", pe.party, pe.modified_by,
               title=title, body="{0} · {1}".format(customer, amount))


_payment_to_rep = _payment_to_readers  # the previous release's name, for jobs queued during a deploy

LAST_DEBT_ALERTS = "kayanick_crm_debt_alerts_last_run"  # DefaultValue: the day debt_alerts last ran
CATCH_UP_DAYS = 7  # after the scheduler was off, invoices that fell overdue up to this many days ago are announced


def debt_alerts():
    """Daily: invoices that became overdue since the last run (one line per customer), to everyone who sees the
    customer. Sundays: every app user gets the overdue debt of the customers they see."""
    from kayanick_crm.debt_api import currency, open_invoices

    day = getdate(today())
    last = frappe.db.get_default(LAST_DEBT_ALERTS)
    # an invoice falls overdue the day after its due date: since the last run (on a normal day, yesterday's)
    since = max(getdate(last), getdate(add_days(day, -CATCH_UP_DAYS))) if last else getdate(add_days(day, -1))
    cur = currency()
    viewers = debt_viewers()
    newly = {}  # customer -> invoices that fell overdue since the last run
    for inv in open_invoices():
        if inv.outstanding_amount > 0 and inv.due_date and since <= getdate(inv.due_date) < day:
            newly.setdefault(inv.customer, []).append(inv)
    for customer, invoices in newly.items():
        name = invoices[0].customer_name or customer
        amount = _money(sum(i.outstanding_amount for i in invoices), cur)
        what = invoices[0].name if len(invoices) == 1 else "{0} invoices".format(len(invoices))
        verb = "is" if len(invoices) == 1 else "are"
        for u in customer_readers(customer, viewers):
            notify(u, "{0} of {1} {2} now overdue: {3}".format(what, name, verb, amount), "Customer", customer,
                   title="⏰ Payment overdue", body="{0} · {1} · {2}".format(name, what, amount))
    frappe.db.set_default(LAST_DEBT_ALERTS, str(day))

    if day.weekday() == WEEKLY_DEBT_DAY:
        weekly_debt_digest()


def weekly_debt_digest():
    from kayanick_crm.debt_api import currency, customer_reps, debts

    cur = currency()
    reps = customer_reps()
    for user, customers in debt_viewers().items():
        rows, totals, _aging = debts(customers, reps)
        if not totals["overdue"]:
            continue
        oldest = max(r.max_days for r in rows)
        n = totals["overdue_customers"]
        line = "{0} from {1} customer{2}, the oldest {3} days late".format(
            _money(totals["overdue"], cur), n, "" if n == 1 else "s", oldest)
        notify(user, DEBT_DIGEST_PREFIX + " " + line + ".", title="💰 Overdue debt this week", body=line)


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
        r["subject"] = frappe.utils.strip_html(r.subject or "")
        r["route"] = _route(r.document_type, r.document_name, r.subject)
    return rows


@frappe.whitelist()
def unread_count():
    return unread(frappe.session.user)


@frappe.whitelist(methods=["POST"])
def mark_read(name: str | None = None):
    filters, or_filters = _ours(frappe.session.user, read=0)
    if name:
        filters["name"] = name
    for n in frappe.get_all("Notification Log", filters=filters, or_filters=or_filters, pluck="name"):
        frappe.db.set_value("Notification Log", n, "read", 1, update_modified=False)
    return "ok"
