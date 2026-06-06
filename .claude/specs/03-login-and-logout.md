# Spec: Login and Logout

## Overview

Implement login, logout, and a basic authenticated dashboard so users who registered in Step 02 can sign in and access the app. The `GET|POST /login` route validates credentials against the stored password hash, sets the session, and redirects to `/dashboard`. The `GET /logout` route clears the session and redirects to the landing page. The `GET /dashboard` route is auth-protected and serves as the post-login home. The navbar in `base.html` becomes auth-aware, showing Sign in / Get started for guests and the user's name + Logout for authenticated users.

## Depends on

- Step 01 — Database setup (`users` table, `get_db()`)
- Step 02 — Registration (`create_user`, `get_user_by_email`, session pattern)

## Routes

- `GET /login` — render the login form; redirect to `/dashboard` if already logged in — public
- `POST /login` — validate email/password, set session on success, redirect to `/dashboard`; re-render form with error on failure — public
- `GET /logout` — clear session, redirect to `/` — any
- `GET /dashboard` — render the dashboard; redirect to `/login` if not logged in — logged-in

## Database changes

No new tables or columns. One new function must be added to `database/db.py`:

- `get_user_by_id(user_id)` — returns the `users` row matching `id`, or `None`. Used by the dashboard route to fetch the current user's display name.

## Templates

- **Create:** `templates/dashboard.html` — authenticated landing page showing the user's name and a welcome message; placeholder cards for expenses summary (static, no real data yet)
- **Modify:** `templates/login.html` — add `value="{{ email or '' }}"` to the email input so it repopulates on validation error; form markup is otherwise already correct
- **Modify:** `templates/base.html` — make navbar auth-aware: when `session.user_id` is set, show the user's name and a Logout link; when not set, show Sign in and Get started

## Files to change

- `app.py` — implement `POST /login`, `GET /logout`, and `GET /dashboard` routes; add `check_password_hash` import; import `get_user_by_id` from `database.db`
- `database/db.py` — add `get_user_by_id(user_id)` function
- `templates/login.html` — add `value="{{ email or '' }}"` to email input
- `templates/base.html` — auth-aware navbar using `session`

## Files to create

- `templates/dashboard.html`

## New dependencies

No new dependencies. `werkzeug.security.check_password_hash` is already available via the existing werkzeug install.

## Rules for implementation

- No SQLAlchemy or ORMs — raw SQLite with parameterised queries only
- Passwords verified with `werkzeug.security.check_password_hash` — never compare plaintext
- All DB access through `database/db.py` only — no inline SQLite in `app.py`
- All templates extend `base.html`
- Use CSS variables — never hardcode hex values
- The login route must redirect to `/dashboard` when the user is already logged in (check `session.get('user_id')`)
- The dashboard route must redirect to `/login` when no session exists
- On login failure, re-render `login.html` with an `error` message and the submitted `email` value so the field stays populated
- Validate: email not empty, password not empty, email exists in DB, password matches hash — show a generic "Invalid email or password" error (do not reveal which field is wrong)
- `session` must store `user_id` (int) and `user_name` (str) — same keys used by the registration route
- `app.secret_key` is already set in `app.py` — do not change it

## Definition of done

- [ ] Visiting `GET /login` renders the sign-in form
- [ ] Visiting `GET /login` while already logged in redirects to `/dashboard`
- [ ] Submitting the login form with an unknown email shows "Invalid email or password"
- [ ] Submitting the login form with a correct email but wrong password shows "Invalid email or password"
- [ ] Submitting with valid credentials sets `session['user_id']` and redirects to `/dashboard`
- [ ] The dashboard page is visible after login and displays the logged-in user's name
- [ ] Visiting `/dashboard` without being logged in redirects to `/login`
- [ ] Clicking logout clears the session and redirects to `/`
- [ ] After logout, visiting `/dashboard` redirects to `/login`
- [ ] The navbar shows Sign in / Get started for logged-out visitors
- [ ] The navbar shows the user's name and a Logout link for logged-in users
- [ ] The email field repopulates when the login form is re-submitted with an error
