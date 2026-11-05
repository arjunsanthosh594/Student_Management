"""
app/routes/student.py — Student portal routes
"""
from functools import wraps
from flask import Blueprint, render_template, redirect, url_for, flash, request, abort
from flask_login import login_required, current_user

from app.extensions import db
from app.models.attendance import Attendance
from app.models.student_user import StudentUser
from app.services.s3_service import S3Service

student_bp = Blueprint("student", __name__)


def student_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        if not current_user.is_authenticated or current_user.role != "student":
            abort(403)
        return f(*args, **kwargs)
    return decorated


@student_bp.route("/dashboard")
@login_required
@student_required
def dashboard():
    student = current_user.student
    s3 = S3Service()
    profile_url = None
    if student.profile_picture:
        if student.picture_source == "s3" and s3.is_configured():
            profile_url = s3.get_presigned_url(student.profile_picture)
        else:
            profile_url = url_for("static", filename=student.profile_picture)

    return render_template("student/dashboard.html", student=student, profile_url=profile_url)


@student_bp.route("/profile")
@login_required
@student_required
def profile():
    student = current_user.student
    s3 = S3Service()
    profile_url = None
    if student.profile_picture:
        if student.picture_source == "s3" and s3.is_configured():
            profile_url = s3.get_presigned_url(student.profile_picture)
        else:
            profile_url = url_for("static", filename=student.profile_picture)
    return render_template("student/profile.html", student=student, profile_url=profile_url)


@student_bp.route("/attendance")
@login_required
@student_required
def attendance():
    student = current_user.student
    records = (Attendance.query
               .filter_by(student_id=student.id)
               .order_by(Attendance.attendance_date.desc())
               .all())

    # Monthly summary
    from collections import defaultdict
    monthly = defaultdict(lambda: {"present": 0, "absent": 0})
    for r in records:
        key = r.attendance_date.strftime("%B %Y")
        if r.status == "Present":
            monthly[key]["present"] += 1
        else:
            monthly[key]["absent"] += 1

    return render_template(
        "student/attendance.html",
        student=student,
        records=records,
        monthly=dict(monthly),
    )


@student_bp.route("/change-password", methods=["GET", "POST"])
@login_required
@student_required
def change_password():
    if request.method == "POST":
        current_pw = request.form.get("current_password", "")
        new_pw = request.form.get("new_password", "")
        confirm_pw = request.form.get("confirm_password", "")

        user: StudentUser = current_user

        if not user.check_password(current_pw):
            flash("Current password is incorrect.", "danger")
            return render_template("student/change_password.html")

        if len(new_pw) < 6:
            flash("New password must be at least 6 characters.", "danger")
            return render_template("student/change_password.html")

        if new_pw != confirm_pw:
            flash("New passwords do not match.", "danger")
            return render_template("student/change_password.html")

        user.set_password(new_pw)
        db.session.commit()
        flash("Password changed successfully.", "success")
        return redirect(url_for("student.dashboard"))

    return render_template("student/change_password.html")
