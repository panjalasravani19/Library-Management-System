"""
Main FastAPI Application for Library Management System.
Provides RESTful API endpoints for Students, Books, and Book Issue/Return operations.
Features Role-Based Access Control (RBAC) with signed JWT tokens for Admin privileges.
"""

import os
from typing import List, Optional
from datetime import date, datetime, timedelta, timezone
from contextlib import asynccontextmanager
from fastapi import FastAPI, Depends, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.orm import Session
from sqlalchemy import or_
import bcrypt
import jwt
from dotenv import load_dotenv

# ---------------------------------------------------------------------------
# Compatibility Imports
# ---------------------------------------------------------------------------
try:
    from database import get_db, engine, Base
    import models
    import schemas
except ImportError:
    from backend.database import get_db, engine, Base
    from backend import models, schemas


# ---------------------------------------------------------------------------
# Load Admin and JWT Configuration from .env
# ---------------------------------------------------------------------------
base_dir = os.path.dirname(os.path.abspath(__file__))
env_path = os.path.join(base_dir, ".env")
load_dotenv(dotenv_path=env_path)

ADMIN_USERNAME = os.getenv("ADMIN_USERNAME", "admin")
ADMIN_PASSWORD = os.getenv("ADMIN_PASSWORD", "")
JWT_SECRET_KEY = os.getenv("JWT_SECRET_KEY", "your-secret-key-for-jwt-tokens-change-in-env")
JWT_ALGORITHM = os.getenv("JWT_ALGORITHM", "HS256")
ACCESS_TOKEN_EXPIRE_HOURS = int(os.getenv("ACCESS_TOKEN_EXPIRE_HOURS", "12"))

# HTTP Bearer security scheme for token authentication
security = HTTPBearer(auto_error=False)


# ---------------------------------------------------------------------------
# Security Helpers (Bcrypt & JWT)
# ---------------------------------------------------------------------------
def hash_password(password: str) -> str:
    """Hash a plain text password using bcrypt."""
    pwd_bytes = password.encode("utf-8")[:72]
    salt = bcrypt.gensalt()
    return bcrypt.hashpw(pwd_bytes, salt).decode("utf-8")


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify whether a plain text password matches a bcrypt hash."""
    try:
        pwd_bytes = plain_password.encode("utf-8")[:72]
        hash_bytes = hashed_password.encode("utf-8")
        return bcrypt.checkpw(pwd_bytes, hash_bytes)
    except Exception:
        return False


def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    """Generate a cryptographically signed JWT token."""
    to_encode = data.copy()
    expire = datetime.now(timezone.utc) + (expires_delta or timedelta(hours=ACCESS_TOKEN_EXPIRE_HOURS))
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, JWT_SECRET_KEY, algorithm=JWT_ALGORITHM)


def get_current_admin(credentials: Optional[HTTPAuthorizationCredentials] = Depends(security)):
    """
    FastAPI dependency that enforces administrator authorization.
    Decodes the JWT Bearer token and verifies the 'admin' role.
    """
    if not credentials:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication required. Please provide an Admin Bearer token.",
            headers={"WWW-Authenticate": "Bearer"},
        )

    token = credentials.credentials
    try:
        payload = jwt.decode(token, JWT_SECRET_KEY, algorithms=[JWT_ALGORITHM])
        role = payload.get("role")
        username = payload.get("sub")
        if role != "admin" or username != ADMIN_USERNAME:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Access denied: Administrator privileges required.",
            )
        return {"username": username, "role": role}
    except jwt.ExpiredSignatureError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Session expired: Token has expired. Please log in again.",
            headers={"WWW-Authenticate": "Bearer"},
        )
    except jwt.PyJWTError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authentication token.",
            headers={"WWW-Authenticate": "Bearer"},
        )


def require_admin_role(current_admin):
    """Guard helper ensuring current_admin is present and has the admin role."""
    if isinstance(current_admin, HTTPAuthorizationCredentials):
        current_admin = get_current_admin(current_admin)
    if not current_admin or not isinstance(current_admin, dict) or current_admin.get("role") != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied: Administrator privileges required.",
        )


def get_current_student(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(security),
    db: Session = Depends(get_db),
) -> models.Student:
    """
    FastAPI dependency that enforces student authorization.
    Decodes the JWT Bearer token and verifies the 'student' role.
    Obtains the authenticated student directly from the database using token 'sub'.
    """
    if not credentials:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication required. Please provide a Student Bearer token.",
            headers={"WWW-Authenticate": "Bearer"},
        )

    token = credentials.credentials
    try:
        payload = jwt.decode(token, JWT_SECRET_KEY, algorithms=[JWT_ALGORITHM])
        role = payload.get("role")
        student_id = payload.get("sub")
        if role != "student" or not student_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Access denied: Student account required.",
            )
        student = db.query(models.Student).filter(models.Student.id == int(student_id)).first()
        if not student:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Student account not found.",
            )
        return student
    except jwt.ExpiredSignatureError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Session expired: Student token has expired. Please log in again.",
            headers={"WWW-Authenticate": "Bearer"},
        )
    except (jwt.PyJWTError, ValueError):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid student authentication token.",
            headers={"WWW-Authenticate": "Bearer"},
        )


# ---------------------------------------------------------------------------
# Lifespan Event: Ensures Tables Exist on Startup
# ---------------------------------------------------------------------------
@asynccontextmanager
async def lifespan(app: FastAPI):
    # Ensure MySQL tables are created
    Base.metadata.create_all(bind=engine)
    yield


# ---------------------------------------------------------------------------
# FastAPI App Initialization & CORS Configuration
# ---------------------------------------------------------------------------
app = FastAPI(
    title="Library Management System API",
    description="Backend API for managing students, books, and book checkout/return records.",
    version="1.0.0",
    lifespan=lifespan,
)

# Enable CORS so React frontend can communicate with backend
import os

allowed_origins = [
    origin.strip()
    for origin in os.getenv(
        "FRONTEND_URL",
        "http://127.0.0.1:5173,http://localhost:5173"
    ).split(",")
    if origin.strip()
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=allowed_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ===========================================================================
# 1. General Endpoints
# ===========================================================================

@app.get("/", tags=["General"])
def read_root():
    """Welcome endpoint confirming the API is reachable."""
    return {
        "message": "Welcome to the Library Management System API",
        "docs_url": "/docs",
        "health_check": "/health",
    }


@app.get("/health", tags=["General"])
def health_check(db: Session = Depends(get_db)):
    """Health check endpoint to verify backend and database connection."""
    return {
        "status": "healthy",
        "database": "connected",
    }


# ===========================================================================
# 2. Admin Authentication Endpoint
# ===========================================================================

@app.post("/admin/login", response_model=schemas.TokenResponse, tags=["Admin"])
def admin_login(login_data: schemas.AdminLogin):
    """
    Authenticate administrator credentials and return a signed JWT access token.
    Credentials are read securely from backend environment variables.
    """
    if (
        login_data.username != ADMIN_USERNAME
        or login_data.password != ADMIN_PASSWORD
    ):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid admin username or password.",
        )

    token = create_access_token({"sub": ADMIN_USERNAME, "role": "admin"})
    return schemas.TokenResponse(
        access_token=token,
        token_type="bearer",
        role="admin",
        username=ADMIN_USERNAME,
    )


# ===========================================================================
# 3. Student Endpoints
# ===========================================================================

@app.post(
    "/students/register",
    response_model=schemas.StudentResponse,
    status_code=status.HTTP_201_CREATED,
    tags=["Students"],
)
def register_student(student_data: schemas.StudentCreate, db: Session = Depends(get_db)):
    """
    Register a new student.
    - Validates email and roll number uniqueness.
    - Securely hashes the password with bcrypt before saving.
    - Never returns the password hash in the response.
    """
    existing_email = db.query(models.Student).filter(models.Student.email == student_data.email).first()
    if existing_email:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="A student with this email address already exists.",
        )

    existing_roll = db.query(models.Student).filter(models.Student.roll_number == student_data.roll_number).first()
    if existing_roll:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="A student with this roll number already exists.",
        )

    hashed_pwd = hash_password(student_data.password)

    new_student = models.Student(
        name=student_data.name,
        email=student_data.email,
        roll_number=student_data.roll_number,
        phone=student_data.phone,
        password_hash=hashed_pwd,
    )
    db.add(new_student)
    db.commit()
    db.refresh(new_student)
    return new_student


@app.post("/students/login", tags=["Students"])
def login_student(login_data: schemas.StudentLogin, db: Session = Depends(get_db)):
    """
    Verify student credentials (email and password).
    Returns student profile information upon successful verification.
    """
    student = db.query(models.Student).filter(models.Student.email == login_data.email).first()
    if not student or not verify_password(login_data.password, student.password_hash):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password.",
        )

    student_response = schemas.StudentResponse.model_validate(student)
    token = create_access_token({"sub": str(student.id), "email": student.email, "role": "student"})
    return {
        "message": "Login successful",
        "access_token": token,
        "token_type": "bearer",
        "student": student_response,
        "role": "student",
    }


@app.get("/students", response_model=List[schemas.StudentResponse], tags=["Students"])
def list_students(
    db: Session = Depends(get_db),
    current_admin: dict = Depends(get_current_admin),
):
    """Retrieve all students (Protected: Admin only)."""
    require_admin_role(current_admin)
    return db.query(models.Student).all()


@app.get("/students/{student_id}", response_model=schemas.StudentResponse, tags=["Students"])
def get_student(student_id: int, db: Session = Depends(get_db)):
    """Retrieve details of a single student by their unique ID."""
    student = db.query(models.Student).filter(models.Student.id == student_id).first()
    if not student:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Student with ID {student_id} not found.",
        )
    return student


# ===========================================================================
# 4. Book Endpoints (CRUD)
# ===========================================================================

@app.post(
    "/books",
    response_model=schemas.BookResponse,
    status_code=status.HTTP_201_CREATED,
    tags=["Books"],
)
def create_book(
    book_data: schemas.BookCreate,
    db: Session = Depends(get_db),
    current_admin: dict = Depends(get_current_admin),
):
    """
    Add a new book to the library catalog (Protected: Admin only).
    Sets available_copies equal to total_copies initially.
    """
    require_admin_role(current_admin)
    if book_data.isbn:
        existing_isbn = db.query(models.Book).filter(models.Book.isbn == book_data.isbn).first()
        if existing_isbn:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="A book with this ISBN already exists.",
            )

    new_book = models.Book(
        title=book_data.title,
        author=book_data.author,
        isbn=book_data.isbn,
        category=book_data.category,
        total_copies=book_data.total_copies,
        available_copies=book_data.total_copies,
    )
    db.add(new_book)
    db.commit()
    db.refresh(new_book)
    return new_book


@app.get("/books", response_model=List[schemas.BookResponse], tags=["Books"])
def list_books(db: Session = Depends(get_db)):
    """Retrieve all books currently in the catalog (Public to all users)."""
    return db.query(models.Book).all()


@app.get("/books/{book_id}", response_model=schemas.BookResponse, tags=["Books"])
def get_book(book_id: int, db: Session = Depends(get_db)):
    """Retrieve details of a specific book by ID."""
    book = db.query(models.Book).filter(models.Book.id == book_id).first()
    if not book:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Book with ID {book_id} not found.",
        )
    return book


@app.put("/books/{book_id}", response_model=schemas.BookResponse, tags=["Books"])
def update_book(
    book_id: int,
    update_data: schemas.BookUpdate,
    db: Session = Depends(get_db),
    current_admin: dict = Depends(get_current_admin),
):
    """Update book details (Protected: Admin only)."""
    require_admin_role(current_admin)
    book = db.query(models.Book).filter(models.Book.id == book_id).first()
    if not book:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Book with ID {book_id} not found.",
        )

    if update_data.isbn and update_data.isbn != book.isbn:
        existing_isbn = db.query(models.Book).filter(models.Book.isbn == update_data.isbn).first()
        if existing_isbn:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="A book with this ISBN already exists.",
            )

    if update_data.total_copies is not None:
        currently_borrowed = book.total_copies - book.available_copies
        if update_data.total_copies < currently_borrowed:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=(
                    f"Cannot reduce total copies to {update_data.total_copies}. "
                    f"There are currently {currently_borrowed} copies issued to students."
                ),
            )
        difference = update_data.total_copies - book.total_copies
        book.total_copies = update_data.total_copies
        book.available_copies += difference

    if update_data.title is not None:
        book.title = update_data.title
    if update_data.author is not None:
        book.author = update_data.author
    if update_data.isbn is not None:
        book.isbn = update_data.isbn
    if update_data.category is not None:
        book.category = update_data.category

    db.commit()
    db.refresh(book)
    return book


@app.delete("/books/{book_id}", tags=["Books"])
def delete_book(
    book_id: int,
    db: Session = Depends(get_db),
    current_admin: dict = Depends(get_current_admin),
):
    """
    Delete a book from the catalog (Protected: Admin only).
    Prevents deletion if the book is currently issued or has borrowing history.
    """
    require_admin_role(current_admin)
    book = db.query(models.Book).filter(models.Book.id == book_id).first()
    if not book:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Book with ID {book_id} not found.",
        )

    active_issues = (
        db.query(models.BookIssue)
        .filter(models.BookIssue.book_id == book_id, models.BookIssue.is_returned == False)
        .count()
    )
    if active_issues > 0:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Cannot delete book: {active_issues} copy/copies are currently issued and unreturned.",
        )

    total_issues = db.query(models.BookIssue).filter(models.BookIssue.book_id == book_id).count()
    if total_issues > 0:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=(
                f"Cannot delete book: this book has {total_issues} borrowing record(s) on file. "
                "Books with borrowing records cannot be deleted to preserve audit history."
            ),
        )

    db.delete(book)
    db.commit()
    return {"message": f"Book '{book.title}' (ID: {book_id}) was deleted successfully."}


@app.get("/books/search/{keyword}", response_model=List[schemas.BookResponse], tags=["Books"])
def search_books(keyword: str, db: Session = Depends(get_db)):
    """Search for books matching keyword in title, author, or category (Public)."""
    search_term = f"%{keyword}%"
    results = (
        db.query(models.Book)
        .filter(
            or_(
                models.Book.title.ilike(search_term),
                models.Book.author.ilike(search_term),
                models.Book.category.ilike(search_term),
            )
        )
        .all()
    )
    return results


# ===========================================================================
# 5. Book Issue and Return Endpoints
# ===========================================================================

@app.post(
    "/issues",
    response_model=schemas.BookIssueResponse,
    status_code=status.HTTP_201_CREATED,
    tags=["Book Issue & Return"],
)
def issue_book(
    issue_data: schemas.BookIssueCreate,
    db: Session = Depends(get_db),
    current_admin: dict = Depends(get_current_admin),
):
    """Issue a book to a student (Protected: Admin only)."""
    require_admin_role(current_admin)
    student = db.query(models.Student).filter(models.Student.id == issue_data.student_id).first()
    if not student:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Student with ID {issue_data.student_id} not found.",
        )

    book = db.query(models.Book).filter(models.Book.id == issue_data.book_id).first()
    if not book:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Book with ID {issue_data.book_id} not found.",
        )

    if book.available_copies <= 0:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Book '{book.title}' is currently out of stock. No copies available to issue.",
        )

    already_issued = (
        db.query(models.BookIssue)
        .filter(
            models.BookIssue.student_id == issue_data.student_id,
            models.BookIssue.book_id == issue_data.book_id,
            models.BookIssue.is_returned == False,
        )
        .first()
    )
    if already_issued:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Student {student.name} already has an unreturned copy of '{book.title}'.",
        )

    book.available_copies -= 1

    today = date.today()
    due = today + timedelta(days=14)

    new_issue = models.BookIssue(
        student_id=issue_data.student_id,
        book_id=issue_data.book_id,
        issue_date=today,
        due_date=due,
        fine=0.0,
        is_returned=False,
    )
    db.add(new_issue)
    db.commit()
    db.refresh(new_issue)
    return new_issue


@app.get("/issues", response_model=List[schemas.BookIssueResponse], tags=["Book Issue & Return"])
def list_issues(
    db: Session = Depends(get_db),
    current_admin: dict = Depends(get_current_admin),
):
    """Retrieve all book issue records (Protected: Admin only)."""
    require_admin_role(current_admin)
    return db.query(models.BookIssue).all()


@app.get(
    "/students/{student_id}/issues",
    response_model=List[schemas.BookIssueResponse],
    tags=["Book Issue & Return"],
)
def get_student_issues(student_id: int, db: Session = Depends(get_db)):
    """Retrieve borrowing history for a specific student (Accessible to student & admin)."""
    student = db.query(models.Student).filter(models.Student.id == student_id).first()
    if not student:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Student with ID {student_id} not found.",
        )
    return db.query(models.BookIssue).filter(models.BookIssue.student_id == student_id).all()


@app.put(
    "/issues/{issue_id}/return",
    response_model=schemas.BookIssueResponse,
    tags=["Book Issue & Return"],
)
def return_book(
    issue_id: int,
    db: Session = Depends(get_db),
    current_admin: dict = Depends(get_current_admin),
):
    """Process returning an issued book (Protected: Admin only)."""
    require_admin_role(current_admin)
    issue = db.query(models.BookIssue).filter(models.BookIssue.id == issue_id).first()
    if not issue:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Issue record with ID {issue_id} not found.",
        )

    if issue.is_returned:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="This book issue has already been marked as returned.",
        )

    book = db.query(models.Book).filter(models.Book.id == issue.book_id).first()
    if book and book.available_copies < book.total_copies:
        book.available_copies += 1

    today = date.today()
    issue.return_date = today
    issue.is_returned = True

    if today > issue.due_date:
        overdue_days = (today - issue.due_date).days
        issue.fine = float(overdue_days * 5.0)
    else:
        issue.fine = 0.0

    db.commit()
    db.refresh(issue)
    return issue


# ===========================================================================
# 6. Book Request Endpoints (Student & Admin)
# ===========================================================================

@app.post(
    "/book-requests",
    response_model=schemas.BookRequestStudentResponse,
    status_code=status.HTTP_201_CREATED,
    tags=["Book Requests (Student)"],
)
def create_book_request(
    req_data: schemas.BookRequestCreate,
    db: Session = Depends(get_db),
    current_student: models.Student = Depends(get_current_student),
):
    """
    Submit a book borrow request as an authenticated student.
    - student_id is extracted exclusively from the student's JWT token.
    - Verifies book existence and copy availability.
    - Prevents duplicate pending requests for the same book by the same student.
    - Saves with status 'Pending' without decrementing inventory yet.
    """
    # 1. Check whether the book exists
    book = db.query(models.Book).filter(models.Book.id == req_data.book_id).first()
    if not book:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Book with ID {req_data.book_id} not found.",
        )

    # 2. Check copy availability
    if book.available_copies <= 0:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Book '{book.title}' is currently out of stock. Cannot submit request.",
        )

    # 3. Check if student already has an active (unreturned) loan of this book
    active_issue = (
        db.query(models.BookIssue)
        .filter(
            models.BookIssue.student_id == current_student.id,
            models.BookIssue.book_id == req_data.book_id,
            models.BookIssue.is_returned == False,
        )
        .first()
    )
    if active_issue:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"You currently have an unreturned copy of '{book.title}'.",
        )

    # 4. Prevent duplicate pending requests for the same student and book
    duplicate_pending = (
        db.query(models.BookRequest)
        .filter(
            models.BookRequest.student_id == current_student.id,
            models.BookRequest.book_id == req_data.book_id,
            models.BookRequest.status == "Pending",
        )
        .first()
    )
    if duplicate_pending:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"You already have a pending request for '{book.title}'.",
        )

    # 5. Create request record (available_copies remains untouched until admin approval)
    new_request = models.BookRequest(
        student_id=current_student.id,
        book_id=req_data.book_id,
        status="Pending",
    )
    db.add(new_request)
    db.commit()
    db.refresh(new_request)

    return schemas.BookRequestStudentResponse(
        id=new_request.id,
        book_id=book.id,
        book_title=book.title,
        book_author=book.author,
        request_date=new_request.request_date,
        status=new_request.status,
        reviewed_at=new_request.reviewed_at,
        remarks=new_request.remarks,
    )


@app.get(
    "/book-requests/my",
    response_model=List[schemas.BookRequestStudentResponse],
    tags=["Book Requests (Student)"],
)
def get_my_book_requests(
    db: Session = Depends(get_db),
    current_student: models.Student = Depends(get_current_student),
):
    """
    Retrieve all book requests belonging exclusively to the authenticated student.
    Includes book title, author, request date, status, and admin remarks.
    """
    requests = (
        db.query(models.BookRequest)
        .filter(models.BookRequest.student_id == current_student.id)
        .order_by(models.BookRequest.request_date.desc())
        .all()
    )
    result = []
    for r in requests:
        result.append(
            schemas.BookRequestStudentResponse(
                id=r.id,
                book_id=r.book_id,
                book_title=r.book.title if r.book else "Unknown",
                book_author=r.book.author if r.book else "Unknown",
                request_date=r.request_date,
                status=r.status,
                reviewed_at=r.reviewed_at,
                remarks=r.remarks,
            )
        )
    return result


@app.get(
    "/admin/book-requests",
    response_model=List[schemas.BookRequestAdminResponse],
    tags=["Book Requests (Admin)"],
)
def list_admin_book_requests(
    db: Session = Depends(get_db),
    current_admin: dict = Depends(get_current_admin),
):
    """
    Retrieve all student book requests across the system (Protected: Admin only).
    Includes student name, roll number, book title, request date, and status.
    """
    require_admin_role(current_admin)
    requests = (
        db.query(models.BookRequest)
        .order_by(models.BookRequest.request_date.desc())
        .all()
    )
    result = []
    for r in requests:
        result.append(
            schemas.BookRequestAdminResponse(
                id=r.id,
                student_id=r.student_id,
                student_name=r.student.name if r.student else "Unknown",
                student_roll_number=r.student.roll_number if r.student else "Unknown",
                book_id=r.book_id,
                book_title=r.book.title if r.book else "Unknown",
                book_author=r.book.author if r.book else "Unknown",
                request_date=r.request_date,
                status=r.status,
                reviewed_at=r.reviewed_at,
                remarks=r.remarks,
            )
        )
    return result


@app.put(
    "/admin/book-requests/{request_id}/approve",
    response_model=schemas.BookRequestAdminResponse,
    tags=["Book Requests (Admin)"],
)
def approve_book_request(
    request_id: int,
    db: Session = Depends(get_db),
    current_admin: dict = Depends(get_current_admin),
):
    """
    Approve a student book request (Protected: Admin only).
    Transactional workflow:
    - Verifies request is in 'Pending' status.
    - Verifies book still has available copies.
    - Creates a BookIssue record with a 14-day loan period.
    - Decrements available_copies by 1.
    - Updates request status to 'Approved' and records reviewed_at.
    """
    require_admin_role(current_admin)
    req = db.query(models.BookRequest).filter(models.BookRequest.id == request_id).first()
    if not req:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Book request with ID {request_id} not found.",
        )

    if req.status != "Pending":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Request #{request_id} cannot be approved because it has already been reviewed (Status: {req.status}).",
        )

    book = db.query(models.Book).filter(models.Book.id == req.book_id).first()
    if not book or book.available_copies <= 0:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot approve request: Book is currently out of stock.",
        )

    try:
        today = date.today()
        due = today + timedelta(days=14)

        # 1. Create loan record
        new_issue = models.BookIssue(
            student_id=req.student_id,
            book_id=req.book_id,
            issue_date=today,
            due_date=due,
            fine=0.0,
            is_returned=False,
        )
        db.add(new_issue)

        # 2. Decrement inventory
        book.available_copies -= 1

        # 3. Update request status
        req.status = "Approved"
        req.reviewed_at = datetime.now(timezone.utc)
        req.remarks = "Approved by Administrator"

        db.commit()
        db.refresh(req)
    except Exception as exc:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to process request approval transaction: {exc}",
        )

    return schemas.BookRequestAdminResponse(
        id=req.id,
        student_id=req.student_id,
        student_name=req.student.name if req.student else "Unknown",
        student_roll_number=req.student.roll_number if req.student else "Unknown",
        book_id=req.book_id,
        book_title=req.book.title if req.book else "Unknown",
        book_author=req.book.author if req.book else "Unknown",
        request_date=req.request_date,
        status=req.status,
        reviewed_at=req.reviewed_at,
        remarks=req.remarks,
    )


@app.put(
    "/admin/book-requests/{request_id}/reject",
    response_model=schemas.BookRequestAdminResponse,
    tags=["Book Requests (Admin)"],
)
def reject_book_request(
    request_id: int,
    review_data: Optional[schemas.BookRequestReview] = None,
    db: Session = Depends(get_db),
    current_admin: dict = Depends(get_current_admin),
):
    """
    Reject a student book request (Protected: Admin only).
    - Verifies request is in 'Pending' status.
    - Sets status to 'Rejected' and records reviewed_at and optional remarks.
    - Does not alter available_copies.
    """
    require_admin_role(current_admin)
    req = db.query(models.BookRequest).filter(models.BookRequest.id == request_id).first()
    if not req:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Book request with ID {request_id} not found.",
        )

    if req.status != "Pending":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Request #{request_id} cannot be rejected because it has already been reviewed (Status: {req.status}).",
        )

    req.status = "Rejected"
    req.reviewed_at = datetime.now(timezone.utc)
    req.remarks = (
        review_data.remarks
        if review_data and review_data.remarks
        else "Rejected by Administrator"
    )

    db.commit()
    db.refresh(req)

    return schemas.BookRequestAdminResponse(
        id=req.id,
        student_id=req.student_id,
        student_name=req.student.name if req.student else "Unknown",
        student_roll_number=req.student.roll_number if req.student else "Unknown",
        book_id=req.book_id,
        book_title=req.book.title if req.book else "Unknown",
        book_author=req.book.author if req.book else "Unknown",
        request_date=req.request_date,
        status=req.status,
        reviewed_at=req.reviewed_at,
        remarks=req.remarks,
    )
