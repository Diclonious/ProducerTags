#!/usr/bin/env python3
"""
Database migration script to add dispute system fields to the orders table.
Run this script to update your database schema.
"""

import mysql.connector
from app.core.config import DATABASE_URL
import os

def run_migration():
    """Add new columns to the orders table for the dispute system."""
    
    # Parse database URL to get connection details
    # Assuming DATABASE_URL format: mysql://user:password@host:port/database
    if DATABASE_URL.startswith('mysql://'):
        db_url = DATABASE_URL[8:]  # Remove 'mysql://'
        if '@' in db_url:
            user_pass, host_db = db_url.split('@')
            if ':' in user_pass:
                user, password = user_pass.split(':')
            else:
                user = user_pass
                password = ''
            
            if ':' in host_db:
                host, port_db = host_db.split(':')
                if '/' in port_db:
                    port, database = port_db.split('/')
                else:
                    port = port_db
                    database = ''
            else:
                host = host_db.split('/')[0]
                port = 3306
                database = host_db.split('/')[1] if '/' in host_db else ''
    else:
        print("Error: Unsupported database URL format")
        return False
    
    try:
        # Connect to MySQL database
        connection = mysql.connector.connect(
            host=host,
            port=int(port),
            user=user,
            password=password,
            database=database
        )
        
        cursor = connection.cursor()
        
        # Check if columns already exist
        cursor.execute("SHOW COLUMNS FROM orders LIKE 'request_type'")
        if cursor.fetchone():
            print("Migration already applied - columns exist")
            return True
        
        # Add new columns
        migration_sql = """
        ALTER TABLE orders 
        ADD COLUMN request_type VARCHAR(50) NULL,
        ADD COLUMN request_message TEXT NULL,
        ADD COLUMN cancellation_reason VARCHAR(100) NULL,
        ADD COLUMN cancellation_message TEXT NULL,
        ADD COLUMN extension_days INT NULL,
        ADD COLUMN extension_reason TEXT NULL,
        ADD COLUMN requested_by_admin VARCHAR(10) NULL;
        """
        
        cursor.execute(migration_sql)
        connection.commit()
        
        print("✅ Migration completed successfully!")
        print("Added the following columns to orders table:")
        print("- request_type")
        print("- request_message") 
        print("- cancellation_reason")
        print("- cancellation_message")
        print("- extension_days")
        print("- extension_reason")
        print("- requested_by_admin")
        
        return True
        
    except mysql.connector.Error as err:
        print(f"❌ Database error: {err}")
        return False
    except Exception as e:
        print(f"❌ Error: {e}")
        return False
    finally:
        if 'connection' in locals() and connection.is_connected():
            cursor.close()
            connection.close()

if __name__ == "__main__":
    print("Running database migration for dispute system...")
    success = run_migration()
    if success:
        print("\n🎉 Migration completed! You can now restart your application.")
    else:
        print("\n💥 Migration failed! Please check the error messages above.")
