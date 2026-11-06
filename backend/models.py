"""
SQLAlchemy ORM models for the Library Management System.
Defines the database schema for Students, Books, and BookIssue records.
"""

import sys
import os
import datetime
from sqlalchemy import Column, Integer, String, Float, Boolean, Date, DateTime, ForeignKey, func
from sqlalchemy.orm import relationship

# ---------------------------------------------------------------------------
# Compatibility import for Base:
# Works whether run from the project root or directly inside backend/
# ---------------------------------------------------------------------------
try:
    from database import Base
except ImportError:
    from backend.database import Base


# ---------------------------------------------------------------------------
# 1. Student Model
# ---------------------------------------------------------------------------
class Student(Base):
    """
    Represents a student registered in the library.
    Each student can have multiple book issue records.
    """
    __tablename__ = "students"

    # Primary key: unique integer identifier for each student
    id = Column(Integer, primary_key=True, index=True, autoincrement=True)

    # Student personal information
    name = Column(String(100), nullable=False)
    email = Column(String(100), unique=True, index=True, nullable=False)
    roll_number = Column(String(50), unique=True, index=True, nullable=False)
    phone = Column(String(20), nullable=True)

    # Security: stores the hashed password (never store plain text passwords)
    password_hash = Column(String(255), nullable=False)

    # Timestamp of when the student registered
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    # Relationship: One student -> Many book issues
    # cascade="all, delete-orphan": if a student is removed, their issue records are also cleaned up
    issues = relationship("BookIssue", back_populates="student", cascade="all, delete-orphan")
    book_requests = relationship("BookRequest", back_populates="student", cascade="all, delete-orphan")

    def __repr__(self):
        return f"<Student(id={self.id}, name='{self.name}', roll_number='{self.roll_number}')>"


# ---------------------------------------------------------------------------
# 2. Book Model
# ---------------------------------------------------------------------------
class Book(Base):
    """
    Represents a book in the library catalog.
    Tracks total copies and copies currently available for issue.
    """
    __tablename__ = "books"

    # Primary key: unique integer identifier for each book
    id = Column(Integer, primary_key=True, index=True, autoincrement=True)

    # Book metadata
    title = Column(String(150), nullable=False, index=True)
    author = Column(String(100), nullable=False)
    isbn = Column(String(30), unique=True, nullable=True, index=True)
    category = Column(String(50), nullable=True)

    # Inventory tracking
    total_copies = Column(Integer, default=1, nullable=False)
    available_copies = Column(Integer, default=1, nullable=False)

    # Timestamp when the book was added to the library
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    # Relationship: One book -> Many issue records over its lifetime
    issues = relationship("BookIssue", back_populates="book")
    book_requests = relationship("BookRequest", back_populates="book")

    def __repr__(self):
        return f"<Book(id={self.id}, title='{self.title}', available={self.available_copies}/{self.total_copies})>"


# ---------------------------------------------------------------------------
# 3. BookIssue Model
# ---------------------------------------------------------------------------
class BookIssue(Base):
    """
    Represents a transaction record when a student borrows a book.
    Connects a Student to a Book via foreign keys.
    """
    __tablename__ = "book_issues"

    # Primary key: unique issue transaction ID
    id = Column(Integer, primary_key=True, index=True, autoincrement=True)

    # Foreign Keys referencing primary keys in students and books tables
    student_id = Column(Integer, ForeignKey("students.id", ondelete="CASCADE"), nullable=False)
    book_id = Column(Integer, ForeignKey("books.id", ondelete="RESTRICT"), nullable=False)

    # Issue dates
    issue_date = Column(Date, default=datetime.date.today, nullable=False)
    due_date = Column(Date, nullable=False)
    return_date = Column(Date, nullable=True)  # Set when the book is physically returned

    # Fine tracking and status
    fine = Column(Float, default=0.0, nullable=False)
    is_returned = Column(Boolean, default=False, nullable=False)

    # Bidirectional ORM relationships
    student = relationship("Student", back_populates="issues")
    book = relationship("Book", back_populates="issues")

    def __repr__(self):
        return (
            f"<BookIssue(id={self.id}, student_id={self.student_id}, "
            f"book_id={self.book_id}, returned={self.is_returned})>"
        )


# ---------------------------------------------------------------------------
# 4. BookRequest Model
# ---------------------------------------------------------------------------
class BookRequest(Base):
    """
    Represents a student request to borrow a book.
    Tracks review status ('Pending', 'Approved', 'Rejected'), review timestamp, and remarks.
    """
    __tablename__ = "book_requests"

    # Primary key: unique request ID
    id = Column(Integer, primary_key=True, index=True, autoincrement=True)

    # Foreign keys
    student_id = Column(Integer, ForeignKey("students.id", ondelete="CASCADE"), nullable=False)
    book_id = Column(Integer, ForeignKey("books.id", ondelete="CASCADE"), nullable=False)

    # Submission timestamp & status
    request_date = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    status = Column(String(20), default="Pending", nullable=False)  # 'Pending', 'Approved', 'Rejected'
    reviewed_at = Column(DateTime(timezone=True), nullable=True)
    remarks = Column(String(255), nullable=True)

    # Bidirectional ORM relationships
    student = relationship("Student", back_populates="book_requests")
    book = relationship("Book", back_populates="book_requests")

    def __repr__(self):
        return (
            f"<BookRequest(id={self.id}, student_id={self.student_id}, "
            f"book_id={self.book_id}, status='{self.status}')>"
        )


# ---------------------------------------------------------------------------
# Standalone Verification Helper
# ---------------------------------------------------------------------------
if __name__ == "__main__":
    print("--- SQLAlchemy Base Metadata Inspection ---")
    registered_tables = list(Base.metadata.tables.keys())
    print(f"Total tables registered: {len(registered_tables)}")
    for table_name in registered_tables:
        table = Base.metadata.tables[table_name]
        print(f"\nTable: '{table_name}'")
        for column in table.columns:
            fk_info = f" -> FK({list(column.foreign_keys)[0].target_fullname})" if column.foreign_keys else ""
            print(f"  - {column.name} ({column.type}){fk_info}")
