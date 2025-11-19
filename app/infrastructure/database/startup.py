"""Database startup and initialization logic"""
from sqlalchemy.orm import Session
from sqlalchemy import text
from sqlalchemy.exc import OperationalError
import time
from app.infrastructure.database import Base, engine, SessionLocal
from app.domain.entities.User import User
from app.domain.entities.Package import Package


def initialize_database():
    """Initialize database tables and default data"""
    print("[*] Starting database initialization...")
    
    # Ensure all models are imported
    from app.domain.entities.User import User
    from app.domain.entities.Order import Order
    from app.domain.entities.Package import Package
    from app.domain.entities.Tag import Tag
    from app.domain.entities.Delivery import Delivery
    from app.domain.entities.DeliveryFile import DeliveryFile
    from app.domain.entities.OrderEvent import OrderEvent
    from app.domain.entities.Message import Message
    from app.domain.entities.Notification import Notification
    
    # Test database connection first
    try:
        print("[*] Testing database connection...")
        # Use connect() with timeout handling
        conn = engine.connect()
        try:
            conn.execute(text("SELECT 1"))
            print("[OK] Database connection successful")
        finally:
            conn.close()
    except OperationalError as e:
        print(f"[ERROR] Database connection failed: {e}")
        print("[WARN] Application will continue but database operations may fail")
        print("[INFO] Make sure MySQL is running and accessible at localhost:3306")
        print("[INFO] Check database credentials in app/infrastructure/database/database.py")
        return
    except Exception as e:
        print(f"[ERROR] Unexpected error during connection test: {e}")
        import traceback
        traceback.print_exc()
        return
    
    db = SessionLocal()
    
    try:
        # Create tables
        print("[*] Creating database tables...")
        Base.metadata.create_all(bind=engine)
        print("[OK] Database tables created/verified")
        
        # Add dispute system columns if they don't exist
        try:
            result = db.execute(text("SHOW COLUMNS FROM orders LIKE 'request_type'"))
            if not result.fetchone():
                print("[*] Adding dispute system columns...")
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
        
        # Create default admin user
        print("[*] Checking admin user...")
        admin = db.query(User).filter(User.username == "Kohina").first()
        if not admin:
            admin = User(username="Kohina", email="anabelabocvarova@yahoo.com", is_admin=True)
            admin.set_password("Luna123!")
            db.add(admin)
            db.commit()
            print("[OK] Admin user created: Kohina / Luna123!")
        else:
            print("[OK] Admin user already exists")
        
        # Create default packages
        print("[*] Checking default packages...")
        if db.query(Package).count() == 0:
            default_packages = [
                {"name": "Basic", "price": 10.0, "delivery_days": 1, "tag_count": 2,
                 "description": "Simple tag, 1 revision"},
                {"name": "Standard", "price": 20.0, "delivery_days": 2, "tag_count": 4,
                 "description": "More features, 2 revisions"},
                {"name": "Premium", "price": 40.0, "delivery_days": 3, "tag_count": 6,
                 "description": "Full customization, unlimited revisions"},
            ]
            for pkg_data in default_packages:
                package = Package(**pkg_data)
                db.add(package)
            db.commit()
            print("[OK] Default packages created")
        else:
            print("[OK] Default packages already exist")
        
        print("[OK] Database initialization completed successfully!")
    except Exception as e:
        print(f"[ERROR] Error during database initialization: {e}")
        import traceback
        traceback.print_exc()
        db.rollback()
    finally:
        db.close()

