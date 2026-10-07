import json

import frappe
from frappe import _
from frappe.utils import cint, get_fullname, get_time, getdate, now, today

from kayanick_crm.perms import field_users, require_employee, user_of


def _check_role():
    from kayanick_crm.perms import is_app_user

    if not is_app_user():
        frappe.throw(_("Not permitted"), frappe.PermissionError)


CASE_FIELDS = ["name", "hospital", "case_date", "case_time", "status", "employee", "employee_name", "used_products",
               "owner", "creation"]
STATUS_FILTER = {"0": "Planned", "1": "Attended", "cancelled": "Cancelled"}  # the app's tabs


def decorate(rows):
    """Adds products, doctors, status flags and names to case rows.
    rep_name is whoever created (planned) the case; attended_by_name whoever attended it."""
    from kayanick_crm.mobile import add_doctor_titles, full_names

    names = [r.name for r in rows]
    products = _products(names)
    postponed = _postponed_counts(names)
    add_doctor_titles("KC Case", rows)
    creators = full_names([r.get("owner") for r in rows])
    for r in rows:
        attended = r.get("status") == "Attended"
        r["case_time"] = str(r.case_time) if r.get("case_time") else ""
        r["products"] = products.get(r.name, [])
        r["attended"] = 1 if attended else 0
        r["cancelled"] = 1 if r.get("status") == "Cancelled" else 0
        r["sales_rep"] = r.get("owner")
        r["rep_name"] = creators.get(r.get("owner"), r.get("owner") or "")
        r["attended_by_name"] = (r.get("employee_name") or r.get("employee") or "") if attended else ""
        r["postponed_count"] = postponed.get(r.name, 0)
    return rows


@frappe.whitelist()
def get_cases(args=None):
    from kayanick_crm.mobile import list_filters, page_args

    a, filters, or_filters = list_filters("case_date", args, "KC Case")
    status = STATUS_FILTER.get(str(a.get("attended")))
    if status:
        filters.append(["status", "=", status])
    start, limit = page_args(a)
    # planned: nearest first; attended / all: newest first
    order = "case_date asc, case_time asc, creation asc" if status == "Planned" else "case_date desc, case_time desc, creation desc"
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


def _postponed_counts(names):
    out = {}
    if names:
        for p in frappe.get_all("KC Case Log", filters={"parent": ["in", names], "parenttype": "KC Case", "action": "Postponed"},
                                pluck="parent"):
            out[p] = out.get(p, 0) + 1
    return out


def attachments(doctype, name):
    return frappe.get_all("File", filters={"attached_to_doctype": doctype, "attached_to_name": name},
                          fields=["name", "file_name", "file_url", "file_size"], order_by="creation asc")


def _attach_files(doctype, name, files):
    """Attaches files the user uploaded before the record existed. Uploading afterwards isn't always possible:
    a case attended by someone else belongs to that person, and its creator can only read it."""
    if isinstance(files, str):
        files = json.loads(files or "[]")
    for f in files or []:
        row = frappe.db.get_value("File", f, ["owner", "attached_to_name"], as_dict=True)
        if row and row.owner == frappe.session.user and not row.attached_to_name:
            frappe.db.set_value("File", f, {"attached_to_doctype": doctype, "attached_to_name": name,
                                            "folder": "Home/Attachments"}, update_modified=False)


@frappe.whitelist()
def get_case(name):
    from kayanick_crm.mobile import doctors_text

    doc = frappe.get_doc("KC Case", name)
    doc.check_permission("read")
    can_edit = bool(frappe.has_permission("KC Case", "write", doc=doc))
    attended = doc.status == "Attended"
    cancelled = [r for r in doc.log if r.action == "Cancelled"]
    cancel = cancelled[-1] if doc.status == "Cancelled" and cancelled else None
    return {
        "name": doc.name, "hospital": doc.hospital, "status": doc.status,
        "doctors": [r.doctor for r in doc.doctors], "doctor_title": doctors_text(doc),
        "case_date": doc.case_date, "case_time": str(doc.case_time or ""),
        "attended": 1 if attended else 0, "cancelled": 1 if doc.status == "Cancelled" else 0,
        "employee": doc.employee if attended else None,
        "attended_by": user_of(doc.employee) if attended else None,
        "attended_by_name": (doc.employee_name or doc.employee or "") if attended else "",
        "notes": doc.notes, "sales_rep": doc.owner, "rep_name": get_fullname(doc.owner),
        "products": [p.product for p in doc.products],
        "used_products": doc.used_products or "",
        "used_items": [{"item_code": r.item_code, "item_name": r.item_name, "qty": r.qty, "uom": r.uom}
                       for r in doc.used_items],
        "attachments": attachments("KC Case", doc.name),
        "can_delete": bool(frappe.has_permission("KC Case", "delete", doc=doc)),
        "can_edit": can_edit,
        "can_postpone": can_edit and doc.status == "Planned",
        "cancel_reason": cancel.reason or "" if cancel else "",
        "cancelled_on": cancel.done_on if cancel else None,
        "cancelled_by_name": get_fullname(cancel.done_by) if cancel and cancel.done_by else "",
        "postponements": [{"from_date": r.from_date, "from_time": str(r.from_time or ""), "to_date": r.to_date,
                           "to_time": str(r.to_time or ""), "reason": r.reason or "",
                           "by": get_fullname(r.done_by) if r.done_by else "", "on": r.done_on}
                          for r in doc.log if r.action == "Postponed"],
    }


def _log(doc, action, reason=None, **extra):
    doc.append("log", {"action": action, "reason": (reason or "").strip(), "done_by": frappe.session.user,
                       "done_on": now(), **extra})


@frappe.whitelist(methods=["POST"])
def postpone_case(name, case_date, case_time, reason=None):
    """Moves a planned case to a new date/time and keeps the old one in the history."""
    doc = frappe.get_doc("KC Case", name)
    doc.check_permission("write")
    if doc.status != "Planned":
        frappe.throw(_("Only a planned case can be postponed"))
    if not case_date or not case_time:
        frappe.throw(_("Choose the new date and time"))
    if getdate(case_date) < getdate(today()):
        frappe.throw(_("The new date can't be in the past"))
    if getdate(case_date) == getdate(doc.case_date) and doc.case_time and get_time(case_time) == get_time(doc.case_time):
        frappe.throw(_("Choose a different date or time"))
    _log(doc, "Postponed", reason, from_date=doc.case_date, from_time=doc.case_time, to_date=case_date, to_time=case_time)
    doc.case_date = case_date
    doc.case_time = case_time
    doc.save()
    return {"case_date": doc.case_date, "case_time": str(doc.case_time or ""),
            "postponed_count": sum(1 for r in doc.log if r.action == "Postponed")}


@frappe.whitelist(methods=["POST"])
def cancel_case(name, reason=None):
    """Cancels a planned case (kept for history, hidden from Planned / Today / reminders)."""
    doc = frappe.get_doc("KC Case", name)
    doc.check_permission("write")
    if doc.status != "Planned":
        frappe.throw(_("Only a planned case can be cancelled"))
    if not (reason or "").strip():
        frappe.throw(_("Write why the case is cancelled"))
    _log(doc, "Cancelled", reason)
    doc.status = "Cancelled"
    doc.save()
    frappe.enqueue("kayanick_crm.notify._case_cancelled_to_managers", name=doc.name, enqueue_after_commit=True)
    return "ok"


@frappe.whitelist(methods=["POST"])
def reopen_case(name):
    """Puts a cancelled case back to Planned."""
    doc = frappe.get_doc("KC Case", name)
    doc.check_permission("write")
    if doc.status != "Cancelled":
        frappe.throw(_("This case is not cancelled"))
    _log(doc, "Reopened")
    doc.status = "Planned"
    doc.save()
    return "ok"


def _used_rows(items):
    if isinstance(items, str):
        items = json.loads(items or "[]")
    return [{"item_code": r.get("item_code"), "qty": frappe.utils.flt(r.get("qty"))}
            for r in (items or []) if r.get("item_code")]


def _apply_used(doc, used_products, used_items, attended_by=None):
    """Who attended + the used products, for a case being saved as attended."""
    doc.employee = _attendee(attended_by)
    if used_products not in ("Yes", "No"):
        frappe.throw(_("Did you use products in this case? Choose Yes or No"))
    doc.used_products = used_products
    doc.set("used_items", _used_rows(used_items) if used_products == "Yes" else [])


def _attendee(user):
    """The Employee of whoever attended: the current user, or a rep / manager he picked."""
    me = frappe.session.user
    if not user or user == me:
        return require_employee(me)
    employee = field_users().get(user)
    if not employee:
        frappe.throw(_("{0} can't be picked: he needs the KC Rep or KC Manager role and an active Employee").format(user))
    return employee


@frappe.whitelist()
def search_attendees(text=""):
    """Reps and managers (KC Rep / KC Manager with an active Employee) can be picked as the one who attended."""
    _check_role()
    users = set(field_users())
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
    kw = dict(filters={"disabled": 0, "has_variants": 0, "is_stock_item": 1}, fields=["name", "item_name", "stock_uom"],
              order_by="item_name asc", limit_page_length=50)
    if text:
        kw["or_filters"] = [["item_name", "like", "%" + text + "%"], ["name", "like", "%" + text + "%"]]
    return frappe.get_all("Item", **kw)


@frappe.whitelist(methods=["POST"])
def set_attended(name, attended=1, used_products=None, used_items=None, attended_by=None):
    doc = frappe.get_doc("KC Case", name)
    doc.check_permission("write")  # on the case as it is now
    if doc.status == "Cancelled":
        frappe.throw(_("This case is cancelled. Reopen it first"))
    if cint(attended):
        doc.status = "Attended"
        _apply_used(doc, used_products, used_items, attended_by)
    else:
        doc.status = "Planned"
    doc.flags.handled_by = frappe.session.user
    # once attended by someone else the case belongs to him, which this user may not be allowed to edit:
    # the permission was checked above, on the case before the change
    doc.save(ignore_permissions=True)
    return {"attended": 1 if doc.status == "Attended" else 0,
            "can_read": bool(frappe.has_permission("KC Case", "read", doc=doc.name))}


@frappe.whitelist(methods=["POST"])
def create_case(payload):
    _check_role()
    frappe.has_permission("KC Case", "create", throw=True)
    from kayanick_crm.mobile import doctor_rows

    data = json.loads(payload) if isinstance(payload, str) else dict(payload or {})
    doctors = [d["doctor"] for d in doctor_rows(data)]
    if not doctors:
        frappe.throw(_("Choose at least one doctor"))
    case = frappe.get_doc({
        "doctype": "KC Case",
        "hospital": data.get("hospital"),
        "doctors": [{"doctor": d} for d in doctors],
        "case_date": data.get("case_date") or today(),
        "case_time": data.get("case_time"),
        "status": "Attended" if data.get("attended") else "Planned",
        "notes": data.get("notes"),
        "products": [{"product": p} for p in (data.get("products") or []) if p],
    })
    if case.status == "Attended":
        _apply_used(case, data.get("used_products"), data.get("used_items"), data.get("attended_by"))
    case.flags.handled_by = frappe.session.user
    # Create permission was checked above; the attendee may be someone outside this user's team
    case.insert(ignore_permissions=True)
    _attach_files("KC Case", case.name, data.get("files"))
    return {"case": case.name, "can_read": bool(frappe.has_permission("KC Case", "read", doc=case.name))}
