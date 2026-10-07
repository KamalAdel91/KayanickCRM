"""Who sees what in Kayanick CRM.

Used by the "KC Access" report and from the terminal:

    bench --site <site> execute kayanick_crm.access.check
"""
import frappe

from kayanick_crm.perms import visible_employees

ROLES = ("System Manager", "KC Manager", "KC Viewer", "KC Rep")  # highest first
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


def rows():
    has_role = frappe.get_all("Has Role", filters={"parenttype": "User", "role": ["in", ROLES]}, fields=["parent", "role"])
    roles = {}
    for r in has_role:
        if r.parent not in ("Administrator", "Guest"):
            roles.setdefault(r.parent, set()).add(r.role)
    users = {u.name: u for u in frappe.get_all("User", filters={"name": ["in", list(roles) or [""]], "enabled": 1},
                                                fields=["name", "full_name"])}
    employees = {}
    for e in frappe.get_all("Employee", filters={"user_id": ["in", list(users) or [""]], "status": "Active"},
                            fields=["name", "employee_name", "user_id", "reports_to"], order_by="creation asc"):
        employees.setdefault(e.user_id, e)
    names = dict(frappe.get_all("Employee", fields=["name", "employee_name"], as_list=True))

    out = []
    for user in sorted(users, key=lambda u: (users[u].full_name or u).lower()):
        mine = roles[user]
        role = next(r for r in ROLES if r in mine)  # the one that decides what he can do
        emp = employees.get(user)
        allowed = visible_employees(user)
        if allowed is None:
            sees = "Everything"
        else:
            team = len(allowed - {emp.name if emp else None})
            sees = "Own records" if not team else "Own + team ({0})".format(team)
        problems = []
        if role == "KC Rep" and allowed is None:
            problems.append("Sees everyone's records: tick Create User Permission on his Employee")
        if role in ("KC Rep", "KC Manager") and not emp:
            problems.append("No active Employee with this user in User ID: can't log visits or attend cases")
        if role == "KC Viewer" and allowed is not None:
            problems.append("A viewer limited to his own records: untick Create User Permission on his Employee")
        out.append({
            "user": user, "full_name": users[user].full_name, "role": ", ".join(r for r in reversed(ROLES) if r in mine),
            "employee": emp.name if emp else None,
            "reports_to_name": names.get(emp.reports_to) if emp and emp.reports_to else None,
            "sees": sees, "problem": "; ".join(problems),
        })
    return out


def notes():
    """Site-wide settings that change who sees what."""
    out = []
    if frappe.get_system_settings("apply_strict_user_permissions"):
        out.append("Apply Strict User Permissions is ON (System Settings): planned cases are hidden from the reps. "
                   "Turn it off.")
    custom = sorted(set(frappe.get_all("Custom DocPerm", filters={"parent": ["in", KC_DOCTYPES]}, pluck="parent")))
    if custom:
        out.append("Role Permission Manager has its own rules for {0}, so the app's permissions are not used there. "
                   "Use Reset to Default in Role Permission Manager unless you meant it.".format(", ".join(custom)))
    return out


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
    print("{0:<34} {1:<26} {2:<14} {3:<16} {4:>6} {5:>6}  {6}".format(
        "User", "Roles", "Employee", "Sees", "Visits", "Cases", "Problem"))
    for r in rows():
        visits, cases = _counts_as(r["user"])
        print("{0:<34} {1:<26} {2:<14} {3:<16} {4:>6} {5:>6}  {6}".format(
            r["user"], r["role"], r["employee"] or "-", r["sees"], visits, cases, r["problem"]))
