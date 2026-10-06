import frappe


def execute():
    """Planned / cancelled cases carry no Sales Person, so every user sees them (as before KC Settings was removed)."""
    frappe.db.sql("update `tabKC Case` set sales_person = null where attended = 0")
