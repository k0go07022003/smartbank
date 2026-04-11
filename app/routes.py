"""HTTP routes for SmartBank (server-rendered + a small JSON API)."""
from functools import wraps
from flask import (Blueprint, render_template, request, redirect, url_for,
                   session, flash, jsonify, abort)
from .db import get_db
from . import models as m

bp = Blueprint("bank", __name__)


# ---------- auth helpers ----------

def login_required(view):
    @wraps(view)
    def wrapped(*a, **kw):
        if "user_id" not in session:
            return redirect(url_for("bank.login"))
        return view(*a, **kw)
    return wrapped


def admin_required(view):
    @wraps(view)
    def wrapped(*a, **kw):
        if session.get("role") != "admin":
            abort(403)
        return view(*a, **kw)
    return wrapped


# ---------- public ----------

@bp.route("/")
def index():
    if "user_id" in session:
        return redirect(url_for("bank.dashboard"))
    return redirect(url_for("bank.login"))


@bp.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        try:
            uid = m.register_user(
                get_db(),
                request.form["username"].strip(),
                request.form["email"].strip(),
                request.form["password"],
                full_name=request.form.get("full_name", "").strip() or None,
            )
            flash("Account created. Please log in.", "success")
            return redirect(url_for("bank.login"))
        except m.DomainError as e:
            flash(str(e), "error")
    return render_template("register.html")


@bp.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        try:
            user = m.authenticate(
                get_db(),
                request.form["username"].strip(),
                request.form["password"],
            )
            session.clear()
            session["user_id"] = user["user_id"]
            session["username"] = user["username"]
            session["role"] = user["role"]
            if user["role"] == "admin":
                return redirect(url_for("bank.admin_panel"))
            return redirect(url_for("bank.dashboard"))
        except m.AuthError as e:
            flash(str(e), "error")
    return render_template("login.html")


@bp.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("bank.login"))


# ---------- customer ----------

@bp.route("/dashboard")
@login_required
def dashboard():
    db = get_db()
    user = m.get_user(db, session["user_id"])
    accounts = m.get_accounts(db, user["user_id"])
    notifications = m.get_notifications(db, user["user_id"], limit=5)
    return render_template("dashboard.html", user=user, accounts=accounts,
                           notifications=notifications)


@bp.route("/account/<account_number>")
@login_required
def account_detail(account_number):
    db = get_db()
    acc = m.get_account(db, account_number)
    if acc is None or acc["user_id"] != session["user_id"]:
        abort(404)
    history = m.transaction_history(db, account_number)
    return render_template("account.html", account=acc, history=history)


@bp.route("/deposit", methods=["GET", "POST"])
@login_required
def deposit():
    db = get_db()
    accounts = m.get_accounts(db, session["user_id"])
    if request.method == "POST":
        try:
            m.deposit(db, request.form["account"], float(request.form["amount"]),
                      description=request.form.get("description", "Deposit"))
            flash("Deposit successful", "success")
            return redirect(url_for("bank.dashboard"))
        except (m.DomainError, ValueError) as e:
            flash(str(e), "error")
    return render_template("deposit.html", accounts=accounts)


@bp.route("/withdraw", methods=["GET", "POST"])
@login_required
def withdraw():
    db = get_db()
    accounts = m.get_accounts(db, session["user_id"])
    if request.method == "POST":
        try:
            m.withdraw(db, request.form["account"], float(request.form["amount"]),
                       description=request.form.get("description", "Withdraw"))
            flash("Withdrawal successful", "success")
            return redirect(url_for("bank.dashboard"))
        except (m.DomainError, ValueError) as e:
            flash(str(e), "error")
    return render_template("withdraw.html", accounts=accounts)


@bp.route("/transfer", methods=["GET", "POST"])
@login_required
def transfer():
    db = get_db()
    accounts = m.get_accounts(db, session["user_id"])
    if request.method == "POST":
        try:
            m.transfer(
                db,
                request.form["source"],
                request.form["dest"].strip(),
                float(request.form["amount"]),
                description=request.form.get("description", ""),
            )
            flash("Transfer completed", "success")
            return redirect(url_for("bank.dashboard"))
        except (m.DomainError, ValueError) as e:
            flash(str(e), "error")
    return render_template("transfer.html", accounts=accounts)


@bp.route("/profile", methods=["GET", "POST"])
@login_required
def profile():
    db = get_db()
    if request.method == "POST":
        m.update_profile(
            db, session["user_id"],
            full_name=request.form.get("full_name") or None,
            address=request.form.get("address") or None,
            phone=request.form.get("phone") or None,
            email=request.form.get("email") or None,
        )
        flash("Profile updated", "success")
        return redirect(url_for("bank.profile"))
    user = m.get_user(db, session["user_id"])
    return render_template("profile.html", user=user)


@bp.route("/notifications")
@login_required
def notifications():
    db = get_db()
    items = m.get_notifications(db, session["user_id"], limit=50)
    return render_template("notifications.html", notifications=items)


# ---------- admin ----------

@bp.route("/admin")
@login_required
@admin_required
def admin_panel():
    db = get_db()
    users = m.list_users(db)
    txs = m.all_transactions(db, limit=50)
    return render_template("admin.html", users=users, transactions=txs)


@bp.route("/admin/user/<int:user_id>/status", methods=["POST"])
@login_required
@admin_required
def admin_set_status(user_id):
    db = get_db()
    try:
        m.set_user_status(db, session["user_id"], user_id,
                          request.form["status"])
        flash("User status updated", "success")
    except m.DomainError as e:
        flash(str(e), "error")
    return redirect(url_for("bank.admin_panel"))


# ---------- JSON API ----------

@bp.route("/api/accounts")
@login_required
def api_accounts():
    return jsonify(m.get_accounts(get_db(), session["user_id"]))


@bp.route("/api/transactions/<account_number>")
@login_required
def api_transactions(account_number):
    db = get_db()
    acc = m.get_account(db, account_number)
    if acc is None or acc["user_id"] != session["user_id"]:
        abort(404)
    return jsonify(m.transaction_history(db, account_number))
