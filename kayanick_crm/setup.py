import frappe

WORKSPACE = "KAYANICK Sales"
APP = "kayanick_crm"
MODULE = "KAYANICK CRM"
SIDEBAR = "Kayanick CRM"


# A Sales Order from the app: the rep who placed it (the app's lists and notifications follow it, see perms.scope),
# where it came from (a rep's direct order, or the used products of an attended case) and its invoice type.
# Employee User Permissions are ignored on kc_employee, so it changes nothing for Sales Order users in the Desk.
CUSTOM_FIELDS = {
    "Sales Order": [
        {"fieldname": "kc_employee", "label": "Kayanick Rep", "fieldtype": "Link", "options": "Employee",
         "insert_after": "customer_name", "read_only": 1, "no_copy": 1, "in_standard_filter": 1,
         "ignore_user_permissions": 1, "description": "The rep who placed this order from the Kayanick CRM app"},
        {"fieldname": "kc_source", "label": "Order Source", "fieldtype": "Select", "options": "\nDirect Order\nCase",
         "insert_after": "kc_employee", "read_only": 1, "no_copy": 1, "in_standard_filter": 1, "in_list_view": 1,
         "depends_on": "eval:doc.kc_source"},
        {"fieldname": "kc_case", "label": "Kayanick Case", "fieldtype": "Link", "options": "KC Case",
         "insert_after": "kc_source", "read_only": 1, "no_copy": 1, "depends_on": "eval:doc.kc_source=='Case'",
         "description": "The attended case whose used products this order bills"},
        {"fieldname": "kc_invoice_type", "label": "Invoice Type", "fieldtype": "Select", "options": "\nSystem\nCash",
         "insert_after": "kc_case", "no_copy": 1, "in_standard_filter": 1, "depends_on": "eval:doc.kc_source"},
    ],
}


def make_custom_fields():
    """Idempotent: runs after install and after every migrate."""
    from frappe.custom.doctype.custom_field.custom_field import create_custom_fields

    create_custom_fields(CUSTOM_FIELDS, update=True)


def fix_module_def():
    """The site's Module Def row is spelled "Kayanick CRM" and filed under erpnext, while modules.txt
    says "KAYANICK CRM". Frappe 16 places a module's sidebar and dock by that row, so the app's
    navigation landed under ERPNext. Make the row match the app exactly. Idempotent."""
    row = frappe.db.sql("select name, app_name, custom from `tabModule Def` where name = %s", MODULE, as_dict=True)
    if not row:
        return
    row = row[0]
    if row.name == MODULE and row.app_name == APP and not row.custom:
        return
    frappe.db.sql(
        "update `tabModule Def` set name = %s, module_name = %s, app_name = %s, custom = 0 where name = %s",
        (MODULE, MODULE, APP, row.name),
    )
    frappe.clear_cache()
    print("Fixed Module Def {0} ({1}) -> {2} ({3})".format(row.name, row.app_name, MODULE, APP))


def hide_extra_desktop_icons():
    # v16 creates a desktop icon for every public workspace; the app already has its own
    # "Kayanick CRM" icon, so the workspace one is hidden (runs on every migrate, idempotent)
    for name in frappe.get_all("Desktop Icon", filters={"label": WORKSPACE, "hidden": 0}, pluck="name"):
        frappe.db.set_value("Desktop Icon", name, "hidden", 1)


def remove_converted_sidebars():
    """Frappe's navigation update turned the old auto-made "KAYANICK Sales" workspace sidebar into a
    custom module of the same name (with its own sidebar, a dock entry and module blocks). The app
    ships its own sidebar ("Kayanick CRM"), so that conversion is undone here. Idempotent."""
    if not frappe.db.table_exists("Sidebar") or not frappe.db.exists("Sidebar", SIDEBAR):
        return

    changed = False
    custom_modules = [m for m in frappe.get_all("Module Def", filters={"custom": 1, "app_name": APP}, pluck="name")
                      if m.startswith(WORKSPACE)]
    for module in custom_modules:
        sidebars = frappe.get_all("Sidebar", filters={"module": module}, pluck="name")
        _drop_from_site_dock(set(sidebars))
        frappe.db.delete("Block Module", {"module": module})
        for ws in frappe.get_all("Workspace", filters={"module": module}, pluck="name"):
            frappe.db.set_value("Workspace", ws, "module", MODULE, update_modified=False)
        # deleting the module also deletes its sidebars and their customizations
        frappe.delete_doc("Module Def", module, force=True, ignore_permissions=True)
        print("Removed converted module", module)
        changed = True

    for name in frappe.get_all("Sidebar", filters={"module": MODULE, "standard": 0, "name": ["!=", SIDEBAR]},
                               pluck="name"):
        _drop_from_site_dock({name})
        frappe.delete_doc("Sidebar", name, force=True, ignore_permissions=True)
        print("Removed converted sidebar", name)
        changed = True

    if changed:
        frappe.clear_cache()


def _drop_from_site_dock(sidebars):
    """Remove dock entries that open these sidebars from the site's dock of this app."""
    if not sidebars:
        return
    try:
        from frappe.desk.doctype.dock.dock import get_dock, mounted_apps, resolve_app_dock, save_site_dock

        app = mounted_apps().get(APP, APP)
        if not get_dock(app):
            return
        rail = resolve_app_dock(app, upto="site", gated=False)
        keep = [e for e in rail if not (e.get("link_type") == "Sidebar" and e.get("link_to") in sidebars)]
        if len(keep) != len(rail):
            save_site_dock(app, keep)
            print("Removed dock entries", ", ".join(sorted(sidebars)))
    except Exception:
        frappe.log_error("Kayanick CRM: could not clean the dock")
