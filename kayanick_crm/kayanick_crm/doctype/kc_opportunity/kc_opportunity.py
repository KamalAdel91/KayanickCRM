import frappe
from frappe.model.document import Document
from frappe.utils import getdate, today

DT = "KC Opportunity"
OWNERS = ["sales_rep"]
PRIVILEGED = {"System Manager", "Sales Manager"}


class KCOpportunity(Document):
    def before_insert(self):
        if not self.get(OWNERS[0]):
            self.set(OWNERS[0], frappe.session.user)

    def validate(self):
        revenue = self.estimated_annual_revenue_usd or 0
        prob = self.probability_percent or 0
        self.weighted_revenue_usd = revenue * prob / 100.0


def _privileged(user):
    return user == "Administrator" or bool(PRIVILEGED & set(frappe.get_roles(user)))


def has_permission(doc, user=None, permission_type=None):
    user = user or frappe.session.user
    if _privileged(user) or permission_type == "create":
        return True
    return any(doc.get(f) == user for f in OWNERS)


def get_permission_query_conditions(user=None):
    user = user or frappe.session.user
    if _privileged(user):
        return ""
    u = frappe.db.escape(user)
    return "(" + " OR ".join(f"`tab{DT}`.`{f}` = {u}" for f in OWNERS) + ")"
