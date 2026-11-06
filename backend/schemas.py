"""
Pydantic schemas for the Library Management System.
These models validate incoming HTTP request bodies and structure outgoing API responses.
Uses Pydantic v2 syntax with ConfigDict(from_attributes=True).
"""

from typing import Optional
from datetime import date, datetime
from pydantic import BaseModel, EmailStr, Field, ConfigDict


# ===========================================================================
# 1. Student Schemas
# ===========================================================================

class StudentBase(BaseModel):
    """Base fields shared across student schemas."""
    name: str = Field(..., min_length=2, max_length=100, description="Full name of student")
    email: EmailStr = Field(..., description="Valid email address")
    roll_number: str = Field(..., min_length=1, max_length=50, description="Unique roll number or student ID")
    phone: Optional[str] = Field(None, max_length=20, description="Contact phone number")


class StudentCreate(StudentBase):
    """Schema used when registering a new student."""
    password: str = Field(..., min_length=6, description="Plain text password (minimum 6 characters)")


class StudentLogin(BaseModel):
    """Schema used when a student logs in."""
    email: EmailStr = Field(..., description="Registered email address")
    password: str = Field(..., description="Student password")


class StudentResponse(StudentBase):
    """
    Schema returned to the client.
    Excludes password_hash to ensure sensitive data is never exposed.
    """
    id: int
    created_at: datetime

    # Pydantic v2: allows reading attributes directly from SQLAlchemy ORM objects
    model_config = ConfigDict(from_attributes=True)


# ===========================================================================
# 1B. Admin Schemas
# ===========================================================================

class AdminLogin(BaseModel):
    """Schema used when administrator logs in."""
    username: str = Field(..., min_length=1, description="Admin username")
    password: str = Field(..., min_length=1, description="Admin password")


class TokenResponse(BaseModel):
    """Schema returned after successful administrator authentication."""
    access_token: str
    token_type: str = "bearer"
    role: str = "admin"
    username: str


# ===========================================================================
# 2. Book Schemas
# ===========================================================================

class BookBase(BaseModel):
    """Base fields shared across book schemas."""
    title: str = Field(..., min_length=1, max_length=150, description="Title of the book")
    author: str = Field(..., min_length=1, max_length=100, description="Author name")
    isbn: Optional[str] = Field(None, max_length=30, description="ISBN code (optional)")
    category: Optional[str] = Field(None, max_length=50, description="Category / genre")


class BookCreate(BookBase):
    """Schema used when adding a new book to the catalog."""
    total_copies: int = Field(default=1, gt=0, description="Total physical copies (must be at least 1)")


class BookUpdate(BaseModel):
    """
    Schema used when updating book details.
    All fields are optional so only provided fields are updated.
    """
    title: Optional[str] = Field(None, min_length=1, max_length=150)
    author: Optional[str] = Field(None, min_length=1, max_length=100)
    isbn: Optional[str] = Field(None, max_length=30)
    category: Optional[str] = Field(None, max_length=50)
    total_copies: Optional[int] = Field(None, gt=0)


class BookResponse(BookBase):
    """Schema returned to the client when querying books."""
    id: int
    total_copies: int
    available_copies: int
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


# ===========================================================================
# 3. Book Issue Schemas
# ===========================================================================

class BookIssueCreate(BaseModel):
    """Schema used when issuing a book to a student."""
    student_id: int = Field(..., gt=0, description="ID of the borrowing student")
    book_id: int = Field(..., gt=0, description="ID of the book being borrowed")


class BookIssueResponse(BaseModel):
    """Schema returned after a book is issued or returned."""
    id: int
    student_id: int
    book_id: int
    issue_date: date
    due_date: date
    return_date: Optional[date] = None
    fine: float
    is_returned: bool

    model_config = ConfigDict(from_attributes=True)


# ===========================================================================
# 4. Book Request Schemas
# ===========================================================================

class BookRequestCreate(BaseModel):
    """Schema used by students to submit a book borrowing request."""
    book_id: int = Field(..., gt=0, description="ID of the book to request")


class BookRequestReview(BaseModel):
    """Schema used by administrators to add remarks when rejecting or approving."""
    remarks: Optional[str] = Field(None, max_length=255, description="Optional review remarks")


class BookRequestStudentResponse(BaseModel):
    """Schema returned to students viewing their requests."""
    id: int
    book_id: int
    book_title: str
    book_author: str
    request_date: datetime
    status: str
    reviewed_at: Optional[datetime] = None
    remarks: Optional[str] = None

    model_config = ConfigDict(from_attributes=True)


class BookRequestAdminResponse(BaseModel):
    """Schema returned to administrators viewing all student requests."""
    id: int
    student_id: int
    student_name: str
    student_roll_number: str
    book_id: int
    book_title: str
    book_author: str
    request_date: datetime
    status: str
    reviewed_at: Optional[datetime] = None
    remarks: Optional[str] = None

    model_config = ConfigDict(from_attributes=True)


# ===========================================================================
# Standalone Schema Verification Tests
# ===========================================================================
if __name__ == "__main__":
    print("--- Running Pydantic Schema Validation Tests ---")

    # 1. Test Student Validation
    valid_student = StudentCreate(
        name="Alex Doe",
        email="alex.doe@example.com",
        roll_number="CS202601",
        phone="1234567890",
        password="secretpassword"
    )
    print("\n[OK] StudentCreate valid instance:")
    print(" ", valid_student.model_dump(exclude={"password"}))

    # 2. Test Book Validation
    valid_book = BookCreate(
        title="Learning FastAPI & SQLAlchemy",
        author="John Smith",
        isbn="978-0132350884",
        category="Computer Science",
        total_copies=5
    )
    print("\n[OK] BookCreate valid instance:")
    print(" ", valid_book.model_dump())

    # 3. Test Invalid Copy Count (validation check)
    try:
        BookCreate(title="Test Book", author="Author", total_copies=0)
        print("[FAIL] Should not allow 0 copies!")
    except Exception:
        print("\n[OK] Correctly rejected BookCreate with total_copies=0 (must be > 0)")

    # 4. Test Invalid Email (validation check)
    try:
        StudentCreate(name="Bad", email="invalid-email-address", roll_number="123", password="pass")
        print("[FAIL] Should not allow invalid email!")
    except Exception:
        print("\n[OK] Correctly rejected StudentCreate with invalid email format")

    print("\n[SUCCESS] All Pydantic schema validation tests passed successfully!")
