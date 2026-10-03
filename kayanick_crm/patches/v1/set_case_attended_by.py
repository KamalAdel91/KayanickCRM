import frappe


def execute():
    # cases attended before this field existed were attended by the rep who logged them
    frappe.db.sql("""update `tabKC Case` set attended_by = sales_rep
        where attended = 1 and ifnull(attended_by, '') = ''""")
