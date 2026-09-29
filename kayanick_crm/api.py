import frappe
from frappe.utils import get_first_day, today


def _month_visits(extra=None):
    filters = [["visit_date", ">=", get_first_day(today())]] + (extra or [])
    n = len(frappe.get_list("KC Visit", filters=filters, pluck="name", limit_page_length=100000))
    return {"value": n, "fieldtype": "Int"}


@frappe.whitelist()
def visits_this_month(filters=None):
    return _month_visits()


@frappe.whitelist()
def positive_this_month(filters=None):
    return _month_visits([["visit_outcome", "=", "Positive"]])


@frappe.whitelist()
def orders_this_month(filters=None):
    return _month_visits([["order_expected", "=", 1]])
