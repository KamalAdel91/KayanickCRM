import frappe

WORKSPACE = "KAYANICK Sales"


def hide_extra_desktop_icons():
    # v16 creates a desktop icon for every public workspace; the app already has its own
    # "Kayanick CRM" icon, so the workspace one is hidden (runs on every migrate, idempotent)
    for name in frappe.get_all("Desktop Icon", filters={"label": WORKSPACE, "hidden": 0}, pluck="name"):
        frappe.db.set_value("Desktop Icon", name, "hidden", 1)


SIDEBAR = "Kayanick CRM"
MODULE = "KAYANICK CRM"


def remove_converted_sidebars():
    """Frappe 16 turned the old auto-made "KAYANICK Sales" workspace sidebar into a site Sidebar of this
    module. The app ships its own ("Kayanick CRM"), so any other non-standard sidebar of the module is removed."""
    if not frappe.db.table_exists("Sidebar") or not frappe.db.exists("Sidebar", SIDEBAR):
        return
    for name in frappe.get_all("Sidebar", filters={"module": MODULE, "standard": 0, "name": ["!=", SIDEBAR]},
                               pluck="name"):
        frappe.delete_doc("Sidebar", name, force=True, ignore_permissions=True)
        print("Removed converted sidebar", name)
    frappe.clear_cache()
