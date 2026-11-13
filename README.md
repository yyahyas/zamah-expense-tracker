# Zamah Expense Tracker

A personal expense tracking web app built with Flask and SQLite. Users register, log expenses in **PKR (₨)**, and review spending through a dashboard, date-filtered profile summary, category breakdown, and analytics view.

## Features

- **Authentication** — registration, login, logout with hashed passwords (Werkzeug) and session-based auth
- **Expense management** — add, edit, and delete expenses, with per-user ownership checks
- **Dashboard** — overview of recent expenses and totals
- **Profile** — update name/email, change password, and filter the expense summary by date range
- **Category breakdown** — spending grouped by category
- **Analytics** — spending insights page
- **PKR formatting** throughout
- Legal pages: Terms and Privacy

Expense categories: Food, Transport, Bills, Health, Entertainment, Shopping, Other.

## Tech Stack

| Layer      | Choice                                   |
|------------|------------------------------------------|
| Backend    | Flask 3.1, Werkzeug 3.1                  |
| Database   | SQLite (`zamah.db`), foreign keys enabled |
| Frontend   | Jinja2 templates, plain CSS, vanilla JS (no framework) |
| Testing    | pytest, pytest-flask                     |

## Project Structure

```
zamah-expense-tracker/
├── app.py                 # Flask app and all routes
├── database/
│   └── db.py              # All DB access: get_db, init_db, seed_db, queries
├── templates/
│   ├── base.html          # Shared navbar/footer
│   ├── landing.html, login.html, register.html
│   ├── dashboard.html, profile.html, analytics.html
│   ├── expenses.html, category_breakdown.html
│   ├── expenses/          # add / edit expense forms
│   └── terms.html, privacy.html
├── static/
│   ├── css/style.css      # Global styles
│   ├── css/landing.css    # Landing page only
│   └── js/main.js
├── tests/                 # pytest suite
├── requirements.txt
└── Procfile
```

## Getting Started

### Prerequisites

- Python 3.12+ (Flask 3.1 compatible)

### Setup

```bash
# Create and activate a virtual environment
python -m venv venv
# Windows (PowerShell)
.\venv\Scripts\Activate.ps1
# macOS / Linux
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Run the app
python app.py
```

The app starts on **http://localhost:5001**. On first run it creates `zamah.db` and seeds a demo account.

### Demo account (development only)

| Email             | Password  |
|-------------------|-----------|
| demo@zamah.com    | demo123   |

This account is seeded automatically when the users table is empty. Do not rely on it outside local development.

### Configuration

| Variable     | Purpose                    | Default             |
|--------------|----------------------------|---------------------|
| `SECRET_KEY` | Flask session signing key  | `zamah-dev-secret`  |

**Set a strong, unique `SECRET_KEY` in any non-local environment.** The default is for development only.

## Routes

| Method    | Path                       | Description                          |
|-----------|----------------------------|--------------------------------------|
| GET       | `/`                        | Landing page                         |
| GET/POST  | `/register`                | Create an account                    |
| GET/POST  | `/login`                   | Sign in                              |
| GET       | `/logout`                  | Sign out                             |
| GET       | `/dashboard`               | Dashboard                            |
| GET/POST  | `/profile`                 | View/update profile, date filter     |
| POST      | `/profile/password`        | Change password                      |
| GET       | `/analytics`               | Analytics                            |
| GET       | `/expenses`                | Expense list                         |
| GET/POST  | `/expenses/add`            | Add an expense                       |
| GET/POST  | `/expenses/<id>/edit`      | Edit an expense (owner only)         |
| POST      | `/expenses/<id>/delete`    | Delete an expense (owner only)       |
| GET       | `/expenses/categories`     | Category breakdown                   |
| GET       | `/terms`, `/privacy`       | Legal pages                          |

## Database Schema

```sql
users (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  name TEXT NOT NULL,
  email TEXT NOT NULL UNIQUE,
  password_hash TEXT NOT NULL,
  created_at TEXT DEFAULT (datetime('now'))
)

expenses (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  user_id INTEGER NOT NULL REFERENCES users(id),
  amount REAL NOT NULL,
  category TEXT NOT NULL,
  date TEXT NOT NULL,
  description TEXT,
  created_at TEXT DEFAULT (datetime('now'))
)
```

## Testing

```bash
pytest
```

Tests cover adding, editing, and deleting expenses and the profile date filter.

## Development Conventions

- All database access goes through `database/db.py`; no inline SQLite in routes.
- Foreign keys must be enabled on every connection.
- Plain CSS and vanilla JS only; no frontend framework.
- Currency is PKR everywhere.

## Deployment

A `Procfile` is included (`web: python app.py`) for platforms that read it. Before deploying:

- Set `SECRET_KEY` via the platform's environment/secrets settings.
- Use a production WSGI server (e.g. gunicorn) rather than the Flask development server.
- SQLite stores data in a local file; use a persistent volume, or move to a managed database if you need durability across redeploys.
