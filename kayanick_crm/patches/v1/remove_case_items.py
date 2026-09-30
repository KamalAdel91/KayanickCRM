import frappe


def execute():
    # cases now use KC Product (like visits) instead of ERPNext items
    if frappe.db.exists("DocType", "KC Case Item"):
        frappe.delete_doc("DocType", "KC Case Item", force=1, ignore_permissions=True)
