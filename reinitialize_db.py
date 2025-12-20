"""
Manual database reinitialization script

Run this script to manually reinitialize your database.
Useful when you need to reset the database or after deleting volumes.

Usage:
    python reinitialize_db.py
"""

import os
import sys
from pathlib import Path

# Add app directory to path
BASE_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(BASE_DIR))

from app.infrastructure.database import engine, SessionLocal, Base
from app.infrastructure.database.startup import initialize_database
from sqlalchemy import text, inspect
from sqlalchemy.exc import OperationalError


def drop_all_tables():
    """Drop all existing tables"""
    print("[*] Dropping all existing tables...")
    
    # Get all table names
    inspector = inspect(engine)
    tables = inspector.get_table_names()
    
    if not tables:
        print("[OK] No tables to drop")
        return
    
    print(f"[*] Found {len(tables)} tables to drop: {', '.join(tables)}")
    
    # Drop all tables
    Base.metadata.drop_all(bind=engine)
    print("[OK] All tables dropped successfully")


def reinitialize():
    """Reinitialize the database"""
    print("=" * 60)
    print("DATABASE REINITIALIZATION")
    print("=" * 60)
    
    # Check database connection
    try:
        print("[*] Testing database connection...")
        conn = engine.connect()
        try:
            conn.execute(text("SELECT 1"))
            print("[OK] Database connection successful")
        finally:
            conn.close()
    except OperationalError as e:
        print(f"[ERROR] Database connection failed: {e}")
        print("[INFO] Make sure your DATABASE_URL environment variable is set correctly")
        return False
    
    # Ask user if they want to drop existing tables
    print("\n[*] Checking for existing tables...")
    inspector = inspect(engine)
    existing_tables = inspector.get_table_names()
    
    if existing_tables:
        print(f"[WARN] Found {len(existing_tables)} existing tables: {', '.join(existing_tables)}")
        response = input("\nDo you want to DROP all existing tables? (yes/no): ").strip().lower()
        if response in ['yes', 'y']:
            drop_all_tables()
        else:
            print("[INFO] Keeping existing tables, will only add missing data")
    else:
        print("[OK] No existing tables found (database is empty)")
    
    # Initialize database
    print("\n" + "=" * 60)
    try:
        initialize_database()
        print("\n" + "=" * 60)
        print("[SUCCESS] Database reinitialization completed!")
        print("=" * 60)
        return True
    except Exception as e:
        print(f"\n[ERROR] Failed to reinitialize database: {e}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    # Check if DATABASE_URL is set
    if not os.getenv("DATABASE_URL"):
        print("[ERROR] DATABASE_URL environment variable is not set")
        print("[INFO] Please set it before running this script:")
        print("       export DATABASE_URL='your_database_url'")
        sys.exit(1)
    
    success = reinitialize()
    sys.exit(0 if success else 1)



