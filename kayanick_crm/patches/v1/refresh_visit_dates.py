import frappe


def execute():
    """Rebuild Last visit / Next visit on every hospital and doctor from the visits that exist now."""
    from kayanick_crm.kayanick_crm.doctype.kc_visit.kc_visit import refresh_visit_dates

    refresh_visit_dates(frappe.get_all("KC Hospital", pluck="name"), frappe.get_all("KC Doctor", pluck="name"))
