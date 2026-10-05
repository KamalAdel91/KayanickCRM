import frappe

from kayanick_crm.settings import DEFAULTS, ROLE_FIELDS, clear_cache


def execute():
    """Fill KC Settings with the roles the app used before they became configurable."""
    if frappe.db.sql("select count(*) from `tabSingles` where doctype = 'KC Settings'")[0][0]:
        return
    doc = frappe.get_single("KC Settings")
    for field in ROLE_FIELDS:
        doc.set(field, [{"role": r} for r in DEFAULTS[field] if frappe.db.exists("Role", r)])
    doc.planned_cases_open = DEFAULTS["planned_cases_open"]
    doc.flags.ignore_permissions = True
    doc.save()
    clear_cache()
