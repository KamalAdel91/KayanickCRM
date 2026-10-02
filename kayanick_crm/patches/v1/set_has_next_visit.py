import frappe


def execute():
    # existing visits: answer the new question from the date they already have
    frappe.db.sql("""update `tabKC Visit` set has_next_visit = if(next_visit_date is null, 'No', 'Yes')
        where ifnull(has_next_visit, '') = ''""")
