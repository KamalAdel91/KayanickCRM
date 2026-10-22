"""Invoicing a case's used products (invoice type, prices, invoice number) and the reps' Sales Orders."""
from unittest.mock import patch

import frappe
from frappe.tests import IntegrationTestCase

from kayanick_crm import notify
from kayanick_crm.case_api import set_attended
from kayanick_crm.orders_api import create_order, get_order, get_orders
from kayanick_crm.tests.test_notify import Sent
from kayanick_crm.tests.utils import Team, as_user, first, make_customer, make_user


class OrdersTestCase(IntegrationTestCase):
    def setUp(self):
        frappe.set_user("Administrator")
        self.t = Team()
        self.accounts = make_user("accounts", "KC Accounts", "Sales User")
        self.addCleanup(self.t.clear_caches)
        self.addCleanup(frappe.clear_cache, user=self.accounts)
        self.item = first("Item", {"is_stock_item": 1, "is_sales_item": 1, "disabled": 0, "has_variants": 0})

    def capture(self):
        sent = Sent()
        p = patch.object(notify, "notify", sent)
        p.start()
        self.addCleanup(p.stop)
        return sent


class TestCaseInvoice(OrdersTestCase):
    def attend(self, case, rate=150, invoice_type="Cash", qty=2):
        with as_user(self.t.rep_a):
            set_attended(case, 1, "Yes", [{"item_code": self.item, "qty": qty, "rate": rate}], None, "Done",
                         invoice_type)

    def test_prices_total_and_invoice_type(self):
        case = self.t.case(self.t.rep_a)
        with self.assertRaises(frappe.ValidationError):
            self.attend(case, invoice_type=None)
        with self.assertRaises(frappe.ValidationError):
            self.attend(case, rate=0)
        self.attend(case)
        doc = frappe.get_doc("KC Case", case)
        self.assertEqual((doc.invoice_type, doc.total_amount, doc.invoice_status), ("Cash", 300, "To Invoice"))
        self.assertEqual(doc.used_items[0].amount, 300)

    def test_accounts_hear_and_invoice_it(self):
        t = self.t
        case = t.case(t.rep_a)
        self.attend(case)
        sent = self.capture()
        notify._case_to_accounts(case)
        self.assertIn(self.accounts, sent.users())
        self.assertFalse({t.rep_a, t.rep_b, t.manager} & sent.users())

        # a rep can't type the invoice number (permlevel 1): Frappe drops it
        with as_user(t.rep_a):
            doc = frappe.get_doc("KC Case", case)
            doc.invoice_number = "SINV-REP"
            doc.save()
        self.assertEqual(frappe.db.get_value("KC Case", case, "invoice_status"), "To Invoice")

        with as_user(self.accounts):
            doc = frappe.get_doc("KC Case", case)
            doc.invoice_number = "SINV-0001"
            doc.save()
        doc.reload()
        self.assertEqual((doc.invoice_status, doc.invoiced_by), ("Invoiced", self.accounts))

        # once invoiced, the prices are locked until the number is cleared
        with as_user(t.rep_a), self.assertRaises(frappe.ValidationError):
            doc = frappe.get_doc("KC Case", case)
            doc.used_items[0].rate = 200
            doc.save()


class TestOrders(OrdersTestCase):
    def order(self, user, customer, **row):
        with as_user(user):
            return create_order({"customer": customer, "notes": "Urgent",
                                 "items": [{"item_code": self.item, "qty": 3, "rate": 100, **row}]})["name"]

    def test_rep_orders_any_customer_as_draft(self):
        t = self.t
        customer = make_customer("Any")  # not the rep's customer
        name = self.order(t.rep_a, customer)
        so = frappe.get_doc("Sales Order", name)
        self.assertEqual((so.docstatus, so.kc_employee, so.owner, so.total), (0, t.ea, t.rep_a, 300))
        with self.assertRaises(frappe.ValidationError):
            self.order(t.rep_a, customer, rate=0)
        for user in (t.unlinked, t.viewer):
            with self.assertRaises(frappe.PermissionError):
                self.order(user, customer)

    def test_ordering_keeps_the_session(self):
        t = self.t
        customer = make_customer("Session")
        with as_user(t.rep_a):
            session = frappe.local.session
            session.sid, session.data = "test-sid", frappe._dict(csrf_token="test-token")
            frappe.local.form_dict = frappe._dict(cmd="kayanick_crm.orders_api.create_order")
            create_order({"customer": customer, "items": [{"item_code": self.item, "qty": 1, "rate": 10}]})
            self.assertEqual((frappe.session.user, session.sid, session.data.csrf_token, frappe.local.form_dict.cmd),
                             (t.rep_a, "test-sid", "test-token", "kayanick_crm.orders_api.create_order"))

    def test_orders_follow_scope(self):
        t = self.t
        name = self.order(t.rep_a, make_customer("Scope"))

        def listed(user):
            with as_user(user):
                return name in {o.name for o in get_orders({"limit": 500})}

        self.assertTrue(listed(t.rep_a))
        self.assertTrue(listed(t.manager))
        self.assertTrue(listed(t.viewer))
        self.assertFalse(listed(t.rep_b))
        with as_user(t.outsider), self.assertRaises(frappe.PermissionError):
            get_order(name)
        with as_user(t.rep_a):
            self.assertEqual(get_order(name)["notes"][0]["text"], "Urgent")

    def test_order_notifications(self):
        t = self.t
        name = self.order(t.rep_a, make_customer("Notify"))
        sent = self.capture()
        notify._order_to_readers(name, "new")
        self.assertTrue({self.accounts, t.manager, t.viewer} <= sent.users())
        self.assertFalse({t.rep_a, t.rep_b, t.outsider} & sent.users())

        sent.by_user.clear()
        frappe.db.set_value("Sales Order", name, "modified_by", self.accounts, update_modified=False)
        notify._order_to_readers(name, "approved")
        self.assertIn(t.rep_a, sent.users())
        self.assertNotIn(self.accounts, sent.users())
