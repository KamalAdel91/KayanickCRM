"""Kayanick CRM v2: one person field per record (Employee), the app's own roles, a doctors table with a
relationship level per doctor, and a status + history on cases.

- roles: Sales Rep -> KC Rep; users with ERPNext's Sales Manager (not viewers) get KC Manager; the old
  Sales Rep role is removed and plain reps lose ERPNext's Sales User (the app doesn't need it)
- Role Permission Manager rules on the KC doctypes are reset, so the app's permissions apply
- Reports To is filled from the Sales Person tree (where HR left it empty)
- every plain KC Rep is limited to his own records (Create User Permission on his Employee)
- the User Permissions on Sales Person made for KC Visit / KC Case are removed
- data: visits and cases get their Employee, the rep who created a record becomes its owner, cases get a
  status, their postponements / cancellation move to the history, each doctor row gets the visit's level
- a case attended by someone else is shared (read only) with the rep who created it

Runs after the new schema is synced: the old columns are still in the tables, so they are read with SQL.
"""
import frappe
from frappe.permissions import add_user_permission
from frappe.utils.nestedset import rebuild_tree

OLD_REP_ROLE = "Sales Rep"
SKIP = {"Administrator", "Guest"}


def say(msg):
    print("  " + msg)


def execute():
    print("Kayanick CRM v2:")
    _ensure_roles()
    _reload_navigation()
    _move_roles()
    _reset_role_permission_manager()
    _reports_to_from_sales_person_tree()
    frappe.cache.delete_value("user_permissions")
    emp_by_user = _employees_by_user()
    _restrict_reps(emp_by_user)
    _drop_sales_person_permissions()
    frappe.cache.delete_value("user_permissions")
    _migrate_visits(emp_by_user)
    _migrate_cases(emp_by_user)
    _share_cases_with_creators()
    _drop_old_property_setters()
    frappe.clear_cache()
    print("Kayanick CRM v2: done. Check who sees what: bench --site <site> execute kayanick_crm.access.check")


# ---- roles ----

def _ensure_roles():
    for role in ("KC Rep", "KC Manager", "KC Viewer"):
        if not frappe.db.exists("Role", role):
            frappe.get_doc({"doctype": "Role", "role_name": role, "desk_access": 1}).insert(ignore_permissions=True)


def _reload_navigation():
    """Reports, dashboard and sidebar now name the new roles. Reloaded on purpose: the normal sync skips a file
    whose timestamp isn't newer than the copy on the site."""
    for folder, name in (("report", "sales_rep_activity"), ("report", "kc_access"),
                         ("workspace", "kayanick_sales"), ("sidebar", "kayanick_crm")):
        frappe.reload_doc("kayanick_crm", folder, name, force=True)


def _users_with(role):
    return set(frappe.get_all("Has Role", filters={"parenttype": "User", "role": role}, pluck="parent")) - SKIP


def _has(user, role):
    return frappe.db.exists("Has Role", {"parenttype": "User", "parent": user, "role": role})


def _add_role(user, role):
    if not _has(user, role):
        frappe.get_doc({"doctype": "Has Role", "parent": user, "parenttype": "User", "parentfield": "roles",
                        "role": role}).db_insert()
        return True


def _remove_role(user, role):
    if _has(user, role):
        frappe.db.delete("Has Role", {"parenttype": "User", "parent": user, "role": role})
        return True


def _move_roles():
    reps = _users_with(OLD_REP_ROLE)
    viewers = _users_with("KC Viewer")
    managers = _users_with("Sales Manager") - viewers
    admins = _users_with("System Manager")
    for user in sorted(reps):
        if _add_role(user, "KC Rep"):
            say("KC Rep -> " + user)
    for user in sorted(managers):
        if _add_role(user, "KC Manager"):
            say("KC Manager -> " + user)
        _remove_role(user, "KC Rep")
    for user in sorted(reps - managers - viewers - admins):
        if _remove_role(user, "Sales User"):
            say("Sales User removed from " + user + " (works in the app only)")
    if frappe.db.exists("Role", OLD_REP_ROLE):
        for dt in ("Has Role", "Custom DocPerm", "DocPerm"):
            frappe.db.delete(dt, {"role": OLD_REP_ROLE})
        frappe.delete_doc("Role", OLD_REP_ROLE, force=True, ignore_permissions=True)
        say("Role {0} removed".format(OLD_REP_ROLE))
    for user in reps | managers:
        frappe.clear_cache(user=user)


def _reset_role_permission_manager():
    for dt in frappe.get_all("DocType", filters={"module": "KAYANICK CRM", "istable": 0}, pluck="name"):
        if frappe.db.exists("Custom DocPerm", {"parent": dt}):
            frappe.db.delete("Custom DocPerm", {"parent": dt})
            frappe.clear_cache(doctype=dt)
            say("Role Permission Manager reset for {0}: the app's permissions apply".format(dt))


# ---- employees ----

def _employees_by_user():
    out = {}
    for e in frappe.get_all("Employee", filters={"user_id": ["is", "set"], "status": "Active"},
                            fields=["name", "user_id"], order_by="creation asc"):
        out.setdefault(e.user_id, e.name)
    return out


def _reports_to_from_sales_person_tree():
    """Each Sales Person's nearest parent that is a person becomes his Employee's Reports To (if empty)."""
    if not frappe.db.exists("DocType", "Sales Person"):
        return
    nodes = {n.name: n for n in frappe.get_all("Sales Person", fields=["name", "parent_sales_person", "employee"])}
    changed = False
    for n in nodes.values():
        if not n.employee or frappe.db.get_value("Employee", n.employee, "reports_to"):
            continue
        boss, parent, hops = None, n.parent_sales_person, 0
        while parent and parent in nodes and hops < 50:
            p = nodes[parent]
            if p.employee and p.employee != n.employee:
                boss = p.employee
                break
            parent, hops = p.parent_sales_person, hops + 1
        if not boss or _reports_up_to(boss, n.employee):
            continue
        frappe.db.set_value("Employee", n.employee, "reports_to", boss, update_modified=False)
        say("Reports To: {0} -> {1}".format(_emp_name(n.employee), _emp_name(boss)))
        changed = True
    if changed:
        rebuild_tree("Employee")


def _reports_up_to(employee, target):
    """True if `employee` already reports (directly or not) to `target` (setting the reverse would loop)."""
    seen = set()
    while employee and employee not in seen:
        if employee == target:
            return True
        seen.add(employee)
        employee = frappe.db.get_value("Employee", employee, "reports_to")
    return False


def _emp_name(employee):
    return frappe.db.get_value("Employee", employee, "employee_name") or employee


def _restrict_reps(emp_by_user):
    """A plain rep sees his own records only: Create User Permission on his Employee."""
    others = _users_with("KC Manager") | _users_with("KC Viewer") | _users_with("System Manager")
    for user in sorted(_users_with("KC Rep") - others):
        if not frappe.db.get_value("User", user, "enabled"):
            continue
        employee = emp_by_user.get(user)
        if not employee:
            say("WARNING: {0} has KC Rep but no active Employee with this User ID: "
                "he sees every visit and case until one is linked".format(user))
            continue
        company, ticked = frappe.db.get_value("Employee", employee, ["company", "create_user_permission"])
        if not ticked:
            frappe.db.set_value("Employee", employee, "create_user_permission", 1, update_modified=False)
            say("Create User Permission ticked on {0} ({1})".format(_emp_name(employee), user))
        add_user_permission("Employee", employee, user, ignore_permissions=True)
        if company:
            add_user_permission("Company", company, user, ignore_permissions=True)


def _drop_sales_person_permissions():
    rows = frappe.get_all("User Permission", filters={"allow": "Sales Person",
                                                      "applicable_for": ["in", ["KC Visit", "KC Case"]]},
                          fields=["name", "user"])
    for r in rows:
        frappe.db.delete("User Permission", {"name": r.name})
    for user in {r.user for r in rows}:
        frappe.clear_cache(user=user)
    if rows:
        say("{0} User Permissions on Sales Person (KC Visit / KC Case) removed".format(len(rows)))


# ---- data ----

def _cols(doctype):
    return set(frappe.db.get_table_columns(doctype))


_names = {}


def _employee_name(employee):
    if employee not in _names:
        _names[employee] = frappe.db.get_value("Employee", employee, "employee_name")
    return _names[employee]


def _migrate_visits(emp_by_user):
    cols = _cols("KC Visit")
    if "sales_rep" not in cols:
        return
    level = "relationship_level" if "relationship_level" in cols else "null"
    doctor = "doctor" if "doctor" in cols else "null"
    rows = frappe.db.sql(f"select name, owner, sales_rep, {level} as level, {doctor} as doctor from `tabKC Visit`",
                         as_dict=True)
    missing = set()
    for v in rows:
        values = {}
        employee = emp_by_user.get(v.sales_rep)
        if employee:
            values.update(employee=employee, employee_name=_employee_name(employee))
        else:
            missing.add(v.sales_rep)
        if v.sales_rep and v.owner != v.sales_rep:
            values["owner"] = v.sales_rep
        if values:
            frappe.db.set_value("KC Visit", v.name, values, update_modified=False)
        if v.doctor and not frappe.db.exists("KC Visit Doctor", {"parent": v.name, "parenttype": "KC Visit"}):
            frappe.get_doc({"doctype": "KC Visit Doctor", "parent": v.name, "parenttype": "KC Visit",
                            "parentfield": "doctors", "idx": 1, "doctor": v.doctor}).db_insert()
        if v.level:
            frappe.db.sql("""update `tabKC Visit Doctor` set relationship_level = %s
                where parent = %s and parenttype = 'KC Visit' and ifnull(relationship_level, '') = ''""",
                          (v.level, v.name))
    say("{0} visits moved to Employee".format(len(rows)))
    for user in sorted(u for u in missing if u):
        say("WARNING: visits of {0} have no Employee (no active Employee with this User ID)".format(user))


def _migrate_cases(emp_by_user):
    cols = _cols("KC Case")
    if "attended" not in cols:
        return
    pick = lambda c: c if c in cols else "null"  # noqa: E731
    rows = frappe.db.sql(f"""select name, owner, {pick('sales_rep')} as sales_rep, attended, {pick('attended_by')} as attended_by,
        {pick('cancelled')} as cancelled, {pick('cancelled_by')} as cancelled_by, {pick('cancelled_on')} as cancelled_on,
        {pick('cancel_reason')} as cancel_reason, {pick('doctor')} as doctor from `tabKC Case`""", as_dict=True)
    postponements = {}
    if frappe.db.table_exists("KC Case Postponement"):
        for p in frappe.db.sql("""select parent, from_date, from_time, to_date, to_time, reason, postponed_by, postponed_on
                from `tabKC Case Postponement` where parenttype = 'KC Case' order by parent, idx""", as_dict=True):
            postponements.setdefault(p.parent, []).append(p)
    counts, missing = {}, set()
    for c in rows:
        status = "Cancelled" if c.cancelled else "Attended" if c.attended else "Planned"
        counts[status] = counts.get(status, 0) + 1
        values = {"status": status, "employee": None, "employee_name": None}
        if status == "Attended":
            who = c.attended_by or c.sales_rep
            employee = emp_by_user.get(who)
            if employee:
                values.update(employee=employee, employee_name=_employee_name(employee))
            else:
                missing.add(who)
        if c.sales_rep and c.owner != c.sales_rep:
            values["owner"] = c.sales_rep
        frappe.db.set_value("KC Case", c.name, values, update_modified=False)

        if not frappe.db.exists("KC Case Log", {"parent": c.name, "parenttype": "KC Case"}):
            idx = 0
            for p in postponements.get(c.name, []):
                idx += 1
                _log_row(c.name, idx, "Postponed", p.reason, p.postponed_by, p.postponed_on,
                         from_date=p.from_date, from_time=p.from_time, to_date=p.to_date, to_time=p.to_time)
            if c.cancelled:
                _log_row(c.name, idx + 1, "Cancelled", c.cancel_reason, c.cancelled_by, c.cancelled_on)
        if c.doctor and not frappe.db.exists("KC Case Doctor", {"parent": c.name, "parenttype": "KC Case"}):
            frappe.get_doc({"doctype": "KC Case Doctor", "parent": c.name, "parenttype": "KC Case",
                            "parentfield": "doctors", "idx": 1, "doctor": c.doctor}).db_insert()
    say("{0} cases: {1}".format(len(rows), ", ".join("{0} {1}".format(n, s) for s, n in sorted(counts.items()))))
    say("{0} postponements moved to the case history".format(sum(len(v) for v in postponements.values())))
    for user in sorted(u for u in missing if u):
        say("WARNING: cases attended by {0} have no Employee: they stay visible to everyone".format(user))


def _log_row(case, idx, action, reason, by, on, **extra):
    frappe.get_doc({"doctype": "KC Case Log", "parent": case, "parenttype": "KC Case", "parentfield": "log",
                    "idx": idx, "action": action, "reason": reason, "done_by": by, "done_on": on, **extra}).db_insert()


def _share_cases_with_creators():
    from kayanick_crm.kayanick_crm.doctype.kc_case.kc_case import share_with_handlers

    before = frappe.db.count("DocShare", {"share_doctype": "KC Case"})
    for c in frappe.get_all("KC Case", filters={"status": "Attended", "employee": ["is", "set"]},
                            fields=["name", "owner", "employee"], limit_page_length=0):
        share_with_handlers(c.name, c.employee, {c.owner})
    added = frappe.db.count("DocShare", {"share_doctype": "KC Case"}) - before
    if added:
        say("{0} cases attended by someone else shared (read only) with the rep who created them".format(added))


def _drop_old_property_setters():
    for dt in ("KC Visit", "KC Case"):
        frappe.clear_cache(doctype=dt)
        meta = frappe.get_meta(dt)
        for ps in frappe.get_all("Property Setter", filters={"doc_type": dt, "field_name": ["is", "set"]},
                                 fields=["name", "field_name"]):
            if not meta.has_field(ps.field_name):
                frappe.delete_doc("Property Setter", ps.name, force=True, ignore_permissions=True)
                say("Old list setting removed: {0}.{1}".format(dt, ps.field_name))
