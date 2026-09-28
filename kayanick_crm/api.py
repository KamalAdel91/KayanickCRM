import frappe
from frappe.utils import add_days, today

CLOSED = ["Completed", "Cancelled"]


def _count(filters):
    return len(frappe.get_list("KC Task", filters=filters, pluck="name", limit_page_length=100000))


@frappe.whitelist()
def overdue_tasks():
    n = _count([["status", "not in", CLOSED], ["due_date", "<", today()]])
    return {"value": n, "fieldtype": "Int"}


@frappe.whitelist()
def tasks_due_next_7_days():
    n = _count([
        ["status", "not in", CLOSED],
        ["due_date", "between", [today(), add_days(today(), 7)]],
    ])
    return {"value": n, "fieldtype": "Int"}
