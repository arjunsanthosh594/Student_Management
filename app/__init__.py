"""
app/__init__.py — Application Factory
"""
import os
from flask import Flask
from config import config_map
from app.extensions import db, login_manager, csrf, migrate


def create_app(env: str = None) -> Flask:
    """Create and configure a Flask application instance."""
    if env is None:
        env = os.environ.get("FLASK_ENV", "development")

    cfg = config_map.get(env, config_map["development"])

    app = Flask(__name__, template_folder="templates", static_folder="static")
    app.config.from_object(cfg)

    # ------------------------------------------------------------------
    # Initialise extensions
    # ------------------------------------------------------------------
    db.init_app(app)
    csrf.init_app(app)
    migrate.init_app(app, db)

    login_manager.init_app(app)
    login_manager.login_view = "auth.login"
    login_manager.login_message = "Please log in to access this page."
    login_manager.login_message_category = "warning"

    # ------------------------------------------------------------------
    # Ensure local upload folder exists
    # ------------------------------------------------------------------
    upload_path = os.path.join(app.root_path, "static", "images", "uploads")
    os.makedirs(upload_path, exist_ok=True)

    # ------------------------------------------------------------------
    # Register blueprints
    # ------------------------------------------------------------------
    from app.routes.auth import auth_bp
    from app.routes.admin import admin_bp
    from app.routes.student import student_bp
    from app.routes.attendance import attendance_bp
    from app.routes.courses import courses_bp

    app.register_blueprint(auth_bp)
    app.register_blueprint(admin_bp, url_prefix="/admin")
    app.register_blueprint(student_bp, url_prefix="/student")
    app.register_blueprint(attendance_bp, url_prefix="/admin/attendance")
    app.register_blueprint(courses_bp, url_prefix="/admin")

    # ------------------------------------------------------------------
    # Register user loader
    # ------------------------------------------------------------------
    from app.models.admin import Admin
    from app.models.student_user import StudentUser

    @login_manager.user_loader
    def load_user(user_id: str):
        """Load admin or student by encoded user_id: 'a:<id>' or 's:<id>'."""
        if user_id.startswith("a:"):
            return Admin.query.get(int(user_id[2:]))
        elif user_id.startswith("s:"):
            return StudentUser.query.get(int(user_id[2:]))
        return None

    # ------------------------------------------------------------------
    # Error Handlers
    # ------------------------------------------------------------------
    from flask import render_template

    @app.errorhandler(403)
    def forbidden(e):
        return render_template("errors/403.html"), 403

    @app.errorhandler(404)
    def page_not_found(e):
        return render_template("errors/404.html"), 404

    @app.errorhandler(500)
    def internal_server_error(e):
        return render_template("errors/500.html"), 500

    return app
