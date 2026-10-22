"""Tests for Kayanick CRM. Every test builds its own data and rolls it back.

On a disposable test site:

    bench --site <test-site> run-tests --app kayanick_crm

On a site with real data (nothing is written: commits are skipped and everything is rolled back):

    bench --site <site> execute kayanick_crm.tests.run.run
"""
