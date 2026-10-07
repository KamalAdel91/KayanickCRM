import frappe
from frappe import _
from frappe.model.document import Document
from frappe.utils import flt


class KCCase(Document):
    def validate(self):
        from kayanick_crm.mobile import sync_doctors
        from kayanick_crm.perms import require_employee

        sync_doctors(self)
        if self.status != "Attended":
            # a planned (or cancelled) case belongs to nobody yet, so the whole team sees it (ERPNext shows
            # records with an empty link to everyone while "Apply Strict User Permissions" is off)
            self.employee = None
            self.employee_name = None
            self.used_products = None
            self.used_items = []
            return
        # attended: it belongs to whoever attended it (and, through Reports To, to his managers)
        if not self.employee:
            self.employee = require_employee()
        self.employee_name = frappe.db.get_value("Employee", self.employee, "employee_name")
        if self.used_products not in ("Yes", "No"):
            frappe.throw(_("Did you use products in this case? Choose Yes or No"))
        if self.used_products != "Yes":
            self.used_items = []
            return
        if not self.used_items:
            frappe.throw(_("Add the products that were used"))
        for row in self.used_items:
            if flt(row.qty) <= 0:
                frappe.throw(_("Row {0}: quantity must be more than zero").format(row.idx))

    def on_update(self):
        if self.status == "Attended" and self.employee:
            share_with_handlers(self.name, self.employee, {self.owner, self.flags.handled_by})


def share_with_handlers(case, employee, users):
    """A case attended by someone else moves to that person's team. Whoever created it, and whoever marked it
    attended, keep read access to it through a share (only when they couldn't see it otherwise)."""
    from kayanick_crm.perms import visible_employees

    attendee = frappe.db.get_value("Employee", employee, "user_id")
    for user in users:
        if not user or user in ("Administrator", "Guest") or user == attendee:
            continue
        allowed = visible_employees(user)
        if allowed is None or employee in allowed:
            continue  # sees it anyway
        if frappe.db.exists("DocShare", {"share_doctype": "KC Case", "share_name": case, "user": user}):
            continue
        frappe.share.add_docshare("KC Case", case, user, read=1, flags={"ignore_share_permission": True}, notify=0)
