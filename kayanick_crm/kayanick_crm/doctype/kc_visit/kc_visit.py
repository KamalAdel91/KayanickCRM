import frappe
from frappe.model.document import Document
from frappe.utils import getdate, today

DT = "KC Visit"
OWNERS = ["sales_rep"]
PRIVILEGED = {"System Manager", "Sales Manager"}


class KCVisit(Document):
    def before_insert(self):
        if not self.get(OWNERS[0]):
            self.set(OWNERS[0], frappe.session.user)

    def on_update(self):
        self._sync_last_next()
        self._create_followup_task()

    def _sync_last_next(self):
        visit_day = getdate(self.visit_date)
        next_day = getdate(self.next_visit_date) if self.next_visit_date else None
        targets = (
            ("KC Account", self.hospital_account, "last_visit", "next_visit"),
            ("KC Doctor", self.doctor, "last_visit", "next_followup"),
        )
        for dt, name, last_f, next_f in targets:
            if not name:
                continue
            cur_last, cur_next = frappe.db.get_value(dt, name, [last_f, next_f])
            if not cur_last or visit_day > getdate(cur_last):
                frappe.db.set_value(dt, name, last_f, visit_day, update_modified=False)
            if next_day and next_day >= getdate(today()):
                stale = (not cur_next) or getdate(cur_next) < getdate(today())
                if stale or next_day < getdate(cur_next):
                    frappe.db.set_value(dt, name, next_f, next_day, update_modified=False)

    def _create_followup_task(self):
        if not (self.next_action and self.due_date and self.next_action_owner):
            return
        if frappe.db.exists("KC Task", {
            "related_visit": self.name,
            "task_type": "Follow-up",
            "status": ["not in", ["Completed", "Cancelled"]],
        }):
            return
        frappe.get_doc({
            "doctype": "KC Task",
            "task_type": "Follow-up",
            "status": "Open",
            "task_description": self.next_action,
            "due_date": self.due_date,
            "owner_rep": self.next_action_owner,
            "sales_rep": self.sales_rep,
            "hospital_account": self.hospital_account,
            "doctor": self.doctor,
            "related_visit": self.name,
        }).insert(ignore_permissions=True)


def _privileged(user):
    return user == "Administrator" or bool(PRIVILEGED & set(frappe.get_roles(user)))


def has_permission(doc, user=None, permission_type=None):
    user = user or frappe.session.user
    if _privileged(user) or permission_type == "create":
        return True
    return any(doc.get(f) == user for f in OWNERS)


def get_permission_query_conditions(user=None):
    user = user or frappe.session.user
    if _privileged(user):
        return ""
    u = frappe.db.escape(user)
    return "(" + " OR ".join(f"`tab{DT}`.`{f}` = {u}" for f in OWNERS) + ")"
