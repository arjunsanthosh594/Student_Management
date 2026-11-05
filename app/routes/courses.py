"""
app/routes/courses.py — Course CRUD routes
"""
from flask import Blueprint, render_template, redirect, url_for, flash, request
from flask_login import login_required, current_user
from functools import wraps
from flask import abort

from app.extensions import db
from app.models.course import Course
from app.models.department import Department

courses_bp = Blueprint("courses", __name__)


def admin_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        if not current_user.is_authenticated or current_user.role != "admin":
            abort(403)
        return f(*args, **kwargs)
    return decorated


@courses_bp.route("/courses")
@login_required
@admin_required
def courses():
    search = request.args.get("search", "").strip()
    query = Course.query
    if search:
        like = f"%{search}%"
        query = query.filter(
            Course.course_name.ilike(like) | Course.course_code.ilike(like)
        )
    all_courses = query.order_by(Course.course_name).all()
    return render_template("admin/courses.html", courses=all_courses, search=search)


@courses_bp.route("/courses/add", methods=["GET", "POST"])
@login_required
@admin_required
def add_course():
    departments = Department.query.order_by(Department.dept_name).all()
    if request.method == "POST":
        name = request.form.get("course_name", "").strip()
        code = request.form.get("course_code", "").strip().upper()
        dept_id = request.form.get("department_id", type=int)
        duration = request.form.get("duration", "").strip()
        description = request.form.get("description", "").strip()

        if not name or not code or not dept_id:
            flash("Course name, code, and department are required.", "danger")
            return render_template("admin/add_course.html", departments=departments)

        if Course.query.filter_by(course_code=code).first():
            flash("Course code already exists.", "danger")
            return render_template("admin/add_course.html", departments=departments)

        course = Course(
            course_name=name,
            course_code=code,
            department_id=dept_id,
            duration=duration,
            description=description,
        )
        db.session.add(course)
        db.session.commit()
        flash(f"Course '{name}' added.", "success")
        return redirect(url_for("courses.courses"))

    return render_template("admin/add_course.html", departments=departments)


@courses_bp.route("/courses/<int:cid>/edit", methods=["GET", "POST"])
@login_required
@admin_required
def edit_course(cid):
    course = Course.query.get_or_404(cid)
    departments = Department.query.order_by(Department.dept_name).all()
    if request.method == "POST":
        course.course_name = request.form.get("course_name", course.course_name).strip()
        course.course_code = request.form.get("course_code", course.course_code).strip().upper()
        course.department_id = request.form.get("department_id", course.department_id, type=int)
        course.duration = request.form.get("duration", "").strip()
        course.description = request.form.get("description", "").strip()
        db.session.commit()
        flash("Course updated.", "success")
        return redirect(url_for("courses.courses"))
    return render_template("admin/edit_course.html", course=course, departments=departments)


@courses_bp.route("/courses/<int:cid>/delete", methods=["POST"])
@login_required
@admin_required
def delete_course(cid):
    course = Course.query.get_or_404(cid)
    if course.student_count > 0:
        flash("Cannot delete: course has enrolled students.", "danger")
        return redirect(url_for("courses.courses"))
    db.session.delete(course)
    db.session.commit()
    flash(f"Course '{course.course_name}' deleted.", "success")
    return redirect(url_for("courses.courses"))
