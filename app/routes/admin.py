"""
app/routes/admin.py — Admin routes: dashboard, students, departments
"""
from datetime import date, datetime
from functools import wraps
from flask import (Blueprint, render_template, redirect, url_for,
                   flash, request, current_app, abort)
from flask_login import login_required, current_user
from sqlalchemy import func
from werkzeug.utils import secure_filename
import os
import uuid
from urllib.parse import urlparse, unquote
from app.extensions import db
from app.models.admin import Admin
from app.models.student import Student
from app.models.student_user import StudentUser
from app.models.course import Course
from app.models.department import Department
from app.models.attendance import Attendance
from app.services.s3_service import S3Service

admin_bp = Blueprint("admin", __name__)


def get_s3_object_key(image_url):
    """Extract and validate an S3 object key from an S3 URI or HTTPS URL."""
    if not image_url:
        return None

    bucket = current_app.config.get("S3_BUCKET_NAME", "")
    if not bucket:
        return None

    parsed = urlparse(image_url.strip())

    if parsed.scheme == "s3":
        if parsed.netloc != bucket:
            return None
        key = unquote(parsed.path.lstrip("/"))
    elif parsed.scheme == "https":
        host = (parsed.hostname or "").lower()
        valid_host = (
            host == f"{bucket}.s3.amazonaws.com"
            or host.startswith(f"{bucket}.s3.")
            or host.startswith(f"{bucket}.s3-")
        )
        if not valid_host:
            return None
        key = unquote(parsed.path.lstrip("/"))
    else:
        return None

    if not key or ".." in key.split("/"):
        return None

    return key


# ------------------------------------------------------------------
# Decorators
# ------------------------------------------------------------------
def admin_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        if not current_user.is_authenticated or current_user.role != "admin":
            abort(403)
        return f(*args, **kwargs)
    return decorated


def allowed_file(filename: str) -> bool:
    allowed = current_app.config.get("ALLOWED_EXTENSIONS", {"png", "jpg", "jpeg", "gif", "webp"})
    return "." in filename and filename.rsplit(".", 1)[1].lower() in allowed


# ------------------------------------------------------------------
# Dashboard
# ------------------------------------------------------------------
@admin_bp.route("/dashboard")
@login_required
@admin_required
def dashboard():
    today = date.today()

    total_students = Student.query.count()
    total_courses = Course.query.count()
    total_departments = Department.query.count()

    present_today = Attendance.query.filter_by(attendance_date=today, status="Present").count()
    absent_today = Attendance.query.filter_by(attendance_date=today, status="Absent").count()

    total_att = Attendance.query.count()
    total_present_all = Attendance.query.filter_by(status="Present").count()
    overall_pct = round((total_present_all / total_att * 100), 2) if total_att > 0 else 0.0

    recent_students = (Student.query
                       .order_by(Student.created_at.desc())
                       .limit(5).all())

    # Monthly enrolment data for chart (last 6 months)
    enrolment_data = []
    current_year = today.year
    current_month = today.month

    for i in range(5, -1, -1):
        m = current_month - i
        y = current_year
        while m <= 0:
            m += 12
            y -= 1
        month_start = date(y, m, 1)
        next_m = m + 1
        next_y = y
        if next_m > 12:
            next_m = 1
            next_y += 1
        month_end = date(next_y, next_m, 1)

        count = Student.query.filter(
            Student.admission_date >= month_start,
            Student.admission_date < month_end
        ).count()
        enrolment_data.append({
            "month": month_start.strftime("%b %Y"),
            "count": count
        })

    return render_template(
        "admin/dashboard.html",
        total_students=total_students,
        total_courses=total_courses,
        total_departments=total_departments,
        present_today=present_today,
        absent_today=absent_today,
        overall_pct=overall_pct,
        recent_students=recent_students,
        enrolment_data=enrolment_data,
        today=today,
    )


# ------------------------------------------------------------------
# Students — List
# ------------------------------------------------------------------
@admin_bp.route("/students")
@login_required
@admin_required
def students():
    page = request.args.get("page", 1, type=int)
    search = request.args.get("search", "").strip()
    dept_filter = request.args.get("department", "", type=str)
    course_filter = request.args.get("course", "", type=str)
    gender_filter = request.args.get("gender", "").strip()

    per_page = current_app.config.get("STUDENTS_PER_PAGE", 10)

    query = Student.query

    if search:
        like = f"%{search}%"
        query = query.filter(
            (Student.full_name.ilike(like)) |
            (Student.student_id.ilike(like)) |
            (Student.email.ilike(like))
        )
    if dept_filter:
        query = query.filter(Student.department_id == dept_filter)
    if course_filter:
        query = query.filter(Student.course_id == course_filter)
    if gender_filter:
        query = query.filter(Student.gender == gender_filter)

    pagination = query.order_by(Student.created_at.desc()).paginate(page=page, per_page=per_page, error_out=False)
    departments = Department.query.order_by(Department.dept_name).all()
    courses = Course.query.order_by(Course.course_name).all()

    return render_template(
        "admin/students.html",
        pagination=pagination,
        students=pagination.items,
        departments=departments,
        courses=courses,
        search=search,
        dept_filter=dept_filter,
        course_filter=course_filter,
        gender_filter=gender_filter,
    )


# ------------------------------------------------------------------
# Students — Add
# ------------------------------------------------------------------
@admin_bp.route("/students/add", methods=["GET", "POST"])
@login_required
@admin_required
def add_student():
    departments = Department.query.order_by(Department.dept_name).all()
    courses = Course.query.order_by(Course.course_name).all()

    if request.method == "POST":
        full_name = request.form.get("full_name", "").strip()
        email = request.form.get("email", "").strip().lower()
        phone = request.form.get("phone", "").strip()
        gender = request.form.get("gender", "")
        dob_str = request.form.get("date_of_birth", "")
        address = request.form.get("address", "").strip()
        dept_id = request.form.get("department_id", type=int)
        course_id = request.form.get("course_id", type=int)
        admission_str = request.form.get("admission_date", "")
        password = request.form.get("password", "")

        # Validate required fields.
        errors = []
        if not full_name:
            errors.append("Full name is required.")
        if not email:
            errors.append("Email is required.")
        elif Student.query.filter_by(email=email).first():
            errors.append("A student with this email already exists.")
        if not gender:
            errors.append("Gender is required.")
        if not dept_id:
            errors.append("Department is required.")
        if not course_id:
            errors.append("Course is required.")
        if not password or len(password) < 6:
            errors.append("Password must be at least 6 characters.")

        if errors:
            for error in errors:
                flash(error, "danger")
            return render_template(
                "admin/add_student.html",
                departments=departments,
                courses=courses
            )

        # Parse optional dates.
        dob = datetime.strptime(dob_str, "%Y-%m-%d").date() if dob_str else None
        admission_date = (
            datetime.strptime(admission_str, "%Y-%m-%d").date()
            if admission_str else None
        )

        # Handle profile picture: accept an S3 URL or an uploaded file.
        picture_path = None
        picture_source = "local"
        image_url = request.form.get("profile_picture_url", "").strip()
        file = request.files.get("profile_picture")
        s3 = S3Service()

        if image_url:
            key = get_s3_object_key(image_url)
            if not key:
                flash("Invalid S3 image URL. Please check the bucket URL.", "danger")
                return render_template(
                    "admin/add_student.html",
                    departments=departments,
                    courses=courses
                )
            if not s3.is_configured():
                flash("S3 is not configured.", "danger")
                return render_template(
                    "admin/add_student.html",
                    departments=departments,
                    courses=courses
                )
            picture_path = key
            picture_source = "s3"

        elif file and file.filename and allowed_file(file.filename):
            filename = secure_filename(f"{uuid.uuid4().hex}_{file.filename}")

            if s3.is_configured():
                # Keep uploads under students/* to match the EC2 IAM policy.
                key = f"students/{filename}"
                if s3.upload_file(file, key):
                    picture_path = key
                    picture_source = "s3"
                else:
                    flash("Unable to upload profile image to S3.", "danger")
                    return render_template(
                        "admin/add_student.html",
                        departments=departments,
                        courses=courses
                    )
            else:
                upload_dir = os.path.join(
                    current_app.root_path, "static", "images", "uploads"
                )
                os.makedirs(upload_dir, exist_ok=True)
                file.save(os.path.join(upload_dir, filename))
                picture_path = f"images/uploads/{filename}"
                picture_source = "local"

        # Save student and corresponding login account together.
        student = Student(
            full_name=full_name,
            email=email,
            phone=phone,
            gender=gender,
            date_of_birth=dob,
            address=address,
            department_id=dept_id,
            course_id=course_id,
            admission_date=admission_date,
            profile_picture=picture_path,
            picture_source=picture_source,
        )

        try:
            db.session.add(student)
            db.session.flush()

            student_user = StudentUser(
                student_id=student.id,
                username=student.student_id
            )
            student_user.set_password(password)
            db.session.add(student_user)

            db.session.commit()
        except Exception:
            db.session.rollback()
            current_app.logger.exception("Unable to add student")
            flash("Unable to add student. Check the application log.", "danger")
            return render_template(
                "admin/add_student.html",
                departments=departments,
                courses=courses
            )

        flash(
            f"Student '{full_name}' added successfully! Login: {student.student_id}",
            "success"
        )
        return redirect(url_for("admin.students"))

    return render_template(
        "admin/add_student.html",
        departments=departments,
        courses=courses
    )


# ------------------------------------------------------------------
# Students — View Profile
# ------------------------------------------------------------------
@admin_bp.route("/students/<int:sid>")
@login_required
@admin_required
def view_student(sid):
    student = Student.query.get_or_404(sid)
    s3 = S3Service()
    profile_url = None
    if student.profile_picture:
        if student.picture_source == "s3" and s3.is_configured():
            profile_url = s3.get_presigned_url(student.profile_picture)
        else:
            profile_url = url_for("static", filename=student.profile_picture)
    return render_template("admin/view_student.html", student=student, profile_url=profile_url)


# ------------------------------------------------------------------
# Students — Edit
# ------------------------------------------------------------------
@admin_bp.route("/students/<int:sid>/edit", methods=["GET", "POST"])
@login_required
@admin_required
def edit_student(sid):
    student = Student.query.get_or_404(sid)
    departments = Department.query.order_by(Department.dept_name).all()
    courses = Course.query.order_by(Course.course_name).all()

    if request.method == "POST":
        student.full_name = request.form.get("full_name", student.full_name).strip()
        new_email = request.form.get("email", student.email).strip().lower()
        if new_email != student.email and Student.query.filter_by(email=new_email).first():
            flash("Another student already uses this email.", "danger")
            return render_template("admin/edit_student.html", student=student, departments=departments, courses=courses)
        student.email = new_email
        student.phone = request.form.get("phone", "").strip()
        student.gender = request.form.get("gender", student.gender)
        dob_str = request.form.get("date_of_birth", "")
        student.date_of_birth = datetime.strptime(dob_str, "%Y-%m-%d").date() if dob_str else student.date_of_birth
        student.address = request.form.get("address", "").strip()
        student.department_id = request.form.get("department_id", student.department_id, type=int)
        student.course_id = request.form.get("course_id", student.course_id, type=int)
        adm_str = request.form.get("admission_date", "")
        student.admission_date = datetime.strptime(adm_str, "%Y-%m-%d").date() if adm_str else student.admission_date

        # Handle new profile picture
        file = request.files.get("profile_picture")
        s3 = S3Service()
        if file and file.filename and allowed_file(file.filename):
            filename = secure_filename(f"{uuid.uuid4().hex}_{file.filename}")
            if s3.is_configured():
                # Delete old S3 object if exists
                if student.profile_picture and student.picture_source == "s3":
                    s3.delete_file(student.profile_picture)
                key = f"students/{filename}"
                s3.upload_file(file, key)
                student.profile_picture = key
                student.picture_source = "s3"
            else:
                # Delete old local file
                if student.profile_picture and student.picture_source == "local":
                    old_path = os.path.join(current_app.root_path, "static", student.profile_picture)
                    if os.path.exists(old_path):
                        os.remove(old_path)
                upload_dir = os.path.join(current_app.root_path, "static", "images", "uploads")
                file.save(os.path.join(upload_dir, filename))
                student.profile_picture = f"images/uploads/{filename}"
                student.picture_source = "local"

        db.session.commit()
        flash(f"Student '{student.full_name}' updated successfully.", "success")
        return redirect(url_for("admin.view_student", sid=student.id))

    s3 = S3Service()
    profile_url = None
    if student.profile_picture:
        if student.picture_source == "s3" and s3.is_configured():
            profile_url = s3.get_presigned_url(student.profile_picture)
        else:
            profile_url = url_for("static", filename=student.profile_picture)

    return render_template("admin/edit_student.html", student=student,
                           departments=departments, courses=courses, profile_url=profile_url)


# ------------------------------------------------------------------
# Students — Delete
# ------------------------------------------------------------------
@admin_bp.route("/students/<int:sid>/delete", methods=["POST"])
@login_required
@admin_required
def delete_student(sid):
    student = Student.query.get_or_404(sid)
    name = student.full_name

    # Remove profile picture
    s3 = S3Service()
    if student.profile_picture:
        if student.picture_source == "s3" and s3.is_configured():
            s3.delete_file(student.profile_picture)
        elif student.picture_source == "local":
            path = os.path.join(current_app.root_path, "static", student.profile_picture)
            if os.path.exists(path):
                os.remove(path)

    db.session.delete(student)
    db.session.commit()
    flash(f"Student '{name}' deleted successfully.", "success")
    return redirect(url_for("admin.students"))


# ------------------------------------------------------------------
# Departments — CRUD
# ------------------------------------------------------------------
@admin_bp.route("/departments")
@login_required
@admin_required
def departments():
    depts = Department.query.order_by(Department.dept_name).all()
    return render_template("admin/departments.html", departments=depts)


@admin_bp.route("/departments/add", methods=["GET", "POST"])
@login_required
@admin_required
def add_department():
    if request.method == "POST":
        name = request.form.get("dept_name", "").strip()
        code = request.form.get("dept_code", "").strip().upper()
        desc = request.form.get("description", "").strip()

        if not name or not code:
            flash("Department name and code are required.", "danger")
            return render_template("admin/add_department.html")

        if Department.query.filter_by(dept_code=code).first():
            flash("Department code already exists.", "danger")
            return render_template("admin/add_department.html")

        if Department.query.filter_by(dept_name=name).first():
            flash("Department name already exists.", "danger")
            return render_template("admin/add_department.html")

        dept = Department(dept_name=name, dept_code=code, description=desc)
        db.session.add(dept)
        db.session.commit()
        flash(f"Department '{name}' added.", "success")
        return redirect(url_for("admin.departments"))

    return render_template("admin/add_department.html")


@admin_bp.route("/departments/<int:did>/edit", methods=["GET", "POST"])
@login_required
@admin_required
def edit_department(did):
    dept = Department.query.get_or_404(did)
    if request.method == "POST":
        dept.dept_name = request.form.get("dept_name", dept.dept_name).strip()
        dept.dept_code = request.form.get("dept_code", dept.dept_code).strip().upper()
        dept.description = request.form.get("description", "").strip()
        db.session.commit()
        flash("Department updated.", "success")
        return redirect(url_for("admin.departments"))
    return render_template("admin/edit_department.html", dept=dept)


@admin_bp.route("/departments/<int:did>/delete", methods=["POST"])
@login_required
@admin_required
def delete_department(did):
    dept = Department.query.get_or_404(did)
    if dept.student_count > 0 or dept.course_count > 0:
        flash("Cannot delete: department has assigned students or courses.", "danger")
        return redirect(url_for("admin.departments"))
    db.session.delete(dept)
    db.session.commit()
    flash(f"Department '{dept.dept_name}' deleted.", "success")
    return redirect(url_for("admin.departments"))
