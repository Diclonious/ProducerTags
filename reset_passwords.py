#!/usr/bin/env python3
"""
Script to reset password for Kohina234
"""
import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app.db.database import SessionLocal
from app.domain.User import User
from app.domain.Order import Order
from app.domain.Package import Package
from app.domain.Tag import Tag
from app.domain.OrderEvent import OrderEvent

db = SessionLocal()

try:
    # Find the user
    user = db.query(User).filter(User.username == "Kohina234").first()
    if user:
        # Reset password to a known value
        user.set_password("password123")
        db.commit()
        print("✅ Password reset successfully for Kohina234")
        print("New password: password123")
    else:
        print("❌ User Kohina234 not found")
        
    # Also reset Kohina2
    user2 = db.query(User).filter(User.username == "Kohina2").first()
    if user2:
        user2.set_password("password123")
        db.commit()
        print("✅ Password reset successfully for Kohina2")
        print("New password: password123")
    else:
        print("❌ User Kohina2 not found")
        
except Exception as e:
    print(f"❌ Error: {e}")
    db.rollback()
finally:
    db.close()


