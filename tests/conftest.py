import os
import tempfile
import pytest
from app import create_app
from app.db import get_db
from app.models import register_user, deposit


@pytest.fixture
def app():
    fd, path = tempfile.mkstemp(suffix=".sqlite")
    os.close(fd)
    app = create_app({"TESTING": True, "DATABASE": path, "SECRET_KEY": "t"})
    yield app
    os.unlink(path)


@pytest.fixture
def client(app):
    return app.test_client()


@pytest.fixture
def alice(app):
    with app.app_context():
        db = get_db()
        uid = register_user(db, "alice", "alice@test.com", "pass123",
                            full_name="Alice Test")
        acc = db.execute("SELECT account_number FROM accounts WHERE user_id=?",
                         (uid,)).fetchone()["account_number"]
        deposit(db, acc, 1000.0, "seed")
        return {"user_id": uid, "account": acc}


@pytest.fixture
def bob(app):
    with app.app_context():
        db = get_db()
        uid = register_user(db, "bob", "bob@test.com", "pass123",
                            full_name="Bob Test")
        acc = db.execute("SELECT account_number FROM accounts WHERE user_id=?",
                         (uid,)).fetchone()["account_number"]
        return {"user_id": uid, "account": acc}


def _login(client, username, password):
    return client.post("/login", data={"username": username, "password": password},
                       follow_redirects=True)
