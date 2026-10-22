"""Notifications (notify.py): each goes to whoever can see the record or the customer, never to whoever caused it;
the daily overdue alert catches up on missed days without repeating itself."""
from unittest.mock import patch

import frappe
from frappe.tests import IntegrationTestCase
from frappe.utils import add_days, getdate

from kayanick_crm import notify
from kayanick_crm.tests.utils import Team, as_user, make_customer

DAY = "2026-10-21"  # a Wednesday: no weekly digest


class Sent:
    """Captures notify.notify calls: {user: [subject, ...]}."""

    def __init__(self):
        self.by_user = {}

    def __call__(self, user, subject, *args, **kwargs):
        self.by_user.setdefault(user, []).append(subject)

    def users(self):
        return set(self.by_user)


class TestNotify(IntegrationTestCase):
    def setUp(self):
        frappe.set_user("Administrator")
        self.t = Team()
        self.addCleanup(self.t.clear_caches)

    def capture(self):
        sent = Sent()
        p = patch.object(notify, "notify", sent)
        p.start()
        self.addCleanup(p.stop)
        return sent

    def test_visit_and_case_audiences(self):
        t = self.t
        sent = self.capture()
        notify._visit_to_readers(t.visit(t.rep_a, t.ea))
        self.assertTrue({t.manager, t.viewer} <= sent.users())
        self.assertFalse({t.rep_a, t.rep_b, t.outsider, t.unlinked} & sent.users())

        sent.by_user.clear()
        planned = t.case(t.rep_a)
        notify._case_to_readers(planned)
        self.assertTrue({t.rep_b, t.outsider, t.manager, t.viewer} <= sent.users())
        self.assertFalse({t.rep_a, t.unlinked} & sent.users())

        from kayanick_crm.case_api import cancel_case

        sent.by_user.clear()
        with as_user(t.rep_b):
            cancel_case(planned, "Doctor travelling")
        notify._case_cancelled_to_readers(planned)
        self.assertTrue({t.rep_a, t.outsider, t.manager} <= sent.users())
        self.assertNotIn(t.rep_b, sent.users())

    def test_payment_audience(self):
        t = self.t
        customer = make_customer("Payer", t.ea)
        payment = frappe._dict(name="ACC-PAY-TEST", party=customer, party_name="Payer", paid_amount=500,
                               paid_from_account_currency="EGP", modified_by=t.manager)
        real_get_doc = frappe.get_doc
        sent = self.capture()
        with patch.object(frappe, "get_doc", lambda *a, **k: payment if a[:1] == ("Payment Entry",) else real_get_doc(*a, **k)):
            notify._payment_to_readers(payment.name)
            self.assertTrue({t.rep_a, t.viewer} <= sent.users())
            self.assertFalse({t.manager, t.rep_b, t.outsider, t.unlinked} & sent.users())
            self.assertIn("Payment received", sent.by_user[t.rep_a][0])

            sent.by_user.clear()
            notify._payment_to_readers(payment.name, cancelled=True)
            self.assertIn("Payment cancelled", sent.by_user[t.rep_a][0])

    def overdue_run(self, invoices, last_run):
        """Runs debt_alerts on DAY with these (customer, due date) invoices; returns the customers announced."""
        rows = [frappe._dict(name="SINV-TEST-{0}".format(i), customer=c, customer_name=c, outstanding_amount=100,
                             due_date=getdate(due)) for i, (c, due) in enumerate(invoices)]
        if last_run:
            frappe.db.set_default(notify.LAST_DEBT_ALERTS, last_run)
        else:
            frappe.defaults.clear_default(key=notify.LAST_DEBT_ALERTS, parent="__default")
        sent = Sent()
        with patch.object(notify, "notify", sent), patch.object(notify, "today", lambda: DAY), \
                patch("kayanick_crm.debt_api.open_invoices", lambda customers=None: rows):
            notify.debt_alerts()
        self.assertEqual(frappe.db.get_default(notify.LAST_DEBT_ALERTS), DAY)
        return {s.split(" of ")[1].split(" is now")[0] for s in sent.by_user.get(self.t.viewer, [])}

    def test_overdue_alerts_catch_up(self):
        def ago(n):
            return str(add_days(DAY, -n))

        due = [("C1", ago(1)), ("C2", ago(2)), ("C3", ago(3)), ("C4", ago(4)), ("C7", ago(7)), ("C8", ago(8))]
        self.assertEqual(self.overdue_run(due, None), {"C1"})  # first run: yesterday's only
        self.assertEqual(self.overdue_run(due, DAY), set())  # a second run on the same day
        self.assertEqual(self.overdue_run(due, ago(1)), {"C1"})  # a normal day
        self.assertEqual(self.overdue_run(due, ago(3)), {"C1", "C2", "C3"})  # two days missed
        self.assertEqual(self.overdue_run(due, ago(30)), {"C1", "C2", "C3", "C4", "C7"})  # at most a week back

    def test_notifications_off_are_respected(self):
        t = self.t
        frappe.db.set_value("Notification Settings", t.manager, "enabled", 0)
        logs = lambda user: frappe.db.count("Notification Log", {"for_user": user})  # noqa: E731
        with patch.object(notify, "_push"):
            notify.notify(t.manager, "Test")
            notify.notify(t.viewer, "Test")
        self.assertEqual(logs(t.manager), 0)
        self.assertEqual(logs(t.viewer), 1)
