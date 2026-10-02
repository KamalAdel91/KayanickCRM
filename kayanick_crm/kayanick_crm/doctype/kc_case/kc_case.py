import frappe
from frappe import _
from frappe.model.document import Document
from frappe.utils import flt


class KCCase(Document):
    def before_insert(self):
        if not self.sales_rep:
            self.sales_rep = frappe.session.user

    def validate(self):
        # used items are info only (no stock effect); they only make sense once the case is attended
        if not self.attended:
            self.used_products = ""
        if self.used_products != "Yes":
            self.used_items = []
            return
        if not self.used_items:
            frappe.throw(_("Add the products that were used"))
        for row in self.used_items:
            if flt(row.qty) <= 0:
                frappe.throw(_("Row {0}: quantity must be more than zero").format(row.idx))
