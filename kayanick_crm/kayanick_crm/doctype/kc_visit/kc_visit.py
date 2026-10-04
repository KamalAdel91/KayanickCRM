import frappe
from frappe.model.document import Document
from frappe import _
from frappe.utils import getdate

class KCVisit(Document):
    def before_insert(self):
        if not self.sales_rep:
            self.sales_rep = frappe.session.user

    def validate(self):
        from kayanick_crm.mobile import sync_doctors

        sync_doctors(self)
        if self.has_next_visit != "Yes":
            self.next_visit_date = None
        if self.next_visit_date and self.visit_date and getdate(self.next_visit_date) < getdate(self.visit_date):
            frappe.throw(_("Next visit date can't be before the visit date"))

    def on_update(self):
        visit_day = getdate(self.visit_date)
        next_day = getdate(self.next_visit_date) if self.next_visit_date else None
        targets = [("KC Hospital", self.hospital)] + [("KC Doctor", r.doctor) for r in self.doctors]
        for dt, name in targets:
            if not name:
                continue
            cur_last = frappe.db.get_value(dt, name, "last_visit")
            if cur_last and visit_day < getdate(cur_last):
                continue  # an older visit never overrides the latest one
            values = {"last_visit": visit_day, "next_visit": next_day}
            if dt == "KC Doctor" and name == self.doctor and self.relationship_level:  # level belongs to the primary doctor
                values["relationship_level"] = self.relationship_level
            frappe.db.set_value(dt, name, values, update_modified=False)

