"""Remove "blocked module" rows (on Users and Module Profiles) that name this app's module with old casing
(e.g. "Kayanick CRM" from before the Module Def fix). They block nothing, but show a duplicate module."""
import frappe

MODULE = "KAYANICK CRM"


def execute():
    rows = frappe.db.sql(
        """select name, parenttype, parent, module from `tabBlock Module`
           where module = %s and binary module != %s""", (MODULE, MODULE), as_dict=True)
    for r in rows:
        frappe.db.delete("Block Module", {"name": r.name})
        print("  Stale module block removed: {0} {1} ({2})".format(r.parenttype, r.parent, r.module))
    if rows:
        frappe.clear_cache()
