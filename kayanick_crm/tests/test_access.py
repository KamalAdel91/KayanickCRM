"""The access rule (perms.py): what each role sees, that the scope is applied by itself, and that a field user who
is not set up sees nothing."""
import frappe
from frappe.tests import IntegrationTestCase

from kayanick_crm.access import problems
from kayanick_crm.debt_api import visible_customers
from kayanick_crm.perms import access_problem, scope
from kayanick_crm.tests.utils import Team, as_user, make_customer, make_employee, make_user


def seen(user, doctype, names):
    """Which of these records the user can list."""
    with as_user(user):
        return set(frappe.get_list(doctype, filters={"name": ["in", list(names)]}, pluck="name"))


def can_read(user, doctype, name):
    return bool(frappe.has_permission(doctype, "read", doc=frappe.get_doc(doctype, name), user=user))


class TestAccess(IntegrationTestCase):
    def setUp(self):
        frappe.set_user("Administrator")
        self.t = Team()
        self.addCleanup(self.t.clear_caches)

    def test_scope_by_role(self):
        t = self.t
        self.assertEqual(scope(t.rep_a), {t.ea})
        self.assertEqual(scope(t.manager), {t.em, t.ea, t.eb})
        self.assertEqual(scope(t.outsider), {t.eo})
        self.assertIsNone(scope(t.viewer))
        self.assertIsNone(scope("Administrator"))
        self.assertEqual(scope(t.unlinked), set())

    def test_visits_follow_scope(self):
        t = self.t
        visits = {"a": t.visit(t.rep_a, t.ea), "b": t.visit(t.rep_b, t.eb), "o": t.visit(t.outsider, t.eo)}
        names = set(visits.values())
        self.assertEqual(seen(t.rep_a, "KC Visit", names), {visits["a"]})
        self.assertEqual(seen(t.manager, "KC Visit", names), {visits["a"], visits["b"]})
        self.assertEqual(seen(t.outsider, "KC Visit", names), {visits["o"]})
        self.assertEqual(seen(t.viewer, "KC Visit", names), names)
        self.assertFalse(can_read(t.rep_a, "KC Visit", visits["b"]))
        self.assertTrue(can_read(t.manager, "KC Visit", visits["b"]))

    def test_cases_follow_scope(self):
        t = self.t
        planned = t.case(t.rep_a)
        # planned by rep A, attended by rep B: it moves to B's team and A keeps reading it through a share
        handed_over = t.case(t.rep_a, attended_by=t.eb)
        for user in (t.rep_a, t.rep_b, t.outsider, t.manager, t.viewer):
            self.assertTrue(can_read(user, "KC Case", planned), user)
        self.assertTrue(can_read(t.rep_b, "KC Case", handed_over))
        self.assertTrue(can_read(t.rep_a, "KC Case", handed_over))
        self.assertTrue(can_read(t.manager, "KC Case", handed_over))
        self.assertFalse(can_read(t.outsider, "KC Case", handed_over))

    def test_not_set_up_sees_nothing(self):
        t = self.t
        visit = t.visit(t.rep_a, t.ea)
        planned = t.case(t.rep_a)
        with as_user(t.unlinked):
            self.assertEqual(frappe.get_list("KC Visit", pluck="name", limit_page_length=5), [])
            self.assertEqual(frappe.get_list("KC Case", pluck="name", limit_page_length=5), [])
        self.assertFalse(can_read(t.unlinked, "KC Visit", visit))
        self.assertFalse(can_read(t.unlinked, "KC Case", planned))
        self.assertTrue(access_problem(t.unlinked))
        self.assertFalse(access_problem(t.rep_a))
        self.assertEqual(visible_customers(t.unlinked)[0], set())

        from kayanick_crm.case_api import create_case

        with as_user(t.unlinked), self.assertRaises(frappe.PermissionError):
            create_case({"hospital": t.hospital, "doctors": [t.doctor], "case_time": "10:00:00", "notes": "x"})

    def test_scope_is_applied_by_itself(self):
        # the role first, the Employee later
        rep = make_user("late-employee", "KC Rep")
        self.addCleanup(frappe.clear_cache, user=rep)
        self.assertEqual(scope(rep), set())
        employee = make_employee("Late Employee", rep, reports_to=self.t.em)
        self.assertEqual(scope(rep), {employee})
        self.assertEqual(frappe.db.get_value("Employee", employee, "create_user_permission"), 1)

        # someone who saw everything (Create User Permission unticked) becomes a rep
        user = make_user("late-role")
        self.addCleanup(frappe.clear_cache, user=user)
        employee = make_employee("Late Role", user, create_user_permission=0)
        self.assertIsNone(scope(user))
        frappe.get_doc("User", user).add_roles("KC Rep")
        self.assertEqual(scope(user), {employee})

        # unticking Create User Permission doesn't lift it: a field user who must see everything gets KC Viewer
        doc = frappe.get_doc("Employee", self.t.ea)
        doc.create_user_permission = 0
        doc.save(ignore_permissions=True)
        self.assertEqual(frappe.db.get_value("Employee", self.t.ea, "create_user_permission"), 1)
        self.assertEqual(scope(self.t.rep_a), {self.t.ea})

    def test_everything_roles_are_not_limited_by_the_app(self):
        user = make_user("manager-viewer", "KC Manager", "KC Viewer")
        self.addCleanup(frappe.clear_cache, user=user)
        make_employee("Manager Viewer", user, create_user_permission=0)
        self.assertIsNone(scope(user))
        self.assertFalse(frappe.db.exists("User Permission", {"user": user, "allow": "Employee"}))

        # ERPNext's default tick limits a viewer too: the app never lifts it, the KC Access report says so
        limited = make_user("limited-viewer", "KC Viewer")
        self.addCleanup(frappe.clear_cache, user=limited)
        employee = make_employee("Limited Viewer", limited)
        self.assertEqual(scope(limited), {employee})
        self.assertIn("untick", " ".join(problems(limited, {"KC Viewer"}, employee)))

    def test_endpoints_take_text_only(self):
        from kayanick_crm.case_api import get_case
        from kayanick_crm.debt_api import get_customer_debt
        from kayanick_crm.mobile import get_visit

        t = self.t
        visit, case = t.visit(t.rep_a, t.ea), t.case(t.rep_a)
        with as_user(t.rep_a):
            self.assertEqual(get_visit(visit)["name"], visit)
            self.assertEqual(get_case(case)["name"], case)
            for call, value in ((get_visit, {"employee": t.eb}), (get_case, ["like", "%"]),
                                (get_customer_debt, {"name": ["is", "set"]})):
                with self.assertRaises(frappe.FrappeTypeError):
                    call(value)

    def test_debt_follows_scope(self):
        t = self.t
        ca, cb, cx = make_customer("A", t.ea), make_customer("B", t.eb), make_customer("No rep")
        mine = {ca, cb, cx}
        self.assertEqual(visible_customers(t.rep_a)[0] & mine, {ca})
        self.assertEqual(visible_customers(t.rep_b)[0] & mine, {cb})
        self.assertEqual(visible_customers(t.manager)[0] & mine, {ca, cb})
        self.assertEqual(visible_customers(t.outsider)[0] & mine, set())
        self.assertIsNone(visible_customers(t.viewer)[0])
