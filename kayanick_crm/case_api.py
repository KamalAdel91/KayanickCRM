import json

import frappe
from frappe import _
from frappe.utils import today

ALLOWED = {"Sales Rep", "Sales Manager", "System Manager"}


def _check_role():
    if frappe.session.user != "Administrator" and not (ALLOWED & set(frappe.get_roles())):
        frappe.throw(_("Not permitted"), frappe.PermissionError)


CASE_FIELDS = ["name", "hospital", "doctor", "case_date", "attended", "sales_rep", "creation"]


def decorate(rows):
    """Adds products, doctor title and rep name to case rows."""
    from kayanick_crm.mobile import _doctor_titles, full_names

    products = _products([r.name for r in rows])
    titles = _doctor_titles([r.doctor for r in rows])
    names = full_names([r.sales_rep for r in rows])
    for r in rows:
        r["products"] = products.get(r.name, [])
        r["doctor_title"] = titles.get(r.doctor, r.doctor)
        r["rep_name"] = names.get(r.sales_rep, r.sales_rep)
    return rows


@frappe.whitelist()
def get_cases(args=None):
    from kayanick_crm.mobile import list_filters, page_args

    a, filters, or_filters = list_filters("case_date", args)
    if a.get("attended") in (0, 1, "0", "1"):
        filters.append(["attended", "=", frappe.utils.cint(a.attended)])
    start, limit = page_args(a)
    rows = frappe.get_list("KC Case", filters=filters, or_filters=or_filters, fields=CASE_FIELDS,
                           order_by="case_date desc, creation desc", limit_start=start, limit_page_length=limit)
    return decorate(rows)


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
        "name": doc.name, "hospital": doc.hospital, "doctor": doc.doctor,
        "doctor_title": frappe.db.get_value("KC Doctor", doc.doctor, "doctor_name") if doc.doctor else "",
        "case_date": doc.case_date, "attended": doc.attended, "notes": doc.notes, "sales_rep": doc.sales_rep,
        "rep_name": frappe.utils.get_fullname(doc.sales_rep),
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
        "hospital": data.get("hospital"),
        "doctor": data.get("doctor"),
        "case_date": data.get("case_date") or today(),
        "attended": 1 if data.get("attended") else 0,
        "sales_rep": frappe.session.user,
        "notes": data.get("notes"),
        "products": [{"product": p} for p in (data.get("products") or []) if p],
    })
    case.insert()
    return {"case": case.name}
