"""Attended cases with used products, for KC Accounts to invoice. To mark a case invoiced, type the invoice number on
the case (KCCase.set_invoice_status)."""
import frappe
from frappe import _
from frappe.utils import flt


def execute(filters=None):
    f = frappe._dict(filters or {})
    conditions = [["invoice_status", "in", ["To Invoice", "Invoiced"] if f.status == "All" else [f.status or "To Invoice"]]]
    if f.invoice_type:
        conditions.append(["invoice_type", "=", f.invoice_type])
    if f.from_date:
        conditions.append(["case_date", ">=", f.from_date])
    if f.to_date:
        conditions.append(["case_date", "<=", f.to_date])
    cases = frappe.get_list("KC Case", filters=conditions, order_by="case_date asc, creation asc", limit_page_length=0,
                            fields=["name", "case_date", "hospital", "employee_name", "invoice_type", "total_amount",
                                    "invoice_status", "invoice_number", "invoiced_by"])
    items = {}
    for r in frappe.get_all("KC Case Used Item", filters={"parenttype": "KC Case",
                                                          "parent": ["in", [c.name for c in cases] or [""]]},
                            fields=["parent", "item_name", "item_code", "qty", "uom", "rate"], order_by="idx asc"):
        items.setdefault(r.parent, []).append("{0} × {1:g} @ {2:,.2f}".format(r.item_name or r.item_code, flt(r.qty),
                                                                               flt(r.rate)))
    customers = dict(frappe.get_all("KC Hospital", filters={"name": ["in", list({c.hospital for c in cases}) or [""]]},
                                    fields=["name", "customer"], as_list=True))
    for c in cases:
        c["customer"] = customers.get(c.hospital)
        c["items"] = "; ".join(items.get(c.name, []))
    return columns(), cases


def columns():
    return [
        {"label": _("Case"), "fieldname": "name", "fieldtype": "Link", "options": "KC Case", "width": 140},
        {"label": _("Date"), "fieldname": "case_date", "fieldtype": "Date", "width": 100},
        {"label": _("Hospital"), "fieldname": "hospital", "fieldtype": "Link", "options": "KC Hospital", "width": 180},
        {"label": _("Customer"), "fieldname": "customer", "fieldtype": "Link", "options": "Customer", "width": 160},
        {"label": _("Rep"), "fieldname": "employee_name", "fieldtype": "Data", "width": 140},
        {"label": _("Invoice Type"), "fieldname": "invoice_type", "fieldtype": "Data", "width": 100},
        {"label": _("Used Items"), "fieldname": "items", "fieldtype": "Data", "width": 320},
        {"label": _("Total"), "fieldname": "total_amount", "fieldtype": "Currency", "width": 120},
        {"label": _("Status"), "fieldname": "invoice_status", "fieldtype": "Data", "width": 100},
        {"label": _("Invoice Number"), "fieldname": "invoice_number", "fieldtype": "Data", "width": 130},
        {"label": _("Invoiced By"), "fieldname": "invoiced_by", "fieldtype": "Link", "options": "User", "width": 160},
    ]
