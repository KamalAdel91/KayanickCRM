import frappe
from frappe import _
from frappe.model.document import Document

class KCCase(Document):
    def before_insert(self):
        if not self.sales_rep:
            self.sales_rep = frappe.session.user
        if not self.company:
            from kayanick_crm.case_api import default_company
            self.company = default_company()

    def validate(self):
        before = None if self.is_new() else self.get_doc_before_save()
        if before and before.sales_order and "System Manager" not in frappe.get_roles():
            frappe.throw(_("This case is frozen: Sales Order {0} was already created").format(before.sales_order))
        if not self.items:
            frappe.throw(_("Add at least one item"))
        for row in self.items:
            if not row.qty or row.qty <= 0:
                frappe.throw(_("Row {0}: quantity must be more than zero").format(row.idx))

