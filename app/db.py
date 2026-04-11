"""SQLite connection management + schema bootstrap."""
import sqlite3
from flask import g, current_app

SCHEMA = """
CREATE TABLE IF NOT EXISTS users (
    user_id        INTEGER PRIMARY KEY AUTOINCREMENT,
    username       TEXT UNIQUE NOT NULL,
    password_hash  TEXT NOT NULL,
    email          TEXT UNIQUE NOT NULL,
    role           TEXT NOT NULL DEFAULT 'customer',  -- customer | admin
    status         TEXT NOT NULL DEFAULT 'active',    -- active | blocked
    full_name      TEXT,
    address        TEXT,
    phone          TEXT,
    created_at     TEXT DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS accounts (
    account_number TEXT PRIMARY KEY,
    user_id        INTEGER NOT NULL,
    balance        REAL NOT NULL DEFAULT 0,
    currency       TEXT NOT NULL DEFAULT 'PLN',
    account_type   TEXT NOT NULL DEFAULT 'checking',
    status         TEXT NOT NULL DEFAULT 'active',
    FOREIGN KEY(user_id) REFERENCES users(user_id)
);

CREATE TABLE IF NOT EXISTS transactions (
    transaction_id INTEGER PRIMARY KEY AUTOINCREMENT,
    date           TEXT DEFAULT CURRENT_TIMESTAMP,
    type           TEXT NOT NULL,          -- deposit | withdraw | transfer
    amount         REAL NOT NULL,
    description    TEXT,
    source_account TEXT,
    dest_account   TEXT,
    status         TEXT NOT NULL DEFAULT 'completed'
);

CREATE TABLE IF NOT EXISTS notifications (
    notification_id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id         INTEGER NOT NULL,
    type            TEXT,
    message         TEXT NOT NULL,
    timestamp       TEXT DEFAULT CURRENT_TIMESTAMP,
    read            INTEGER DEFAULT 0,
    FOREIGN KEY(user_id) REFERENCES users(user_id)
);

CREATE TABLE IF NOT EXISTS audit_log (
    id         INTEGER PRIMARY KEY AUTOINCREMENT,
    admin_id   INTEGER NOT NULL,
    action     TEXT NOT NULL,
    target     TEXT,
    timestamp  TEXT DEFAULT CURRENT_TIMESTAMP
);
"""


def get_db():
    if "db" not in g:
        g.db = sqlite3.connect(current_app.config["DATABASE"])
        g.db.row_factory = sqlite3.Row
        g.db.execute("PRAGMA foreign_keys = ON")
    return g.db


def close_db(_exc=None):
    db = g.pop("db", None)
    if db is not None:
        db.close()


def init_db():
    db = get_db()
    db.executescript(SCHEMA)
    db.commit()
