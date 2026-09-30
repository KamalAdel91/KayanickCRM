import frappe
from frappe.model.document import Document
from frappe.utils import getdate

class KCVisit(Document):
    def before_insert(self):
        if not self.sales_rep:
            self.sales_rep = frappe.session.user

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

