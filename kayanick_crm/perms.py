"""Row-level access for KC Visit and KC Case, driven by ERPNext's Sales Person tree.

User -> Employee (user_id) -> Sales Person (employee). A Sales Manager sees himself plus every
Sales Person below his node(s) in the tree. A Sales Rep sees only himself. System Manager sees all.
"""
import frappe

ADMIN_ROLES = {"System Manager"}


def _is_admin(user):
    return user == "Administrator" or bool(ADMIN_ROLES & set(frappe.get_roles(user)))


def _employee_users(employees):
    if not employees:
        return set()
    return {u for u in frappe.get_all("Employee", filters={"name": ["in", list(employees)]}, pluck="user_id") if u}


def visible_reps(user=None):
    """None means no restriction; otherwise the set of users whose records this user may see."""
    user = user or frappe.session.user
    if _is_admin(user):
        return None
    cache = getattr(frappe.local, "kc_visible_reps", None)
    if cache is None:
        cache = frappe.local.kc_visible_reps = {}
    if user in cache:
        return cache[user]
    reps = {user}
    if "Sales Manager" in frappe.get_roles(user):
        employees = frappe.get_all("Employee", filters={"user_id": user}, pluck="name")
        nodes = frappe.get_all("Sales Person", filters={"employee": ["in", employees], "enabled": 1},
                               fields=["lft", "rgt"]) if employees else []
        for n in nodes:
            below = frappe.get_all("Sales Person",
                                   filters={"lft": [">", n.lft], "rgt": ["<", n.rgt], "enabled": 1, "employee": ["is", "set"]},
                                   pluck="employee")
            reps |= _employee_users(below)
    cache[user] = reps
    return reps


def _condition(doctype, user):
    reps = visible_reps(user)
    if reps is None:
        return ""
    return "`tab%s`.`sales_rep` in (%s)" % (doctype, ", ".join(frappe.db.escape(r) for r in sorted(reps)))


def _allowed(doc, user):
    reps = visible_reps(user)
    return reps is None or doc.get("sales_rep") in reps


def visit_query(user=None):
    return _condition("KC Visit", user or frappe.session.user)


def case_query(user=None):
    return _condition("KC Case", user or frappe.session.user)


def visit_has_permission(doc, user=None, permission_type=None):
    user = user or frappe.session.user
    if permission_type == "create":
        return True
    return _allowed(doc, user)


def case_has_permission(doc, user=None, permission_type=None):
    user = user or frappe.session.user
    if permission_type == "create":
        return True
    return _allowed(doc, user)
