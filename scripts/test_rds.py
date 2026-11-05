"""
scripts/test_rds.py — Amazon RDS / MySQL Connectivity & Latency Test Utility
Run with: python scripts/test_rds.py
"""
import sys
import os
import time

sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from app import create_app
from app.extensions import db
from sqlalchemy import text

app = create_app()

with app.app_context():
    print("=" * 60)
    print(" Database & Amazon RDS Connectivity Verification")
    print("=" * 60)

    engine = db.engine
    db_uri = app.config.get("SQLALCHEMY_DATABASE_URI", "")
    
    # Redact password in display
    safe_uri = db_uri
    if "@" in safe_uri and ":" in safe_uri.split("@")[0]:
        prefix, rest = safe_uri.split("@", 1)
        scheme_user = prefix.rsplit(":", 1)[0]
        safe_uri = f"{scheme_user}:******@{rest}"

    print(f"Target Database URI: {safe_uri}")
    print(f"Flask Environment  : {app.config.get('ENV', 'development')}")
    print(f"Connection Pool    : pre_ping=True, recycle=300s, timeout=30s")

    print("\nPinging database server...")
    start_time = time.time()
    try:
        with engine.connect() as conn:
            result = conn.execute(text("SELECT VERSION() AS version, DATABASE() AS current_db;"))
            row = result.fetchone()
            latency = (time.time() - start_time) * 1000

            print(f"[SUCCESS] Handshake successful! Latency: {latency:.2f} ms")
            print(f"[INFO]    Database Version : {row.version}")
            print(f"[INFO]    Connected DB     : {row.current_db}")

            # Inspect existing tables
            tables_result = conn.execute(text("SHOW TABLES;"))
            tables = [r[0] for r in tables_result.fetchall()]
            print(f"[INFO]    Tables Found ({len(tables)}): {', '.join(tables) if tables else 'None'}")

        print("\n[OK] Database / Amazon RDS connection is healthy and ready for traffic.")
    except Exception as e:
        print(f"\n[ERROR] Database connection failed:")
        print(f"        {e}")
        print("\nTroubleshooting Checklist:")
        print("1. Verify MySQL service or Amazon RDS instance is in 'Available' state.")
        print("2. Ensure RDS Security Group allows inbound traffic on port 3306 from your IP/EC2.")
        print("3. Check credentials (DB_USER, DB_PASSWORD, DB_NAME, DB_HOST) in your .env.")
    print("=" * 60)
