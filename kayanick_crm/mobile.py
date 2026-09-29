import json

import frappe
from frappe import _
from frappe.utils import add_days, get_first_day, get_fullname, getdate, now, today

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

    month = [["visit_date", ">=", get_first_day(today())]]
    stats = {
        "month_visits": _count(month),
        "month_positive": _count(month + [["visit_outcome", "=", "Positive"]]),
        "month_orders": _count(month + [["order_expected", "=", 1]]),
        "due": sum(1 for v in due if getdate(v.next_visit_date) <= day),
    }
    return {"user": get_fullname(user), "today": today(), "stats": stats, "due": due, "recent": visits[:5]}


@frappe.whitelist()
def search(text=""):
    text = (text or "").strip()[:60]
    like = "%" + text + "%"
    hosp = dict(fields=["name", "area", "hospital_type", "last_visit", "next_visit"],
                order_by="name asc", limit_page_length=200)
    doc = dict(fields=["name", "doctor_name", "hospital", "relationship_level", "last_visit"],
               order_by="modified desc", limit_page_length=30)
    if text:
        hosp["or_filters"] = [["hospital_name", "like", like], ["area", "like", like]]
        doc["or_filters"] = [["doctor_name", "like", like], ["hospital", "like", like]]
    return {"hospitals": frappe.get_list("KC Hospital", **hosp), "doctors": frappe.get_list("KC Doctor", **doc)}


@frappe.whitelist()
def get_doctors(hospital):
    return frappe.get_list(
        "KC Doctor", filters={"hospital": hospital},
        fields=["name", "doctor_name", "relationship_level"],
        order_by="doctor_name asc", limit_page_length=300,
    )


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


@frappe.whitelist(methods=["POST"])
def add_doctor(hospital, doctor_name):
    doctor_name = (doctor_name or "").strip()
    if not doctor_name:
        frappe.throw(_("Doctor name is required"))
    if not frappe.db.exists("KC Hospital", hospital):
        frappe.throw(_("Hospital {0} not found").format(hospital))
    existing = frappe.db.get_value("KC Doctor", {"hospital": hospital, "doctor_name": doctor_name},
                                   ["name", "doctor_name", "relationship_level"], as_dict=True)
    if existing:
        return existing
    doc = frappe.get_doc({"doctype": "KC Doctor", "doctor_name": doctor_name, "hospital": hospital}).insert()
    return {"name": doc.name, "doctor_name": doc.doctor_name, "relationship_level": doc.relationship_level}
