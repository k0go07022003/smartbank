"""Flask application factory for SmartBank.

This package implements the **Application Factory** design pattern: the
:func:`create_app` function is the single place responsible for building
a configured Flask application. Production code (``run.py``) and the
``pytest`` suite both call it, which keeps global state out of the
module import path and makes the database easy to override in tests.

On first startup the factory also seeds a default administrator account
(``admin`` / ``admin123``) so the admin panel can be exercised end to
end without manual database setup.
"""
import os
from flask import Flask
from . import db as db_mod


def create_app(test_config=None):
    """Build and configure a :class:`flask.Flask` instance.

    :param test_config: optional dict used to override configuration
        (e.g. ``DATABASE`` and ``TESTING`` in pytest fixtures).
    :returns: a fully wired Flask app with the ``bank`` blueprint
        registered and the SQLite schema initialised.
    """
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
    """Create the default administrator on a fresh database.

    Idempotent: if an ``admin`` user already exists nothing happens.
    """
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
