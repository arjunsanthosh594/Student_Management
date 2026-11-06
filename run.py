"""
Student Management System
Flask Application Entry Point
"""

from app import create_app

app = create_app("production")

if __name__ == "__main__":
    app.run(
        host="127.0.0.1",
        port=5000,
        debug=False
    )
