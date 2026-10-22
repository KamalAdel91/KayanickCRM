"""Sales Orders from the mobile app. They come from two places (Sales Order.kc_source):

- Direct Order: a rep orders for any customer from the Orders tab.
- Case: a rep marks a case attended with used products. The case keeps its Sales Order in step while the order
  is a Draft, and deletes the Draft if the case no longer has used products. Once accounts submit the order, the
  case's used products are locked (KCCase.validate_order_lock).

Either way the order is a Draft with an invoice type (System / Cash). KC Accounts review it in the Desk and
submit it. An order belongs to the rep (Sales Order.kc_employee), and who sees it follows the app's one rule
(perms.scope). Reps have no permission on Sales Order, so the orders are read and written here.
"""
import json
from contextlib import contextmanager

import frappe
from frappe import _
from frappe.utils import add_days, flt, getdate, strip_html, today

from kayanick_crm.perms import FIELD_ROLES, as_administrator, is_app_user, require_employee, require_scope, scope

ORDER_FIELDS = ["name", "customer", "customer_name", "transaction_date", "delivery_date", "total", "grand_total",
                "currency", "status", "docstatus", "kc_employee", "kc_source", "kc_case", "kc_invoice_type",
                "creation"]
STATES = {"draft": 0, "approved": 1, "cancelled": 2}  # the app's tabs -> docstatus
INVOICE_TYPES = ("System", "Cash")


def can_order(user=None):
    """KC Rep / KC Manager place orders (their user needs an Employee)."""
    return bool(set(frappe.get_roles(user or frappe.session.user)) & set(FIELD_ROLES))


def _require_orderer():
    if not can_order():
        frappe.throw(_("Only reps and managers can place orders"), frappe.PermissionError)


def _require_app_user():
    if not is_app_user():
        frappe.throw(_("Not permitted"), frappe.PermissionError)


def _in_scope(employee):
    allowed = scope()
    return allowed is None or employee in allowed


def state(row):
    """What the app shows: waiting for review (Draft), the ERPNext status once submitted, or Cancelled."""
    if row.docstatus == 0:
        return "Waiting for review"
    if row.docstatus == 2:
        return "Cancelled"
    return row.status


@frappe.whitelist()
def search_customers(text: str | None = ""):
    """Any enabled customer: orders are not limited to the rep's own customers."""
    _require_orderer()
    text = (text or "").strip()[:60]
    kw = dict(filters={"disabled": 0}, fields=["name", "customer_name"], order_by="customer_name asc",
              limit_page_length=30)
    if text:
        kw["or_filters"] = [["customer_name", "like", "%" + text + "%"], ["name", "like", "%" + text + "%"]]
    return frappe.get_all("Customer", **kw)


@frappe.whitelist()
def search_items(text: str | None = ""):
    """Items that can be sold."""
    _require_orderer()
    text = (text or "").strip()[:60]
    kw = dict(filters={"disabled": 0, "has_variants": 0, "is_sales_item": 1}, fields=["name", "item_name", "stock_uom"],
              order_by="item_name asc", limit_page_length=50)
    if text:
        kw["or_filters"] = [["item_name", "like", "%" + text + "%"], ["name", "like", "%" + text + "%"]]
    return frappe.get_all("Item", **kw)


def _order_rows(items, delivery_date):
    rows = []
    for i, r in enumerate(items or [], 1):
        code = r.get("item_code")
        if not code:
            continue
        if not frappe.db.exists("Item", {"name": code, "disabled": 0, "is_sales_item": 1}):
            frappe.throw(_("Row {0}: {1} can't be sold").format(i, code))
        if flt(r.get("qty")) <= 0:
            frappe.throw(_("Row {0}: quantity must be more than zero").format(i))
        if flt(r.get("rate")) <= 0:
            frappe.throw(_("Row {0}: enter the price").format(i))
        rows.append({"item_code": code, "qty": flt(r.get("qty")), "rate": flt(r.get("rate")),
                     "delivery_date": delivery_date})
    if not rows:
        frappe.throw(_("Add at least one item"))
    return rows


def _fill(order, customer, employee, invoice_type, items, transaction_date, delivery_date):
    """Sets what the app decides on a new or Draft order."""
    order.update({
        "customer": customer, "customer_name": frappe.db.get_value("Customer", customer, "customer_name"),
        "transaction_date": transaction_date, "delivery_date": delivery_date, "kc_employee": employee,
        "kc_invoice_type": invoice_type,
    })
    order.set("items", _order_rows(items, delivery_date))
    order.set("sales_team", [])
    person = frappe.db.get_value("Sales Person", {"employee": employee, "enabled": 1}, "name")
    if person:
        order.append("sales_team", {"sales_person": person, "allocated_percentage": 100})


@contextmanager
def price_list_kept(item_codes):
    """The rep's price stays on the order. ERPNext's Stock Settings ("Update Existing Price List Rate", "Auto Insert
    Price List Rate If Missing") would copy it into the price list when the order is saved: such changes to these
    items' Item Prices are undone, in the same transaction."""
    fields = ["name", "price_list_rate", "modified", "modified_by"]
    filters = {"item_code": ["in", list(set(item_codes)) or [""]]}
    before = {r.name: r for r in frappe.get_all("Item Price", filters=filters, fields=fields)}
    yield
    for r in frappe.get_all("Item Price", filters=filters, fields=fields):
        old = before.get(r.name)
        if not old:
            frappe.db.delete("Item Price", {"name": r.name})
        elif flt(old.price_list_rate) != flt(r.price_list_rate):
            frappe.db.set_value("Item Price", r.name, {"price_list_rate": old.price_list_rate, "modified": old.modified,
                                                       "modified_by": old.modified_by}, update_modified=False)


def _save(order):
    """Saves the order for the current user, after the app checked their right to order.

    Reps have no permission on Sales Order or Item (it shows the valuation rate), and ERPNext checks Item while it
    fills the item details. So the order is saved as Administrator, and a new one is given back to the user as its
    owner. The price list is not touched (price_list_kept)."""
    user = frappe.session.user
    new = order.is_new()
    with as_administrator(), price_list_kept([row.item_code for row in order.items]):
        if new:
            order.insert(ignore_permissions=True)
        else:
            order.save(ignore_permissions=True)
    if new:
        frappe.db.set_value("Sales Order", order.name, {"owner": user, "modified_by": user}, update_modified=False)
    return order


@frappe.whitelist(methods=["POST"])
def create_order(payload):
    """A rep's direct order: a Draft Sales Order; KC Accounts get notified (notify.order_created)."""
    _require_orderer()
    require_scope()
    employee = require_employee()
    data = json.loads(payload) if isinstance(payload, str) else dict(payload or {})
    customer = data.get("customer")
    if not customer or not frappe.db.exists("Customer", {"name": customer, "disabled": 0}):
        frappe.throw(_("Choose the customer"))
    if data.get("invoice_type") not in INVOICE_TYPES:
        frappe.throw(_("Choose the invoice type: System or Cash"))
    delivery_date = getdate(data.get("delivery_date") or add_days(today(), 1))
    if delivery_date < getdate(today()):
        frappe.throw(_("The delivery date can't be in the past"))

    order = frappe.new_doc("Sales Order")
    order.kc_source = "Direct Order"
    _fill(order, customer, employee, data.get("invoice_type"), data.get("items"), getdate(today()), delivery_date)
    _save(order)
    notes = (data.get("notes") or "").strip()
    if notes:
        order.add_comment("Comment", notes)
    return {"name": order.name}


def sync_case_order(case):
    """Called after a case is saved (KCCase.on_update): makes, updates or deletes the Draft Sales Order of its
    used products. A case attended before Sales Orders existed (no customer or invoice type) gets none."""
    order = None
    if case.sales_order and frappe.db.exists("Sales Order", case.sales_order):
        order = frappe.get_doc("Sales Order", case.sales_order)
        if order.docstatus == 1:
            return  # approved: the case can't change it any more
        if order.docstatus == 2:
            order = None  # cancelled by accounts: a new one replaces it
    wanted = (case.status == "Attended" and case.used_products == "Yes" and case.used_items and case.customer
              and case.invoice_type)
    if not wanted:
        if order:
            case.db_set("sales_order", None, update_modified=False)
            with as_administrator():
                frappe.delete_doc("Sales Order", order.name, ignore_permissions=True)
        elif case.sales_order:
            case.db_set("sales_order", None, update_modified=False)
        return

    day = getdate(case.case_date)
    if not order:
        order = frappe.new_doc("Sales Order")
        order.update({"kc_source": "Case", "kc_case": case.name})
    _fill(order, case.customer, case.employee, case.invoice_type,
          [{"item_code": r.item_code, "qty": r.qty, "rate": r.rate} for r in case.used_items], day, day)
    _save(order)
    if case.sales_order != order.name:
        case.db_set("sales_order", order.name, update_modified=False)


@frappe.whitelist()
def get_orders(args=None):
    """The app's orders the user sees, newest first. args: status (draft / approved / cancelled), source
    (Direct Order / Case), employee, customer, start, limit."""
    from kayanick_crm.mobile import page_args

    _require_app_user()
    a = frappe._dict(frappe.parse_json(args) if isinstance(args, str) else (args or {}))
    filters = [["kc_employee", "is", "set"]]
    allowed = scope()
    if allowed is not None:
        filters.append(["kc_employee", "in", list(allowed) or [""]])
    if a.get("employee"):
        filters.append(["kc_employee", "=", a.employee])
    if a.get("customer"):
        filters.append(["customer", "=", a.customer])
    if a.get("source") in ("Direct Order", "Case"):
        filters.append(["kc_source", "=", a.source])
    if a.get("status") in STATES:
        filters.append(["docstatus", "=", STATES[a.status]])
    start, limit = page_args(a)
    rows = frappe.get_all("Sales Order", filters=filters, fields=ORDER_FIELDS, order_by="creation desc",
                          limit_start=start, limit_page_length=limit)
    names = _rep_names(r.kc_employee for r in rows)
    for r in rows:
        r["rep_name"] = names.get(r.kc_employee) or r.kc_employee
        r["state"] = state(r)
    return rows


@frappe.whitelist()
def get_order(name: str):
    _require_app_user()
    employee = frappe.db.get_value("Sales Order", name, "kc_employee")
    if not employee or not _in_scope(employee):
        frappe.throw(_("Not permitted"), frappe.PermissionError)
    doc = frappe.get_doc("Sales Order", name)
    notes = frappe.get_all("Comment", filters={"reference_doctype": "Sales Order", "reference_name": name,
                                               "comment_type": "Comment"},
                           fields=["content", "comment_email", "creation"], order_by="creation asc")
    return {
        "name": doc.name, "customer": doc.customer, "customer_name": doc.customer_name, "currency": doc.currency,
        "transaction_date": doc.transaction_date, "delivery_date": doc.delivery_date, "state": state(doc),
        "docstatus": doc.docstatus, "rep_name": _rep_names([employee]).get(employee) or employee,
        "source": doc.kc_source or "", "case": doc.kc_case or "", "invoice_type": doc.kc_invoice_type or "",
        "items": [{"item_code": i.item_code, "item_name": i.item_name, "qty": i.qty, "uom": i.uom, "rate": i.rate,
                   "amount": i.amount} for i in doc.items],
        "total": doc.total, "taxes": doc.total_taxes_and_charges, "grand_total": doc.grand_total,
        "notes": [{"text": strip_html(n.content or ""), "by": n.comment_email, "on": n.creation} for n in notes],
    }


def _rep_names(employees):
    employees = sorted({e for e in employees if e})
    if not employees:
        return {}
    return dict(frappe.get_all("Employee", filters={"name": ["in", employees]}, fields=["name", "employee_name"],
                               as_list=True))
