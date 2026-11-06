"""
scripts/seed_db.py — Seed the database with an admin account and sample data.
Run after init_db.py: python scripts/seed_db.py
"""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from datetime import date, timedelta
import random
import getpass
from app import create_app
from app.extensions import db
from app.models.admin import Admin
from app.models.department import Department
from app.models.course import Course
from app.models.student import Student
from app.models.student_user import StudentUser
from app.models.attendance import Attendance

app = create_app()

with app.app_context():
    # ------------------------------------------------------------------
    # Admin account
    # ------------------------------------------------------------------
    if not Admin.query.filter_by(username="admin").first():
        admin = Admin(
            username="admin",
            email="admin@sms.edu",
            full_name="System Administrator",
        )

        admin_password = getpass.getpass(
            "Enter a strong initial admin password (minimum 12 characters): "
        )

        if len(admin_password) < 12:
            raise ValueError("Admin password must contain at least 12 characters.")

        admin.set_password(admin_password)
        db.session.add(admin)
        print("[OK] Admin account created. Password not displayed.")
    else:
        print("[--] Admin account already exists.")


    # ------------------------------------------------------------------
    # Departments
    # ------------------------------------------------------------------
    dept_data = [
        ("CS", "Computer Science", "Department of Computer Science and Engineering"),
        ("EC", "Electronics & Communication", "Department of Electronics and Communication"),
        ("ME", "Mechanical Engineering", "Department of Mechanical Engineering"),
        ("BA", "Business Administration", "Department of Business Administration"),
    ]
    depts = {}
    for code, name, desc in dept_data:
        d = Department.query.filter_by(dept_code=code).first()
        if not d:
            d = Department(dept_code=code, dept_name=name, description=desc)
            db.session.add(d)
            db.session.flush()
            print(f"[OK] Department: {name}")
        depts[code] = d

    # ------------------------------------------------------------------
    # Courses
    # ------------------------------------------------------------------
    course_data = [
        ("CS101", "Bachelor of Computer Science", "CS", "4 Years", "B.Sc. in Computer Science"),
        ("CS201", "Master of Computer Science", "CS", "2 Years", "M.Sc. in Computer Science"),
        ("EC101", "Bachelor of Electronics", "EC", "4 Years", "B.E. in Electronics"),
        ("ME101", "Bachelor of Mechanical Engineering", "ME", "4 Years", "B.E. in Mechanical"),
        ("BA101", "Bachelor of Business Administration", "BA", "3 Years", "BBA"),
    ]
    courses = {}
    for code, name, dept_code, duration, desc in course_data:
        c = Course.query.filter_by(course_code=code).first()
        if not c:
            c = Course(
                course_code=code,
                course_name=name,
                department_id=depts[dept_code].id,
                duration=duration,
                description=desc,
            )
            db.session.add(c)
            db.session.flush()
            print(f"[OK] Course: {name}")
        courses[code] = c

    # ------------------------------------------------------------------
    # Sample Students
    # ------------------------------------------------------------------
    sample_students = [
        ("Alice Johnson", "alice@student.edu", "Female", "CS101"),
        ("Bob Smith", "bob@student.edu", "Male", "CS101"),
        ("Carol White", "carol@student.edu", "Female", "EC101"),
        ("David Brown", "david@student.edu", "Male", "ME101"),
        ("Eva Martinez", "eva@student.edu", "Female", "BA101"),
        ("Frank Lee", "frank@student.edu", "Male", "CS201"),
        ("Grace Kim", "grace@student.edu", "Female", "CS101"),
        ("Henry Davis", "henry@student.edu", "Male", "EC101"),
    ]

    student_password = getpass.getpass(
        "Enter a temporary password for all sample student accounts (minimum 12 characters): "
    )

    if len(student_password) < 12:
        raise ValueError("Student password must contain at least 12 characters.")

    for full_name, email, gender, course_code in sample_students:

        if Student.query.filter_by(email=email).first():
            print(f"[--] Student already exists: {full_name}")
            continue

        course = courses[course_code]
        dept = Department.query.get(course.department_id)

        student = Student(
            full_name=full_name,
            email=email,
            phone=f"98{random.randint(10000000, 99999999)}",
            gender=gender,
            date_of_birth=date(2000, random.randint(1, 12), random.randint(1, 28)),
            address=f"{random.randint(1, 999)} Sample Street, City",
            department_id=dept.id,
            course_id=course.id,
            admission_date=date(2023, 7, 1),
        )
        db.session.add(student)
        db.session.flush()

        # Create student login account
        su = StudentUser(student_id=student.id, username=student.student_id)
        su.set_password(student_password)
        db.session.add(su)
        db.session.flush()

        print(f"[OK] Student: {full_name}  login: {student.student_id}  password set")

        # Generate sample attendance (last 30 days)
        for days_ago in range(30, 0, -1):
            att_date = date.today() - timedelta(days=days_ago)
            if att_date.weekday() >= 5:
                continue
            status = "Present" if random.random() > 0.2 else "Absent"
            att = Attendance(
                student_id=student.id,
                attendance_date=att_date,
                status=status,
            )
            db.session.add(att)

    db.session.commit()
    print("\n[DONE] Database seeded successfully.")
    print("Admin login → username: admin")
    print("Student login → username: <student_id>")
    print("Use the passwords entered during seeding.")
print("       Admin login → username: admin")
print("       Student login → username: <student_id>")
print("       Use the passwords entered during seeding.")
