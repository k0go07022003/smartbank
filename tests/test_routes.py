"""Integration tests driving the Flask HTTP layer."""
from tests.conftest import _login


def test_register_and_login_flow(client):
    r = client.post("/register", data={
        "username": "newuser", "email": "new@user.com",
        "password": "pass123", "full_name": "New User",
    }, follow_redirects=True)
    assert r.status_code == 200

    r = _login(client, "newuser", "pass123")
    assert b"Welcome" in r.data or b"Dashboard" in r.data


def test_login_required_redirects(client):
    r = client.get("/dashboard")
    assert r.status_code == 302
    assert "/login" in r.headers["Location"]


def test_wrong_password_rejected(client, alice):
    r = client.post("/login", data={"username": "alice", "password": "bad"},
                    follow_redirects=True)
    assert b"Invalid" in r.data


def test_dashboard_shows_balance(client, alice):
    _login(client, "alice", "pass123")
    r = client.get("/dashboard")
    assert r.status_code == 200
    assert b"1000.00" in r.data
    assert alice["account"].encode() in r.data


def test_transfer_via_http(client, alice, bob):
    _login(client, "alice", "pass123")
    r = client.post("/transfer", data={
        "source": alice["account"], "dest": bob["account"],
        "amount": "250", "description": "test",
    }, follow_redirects=True)
    assert r.status_code == 200
    assert b"750.00" in r.data  # remaining balance


def test_transfer_insufficient_funds_shows_error(client, alice, bob):
    _login(client, "alice", "pass123")
    r = client.post("/transfer", data={
        "source": alice["account"], "dest": bob["account"],
        "amount": "999999",
    }, follow_redirects=True)
    assert b"Insufficient" in r.data


def test_deposit_and_withdraw_endpoints(client, alice):
    _login(client, "alice", "pass123")
    client.post("/deposit", data={"account": alice["account"], "amount": "100"})
    client.post("/withdraw", data={"account": alice["account"], "amount": "50"})
    r = client.get("/dashboard")
    assert b"1050.00" in r.data


def test_profile_update(client, alice):
    _login(client, "alice", "pass123")
    client.post("/profile", data={"phone": "555-0100", "address": "",
                                   "email": "alice@test.com", "full_name": "Alice"})
    r = client.get("/profile")
    assert b"555-0100" in r.data


def test_customer_cannot_access_admin(client, alice):
    _login(client, "alice", "pass123")
    r = client.get("/admin")
    assert r.status_code == 403


def test_admin_login_and_block_user(client, alice):
    _login(client, "admin", "admin123")
    r = client.get("/admin")
    assert r.status_code == 200
    assert b"alice" in r.data
    client.post(f"/admin/user/{alice['user_id']}/status",
                data={"status": "blocked"}, follow_redirects=True)
    # Alice now blocked
    client.get("/logout")
    r = client.post("/login", data={"username": "alice", "password": "pass123"},
                    follow_redirects=True)
    assert b"blocked" in r.data


def test_api_accounts_returns_json(client, alice):
    _login(client, "alice", "pass123")
    r = client.get("/api/accounts")
    assert r.status_code == 200
    data = r.get_json()
    assert len(data) == 1
    assert data[0]["account_number"] == alice["account"]


def test_cannot_view_other_users_account(client, alice, bob):
    _login(client, "alice", "pass123")
    r = client.get(f"/account/{bob['account']}")
    assert r.status_code == 404


def test_notifications_page_shows_transfer_entry(client, alice, bob):
    _login(client, "alice", "pass123")
    client.post("/transfer", data={"source": alice["account"],
                                    "dest": bob["account"], "amount": "20"})
    r = client.get("/notifications")
    assert b"Sent" in r.data
