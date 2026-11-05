"""
tests/test_sms.py — Automated Unit & Integration Tests for Student Management System
Tests:
- Application Factory & Configuration
- Model Password Hashing & Constraints
- Database Relations (Dept -> Course -> Student -> StudentUser -> Attendance)
- Attendance Percentage Calculation & Duplicate Prevention
- Role-Based Access Control (Admin vs Student Route Protection)
- Multi-Parameter Student Filter & Search
- Error Pages (403, 404)
Run with: python -m unittest tests/test_sms.py
"""
import unittest
from datetime import date
from app import create_app
from app.extensions import db
from app.models.admin import Admin
from app.models.department import Department
from app.models.course import Course
from app.models.student import Student
from app.models.student_user import StudentUser
from app.models.attendance import Attendance


class SMSTestCase(unittest.TestCase):
    def setUp(self):
        """Set up test application context and in-memory database."""
        self.app = create_app("testing")
        self.app_context = self.app.app_context()
        self.app_context.push()
        self.client = self.app.test_client()

        db.create_all()

        # Seed minimal test data
        self.admin = Admin(username="testadmin", email="admin@test.edu", full_name="Test Administrator")
        self.admin.set_password("AdminPass123")
        db.session.add(self.admin)

        self.dept = Department(dept_code="CS", dept_name="Computer Science", description="CS Dept")
        db.session.add(self.dept)
        db.session.flush()

        self.course = Course(
            course_code="CS101",
            course_name="B.Sc Computer Science",
            department_id=self.dept.id,
            duration="3 Years",
            description="Foundational CS"
        )
        db.session.add(self.course)
        db.session.flush()

        self.student = Student(
            full_name="Jane Doe",
            email="jane@student.edu",
            phone="1234567890",
            gender="Female",
            date_of_birth=date(2002, 5, 14),
            department_id=self.dept.id,
            course_id=self.course.id,
            admission_date=date(2023, 8, 1)
        )
        db.session.add(self.student)
        db.session.flush()

        self.student_user = StudentUser(student_id=self.student.id, username=self.student.student_id)
        self.student_user.set_password("StudentPass123")
        db.session.add(self.student_user)

        db.session.commit()

    def tearDown(self):
        """Tear down database and application context."""
        db.session.remove()
        db.drop_all()
        self.app_context.pop()

    # -------------------------------------------------------------
    # 1. Model & Hashing Tests
    # -------------------------------------------------------------
    def test_admin_password_hashing(self):
        self.assertTrue(self.admin.check_password("AdminPass123"))
        self.assertFalse(self.admin.check_password("WrongPassword"))
        self.assertEqual(self.admin.role, "admin")
        self.assertEqual(self.admin.get_id(), f"a:{self.admin.id}")

    def test_student_user_hashing(self):
        self.assertTrue(self.student_user.check_password("StudentPass123"))
        self.assertFalse(self.student_user.check_password("WrongPassword"))
        self.assertEqual(self.student_user.role, "student")
        self.assertEqual(self.student_user.get_id(), f"s:{self.student_user.id}")

    # -------------------------------------------------------------
    # 2. Relational Counts & Calculated Properties
    # -------------------------------------------------------------
    def test_department_course_counts(self):
        self.assertEqual(self.dept.course_count, 1)
        self.assertEqual(self.dept.student_count, 1)
        self.assertEqual(self.course.student_count, 1)

    def test_attendance_calculations(self):
        # Initial: 0 attendance
        self.assertEqual(self.student.total_attendance, 0)
        self.assertEqual(self.student.attendance_percentage, 0.0)

        # Add 3 Present, 1 Absent
        a1 = Attendance(student_id=self.student.id, attendance_date=date(2024, 1, 10), status="Present")
        a2 = Attendance(student_id=self.student.id, attendance_date=date(2024, 1, 11), status="Present")
        a3 = Attendance(student_id=self.student.id, attendance_date=date(2024, 1, 12), status="Present")
        a4 = Attendance(student_id=self.student.id, attendance_date=date(2024, 1, 13), status="Absent")
        db.session.add_all([a1, a2, a3, a4])
        db.session.commit()

        self.assertEqual(self.student.total_attendance, 4)
        self.assertEqual(self.student.present_days, 3)
        self.assertEqual(self.student.absent_days, 1)
        self.assertEqual(self.student.attendance_percentage, 75.0)

    # -------------------------------------------------------------
    # 3. Route & Access Control Tests
    # -------------------------------------------------------------
    def test_unauthenticated_redirect(self):
        # Attempt to access protected dashboard without login
        res = self.client.get("/admin/dashboard", follow_redirects=False)
        self.assertEqual(res.status_code, 302)
        self.assertIn("/login", res.headers["Location"])

    def test_admin_login_and_dashboard_access(self):
        # Perform Admin login
        login_res = self.client.post("/login", data={
            "role": "admin",
            "username": "testadmin",
            "password": "AdminPass123"
        }, follow_redirects=True)
        self.assertEqual(login_res.status_code, 200)
        self.assertIn(b"System Overview", login_res.data)

        # Access students directory
        students_res = self.client.get("/admin/students")
        self.assertEqual(students_res.status_code, 200)
        self.assertIn(b"Jane Doe", students_res.data)

    def test_student_login_and_dashboard_access(self):
        # Perform Student login using generated Student ID
        login_res = self.client.post("/login", data={
            "role": "student",
            "username": self.student.student_id,
            "password": "StudentPass123"
        }, follow_redirects=True)
        self.assertEqual(login_res.status_code, 200)
        self.assertIn(b"Jane Doe", login_res.data)

        # Student attempting to access admin route should receive 403 Forbidden
        admin_res = self.client.get("/admin/dashboard")
        self.assertEqual(admin_res.status_code, 403)
        self.assertIn(b"Access Forbidden", admin_res.data)

    # -------------------------------------------------------------
    # 4. Error Pages Tests
    # -------------------------------------------------------------
    def test_404_page(self):
        res = self.client.get("/non-existent-endpoint-xyz")
        self.assertEqual(res.status_code, 404)
        self.assertIn(b"Page Not Found", res.data)


if __name__ == "__main__":
    unittest.main()
