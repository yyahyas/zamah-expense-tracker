# Spec: Date Filter for Profile Page

## Overview

Extend the profile page with a personal expense summary section that lets the logged-in user filter their expenses by a date range. A compact "from / to" date picker form submits via `GET` so the filtered view is bookmarkable and shareable. The route reads `from_date` and `to_date` query params, queries only the matching expenses, and passes them — along with a filtered total — to the template. When no params are provided the section defaults to showing the current calendar month. This gives users a quick "how much did I spend between X and Y?" view without leaving their profile.

## Depends on

- Step 01 — Database setup (`expenses` table, `get_db()`)
- Step 04 — Profile page template (`templates/profile.html`, base layout)
- Step 05 — Backend routes for profile page (`GET /profile` route structure, auth pattern)

## Routes

- `GET /profile` — extended to accept optional `?from_date=YYYY-MM-DD&to_date=YYYY-MM-DD` query params; fetches filtered expenses and computes a filtered total; passes `expenses`, `filtered_total`, `from_date`, and `to_date` to the template — logged-in

No new routes.

## Database changes

One new function in `database/db.py`:

- `get_expenses_filtered(user_id, from_date, to_date)` — returns all expenses for `user_id` where `date` is between `from_date` and `to_date` (inclusive), ordered `date DESC`. Both date params are plain strings in `YYYY-MM-DD` format. Uses parameterised queries.

No new tables or columns.

## Templates

- **Modify:** `templates/profile.html` — add a new "Expense History" section below the existing account-details and password-change forms. The section contains:
  1. A filter form (`method="get" action="/profile"`) with two `<input type="date">` fields (`name="from_date"`, `name="to_date"`) pre-populated from the current query params (or defaulting to the first and last day of the current month), and a submit button labelled "Filter".
  2. A summary line showing the filtered total: e.g. "Total: ₨ 12,350.00 across 4 expenses".
  3. A table listing the filtered expenses with columns: Date, Category, Description, Amount (PKR).
  4. An empty-state message ("No expenses found for this period.") when the filtered list is empty.

## Files to change

- `app.py` — update `GET /profile` (`profile` function) to read `from_date` and `to_date` from `request.args`, default both to the first and last day of the current month when absent, call `get_expenses_filtered`, compute `filtered_total`, and pass all four values to `render_template`
- `database/db.py` — add `get_expenses_filtered(user_id, from_date, to_date)`
- `templates/profile.html` — add the Expense History section as described above

## Files to create

No new files.

## New dependencies

No new dependencies.

## Rules for implementation

- No SQLAlchemy or ORMs — raw SQLite with parameterised queries only
- All DB access through `database/db.py` only — never inline SQLite in `app.py`
- Passwords hashed with `werkzeug.security.generate_password_hash` (unchanged from earlier steps)
- All templates extend `base.html`
- Use CSS variables — never hardcode hex values
- Date defaulting must happen in `app.py`, not in the template — pass concrete `from_date` / `to_date` strings to the template always
- `from_date` and `to_date` values must be validated as valid `YYYY-MM-DD` strings before being passed to the DB function; if either is malformed, fall back to the current-month defaults silently (do not show an error)
- `filtered_total` must be computed in Python from the returned rows (`sum(row['amount'] for row in expenses)`), not via a separate SQL query
- Amount display: format as `₨ {:,.2f}` — always two decimal places, thousands separator
- The filter form must preserve both date values as `value=` attributes so the inputs are pre-filled on page load
- The existing account-details and password sections must remain fully functional and visually unchanged

## Definition of done

- [ ] Visiting `GET /profile` while logged in shows the Expense History section with dates defaulting to the first and last day of the current month
- [ ] The filter form is pre-populated with the active `from_date` and `to_date` values on every load
- [ ] Submitting the filter form with a valid date range updates the expense table to show only expenses within that range
- [ ] The filtered total reflects only the expenses shown in the table
- [ ] Submitting a range that contains no expenses shows the empty-state message and a total of ₨ 0.00
- [ ] A malformed date in either param (e.g. `?from_date=abc`) silently falls back to current-month defaults without showing an error
- [ ] Existing account-details update and password-change forms still work correctly after this change
- [ ] `GET /profile` without a session still redirects to `/login`
- [ ] Expense amounts are formatted as `₨ X,XXX.00` in the table and the summary line
