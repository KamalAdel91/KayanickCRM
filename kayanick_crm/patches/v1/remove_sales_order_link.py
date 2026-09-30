import frappe


def execute():
    # cases are no longer linked to Sales Orders
    if frappe.db.exists("Custom Field", "Sales Order-kc_case"):
        frappe.delete_doc("Custom Field", "Sales Order-kc_case", ignore_permissions=True)
