import json

import frappe
from frappe import _
from frappe.utils import getdate, today

ALLOWED = {"Sales Rep", "Sales Manager", "System Manager"}


def _check_role():
    if frappe.session.user != "Administrator" and not (ALLOWED & set(frappe.get_roles())):
        frappe.throw(_("Not permitted"), frappe.PermissionError)


def default_company():
    company = (frappe.defaults.get_user_default("Company")
               or frappe.defaults.get_global_default("company")
               or frappe.db.get_value("Company", {}, "name"))
    if not company:
        frappe.throw(_("Set a default company first"))
    return company


@frappe.whitelist()
def search_customers(text=""):
    _check_role()
    text = (text or "").strip()[:60]
    kw = dict(filters={"disabled": 0}, fields=["name", "customer_name", "territory"],
              order_by="customer_name asc", limit_page_length=30)
    if text:
        kw["or_filters"] = [["customer_name", "like", "%" + text + "%"], ["name", "like", "%" + text + "%"]]
    return frappe.get_all("Customer", **kw)


@frappe.whitelist()
def search_items(text=""):
    _check_role()
    text = (text or "").strip()[:60]
    kw = dict(filters={"disabled": 0, "is_sales_item": 1, "has_variants": 0},
              fields=["name", "item_name", "stock_uom"], order_by="item_name asc", limit_page_length=30)
    if text:
        kw["or_filters"] = [["item_name", "like", "%" + text + "%"], ["name", "like", "%" + text + "%"]]
    return frappe.get_all("Item", **kw)


@frappe.whitelist()
def get_cases():
    rows = frappe.get_list("KC Case", fields=["name", "customer_name", "case_date", "sales_order", "creation"],
                           order_by="creation desc", limit_page_length=30)
    names = [r.name for r in rows]
    counts = {}
    if names:
        for it in frappe.get_all("KC Case Item", filters={"parent": ["in", names], "parenttype": "KC Case"},
                                 fields=["parent", "qty"]):
            counts[it.parent] = counts.get(it.parent, 0) + 1
    orders = [r.sales_order for r in rows if r.sales_order]
    status = {}
    if orders:
        for so in frappe.get_all("Sales Order", filters={"name": ["in", orders]}, fields=["name", "docstatus"]):
            status[so.name] = {0: "Draft", 1: "Submitted", 2: "Cancelled"}[so.docstatus]
    for r in rows:
        r["items"] = counts.get(r.name, 0)
        r["so_status"] = status.get(r.sales_order, "No order" if not r.sales_order else "Deleted")
    return rows


@frappe.whitelist(methods=["POST"])
def make_sales_order(case):
    doc = frappe.get_doc("KC Case", case)
    doc.check_permission("write")
    if doc.sales_order and frappe.db.exists("Sales Order", doc.sales_order):
        return doc.sales_order
    delivery = max(getdate(doc.case_date), getdate(today()))
    so = frappe.get_doc({
        "doctype": "Sales Order",
        "customer": doc.customer,
        "company": doc.company,
        "transaction_date": today(),
        "delivery_date": delivery,
        "kc_case": doc.name,
        "items": [{"item_code": r.item_code, "qty": r.qty, "delivery_date": delivery} for r in doc.items],
    })
    so.flags.ignore_permissions = True
    so.insert()
    doc.db_set("sales_order", so.name)
    return so.name


@frappe.whitelist(methods=["POST"])
def create_case(payload):
    _check_role()
    data = json.loads(payload) if isinstance(payload, str) else dict(payload or {})
    items = [i for i in (data.get("items") or []) if i.get("item_code") and float(i.get("qty") or 0) > 0]
    case = frappe.get_doc({
        "doctype": "KC Case",
        "customer": data.get("customer"),
        "case_date": data.get("case_date") or today(),
        "sales_rep": frappe.session.user,
        "notes": data.get("notes"),
        "items": [{"item_code": i["item_code"], "qty": float(i["qty"])} for i in items],
    })
    case.insert()
    so = make_sales_order(case.name)
    return {"case": case.name, "sales_order": so}
