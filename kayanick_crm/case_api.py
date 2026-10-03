import json

import frappe
from frappe import _
from frappe.utils import today

ALLOWED = {"Sales Rep", "Sales Manager", "System Manager"}


def _check_role():
    if frappe.session.user != "Administrator" and not (ALLOWED & set(frappe.get_roles())):
        frappe.throw(_("Not permitted"), frappe.PermissionError)


CASE_FIELDS = ["name", "hospital", "doctor", "case_date", "case_time", "attended", "attended_by", "used_products", "sales_rep", "creation"]


def decorate(rows):
    """Adds products, doctor title and rep name to case rows."""
    from kayanick_crm.mobile import _doctor_titles, full_names

    products = _products([r.name for r in rows])
    titles = _doctor_titles([r.doctor for r in rows])
    names = full_names([r.sales_rep for r in rows] + [r.get("attended_by") for r in rows if r.get("attended_by")])
    for r in rows:
        r["case_time"] = str(r.case_time) if r.get("case_time") else ""
        r["products"] = products.get(r.name, [])
        r["doctor_title"] = titles.get(r.doctor, r.doctor)
        r["rep_name"] = names.get(r.sales_rep, r.sales_rep)
        r["attended_by_name"] = names.get(r.get("attended_by"), r.get("attended_by") or "")
    return rows


@frappe.whitelist()
def get_cases(args=None):
    from kayanick_crm.mobile import list_filters, page_args

    a, filters, or_filters = list_filters("case_date", args)
    if a.get("attended") in (0, 1, "0", "1"):
        filters.append(["attended", "=", frappe.utils.cint(a.attended)])
    start, limit = page_args(a)
    # planned: nearest first; attended / all: newest first
    planned = str(a.get("attended")) == "0"
    order = "case_date asc, case_time asc, creation asc" if planned else "case_date desc, case_time desc, creation desc"
    rows = frappe.get_list("KC Case", filters=filters, or_filters=or_filters, fields=CASE_FIELDS,
                           order_by=order, limit_start=start, limit_page_length=limit)
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
        "case_date": doc.case_date, "case_time": str(doc.case_time or ""), "attended": doc.attended,
        "attended_by": doc.attended_by, "attended_by_name": frappe.utils.get_fullname(doc.attended_by) if doc.attended_by else "", "notes": doc.notes, "sales_rep": doc.sales_rep,
        "rep_name": frappe.utils.get_fullname(doc.sales_rep),
        "products": [p.product for p in doc.products],
        "used_products": doc.used_products or "",
        "used_items": [{"item_code": r.item_code, "item_name": r.item_name, "qty": r.qty, "uom": r.uom}
                       for r in doc.used_items],
        "attachments": attachments("KC Case", doc.name),
        "can_delete": bool(frappe.has_permission("KC Case", "delete", doc=doc)),
        "can_edit": bool(frappe.has_permission("KC Case", "write", doc=doc)),
    }


def _used_rows(items):
    if isinstance(items, str):
        items = json.loads(items or "[]")
    return [{"item_code": r.get("item_code"), "qty": frappe.utils.flt(r.get("qty"))}
            for r in (items or []) if r.get("item_code")]


def _apply_used(doc, used_products, used_items, attended_by=None):
    if not doc.attended:
        return
    doc.attended_by = _attendee(attended_by)
    if used_products not in ("Yes", "No"):
        frappe.throw(_("Did you use products in this case? Choose Yes or No"))
    doc.used_products = used_products
    doc.set("used_items", _used_rows(used_items) if used_products == "Yes" else [])


ATTENDEE_ROLES = ("Sales Rep", "Sales Manager")


def _attendee(user):
    user = user or frappe.session.user
    if user != frappe.session.user and not frappe.db.exists(
        "Has Role", {"parent": user, "parenttype": "User", "role": ["in", ATTENDEE_ROLES]}
    ):
        frappe.throw(_("{0} is not a sales user").format(user))
    return user


@frappe.whitelist()
def search_attendees(text=""):
    """Sales reps and managers who can be picked as the one who attended a case."""
    _check_role()
    users = set(frappe.get_all("Has Role", filters={"parenttype": "User", "role": ["in", ATTENDEE_ROLES]},
                               pluck="parent"))
    users.add(frappe.session.user)
    text = (text or "").strip()[:60]
    kw = dict(filters={"name": ["in", list(users)], "enabled": 1}, fields=["name", "full_name"],
              order_by="full_name asc", limit_page_length=100)
    if text:
        kw["or_filters"] = [["full_name", "like", "%" + text + "%"], ["name", "like", "%" + text + "%"]]
    return frappe.get_all("User", **kw)


@frappe.whitelist()
def search_items(text=""):
    """ERPNext items for the 'used products' picker (info only, no stock effect)."""
    _check_role()
    text = (text or "").strip()[:60]
    kw = dict(filters={"disabled": 0, "has_variants": 0}, fields=["name", "item_name", "stock_uom"],
              order_by="item_name asc", limit_page_length=50)
    if text:
        kw["or_filters"] = [["item_name", "like", "%" + text + "%"], ["name", "like", "%" + text + "%"]]
    return frappe.get_all("Item", **kw)


@frappe.whitelist(methods=["POST"])
def set_attended(name, attended=1, used_products=None, used_items=None, attended_by=None):
    doc = frappe.get_doc("KC Case", name)
    doc.check_permission("write")
    doc.attended = 1 if frappe.utils.cint(attended) else 0
    _apply_used(doc, used_products, used_items, attended_by)
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
        "case_time": data.get("case_time"),
        "attended": 1 if data.get("attended") else 0,
        "sales_rep": frappe.session.user,
        "notes": data.get("notes"),
        "products": [{"product": p} for p in (data.get("products") or []) if p],
    })
    _apply_used(case, data.get("used_products"), data.get("used_items"), data.get("attended_by"))
    case.insert()
    return {"case": case.name}
