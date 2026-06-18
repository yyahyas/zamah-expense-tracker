import sqlite3
import os
from flask import current_app, has_app_context
from werkzeug.security import generate_password_hash, check_password_hash

DB_PATH = os.path.join(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "zamah.db"
)


_memory_db_keeper = None  # holds shared in-memory DB alive between get_db() calls


def get_db():
    path = current_app.config.get("DATABASE", DB_PATH) if has_app_context() else DB_PATH
    # SQLite destroys :memory: DBs when the last connection closes. Use the
    # shared-cache URI so all connections in the process see the same DB, and
    # keep _memory_db_keeper open so the DB survives between get_db() calls.
    if path == ":memory:":
        conn = sqlite3.connect("file::memory:?cache=shared", uri=True)
    else:
        conn = sqlite3.connect(path)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    return conn


def init_db():
    global _memory_db_keeper
    path = current_app.config.get("DATABASE", DB_PATH) if has_app_context() else DB_PATH

    if path == ":memory:":
        # Close old keeper → destroys previous shared DB → opens fresh empty one.
        if _memory_db_keeper is not None:
            _memory_db_keeper.close()
        _memory_db_keeper = sqlite3.connect("file::memory:?cache=shared", uri=True)
        _memory_db_keeper.execute("PRAGMA foreign_keys = ON")

    db = get_db()
    db.executescript("""
        CREATE TABLE IF NOT EXISTS users (
            id            INTEGER PRIMARY KEY AUTOINCREMENT,
            name          TEXT    NOT NULL,
            email         TEXT    NOT NULL UNIQUE,
            password_hash TEXT    NOT NULL,
            created_at    TEXT    DEFAULT (datetime('now'))
        );

        CREATE TABLE IF NOT EXISTS expenses (
            id          INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id     INTEGER NOT NULL,
            amount      REAL    NOT NULL,
            category    TEXT    NOT NULL,
            date        TEXT    NOT NULL,
            description TEXT,
            created_at  TEXT    DEFAULT (datetime('now')),
            FOREIGN KEY (user_id) REFERENCES users(id)
        );
    """)
    db.close()


def seed_db():
    db = get_db()
    if db.execute("SELECT COUNT(*) FROM users").fetchone()[0] > 0:
        db.close()
        return

    db.execute(
        "INSERT INTO users (name, email, password_hash) VALUES (?, ?, ?)",
        ("Demo User", "demo@zamah.com", generate_password_hash("demo123")),
    )
    db.commit()

    user_id = db.execute(
        "SELECT id FROM users WHERE email = ?", ("demo@zamah.com",)
    ).fetchone()[0]

    db.executemany(
        "INSERT INTO expenses (user_id, amount, category, date, description) VALUES (?, ?, ?, ?, ?)",
        [
            (user_id, 850.00, "Food", "2026-06-01", "Breakfast at café"),
            (user_id, 2500.00, "Transport", "2026-05-29", "Fuel refill"),
            (user_id, 15000.00, "Bills", "2026-05-27", "Electricity bill"),
            (user_id, 3200.00, "Health", "2026-05-25", "Pharmacy"),
            (user_id, 1200.00, "Entertainment", "2026-05-22", "Cinema tickets"),
            (user_id, 4500.00, "Shopping", "2026-05-20", "Grocery run"),
            (user_id, 900.00, "Other", "2026-05-18", "Miscellaneous"),
            (user_id, 1800.00, "Food", "2026-05-15", "Dinner with family"),
        ],
    )
    db.commit()
    db.close()


def get_user_by_email(email):
    db = get_db()
    row = db.execute("SELECT * FROM users WHERE email = ?", (email,)).fetchone()
    db.close()
    return row


def get_user_by_id(user_id):
    db = get_db()
    row = db.execute("SELECT * FROM users WHERE id = ?", (user_id,)).fetchone()
    db.close()
    return row


def update_user(user_id, name, email):
    db = get_db()
    db.execute(
        "UPDATE users SET name = ?, email = ? WHERE id = ?",
        (name, email, user_id),
    )
    db.commit()
    db.close()


def update_password(user_id, new_password_hash):
    db = get_db()
    db.execute(
        "UPDATE users SET password_hash = ? WHERE id = ?",
        (new_password_hash, user_id),
    )
    db.commit()
    db.close()


def get_expenses(user_id):
    db = get_db()
    rows = db.execute(
        "SELECT * FROM expenses WHERE user_id = ? ORDER BY date DESC", (user_id,)
    ).fetchall()
    db.close()
    return rows


def get_expense_totals(user_id):
    db = get_db()
    total = db.execute(
        "SELECT COALESCE(SUM(amount), 0) FROM expenses WHERE user_id = ?", (user_id,)
    ).fetchone()[0]
    month_total = db.execute(
        "SELECT COALESCE(SUM(amount), 0) FROM expenses "
        "WHERE user_id = ? AND strftime('%Y-%m', date) = strftime('%Y-%m', 'now')",
        (user_id,),
    ).fetchone()[0]
    top = db.execute(
        "SELECT category FROM expenses WHERE user_id = ? "
        "GROUP BY category ORDER BY SUM(amount) DESC LIMIT 1",
        (user_id,),
    ).fetchone()
    db.close()
    return {
        "total": total,
        "month_total": month_total,
        "top_category": top[0] if top else "—",
    }


def get_expenses_filtered(user_id, from_date, to_date):
    db = get_db()
    rows = db.execute(
        "SELECT * FROM expenses WHERE user_id = ? AND date BETWEEN ? AND ? ORDER BY date DESC",
        (user_id, from_date, to_date),
    ).fetchall()
    db.close()
    return rows


def get_expenses_by_category(user_id):
    db = get_db()
    rows = db.execute(
        "SELECT category, SUM(amount) as total, COUNT(*) as count "
        "FROM expenses WHERE user_id = ? "
        "GROUP BY category ORDER BY total DESC",
        (user_id,),
    ).fetchall()
    db.close()
    return rows


def create_user(name, email, password):
    db = get_db()
    password_hash = generate_password_hash(password)
    try:
        cursor = db.execute(
            "INSERT INTO users (name, email, password_hash) VALUES (?, ?, ?)",
            (name, email, password_hash),
        )
        db.commit()
        return cursor.lastrowid
    finally:
        db.close()


def create_expense(user_id, amount, category, expense_date, description):
    db = get_db()
    try:
        cursor = db.execute(
            "INSERT INTO expenses (user_id, amount, category, date, description) VALUES (?, ?, ?, ?, ?)",
            (user_id, amount, category, expense_date, description or None),
        )
        db.commit()
        return cursor.lastrowid
    finally:
        db.close()


def get_expense_by_id(expense_id):
    db = get_db()
    row = db.execute("SELECT * FROM expenses WHERE id = ?", (expense_id,)).fetchone()
    db.close()
    return row


def update_expense(expense_id, amount, category, expense_date, description):
    db = get_db()
    db.execute(
        "UPDATE expenses SET amount = ?, category = ?, date = ?, description = ? WHERE id = ?",
        (amount, category, expense_date, description or None, expense_id),
    )
    db.commit()
    db.close()
