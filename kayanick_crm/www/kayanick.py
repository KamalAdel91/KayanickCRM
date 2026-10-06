import frappe

no_cache = 1
BASE = "/KayanickCRM"


def _redirect(location):
    frappe.local.flags.redirect_location = location
    redirect = frappe.Redirect()
    redirect.http_status_code = 302
    raise redirect


def get_context(context):
    path = frappe.local.request.path
    if path == "/kayanick" or path.startswith("/kayanick/"):
        _redirect(BASE + path[len("/kayanick"):])
    if frappe.session.user == "Guest":
        _redirect("/login?redirect-to=" + BASE)
    from kayanick_crm.perms import is_app_user

    if not is_app_user():
        frappe.throw("You do not have permission to access Kayanick CRM", frappe.PermissionError)
    context.csrf_token = frappe.sessions.get_csrf_token()
    context.push_relay = frappe.conf.get("push_relay_server_url") or ""
    context.push_enabled = 1 if frappe.db.get_single_value("Push Notification Settings", "enable_push_notification_relay") else 0
    frappe.db.commit()  # nosemgrep
    return context
