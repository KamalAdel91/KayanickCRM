"""Access helpers for Kayanick CRM.

The app has no permission rules of its own; it runs on ERPNext's standard system:
- Roles decide what a user can do: KC Rep (log visits and cases), KC Manager (also edit, delete and manage the
  lists), KC Viewer (read only). System Manager can do everything.
- The Employee decides whose records a user sees. KC Visit and KC Case carry an `employee` field (the rep who
  visited / whoever attended the case). When "Create User Permission" is ticked on a user's Employee, ERPNext
  limits him to his own Employee and everyone below him in Reports To. Users without it see everything.
- A planned case has no employee yet, so the whole team sees it (ERPNext shows records with an empty link
  while "Apply Strict User Permissions" is off).
"""
import frappe
from frappe import _

APP_ROLES = ("KC Rep", "KC Manager", "KC Viewer")
FIELD_ROLES = ("KC Rep", "KC Manager")  # people who log visits and attend cases


def employee_of(user=None):
    """The active Employee linked to this user (User ID on the Employee), if any."""
    user = user or frappe.session.user
    if not user or user == "Guest":
        return None
    rows = frappe.get_all("Employee", filters={"user_id": user, "status": "Active"}, pluck="name",
                          order_by="creation asc", limit=1)
    return rows[0] if rows else None


def require_employee(user=None):
    employee = employee_of(user)
    if not employee:
        frappe.throw(_("Your user is not linked to an Employee. Ask the admin to put your user in "
                       "User ID on your Employee record."))
    return employee


def user_of(employee):
    return frappe.db.get_value("Employee", employee, "user_id") if employee else None


def field_users():
    """{user: employee} for enabled users with KC Rep / KC Manager and an active Employee."""
    users = set(frappe.get_all("Has Role", filters={"parenttype": "User", "role": ["in", FIELD_ROLES]},
                               pluck="parent"))
    users = set(frappe.get_all("User", filters={"name": ["in", list(users) or [""]], "enabled": 1}, pluck="name"))
    out = {}
    for e in frappe.get_all("Employee", filters={"user_id": ["in", list(users) or [""]], "status": "Active"},
                            fields=["name", "user_id"], order_by="creation asc"):
        out.setdefault(e.user_id, e.name)
    return out


def visible_employees(user=None):
    """Employees whose visits / cases the user can see: None means everyone (no User Permission on Employee),
    otherwise the set ERPNext allows (his own Employee and everyone below him in Reports To)."""
    from frappe.core.doctype.user_permission.user_permission import get_user_permissions

    perms = get_user_permissions(user or frappe.session.user).get("Employee") or []
    perms = [p for p in perms if not p.get("applicable_for") or p.get("applicable_for") in ("KC Visit", "KC Case")]
    return {p.get("doc") for p in perms} if perms else None


def is_app_user(user=None):
    """Anyone who can read visits or cases may open the app."""
    user = user or frappe.session.user
    return bool(frappe.has_permission("KC Visit", "read", user=user)
                or frappe.has_permission("KC Case", "read", user=user))


def can_reset_passwords(user=None):
    user = user or frappe.session.user
    return user == "Administrator" or "System Manager" in frappe.get_roles(user)
