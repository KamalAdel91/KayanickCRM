import frappe
from frappe import _
from frappe.model.document import Document
from frappe.utils import getdate


class KCVisit(Document):
    def validate(self):
        from kayanick_crm.mobile import sync_doctors
        from kayanick_crm.perms import require_employee

        sync_doctors(self)
        if not self.employee:
            self.employee = require_employee()
        self.employee_name = frappe.db.get_value("Employee", self.employee, "employee_name")
        if self.has_next_visit != "Yes":
            self.next_visit_date = None
        if self.next_visit_date and self.visit_date and getdate(self.next_visit_date) < getdate(self.visit_date):
            frappe.throw(_("Next visit date can't be before the visit date"))

    def _targets(self, doc=None):
        doc = doc or self
        return {doc.hospital}, {r.doctor for r in doc.doctors}

    def on_update(self):
        hospitals, doctors = self._targets()
        before = self.get_doc_before_save()
        if before:  # the hospital or a doctor may have been changed: refresh the old ones too
            h, d = self._targets(before)
            hospitals |= h
            doctors |= d
        refresh_visit_dates(hospitals, doctors)
        # each doctor's relationship level comes from his latest visit
        for row in self.doctors:
            if row.relationship_level and latest_visit_of(row.doctor) == self.name:
                frappe.db.set_value("KC Doctor", row.doctor, "relationship_level", row.relationship_level,
                                    update_modified=False)

    def on_trash(self):
        hospitals, doctors = self._targets()
        refresh_visit_dates(hospitals, doctors, exclude=self.name)


def latest_visit_of(doctor, exclude=""):
    row = frappe.db.sql(
        """select v.name from `tabKC Visit` v
           join `tabKC Visit Doctor` d on d.parent = v.name and d.parenttype = 'KC Visit'
           where d.doctor = %s and v.name != %s
           order by v.visit_date desc, v.creation desc limit 1""", (doctor, exclude))
    return row[0][0] if row else None


def refresh_visit_dates(hospitals=(), doctors=(), exclude=None):
    """Recomputes Last visit / Next visit on hospitals and doctors from the visits that actually exist
    (the latest visit decides both), so edits and deletions never leave stale dates behind."""
    exclude = exclude or ""
    for name in {h for h in hospitals if h}:
        row = frappe.db.sql(
            """select visit_date, next_visit_date from `tabKC Visit`
               where hospital = %s and name != %s order by visit_date desc, creation desc limit 1""",
            (name, exclude), as_dict=True)
        _set_dates("KC Hospital", name, row)
    for name in {d for d in doctors if d}:
        row = frappe.db.sql(
            """select v.visit_date, v.next_visit_date from `tabKC Visit` v
               join `tabKC Visit Doctor` d on d.parent = v.name and d.parenttype = 'KC Visit'
               where d.doctor = %s and v.name != %s
               order by v.visit_date desc, v.creation desc limit 1""",
            (name, exclude), as_dict=True)
        _set_dates("KC Doctor", name, row)


def _set_dates(doctype, name, row):
    if not frappe.db.exists(doctype, name):
        return
    last = row[0].visit_date if row else None
    nxt = row[0].next_visit_date if row else None
    frappe.db.set_value(doctype, name, {"last_visit": last, "next_visit": nxt}, update_modified=False)
