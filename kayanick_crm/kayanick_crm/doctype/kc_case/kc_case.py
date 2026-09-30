import frappe
from frappe.model.document import Document


class KCCase(Document):
    def before_insert(self):
        if not self.sales_rep:
            self.sales_rep = frappe.session.user
