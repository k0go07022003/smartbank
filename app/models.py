"""Domain operations — mirrors the UML class diagram.

The class diagram had User / Customer / Administrator, BankAccount,
Transaction (+ Deposit/Withdraw/Transfer subclasses), Notification,
NotificationManager. This module exposes those behaviors as functions
over the sqlite3 connection; keeping it procedural avoids an ORM layer
for a coursework project while still honoring the design.
"""
import random
import string
from werkzeug.security import generate_password_hash as _gph, check_password_hash


def generate_password_hash(password):
    # pbkdf2 is available on all Python builds; scrypt is not on stock macOS 3.9
    return _gph(password, method="pbkdf2:sha256")


# ---------- users ----------

class AuthError(Exception):
    pass


class DomainError(Exception):
    pass


def register_user(db, username, email, password, full_name=None, role="customer"):
    if len(password) < 6:
        raise DomainError("Password must be at least 6 characters")
    if "@" not in email:
        raise DomainError("Invalid email")
    try:
        cur = db.execute(
            "INSERT INTO users (username, password_hash, email, role, full_name) "
            "VALUES (?, ?, ?, ?, ?)",
            (username, generate_password_hash(password), email, role, full_name),
        )
        user_id = cur.lastrowid
        # Open a default account for customers
        if role == "customer":
            open_account(db, user_id)
        db.commit()
        return user_id
    except Exception as e:
        db.rollback()
        if "UNIQUE" in str(e):
            raise DomainError("Username or email already taken") from e
        raise


def authenticate(db, username, password):
    row = db.execute("SELECT * FROM users WHERE username=?", (username,)).fetchone()
    if row is None or not check_password_hash(row["password_hash"], password):
        raise AuthError("Invalid credentials")
    if row["status"] == "blocked":
        raise AuthError("Account is blocked")
    return dict(row)


def get_user(db, user_id):
    row = db.execute("SELECT * FROM users WHERE user_id=?", (user_id,)).fetchone()
    return dict(row) if row else None


def update_profile(db, user_id, full_name=None, address=None, phone=None, email=None):
    fields, values = [], []
    for col, val in [("full_name", full_name), ("address", address),
                     ("phone", phone), ("email", email)]:
        if val is not None:
            fields.append(f"{col}=?")
            values.append(val)
    if not fields:
        return
    values.append(user_id)
    db.execute(f"UPDATE users SET {', '.join(fields)} WHERE user_id=?", values)
    db.commit()


# ---------- accounts ----------

def _generate_account_number():
    return "PL" + "".join(random.choices(string.digits, k=20))


def open_account(db, user_id, currency="PLN", account_type="checking"):
    number = _generate_account_number()
    db.execute(
        "INSERT INTO accounts (account_number, user_id, balance, currency, account_type) "
        "VALUES (?, ?, 0, ?, ?)",
        (number, user_id, currency, account_type),
    )
    db.commit()
    return number


def get_accounts(db, user_id):
    rows = db.execute("SELECT * FROM accounts WHERE user_id=?", (user_id,)).fetchall()
    return [dict(r) for r in rows]


def get_account(db, account_number):
    row = db.execute("SELECT * FROM accounts WHERE account_number=?",
                     (account_number,)).fetchone()
    return dict(row) if row else None


def set_account_status(db, account_number, status):
    db.execute("UPDATE accounts SET status=? WHERE account_number=?",
               (status, account_number))
    db.commit()


# ---------- transactions ----------

def _log_tx(db, type_, amount, description, source=None, dest=None,
            status="completed"):
    cur = db.execute(
        "INSERT INTO transactions (type, amount, description, source_account, "
        "dest_account, status) VALUES (?, ?, ?, ?, ?, ?)",
        (type_, amount, description, source, dest, status),
    )
    return cur.lastrowid


def deposit(db, account_number, amount, description="Deposit"):
    if amount <= 0:
        raise DomainError("Amount must be positive")
    acc = get_account(db, account_number)
    if acc is None:
        raise DomainError("Account not found")
    if acc["status"] != "active":
        raise DomainError("Account is not active")
    db.execute("UPDATE accounts SET balance = balance + ? WHERE account_number=?",
               (amount, account_number))
    tx_id = _log_tx(db, "deposit", amount, description, dest=account_number)
    _notify(db, acc["user_id"], "deposit",
            f"Deposit of {amount:.2f} {acc['currency']} completed.")
    db.commit()
    return tx_id


def withdraw(db, account_number, amount, description="Withdraw"):
    if amount <= 0:
        raise DomainError("Amount must be positive")
    acc = get_account(db, account_number)
    if acc is None:
        raise DomainError("Account not found")
    if acc["status"] != "active":
        raise DomainError("Account is not active")
    if acc["balance"] < amount:
        raise DomainError("Insufficient funds")
    db.execute("UPDATE accounts SET balance = balance - ? WHERE account_number=?",
               (amount, account_number))
    tx_id = _log_tx(db, "withdraw", amount, description, source=account_number)
    _notify(db, acc["user_id"], "withdraw",
            f"Withdrawal of {amount:.2f} {acc['currency']} completed.")
    db.commit()
    return tx_id


def transfer(db, source_number, dest_number, amount, description=""):
    if amount <= 0:
        raise DomainError("Amount must be positive")
    if source_number == dest_number:
        raise DomainError("Source and destination must differ")
    src = get_account(db, source_number)
    dst = get_account(db, dest_number)
    if src is None:
        raise DomainError("Source account not found")
    if dst is None:
        raise DomainError("Recipient account not found")
    if src["status"] != "active" or dst["status"] != "active":
        raise DomainError("One of the accounts is not active")
    if src["balance"] < amount:
        raise DomainError("Insufficient funds")
    db.execute("UPDATE accounts SET balance = balance - ? WHERE account_number=?",
               (amount, source_number))
    db.execute("UPDATE accounts SET balance = balance + ? WHERE account_number=?",
               (amount, dest_number))
    tx_id = _log_tx(db, "transfer", amount, description,
                    source=source_number, dest=dest_number)
    _notify(db, src["user_id"], "transfer_out",
            f"Sent {amount:.2f} {src['currency']} to {dest_number}")
    _notify(db, dst["user_id"], "transfer_in",
            f"Received {amount:.2f} {dst['currency']} from {source_number}")
    db.commit()
    return tx_id


def transaction_history(db, account_number):
    rows = db.execute(
        "SELECT * FROM transactions "
        "WHERE source_account=? OR dest_account=? "
        "ORDER BY date DESC",
        (account_number, account_number),
    ).fetchall()
    return [dict(r) for r in rows]


# ---------- notifications ----------

def _notify(db, user_id, type_, message):
    db.execute(
        "INSERT INTO notifications (user_id, type, message) VALUES (?, ?, ?)",
        (user_id, type_, message),
    )


def get_notifications(db, user_id, limit=20):
    rows = db.execute(
        "SELECT * FROM notifications WHERE user_id=? ORDER BY timestamp DESC LIMIT ?",
        (user_id, limit),
    ).fetchall()
    return [dict(r) for r in rows]


# ---------- admin ----------

def list_users(db):
    rows = db.execute("SELECT user_id, username, email, role, status FROM users "
                      "ORDER BY user_id").fetchall()
    return [dict(r) for r in rows]


def set_user_status(db, admin_id, user_id, status):
    if status not in ("active", "blocked"):
        raise DomainError("Invalid status")
    db.execute("UPDATE users SET status=? WHERE user_id=?", (status, user_id))
    # cascade to their accounts
    db.execute("UPDATE accounts SET status=? WHERE user_id=?", (status, user_id))
    db.execute("INSERT INTO audit_log (admin_id, action, target) VALUES (?, ?, ?)",
               (admin_id, f"set_status:{status}", str(user_id)))
    db.commit()


def all_transactions(db, limit=100):
    rows = db.execute("SELECT * FROM transactions ORDER BY date DESC LIMIT ?",
                      (limit,)).fetchall()
    return [dict(r) for r in rows]
