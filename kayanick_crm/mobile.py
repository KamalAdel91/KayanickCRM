import json

import frappe
from frappe import _
from frappe.utils import add_days, cint, get_first_day, get_fullname, get_last_day, getdate, now, today

from kayanick_crm.notify import unread
from kayanick_crm.perms import employee_of, field_users, require_employee, visible_employees

VISIT_FIELDS = (
    "hospital", "visit_purpose", "visit_outcome", "notes", "next_action", "has_next_visit",
    "next_visit_date", "visit_date", "geolocation",
)
LIST_DTS = {
    "purposes": "KC Visit Purpose",
    "outcomes": "KC Visit Outcome",
    "levels": "KC Relationship Level",
    "products": "KC Product",
    "areas": "KC Area",
    "hospital_types": "KC Hospital Type",
}
DOCTOR_CHILD = {"KC Visit": "KC Visit Doctor", "KC Case": "KC Case Doctor"}
FOLLOW_UP_DAYS = 180  # older visits no longer raise a follow-up (Today screen and morning reminder)


def _doctor_titles(names):
    names = sorted({n for n in names if n})
    if not names:
        return {}
    rows = frappe.get_list("KC Doctor", filters={"name": ["in", names]}, fields=["name", "doctor_name"],
                           limit_page_length=len(names))
    return {r.name: r.doctor_name for r in rows}


def sync_doctors(doc):
    """Drops empty / duplicate doctor rows. At least one doctor is required."""
    seen, rows = set(), []
    for r in doc.get("doctors") or []:
        if r.doctor and r.doctor not in seen:
            seen.add(r.doctor)
            rows.append(r)
    if not rows:
        frappe.throw(_("Add at least one doctor"))
    doc.set("doctors", rows)


def doctor_rows(data):
    """Doctors from an API payload, in order, no duplicates: [{"doctor": .., "relationship_level": ..}].

    Takes names or {"doctor" / "name", "relationship_level"} dicts. A payload-level relationship_level
    (sent by app versions before levels were per doctor) applies to every doctor that has none."""
    default_level = data.get("relationship_level")
    items = data.get("doctors") or ([data.get("doctor")] if data.get("doctor") else [])
    out, seen = [], set()
    for d in items:
        if isinstance(d, dict):
            name, level = d.get("doctor") or d.get("name"), d.get("relationship_level") or default_level
        else:
            name, level = d, default_level
        if name and name not in seen:
            seen.add(name)
            out.append({"doctor": name, "relationship_level": level})
    return out


def doctors_of(parenttype, names):
    out = {}
    if names:
        for r in frappe.get_all(DOCTOR_CHILD[parenttype], filters={"parent": ["in", names], "parenttype": parenttype},
                                fields=["parent", "doctor"], order_by="idx asc"):
            out.setdefault(r.parent, []).append(r.doctor)
    return out


def add_doctor_titles(parenttype, rows):
    """Sets row.doctors (names) and row.doctor_title ("Dr. A, Dr. B") on visit/case rows.
    A row that already carries `doctors` (e.g. the doctors a follow-up is still open for) keeps them."""
    docs = doctors_of(parenttype, [r.name for r in rows if r.get("doctors") is None])
    for r in rows:
        if r.get("doctors") is None:
            r["doctors"] = docs.get(r.name, [])
    titles = _doctor_titles([d for r in rows for d in r["doctors"]])
    for r in rows:
        r["doctor_title"] = ", ".join(titles.get(d, d) for d in r["doctors"])
    return rows


def doctors_text(doc):
    """Doctor names of a loaded visit/case, for notifications (no permission checks)."""
    names = [r.doctor for r in doc.get("doctors") or []]
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


# ---- follow-ups ----

def open_follow_ups(visits):
    """Visits (newest first) -> [(visit, doctors)]: each visit with the doctors it is still the latest visit for
    at that hospital. A later visit to the same hospital + doctor closes the earlier follow-up for that doctor
    only, so a visit with three doctors stays open for the ones nobody went back to."""
    docs = doctors_of("KC Visit", [v.name for v in visits])
    seen, out = set(), []
    for v in visits:
        keys = [(v.hospital, d) for d in (docs.get(v.name) or [""])]
        fresh = [d for (h, d) in keys if (h, d) not in seen]
        seen.update(keys)
        if fresh:
            out.append((v, [d for d in fresh if d]))
    return out


def recent_visits(fields, filters=None, as_user=True):
    """Visits of the last FOLLOW_UP_DAYS days, newest first (within what the user can see when as_user)."""
    get = frappe.get_list if as_user else frappe.get_all
    return get("KC Visit", filters=[["visit_date", ">=", add_days(today(), -FOLLOW_UP_DAYS)]] + (filters or []),
               fields=fields, order_by="visit_date desc, creation desc", limit_page_length=5000)


def due_followup_names(until):
    """Visits whose follow-up is due by `until`, within what the user can see."""
    rows = recent_visits(["name", "hospital", "next_visit_date"])
    return [v.name for v, _d in open_follow_ups(rows)
            if v.next_visit_date and getdate(v.next_visit_date) <= getdate(until)]


@frappe.whitelist()
def get_options():
    out = {k: frappe.get_list(dt, pluck="name", order_by="creation asc", limit_page_length=500)
           for k, dt in LIST_DTS.items()}
    # Create permission on KC Hospital / KC Doctor (KC Manager)
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


@frappe.whitelist()
def get_today():
    user = frappe.session.user
    me = employee_of(user)
    day = getdate(today())
    horizon = getdate(add_days(today(), 7))
    fields = ["name", "visit_date", "hospital", "visit_purpose", "visit_outcome", "next_action", "next_visit_date",
              "order_expected", "employee", "employee_name"]
    # follow-ups of everyone this user can see: his own for a rep, his team for a manager, all for the rest
    team = recent_visits(fields)
    recent = [frappe._dict(v) for v in team if me and v.employee == me][:5]  # "Recent visits" stays personal

    due = []
    for v, doctors in open_follow_ups(team):
        if v.next_visit_date and getdate(v.next_visit_date) <= horizon:
            v["doctors"] = doctors
            v["mine"] = bool(me) and v.employee == me
            v["rep_name"] = v.employee_name or v.employee
            nd = getdate(v.next_visit_date)
            v["is_overdue"] = nd < day
            v["is_today"] = nd == day
            due.append(v)
    due.sort(key=lambda x: getdate(x.next_visit_date))
    add_doctor_titles("KC Visit", due + recent)

    from kayanick_crm.case_api import CASE_FIELDS, decorate

    cases = frappe.get_list(
        "KC Case",
        filters={"status": "Planned", "case_date": ["<=", horizon]},  # planned cases are open to the whole team
        fields=CASE_FIELDS, order_by="case_date asc, case_time asc", limit_page_length=100,
    )
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
    return {"user": get_fullname(user), "today": today(), "stats": stats, "due": due, "cases": cases, "recent": recent,
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


def _rep_employee(value):
    """The rep filter carries an Employee; older app versions sent the rep's user."""
    if value and "@" in str(value):
        return employee_of(value) or value
    return value


def list_filters(date_field, args, doctype):
    """Filters shared by the visits and cases lists. Row-level (team) permissions still apply on top."""
    a = frappe._dict(frappe.parse_json(args) if isinstance(args, str) else (args or {}))
    filters, or_filters = [], []
    if a.get("hospital"):
        filters.append(["hospital", "=", a.hospital])
    rep = _rep_employee(a.get("employee") or a.get("sales_rep"))
    if rep and doctype == "KC Visit":
        filters.append(["employee", "=", rep])
    elif rep:
        # a rep's cases: the ones he attended and the ones he planned
        creator = frappe.db.get_value("Employee", rep, "user_id") or ""
        names = frappe.get_list("KC Case", or_filters=[["employee", "=", rep], ["owner", "=", creator]],
                                pluck="name", limit_page_length=0)
        filters.append(["name", "in", names or [""]])
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
    start = max(cint(a.get("start")), 0)
    limit = min(max(cint(a.get("limit")) or PAGE, 1), 500)
    return start, limit


@frappe.whitelist()
def get_team():
    """Reps whose records the current user can see (for the rep filter). Empty for a plain rep.
    `user` carries the rep's Employee (the key name is kept for the app)."""
    reps = field_users().values()
    allowed = visible_employees()
    reps = [e for e in reps if allowed is None or e in allowed]
    if len(reps) <= 1:
        return []
    names = dict(frappe.get_all("Employee", filters={"name": ["in", reps]}, fields=["name", "employee_name"], as_list=True))
    return sorted(({"user": e, "name": names.get(e) or e} for e in reps), key=lambda x: x["name"].lower())


@frappe.whitelist()
def get_visits(args=None):
    a, filters, or_filters = list_filters("visit_date", args, "KC Visit")
    if a.get("outcome"):
        filters.append(["visit_outcome", "=", a.outcome])
    if cint(a.get("order_expected")):
        filters.append(["order_expected", "=", 1])
    if cint(a.get("due")):
        filters.append(["name", "in", due_followup_names(today()) or [""]])
    start, limit = page_args(a)
    rows = frappe.get_list(
        "KC Visit", fields=["name", "visit_date", "hospital", "visit_purpose", "visit_outcome", "order_expected",
                            "employee", "employee_name"],
        filters=filters, or_filters=or_filters,
        order_by="visit_date desc, creation desc", limit_start=start, limit_page_length=limit,
    )
    add_doctor_titles("KC Visit", rows)
    for r in rows:
        r["rep_name"] = r.employee_name or r.employee
    return rows


@frappe.whitelist()
def get_visit(name):
    from kayanick_crm.case_api import attachments

    doc = frappe.get_doc("KC Visit", name)
    doc.check_permission("read")
    titles = _doctor_titles([r.doctor for r in doc.doctors])
    out = {f: doc.get(f) for f in VISIT_FIELDS if f != "geolocation"}
    out.update({
        "name": doc.name, "employee": doc.employee, "sales_rep": doc.employee_name or doc.employee or "",
        "order_expected": doc.order_expected, "check_in_time": doc.check_in_time,
        "products": [p.product for p in doc.products],
        "doctors": [{"doctor": r.doctor, "doctor_name": titles.get(r.doctor, r.doctor),
                     "relationship_level": r.relationship_level} for r in doc.doctors],
        "doctor_title": ", ".join(titles.get(r.doctor, r.doctor) for r in doc.doctors),
        "attachments": attachments("KC Visit", doc.name),
        "can_delete": bool(frappe.has_permission("KC Visit", "delete", doc=doc)),
    })
    return out


@frappe.whitelist(methods=["POST"])
def delete_record(doctype, name):
    # frappe.delete_doc checks the Delete permission (KC Manager)
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
    doctors = doctor_rows(data)
    if not doctors:
        frappe.throw(_("Choose at least one doctor"))
    if any(not d["relationship_level"] for d in doctors):
        frappe.throw(_("Choose the relationship level for every doctor"))
    clean.setdefault("visit_date", today())

    visit = frappe.get_doc({
        "doctype": "KC Visit",
        "employee": require_employee(),
        "order_expected": 1 if data.get("order_expected") else 0,
        "check_in_time": now(),
        **clean,
    })
    for d in doctors:
        visit.append("doctors", d)
    for product in data.get("products") or []:
        if product:
            visit.append("products", {"product": product})
    visit.insert()
    return {"name": visit.name}
