# Spec: Delete Expense

## Overview
This step implements the expense deletion feature. Users can delete any of their own expenses directly from the expense list, dashboard recent-expenses table, and profile page expense table. A browser `confirm()` prompt prevents accidental deletions. The route was previously a GET stub returning a string; this step replaces it with a proper POST-only route that enforces ownership and redirects after deletion.

## Depends on
- Step 07 — Add Expense (expenses table and `create_expense` exist)
- Step 08 — Edit Expense (ownership-check pattern already established in `edit_expense`)

## Routes

- `POST /expenses/<int:id>/delete` — delete the expense with the given ID — logged-in only

The existing GET stub at the same path must be removed and replaced with this POST-only route.

## Database changes
No new tables or columns. A new helper function is required:

- `delete_expense(expense_id)` — executes `DELETE FROM expenses WHERE id = ?` using a parameterised query.

## Templates

- **Modify:** `templates/expenses.html` — add a Delete button next to the existing Edit link for each row
- **Modify:** `templates/dashboard.html` — add a Delete button next to the existing Edit link in the recent-expenses table
- **Modify:** `templates/profile.html` — add a Delete button next to the existing Edit link in the filtered-expenses table

No new templates. Deletion redirects to `url_for('expense_list')`.

## Files to change
- `database/db.py` — add `delete_expense(expense_id)` function
- `app.py` — replace stub `delete_expense` route; import `delete_expense` from `database.db`
- `templates/expenses.html` — add Delete form/button per row
- `templates/dashboard.html` — add Delete form/button per row
- `templates/profile.html` — add Delete form/button per row

## Files to create
None.

## New dependencies
No new dependencies.

## Rules for implementation
- No SQLAlchemy or ORMs
- Parameterised queries only
- Passwords hashed with werkzeug (not applicable here, but keep existing hashing untouched)
- Use CSS variables — never hardcode hex values
- All templates extend `base.html`
- The route must be POST only — no GET handler for delete
- Auth check: redirect to `url_for('login')` if `session.get('user_id')` is falsy
- Ownership check: `abort(403)` if `expense['user_id'] != session['user_id']`
- Existence check: `abort(404)` if `get_expense_by_id(id)` returns `None`
- The Delete button must be a `<form method="POST">` submitting to `url_for('delete_expense', id=expense.id)` — not a plain `<a>` link (GET)
- Add `onsubmit="return confirm('Delete this expense?')"` to the form to prevent accidental deletes
- Style the Delete button to match the existing Edit link style (same border, border-radius, padding) but use `var(--danger)` or `var(--error)` for the text color to signal destructiveness; if neither variable exists use `var(--ink-muted)` as a safe fallback
- After a successful delete, redirect to `url_for('expense_list')`
- Import `delete_expense` in `app.py` alongside the existing imports from `database.db`

## Definition of done
- [ ] Visiting `GET /expenses/<id>/delete` returns 405 Method Not Allowed (no GET handler)
- [ ] Submitting the delete form for an expense owned by the logged-in user removes it from the database and redirects to `/expenses`
- [ ] The deleted expense no longer appears in the expense list after deletion
- [ ] Attempting to delete an expense belonging to another user returns 403
- [ ] Attempting to delete a non-existent expense ID returns 404
- [ ] Delete buttons are visible in the expense list (`/expenses`)
- [ ] Delete buttons are visible in the recent-expenses table on the dashboard (`/dashboard`)
- [ ] Delete buttons are visible in the filtered-expenses table on the profile page (`/profile`)
- [ ] Clicking a Delete button shows a browser confirm dialog before submitting
- [ ] A logged-out user who POSTs to `/expenses/<id>/delete` is redirected to `/login`
