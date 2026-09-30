import json

import frappe
from frappe import _
from frappe.utils import add_days, get_first_day, get_fullname, get_last_day, getdate, now, today

from kayanick_crm.notify import unread

VISIT_FIELDS = (
    "hospital", "doctor", "visit_purpose", "visit_outcome", "relationship_level",
    "notes", "next_action", "next_visit_date", "visit_date", "geolocation",
)
LIST_DTS = {
    "purposes": "KC Visit Purpose",
    "outcomes": "KC Visit Outcome",
    "levels": "KC Relationship Level",
    "products": "KC Product",
}


def _doctor_titles(names):
    names = sorted({n for n in names if n})
    if not names:
        return {}
    rows = frappe.get_list("KC Doctor", filters={"name": ["in", names]}, fields=["name", "doctor_name"],
                           limit_page_length=len(names))
    return {r.name: r.doctor_name for r in rows}


def full_names(users):
    users = sorted({u for u in users if u})
    if not users:
        return {}
    return {u.name: u.full_name or u.name for u in frappe.get_all("User", filters={"name": ["in", users]}, fields=["name", "full_name"])}


def _count(filters):
    return len(frappe.get_list("KC Visit", filters=filters, pluck="name", limit_page_length=100000))


@frappe.whitelist()
def get_options():
    return {k: frappe.get_list(dt, pluck="name", order_by="creation asc", limit_page_length=500)
            for k, dt in LIST_DTS.items()}


@frappe.whitelist()
def get_today():
    user = frappe.session.user
    day = getdate(today())
    horizon = getdate(add_days(today(), 7))
    fields = ["name", "visit_date", "hospital", "doctor", "visit_purpose", "visit_outcome",
              "next_action", "next_visit_date", "order_expected"]
    visits = frappe.get_list(
        "KC Visit",
        filters={"sales_rep": user, "visit_date": [">=", add_days(today(), -180)]},
        fields=fields, order_by="visit_date desc, creation desc", limit_page_length=500,
    )
    titles = _doctor_titles([v.doctor for v in visits])
    for v in visits:
        v["doctor_title"] = titles.get(v.doctor, v.doctor)

    seen, due = set(), []
    for v in visits:  # newest first: only the latest visit per hospital + doctor decides the follow-up
        key = (v.hospital, v.doctor or "")
        if key in seen:
            continue
        seen.add(key)
        if v.next_visit_date and getdate(v.next_visit_date) <= horizon:
            nd = getdate(v.next_visit_date)
            v["is_overdue"] = nd < day
            v["is_today"] = nd == day
            due.append(v)
    due.sort(key=lambda x: getdate(x.next_visit_date))

    cases = frappe.get_list(
        "KC Case",
        filters={"sales_rep": user, "attended": 0, "case_date": ["<=", horizon]},
        fields=["name", "hospital", "doctor", "case_date"], order_by="case_date asc", limit_page_length=100,
    )
    from kayanick_crm.case_api import decorate

    decorate(cases)
    for c in cases:
        cd = getdate(c.case_date)
        c["is_overdue"] = cd < day
        c["is_today"] = cd == day

    month = [["visit_date", ">=", get_first_day(today())]]
    stats = {
        "month_visits": _count(month),
        "month_positive": _count(month + [["visit_outcome", "=", "Positive"]]),
        "month_orders": _count(month + [["order_expected", "=", 1]]),
        "due": sum(1 for v in due if getdate(v.next_visit_date) <= day),
        "month_cases": len(frappe.get_list("KC Case", filters={"case_date": ["between", [get_first_day(today()), get_last_day(today())]]},
                                           pluck="name", limit_page_length=100000)),
        "cases_due": sum(1 for c in cases if getdate(c.case_date) <= day),
    }
    return {"user": get_fullname(user), "today": today(), "stats": stats, "due": due, "cases": cases, "recent": visits[:5],
            "unread": unread(user)}


@frappe.whitelist()
def search(text=""):
    text = (text or "").strip()[:60]
    like = "%" + text + "%"
    hosp = dict(fields=["name", "area", "hospital_type", "last_visit", "next_visit"],
                order_by="name asc", limit_page_length=200)
    doc = dict(fields=["name", "doctor_name", "relationship_level", "last_visit"],
               order_by="doctor_name asc", limit_page_length=200)
    if text:
        hosp["or_filters"] = [["hospital_name", "like", like], ["area", "like", like]]
        doc["filters"] = [["doctor_name", "like", like]]
    return {"hospitals": frappe.get_list("KC Hospital", **hosp), "doctors": frappe.get_list("KC Doctor", **doc)}


@frappe.whitelist()
def get_doctor(name):
    rows = frappe.get_list("KC Doctor", filters={"name": name}, fields=["name", "doctor_name", "relationship_level"])
    return rows[0] if rows else None


@frappe.whitelist()
def get_profile(doctype, name):
    """Hospital or doctor card with its visits and cases (visits/cases follow the usual team visibility)."""
    if doctype not in ("KC Hospital", "KC Doctor"):
        frappe.throw(_("Not permitted"), frappe.PermissionError)
    doc = frappe.get_doc(doctype, name)
    doc.check_permission("read")
    key = "hospital" if doctype == "KC Hospital" else "doctor"
    counts = {
        "visits": len(frappe.get_list("KC Visit", filters={key: name}, pluck="name", limit_page_length=100000)),
        "cases": len(frappe.get_list("KC Case", filters={key: name}, pluck="name", limit_page_length=100000)),
    }
    info = {"name": doc.name, "title": doc.get("hospital_name") or doc.get("doctor_name"),
            "last_visit": doc.last_visit, "next_visit": doc.next_visit, "customer": doc.get("customer")}
    if doctype == "KC Hospital":
        info.update(area=doc.area, hospital_type=doc.hospital_type)
    else:
        info.update(relationship_level=doc.relationship_level)
    return {"info": info, "counts": counts}


PAGE = 50


def list_filters(date_field, args):
    """Filters shared by the visits and cases lists. Row-level (team) permissions still apply on top."""
    a = frappe._dict(frappe.parse_json(args) if isinstance(args, str) else (args or {}))
    filters, or_filters = [], []
    for key in ("hospital", "doctor", "sales_rep"):
        if a.get(key):
            filters.append([key, "=", a[key]])
    if a.get("from_date"):
        filters.append([date_field, ">=", a.from_date])
    if a.get("to_date"):
        filters.append([date_field, "<=", a.to_date])
    text = (a.get("text") or "").strip()[:60]
    if text:
        doctors = frappe.get_all("KC Doctor", filters={"doctor_name": ["like", "%" + text + "%"]}, pluck="name", limit=300)
        or_filters = [["hospital", "like", "%" + text + "%"]]
        if doctors:
            or_filters.append(["doctor", "in", doctors])
    return a, filters, or_filters


def page_args(a):
    start = max(frappe.utils.cint(a.get("start")), 0)
    limit = min(max(frappe.utils.cint(a.get("limit")) or PAGE, 1), 200)
    return start, limit


@frappe.whitelist()
def get_team():
    """Reps whose records the current user can see (for the rep filter). Empty for a plain rep."""
    from kayanick_crm.perms import visible_reps

    reps = visible_reps()
    if reps is None:  # admin: everyone who has logged a visit or case
        reps = set(frappe.get_all("KC Visit", pluck="sales_rep", distinct=True)) | \
            set(frappe.get_all("KC Case", pluck="sales_rep", distinct=True))
    reps = {r for r in reps if r}
    if len(reps) <= 1:
        return []
    names = full_names(reps)
    return sorted(({"user": u, "name": names.get(u, u)} for u in reps), key=lambda x: x["name"].lower())


@frappe.whitelist()
def get_visits(args=None):
    a, filters, or_filters = list_filters("visit_date", args)
    if a.get("outcome"):
        filters.append(["visit_outcome", "=", a.outcome])
    start, limit = page_args(a)
    rows = frappe.get_list(
        "KC Visit", fields=["name", "visit_date", "hospital", "doctor", "visit_purpose", "visit_outcome", "order_expected", "sales_rep"],
        filters=filters, or_filters=or_filters,
        order_by="visit_date desc, creation desc", limit_start=start, limit_page_length=limit,
    )
    titles = _doctor_titles([r.doctor for r in rows])
    names = full_names([r.sales_rep for r in rows])
    for r in rows:
        r["doctor_title"] = titles.get(r.doctor, r.doctor)
        r["rep_name"] = names.get(r.sales_rep, r.sales_rep)
    return rows


@frappe.whitelist()
def get_visit(name):
    from kayanick_crm.case_api import attachments

    doc = frappe.get_doc("KC Visit", name)
    doc.check_permission("read")
    out = {f: doc.get(f) for f in VISIT_FIELDS if f != "geolocation"}
    out.update({
        "name": doc.name, "sales_rep": get_fullname(doc.sales_rep), "order_expected": doc.order_expected,
        "check_in_time": doc.check_in_time, "products": [p.product for p in doc.products],
        "doctor_title": _doctor_titles([doc.doctor]).get(doc.doctor, doc.doctor),
        "attachments": attachments("KC Visit", doc.name),
        "can_delete": bool(frappe.has_permission("KC Visit", "delete", doc=doc)),
    })
    return out


@frappe.whitelist(methods=["POST"])
def delete_record(doctype, name):
    # only managers/admins have delete permission; frappe.delete_doc checks it
    if doctype not in ("KC Visit", "KC Case"):
        frappe.throw(_("Not permitted"), frappe.PermissionError)
    frappe.delete_doc(doctype, name)
    return "ok"


@frappe.whitelist(methods=["POST"])
def create_visit(payload):
    data = json.loads(payload) if isinstance(payload, str) else dict(payload or {})
    clean = {k: data.get(k) for k in VISIT_FIELDS if data.get(k) not in (None, "")}
    hospital = clean.get("hospital")
    if not hospital:
        frappe.throw(_("Hospital is required"))
    if not frappe.db.exists("KC Hospital", hospital):
        frappe.throw(_("Hospital {0} not found").format(hospital))
    if not clean.get("doctor"):
        frappe.throw(_("Doctor is required"))
    clean.setdefault("visit_date", today())

    visit = frappe.get_doc({
        "doctype": "KC Visit",
        "sales_rep": frappe.session.user,
        "order_expected": 1 if data.get("order_expected") else 0,
        "check_in_time": now(),
        **clean,
    })
    for product in data.get("products") or []:
        if product:
            visit.append("products", {"product": product})
    visit.insert()
    return {"name": visit.name}

