"""Unit tests for domain logic (mirrors UML class diagram behaviors)."""
import pytest
from app.db import get_db
from app.models import (
    register_user, authenticate, deposit, withdraw, transfer,
    transaction_history, get_account, get_notifications,
    set_user_status, update_profile, DomainError, AuthError,
)


def test_register_creates_user_and_default_account(app):
    with app.app_context():
        db = get_db()
        uid = register_user(db, "carol", "carol@x.com", "secret1")
        rows = db.execute("SELECT * FROM accounts WHERE user_id=?", (uid,)).fetchall()
        assert len(rows) == 1
        assert rows[0]["balance"] == 0


def test_register_rejects_short_password(app):
    with app.app_context():
        with pytest.raises(DomainError):
            register_user(get_db(), "x", "x@x.com", "abc")


def test_register_rejects_duplicate_username(app):
    with app.app_context():
        db = get_db()
        register_user(db, "dup", "a@a.com", "secret1")
        with pytest.raises(DomainError):
            register_user(db, "dup", "b@b.com", "secret1")


def test_authenticate_ok_and_fail(app):
    with app.app_context():
        db = get_db()
        register_user(db, "eve", "e@e.com", "secret1")
        assert authenticate(db, "eve", "secret1")["username"] == "eve"
        with pytest.raises(AuthError):
            authenticate(db, "eve", "wrong")


def test_deposit_increases_balance(app, alice):
    with app.app_context():
        db = get_db()
        deposit(db, alice["account"], 250.50)
        assert get_account(db, alice["account"])["balance"] == pytest.approx(1250.50)


def test_deposit_rejects_negative(app, alice):
    with app.app_context():
        with pytest.raises(DomainError):
            deposit(get_db(), alice["account"], -10)


def test_withdraw_decreases_balance(app, alice):
    with app.app_context():
        db = get_db()
        withdraw(db, alice["account"], 400)
        assert get_account(db, alice["account"])["balance"] == pytest.approx(600)


def test_withdraw_insufficient_funds(app, alice):
    with app.app_context():
        with pytest.raises(DomainError, match="Insufficient"):
            withdraw(get_db(), alice["account"], 9999)


def test_transfer_moves_funds_and_creates_notifications(app, alice, bob):
    with app.app_context():
        db = get_db()
        transfer(db, alice["account"], bob["account"], 300, description="rent")
        assert get_account(db, alice["account"])["balance"] == pytest.approx(700)
        assert get_account(db, bob["account"])["balance"] == pytest.approx(300)
        # Both users should have been notified
        assert any("Sent" in n["message"] for n in get_notifications(db, alice["user_id"]))
        assert any("Received" in n["message"] for n in get_notifications(db, bob["user_id"]))


def test_transfer_rejects_same_account(app, alice):
    with app.app_context():
        with pytest.raises(DomainError):
            transfer(get_db(), alice["account"], alice["account"], 10)


def test_transfer_rejects_insufficient_funds(app, alice, bob):
    with app.app_context():
        with pytest.raises(DomainError, match="Insufficient"):
            transfer(get_db(), alice["account"], bob["account"], 9999)


def test_transfer_unknown_dest(app, alice):
    with app.app_context():
        with pytest.raises(DomainError, match="Recipient"):
            transfer(get_db(), alice["account"], "PL00000000000000000000", 10)


def test_transaction_history_contains_all(app, alice, bob):
    with app.app_context():
        db = get_db()
        deposit(db, alice["account"], 50)
        withdraw(db, alice["account"], 20)
        transfer(db, alice["account"], bob["account"], 10)
        hist = transaction_history(db, alice["account"])
        types = {h["type"] for h in hist}
        assert {"deposit", "withdraw", "transfer"} <= types


def test_admin_block_cascades_to_accounts(app, alice):
    with app.app_context():
        db = get_db()
        admin = db.execute("SELECT user_id FROM users WHERE role='admin'").fetchone()
        set_user_status(db, admin["user_id"], alice["user_id"], "blocked")
        assert get_account(db, alice["account"])["status"] == "blocked"
        with pytest.raises(DomainError):
            deposit(db, alice["account"], 10)


def test_blocked_user_cannot_login(app, alice):
    with app.app_context():
        db = get_db()
        admin = db.execute("SELECT user_id FROM users WHERE role='admin'").fetchone()
        set_user_status(db, admin["user_id"], alice["user_id"], "blocked")
        with pytest.raises(AuthError, match="blocked"):
            authenticate(db, "alice", "pass123")


def test_update_profile(app, alice):
    with app.app_context():
        db = get_db()
        update_profile(db, alice["user_id"], phone="123-456", address="Main 1")
        row = db.execute("SELECT * FROM users WHERE user_id=?",
                         (alice["user_id"],)).fetchone()
        assert row["phone"] == "123-456"
        assert row["address"] == "Main 1"
