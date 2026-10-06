import frappe
from frappe import _
from frappe.model.document import Document
from frappe.utils import flt


class KCCase(Document):
    def before_insert(self):
        if not self.sales_rep:
            self.sales_rep = frappe.session.user

    def validate(self):
        from kayanick_crm.mobile import sync_doctors

        sync_doctors(self)
        self.postponed_count = len(self.postponements or [])
        if self.attended and self.cancelled:
            frappe.throw(_("A cancelled case can't be marked attended. Reopen it first"))
        if not self.cancelled:
            self.cancelled_by = self.cancelled_on = self.cancel_reason = None
        # used items are info only (no stock effect); they only make sense once the case is attended
        if not self.attended:
            self.used_products = ""
            self.attended_by = None
        elif not self.attended_by:
            self.attended_by = frappe.session.user
        # a planned case belongs to its rep; once attended, to whoever attended it
        from kayanick_crm.perms import sales_person_of

        self.sales_person = sales_person_of(self.attended_by or self.sales_rep)
        if self.used_products != "Yes":
            self.used_items = []
            return
        if not self.used_items:
            frappe.throw(_("Add the products that were used"))
        for row in self.used_items:
            if flt(row.qty) <= 0:
                frappe.throw(_("Row {0}: quantity must be more than zero").format(row.idx))
