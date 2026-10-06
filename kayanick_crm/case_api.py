import json

import frappe
from frappe import _
from frappe.utils import get_fullname, get_time, getdate, now, today



def _check_role():
    from kayanick_crm.perms import is_app_user

    if not is_app_user():
        frappe.throw(_("Not permitted"), frappe.PermissionError)


CASE_FIELDS = ["name", "hospital", "doctor", "case_date", "case_time", "attended", "attended_by", "used_products", "sales_rep",
               "postponed_count", "cancelled", "creation"]


def decorate(rows):
    """Adds products, doctor title and rep name to case rows."""
    from kayanick_crm.mobile import add_doctor_titles, full_names

    products = _products([r.name for r in rows])
    add_doctor_titles("KC Case", rows)
    names = full_names([r.sales_rep for r in rows] + [r.get("attended_by") for r in rows if r.get("attended_by")])
    for r in rows:
        r["case_time"] = str(r.case_time) if r.get("case_time") else ""
        r["products"] = products.get(r.name, [])
        r["rep_name"] = names.get(r.sales_rep, r.sales_rep)
        r["attended_by_name"] = names.get(r.get("attended_by"), r.get("attended_by") or "")
    return rows


@frappe.whitelist()
def get_cases(args=None):
    from kayanick_crm.mobile import list_filters, page_args

    a, filters, or_filters = list_filters("case_date", args, "KC Case")
    if a.get("attended") == "cancelled":
        filters.append(["cancelled", "=", 1])
    elif a.get("attended") in (0, 1, "0", "1"):
        filters.append(["attended", "=", frappe.utils.cint(a.attended)])
        if not frappe.utils.cint(a.attended):
            filters.append(["cancelled", "=", 0])  # planned = not attended and not cancelled
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
    from kayanick_crm.mobile import doctors_text

    doc = frappe.get_doc("KC Case", name)
    doc.check_permission("read")
    can_edit = bool(frappe.has_permission("KC Case", "write", doc=doc))
    return {
        "name": doc.name, "hospital": doc.hospital, "doctor": doc.doctor,
        "doctors": [r.doctor for r in doc.doctors], "doctor_title": doctors_text(doc),
        "case_date": doc.case_date, "case_time": str(doc.case_time or ""), "attended": doc.attended,
        "attended_by": doc.attended_by, "attended_by_name": frappe.utils.get_fullname(doc.attended_by) if doc.attended_by else "", "notes": doc.notes, "sales_rep": doc.sales_rep,
        "rep_name": frappe.utils.get_fullname(doc.sales_rep),
        "products": [p.product for p in doc.products],
        "used_products": doc.used_products or "",
        "used_items": [{"item_code": r.item_code, "item_name": r.item_name, "qty": r.qty, "uom": r.uom}
                       for r in doc.used_items],
        "attachments": attachments("KC Case", doc.name),
        "can_delete": bool(frappe.has_permission("KC Case", "delete", doc=doc)),
        "can_edit": can_edit,
        "can_postpone": can_edit and not doc.attended and not doc.cancelled,
        "cancelled": doc.cancelled, "cancel_reason": doc.cancel_reason or "", "cancelled_on": doc.cancelled_on,
        "cancelled_by_name": get_fullname(doc.cancelled_by) if doc.cancelled_by else "",
        "postponements": [{"from_date": r.from_date, "from_time": str(r.from_time or ""), "to_date": r.to_date,
                           "to_time": str(r.to_time or ""), "reason": r.reason or "",
                           "by": get_fullname(r.postponed_by) if r.postponed_by else "", "on": r.postponed_on}
                          for r in doc.postponements],
    }


@frappe.whitelist(methods=["POST"])
def postpone_case(name, case_date, case_time, reason=None):
    """Moves a planned case to a new date/time and keeps the old one in the postponement log."""
    doc = frappe.get_doc("KC Case", name)
    doc.check_permission("write")
    if doc.attended or doc.cancelled:
        frappe.throw(_("Only a planned case can be postponed"))
    if not case_date or not case_time:
        frappe.throw(_("Choose the new date and time"))
    if getdate(case_date) < getdate(today()):
        frappe.throw(_("The new date can't be in the past"))
    if getdate(case_date) == getdate(doc.case_date) and doc.case_time and get_time(case_time) == get_time(doc.case_time):
        frappe.throw(_("Choose a different date or time"))
    doc.append("postponements", {
        "from_date": doc.case_date, "from_time": doc.case_time, "to_date": case_date, "to_time": case_time,
        "reason": (reason or "").strip(), "postponed_by": frappe.session.user, "postponed_on": now(),
    })
    doc.case_date = case_date
    doc.case_time = case_time
    doc.save()
    return {"case_date": doc.case_date, "case_time": str(doc.case_time or ""), "postponed_count": doc.postponed_count}


@frappe.whitelist(methods=["POST"])
def cancel_case(name, reason=None):
    """Cancels a planned case (kept for history, hidden from Planned / Today / reminders)."""
    doc = frappe.get_doc("KC Case", name)
    doc.check_permission("write")
    if doc.attended or doc.cancelled:
        frappe.throw(_("Only a planned case can be cancelled"))
    reason = (reason or "").strip()
    if not reason:
        frappe.throw(_("Write why the case is cancelled"))
    doc.cancelled = 1
    doc.cancelled_by = frappe.session.user
    doc.cancelled_on = now()
    doc.cancel_reason = reason
    doc.save()
    frappe.enqueue("kayanick_crm.notify._case_cancelled_to_managers", name=doc.name, enqueue_after_commit=True)
    return "ok"


@frappe.whitelist(methods=["POST"])
def reopen_case(name):
    """Puts a cancelled case back to Planned."""
    doc = frappe.get_doc("KC Case", name)
    doc.check_permission("write")
    if not doc.cancelled:
        frappe.throw(_("This case is not cancelled"))
    doc.cancelled = 0
    doc.save()
    return "ok"


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


def _attendee(user):
    from kayanick_crm.perms import sales_users

    user = user or frappe.session.user
    if user != frappe.session.user and user not in sales_users():
        frappe.throw(_("{0} is not in the Sales Person tree").format(user))
    return user


@frappe.whitelist()
def search_attendees(text=""):
    """Everyone in the Sales Person tree can be picked as the one who attended a case."""
    from kayanick_crm.perms import sales_users

    _check_role()
    users = sales_users()
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
    if doc.cancelled:
        frappe.throw(_("This case is cancelled. Reopen it first"))
    doc.attended = 1 if frappe.utils.cint(attended) else 0
    _apply_used(doc, used_products, used_items, attended_by)
    doc.save()
    return doc.attended


@frappe.whitelist(methods=["POST"])
def create_case(payload):
    _check_role()
    from kayanick_crm.mobile import doctor_list

    data = json.loads(payload) if isinstance(payload, str) else dict(payload or {})
    doctors = doctor_list(data)
    if not doctors:
        frappe.throw(_("Choose at least one doctor"))
    case = frappe.get_doc({
        "doctype": "KC Case",
        "hospital": data.get("hospital"),
        "doctor": doctors[0],
        "doctors": [{"doctor": d} for d in doctors],
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
