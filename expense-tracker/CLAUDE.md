# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Commands

```bash
# Activate virtual environment (Windows)
..\venv\Scripts\Activate.ps1

# Install dependencies
pip install -r requirements.txt

# Run the app (port 5001)
python app.py

# Run tests
pytest
```

## Architecture

This is a Flask expense tracker app called **Zamah Expense Tracker**. It uses SQLite via a custom `database/db.py` module and Jinja2 templates.

**Stack:** Flask 3.1, SQLite, plain HTML/CSS/JS (no frontend framework)

**Key files:**
- `app.py` — all routes; placeholder routes for steps 3–9 are stubs returning strings
- `database/db.py` — must implement `get_db()`, `init_db()`, `seed_db()` (SQLite, row_factory, foreign keys enabled)
- `templates/base.html` — shared navbar and footer inherited by all pages
- `static/css/style.css` — global styles; `static/css/landing.css` — landing page only

**Route structure:**
- `GET /` — landing page
- `GET|POST /register` — registration form
- `GET|POST /login` — login form
- `/logout`, `/profile`, `/expenses/add`, `/expenses/<id>/edit`, `/expenses/<id>/delete` — stubs to be implemented in later steps

**Currency:** PKR (Pakistani Rupees, ₨). All amounts should use PKR formatting.

**Template placeholders:** `yousaf@example.com` / `Yousaf Shamozai` are the example values used in form inputs.
