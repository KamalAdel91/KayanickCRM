import frappe

WORKSPACE = "KAYANICK Sales"


def hide_extra_desktop_icons():
    # v16 creates a desktop icon for every public workspace; the app already has its own
    # "Kayanick CRM" icon, so the workspace one is hidden (runs on every migrate, idempotent)
    for name in frappe.get_all("Desktop Icon", filters={"label": WORKSPACE, "hidden": 0}, pluck="name"):
        frappe.db.set_value("Desktop Icon", name, "hidden", 1)
