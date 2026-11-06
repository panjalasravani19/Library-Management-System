"""
Database table creation script for the Library Management System.
Connects to MySQL and creates physical tables for all registered SQLAlchemy models.
"""

import sys
import os

# ---------------------------------------------------------------------------
# Compatibility import:
# Allows this script to be run either from the project root or from inside backend/
# ---------------------------------------------------------------------------
try:
    from database import Base, engine
    from models import Student, Book, BookIssue, BookRequest
except ImportError:
    from backend.database import Base, engine
    from backend.models import Student, Book, BookIssue, BookRequest


def create_all_tables():
    """
    Creates tables in the MySQL database defined in Base.metadata.
    Base.metadata.create_all() generates 'CREATE TABLE IF NOT EXISTS' queries,
    so it is completely safe and will not delete or alter existing tables.
    """
    print("Connecting to MySQL and creating database tables...")
    try:
        # Create physical tables in MySQL using the engine connection
        Base.metadata.create_all(bind=engine)
        print("\n[SUCCESS] Successfully created the following tables in MySQL:")
        for table_name in Base.metadata.tables.keys():
            print(f"  - {table_name}")
        print("\nAll database tables are ready for use!")
    except Exception as error:
        print(f"\n[ERROR] Failed to create tables: {error}")
        raise error


if __name__ == "__main__":
    create_all_tables()
