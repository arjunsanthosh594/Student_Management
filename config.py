"""
config.py — Application Configuration
Supports development (local MySQL) and production (Amazon RDS).
All sensitive values are read from environment variables or a .env file.
"""
import os
from datetime import timedelta
from dotenv import load_dotenv

load_dotenv()


class Config:
    """Base configuration shared by all environments."""

    # ------------------------------------------------------------------ #
    # Flask Core
    # ------------------------------------------------------------------ #
    SECRET_KEY: str = os.environ.get("SECRET_KEY", "dev-secret-key-CHANGE-ME")
    WTF_CSRF_ENABLED: bool = True

    # ------------------------------------------------------------------ #
    # Session & Cookie Security
    # ------------------------------------------------------------------ #
    SESSION_COOKIE_SECURE: bool = os.environ.get("SESSION_COOKIE_SECURE", "False").lower() == "true"
    SESSION_COOKIE_HTTPONLY: bool = True
    SESSION_COOKIE_SAMESITE: str = "Lax"
    PERMANENT_SESSION_LIFETIME: timedelta = timedelta(
        seconds=int(os.environ.get("PERMANENT_SESSION_LIFETIME", 3600))
    )

    # ------------------------------------------------------------------ #
    # Database
    # ------------------------------------------------------------------ #
    DB_HOST: str = os.environ.get("DB_HOST", "localhost")
    DB_PORT: str = os.environ.get("DB_PORT", "3306")
    DB_NAME: str = os.environ.get("DB_NAME", "student_management_db")
    DB_USER: str = os.environ.get("DB_USER", "root")
    DB_PASSWORD: str = os.environ.get("DB_PASSWORD", "")

    SQLALCHEMY_DATABASE_URI: str = (
        f"mysql+pymysql://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}"
    )
    SQLALCHEMY_TRACK_MODIFICATIONS: bool = False
    SQLALCHEMY_ENGINE_OPTIONS: dict = {
        "pool_pre_ping": True,
        "pool_recycle": 300,
        "pool_timeout": 30,
    }

    # ------------------------------------------------------------------ #
    # File Uploads
    # ------------------------------------------------------------------ #
    MAX_CONTENT_LENGTH: int = int(os.environ.get("MAX_CONTENT_LENGTH", 5 * 1024 * 1024))  # 5 MB
    UPLOAD_FOLDER: str = os.environ.get("UPLOAD_FOLDER", "app/static/images/uploads")
    ALLOWED_EXTENSIONS: set = {"png", "jpg", "jpeg", "gif", "webp"}

    # ------------------------------------------------------------------ #
    # Amazon S3
    # ------------------------------------------------------------------ #
    # On EC2, leave these unset and rely on the instance IAM Role.
    AWS_ACCESS_KEY_ID: str = os.environ.get("AWS_ACCESS_KEY_ID", "")
    AWS_SECRET_ACCESS_KEY: str = os.environ.get("AWS_SECRET_ACCESS_KEY", "")
    AWS_REGION: str = os.environ.get("AWS_REGION", "us-east-1")
    S3_BUCKET_NAME: str = os.environ.get("S3_BUCKET_NAME", "")

    # ------------------------------------------------------------------ #
    # Pagination
    # ------------------------------------------------------------------ #
    STUDENTS_PER_PAGE: int = 10
    ATTENDANCE_PER_PAGE: int = 15


class DevelopmentConfig(Config):
    """Local development — uses local MySQL, debug mode on."""
    DEBUG: bool = True
    TESTING: bool = False


class ProductionConfig(Config):
    """Production — uses Amazon RDS, debug off, secure cookies."""
    DEBUG: bool = False
    TESTING: bool = False
    SESSION_COOKIE_SECURE: bool = True

    # Override DB settings with RDS values when present
    DB_HOST: str = os.environ.get("RDS_HOST", os.environ.get("DB_HOST", "localhost"))
    DB_PORT: str = os.environ.get("RDS_PORT", os.environ.get("DB_PORT", "3306"))
    DB_NAME: str = os.environ.get("RDS_NAME", os.environ.get("DB_NAME", "student_management_db"))
    DB_USER: str = os.environ.get("RDS_USER", os.environ.get("DB_USER", "admin"))
    DB_PASSWORD: str = os.environ.get("RDS_PASSWORD", os.environ.get("DB_PASSWORD", ""))

    SQLALCHEMY_DATABASE_URI: str = (
        f"mysql+pymysql://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}"
    )


class TestingConfig(Config):
    """Testing — uses an in-memory SQLite database."""
    DEBUG: bool = True
    TESTING: bool = True
    SQLALCHEMY_DATABASE_URI: str = "sqlite:///:memory:"
    WTF_CSRF_ENABLED: bool = False


# Map environment names to config classes
config_map: dict = {
    "development": DevelopmentConfig,
    "production": ProductionConfig,
    "testing": TestingConfig,
}
