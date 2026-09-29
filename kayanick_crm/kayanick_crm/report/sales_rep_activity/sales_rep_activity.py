import frappe
from frappe import _
from frappe.utils import get_first_day, today

from kayanick_crm.perms import visible_reps


def execute(filters=None):
    columns = [
        {"label": _("Sales Rep"), "fieldname": "sales_rep", "fieldtype": "Link", "options": "User", "width": 220},
        {"label": _("Name"), "fieldname": "full_name", "fieldtype": "Data", "width": 160},
        {"label": _("This Month"), "fieldname": "this_month", "fieldtype": "Int", "width": 110},
        {"label": _("Total Visits"), "fieldname": "total_visits", "fieldtype": "Int", "width": 110},
        {"label": _("Positive"), "fieldname": "positive", "fieldtype": "Int", "width": 90},
        {"label": _("Orders Expected"), "fieldname": "orders_expected", "fieldtype": "Int", "width": 130},
        {"label": _("Cases"), "fieldname": "cases", "fieldtype": "Int", "width": 90},
        {"label": _("Last Visit"), "fieldname": "last_visit", "fieldtype": "Date", "width": 110},
    ]
    reps = set(frappe.get_all("Has Role", filters={"role": "Sales Rep", "parenttype": "User"}, pluck="parent"))
    reps = {u for u in reps if frappe.db.get_value("User", u, "enabled")}
    allowed = visible_reps()
    if allowed is not None:
        reps &= allowed
    month = get_first_day(today())
    data = []
    for u in sorted(reps):
        v = frappe.db.sql(
            """select count(*) total,
                      ifnull(sum(visit_date >= %(m)s), 0) this_month,
                      ifnull(sum(visit_outcome = 'Positive'), 0) positive,
                      ifnull(sum(order_expected = 1), 0) orders,
                      max(visit_date) last_visit
               from `tabKC Visit` where sales_rep = %(u)s""", {"u": u, "m": month}, as_dict=True)[0]
        data.append({
            "sales_rep": u, "full_name": frappe.utils.get_fullname(u), "this_month": v.this_month,
            "total_visits": v.total, "positive": v.positive, "orders_expected": v.orders,
            "cases": frappe.db.count("KC Case", {"sales_rep": u}), "last_visit": v.last_visit,
        })
    data.sort(key=lambda r: (-r["this_month"], -r["total_visits"]))
    return columns, data
