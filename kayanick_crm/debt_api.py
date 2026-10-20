"""Customer debt for the mobile app.

A customer belongs to the rep in his Sales Team (Customer > Sales Team > Sales Person, whose Employee is the rep).

Who sees which customers:
- A rep (no KC Manager / KC Viewer / System Manager role) sees only his own customers, whatever his User
  Permissions say. A rep with no Employee sees none.
- Everyone else follows the Employee rule of visits and cases (see perms.py): a manager with Create User Permission
  sees his own and his team's customers; users without it see every customer, including the ones with no rep.

Reps have no permission on Sales Invoice / Payment Entry, so the figures are read here, limited to those customers.
"""
import frappe
from frappe import _
from frappe.utils import add_days, date_diff, flt, getdate, today

from kayanick_crm.perms import employee_of, is_app_user, visible_employees

BEYOND_OWN_ROLES = ("System Manager", "KC Manager", "KC Viewer")
AGING = (("1-30", 30), ("31-60", 60), ("61-90", 90), ("90+", None))  # days overdue
DUE_SOON_DAYS = 7


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
    user = user or frappe.session.user
    reps = customer_reps()
    if user != "Administrator" and not set(frappe.get_roles(user)) & set(BEYOND_OWN_ROLES):
        me = employee_of(user)
        return {c for c, e in reps.items() if me and e == me}, reps
    allowed = visible_employees(user)
    if allowed is None:
        return None, reps
    return {c for c, e in reps.items() if e in allowed}, reps


def open_invoices(customers=None):
    """Submitted invoices with something outstanding (credit notes come in negative). None: all customers."""
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


def days_overdue(due_date, day):
    return max(date_diff(day, due_date), 0) if due_date else 0


def aging_bucket(days):
    for label, upto in AGING:
        if upto is None or days <= upto:
            return label


def rep_names(employees):
    employees = sorted({e for e in employees if e})
    if not employees:
        return {}
    return dict(frappe.get_all("Employee", filters={"name": ["in", employees]}, fields=["name", "employee_name"],
                               as_list=True))


def debts(customers, reps):
    """Per customer: balance, overdue, aging and what falls due soon; plus the totals. customers None: all."""
    day = getdate(today())
    soon = getdate(add_days(day, DUE_SOON_DAYS))
    by = {}

    def row(customer, name=None):
        if customer not in by:
            by[customer] = frappe._dict(customer=customer, customer_name=name or customer, employee=reps.get(customer),
                                        outstanding=0.0, overdue=0.0, due_soon=0.0, unallocated=0.0, invoices=0,
                                        max_days=0, next_due=None)
        return by[customer]

    aging = {label: 0.0 for label, _u in AGING}
    for inv in open_invoices(customers):
        r = row(inv.customer, inv.customer_name)
        amount = flt(inv.outstanding_amount)
        r.outstanding += amount
        if amount <= 0:
            continue
        r.invoices += 1
        days = days_overdue(inv.due_date, day)
        if days:
            r.overdue += amount
            r.max_days = max(r.max_days, days)
            aging[aging_bucket(days)] += amount
        elif inv.due_date and getdate(inv.due_date) <= soon:
            r.due_soon += amount
            r.next_due = min(r.next_due or inv.due_date, inv.due_date)
    for pe in _unallocated_payments(customers):
        row(pe.party).unallocated += flt(pe.unallocated_amount)

    names = rep_names(r.employee for r in by.values())
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

    totals = {k: sum(r[k] for r in out) for k in ("balance", "outstanding", "overdue", "due_soon", "unallocated")}
    totals["customers"] = sum(1 for r in out if r.balance > 0)
    totals["overdue_customers"] = sum(1 for r in out if r.overdue > 0)
    return out, totals, [{"label": label, "amount": aging[label]} for label, _u in AGING]


@frappe.whitelist()
def get_debts(employee=None):
    """Customers that owe money, biggest first, with the totals and aging. `employee` narrows to one rep's
    customers (within what the user sees)."""
    _check_app_user()
    customers, reps = visible_customers()
    all_reps = sorted({reps[c] for c in (customers if customers is not None else reps)})
    if employee:
        mine = {c for c, e in reps.items() if e == employee}
        customers = mine if customers is None else customers & mine
    rows, totals, aging = debts(customers, reps)
    names = rep_names(all_reps)
    rep_filter = sorted(({"employee": e, "name": names.get(e) or e} for e in all_reps), key=lambda x: x["name"].lower())
    return {"currency": currency(), "totals": totals, "aging": aging, "customers": rows,
            "reps": rep_filter if len(rep_filter) > 1 else []}


def debt_summary(user=None):
    """Overdue figures for the Today screen card."""
    customers, reps = visible_customers(user)
    _rows, totals, _aging = debts(customers, reps)
    return {"overdue": totals["overdue"], "customers": totals["overdue_customers"], "due_soon": totals["due_soon"],
            "currency": currency()}


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
    invoices = open_invoices({customer})
    for inv in invoices:
        inv["days_overdue"] = days_overdue(inv.due_date, day) if inv.outstanding_amount > 0 else 0
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
        "currency": currency(),
        "customer": customer,
        "customer_name": frappe.db.get_value("Customer", customer, "customer_name") or customer,
        "rep_name": rep_names([employee]).get(employee) or "",
        "outstanding": outstanding,
        "overdue": sum(flt(i.outstanding_amount) for i in invoices if i.days_overdue),
        "unallocated": unalloc,
        "balance": outstanding - unalloc,
        "invoices": invoices,
        "unallocated_payments": unallocated,
        "payments": payments,
    }


def currency():
    company = frappe.defaults.get_global_default("company")
    return (company and frappe.get_cached_value("Company", company, "default_currency")) or ""
