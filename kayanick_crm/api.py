"""Number cards on the KAYANICK Sales dashboard (each counts only what the user can see)."""
import frappe
from frappe.utils import get_first_day, get_last_day, today


def _card(doctype, filters):
    n = len(frappe.get_list(doctype, filters=filters, pluck="name", limit_page_length=100000))
    return {"value": n, "fieldtype": "Int"}


def _month_visits(extra=None):
    return _card("KC Visit", [["visit_date", ">=", get_first_day(today())]] + (extra or []))


@frappe.whitelist()
def visits_this_month(filters=None):
    return _month_visits()


@frappe.whitelist()
def positive_this_month(filters=None):
    return _month_visits([["visit_outcome", "=", "Positive"]])


@frappe.whitelist()
def orders_this_month(filters=None):
    return _month_visits([["order_expected", "=", 1]])


@frappe.whitelist()
def cases_attended_this_month(filters=None):
    return _card("KC Case", [["status", "=", "Attended"], ["case_date", ">=", get_first_day(today())],
                             ["case_date", "<=", get_last_day(today())]])


@frappe.whitelist()
def planned_cases(filters=None):
    return _card("KC Case", [["status", "=", "Planned"], ["case_date", ">=", today()]])


@frappe.whitelist()
def overdue_cases(filters=None):
    return _card("KC Case", [["status", "=", "Planned"], ["case_date", "<", today()]])
