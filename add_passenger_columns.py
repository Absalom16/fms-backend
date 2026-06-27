"""
Run once to add missing columns to the passengers table.
Usage (from the backend directory, with the venv active):
    python add_passenger_columns.py
"""
import sys, os
sys.path.insert(0, os.path.dirname(__file__))

# Bootstrap Flask so we reuse its exact DB connection
os.environ.setdefault('FLASK_ENV', 'development')

try:
    from app import create_app
    from app.extensions import db

    app = create_app()
    with app.app_context():
        stmts = [
            "ALTER TABLE passengers ADD COLUMN IF NOT EXISTS address TEXT",
            "ALTER TABLE passengers ADD COLUMN IF NOT EXISTS emergency_contact_name VARCHAR(100)",
            "ALTER TABLE passengers ADD COLUMN IF NOT EXISTS emergency_contact_phone VARCHAR(20)",
        ]
        with db.engine.connect() as conn:
            for sql in stmts:
                try:
                    conn.execute(db.text(sql))
                    print("OK :", sql)
                except Exception as e:
                    print("ERR:", e)
            conn.commit()
        print("Migration complete.")

except ImportError as e:
    print("Import error — make sure you run this from the backend directory with the venv active.")
    print(e)
    sys.exit(1)
