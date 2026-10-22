import frappe
from frappe import _
from frappe.model.document import Document
from frappe.utils import flt


class KCCase(Document):
    def validate(self):
        from kayanick_crm.mobile import sync_doctors

        sync_doctors(self)
        self.validate_attendance()
        self.set_amounts()
        self.validate_order_lock()

    def validate_attendance(self):
        from kayanick_crm.perms import require_employee

        if self.status != "Attended":
            # a planned (or cancelled) case belongs to nobody yet, so the whole team sees it (ERPNext shows
            # records with an empty link to everyone while "Apply Strict User Permissions" is off)
            self.employee = None
            self.employee_name = None
            self.used_products = None
            self.used_items = []
            self.invoice_type = None
            self.customer = None
            self.attended_notes = None
            return
        # attended: it belongs to whoever attended it (and, through Reports To, to their managers)
        if not self.employee:
            self.employee = require_employee()
        self.employee_name = frappe.db.get_value("Employee", self.employee, "employee_name")
        if not (self.attended_notes or "").strip():
            frappe.throw(_("Write your notes on the case"))
        if self.used_products not in ("Yes", "No"):
            frappe.throw(_("Did you use products in this case? Choose Yes or No"))
        if self.used_products != "Yes":
            self.used_items = []
            self.invoice_type = None
            self.customer = None
            return
        if not self.used_items:
            frappe.throw(_("Add the products that were used"))
        for row in self.used_items:
            if flt(row.qty) <= 0:
                frappe.throw(_("Row {0}: quantity must be more than zero").format(row.idx))
        # cases attended before invoice types and Sales Orders existed keep none, until their attendance changes
        changed = self.is_new() or self.has_value_changed("status") or self.has_value_changed("used_products")
        if changed and not self.invoice_type:
            frappe.throw(_("Choose the invoice type: System or Cash"))
        if changed and not self.customer:
            frappe.throw(_("Choose the customer of the Sales Order"))
        if self.invoice_type:
            for row in self.used_items:
                if flt(row.rate) <= 0:
                    frappe.throw(_("Row {0}: enter the price of {1}").format(row.idx, row.item_name or row.item_code))

    def set_amounts(self):
        for row in self.used_items:
            row.amount = flt(row.qty) * flt(row.rate)
        self.total_amount = sum(flt(row.amount) for row in self.used_items)

    def validate_order_lock(self):
        """Once accounts submit the Sales Order of the used products, those can't change on the case."""
        if not self.sales_order or frappe.db.get_value("Sales Order", self.sales_order, "docstatus") != 1:
            return
        before = self.get_doc_before_save()
        if before and order_inputs(before) != order_inputs(self):
            frappe.throw(_("Sales Order {0} of this case is already approved, so its used products can't change")
                         .format(self.sales_order))

    def on_update(self):
        from kayanick_crm.orders_api import sync_case_order

        if self.status == "Attended" and self.employee:
            share_with_handlers(self.name, self.employee, {self.owner, self.flags.handled_by})
        sync_case_order(self)


def order_inputs(doc):
    """What the case's Sales Order is made from."""
    return (doc.status, doc.used_products, doc.invoice_type, doc.customer,
            [(r.item_code, flt(r.qty), flt(r.rate)) for r in doc.get("used_items") or []])


def share_with_handlers(case, employee, users):
    """A case attended by someone else moves to that person's team. Whoever created it, and whoever marked it
    attended, keep read access to it through a share (only when they couldn't see it otherwise)."""
    from kayanick_crm.perms import scope

    attendee = frappe.db.get_value("Employee", employee, "user_id")
    for user in users:
        if not user or user in ("Administrator", "Guest") or user == attendee:
            continue
        allowed = scope(user)
        if allowed is None or employee in allowed:
            continue  # sees it anyway
        if frappe.db.exists("DocShare", {"share_doctype": "KC Case", "share_name": case, "user": user}):
            continue
        frappe.share.add_docshare("KC Case", case, user, read=1, flags={"ignore_share_permission": True}, notify=0)
