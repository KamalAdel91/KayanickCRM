import frappe
from frappe import _
from frappe.model.document import Document
from frappe.utils import getdate

PRIVILEGED = {"System Manager", "Sales Manager"}


class KCVisit(Document):
    def before_insert(self):
        if not self.sales_rep:
            self.sales_rep = frappe.session.user

    def validate(self):
        if self.doctor:
            hospital = frappe.db.get_value("KC Doctor", self.doctor, "hospital")
            if hospital != self.hospital:
                frappe.throw(_("Doctor {0} does not belong to {1}").format(self.doctor, self.hospital))

    def on_update(self):
        visit_day = getdate(self.visit_date)
        next_day = getdate(self.next_visit_date) if self.next_visit_date else None
        for dt, name in (("KC Hospital", self.hospital), ("KC Doctor", self.doctor)):
            if not name:
                continue
            cur_last = frappe.db.get_value(dt, name, "last_visit")
            if cur_last and visit_day < getdate(cur_last):
                continue  # an older visit never overrides the latest one
            values = {"last_visit": visit_day, "next_visit": next_day}
            if dt == "KC Doctor" and self.relationship_level:
                values["relationship_level"] = self.relationship_level
            frappe.db.set_value(dt, name, values, update_modified=False)


def _privileged(user):
    return user == "Administrator" or bool(PRIVILEGED & set(frappe.get_roles(user)))


def has_permission(doc, user=None, permission_type=None):
    user = user or frappe.session.user
    if _privileged(user) or permission_type == "create":
        return True
    return doc.get("sales_rep") == user


def get_permission_query_conditions(user=None):
    user = user or frappe.session.user
    if _privileged(user):
        return ""
    return "`tabKC Visit`.`sales_rep` = {0}".format(frappe.db.escape(user))
