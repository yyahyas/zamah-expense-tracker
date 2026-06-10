# Spec: Profile Page

## Overview

Implement the profile page so logged-in users can view and update their account details. The `GET /profile` route fetches the current user's record and renders a page showing their name, email, and member-since date. Two separate forms handle updates: one for changing name/email, and one for changing the password. Both `POST /profile` and `POST /profile/password` validate input, update the database, refresh the session where needed, and redirect back to `/profile` with a success or error flash message.

## Depends on

- Step 01 — Database setup (`users` table, `get_db()`)
- Step 02 — Registration (`create_user`, session pattern)
- Step 03 — Login and logout (`session['user_id']`, `session['user_name']`, auth redirect pattern)

## Routes

- `GET /profile` — render the profile page with the current user's data; redirect to `/login` if not logged in — logged-in
- `POST /profile` — update name and/or email; redirect back to `GET /profile` with success or error message — logged-in
- `POST /profile/password` — validate current password then update to new password; redirect back to `GET /profile` with success or error message — logged-in

## Database changes

No new tables. Two new functions must be added to `database/db.py`:

- `update_user(user_id, name, email)` — updates the `name` and `email` columns for the given user; returns nothing
- `update_password(user_id, new_password_hash)` — updates `password_hash` for the given user; returns nothing

## Templates

- **Create:** `templates/profile.html` — profile page with two sections: (1) an "Account details" form pre-populated with current name and email; (2) a "Change password" form with current password, new password, and confirm new password fields. Show a flash message banner at the top when `message` or `error` is passed from the route.
- **Modify:** `templates/base.html` — ensure the "Profile" link in the authenticated navbar points to `url_for('profile')` (it may already be present; verify and add if missing)

## Files to change

- `app.py` — replace the `/profile` stub with a full `GET /profile` route and add `POST /profile` and `POST /profile/password` routes; import `update_user`, `update_password` from `database.db`
- `database/db.py` — add `update_user(user_id, name, email)` and `update_password(user_id, new_password_hash)` functions
- `templates/base.html` — verify/add Profile link in auth-aware navbar

## Files to create

- `templates/profile.html`

## New dependencies

No new dependencies.

## Rules for implementation

- No SQLAlchemy or ORMs — raw SQLite with parameterised queries only
- All DB access through `database/db.py` only — no inline SQLite in `app.py`
- Passwords hashed with `werkzeug.security.generate_password_hash`; current password verified with `check_password_hash` before allowing a password change
- All templates extend `base.html`
- Use CSS variables — never hardcode hex values
- Both POST routes must redirect to `/login` if `session.get('user_id')` is falsy
- On a successful name/email update, refresh `session['user_name']` to reflect the new name immediately
- Validate name/email update: name not empty, email not empty, new email not already taken by a different user (query by email and check the returned id differs from the current user)
- Validate password change: current password not empty, new password at least 8 characters, new password and confirm match, current password must verify against the stored hash
- Never expose which specific field caused a validation failure for the password form beyond the specific error listed (e.g. "Current password is incorrect" is fine; don't say which hash comparison failed in detail)
- On any validation failure, redirect back to `/profile` passing the error as a query param or use `session` flash — do not re-render with a 200 that could be re-submitted

## Definition of done

- [ ] Visiting `GET /profile` without being logged in redirects to `/login`
- [ ] Visiting `GET /profile` while logged in renders the profile page with the user's current name and email pre-filled
- [ ] The profile page shows the account's member-since date
- [ ] Submitting the account details form with a blank name shows an error and does not update the DB
- [ ] Submitting the account details form with a blank email shows an error and does not update the DB
- [ ] Submitting the account details form with an email already used by another account shows an error
- [ ] Submitting the account details form with valid name and email updates the DB and refreshes the navbar to show the new name
- [ ] Submitting the password form with an incorrect current password shows an error and does not update the DB
- [ ] Submitting the password form with a new password shorter than 8 characters shows an error
- [ ] Submitting the password form where new password and confirm do not match shows an error
- [ ] Submitting the password form with all valid inputs updates `password_hash` in the DB
- [ ] After a successful password change the user can log out and log back in with the new password
- [ ] A success message is displayed on `/profile` after a successful update
