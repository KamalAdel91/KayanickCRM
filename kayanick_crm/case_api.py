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
def get_cases():
    rows = frappe.get_list("KC Case", fields=["name", "customer_name", "case_date", "attended", "creation"],
                           order_by="creation desc", limit_page_length=30)
    products = _products([r.name for r in rows])
    for r in rows:
        r["products"] = products.get(r.name, [])
    return rows


def _products(names):
    out = {}
    if names:
        for p in frappe.get_all("KC Case Product", filters={"parent": ["in", names], "parenttype": "KC Case"},
                                fields=["parent", "product"], order_by="idx asc"):
            out.setdefault(p.parent, []).append(p.product)
    return out


def attachments(doctype, name):
    return frappe.get_all("File", filters={"attached_to_doctype": doctype, "attached_to_name": name},
                          fields=["name", "file_name", "file_url", "file_size"], order_by="creation asc")


@frappe.whitelist()
def get_case(name):
    doc = frappe.get_doc("KC Case", name)
    doc.check_permission("read")
    return {
        "name": doc.name, "customer": doc.customer, "customer_name": doc.customer_name,
        "case_date": doc.case_date, "attended": doc.attended, "notes": doc.notes, "sales_rep": doc.sales_rep,
        "products": [p.product for p in doc.products],
        "attachments": attachments("KC Case", doc.name),
        "can_delete": bool(frappe.has_permission("KC Case", "delete", doc=doc)),
        "can_edit": bool(frappe.has_permission("KC Case", "write", doc=doc)),
    }


@frappe.whitelist(methods=["POST"])
def set_attended(name, attended=1):
    doc = frappe.get_doc("KC Case", name)
    doc.check_permission("write")
    doc.attended = 1 if frappe.utils.cint(attended) else 0
    doc.save()
    return doc.attended


@frappe.whitelist(methods=["POST"])
def create_case(payload):
    _check_role()
    data = json.loads(payload) if isinstance(payload, str) else dict(payload or {})
    case = frappe.get_doc({
        "doctype": "KC Case",
        "customer": data.get("customer"),
        "case_date": data.get("case_date") or today(),
        "attended": 1 if data.get("attended") else 0,
        "sales_rep": frappe.session.user,
        "notes": data.get("notes"),
        "products": [{"product": p} for p in (data.get("products") or []) if p],
    })
    case.insert()
    return {"case": case.name}
