"""
app/routes/auth.py — Authentication routes (login/logout) for Admin and Student
Includes:
- Dual-role authentication
- Login with Username OR Email for Admin
- Login with Student ID OR Email for Student
- Open redirect vulnerability protection (safe URL validation)
- Secure session management and logout
"""
from urllib.parse import urlparse, urljoin
from flask import Blueprint, render_template, redirect, url_for, flash, request, session, current_app
from flask_login import login_user, logout_user, login_required, current_user
from sqlalchemy import or_

from app.extensions import db
from app.models.admin import Admin
from app.models.student import Student
from app.models.student_user import StudentUser

auth_bp = Blueprint("auth", __name__)


def is_safe_url(target: str) -> bool:
    """Validate target redirect URL to prevent Open Redirect attacks."""
    if not target:
        return False
    ref_url = urlparse(request.host_url)
    test_url = urlparse(urljoin(request.host_url, target))
    return test_url.scheme in ("http", "https") and ref_url.netloc == test_url.netloc


@auth_bp.route("/", methods=["GET"])
def index():
    """Root route — redirects authenticated users to their corresponding dashboard."""
    if current_user.is_authenticated:
        if getattr(current_user, "role", None) == "admin":
            return redirect(url_for("admin.dashboard"))
        return redirect(url_for("student.dashboard"))
    return redirect(url_for("auth.login"))


@auth_bp.route("/login", methods=["GET", "POST"])
def login():
    """Handles both Administrator and Student authentication."""
    if current_user.is_authenticated:
        return redirect(url_for("auth.index"))

    if request.method == "POST":
        role = request.form.get("role", "admin").strip().lower()
        credential = request.form.get("username", "").strip()
        password = request.form.get("password", "")

        if not credential or not password:
            flash("Please provide both your identification and password.", "danger")
            return render_template("auth/login.html")

        # -------------------------------------------------------------
        # 1. Administrator Authentication
        # -------------------------------------------------------------
        if role == "admin":
            # Admin can log in using either their username OR their registered email
            admin = Admin.query.filter(
                or_(Admin.username == credential, Admin.email.ilike(credential))
            ).first()

            if admin and admin.check_password(password):
                if not admin.is_active:
                    flash("This administrator account has been disabled.", "danger")
                    return render_template("auth/login.html")

                login_user(admin, remember=False)
                session.permanent = True
                flash(f"Welcome back, {admin.full_name}!", "success")

                next_page = request.args.get("next")
                if next_page and is_safe_url(next_page):
                    return redirect(next_page)
                return redirect(url_for("admin.dashboard"))

            flash("Invalid administrator credentials. Please check your username and password.", "danger")

        # -------------------------------------------------------------
        # 2. Student Authentication
        # -------------------------------------------------------------
        elif role == "student":
            # Student can log in using either their Student ID (StudentUser.username)
            # OR their registered student email (Student.email)
            student_user = None

            # First check direct StudentUser.username (e.g. SMS-202612345)
            student_user = StudentUser.query.filter_by(username=credential).first()

            # If not found by student ID, check if credential is the student's email
            if not student_user:
                student = Student.query.filter(Student.email.ilike(credential)).first()
                if student and student.student_user:
                    student_user = student.student_user

            if student_user and student_user.check_password(password):
                if not student_user.is_active:
                    flash("This student portal account is inactive. Please consult the administrator.", "danger")
                    return render_template("auth/login.html")

                login_user(student_user, remember=False)
                session.permanent = True
                flash(f"Welcome, {student_user.student.full_name}!", "success")

                next_page = request.args.get("next")
                if next_page and is_safe_url(next_page):
                    return redirect(next_page)
                return redirect(url_for("student.dashboard"))

            flash("Invalid student credentials. Please verify your Student ID/Email and password.", "danger")

        else:
            flash("Unrecognized login role selected.", "danger")

    return render_template("auth/login.html")


@auth_bp.route("/logout")
@login_required
def logout():
    """Terminates session and logs user out."""
    logout_user()
    session.clear()
    flash("You have been signed out successfully.", "info")
    return redirect(url_for("auth.login"))
