import json

import frappe
from frappe import _
from frappe.utils import get_fullname, getdate, now, today

CLOSED = ["Completed", "Cancelled"]

# fields the mobile form may set; sales_rep is always the logged-in user
VISIT_FIELDS = (
    "hospital_account", "doctor", "visit_type", "purpose", "products_discussed",
    "doctor_interest_level", "visit_notes", "next_action", "next_action_owner",
    "due_date", "next_visit_date", "visit_date", "geolocation", "check_in_time",
)


def _titles(doctype, title_field, names):
    names = sorted({n for n in names if n})
    if not names:
        return {}
    rows = frappe.get_list(
        doctype, filters={"name": ["in", names]}, fields=["name", title_field],
        limit_page_length=len(names),
    )
    return {r.name: r.get(title_field) for r in rows}


@frappe.whitelist()
def get_today():
    user = frappe.session.user
    tasks = frappe.get_list(
        "KC Task",
        filters={"owner_rep": user, "status": ["not in", CLOSED]},
        fields=["name", "task_description", "task_type", "priority", "status",
                "due_date", "hospital_account", "doctor"],
        order_by="due_date asc",
        limit_page_length=50,
    )
    hospitals = _titles("KC Account", "account_name", [t.hospital_account for t in tasks])
    doctors = _titles("KC Doctor", "doctor_name", [t.doctor for t in tasks])
    limit = getdate(today())
    for t in tasks:
        t["hospital_title"] = hospitals.get(t.hospital_account, t.hospital_account)
        t["doctor_title"] = doctors.get(t.doctor, t.doctor)
        t["is_overdue"] = bool(t.due_date) and getdate(t.due_date) < limit

    due_visits = frappe.get_list(
        "KC Account",
        filters={"account_owner": user, "next_visit": ["<=", today()]},
        fields=["name", "account_name", "city", "tier", "last_visit", "next_visit"],
        order_by="next_visit asc",
        limit_page_length=50,
    )
    for a in due_visits:
        a["is_overdue"] = getdate(a.next_visit) < limit
    return {"user": get_fullname(user), "today": today(), "tasks": tasks, "due_visits": due_visits}


@frappe.whitelist()
def search(text=""):
    text = (text or "").strip()[:60]
    like = "%" + text + "%"
    acc = dict(fields=["name", "account_name", "city", "tier", "last_visit", "next_visit"],
               order_by="modified desc", limit_page_length=20)
    doc = dict(fields=["name", "doctor_name", "specialty", "hospital_account", "last_visit"],
               order_by="modified desc", limit_page_length=20)
    if text:
        acc["or_filters"] = [["account_name", "like", like], ["city", "like", like]]
        doc["or_filters"] = [["doctor_name", "like", like], ["specialty", "like", like]]
    accounts = frappe.get_list("KC Account", **acc)
    doctors = frappe.get_list("KC Doctor", **doc)
    titles = _titles("KC Account", "account_name", [d.hospital_account for d in doctors])
    for d in doctors:
        d["hospital_title"] = titles.get(d.hospital_account, d.hospital_account)
    return {"accounts": accounts, "doctors": doctors}


@frappe.whitelist()
def get_doctors(hospital):
    return frappe.get_list(
        "KC Doctor", filters={"hospital_account": hospital},
        fields=["name", "doctor_name", "specialty"],
        order_by="doctor_name asc", limit_page_length=100,
    )


@frappe.whitelist(methods=["POST"])
def create_visit(payload):
    data = json.loads(payload) if isinstance(payload, str) else dict(payload or {})
    user = frappe.session.user
    clean = {k: data.get(k) for k in VISIT_FIELDS if data.get(k) not in (None, "")}

    hospital = clean.get("hospital_account")
    if not hospital:
        frappe.throw(_("Hospital is required"))
    if not frappe.has_permission("KC Account", "read", doc=hospital):
        frappe.throw(_("You cannot log visits for this account"), frappe.PermissionError)
    doctor = clean.get("doctor")
    if doctor and frappe.db.get_value("KC Doctor", doctor, "hospital_account") != hospital:
        frappe.throw(_("This doctor does not belong to the selected hospital"))
    if clean.get("next_action") and clean.get("due_date") and not clean.get("next_action_owner"):
        clean["next_action_owner"] = user
    clean.setdefault("visit_date", now())
    if clean.get("geolocation") and not clean.get("check_in_time"):
        clean["check_in_time"] = now()

    visit = frappe.get_doc({"doctype": "KC Visit", "sales_rep": user, **clean})
    visit.insert()
    return {"name": visit.name}


@frappe.whitelist(methods=["POST"])
def complete_task(task, result_feedback=None):
    doc = frappe.get_doc("KC Task", task)
    doc.check_permission("write")
    doc.status = "Completed"
    doc.completion_date = today()
    if result_feedback:
        doc.result_feedback = result_feedback
    doc.save()
    return {"name": doc.name, "status": doc.status}
