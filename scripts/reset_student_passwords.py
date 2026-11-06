import sys
import os
import getpass

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app import create_app
from app.extensions import db
from app.models.student_user import StudentUser

app = create_app("production")

with app.app_context():
    password = getpass.getpass("Enter new student password (minimum 12 characters): ")
    confirm = getpass.getpass("Confirm new student password: ")

    if len(password) < 12:
        raise ValueError("Password must contain at least 12 characters.")

    if password != confirm:
        raise ValueError("Passwords do not match.")

    students = StudentUser.query.all()

    for student in students:
        student.set_password(password)
        student.is_active = True

    db.session.commit()

    print(f"Successfully reset passwords for {len(students)} student accounts.")
