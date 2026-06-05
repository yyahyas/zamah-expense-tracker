# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project

**Zamah Expense Tracker** — a Flask-based personal expense tracking web app.
- Previously named "Spendly"; all references should use "Zamah" now
- Database file: `zamah.db` (renamed from `spendly.db`)
- Currency: PKR (Pakistani Rupees, ₨) — use PKR formatting everywhere

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

**Stack:** Flask 3.1, SQLite, plain HTML/CSS/JS (no frontend framework), Jinja2 templates

**Key files:**
- `app.py` — all routes; placeholder routes for steps 3–9 are stubs returning strings
- `database/db.py` — implements `get_db()`, `init_db()`, `seed_db()` (SQLite, row_factory, foreign keys enabled)
- `templates/base.html` — shared navbar and footer inherited by all pages
- `static/css/style.css` — global styles
- `static/css/landing.css` — landing page only

**Route structure:**
- `GET /` — landing page
- `GET|POST /register` — registration form
- `GET|POST /login` — login form
- `/logout`, `/profile`, `/expenses/add`, `/expenses/<id>/edit`, `/expenses/<id>/delete` — stubs to be implemented in later steps

## Conventions

- Example placeholder values in forms: `yousaf@example.com` / `Yousaf Shamozai`
- No frontend framework — keep JS vanilla and CSS plain
- All DB access through `database/db.py` only, never inline SQLite in routes
- Foreign keys must stay enabled on every connection