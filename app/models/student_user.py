"""
app/models/student_user.py — Login credentials for a student
"""
from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash
from app.extensions import db


class StudentUser(UserMixin, db.Model):
    __tablename__ = "student_users"

    id = db.Column(db.Integer, primary_key=True)
    student_id = db.Column(db.Integer, db.ForeignKey("students.id", ondelete="CASCADE"), unique=True, nullable=False)
    username = db.Column(db.String(80), unique=True, nullable=False, index=True)
    password_hash = db.Column(db.String(256), nullable=False)
    is_active = db.Column(db.Boolean, default=True, nullable=False)
    created_at = db.Column(db.DateTime, server_default=db.func.now())

    # Relationship back to Student
    student = db.relationship("Student", back_populates="student_user")

    # ------------------------------------------------------------------
    # Flask-Login: encode role in the ID
    # ------------------------------------------------------------------
    def get_id(self) -> str:
        return f"s:{self.id}"

    @property
    def role(self) -> str:
        return "student"

    # ------------------------------------------------------------------
    # Password helpers
    # ------------------------------------------------------------------
    def set_password(self, password: str) -> None:
        self.password_hash = generate_password_hash(password)

    def check_password(self, password: str) -> bool:
        return check_password_hash(self.password_hash, password)

    def __repr__(self) -> str:
        return f"<StudentUser {self.username}>"
