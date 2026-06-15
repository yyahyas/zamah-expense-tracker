read# Spec: Add Expense

## Overview
This feature implements the expense creation flow, allowing a logged-in user to record a new expense by filling in the amount, category, date, and an optional description. It replaces the existing stub at `GET /expenses/add` with a real form and handler, and adds the `create_expense` DB helper to `database/db.py`. The `expenses` table already exists in the schema — no migrations are needed.

## Depends on
- Step 01: Database Setup (expenses table exists)
- Step 03: Login and Logout (session management, login_required redirect pattern)

## Routes

- `GET /expenses/add` — render the add-expense form — logged-in only
- `POST /expenses/add` — validate and insert the expense, then redirect — logged-in only

## Database changes

No new tables or columns. A new helper function is needed:

- `create_expense(user_id, amount, category, date, description)` → inserts a row into the `expenses` table and returns the new row's `id`. Uses a parameterised INSERT.

## Templates

- **Create:** `templates/expenses/add.html` — full-page form extending `base.html`

## Files to change

- `app.py` — replace the `add_expense` stub with a real `GET|POST` route; import `create_expense` from `database.db`
- `database/db.py` — add `create_expense` helper

## Files to create

- `templates/expenses/add.html` — add-expense form page

## New dependencies

No new dependencies.

## Rules for implementation

- No SQLAlchemy or ORMs — raw SQLite only
- Parameterised queries only — no string interpolation in SQL
- Passwords hashed with werkzeug (not relevant here, but keep the pattern)
- Use CSS variables — never hardcode hex values
- All templates extend `base.html`
- Redirect to `/expenses` on successful submission
- On validation error, re-render the form with an inline error message and preserve the user's entered values
- `amount` must be a positive number (> 0); reject non-numeric input
- `date` must be a valid ISO date (`YYYY-MM-DD`); default the date input to today
- `category` must be one of the fixed list: Food, Transport, Bills, Health, Entertainment, Shopping, Other
- `description` is optional (max 200 chars displayed, no hard DB constraint)
- Auth guard: if `session["user_id"]` is absent, redirect to `/login`
- Do not add the `create_expense` import to the existing import line — update the existing import from `database.db` to include it

## Definition of done

- [ ] `GET /expenses/add` renders a form with fields: amount, category (dropdown), date, description
- [ ] The date field defaults to today's date on page load
- [ ] Submitting a valid form inserts a row in `expenses` and redirects to `/expenses`
- [ ] The new expense appears at the top of the `/expenses` list after submission
- [ ] Submitting with an empty amount shows an inline error and keeps other field values intact
- [ ] Submitting with a non-numeric amount shows an inline error
- [ ] Submitting with amount ≤ 0 shows an inline error
- [ ] Submitting with no category selected (or an invalid category) shows an inline error
- [ ] Submitting with an empty or invalid date shows an inline error
- [ ] Visiting `/expenses/add` while logged out redirects to `/login`
- [ ] PKR (₨) symbol is displayed next to the amount field
- [ ] The form is styled consistently with the rest of the app (CSS variables, no hardcoded hex)
