import json
from contextlib import contextmanager

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


def attachments(doctype, name):
    return frappe.get_all("File", filters={"attached_to_doctype": doctype, "attached_to_name": name},
                          fields=["name", "file_name", "file_url", "file_size"], order_by="creation asc")


@contextmanager
def _as_administrator():
    # frappe.set_user() also rewrites session.sid; restoring only the user would send the
    # browser a broken sid cookie and log the rep out, so the whole session is put back.
    session = frappe.local.session
    saved = frappe._dict(session)
    form_dict = frappe.local.form_dict
    frappe.set_user("Administrator")
    try:
        yield
    finally:
        frappe.set_user(saved.user)
        session.update(saved)
        frappe.local.form_dict = form_dict


@frappe.whitelist()
def get_case(name):
    doc = frappe.get_doc("KC Case", name)
    doc.check_permission("read")
    so_status = ""
    if doc.sales_order:
        ds = frappe.db.get_value("Sales Order", doc.sales_order, "docstatus")
        so_status = {0: "Draft", 1: "Submitted", 2: "Cancelled"}.get(ds, "Deleted")
    return {
        "name": doc.name, "customer": doc.customer, "customer_name": doc.customer_name,
        "case_date": doc.case_date, "notes": doc.notes, "sales_order": doc.sales_order,
        "so_status": so_status or "No order", "sales_rep": doc.sales_rep,
        "items": [{"item_code": r.item_code, "item_name": r.item_name, "qty": r.qty, "uom": r.uom} for r in doc.items],
        "attachments": attachments("KC Case", doc.name),
        "can_order": not doc.sales_order and bool(frappe.has_permission("KC Case", "write", doc=doc)),
    }


def _default_warehouse(item_code, company):
    wh = frappe.db.get_value("Item Default", {"parent": item_code, "company": company}, "default_warehouse")
    if not wh:
        wh = frappe.db.get_single_value("Stock Settings", "default_warehouse")
        if wh and frappe.db.get_value("Warehouse", wh, "company") != company:
            wh = None
    return wh


@frappe.whitelist(methods=["POST"])
def make_sales_order(case):
    doc = frappe.get_doc("KC Case", case)
    doc.check_permission("write")
    if doc.sales_order and frappe.db.exists("Sales Order", doc.sales_order):
        return doc.sales_order
    delivery = max(getdate(doc.case_date), getdate(today()))
    rows, missing = [], []
    for r in doc.items:
        wh = _default_warehouse(r.item_code, doc.company)
        if not wh and frappe.db.get_value("Item", r.item_code, "is_stock_item"):
            missing.append(r.item_code)
        rows.append({"item_code": r.item_code, "qty": r.qty, "delivery_date": delivery, "warehouse": wh})
    if missing:
        frappe.throw(_("No default warehouse for {0} in {1}. Please ask the office to set it.").format(
            ", ".join(missing), doc.company))
    so = frappe.get_doc({
        "doctype": "Sales Order",
        "customer": doc.customer,
        "company": doc.company,
        "transaction_date": today(),
        "delivery_date": delivery,
        "kc_case": doc.name,
        "items": rows,
    })
    so.flags.ignore_permissions = True
    user = frappe.session.user
    # ERPNext checks the session user while pricing items; the rep has no ERPNext roles,
    # so the draft is built as Administrator after the case permission check above.
    with _as_administrator():
        so.insert()
    frappe.db.set_value("Sales Order", so.name, "owner", user, update_modified=False)
    doc.db_set("sales_order", so.name)
    return so.name


@frappe.whitelist(methods=["POST"])
def create_case(payload, make_order=1):
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
    # the mobile app passes make_order=0, uploads the attachments, then calls make_sales_order,
    # because a case is read-only for the rep once its Sales Order exists
    so = make_sales_order(case.name) if frappe.utils.cint(make_order) else None
    return {"case": case.name, "sales_order": so}
