# Kayanick CRM

Field sales CRM for Kayanick, built on Frappe / ERPNext v16.

- **Visits**: hospital + doctors visits (a relationship level per doctor), purpose, outcome, products discussed, next action and GPS check-in.
- **Cases**: hospital + doctors + products, notes and attachments, with a status (Planned / Attended / Cancelled) and a history of postponements and cancellations.
- **Mobile web app** at `/KayanickCRM` (installable to the home screen).

## Who can do what (roles)

| Role | Can |
|---|---|
| KC Rep | log his visits and cases; read hospitals, doctors and lists |
| KC Manager | also edit and delete visits and cases, add hospitals, doctors and list values |
| KC Viewer | read only |
| System Manager | everything, and reset passwords from the app |

ERPNext's own roles (Sales Manager, Sales User, Stock User) give nothing in the app.

## Who sees what (the Employee)

Visits and cases carry an **Employee**: the rep who made the visit, or whoever attended the case.

- A user whose Employee has **Create User Permission** ticked sees his own records and those of everyone below
  him in **Reports To**. That is every rep.
- A user without it (owners, managers who see everything, viewers, admins) sees everything.
- A **planned** case has no Employee yet, so the whole team sees it. Once attended it belongs to whoever attended
  it; the rep who planned it (and whoever marked it attended) keep read access.
- Keep **Apply Strict User Permissions** (System Settings) off, or planned cases disappear for the reps.

The **KC Access** report (sidebar > Settings) lists every user with what he sees and flags mistakes. From the
terminal: `bench --site <site> execute kayanick_crm.access.check`

## Install

```bash
bench get-app https://github.com/KamalAdel91/KayanickCRM --branch version-16
bench --site <site> install-app kayanick_crm
```

Requires ERPNext.

## Adding a rep

1. **User** with the **KC Rep** role.
2. **Employee** with that user in **User ID** and his manager in **Reports To** (Create User Permission stays ticked).

That's all: he sees his own visits and cases plus the planned ones, and his manager gets his notifications.

## Mobile app development

```bash
cd frontend
npm install
npm run build   # writes kayanick_crm/public/frontend and kayanick_crm/www/kayanick.html
```

The built files are committed, so no Node build is needed on deploy.

## License

MIT
