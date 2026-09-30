import frappe
from frappe.utils import today


def execute():
    # cases created before the Attended flag existed were already done
    frappe.db.sql("update `tabKC Case` set attended = 1 where case_date <= %s", today())
