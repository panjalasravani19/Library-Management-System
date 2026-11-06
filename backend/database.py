"""
Database configuration and session management for the Library Management System.
This file connects FastAPI to MySQL using SQLAlchemy and PyMySQL.
"""

import os
from urllib.parse import quote_plus
from dotenv import load_dotenv
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker, declarative_base

# ---------------------------------------------------------------------------
# 1. Load Environment Variables
# ---------------------------------------------------------------------------
# Locate the .env file in the backend directory
base_dir = os.path.dirname(os.path.abspath(__file__))
env_path = os.path.join(base_dir, ".env")

# Load variables from .env into os.environ
load_dotenv(dotenv_path=env_path)

# Retrieve database connection settings
DB_HOST = os.getenv("DB_HOST", "localhost")
DB_PORT = os.getenv("DB_PORT", "3306")
DB_USER = os.getenv("DB_USER", "root")
DB_PASSWORD = os.getenv("DB_PASSWORD", "")
DB_NAME = os.getenv("DB_NAME", "library_db")

# ---------------------------------------------------------------------------
# 2. Build Database URL
# ---------------------------------------------------------------------------
# Use quote_plus so passwords with special characters (e.g. @, #, $, %) don't break the connection URL
encoded_password = quote_plus(DB_PASSWORD) if DB_PASSWORD else ""

# Format: mysql+pymysql://<username>:<password>@<host>:<port>/<database_name>
DATABASE_URL = f"mysql+pymysql://{DB_USER}:{encoded_password}@{DB_HOST}:{DB_PORT}/{DB_NAME}"

# ---------------------------------------------------------------------------
# 3. Create SQLAlchemy Engine
# ---------------------------------------------------------------------------
# The engine is the central connection point to the MySQL database.
# pool_pre_ping=True checks connections before using them to prevent stale connections.
engine = create_engine(DATABASE_URL, pool_pre_ping=True)

# ---------------------------------------------------------------------------
# 4. Create SessionLocal Class
# ---------------------------------------------------------------------------
# Each instance of SessionLocal is an active database conversation/transaction.
# autocommit=False ensures transactions are explicitly committed when safe.
# autoflush=False prevents automatic premature flushes before commit.
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# ---------------------------------------------------------------------------
# 5. Base Class for ORM Models
# ---------------------------------------------------------------------------
# Models in models.py will inherit from this Base class to create tables.
Base = declarative_base()

# ---------------------------------------------------------------------------
# 6. Database Session Dependency for FastAPI
# ---------------------------------------------------------------------------
def get_db():
    """
    FastAPI dependency function.
    Opens a new database session for a single request, yields it to the route,
    and guarantees the session is closed when the request finishes.
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# ---------------------------------------------------------------------------
# 7. Database Connection Test Helper
# ---------------------------------------------------------------------------
def test_connection():
    """
    Helper function to verify if MySQL is running and accessible
    using the credentials defined in the .env file.
    """
    print("Testing connection to MySQL database...")
    print(f"- Host: {DB_HOST}")
    print(f"- Port: {DB_PORT}")
    print(f"- User: {DB_USER}")
    print(f"- Database: {DB_NAME}")

    if not DB_PASSWORD:
        print("\n[WARNING] DB_PASSWORD is empty in backend/.env!")
        print("Please open backend/.env and enter your MySQL root password.")
        return False

    try:
        with engine.connect() as connection:
            # Execute a lightweight ping query
            result = connection.execute(text("SELECT 1"))
            result.fetchone()
            print("\n[SUCCESS] Successfully connected to the MySQL database!")
            return True
    except Exception as error:
        print("\n[FAILED] Could not connect to MySQL database.")
        print(f"Error details: {error}")
        print("\nTroubleshooting tips:")
        print("1. Ensure MySQL Server is running (in Windows Services or MySQL Workbench).")
        print("2. Check that the password in backend/.env matches your MySQL password.")
        print("3. Check that the database exists: CREATE DATABASE library_db;")
        return False

if __name__ == "__main__":
    test_connection()
