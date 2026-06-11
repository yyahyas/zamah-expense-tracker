# Spec: Backend Routes for Profile Page

## Overview

This spec documents and validates the backend routes that power the profile page in Zamah. By step 05, users can already register, log in, and log out; the profile page closes the account-management loop by letting logged-in users view their details, update their name or email, and change their password. All three routes enforce authentication, validate input server-side, and redirect back to `/profile` with a query-param message rather than re-rendering on POST — following the PRG (Post/Redirect/Get) pattern established in earlier steps.

> **Note:** These routes were implemented as part of step 04. This spec documents the existing implementation for reference and provides a verification checklist.

## Depends on

- Step 01 — Database setup (`users` table, `get_db()`, `get_user_by_id()`)
- Step 02 — Registration (`create_user`, session keys `user_id` / `user_name`)
- Step 03 — Login and logout (auth-redirect pattern, `session.clear()`)
- Step 04 — Profile page template (`templates/profile.html`)

## Routes

- `GET /profile` — fetch current user from DB and render profile page; redirect to `/login` if not authenticated — logged-in
- `POST /profile` — validate and update name/email; refresh `session['user_name']` on success; redirect to `GET /profile` with `?message=` or `?error=` — logged-in
- `POST /profile/password` — verify current password, validate new password, update hash; redirect to `GET /profile` with `?message=` or `?error=` — logged-in

## Database changes

No database changes. The following functions in `database/db.py` are used:

- `get_user_by_id(user_id)` — fetch the logged-in user's record
- `get_user_by_email(email)` — check for email conflicts on update
- `update_user(user_id, name, email)` — persist name/email changes
- `update_password(user_id, new_password_hash)` — persist hashed new password

## Templates

- **Modify:** `templates/profile.html` — must accept `user`, `message`, and `error` variables from the route; display a success banner when `message` is set and an error banner when `error` is set; the account-details form posts to `POST /profile`; the change-password form posts to `POST /profile/password`

## Files to change

- `app.py` — three profile routes: `GET /profile`, `POST /profile` (`profile_update`), `POST /profile/password` (`profile_password`)
- `database/db.py` — `update_user` and `update_password` functions (already present)

## Files to create

No new files.

## New dependencies

No new dependencies.

## Rules for implementation

- No SQLAlchemy or ORMs — raw SQLite with parameterised queries only
- All DB access through `database/db.py` — never inline SQLite in `app.py`
- Passwords hashed with `werkzeug.security.generate_password_hash`; current password verified with `check_password_hash` before any password change
- All templates extend `base.html`
- Use CSS variables — never hardcode hex values
- Both POST routes must redirect to `/login` if `session.get('user_id')` is falsy
- PRG pattern: on both success and validation failure, always redirect (never re-render on POST)
- On a successful name/email update, refresh `session['user_name']` so the navbar reflects the change immediately
- Email uniqueness check: query by email; if a record is returned whose `id` differs from `session['user_id']`, reject with an error
- Password validation order: current password not empty → new password ≥ 8 chars → passwords match → verify hash

## Definition of done

- [ ] `GET /profile` without a session redirects to `/login`
- [ ] `GET /profile` while logged in renders the profile page with the user's current name and email pre-filled in the account-details form
- [ ] The profile page displays the account's `created_at` date as the member-since date
- [ ] Submitting the account-details form with a blank name shows an error and leaves the DB unchanged
- [ ] Submitting the account-details form with a blank email shows an error and leaves the DB unchanged
- [ ] Submitting the account-details form with an email belonging to a different account shows an error
- [ ] Submitting the account-details form with valid inputs updates the DB and immediately reflects the new name in the navbar
- [ ] A success message is visible on `/profile` after a successful account-details update
- [ ] `POST /profile/password` with an incorrect current password shows an error and does not update `password_hash`
- [ ] `POST /profile/password` with a new password shorter than 8 characters shows an error
- [ ] `POST /profile/password` where new password and confirm do not match shows an error
- [ ] `POST /profile/password` with all valid inputs updates `password_hash` in the DB
- [ ] After a successful password change the user can log out, log back in with the new password, and the old password is rejected
- [ ] A success message is visible on `/profile` after a successful password change
- [ ] Manually POSTing to `/profile` or `/profile/password` without a session redirects to `/login`
