
"""
Database configuration and session management.
Supports local MySQL and hosted Aiven MySQL.
"""

import os
from pathlib import Path
from urllib.parse import quote_plus

from dotenv import load_dotenv
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker, declarative_base

# Load backend/.env
BASE_DIR = Path(__file__).resolve().parent
load_dotenv(BASE_DIR / ".env")

# Database settings
DB_HOST = os.getenv("DB_HOST", "localhost")
DB_PORT = os.getenv("DB_PORT", "3306")
DB_USER = os.getenv("DB_USER", "root")
DB_PASSWORD = os.getenv("DB_PASSWORD", "")
DB_NAME = os.getenv("DB_NAME", "library_db")

# Optional SSL certificate for Aiven
DB_SSL_CA = os.getenv("DB_SSL_CA", "").strip()

# Build database URL
encoded_user = quote_plus(DB_USER)
encoded_password = quote_plus(DB_PASSWORD)

DATABASE_URL = (
    f"mysql+pymysql://{encoded_user}:{encoded_password}"
    f"@{DB_HOST}:{DB_PORT}/{DB_NAME}"
)

# Configure SSL only when a CA certificate is provided
connect_args = {}

if DB_SSL_CA:
    ca_path = Path(DB_SSL_CA)

    if not ca_path.is_absolute():
        ca_path = BASE_DIR / ca_path

    if not ca_path.is_file():
        raise FileNotFoundError(
            f"MySQL SSL CA certificate not found: {ca_path}"
        )

    connect_args["ssl"] = {"ca": str(ca_path)}

# Create SQLAlchemy engine
engine = create_engine(
    DATABASE_URL,
    pool_pre_ping=True,
    pool_recycle=300,
    connect_args=connect_args,
)

# Database sessions
SessionLocal = sessionmaker(
    autocommit=False,
    autoflush=False,
    bind=engine,
)

Base = declarative_base()


def get_db():
    """Provide a database session to FastAPI routes."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def test_connection():
    """Test the configured MySQL connection."""
    print("Testing MySQL database connection...")
    print(f"Host: {DB_HOST}")
    print(f"Port: {DB_PORT}")
    print(f"User: {DB_USER}")
    print(f"Database: {DB_NAME}")
    print(f"SSL enabled: {bool(DB_SSL_CA)}")

    if not DB_PASSWORD:
        print("[FAILED] DB_PASSWORD is empty.")
        return False

    try:
        with engine.connect() as connection:
            result = connection.execute(text("SELECT VERSION()"))
            print("[SUCCESS] Connected to MySQL!")
            print("MySQL version:", result.scalar())
            return True

    except Exception as error:
        print("[FAILED] Database connection error:")
        print(error)
        return False


if __name__ == "__main__":
    test_connection()
