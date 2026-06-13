from flask import Flask, render_template, request, session, redirect, url_for
from werkzeug.security import check_password_hash, generate_password_hash
from datetime import date
import calendar
from database.db import init_db, seed_db, create_user, get_user_by_email, get_user_by_id, update_user, update_password, get_expenses, get_expense_totals, get_expenses_by_category, get_expenses_filtered

app = Flask(__name__)
app.secret_key = "zamah-dev-secret"

with app.app_context():
    init_db()
    seed_db()


# ------------------------------------------------------------------ #
# Routes                                                              #
# ------------------------------------------------------------------ #

@app.route("/")
def landing():
    return render_template("landing.html")


@app.route("/register", methods=["GET", "POST"])
def register():
    if session.get("user_id"):
        return redirect(url_for("dashboard"))

    if request.method == "POST":
        name = request.form.get("name", "").strip()
        email = request.form.get("email", "").strip()
        password = request.form.get("password", "")
        confirm_password = request.form.get("confirm_password", "")

        if not name:
            return render_template("register.html", error="Name is required.", name=name, email=email)
        if not email:
            return render_template("register.html", error="Email is required.", name=name, email=email)
        if len(password) < 8:
            return render_template("register.html", error="Password must be at least 8 characters.", name=name, email=email)
        if password != confirm_password:
            return render_template("register.html", error="Passwords do not match.", name=name, email=email)
        if get_user_by_email(email):
            return render_template("register.html", error="Email already registered.", name=name, email=email)

        user_id = create_user(name, email, password)
        session["user_id"] = user_id
        session["user_name"] = name
        return redirect(url_for("dashboard"))

    return render_template("register.html")


@app.route("/login", methods=["GET", "POST"])
def login():
    if session.get("user_id"):
        return redirect(url_for("dashboard"))

    if request.method == "POST":
        email = request.form.get("email", "").strip()
        password = request.form.get("password", "")

        user = get_user_by_email(email) if email else None
        if not user or not password or not check_password_hash(user["password_hash"], password):
            return render_template("login.html", error="Invalid email or password.", email=email)

        session["user_id"] = user["id"]
        session["user_name"] = user["name"]
        return redirect(url_for("dashboard"))

    return render_template("login.html")


@app.route("/terms")
def terms():
    return render_template("terms.html")


@app.route("/privacy")
def privacy():
    return render_template("privacy.html")


# ------------------------------------------------------------------ #
# Placeholder routes — students will implement these                  #
# ------------------------------------------------------------------ #

@app.route("/dashboard")
def dashboard():
    if not session.get("user_id"):
        return redirect(url_for("login"))
    totals = get_expense_totals(session["user_id"])
    recent = get_expenses(session["user_id"])[:5]
    return render_template("dashboard.html", totals=totals, recent=recent)


@app.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("landing"))


@app.route("/profile")
def profile():
    if not session.get("user_id"):
        return redirect(url_for("login"))

    today = date.today()
    period = request.args.get("period", "month")

    def _valid_date(s):
        try:
            date.fromisoformat(s)
            return True
        except (ValueError, TypeError):
            return False

    if period == "all":
        from_date = ""
        to_date = ""
        expenses = get_expenses(session["user_id"])
    elif period == "6months":
        month = today.month - 6
        year = today.year
        if month <= 0:
            month += 12
            year -= 1
        try:
            start = date(year, month, today.day)
        except ValueError:
            start = date(year, month, calendar.monthrange(year, month)[1])
        from_date = start.strftime("%Y-%m-%d")
        to_date = today.strftime("%Y-%m-%d")
        expenses = get_expenses_filtered(session["user_id"], from_date, to_date)
    elif period == "custom":
        from_date = request.args.get("from_date", "")
        to_date = request.args.get("to_date", "")
        if not _valid_date(from_date):
            from_date = today.replace(day=1).strftime("%Y-%m-%d")
        if not _valid_date(to_date):
            to_date = today.replace(day=calendar.monthrange(today.year, today.month)[1]).strftime("%Y-%m-%d")
        expenses = get_expenses_filtered(session["user_id"], from_date, to_date)
    else:
        period = "month"
        from_date = today.replace(day=1).strftime("%Y-%m-%d")
        to_date = today.replace(day=calendar.monthrange(today.year, today.month)[1]).strftime("%Y-%m-%d")
        expenses = get_expenses_filtered(session["user_id"], from_date, to_date)

    filtered_total = sum(row["amount"] for row in expenses)
    user = get_user_by_id(session["user_id"])

    return render_template(
        "profile.html",
        user=user,
        message=request.args.get("message"),
        error=request.args.get("error"),
        expenses=expenses,
        filtered_total=filtered_total,
        from_date=from_date,
        to_date=to_date,
        period=period,
    )


@app.route("/profile", methods=["POST"])
def profile_update():
    if not session.get("user_id"):
        return redirect(url_for("login"))

    name = request.form.get("name", "").strip()
    email = request.form.get("email", "").strip()

    if not name:
        return redirect(url_for("profile", error="Name is required."))
    if not email:
        return redirect(url_for("profile", error="Email is required."))

    existing = get_user_by_email(email)
    if existing and existing["id"] != session["user_id"]:
        return redirect(url_for("profile", error="That email is already used by another account."))

    update_user(session["user_id"], name, email)
    session["user_name"] = name
    return redirect(url_for("profile", message="Account details updated."))


@app.route("/profile/password", methods=["POST"])
def profile_password():
    if not session.get("user_id"):
        return redirect(url_for("login"))

    current_password = request.form.get("current_password", "")
    new_password = request.form.get("new_password", "")
    confirm_password = request.form.get("confirm_password", "")

    if not current_password:
        return redirect(url_for("profile", error="Current password is required."))
    if len(new_password) < 8:
        return redirect(url_for("profile", error="New password must be at least 8 characters."))
    if new_password != confirm_password:
        return redirect(url_for("profile", error="New passwords do not match."))

    user = get_user_by_id(session["user_id"])
    if not check_password_hash(user["password_hash"], current_password):
        return redirect(url_for("profile", error="Current password is incorrect."))

    update_password(session["user_id"], generate_password_hash(new_password))
    return redirect(url_for("profile", message="Password changed successfully."))


@app.route("/expenses/add")
def add_expense():
    return "Add expense — coming in Step 7"


@app.route("/expenses/<int:id>/edit")
def edit_expense(id):
    return "Edit expense — coming in Step 8"


@app.route("/expenses/<int:id>/delete")
def delete_expense(id):
    return "Delete expense — coming in Step 9"


# ------------------------------------------------------------------ #
# Transaction History                                                  #
# ------------------------------------------------------------------ #

@app.route("/expenses")
def expense_list():
    if not session.get("user_id"):
        return redirect(url_for("login"))
    expenses = get_expenses(session["user_id"])
    return render_template("expenses.html", expenses=expenses)


# ------------------------------------------------------------------ #
# Category Breakdown                                                   #
# ------------------------------------------------------------------ #

@app.route("/expenses/categories")
def category_breakdown():
    if not session.get("user_id"):
        return redirect(url_for("login"))
    categories = get_expenses_by_category(session["user_id"])
    return render_template("category_breakdown.html", categories=categories)


if __name__ == "__main__":
    app.run(debug=True, port=5001)
