import frappe
from frappe import _


def validate_stock_items(doc, method=None):
    for row in doc.get("used_items") or []:
        if row.item_code and not frappe.db.get_value("Item", row.item_code, "is_stock_item"):
            frappe.throw(_("Row {0}: Item {1} is not a stock item").format(row.idx, row.item_code))
