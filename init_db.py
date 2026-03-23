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
    print(f"  DB_HOST: {os.environ.get('DB_HOST', 'localhost')}")
    print(f"  DB_USER: {os.environ.get('DB_USER', 'root')}")
    print(f"  DB_NAME: {os.environ.get('DB_NAME', 'disease_recognition')}")
    print()
    
    db.init_db()
    print("\nDatabase initialization completed successfully!")
    print("\nMake sure you have:")
    print("1. MySQL server running on localhost")
    print("2. Set environment variables:")
    print("   - DB_HOST (default: localhost)")
    print("   - DB_USER (default: root)")
    print("   - DB_PASSWORD (default: empty string)")
    print("   - DB_NAME (default: symptom_predictor)")
    print("   - SECRET_KEY (for Flask session)")
