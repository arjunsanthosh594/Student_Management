"""
app/models/student.py — Student (academic record) model
"""
import uuid
from datetime import date
from app.extensions import db


def _generate_student_id() -> str:
    """Auto-generate a unique student ID: SMS-YYYYNNNNN."""
    year = date.today().year
    uid = str(uuid.uuid4().int)[:5]
    return f"SMS-{year}{uid}"


class Student(db.Model):
    __tablename__ = "students"

    id = db.Column(db.Integer, primary_key=True)
    student_id = db.Column(db.String(30), unique=True, nullable=False, index=True, default=_generate_student_id)
    full_name = db.Column(db.String(200), nullable=False)
    email = db.Column(db.String(150), unique=True, nullable=False, index=True)
    phone = db.Column(db.String(20), nullable=True)
    gender = db.Column(db.Enum("Male", "Female", "Other"), nullable=False)
    date_of_birth = db.Column(db.Date, nullable=True)
    address = db.Column(db.Text, nullable=True)

    department_id = db.Column(db.Integer, db.ForeignKey("departments.id", ondelete="RESTRICT"), nullable=False)
    course_id = db.Column(db.Integer, db.ForeignKey("courses.id", ondelete="RESTRICT"), nullable=False)
    admission_date = db.Column(db.Date, nullable=False, default=date.today)

    # Profile image: local path or S3 object key
    profile_picture = db.Column(db.String(500), nullable=True)
    # Flag to know where the image lives
    picture_source = db.Column(db.Enum("local", "s3"), nullable=True, default="local")

    created_at = db.Column(db.DateTime, server_default=db.func.now())
    updated_at = db.Column(db.DateTime, server_default=db.func.now(), onupdate=db.func.now())

    # Relationships
    department = db.relationship("Department", back_populates="students")
    course = db.relationship("Course", back_populates="students")
    student_user = db.relationship("StudentUser", back_populates="student", uselist=False, cascade="all, delete-orphan")
    attendance_records = db.relationship("Attendance", back_populates="student", cascade="all, delete-orphan", lazy="dynamic")

    # ------------------------------------------------------------------
    # Computed properties
    # ------------------------------------------------------------------
    @property
    def total_attendance(self) -> int:
        return self.attendance_records.count()

    @property
    def present_days(self) -> int:
        return self.attendance_records.filter_by(status="Present").count()

    @property
    def absent_days(self) -> int:
        return self.attendance_records.filter_by(status="Absent").count()

    @property
    def attendance_percentage(self) -> float:
        total = self.total_attendance
        if total == 0:
            return 0.0
        return round((self.present_days / total) * 100, 2)

    def __repr__(self) -> str:
        return f"<Student {self.student_id} - {self.full_name}>"
