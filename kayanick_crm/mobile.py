import json

import frappe
from frappe import _
from frappe.utils import add_days, get_first_day, get_fullname, get_last_day, getdate, now, today

from kayanick_crm.notify import unread

VISIT_FIELDS = (
    "hospital", "doctor", "visit_purpose", "visit_outcome", "relationship_level",
    "notes", "next_action", "has_next_visit", "next_visit_date", "visit_date", "geolocation",
)
LIST_DTS = {
    "purposes": "KC Visit Purpose",
    "outcomes": "KC Visit Outcome",
    "levels": "KC Relationship Level",
    "products": "KC Product",
    "areas": "KC Area",
    "hospital_types": "KC Hospital Type",
}


def _doctor_titles(names):
    names = sorted({n for n in names if n})
    if not names:
        return {}
    rows = frappe.get_list("KC Doctor", filters={"name": ["in", names]}, fields=["name", "doctor_name"],
                           limit_page_length=len(names))
    return {r.name: r.doctor_name for r in rows}


DOCTOR_CHILD = {"KC Visit": "KC Visit Doctor", "KC Case": "KC Case Doctor"}


def sync_doctors(doc):
    """Drops empty/duplicate doctor rows and keeps the hidden `doctor` field = first (primary) doctor."""
    seen, rows = set(), []
    for r in doc.get("doctors") or []:
        if r.doctor and r.doctor not in seen:
            seen.add(r.doctor)
            rows.append(r)
    if not rows:
        frappe.throw(_("Add at least one doctor"))
    doc.set("doctors", rows)
    doc.doctor = rows[0].doctor


def doctor_list(data):
    """Doctor names from an API payload ("doctors": [...], or the old single "doctor"), in order, no duplicates."""
    names = data.get("doctors") or ([data.get("doctor")] if data.get("doctor") else [])
    out = []
    for n in names:
        n = n.get("name") if isinstance(n, dict) else n
        if n and n not in out:
            out.append(n)
    return out


def doctors_of(parenttype, names):
    out = {}
    if names:
        for r in frappe.get_all(DOCTOR_CHILD[parenttype], filters={"parent": ["in", names], "parenttype": parenttype},
                                fields=["parent", "doctor"], order_by="idx asc"):
            out.setdefault(r.parent, []).append(r.doctor)
    return out


def add_doctor_titles(parenttype, rows):
    """Sets row.doctors (names) and row.doctor_title ("Dr. A, Dr. B") on visit/case rows."""
    docs = doctors_of(parenttype, [r.name for r in rows])
    titles = _doctor_titles([d for ds in docs.values() for d in ds] + [r.get("doctor") for r in rows])
    for r in rows:
        ds = docs.get(r.name) or ([r.doctor] if r.get("doctor") else [])
        r["doctors"] = ds
        r["doctor_title"] = ", ".join(titles.get(d, d) for d in ds)
    return rows


def doctors_text(doc):
    """Doctor names of a loaded visit/case, for notifications (no permission checks)."""
    names = [r.doctor for r in doc.get("doctors") or []] or ([doc.doctor] if doc.get("doctor") else [])
    if not names:
        return ""
    titles = dict(frappe.get_all("KC Doctor", filters={"name": ["in", names]}, fields=["name", "doctor_name"], as_list=True))
    return ", ".join(titles.get(n) or n for n in names)


def parents_with(parenttype, doctors):
    """Visits/cases that have any of these doctors."""
    if not doctors:
        return []
    return frappe.get_all(DOCTOR_CHILD[parenttype], filters={"doctor": ["in", doctors], "parenttype": parenttype},
                          pluck="parent", distinct=True, limit_page_length=0)


def full_names(users):
    users = sorted({u for u in users if u})
    if not users:
        return {}
    return {u.name: u.full_name or u.name for u in frappe.get_all("User", filters={"name": ["in", users]}, fields=["name", "full_name"])}


def _count(filters):
    return len(frappe.get_list("KC Visit", filters=filters, pluck="name", limit_page_length=100000))


@frappe.whitelist()
def get_options():
    out = {k: frappe.get_list(dt, pluck="name", order_by="creation asc", limit_page_length=500)
           for k, dt in LIST_DTS.items()}
    # admins and sales managers may add hospitals/doctors (same rule as the Desk permissions)
    out["can_add_hospital"] = bool(frappe.has_permission("KC Hospital", "create"))
    out["can_add_doctor"] = bool(frappe.has_permission("KC Doctor", "create"))
    return out


def _doctor_display(text):
    """'dr ahmed  el gamal' -> 'Dr. Ahmed El Gamal' (Arabic names are kept as typed)."""
    import re

    text = re.sub(r"\s+", " ", (text or "").strip())
    if not re.search(r"[A-Za-z]", text):
        return text
    text = re.sub(r"^(?:dr|doctor)\b\.?\s*", "", text, flags=re.I).strip()
    return "Dr. " + " ".join(w[:1].upper() + w[1:].lower() for w in text.split(" ")) if text else ""


@frappe.whitelist(methods=["POST"])
def create_hospital(hospital_name, area=None, hospital_type=None):
    frappe.has_permission("KC Hospital", "create", throw=True)
    name = " ".join((hospital_name or "").split())
    if not name:
        frappe.throw(_("Hospital name is required"))
    if frappe.db.exists("KC Hospital", {"hospital_name": name}):
        frappe.throw(_("Hospital {0} already exists").format(name))
    doc = frappe.get_doc({"doctype": "KC Hospital", "hospital_name": name,
                          "area": area or None, "hospital_type": hospital_type or None}).insert()
    return {"name": doc.name, "area": doc.area, "hospital_type": doc.hospital_type}


@frappe.whitelist(methods=["POST"])
def create_doctor(doctor_name, relationship_level=None):
    frappe.has_permission("KC Doctor", "create", throw=True)
    name = _doctor_display(doctor_name)
    if not name:
        frappe.throw(_("Doctor name is required"))
    if frappe.db.exists("KC Doctor", {"doctor_name": name}):
        frappe.throw(_("{0} already exists").format(name))
    doc = frappe.get_doc({"doctype": "KC Doctor", "doctor_name": name,
                          "relationship_level": relationship_level or None}).insert()
    return {"name": doc.name, "doctor_name": doc.doctor_name, "relationship_level": doc.relationship_level}


def latest_per_pair(visits):
    """Visits sorted newest first -> only the latest one per hospital + doctor (it decides the follow-up)."""
    seen, out = set(), []
    for v in visits:
        key = (v.hospital, v.doctor or "")
        if key not in seen:
            seen.add(key)
            out.append(v)
    return out


def due_followup_names(until):
    """Visits whose follow-up is due by `until` (latest visit per hospital + doctor), within what the user can see."""
    rows = frappe.get_list("KC Visit", filters={"visit_date": [">=", add_days(today(), -180)]},
                           fields=["name", "hospital", "doctor", "next_visit_date"],
                           order_by="visit_date desc, creation desc", limit_page_length=5000)
    return [v.name for v in latest_per_pair(rows) if v.next_visit_date and getdate(v.next_visit_date) <= getdate(until)]


@frappe.whitelist()
def get_today():
    user = frappe.session.user
    day = getdate(today())
    horizon = getdate(add_days(today(), 7))
    fields = ["name", "visit_date", "hospital", "doctor", "visit_purpose", "visit_outcome",
              "next_action", "next_visit_date", "order_expected", "sales_rep"]
    # follow-ups of everyone this user can see: own for a rep, the team for a manager, all for an admin
    team = frappe.get_list(
        "KC Visit",
        filters={"visit_date": [">=", add_days(today(), -180)]},
        fields=fields, order_by="visit_date desc, creation desc", limit_page_length=5000,
    )
    visits = [v for v in team if v.sales_rep == user]  # "Recent visits" stays personal
    names = full_names([v.sales_rep for v in team])

    due = []
    for v in latest_per_pair(team):
        if v.next_visit_date and getdate(v.next_visit_date) <= horizon:
            v["mine"] = v.sales_rep == user
            v["rep_name"] = names.get(v.sales_rep, v.sales_rep)
            nd = getdate(v.next_visit_date)
            v["is_overdue"] = nd < day
            v["is_today"] = nd == day
            due.append(v)
    due.sort(key=lambda x: getdate(x.next_visit_date))
    add_doctor_titles("KC Visit", due + visits[:5])

    cases = frappe.get_list(
        "KC Case",
        filters={"attended": 0, "cancelled": 0, "case_date": ["<=", horizon]},  # planned cases are open to everyone
        fields=["name", "hospital", "doctor", "case_date", "case_time"], order_by="case_date asc, case_time asc", limit_page_length=100,
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
    def by(dt):
        if doctype == "KC Hospital":
            return {"hospital": name}
        return {"name": ["in", parents_with(dt, [name]) or [""]]}

    counts = {
        "visits": len(frappe.get_list("KC Visit", filters=by("KC Visit"), pluck="name", limit_page_length=100000)),
        "cases": len(frappe.get_list("KC Case", filters=by("KC Case"), pluck="name", limit_page_length=100000)),
    }
    info = {"name": doc.name, "title": doc.get("hospital_name") or doc.get("doctor_name"),
            "last_visit": doc.last_visit, "next_visit": doc.next_visit, "customer": doc.get("customer")}
    if doctype == "KC Hospital":
        info.update(area=doc.area, hospital_type=doc.hospital_type)
    else:
        info.update(relationship_level=doc.relationship_level)
    return {"info": info, "counts": counts}


PAGE = 50


def list_filters(date_field, args, doctype):
    """Filters shared by the visits and cases lists. Row-level (team) permissions still apply on top."""
    a = frappe._dict(frappe.parse_json(args) if isinstance(args, str) else (args or {}))
    filters, or_filters = [], []
    for key in ("hospital", "sales_rep"):
        if a.get(key):
            filters.append([key, "=", a[key]])
    if a.get("doctor"):
        filters.append(["name", "in", parents_with(doctype, [a.doctor]) or [""]])
    if a.get("from_date"):
        filters.append([date_field, ">=", a.from_date])
    if a.get("to_date"):
        filters.append([date_field, "<=", a.to_date])
    text = (a.get("text") or "").strip()[:60]
    if text:
        doctors = frappe.get_all("KC Doctor", filters={"doctor_name": ["like", "%" + text + "%"]}, pluck="name", limit=300)
        or_filters = [["hospital", "like", "%" + text + "%"]]
        parents = parents_with(doctype, doctors)
        if parents:
            or_filters.append(["name", "in", parents])
    return a, filters, or_filters


def page_args(a):
    start = max(frappe.utils.cint(a.get("start")), 0)
    limit = min(max(frappe.utils.cint(a.get("limit")) or PAGE, 1), 500)
    return start, limit


@frappe.whitelist()
def get_team():
    """Reps whose records the current user can see (for the rep filter). Empty for a plain rep."""
    from kayanick_crm.perms import sees_all, visible_reps

    reps = visible_reps()
    if reps is None or sees_all("KC Case") or sees_all("KC Visit"):  # everyone who has logged a visit or case
        reps = set(frappe.get_all("KC Visit", pluck="sales_rep", distinct=True)) | \
            set(frappe.get_all("KC Case", pluck="sales_rep", distinct=True))
    reps = {r for r in reps if r}
    if len(reps) <= 1:
        return []
    names = full_names(reps)
    return sorted(({"user": u, "name": names.get(u, u)} for u in reps), key=lambda x: x["name"].lower())


@frappe.whitelist()
def get_visits(args=None):
    a, filters, or_filters = list_filters("visit_date", args, "KC Visit")
    if a.get("outcome"):
        filters.append(["visit_outcome", "=", a.outcome])
    if frappe.utils.cint(a.get("order_expected")):
        filters.append(["order_expected", "=", 1])
    if frappe.utils.cint(a.get("due")):
        filters.append(["name", "in", due_followup_names(today()) or [""]])
    start, limit = page_args(a)
    rows = frappe.get_list(
        "KC Visit", fields=["name", "visit_date", "hospital", "doctor", "visit_purpose", "visit_outcome", "order_expected", "sales_rep"],
        filters=filters, or_filters=or_filters,
        order_by="visit_date desc, creation desc", limit_start=start, limit_page_length=limit,
    )
    add_doctor_titles("KC Visit", rows)
    names = full_names([r.sales_rep for r in rows])
    for r in rows:
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
        "doctor_title": doctors_text(doc),
        "doctors": [r.doctor for r in doc.doctors],
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
    doctors = doctor_list(data)
    if not doctors:
        frappe.throw(_("Choose at least one doctor"))
    clean["doctor"] = doctors[0]
    clean.setdefault("visit_date", today())

    visit = frappe.get_doc({
        "doctype": "KC Visit",
        "sales_rep": frappe.session.user,
        "order_expected": 1 if data.get("order_expected") else 0,
        "check_in_time": now(),
        **clean,
    })
    for d in doctors:
        visit.append("doctors", {"doctor": d})
    for product in data.get("products") or []:
        if product:
            visit.append("products", {"product": product})
    visit.insert()
    return {"name": visit.name}

