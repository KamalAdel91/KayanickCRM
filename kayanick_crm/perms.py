"""Who can do what and who sees what in Kayanick CRM. Every other module asks here.

- The role decides what a user can do (the DocType permissions): KC Rep logs visits, cases and orders, KC Manager
  also edits, deletes and manages the lists, KC Viewer reads, KC Accounts reviews and submits the Sales Orders
  the app makes, System Manager does everything.
- The scope decides whose records a user sees. It is Frappe's own User Permission on Employee: the user's Employee
  and everyone below it in Reports To. A KC Rep / KC Manager always has it: apply_scope adds it whenever their User
  or Employee is saved, and never removes one. KC Viewer and System Manager have none, so they see everything.
- A KC Rep / KC Manager without it (no active Employee yet) sees nothing until they have one.
- A planned case has no Employee yet, so every field user sees it (Frappe shows records with an empty link while
  "Apply Strict User Permissions" is off). Once attended it belongs to whoever attended it.
- A customer's debt follows the customer's rep (Customer > Sales Team > Sales Person > Employee, see debt_api.py):
  whoever sees the rep sees the customer. A customer with no rep is seen only by users who see everything.
- A notification about a record goes to the app users who can see it, except whoever caused it (see notify.py).
"""
from contextlib import contextmanager

import frappe
from frappe import _

APP_ROLES = ("KC Rep", "KC Manager", "KC Viewer")
FIELD_ROLES = ("KC Rep", "KC Manager")  # people who log visits and attend cases: limited to their team
ACCOUNTS_ROLE = "KC Accounts"  # reviews and submits the Sales Orders the app makes
EVERYTHING_ROLES = ("System Manager", "KC Viewer", ACCOUNTS_ROLE)  # no team limit
RECORD_DOCTYPES = ("KC Visit", "KC Case")  # the records that belong to an Employee


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


def app_users():
    """Enabled users with a Kayanick role: the people who use the app."""
    users = frappe.get_all("Has Role", filters={"parenttype": "User", "role": ["in", APP_ROLES]}, pluck="parent")
    return set(frappe.get_all("User", filters={"name": ["in", list(set(users)) or [""]], "enabled": 1},
                              pluck="name")) - {"Administrator", "Guest"}


def accounts_users():
    """Enabled users with KC Accounts."""
    users = frappe.get_all("Has Role", filters={"parenttype": "User", "role": ACCOUNTS_ROLE}, pluck="parent")
    return set(frappe.get_all("User", filters={"name": ["in", users or [""]], "enabled": 1},
                              pluck="name")) - {"Administrator", "Guest"}


def sees_everything(user, roles=None):
    """Administrator, System Manager, KC Viewer and KC Accounts have no team limit (a User Permission can still
    limit them)."""
    roles = set(roles if roles is not None else frappe.get_roles(user))
    return user == "Administrator" or bool(roles & set(EVERYTHING_ROLES))


def is_field_user(user, roles=None):
    """A KC Rep / KC Manager who doesn't see everything: always limited to their team."""
    roles = set(roles if roles is not None else frappe.get_roles(user))
    return bool(roles & set(FIELD_ROLES)) and not sees_everything(user, roles)


def scope(user=None):
    """Employees whose visits, cases and customers the user sees; None means everyone.

    Frappe's User Permissions on Employee decide (the user's Employee and everyone below it in Reports To). A field
    user without them gets an empty set: nothing, until apply_scope can give them one."""
    from frappe.core.doctype.user_permission.user_permission import get_user_permissions

    user = user or frappe.session.user
    perms = get_user_permissions(user).get("Employee") or []
    perms = [p for p in perms if not p.get("applicable_for") or p.get("applicable_for") in RECORD_DOCTYPES]
    if perms:
        return {p.get("doc") for p in perms}
    return set() if is_field_user(user) else None


def access_problem(user=None):
    """Why a field user sees nothing, for the app to show them; "" when their access is set up."""
    user = user or frappe.session.user
    if scope(user) != set():
        return ""
    if not employee_of(user):
        return _("Your user is not linked to an Employee, so you can't see any visits, cases or customers yet. "
                 "Ask the admin to put your user in User ID on your Employee record.")
    return _("Your access is not set up yet, so you can't see any visits, cases or customers. "
             "Ask the admin to open your Employee record and save it.")


def require_scope(user=None):
    problem = access_problem(user)
    if problem:
        frappe.throw(problem, frappe.PermissionError)


def apply_scope(user, roles=None, enabled=None):
    """Limits a field user to their team, the way ERPNext does it: Create User Permission on their active Employee
    and the User Permissions it stands for (that Employee and its Company). Never removes one.
    Returns the Employee the user is limited to, or None when nothing applies."""
    from frappe.permissions import add_user_permission

    if not user or user in ("Administrator", "Guest") or not is_field_user(user, roles):
        return None
    if not (enabled if enabled is not None else frappe.db.get_value("User", user, "enabled")):
        return None
    employee = employee_of(user)
    if not employee:
        return None
    company, ticked = frappe.db.get_value("Employee", employee, ["company", "create_user_permission"])
    if not ticked:
        frappe.db.set_value("Employee", employee, "create_user_permission", 1, update_modified=False)
    add_user_permission("Employee", employee, user, ignore_permissions=True)
    if company:
        add_user_permission("Company", company, user, ignore_permissions=True)
    return employee


def _apply_scope_on_save(user, **kwargs):
    """Never stops a User or Employee from saving: a failure goes to the Error Log, and until it is fixed the user
    sees nothing (scope)."""
    try:
        apply_scope(user, **kwargs)
    except Exception:
        frappe.log_error(title="Kayanick CRM: could not limit {0} to their team".format(user))


def on_user_update(doc, method=None):
    """A user given KC Rep / KC Manager is limited to their team at once."""
    _apply_scope_on_save(doc.name, roles=[r.role for r in doc.get("roles") or []], enabled=doc.enabled)


def on_employee_validate(doc, method=None):
    """A field user's Employee keeps Create User Permission ticked: ERPNext then gives them the User Permissions.
    To let someone see everything, give them KC Viewer instead of unticking it."""
    if doc.user_id and doc.status == "Active" and is_field_user(doc.user_id):
        doc.create_user_permission = 1


def on_employee_update(doc, method=None):
    """Linking a field user to their Employee limits them to their team."""
    if doc.user_id and doc.status == "Active":
        _apply_scope_on_save(doc.user_id)


# ---- KC Visit / KC Case: the standard permission hooks (hooks.py) ----

def record_query_conditions(user=None, doctype=None):
    """Lists: nothing for a field user whose scope isn't set; otherwise Frappe's User Permissions decide."""
    return "1=0" if scope(user or frappe.session.user) == set() else ""


def has_record_permission(doc, ptype=None, user=None, debug=False):
    """One record: the same rule as record_query_conditions. True leaves the decision to Frappe."""
    return scope(user or frappe.session.user) != set()


@contextmanager
def as_administrator():
    """Runs a block as Administrator, then gives the session back unchanged: frappe.set_user alone would also reset
    the session's sid and data (which hold the CSRF token) in the middle of a web request. Use it only after the
    app has checked that the user may do what the block does."""
    session, form_dict, user = frappe.local.session, frappe.local.form_dict, frappe.session.user
    sid, data = session.sid, session.data
    frappe.set_user("Administrator")
    try:
        yield
    finally:
        frappe.set_user(user)
        session.sid, session.data = sid, data
        frappe.local.form_dict = form_dict


def is_app_user(user=None):
    """Anyone who can read visits or cases may open the app."""
    user = user or frappe.session.user
    return bool(frappe.has_permission("KC Visit", "read", user=user)
                or frappe.has_permission("KC Case", "read", user=user))


def can_reset_passwords(user=None):
    user = user or frappe.session.user
    return user == "Administrator" or "System Manager" in frappe.get_roles(user)
