"""Runs the app's tests on a site with real data without writing to it: commits are skipped while they run and
everything is rolled back at the end.

    bench --site <site> execute kayanick_crm.tests.run.run
"""
import unittest

import frappe
from frappe.tests.utils import toggle_test_mode

MODULES = ("kayanick_crm.tests.test_access", "kayanick_crm.tests.test_notify")


def run(verbosity=2):
    frappe.db.rollback()
    commit = frappe.db.commit
    frappe.db.commit = lambda *args, **kwargs: None
    toggle_test_mode(True)
    try:
        suite = unittest.defaultTestLoader.loadTestsFromNames(MODULES)
        result = unittest.TextTestRunner(verbosity=verbosity).run(suite)
    finally:
        frappe.db.rollback()
        frappe.db.commit = commit
        toggle_test_mode(False)
        frappe.set_user("Administrator")
    if not result.wasSuccessful():
        raise SystemExit(1)
