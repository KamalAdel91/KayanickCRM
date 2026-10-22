"""Who sees what in Kayanick CRM, user by user, with what is set up wrong (the rules are in perms.py).

Used by the "KC Access" report and from the terminal:

    bench --site <site> execute kayanick_crm.access.check
"""
import frappe

from kayanick_crm.perms import employee_of, is_field_user, scope, sees_everything

ROLE_ORDER = ("System Manager", "KC Accounts", "KC Manager", "KC Viewer", "KC Rep")
ORDER_SUBMIT_ROLES = ("Sales User", "Sales Manager", "System Manager")  # can submit a Sales Order
KC_DOCTYPES = ("KC Visit", "KC Case", "KC Hospital", "KC Doctor", "KC Area", "KC Hospital Type", "KC Visit Purpose",
               "KC Visit Outcome", "KC Relationship Level", "KC Product")


def columns():
    return [
        {"label": "User", "fieldname": "user", "fieldtype": "Link", "options": "User", "width": 230},
        {"label": "Name", "fieldname": "full_name", "fieldtype": "Data", "width": 160},
        {"label": "Roles", "fieldname": "role", "fieldtype": "Data", "width": 190},
        {"label": "Employee", "fieldname": "employee", "fieldtype": "Link", "options": "Employee", "width": 130},
        {"label": "Reports To", "fieldname": "reports_to_name", "fieldtype": "Data", "width": 150},
        {"label": "Sees", "fieldname": "sees", "fieldtype": "Data", "width": 150},
        {"label": "Problem", "fieldname": "problem", "fieldtype": "Data", "width": 380},
    ]


def sees(user, employee):
    """The user's scope in words."""
    allowed = scope(user)
    if allowed is None:
        return "Everything"
    if not allowed:
        return "Nothing (not set up)"
    team = len(allowed - {employee})
    return "Own records" if not team else "Own + team ({0})".format(team)


def problems(user, roles, employee):
    allowed = scope(user)
    out = []
    if is_field_user(user, roles):
        if not employee:
            out.append("No active Employee with this user in User ID: sees nothing, can't log visits or attend cases")
        elif allowed == set():
            out.append("Not limited to a team yet: save the user's Employee record")
        elif "KC Manager" in roles and allowed == {employee}:
            out.append("A manager with nobody below them in Reports To: sees only their own records")
    elif sees_everything(user, roles) and allowed is not None:
        out.append("Should see everything but is limited by Create User Permission on their Employee: untick it")
    if "KC Accounts" in roles and not set(frappe.get_roles(user)) & set(ORDER_SUBMIT_ROLES):
        out.append("KC Accounts without Sales User: can't submit the reps' orders")
    return out


def rows():
    has_role = frappe.get_all("Has Role", filters={"parenttype": "User", "role": ["in", ROLE_ORDER]},
                              fields=["parent", "role"])
    roles = {}
    for r in has_role:
        if r.parent not in ("Administrator", "Guest"):
            roles.setdefault(r.parent, set()).add(r.role)
    users = {u.name: u for u in frappe.get_all("User", filters={"name": ["in", list(roles) or [""]], "enabled": 1},
                                                fields=["name", "full_name"])}
    names = dict(frappe.get_all("Employee", fields=["name", "employee_name"], as_list=True))

    out = []
    for user in sorted(users, key=lambda u: (users[u].full_name or u).lower()):
        mine = roles[user]
        employee = employee_of(user)
        reports_to = frappe.db.get_value("Employee", employee, "reports_to") if employee else None
        out.append({
            "user": user, "full_name": users[user].full_name,
            "role": ", ".join(r for r in reversed(ROLE_ORDER) if r in mine),
            "employee": employee, "reports_to_name": names.get(reports_to) if reports_to else None,
            "sees": sees(user, employee), "problem": "; ".join(problems(user, mine, employee)),
        })
    return out


def notes():
    """Site-wide settings and data that change who sees what."""
    out = []
    if frappe.get_system_settings("apply_strict_user_permissions"):
        out.append("Apply Strict User Permissions is ON (System Settings): planned cases are hidden from the reps. "
                   "Turn it off.")
    custom = sorted(set(frappe.get_all("Custom DocPerm", filters={"parent": ["in", KC_DOCTYPES]}, pluck="parent")))
    if custom:
        out.append("Role Permission Manager has its own rules for {0}, so the app's permissions are not used there. "
                   "Use Reset to Default in Role Permission Manager unless you meant it.".format(", ".join(custom)))
    without_rep = customers_without_rep()
    if without_rep:
        out.append("{0} customers with an open balance have no rep in their Sales Team, so only System Managers and "
                   "KC Viewers see their debt: {1}".format(len(without_rep), ", ".join(without_rep[:10])
                                                           + (" ..." if len(without_rep) > 10 else "")))
    return out


def customers_without_rep():
    from kayanick_crm.debt_api import customer_reps, open_invoices

    reps = customer_reps()
    return sorted({inv.customer for inv in open_invoices() if inv.outstanding_amount > 0 and inv.customer not in reps})


def message():
    items = notes()
    if not items:
        return ""
    return "<div class='text-danger'>" + "<br>".join(frappe.utils.escape_html(n) for n in items) + "</div>"


def _counts_as(user):
    """How many visits and cases this user can see."""
    current = frappe.session.user
    try:
        frappe.set_user(user)
        out = []
        for dt in ("KC Visit", "KC Case"):
            try:
                out.append(len(frappe.get_list(dt, pluck="name", limit_page_length=0)))
            except frappe.PermissionError:
                out.append("-")
        return out
    finally:
        frappe.set_user(current)


def check():
    """bench --site <site> execute kayanick_crm.access.check"""
    for n in notes():
        print("!", n)
    print("{0:<34} {1:<26} {2:<14} {3:<20} {4:>6} {5:>6}  {6}".format(
        "User", "Roles", "Employee", "Sees", "Visits", "Cases", "Problem"))
    for r in rows():
        visits, cases = _counts_as(r["user"])
        print("{0:<34} {1:<26} {2:<14} {3:<20} {4:>6} {5:>6}  {6}".format(
            r["user"], r["role"], r["employee"] or "-", r["sees"], visits, cases, r["problem"]))
