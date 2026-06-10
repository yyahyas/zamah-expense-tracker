from flask import Flask, render_template, request, session, redirect, url_for
from werkzeug.security import check_password_hash, generate_password_hash
from database.db import init_db, seed_db, create_user, get_user_by_email, get_user_by_id, update_user, update_password

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
    return render_template("dashboard.html")


@app.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("landing"))


@app.route("/profile")
def profile():
    if not session.get("user_id"):
        return redirect(url_for("login"))
    user = get_user_by_id(session["user_id"])
    return render_template(
        "profile.html",
        user=user,
        message=request.args.get("message"),
        error=request.args.get("error"),
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


if __name__ == "__main__":
    app.run(debug=True, port=5001)
