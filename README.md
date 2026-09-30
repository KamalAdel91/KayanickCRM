# Kayanick CRM

Field sales CRM for Kayanick, built on Frappe / ERPNext v16.

- **Visits**: hospital + doctor visits with purpose, outcome, relationship level, products discussed, next action and GPS check-in.
- **Cases**: ERPNext customer + products (same product list as visits), notes and attachments.
- **Mobile web app** at `/KayanickCRM` (installable to the home screen).
- **Team visibility** from the ERPNext **Sales Person** tree: a Sales Manager sees his own records and everyone below him; a Sales Rep sees only his own; System Manager sees all.

## Install

```bash
bench get-app https://github.com/KamalAdel91/KayanickCRM --branch version-16
bench --site <site> install-app kayanick_crm
```

Requires ERPNext.

## Setup

1. Give reps the **Sales Rep** role and managers the **Sales Manager** role.
2. Link each user to an **Employee** (User ID), and each Employee to a **Sales Person**; put reps under their manager's Sales Person.

## Mobile app development

```bash
cd frontend
npm install
npm run build   # writes kayanick_crm/public/frontend and kayanick_crm/www/kayanick.html
```

The built files are committed, so no Node build is needed on deploy.

## License

MIT
