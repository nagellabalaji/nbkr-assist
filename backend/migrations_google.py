import sys
from run import app
from app import db
from sqlalchemy import inspect, text

def run_migration():
    """Safely checks if google_id and avatar_url exist on the users table before adding them."""
    with app.app_context():
        inspector = inspect(db.engine)
        columns = [c['name'] for c in inspector.get_columns('users')]
        print(f"Current users table columns: {columns}")
        
        with db.engine.connect() as conn:
            if 'google_id' not in columns:
                print("Adding google_id column to users table...")
                conn.execute(text("ALTER TABLE users ADD COLUMN google_id VARCHAR(100) NULL UNIQUE;"))
                conn.commit()
                print("google_id column added successfully.")
            else:
                print("google_id column already exists.")

            if 'avatar_url' not in columns:
                print("Adding avatar_url column to users table...")
                conn.execute(text("ALTER TABLE users ADD COLUMN avatar_url VARCHAR(255) NULL;"))
                conn.commit()
                print("avatar_url column added successfully.")
            else:
                print("avatar_url column already exists.")

        updated_cols = [c['name'] for c in inspect(db.engine).get_columns('users')]
        print(f"Verified users table columns: {updated_cols}")

if __name__ == '__main__':
    run_migration()
