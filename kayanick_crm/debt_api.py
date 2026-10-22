"""Customer debt for the mobile app.

A customer belongs to the rep in the customer's Sales Team (Customer > Sales Team > Sales Person, whose Employee is
the rep). Whoever sees the rep's visits and cases sees the rep's customers (perms.scope): a rep their own, a manager
their team's, KC Viewer / System Manager every customer, including the ones with no rep.

Reps have no permission on Sales Invoice / Payment Entry, so the figures are read here, limited to those customers.
"""
import frappe
from frappe import _
from frappe.utils import add_days, date_diff, flt, getdate, today

from kayanick_crm.perms import is_app_user, scope

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
    """(customers the user may see or None for all, {customer: Employee}): those of the reps in the user's scope."""
    reps = customer_reps()
    allowed = scope(user or frappe.session.user)
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


def _invoice(name):
    """A submitted invoice of a customer the user sees."""
    _check_app_user()
    row = frappe.db.get_value("Sales Invoice", name, ["customer", "docstatus"], as_dict=True)
    customers, _reps = visible_customers()
    if not row or row.docstatus != 1 or (customers is not None and row.customer not in customers):
        frappe.throw(_("Not permitted"), frappe.PermissionError)
    return frappe.get_doc("Sales Invoice", name)


def _settled_by(name):
    """What paid this invoice down: payment entries, journal entries and credit notes, oldest first."""
    rows = frappe.db.sql("""
        select pe.name, 'Payment' kind, pe.posting_date, ref.allocated_amount amount, pe.mode_of_payment
        from `tabPayment Entry Reference` ref join `tabPayment Entry` pe on pe.name = ref.parent
        where ref.reference_doctype = 'Sales Invoice' and ref.reference_name = %(name)s and pe.docstatus = 1
        union all
        select je.name, 'Journal Entry', je.posting_date, jea.credit_in_account_currency - jea.debit_in_account_currency, null
        from `tabJournal Entry Account` jea join `tabJournal Entry` je on je.name = jea.parent
        where jea.reference_type = 'Sales Invoice' and jea.reference_name = %(name)s and je.docstatus = 1
        union all
        select name, 'Credit note', posting_date, -grand_total, null
        from `tabSales Invoice` where return_against = %(name)s and docstatus = 1
        order by posting_date asc""", {"name": name}, as_dict=True)
    return [r for r in rows if flt(r.amount)]


@frappe.whitelist()
def get_invoice(name):
    """One invoice: items, taxes, payment schedule and what was paid against it."""
    doc = _invoice(name)
    day = getdate(today())
    outstanding = flt(doc.outstanding_amount)
    return {
        "name": doc.name, "customer": doc.customer, "customer_name": doc.customer_name, "currency": doc.currency,
        "posting_date": doc.posting_date, "due_date": doc.due_date, "is_return": doc.is_return,
        "return_against": doc.return_against, "po_no": doc.po_no, "status": doc.status,
        "subject": doc.get("custom_subject") or "", "notes": doc.get("custom_notes") or doc.remarks or "",
        "days_overdue": days_overdue(doc.due_date, day) if outstanding > 0 else 0,
        "total": doc.total, "discount_amount": doc.discount_amount, "grand_total": doc.grand_total,
        "outstanding": outstanding, "paid": flt(doc.grand_total) - outstanding,
        "items": [{"item_code": i.item_code, "item_name": i.item_name, "qty": i.qty, "uom": i.uom, "rate": i.rate,
                   "amount": i.amount, "discount_percentage": i.discount_percentage} for i in doc.items],
        "taxes": [{"description": t.description, "rate": t.rate, "amount": t.tax_amount,
                   "included": t.included_in_print_rate} for t in doc.taxes if flt(t.tax_amount)],
        "schedule": [{"due_date": p.due_date, "amount": p.payment_amount, "outstanding": p.outstanding}
                     for p in doc.payment_schedule] if len(doc.payment_schedule) > 1 else [],
        "settled_by": _settled_by(doc.name),
    }


@frappe.whitelist()
def invoice_pdf(name):
    """The printed invoice as a PDF. Reps can't print Sales Invoices themselves, so the print permission check is
    skipped here, after _invoice checked the customer is his."""
    doc = _invoice(name)
    # the Sales Invoice default (Customize Form > Default Print Format), as the Desk prints it; Standard when unset
    print_format = frappe.get_meta("Sales Invoice").default_print_format or None
    if print_format and not frappe.db.exists("Print Format", {"name": print_format, "disabled": 0}):
        print_format = None
    frappe.flags.ignore_print_permissions = True
    try:
        pdf = frappe.get_print("Sales Invoice", doc.name, print_format=print_format, doc=doc, as_pdf=True)
    finally:
        frappe.flags.ignore_print_permissions = False
    frappe.local.response.filename = doc.name + ".pdf"
    frappe.local.response.filecontent = pdf
    frappe.local.response.type = "pdf"


def currency():
    company = frappe.defaults.get_global_default("company")
    return (company and frappe.get_cached_value("Company", company, "default_currency")) or ""
