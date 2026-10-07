import frappe
from frappe import _
from frappe.utils import get_first_day, getdate, today


def execute(filters=None):
    columns = [
        {"label": _("Employee"), "fieldname": "employee", "fieldtype": "Link", "options": "Employee", "width": 130},
        {"label": _("Name"), "fieldname": "employee_name", "fieldtype": "Data", "width": 170},
        {"label": _("Visits This Month"), "fieldname": "visits_month", "fieldtype": "Int", "width": 130},
        {"label": _("Total Visits"), "fieldname": "visits", "fieldtype": "Int", "width": 100},
        {"label": _("Positive"), "fieldname": "positive", "fieldtype": "Int", "width": 90},
        {"label": _("Orders Expected"), "fieldname": "orders_expected", "fieldtype": "Int", "width": 120},
        {"label": _("Cases This Month"), "fieldname": "cases_month", "fieldtype": "Int", "width": 130},
        {"label": _("Total Cases"), "fieldname": "cases", "fieldtype": "Int", "width": 100},
        {"label": _("Last Activity"), "fieldname": "last_activity", "fieldtype": "Date", "width": 110},
    ]
    month = getdate(get_first_day(today()))
    out = {}

    def row(employee, name):
        return out.setdefault(employee, {"employee": employee, "employee_name": name, "visits_month": 0, "visits": 0,
                                         "positive": 0, "orders_expected": 0, "cases_month": 0, "cases": 0,
                                         "last_activity": None})

    def seen(r, day):
        if day and (not r["last_activity"] or getdate(day) > getdate(r["last_activity"])):
            r["last_activity"] = day

    # visits and attended cases this user can see (a rep: his own; a manager: his team)
    for v in frappe.get_list("KC Visit", fields=["employee", "employee_name", "visit_date", "visit_outcome", "order_expected"],
                             limit_page_length=0):
        if not v.employee:
            continue
        r = row(v.employee, v.employee_name)
        r["visits"] += 1
        r["visits_month"] += 1 if getdate(v.visit_date) >= month else 0
        r["positive"] += 1 if v.visit_outcome == "Positive" else 0
        r["orders_expected"] += 1 if v.order_expected else 0
        seen(r, v.visit_date)
    for c in frappe.get_list("KC Case", filters={"status": "Attended"}, fields=["employee", "employee_name", "case_date"],
                             limit_page_length=0):
        if not c.employee:
            continue
        r = row(c.employee, c.employee_name)
        r["cases"] += 1
        r["cases_month"] += 1 if getdate(c.case_date) >= month else 0
        seen(r, c.case_date)
    data = sorted(out.values(), key=lambda r: (-(r["visits_month"] + r["cases_month"]), -(r["visits"] + r["cases"])))
    return columns, data
