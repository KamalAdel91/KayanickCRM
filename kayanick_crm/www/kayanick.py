import frappe

no_cache = 1
ALLOWED = {"Sales Rep", "Sales Manager", "System Manager"}


def get_context(context):
    if frappe.session.user == "Guest":
        frappe.local.flags.redirect_location = "/login?redirect-to=/kayanick"
        redirect = frappe.Redirect()
        redirect.http_status_code = 302
        raise redirect
    if not (ALLOWED & set(frappe.get_roles())):
        frappe.throw("You do not have permission to access Kayanick CRM", frappe.PermissionError)
    context.csrf_token = frappe.sessions.get_csrf_token()
    frappe.db.commit()  # nosemgrep
    return context
