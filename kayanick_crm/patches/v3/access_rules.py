"""Kayanick CRM v3: one access rule (perms.py). Every enabled KC Rep / KC Manager who doesn't see everything is
limited to their team: Create User Permission on their Employee. Safe to run again."""
import frappe

from kayanick_crm.perms import FIELD_ROLES, apply_scope, is_field_user, scope


def execute():
    print("Kayanick CRM v3, access rules:")
    users = set(frappe.get_all("Has Role", filters={"parenttype": "User", "role": ["in", FIELD_ROLES]},
                               pluck="parent")) - {"Administrator", "Guest"}
    for user in sorted(users):
        if not frappe.db.get_value("User", user, "enabled") or not is_field_user(user):
            continue
        before = scope(user)
        employee = apply_scope(user)
        if not employee:
            print("  WARNING: {0} has no active Employee with this User ID: they see nothing until one is "
                  "linked".format(user))
        elif before != scope(user):
            print("  {0} limited to their team (Employee {1})".format(user, employee))
    frappe.clear_cache()
