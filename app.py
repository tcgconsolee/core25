import os
from flask import Flask, render_template, redirect, url_for, request, flash
from flask_login import LoginManager, UserMixin, login_user, current_user, login_required, logout_user
from flask_sqlalchemy import SQLAlchemy

app = Flask(__name__)
app.secret_key = os.urandom(24)
app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///db.sqlite"
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

db = SQLAlchemy(app)
login_manager = LoginManager(app)
login_manager.login_view = "login"


class Users(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(250), unique=True, nullable=False)
    password = db.Column(db.String(250), nullable=False)
    is_admin = db.Column(db.Boolean, default=False)  

with app.app_context():
    db.create_all()
    admin = Users.query.filter_by(is_admin=True).first()
    if not admin:
        user = Users(username="admin", password="admin123", is_admin=True)
        db.session.add(user)
        db.session.commit()
        print("✅ Default admin created — username: admin / password: admin123")


@login_manager.user_loader
def loader_user(user_id):
    return Users.query.get(int(user_id))

@app.route('/', methods=["GET", "POST"])
def index():
    if current_user.is_authenticated:
        return redirect(url_for("dashboard"))
    if request.method == "POST":
        user = Users.query.filter_by(username=request.form.get("uname")).first()
        if not user:
            return render_template("index.html", value="USER NOT FOUND")
        if user.password == request.form.get("psw"):
            login_user(user)
            return redirect(url_for("dashboard"))
        else:
            return render_template("index.html", value="WRONG PASSWORD")
    return render_template('index.html')

@app.route("/dashboard")
@login_required
def dashboard():
    return render_template("dashboard.html", user=current_user)

@app.route("/logout")
@login_required
def logout():
    logout_user()
    return redirect(url_for("index"))


@app.route("/login")
def login():
    return redirect(url_for("index"))


@app.route("/admin", methods=["GET", "POST"])
@login_required
def admin_dashboard():
    if not current_user.is_admin:
        flash("Access denied. Admins only.")
        return redirect(url_for("dashboard"))

    if request.method == "POST":
        uname = request.form.get("uname")
        psw = request.form.get("psw")
        email = request.form.get("email")
        is_admin = bool(request.form.get("is_admin"))

        if Users.query.filter_by(username=uname).first():
            flash("Username already exists")
        else:
            user = Users(username=uname, password=psw, is_admin=is_admin)
            db.session.add(user)
            db.session.commit()
            flash(f"User '{uname}' added successfully")

    users = Users.query.all()
    return render_template("admin_dashboard.html", users=users)

@app.route("/admin/delete/<int:user_id>")
@login_required
def delete_user(user_id):
    if not current_user.is_admin:
        flash("Access denied. Admins only.")
        return redirect(url_for("dashboard"))

    user = Users.query.get(user_id)
    if user:
        if user.id == current_user.id:
            flash("You cannot delete your own account.")
        else:
            db.session.delete(user)
            db.session.commit()
            flash(f"User '{user.username}' deleted.")
    return redirect(url_for("admin_dashboard"))

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=10000, debug=True)
