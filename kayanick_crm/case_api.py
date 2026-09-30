import json

import frappe
from frappe import _
from frappe.utils import today

ALLOWED = {"Sales Rep", "Sales Manager", "System Manager"}


def _check_role():
    if frappe.session.user != "Administrator" and not (ALLOWED & set(frappe.get_roles())):
        frappe.throw(_("Not permitted"), frappe.PermissionError)


@frappe.whitelist()
def search_customers(text=""):
    _check_role()
    text = (text or "").strip()[:60]
    kw = dict(filters={"disabled": 0}, fields=["name", "customer_name", "territory"],
              order_by="customer_name asc", limit_page_length=100)
    if text:
        kw["or_filters"] = [["customer_name", "like", "%" + text + "%"], ["name", "like", "%" + text + "%"]]
    return frappe.get_all("Customer", **kw)


@frappe.whitelist()
def search_items(text=""):
    _check_role()
    text = (text or "").strip()[:60]
    kw = dict(filters={"disabled": 0, "is_sales_item": 1, "has_variants": 0},
              fields=["name", "item_name", "stock_uom"], order_by="item_name asc", limit_page_length=100)
    if text:
        kw["or_filters"] = [["item_name", "like", "%" + text + "%"], ["name", "like", "%" + text + "%"]]
    return frappe.get_all("Item", **kw)


@frappe.whitelist()
def get_cases():
    rows = frappe.get_list("KC Case", fields=["name", "customer_name", "case_date", "creation"],
                           order_by="creation desc", limit_page_length=30)
    names = [r.name for r in rows]
    counts = {}
    if names:
        for it in frappe.get_all("KC Case Item", filters={"parent": ["in", names], "parenttype": "KC Case"},
                                 fields=["parent", "qty"]):
            counts[it.parent] = counts.get(it.parent, 0) + 1
    for r in rows:
        r["items"] = counts.get(r.name, 0)
    return rows


def attachments(doctype, name):
    return frappe.get_all("File", filters={"attached_to_doctype": doctype, "attached_to_name": name},
                          fields=["name", "file_name", "file_url", "file_size"], order_by="creation asc")


@frappe.whitelist()
def get_case(name):
    doc = frappe.get_doc("KC Case", name)
    doc.check_permission("read")
    return {
        "name": doc.name, "customer": doc.customer, "customer_name": doc.customer_name,
        "case_date": doc.case_date, "notes": doc.notes, "sales_rep": doc.sales_rep,
        "items": [{"item_code": r.item_code, "item_name": r.item_name, "qty": r.qty, "uom": r.uom} for r in doc.items],
        "attachments": attachments("KC Case", doc.name),
    }


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
    return {"case": case.name}
