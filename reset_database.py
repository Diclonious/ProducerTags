#!/usr/bin/env python3
"""
Script to reset the database while keeping users
"""
import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app.db.database import SessionLocal, engine, Base
from app.domain.User import User
from app.domain.Order import Order
from app.domain.Package import Package
from app.domain.Tag import Tag
from app.domain.Delivery import Delivery
from app.domain.OrderEvent import OrderEvent
from sqlalchemy import text

def reset_database():
    """Reset database but keep users"""
    db = SessionLocal()
    
    try:
        print("[*] Starting database reset...")
        
        # Step 1: Backup all users data
        print("[*] Backing up users data...")
        users_backup = []
        users = db.query(User).all()
        for user in users:
            users_backup.append({
                'id': user.id,
                'username': user.username,
                'email': user.email,
                'hashed_password': user.hashed_password,
                'is_admin': user.is_admin,
                'avatar': user.avatar
            })
        print(f"[OK] Backed up {len(users_backup)} users")
        
        # Step 2: Drop all tables (except users will be recreated)
        print("[*] Dropping all tables...")
        from sqlalchemy import inspect
        inspector = inspect(engine)
        tables = inspector.get_table_names()
        
        # Drop tables in reverse dependency order
        tables_to_drop = ['order_events', 'deliveries', 'tags', 'orders', 'packages', 'users']
        for table_name in tables_to_drop:
            if table_name in tables:
                try:
                    db.execute(text(f"DROP TABLE IF EXISTS `{table_name}`"))
                    print(f"  [OK] Dropped table: {table_name}")
                except Exception as e:
                    print(f"  [WARN] Could not drop {table_name}: {e}")
        
        db.commit()
        print("[OK] All tables dropped")
        
        # Step 3: Recreate all tables
        print("[*] Recreating all tables...")
        Base.metadata.create_all(bind=engine)
        print("[OK] All tables recreated")
        
        # Step 4: Restore users
        print("[*] Restoring users...")
        for user_data in users_backup:
            # Create new user instance with backed up data
            user = User(
                username=user_data['username'],
                email=user_data['email'],
                hashed_password=user_data['hashed_password'],
                is_admin=user_data['is_admin'],
                avatar=user_data['avatar']
            )
            db.add(user)
        
        db.commit()
        print(f"[OK] Restored {len(users_backup)} users")
        
        # Step 5: Recreate admin user if it doesn't exist (from startup)
        admin = db.query(User).filter(User.username == "Kohina").first()
        if not admin:
            admin = User(username="Kohina", email="anabelabocvarova@yahoo.com", is_admin=True)
            admin.set_password("Luna123!")
            db.add(admin)
            db.commit()
            print("[OK] Admin user 'Kohina' created")
        
        # Step 6: Recreate default packages
        print("[*] Creating default packages...")
        if db.query(Package).count() == 0:
            default_packages = [
                {"name": "Basic", "price": 10.0, "delivery_days": 1, "tag_count": 2,
                 "description": "Simple tag, 1 revision"},
                {"name": "Standard", "price": 20.0, "delivery_days": 2, "tag_count": 4,
                 "description": "More features, 2 revisions"},
                {"name": "Premium", "price": 40.0, "delivery_days": 3, "tag_count": 6,
                 "description": "Full customization, unlimited revisions"},
            ]
            for pkg in default_packages:
                db.add(Package(**pkg))
            db.commit()
            print("[OK] Default packages created")
        
        # Step 7: Add dispute system columns if needed
        print("[*] Checking for dispute system columns...")
        try:
            result = db.execute(text("SHOW COLUMNS FROM orders LIKE 'request_type'"))
            if not result.fetchone():
                print("Adding dispute system columns to orders table...")
                db.execute(text("""
                    ALTER TABLE orders 
                    ADD COLUMN request_type VARCHAR(50) NULL,
                    ADD COLUMN request_message TEXT NULL,
                    ADD COLUMN cancellation_reason VARCHAR(100) NULL,
                    ADD COLUMN cancellation_message TEXT NULL,
                    ADD COLUMN extension_days INT NULL,
                    ADD COLUMN extension_reason TEXT NULL,
                    ADD COLUMN requested_by_admin VARCHAR(10) NULL
                """))
                db.commit()
                print("[OK] Dispute system columns added")
            else:
                print("[OK] Dispute system columns already exist")
        except Exception as e:
            print(f"[WARN] Migration warning: {e}")
            db.rollback()
        
        print("\n[OK] Database reset completed successfully!")
        print(f"   - Users preserved: {len(users_backup)}")
        print("   - All other data cleared")
        
    except Exception as e:
        print(f"\n[ERROR] Error during database reset: {e}")
        import traceback
        traceback.print_exc()
        db.rollback()
    finally:
        db.close()


if __name__ == "__main__":
    print("=" * 50)
    print("DATABASE RESET SCRIPT")
    print("=" * 50)
    print("This will:")
    print("  1. Backup all users")
    print("  2. Drop all tables")
    print("  3. Recreate all tables")
    print("  4. Restore users")
    print("  5. Recreate default packages")
    print("=" * 50)
    
    # Check if --yes flag is provided
    if len(sys.argv) > 1 and sys.argv[1] == '--yes':
        reset_database()
    else:
        try:
            response = input("\nAre you sure you want to proceed? (yes/no): ")
            if response.lower() in ['yes', 'y']:
                reset_database()
            else:
                print("[CANCELLED] Database reset cancelled")
        except EOFError:
            # If running non-interactively, proceed automatically
            print("\n[WARN] Running non-interactively, proceeding with reset...")
            reset_database()

