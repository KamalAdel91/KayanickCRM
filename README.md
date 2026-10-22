# Kayanick CRM

Field sales CRM for Kayanick, built on Frappe / ERPNext v16.

- **Visits**: hospital + doctors visits (a relationship level per doctor), purpose, outcome, products discussed, next action and GPS check-in.
- **Cases**: hospital + doctors + products, notes and attachments, with a status (Planned / Attended / Cancelled) and a history of postponements and cancellations.
- **Customer debt**: what each customer owes, the overdue amounts by age, and the invoices.
- **Orders**: Sales Orders from the app, saved as a Draft for accounts to review. A rep places one for any
  customer, or a case makes one from its used products.
- **Mobile web app** at `/KayanickCRM` (installable to the home screen).

## Who can do what (the role)

| Role | Can |
|---|---|
| KC Rep | log visits and cases, place orders. Read hospitals, doctors and lists. |
| KC Manager | also edit and delete visits and cases. Add hospitals, doctors and list values. |
| KC Viewer | read only |
| KC Accounts | review and submit the Sales Orders the app makes (also needs Sales User). |
| System Manager | everything, and reset passwords from the app |

ERPNext's own roles (Sales Manager, Sales User, Stock User) give nothing in the app.

## Who sees what (the scope)

All the rules are in `kayanick_crm/perms.py`. The lists, the Today screen, the debt, the reports and the
notifications all use them.

Visits and cases carry an **Employee**: the rep who made the visit, or the person who attended the case.

| Role | Sees |
|---|---|
| KC Rep | their own records, and the records of everyone below them in **Reports To** |
| KC Manager | their own records and their team's: everyone below them in **Reports To** |
| KC Viewer, KC Accounts, System Manager | everything |

- The scope is Frappe's User Permission on Employee. ERPNext makes it when **Create User Permission** is ticked on
  the user's Employee.
- ERPNext ticks this box on every new Employee.
- For a KC Rep or KC Manager, the app keeps the box ticked. If someone unticks it, the app ticks it again when the
  User or the Employee is saved.
- To let a manager see everything, give the manager the KC Viewer role too.
- The app never unticks the box. Untick it yourself for a KC Viewer or a System Manager who has an Employee.
- A KC Rep or KC Manager without an active Employee sees nothing. The Today screen tells them why.
- A **planned** case has no Employee yet, so all reps see it. After a person attends it, the case belongs to that
  person. The rep who planned it, and the person who marked it attended, can still read it.
- Keep **Apply Strict User Permissions** (System Settings) off. If it is on, the reps do not see planned cases.

### Customer debt

A customer belongs to the rep in the customer's **Sales Team** (Customer > Sales Team > Sales Person, with the rep's
Employee on the Sales Person). A user who sees the rep's records also sees the rep's customers. Only KC Viewer and
System Manager see the customers that have no rep.

The Debt tab shows:

- the total owed, the overdue amounts by age, and what falls due this week
- for each customer: the open invoices, the payments not yet matched to an invoice, and the last payments
- a payment reminder, ready to send on WhatsApp

## Orders

Every Sales Order the app makes is a **Draft** with an **Invoice Type** (System / Cash). The **Kayanick Rep** field
shows the rep, and the **Order Source** field shows where it came from:

- **Direct Order**: the rep opens **Orders > New order** (or "New order" on a customer's debt page). The rep
  chooses any customer, the delivery date, the invoice type, the items, their quantities and prices.
- **Case**: the rep marks a case attended with used products. The rep enters the price of each product, the
  invoice type and the customer. The case shows the total, and the **Kayanick Case** field on the order links back
  to the case.

While the order is a Draft, it changes with the case. If the case goes back to planned, the Draft is deleted.
After accounts submit the order, the used products of the case cannot change.

KC Accounts get a notification for each new order. They review it in the Desk (prices, taxes, warehouse) and
submit it. Filter the Sales Order list by **Order Source** and **Invoice Type**. The rep and the rep's manager get a
notification when the order is approved (submitted) or cancelled.

The rep, the rep's manager, and the users who see everything see the order in the app.

## Notifications

A notification shows in the app and in the Desk bell. It also goes to the phone when **Enable Push Notification
Relay** is on.

A notification goes to the users who can see the record or the customer. The user who caused it does not get it.
A user who turns notifications off in **Notification Settings** gets none.

| Notification | When | Goes to |
|---|---|---|
| Positive visit / order expected | a rep logs the visit | everyone who sees the visit |
| New case | a user adds a case | everyone who sees the case |
| Case cancelled | a user cancels a planned case | everyone who sees the case |
| New order | a rep places an order, or a case with used products makes one | everyone who sees the rep, and KC Accounts |
| Order approved / cancelled | KC Accounts submit or cancel the order | everyone who sees the rep |
| Payment received / cancelled | a payment from a customer is submitted or cancelled | everyone who sees the customer |
| Invoice overdue | every day at 8:00 | everyone who sees the customer |
| Good morning | every day at 8:00 | each rep: their follow-ups and planned cases |
| Overdue debt this week | Sundays at 8:00 | each user: the customers they see |

If the scheduler stops, the next overdue alert also tells about the invoices that became overdue on the missed
days, up to 7 days back.

## Check the setup

The **KC Access** report (sidebar > Settings) lists every user, what each user sees, and what is set up wrong.
From the terminal:

```bash
bench --site <site> execute kayanick_crm.access.check
```

## Add a rep

1. Make a **User** with the **KC Rep** role.
2. Make an **Employee** with that user in **User ID** and the rep's manager in **Reports To**.

The rep then sees their own visits, cases and customers, and the planned cases. The manager sees the rep's records
and gets the rep's notifications.

## Install

```bash
bench get-app https://github.com/KamalAdel91/KayanickCRM --branch version-16
bench --site <site> install-app kayanick_crm
```

Requires ERPNext.

## Tests

On a test site that you can discard:

```bash
bench --site <test-site> run-tests --app kayanick_crm
```

On a site with real data, this command writes nothing. It skips the commits and rolls everything back:

```bash
bench --site <site> execute kayanick_crm.tests.run.run
```

## Mobile app development

```bash
cd frontend
npm install
npm run build   # writes kayanick_crm/public/frontend and kayanick_crm/www/kayanick.html
```

The built files are committed, so no Node build is needed on deploy.

## License

MIT
