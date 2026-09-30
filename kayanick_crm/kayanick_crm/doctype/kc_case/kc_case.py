import frappe
from frappe import _
from frappe.model.document import Document


class KCCase(Document):
    def before_insert(self):
        if not self.sales_rep:
            self.sales_rep = frappe.session.user

    def validate(self):
        if not self.items:
            frappe.throw(_("Add at least one item"))
        for row in self.items:
            if not row.qty or row.qty <= 0:
                frappe.throw(_("Row {0}: quantity must be more than zero").format(row.idx))
