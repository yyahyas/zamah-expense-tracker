# Spec: Registration

## Overview

Implement user registration so new visitors can create a Zamah account. This step upgrades the existing stub `GET /register` route into a fully functional form that accepts a POST, validates input, hashes the password, and inserts a new row into the `users` table. On success the user is shown with a success message and then redirected to the login page. This is the entry point for all authenticated features that follow.
## Depends on

Step 01 — Database setup (`users` table, `get_db()`)


## Routes

- `GET /register` — render the registration form — public
- `POST /register` — process registration form, insert user, redirect to `/login` — public

## Database changes

No new tables or columns. The `users` table already has all required columns:

```
id, name, email, password_hash, created_at
```

One new function must be added to `database/db.py`:

- `create_user(name, email, password)` — hashes the password with `werkzeug`, inserts a row into `users`, returns the new user's `id`. Must use a parameterised query.
- `get_user_by_email(email)` — returns the `users` row matching `email`, or `None`. Used during registration to check for duplicate emails.

## Templates

- **Modify:** `templates/register.html`
 - Change the form `action` to `url_for('register')` with `method="post"`
 - Add `name` attributes to all inputs: `name`, `email`, `password`, `confirm_password`
 - Add a block to display a flash error message (e.g. "Email already registered", "Passwords do not match")
 - Keep all existing visual design

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
