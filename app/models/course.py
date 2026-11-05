"""
app/models/course.py — Course model
"""
from app.extensions import db


class Course(db.Model):
    __tablename__ = "courses"

    id = db.Column(db.Integer, primary_key=True)
    course_code = db.Column(db.String(20), unique=True, nullable=False, index=True)
    course_name = db.Column(db.String(200), nullable=False)
    department_id = db.Column(db.Integer, db.ForeignKey("departments.id", ondelete="RESTRICT"), nullable=False)
    duration = db.Column(db.String(50), nullable=True)   # e.g. "4 Years", "6 Months"
    description = db.Column(db.Text, nullable=True)
    created_at = db.Column(db.DateTime, server_default=db.func.now())

    # Relationships
    department = db.relationship("Department", back_populates="courses")
    students = db.relationship("Student", back_populates="course", lazy="dynamic")

    @property
    def student_count(self) -> int:
        return self.students.count()

    def __repr__(self) -> str:
        return f"<Course {self.course_code}>"
