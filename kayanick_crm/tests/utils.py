"""Test data, built inside the test's transaction (rolled back after every test)."""
from contextlib import contextmanager

import frappe
from frappe.utils import today


def uniq():
    return frappe.generate_hash(length=8).lower()


def first(doctype, filters=None):
    name = frappe.db.get_value(doctype, filters or {}, "name")
    if not name:
        raise AssertionError("The site has no {0}".format(doctype))
    return name


@contextmanager
def as_user(user):
    current = frappe.session.user
    frappe.set_user(user)
    try:
        yield
    finally:
        frappe.set_user(current)


def make_user(label, *roles):
    email = "kc-test-{0}-{1}@example.com".format(uniq(), label)
    frappe.get_doc({"doctype": "User", "email": email, "first_name": label.title(), "send_welcome_email": 0,
                    "roles": [{"role": r} for r in roles]}).insert(ignore_permissions=True)
    return email


def make_employee(label, user=None, reports_to=None, create_user_permission=1):
    """ERPNext ticks Create User Permission on a new Employee; untick it for someone who must see everything."""
    return frappe.get_doc({
        "doctype": "Employee", "first_name": "KC Test " + label, "company": first("Company"),
        "gender": first("Gender"), "date_of_birth": "1990-01-01", "date_of_joining": "2020-01-01",
        "status": "Active", "user_id": user, "reports_to": reports_to,
        "create_user_permission": create_user_permission,
    }).insert(ignore_permissions=True).name


def make_customer(label, employee=None):
    """A customer whose rep (Sales Team > Sales Person) is this Employee."""
    sales_team = []
    if employee:
        root = frappe.db.get_value("Sales Person", {"parent_sales_person": ["is", "not set"]}, "name")
        person = frappe.get_doc({"doctype": "Sales Person", "sales_person_name": "KC Test {0} {1}".format(label, uniq()),
                                 "is_group": 0, "parent_sales_person": root, "employee": employee}
                                ).insert(ignore_permissions=True).name
        sales_team = [{"sales_person": person, "allocated_percentage": 100}]
    return frappe.get_doc({"doctype": "Customer", "customer_name": "KC Test {0} {1}".format(label, uniq()),
                           "customer_type": "Company", "sales_team": sales_team}).insert(ignore_permissions=True).name


class Team:
    """A manager with two reps below them in Reports To, a rep in another team, a viewer, and a rep whose user is
    not linked to an Employee."""

    def __init__(self):
        self.manager = make_user("manager", "KC Manager")
        self.rep_a = make_user("rep-a", "KC Rep")
        self.rep_b = make_user("rep-b", "KC Rep")
        self.outsider = make_user("outsider", "KC Rep")
        self.viewer = make_user("viewer", "KC Viewer")
        self.unlinked = make_user("unlinked", "KC Rep")
        self.em = make_employee("Manager", self.manager)
        self.ea = make_employee("Rep A", self.rep_a, reports_to=self.em)
        self.eb = make_employee("Rep B", self.rep_b, reports_to=self.em)
        self.eo = make_employee("Outsider", self.outsider)
        self.ev = make_employee("Viewer", self.viewer, create_user_permission=0)
        self.hospital = frappe.get_doc({"doctype": "KC Hospital",
                                        "hospital_name": "KC Test Hospital " + uniq()}).insert(ignore_permissions=True).name
        self.doctor = frappe.get_doc({"doctype": "KC Doctor",
                                      "doctor_name": "Dr. KC Test " + uniq()}).insert(ignore_permissions=True).name

    @property
    def users(self):
        return [self.manager, self.rep_a, self.rep_b, self.outsider, self.viewer, self.unlinked]

    def visit(self, user, employee, outcome="Positive"):
        with as_user(user):
            return frappe.get_doc({
                "doctype": "KC Visit", "employee": employee, "visit_date": today(), "hospital": self.hospital,
                "visit_purpose": first("KC Visit Purpose"), "visit_outcome": outcome, "next_action": "Call back",
                "has_next_visit": "No", "products": [{"product": first("KC Product")}],
                "doctors": [{"doctor": self.doctor, "relationship_level": first("KC Relationship Level")}],
            }).insert(ignore_permissions=True).name

    def case(self, user, attended_by=None):
        """A planned case created by `user`; attended by that Employee when given."""
        with as_user(user):
            doc = frappe.get_doc({
                "doctype": "KC Case", "hospital": self.hospital, "case_date": today(), "case_time": "10:00:00",
                "status": "Attended" if attended_by else "Planned", "notes": "Test case",
                "doctors": [{"doctor": self.doctor}], "products": [{"product": first("KC Product")}],
            })
            if attended_by:
                doc.update({"employee": attended_by, "used_products": "No", "attended_notes": "Done"})
            return doc.insert(ignore_permissions=True).name

    def clear_caches(self):
        for user in self.users:
            frappe.clear_cache(user=user)
