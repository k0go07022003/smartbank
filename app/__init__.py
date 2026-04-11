"""Flask application factory for SmartBank."""
import os
from flask import Flask
from . import db as db_mod


def create_app(test_config=None):
    app = Flask(__name__, instance_relative_config=True)
    app.config.from_mapping(
        SECRET_KEY=os.environ.get("SMARTBANK_SECRET", "dev-secret-change-me"),
        DATABASE=os.path.join(app.instance_path, "smartbank.sqlite"),
    )
    if test_config:
        app.config.update(test_config)

    os.makedirs(app.instance_path, exist_ok=True)

    app.teardown_appcontext(db_mod.close_db)

    with app.app_context():
        db_mod.init_db()
        _seed_admin()

    from . import routes
    app.register_blueprint(routes.bp)
    return app


def _seed_admin():
    from .db import get_db
    from .models import register_user, DomainError
    db = get_db()
    row = db.execute("SELECT 1 FROM users WHERE username='admin'").fetchone()
    if row is None:
        try:
            register_user(db, "admin", "admin@smartbank.local", "admin123",
                          full_name="System Administrator", role="admin")
        except DomainError:
            pass
