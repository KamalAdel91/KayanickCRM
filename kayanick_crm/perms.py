"""Access helpers for Kayanick CRM.

The app has no permission rules of its own. Everything is ERPNext's standard system:
- Role Permission Manager decides what each role can read / write / create / delete.
- User Permissions on Sales Person decide whose visits and cases a user sees. Sales Person is a tree,
  so a manager given his own node also sees every rep below him.
- KC Visit / KC Case carry a `sales_person` field, filled here from the user (User -> Employee -> Sales Person).
"""
import frappe


def sales_person_of(user):
    """The enabled Sales Person linked to this user through his Employee record, if any."""
    if not user:
        return None
    employees = frappe.get_all("Employee", filters={"user_id": user}, pluck="name")
    if not employees:
        return None
    rows = frappe.get_all("Sales Person", filters={"employee": ["in", employees], "enabled": 1},
                          pluck="name", order_by="lft asc", limit=1)
    return rows[0] if rows else None


def sales_users():
    """Users linked to an enabled Sales Person (the people who can attend a case)."""
    employees = frappe.get_all("Sales Person", filters={"enabled": 1, "employee": ["is", "set"]}, pluck="employee")
    if not employees:
        return set()
    return {u for u in frappe.get_all("Employee", filters={"name": ["in", employees]}, pluck="user_id") if u}


def is_app_user(user=None):
    """Anyone who can read visits or cases may open the app."""
    user = user or frappe.session.user
    return bool(frappe.has_permission("KC Visit", "read", user=user)
                or frappe.has_permission("KC Case", "read", user=user))


def can_reset_passwords(user=None):
    user = user or frappe.session.user
    return user == "Administrator" or "System Manager" in frappe.get_roles(user)
