"""Role settings for Kayanick CRM, edited from the KC Settings page in Desk.

Every permission rule in the app reads its roles from here instead of hard-coded lists.
Until KC Settings is saved for the first time, DEFAULTS (the old hard-coded behaviour) apply.
"""
import frappe

CACHE_KEY = "kc_settings_roles"

ROLE_FIELDS = ("app_roles", "admin_roles", "password_reset_roles", "manager_roles", "attendee_roles",
               "case_viewer_roles", "visit_viewer_roles")

DEFAULTS = {
    "app_roles": ["Sales Rep", "Sales Manager", "System Manager"],
    "admin_roles": ["System Manager"],
    "password_reset_roles": ["System Manager"],
    "manager_roles": ["Sales Manager"],
    "attendee_roles": ["Sales Rep", "Sales Manager"],
    "case_viewer_roles": [],
    "visit_viewer_roles": [],
    "planned_cases_open": 1,
}


def _load():
    saved = frappe.db.sql("select count(*) from `tabSingles` where doctype = 'KC Settings'")[0][0]
    if not saved:
        return dict(DEFAULTS)
    doc = frappe.get_single("KC Settings")
    out = {f: [r.role for r in doc.get(f) or [] if r.role] for f in ROLE_FIELDS}
    out["planned_cases_open"] = frappe.utils.cint(doc.planned_cases_open)
    return out


def get_settings():
    s = getattr(frappe.local, "kc_settings", None)
    if s is None:
        s = frappe.cache.get_value(CACHE_KEY)
        if s is None:
            s = _load()
            frappe.cache.set_value(CACHE_KEY, s)
        frappe.local.kc_settings = s
    return s


def clear_cache():
    frappe.cache.delete_value(CACHE_KEY)
    frappe.local.kc_settings = None
    frappe.local.kc_visible_reps = None


def roles(field):
    return set(get_settings().get(field) or [])


def has_role(field, user=None):
    """True if the user has any of the roles listed in that KC Settings field (Administrator always does)."""
    user = user or frappe.session.user
    if user == "Administrator":
        return True
    return bool(roles(field) & set(frappe.get_roles(user)))


def is_admin(user=None):
    return has_role("admin_roles", user)


def is_app_user(user=None):
    return has_role("app_roles", user) or is_admin(user)


def planned_cases_open():
    return bool(get_settings().get("planned_cases_open"))
