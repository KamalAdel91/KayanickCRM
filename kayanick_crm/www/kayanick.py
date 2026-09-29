import frappe

no_cache = 1
BASE = "/KayanickCRM"
ALLOWED = {"Sales Rep", "Sales Manager", "System Manager"}


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
    if not (ALLOWED & set(frappe.get_roles())):
        frappe.throw("You do not have permission to access Kayanick CRM", frappe.PermissionError)
    context.csrf_token = frappe.sessions.get_csrf_token()
    frappe.db.commit()  # nosemgrep
    return context
