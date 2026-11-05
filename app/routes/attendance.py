"""
app/routes/attendance.py — Attendance management routes
"""
from datetime import date, datetime
from functools import wraps
from flask import (Blueprint, render_template, redirect, url_for,
                   flash, request, abort)
from flask_login import login_required, current_user
from sqlalchemy import func

from app.extensions import db
from app.models.attendance import Attendance
from app.models.student import Student
from app.models.course import Course

attendance_bp = Blueprint("attendance", __name__)


def admin_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        if not current_user.is_authenticated or current_user.role != "admin":
            abort(403)
        return f(*args, **kwargs)
    return decorated


@attendance_bp.route("/")
@login_required
@admin_required
def index():
    """Attendance overview: pick date and course to mark attendance."""
    att_date_str = request.args.get("att_date", date.today().isoformat())
    course_id = request.args.get("course_id", type=int)

    try:
        att_date = datetime.strptime(att_date_str, "%Y-%m-%d").date()
    except ValueError:
        att_date = date.today()

    courses = Course.query.order_by(Course.course_name).all()
    students = []
    existing = {}

    if course_id:
        students = Student.query.filter_by(course_id=course_id).order_by(Student.full_name).all()
        # Load existing attendance for the date
        records = Attendance.query.filter_by(attendance_date=att_date).filter(
            Attendance.student_id.in_([s.id for s in students])
        ).all()
        existing = {r.student_id: r.status for r in records}

    return render_template(
        "admin/attendance.html",
        courses=courses,
        students=students,
        att_date=att_date,
        att_date_str=att_date.isoformat(),
        course_id=course_id,
        existing=existing,
    )


@attendance_bp.route("/save", methods=["POST"])
@login_required
@admin_required
def save_attendance():
    att_date_str = request.form.get("att_date", date.today().isoformat())
    course_id = request.form.get("course_id", type=int)

    try:
        att_date = datetime.strptime(att_date_str, "%Y-%m-%d").date()
    except ValueError:
        flash("Invalid date.", "danger")
        return redirect(url_for("attendance.index"))

    students = Student.query.filter_by(course_id=course_id).all()
    saved = 0
    for student in students:
        status = request.form.get(f"status_{student.id}", "Absent")
        if status not in ("Present", "Absent"):
            status = "Absent"

        record = Attendance.query.filter_by(student_id=student.id, attendance_date=att_date).first()
        if record:
            record.status = status
        else:
            record = Attendance(student_id=student.id, attendance_date=att_date, status=status)
            db.session.add(record)
        saved += 1

    db.session.commit()
    flash(f"Attendance saved for {saved} student(s) on {att_date}.", "success")
    return redirect(url_for("attendance.index", att_date=att_date_str, course_id=course_id))


@attendance_bp.route("/history")
@login_required
@admin_required
def history():
    """Filter and view attendance history."""
    page = request.args.get("page", 1, type=int)
    att_date_str = request.args.get("att_date", "")
    course_id = request.args.get("course_id", type=int)
    student_search = request.args.get("student", "").strip()

    from flask import current_app
    per_page = current_app.config.get("ATTENDANCE_PER_PAGE", 15)

    query = Attendance.query.join(Student)

    if att_date_str:
        try:
            att_date = datetime.strptime(att_date_str, "%Y-%m-%d").date()
            query = query.filter(Attendance.attendance_date == att_date)
        except ValueError:
            pass
    if course_id:
        query = query.filter(Student.course_id == course_id)
    if student_search:
        like = f"%{student_search}%"
        query = query.filter(Student.full_name.ilike(like) | Student.student_id.ilike(like))

    pagination = query.order_by(Attendance.attendance_date.desc()).paginate(page=page, per_page=per_page, error_out=False)
    courses = Course.query.order_by(Course.course_name).all()

    return render_template(
        "admin/attendance_history.html",
        pagination=pagination,
        records=pagination.items,
        courses=courses,
        att_date_str=att_date_str,
        course_id=course_id,
        student_search=student_search,
    )


@attendance_bp.route("/student/<int:sid>")
@login_required
@admin_required
def student_report(sid):
    """Individual student attendance report."""
    student = Student.query.get_or_404(sid)
    records = (Attendance.query
               .filter_by(student_id=sid)
               .order_by(Attendance.attendance_date.desc())
               .all())
    return render_template("admin/student_attendance_report.html", student=student, records=records)
