"""
app/models/attendance.py — Attendance record model
"""
from datetime import date
from app.extensions import db


class Attendance(db.Model):
    __tablename__ = "attendance"

    id = db.Column(db.Integer, primary_key=True)
    student_id = db.Column(db.Integer, db.ForeignKey("students.id", ondelete="CASCADE"), nullable=False, index=True)
    attendance_date = db.Column(db.Date, nullable=False, index=True)
    status = db.Column(db.Enum("Present", "Absent"), nullable=False)
    created_at = db.Column(db.DateTime, server_default=db.func.now())
    updated_at = db.Column(db.DateTime, server_default=db.func.now(), onupdate=db.func.now())

    # Relationship
    student = db.relationship("Student", back_populates="attendance_records")

    # Unique constraint: one record per student per day
    __table_args__ = (
        db.UniqueConstraint("student_id", "attendance_date", name="uq_student_date"),
        db.Index("ix_att_date_student", "attendance_date", "student_id"),
    )

    def __repr__(self) -> str:
        return f"<Attendance student={self.student_id} date={self.attendance_date} status={self.status}>"
