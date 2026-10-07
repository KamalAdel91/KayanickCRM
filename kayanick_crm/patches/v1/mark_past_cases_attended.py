import frappe
from frappe.utils import today


def execute():
    if not frappe.db.has_column("KC Case", "attended"):  # replaced by `status` (v2)
        return
    # cases created before the Attended flag existed were already done
    frappe.db.sql("update `tabKC Case` set attended = 1 where case_date <= %s", today())
