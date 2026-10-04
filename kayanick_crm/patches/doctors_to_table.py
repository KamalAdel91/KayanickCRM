"""Copies the old single `doctor` of every visit/case into the new Doctors table (one row each)."""
import frappe


def execute():
    for parent, child, folder in (("KC Visit", "KC Visit Doctor", "kc_visit_doctor"),
                                  ("KC Case", "KC Case Doctor", "kc_case_doctor")):
        frappe.reload_doc("kayanick_crm", "doctype", folder)
        has_rows = set(frappe.get_all(child, filters={"parenttype": parent}, pluck="parent", distinct=True))
        moved = 0
        for name, doctor in frappe.get_all(parent, filters={"doctor": ["is", "set"]}, fields=["name", "doctor"], as_list=True):
            if name in has_rows:
                continue
            row = frappe.get_doc({"doctype": child, "parent": name, "parenttype": parent,
                                  "parentfield": "doctors", "idx": 1, "doctor": doctor})
            row.db_insert()
            moved += 1
        print(f"{parent}: {moved} records moved to the Doctors table")
