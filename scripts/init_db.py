"""
scripts/init_db.py — Create all database tables
Run once: python scripts/init_db.py
"""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from app import create_app
from app.extensions import db
# Import all models so SQLAlchemy knows about them
from app.models import Admin, Department, Course, Student, StudentUser, Attendance  # noqa

app = create_app()

with app.app_context():
    db.create_all()
    print("[OK] All tables created successfully.")
