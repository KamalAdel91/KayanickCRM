"""Move Kayanick CRM to ERPNext's standard permissions.

- fills the new `sales_person` field on existing visits and cases
- gives every rep / manager a User Permission on his own Sales Person node (for KC Visit and KC Case),
  so each one keeps seeing exactly what he saw before (a manager's node covers his team below it)
- users who had a "See all" role in KC Settings get the new KC Viewer role instead
- removes KC Settings / KC Settings Role
"""
import frappe

from kayanick_crm.perms import sales_person_of

DOCTYPES = ("KC Visit", "KC Case")
APP_ROLES = ("Sales Rep", "Sales Manager")


def execute():
    _ensure_viewer_role()
    viewers = _old_viewer_users()
    _backfill()
    _user_permissions(skip=viewers)
    for user in viewers:
        frappe.get_doc("User", user).add_roles("KC Viewer")
        print("KC Viewer role given to", user)
    _drop_settings()


def _ensure_viewer_role():
    if not frappe.db.exists("Role", "KC Viewer"):
        frappe.get_doc({"doctype": "Role", "role_name": "KC Viewer", "desk_access": 1}).insert(ignore_permissions=True)


def _old_viewer_users():
    """Users who held a role listed under 'See all Cases / Visits' in the old KC Settings."""
    if not frappe.db.table_exists("KC Settings Role"):
        return set()
    roles = frappe.db.sql_list(
        """select distinct role from `tabKC Settings Role`
           where parent = 'KC Settings' and parentfield in ('case_viewer_roles', 'visit_viewer_roles')""")
    if not roles:
        return set()
    users = set(frappe.get_all("Has Role", filters={"parenttype": "User", "role": ["in", roles]}, pluck="parent"))
    return {u for u in users if u not in ("Administrator", "Guest") and not _is_admin(u)}


def _is_admin(user):
    return "System Manager" in frappe.get_roles(user)


def _backfill():
    cache = {}

    def sp(user):
        if user not in cache:
            cache[user] = sales_person_of(user)
        return cache[user]

    for v in frappe.get_all("KC Visit", fields=["name", "sales_rep"], limit_page_length=0):
        frappe.db.set_value("KC Visit", v.name, "sales_person", sp(v.sales_rep), update_modified=False)
    for c in frappe.get_all("KC Case", fields=["name", "sales_rep", "attended", "attended_by"], limit_page_length=0):
        owner = c.attended_by if c.attended and c.attended_by else c.sales_rep
        frappe.db.set_value("KC Case", c.name, "sales_person", sp(owner), update_modified=False)


def _user_permissions(skip):
    users = set(frappe.get_all("Has Role", filters={"parenttype": "User", "role": ["in", APP_ROLES]}, pluck="parent"))
    for user in sorted(users):
        if user in ("Administrator", "Guest") or user in skip or _is_admin(user):
            continue
        if not frappe.db.get_value("User", user, "enabled"):
            continue
        node = sales_person_of(user)
        if not node:
            print("WARNING: {0} has no Sales Person (User -> Employee -> Sales Person). "
                  "Without a User Permission he sees every visit and case.".format(user))
            continue
        for dt in DOCTYPES:
            exists = frappe.db.exists("User Permission", {"user": user, "allow": "Sales Person", "for_value": node,
                                                          "apply_to_all_doctypes": 0, "applicable_for": dt})
            if not exists:
                frappe.get_doc({
                    "doctype": "User Permission", "user": user, "allow": "Sales Person", "for_value": node,
                    "apply_to_all_doctypes": 0, "applicable_for": dt,
                }).insert(ignore_permissions=True)
        print("User Permission: {0} -> Sales Person {1}".format(user, node))


def _drop_settings():
    for dt in ("KC Settings", "KC Settings Role"):
        if frappe.db.exists("DocType", dt):
            frappe.delete_doc("DocType", dt, force=True, ignore_permissions=True)
    frappe.db.delete("Singles", {"doctype": "KC Settings"})
    frappe.cache.delete_value("kc_settings_roles")
