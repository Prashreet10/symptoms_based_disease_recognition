"""
Database initialization script.
Run this before starting the application for the first time.
"""

import os
import sys

# Add src directory to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from database import db

if __name__ == '__main__':
    print("Initializing database...")
    print(f"Using configuration:")
    print(f"  MONGODB_URI: {os.environ.get('MONGODB_URI', 'mongodb://localhost:27017/disease_recognition')}")
    print(f"  MONGO_DB_NAME: {os.environ.get('MONGO_DB_NAME', os.environ.get('DB_NAME', '(from URI or default)'))}")
    print()
    
    db.init_db()
    print("\nDatabase initialization completed successfully!")
    print("\nMake sure you have:")
    print("1. A MongoDB server or Atlas cluster available")
    print("2. Set environment variables:")
    print("   - MONGODB_URI (default: mongodb://localhost:27017/disease_recognition)")
    print("   - MONGO_DB_NAME (optional if database name is already inside the URI)")
    print("   - SECRET_KEY (for Flask session)")
