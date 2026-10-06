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

        from kayanick_crm.perms import sales_person_of

        sync_doctors(self)
        self.sales_person = sales_person_of(self.sales_rep)
        if self.has_next_visit != "Yes":
            self.next_visit_date = None
        if self.next_visit_date and self.visit_date and getdate(self.next_visit_date) < getdate(self.visit_date):
            frappe.throw(_("Next visit date can't be before the visit date"))

    def _targets(self, doc=None):
        doc = doc or self
        return {doc.hospital}, {r.doctor for r in doc.doctors} | {doc.doctor}

    def on_update(self):
        hospitals, doctors = self._targets()
        before = self.get_doc_before_save()
        if before:  # the hospital or a doctor may have been changed: refresh the old ones too
            h, d = self._targets(before)
            hospitals |= h
            doctors |= d
        refresh_visit_dates(hospitals, doctors)
        # relationship level belongs to the primary doctor, set from his latest visit only
        if self.doctor and self.relationship_level:
            latest = frappe.db.get_value("KC Doctor", self.doctor, "last_visit")
            if not latest or getdate(self.visit_date) >= getdate(latest):
                frappe.db.set_value("KC Doctor", self.doctor, "relationship_level", self.relationship_level,
                                    update_modified=False)

    def on_trash(self):
        hospitals, doctors = self._targets()
        refresh_visit_dates(hospitals, doctors, exclude=self.name)


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
               where v.name != %s and (v.doctor = %s or exists (
                   select 1 from `tabKC Visit Doctor` d
                   where d.parent = v.name and d.parenttype = 'KC Visit' and d.doctor = %s))
               order by v.visit_date desc, v.creation desc limit 1""",
            (exclude, name, name), as_dict=True)
        _set_dates("KC Doctor", name, row)


def _set_dates(doctype, name, row):
    if not frappe.db.exists(doctype, name):
        return
    last = row[0].visit_date if row else None
    nxt = row[0].next_visit_date if row else None
    frappe.db.set_value(doctype, name, {"last_visit": last, "next_visit": nxt}, update_modified=False)
