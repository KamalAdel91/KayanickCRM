"""Customer debt for the mobile app.

A customer belongs to the rep in his Sales Team (Customer > Sales Team > Sales Person, whose Employee is the rep).
Who sees which customers follows the same Employee rule as visits and cases (see perms.py): a rep sees his own
customers and those of everyone below him in Reports To; users without Create User Permission see every customer,
including the ones with no rep.

Reps have no permission on Sales Invoice / Payment Entry, so the figures are read here, limited to those customers.
"""
import frappe
from frappe import _
from frappe.utils import date_diff, flt, getdate, today

from kayanick_crm.perms import is_app_user, visible_employees


def _check_app_user():
    if not is_app_user():
        frappe.throw(_("Not permitted"), frappe.PermissionError)


def customer_reps():
    """{customer: Employee} from the customers' Sales Team (the first row when there are several)."""
    rows = frappe.db.sql("""
        select st.parent customer, sp.employee
        from `tabSales Team` st join `tabSales Person` sp on sp.name = st.sales_person
        where st.parenttype = 'Customer' and st.parentfield = 'sales_team' and ifnull(sp.employee, '') != ''
        order by st.idx asc""", as_dict=True)
    out = {}
    for r in rows:
        out.setdefault(r.customer, r.employee)
    return out


def visible_customers(user=None):
    """(customers the user may see or None for all, {customer: Employee})."""
    reps = customer_reps()
    allowed = visible_employees(user)
    if allowed is None:
        return None, reps
    return {c for c, e in reps.items() if e in allowed}, reps


def _open_invoices(customers):
    """Submitted invoices with something outstanding (credit notes come in negative)."""
    filters = {"docstatus": 1, "outstanding_amount": ["!=", 0]}
    if customers is not None:
        filters["customer"] = ["in", list(customers) or [""]]
    return frappe.get_all("Sales Invoice", filters=filters,
                          fields=["name", "customer", "customer_name", "posting_date", "due_date", "grand_total",
                                  "outstanding_amount", "is_return"],
                          order_by="due_date asc, posting_date asc", limit_page_length=0)


def _unallocated_payments(customers):
    """Received payments not yet matched to an invoice: they reduce what the customer owes."""
    filters = {"docstatus": 1, "party_type": "Customer", "payment_type": "Receive", "unallocated_amount": [">", 0]}
    if customers is not None:
        filters["party"] = ["in", list(customers) or [""]]
    return frappe.get_all("Payment Entry", filters=filters,
                          fields=["name", "party", "posting_date", "unallocated_amount", "mode_of_payment"],
                          order_by="posting_date desc", limit_page_length=0)


def _days_overdue(due_date, day):
    return max(date_diff(day, due_date), 0) if due_date else 0


def _rep_names(employees):
    employees = sorted({e for e in employees if e})
    if not employees:
        return {}
    return dict(frappe.get_all("Employee", filters={"name": ["in", employees]}, fields=["name", "employee_name"],
                               as_list=True))


@frappe.whitelist()
def get_debts(employee=None):
    """Customers that owe money, biggest first, with the totals. `employee` narrows to one rep's customers
    (within what the user sees)."""
    _check_app_user()
    customers, reps = visible_customers()
    if employee:
        mine = {c for c, e in reps.items() if e == employee}
        customers = mine if customers is None else customers & mine

    day = getdate(today())
    by = {}

    def row(customer, name=None):
        if customer not in by:
            by[customer] = frappe._dict(customer=customer, customer_name=name or customer, employee=reps.get(customer),
                                        outstanding=0.0, overdue=0.0, unallocated=0.0, invoices=0, max_days=0)
        return by[customer]

    for inv in _open_invoices(customers):
        r = row(inv.customer, inv.customer_name)
        r.outstanding += flt(inv.outstanding_amount)
        if inv.outstanding_amount > 0:
            r.invoices += 1
            days = _days_overdue(inv.due_date, day)
            if days:
                r.overdue += flt(inv.outstanding_amount)
                r.max_days = max(r.max_days, days)
    for pe in _unallocated_payments(customers):
        row(pe.party).unallocated += flt(pe.unallocated_amount)

    names = _rep_names(r.employee for r in by.values())
    out = []
    for r in by.values():
        r.balance = r.outstanding - r.unallocated
        if abs(r.balance) < 0.005 and not r.invoices:
            continue
        r.rep_name = names.get(r.employee) or ""
        out.append(r)
    missing = [r.customer for r in out if r.customer_name == r.customer]
    if missing:  # customers that only have unallocated payments
        titles = dict(frappe.get_all("Customer", filters={"name": ["in", missing]}, fields=["name", "customer_name"],
                                     as_list=True))
        for r in out:
            r.customer_name = titles.get(r.customer) or r.customer_name
    out.sort(key=lambda r: -r.balance)

    totals = {k: sum(r[k] for r in out) for k in ("balance", "outstanding", "overdue", "unallocated")}
    totals["customers"] = sum(1 for r in out if r.balance > 0)
    return {"currency": _currency(), "totals": totals, "customers": out}


@frappe.whitelist()
def get_customer_debt(customer):
    """One customer's open invoices, unallocated payments and last payments received."""
    _check_app_user()
    customers, reps = visible_customers()
    if customers is not None and customer not in customers:
        frappe.throw(_("Not permitted"), frappe.PermissionError)
    if not frappe.db.exists("Customer", customer):
        frappe.throw(_("Customer {0} not found").format(customer))

    day = getdate(today())
    invoices = _open_invoices({customer})
    for inv in invoices:
        inv["days_overdue"] = _days_overdue(inv.due_date, day) if inv.outstanding_amount > 0 else 0
    unallocated = _unallocated_payments({customer})
    payments = frappe.get_all("Payment Entry",
                              filters={"docstatus": 1, "party_type": "Customer", "party": customer,
                                       "payment_type": "Receive"},
                              fields=["name", "posting_date", "paid_amount", "mode_of_payment"],
                              order_by="posting_date desc, creation desc", limit_page_length=5)

    outstanding = sum(flt(i.outstanding_amount) for i in invoices)
    unalloc = sum(flt(p.unallocated_amount) for p in unallocated)
    employee = reps.get(customer)
    return {
        "currency": _currency(),
        "customer": customer,
        "customer_name": frappe.db.get_value("Customer", customer, "customer_name") or customer,
        "rep_name": _rep_names([employee]).get(employee) or "",
        "outstanding": outstanding,
        "overdue": sum(flt(i.outstanding_amount) for i in invoices if i.days_overdue),
        "unallocated": unalloc,
        "balance": outstanding - unalloc,
        "invoices": invoices,
        "unallocated_payments": unallocated,
        "payments": payments,
    }


def _currency():
    company = frappe.defaults.get_global_default("company")
    return (company and frappe.get_cached_value("Company", company, "default_currency")) or ""
