"""The Sales Orders the app makes: from an attended case's used products, and a rep's direct order."""
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


class TestCaseOrder(OrdersTestCase):
    def attend(self, case, rate=150, invoice_type="Cash", qty=2, customer=None):
        with as_user(self.t.rep_a):
            set_attended(case, 1, "Yes", [{"item_code": self.item, "qty": qty, "rate": rate}], None, "Done",
                         invoice_type, self.customer if customer is None else customer)

    def setUp(self):
        super().setUp()
        self.customer = make_customer("Hospital")

    def test_attending_with_products_makes_a_draft_order(self):
        case = self.t.case(self.t.rep_a)
        for missing in ({"invoice_type": None}, {"rate": 0}, {"customer": ""}):
            with self.assertRaises(frappe.ValidationError):
                self.attend(case, **missing)
        self.attend(case)
        doc = frappe.get_doc("KC Case", case)
        self.assertEqual((doc.invoice_type, doc.total_amount, doc.customer), ("Cash", 300, self.customer))
        so = frappe.get_doc("Sales Order", doc.sales_order)
        self.assertEqual((so.docstatus, so.kc_source, so.kc_case, so.kc_invoice_type, so.kc_employee, so.customer),
                         (0, "Case", case, "Cash", self.t.ea, self.customer))
        self.assertEqual([(i.item_code, i.qty, i.rate) for i in so.items], [(self.item, 2, 150)])

    def test_draft_follows_the_case(self):
        case = self.t.case(self.t.rep_a)
        self.attend(case)
        name = frappe.db.get_value("KC Case", case, "sales_order")
        self.attend(case, rate=180, qty=1, invoice_type="System")  # same order, new figures
        so = frappe.get_doc("Sales Order", name)
        self.assertEqual((so.kc_invoice_type, so.items[0].qty, so.items[0].rate), ("System", 1, 180))
        with as_user(self.t.rep_a):
            set_attended(case, 0)  # back to planned: the draft goes
        self.assertFalse(frappe.db.exists("Sales Order", name))
        self.assertIsNone(frappe.db.get_value("KC Case", case, "sales_order"))

    def test_approved_order_locks_the_case(self):
        case = self.t.case(self.t.rep_a)
        self.attend(case)
        name = frappe.db.get_value("KC Case", case, "sales_order")
        frappe.db.set_value("Sales Order", name, "docstatus", 1)  # approved by accounts
        with self.assertRaises(frappe.ValidationError):
            self.attend(case, rate=999)
        with as_user(self.t.rep_a), self.assertRaises(frappe.ValidationError):
            set_attended(case, 0)

    def test_accounts_hear_about_it(self):
        case = self.t.case(self.t.rep_a)
        self.attend(case)
        sent = self.capture()
        notify._order_to_readers(frappe.db.get_value("KC Case", case, "sales_order"), "new")
        self.assertIn(self.accounts, sent.users())
        self.assertIn("case " + case, sent.by_user[self.accounts][0])
        self.assertNotIn(self.t.rep_a, sent.users())


class TestOrders(OrdersTestCase):
    def order(self, user, customer, **row):
        with as_user(user):
            return create_order({"customer": customer, "notes": "Urgent", "invoice_type": "System",
                                 "items": [{"item_code": self.item, "qty": 3, "rate": 100, **row}]})["name"]

    def test_rep_orders_any_customer_as_draft(self):
        t = self.t
        customer = make_customer("Any")  # not the rep's customer
        name = self.order(t.rep_a, customer)
        so = frappe.get_doc("Sales Order", name)
        self.assertEqual((so.docstatus, so.kc_employee, so.owner, so.total, so.kc_source, so.kc_invoice_type),
                         (0, t.ea, t.rep_a, 300, "Direct Order", "System"))
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
            create_order({"customer": customer, "invoice_type": "Cash",
                          "items": [{"item_code": self.item, "qty": 1, "rate": 10}]})
            self.assertEqual((frappe.session.user, session.sid, session.data.csrf_token, frappe.local.form_dict.cmd),
                             (t.rep_a, "test-sid", "test-token", "kayanick_crm.orders_api.create_order"))

    def test_price_list_is_kept(self):
        """The rep's price stays on the order even when Stock Settings would copy it into the price list."""
        for field in ("update_existing_price_list_rate", "auto_insert_price_list_rate_if_missing"):
            frappe.db.set_single_value("Stock Settings", field, 1)
        frappe.clear_document_cache("Stock Settings", "Stock Settings")
        self.addCleanup(frappe.clear_document_cache, "Stock Settings", "Stock Settings")
        price_list = frappe.db.get_single_value("Selling Settings", "selling_price_list")
        frappe.db.delete("Item Price", {"item_code": self.item, "price_list": price_list})
        price = frappe.get_doc({"doctype": "Item Price", "item_code": self.item, "price_list": price_list,
                                "price_list_rate": 5000}).insert(ignore_permissions=True)
        other = first("Item", {"is_sales_item": 1, "disabled": 0, "has_variants": 0, "name": ["!=", self.item]})
        frappe.db.delete("Item Price", {"item_code": other})
        with as_user(self.t.rep_a):
            name = create_order({"customer": make_customer("Price"), "invoice_type": "Cash",
                                 "items": [{"item_code": self.item, "qty": 1, "rate": 777},
                                           {"item_code": other, "qty": 1, "rate": 888}]})["name"]
        self.assertEqual([i.rate for i in frappe.get_doc("Sales Order", name).items], [777, 888])
        self.assertEqual(frappe.db.get_value("Item Price", price.name, "price_list_rate"), 5000)
        self.assertFalse(frappe.db.exists("Item Price", {"item_code": other}))

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
