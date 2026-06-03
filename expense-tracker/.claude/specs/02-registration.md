# Spec: Registration

## Overview

This step implements a working user registration flow for Zamah Expense Tracker. The `POST /register` route is currently a stub that only renders the template. This spec covers full form handling: validating inputs, hashing passwords, inserting a new user into the database, establishing a session, and redirecting to the dashboard. It is the first step that requires Flask sessions, so a `SECRET_KEY` must also be configured.

## Depends on

- Step 01 — Project scaffold (Flask app, `init_db`, `seed_db`, base template, register template all already in place)

## Routes

- `GET /register` — render the registration form — public
- `POST /register` — validate inputs, create user, start session, redirect to `/dashboard` — public

## Database changes

No new tables or columns. The `users` table already has all required columns:

```
id, name, email, password_hash, created_at
```

One new function must be added to `database/db.py`:

- `create_user(name, email, password)` — hashes the password with `werkzeug`, inserts a row into `users`, returns the new user's `id`. Must use a parameterised query.
- `get_user_by_email(email)` — returns the `users` row matching `email`, or `None`. Used during registration to check for duplicate emails.

## Templates

**Modify:** `templates/register.html`
- Pass `name` and `email` back into the form inputs on validation failure (sticky fields) so the user does not have to retype them
- The `{% if error %}` block is already present — no structural changes needed

## Files to change

- `app.py` — implement `POST /register` logic; add `SECRET_KEY` and `flask.session`
- `database/db.py` — add `create_user` and `get_user_by_email` functions
- `templates/register.html` — add `value="{{ name or '' }}"` and `value="{{ email or '' }}"` to name/email inputs

## Files to create

None.

## New dependencies

No new pip packages. `werkzeug.security` is already imported in `database/db.py`. `flask.session` and `flask.redirect` are part of Flask.

## Rules for implementation

- No SQLAlchemy or ORMs — raw SQLite with parameterised queries only
- Passwords hashed with `werkzeug.security.generate_password_hash` — never store plaintext
- `SECRET_KEY` must be set on the Flask app before sessions will work — use a hardcoded dev value for now: `app.secret_key = "zamah-dev-secret"`
- All DB access through `database/db.py` only — no inline SQLite in `app.py`
- All templates extend `base.html`
- Use CSS variables — never hardcode hex values
- After successful registration, store `user_id` and `user_name` in `session`, then redirect to `/dashboard` (stub route already exists for a later step — redirect there anyway so the flow is correct)
- On validation failure, re-render `register.html` with an `error` message and the submitted `name` and `email` so inputs stay populated
- Validate: name not empty, email not empty, password at least 8 characters, email not already registered

## Definition of done

- [ ] Visiting `GET /register` renders the form with no errors
- [ ] Submitting the form with a blank name shows an error and re-populates the email field
- [ ] Submitting with a password shorter than 8 characters shows an error
- [ ] Submitting a valid name/email/password creates a new row in `users` (verify with SQLite browser or `flask shell`)
- [ ] After successful registration, the browser redirects to `/dashboard`
- [ ] After successful registration, `session['user_id']` is set
- [ ] Registering with an email that already exists shows "Email already registered" error
- [ ] Submitting the form with an invalid email (no `@`) is blocked by the browser's `type="email"` validation
- [ ] Name and email fields retain their values when the form is re-submitted with an error
