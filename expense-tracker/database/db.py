import sqlite3
import os
from werkzeug.security import generate_password_hash

DB_PATH = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "zamah.db")


def get_db():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    return conn


def init_db():
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

    user_id = db.execute("SELECT id FROM users WHERE email = ?", ("demo@zamah.com",)).fetchone()[0]

    db.executemany(
        "INSERT INTO expenses (user_id, amount, category, date, description) VALUES (?, ?, ?, ?, ?)",
        [
            (user_id,  850.00, "Food",          "2026-06-01", "Breakfast at café"),
            (user_id, 2500.00, "Transport",      "2026-05-29", "Fuel refill"),
            (user_id, 15000.00, "Bills",         "2026-05-27", "Electricity bill"),
            (user_id, 3200.00, "Health",         "2026-05-25", "Pharmacy"),
            (user_id, 1200.00, "Entertainment",  "2026-05-22", "Cinema tickets"),
            (user_id, 4500.00, "Shopping",       "2026-05-20", "Grocery run"),
            (user_id,  900.00, "Other",          "2026-05-18", "Miscellaneous"),
            (user_id, 1800.00, "Food",           "2026-05-15", "Dinner with family"),
        ],
    )
    db.commit()
    db.close()
