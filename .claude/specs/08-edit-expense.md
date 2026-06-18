# Spec: Edit Expense

## Overview
This feature implements the expense editing flow, allowing a logged-in user to update an existing expense's amount, category, date, and description. It replaces the stub at `GET /expenses/<int:id>/edit` with a real pre-filled form and POST handler that validates input, enforces ownership (the expense must belong to the session user), and persists changes via a parameterised UPDATE query. No new tables or columns are required — the `expenses` table already has all necessary fields.

## Depends on
- Step 01: Database Setup (expenses table exists)
- Step 03: Login and Logout (session management, login_required redirect pattern)
- Step 07: Add Expense (establishes the expense form pattern and `VALID_CATEGORIES` list)

## Routes

- `GET /expenses/<int:id>/edit` — render the edit form pre-filled with the expense's current values — logged-in only
- `POST /expenses/<int:id>/edit` — validate input and update the expense row, then redirect — logged-in only

## Database changes

No new tables or columns. Two new helper functions are needed in `database/db.py`:

- `get_expense_by_id(expense_id)` — fetches a single expense row by `id`; returns `None` if not found
- `update_expense(expense_id, amount, category, date, description)` — executes a parameterised UPDATE on the `expenses` table

## Templates

- **Create:** `templates/expenses/edit.html` — edit form extending `base.html`, pre-filled with the expense's current values

## Files to change

- `app.py` — replace the `edit_expense` stub with a real `GET|POST` route; add `get_expense_by_id` and `update_expense` to the existing import from `database.db`
- `database/db.py` — add `get_expense_by_id` and `update_expense` helpers

## Files to create

- `templates/expenses/edit.html` — edit expense form page

## New dependencies

No new dependencies.

## Rules for implementation

- No SQLAlchemy or ORMs — raw SQLite only
- Parameterised queries only — no string interpolation in SQL
- Passwords hashed with werkzeug (not applicable here, but keep the pattern)
- Use CSS variables — never hardcode hex values
- All templates extend `base.html`
- Auth guard: if `session["user_id"]` is absent, redirect to `/login`
- Ownership guard: if the expense's `user_id` does not match `session["user_id"]`, return `abort(403)`
- If the expense `id` does not exist, return `abort(404)`
- On successful update, redirect to `/expenses`
- On validation error, re-render the form with an inline error message and preserve the user's entered values
- `amount` must be a positive number (> 0); reject non-numeric and non-positive input
- `date` must be a valid ISO date (`YYYY-MM-DD`)
- `category` must be one of `VALID_CATEGORIES` (already defined in `app.py` — reuse it, do not redefine)
- `description` is optional
- The route must handle both `GET` and `POST` methods — add `methods=["GET", "POST"]` to the decorator
- Do not add a new import line — update the existing `from database.db import ...` line to include the two new helpers

## Definition of done

- [ ] `GET /expenses/<int:id>/edit` renders a form pre-filled with the expense's current amount, category, date, and description
- [ ] The category dropdown shows the current category as selected
- [ ] Submitting a valid form updates the expense row in the DB and redirects to `/expenses`
- [ ] The updated values appear correctly on the `/expenses` list after submission
- [ ] Submitting with an empty amount shows an inline error and preserves other field values
- [ ] Submitting with a non-numeric or non-positive amount shows an inline error
- [ ] Submitting with an invalid or empty date shows an inline error
- [ ] Submitting with an invalid category shows an inline error
- [ ] Visiting `/expenses/<id>/edit` while logged out redirects to `/login`
- [ ] Visiting `/expenses/<id>/edit` for an expense owned by a different user returns 403
- [ ] Visiting `/expenses/9999/edit` for a non-existent expense returns 404
- [ ] PKR (₨) symbol is displayed next to the amount field
- [ ] The form is styled consistently with `expenses/add.html` (CSS variables, no hardcoded hex)
