"""
app/models/department.py — Department model
"""
from app.extensions import db


class Department(db.Model):
    __tablename__ = "departments"

    id = db.Column(db.Integer, primary_key=True)
    dept_code = db.Column(db.String(20), unique=True, nullable=False, index=True)
    dept_name = db.Column(db.String(150), unique=True, nullable=False)
    description = db.Column(db.Text, nullable=True)
    created_at = db.Column(db.DateTime, server_default=db.func.now())

    # Relationships
    courses = db.relationship("Course", back_populates="department", lazy="dynamic")
    students = db.relationship("Student", back_populates="department", lazy="dynamic")

    @property
    def student_count(self) -> int:
        return self.students.count()

    @property
    def course_count(self) -> int:
        return self.courses.count()

    def __repr__(self) -> str:
        return f"<Department {self.dept_code}>"
