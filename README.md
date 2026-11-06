# 📚 Library Management System (Full Stack)

A complete, full-stack **Library Management System** built with **FastAPI**, **MySQL**, **SQLAlchemy**, and **React + Vite**.

Designed with clean, beginner-friendly architecture, role-based security, automated late fines, and a two-stage **Book Request & Approval workflow**.

---

## 🛠️ Technology Stack

- **Backend:** Python 3.13, FastAPI, SQLAlchemy ORM, Pydantic v2
- **Database:** MySQL Server, PyMySQL driver, Cryptography
- **Security:** Bcrypt password hashing, signed JWT Bearer tokens
- **Frontend:** React 18, Vite, custom responsive CSS (no heavy UI dependencies)
- **Architecture:** Decoupled RESTful API with CORS enabled

---

## ✨ Features

### 🎓 Student Portal
- **Student Registration & Login:** Encrypted passwords using `bcrypt`.
- **Catalogue & Real-Time Search:** Search books by title, author, or category.
- **Book Request System:** Request available books with one click (prevents duplicate requests).
- **Personal Borrowing History:** Track active loans, due dates, return dates, and late fines.
- **My Book Requests:** Monitor request status (`Pending`, `Approved`, `Rejected`) with admin remarks.

### 🛡️ Administrator Portal
- **Dashboard & Statistics:** Real-time metrics for total catalog, available copies, active loans, and pending requests.
- **Book Catalog Management (CRUD):** Add new titles, edit existing books, and safe deletion.
- **Request Approval Queue:** Review student requests with transactional approval (auto-creates loan & decreases inventory) or rejection with custom remarks.
- **Manual Issue & Return:** Process physical checkouts and returns with automated fine calculation (₹5/day overdue).
- **Student Directory:** View all registered students.

---

## 📁 Project Structure

```text
Library_Management_System/
├── .gitignore                # Protects credentials, venv, and node_modules
├── README.md                 # Project documentation
├── backend/
│   ├── .env.example          # Environment variables template
│   ├── requirements.txt      # Python dependencies
│   ├── database.py           # Database engine & session management
│   ├── models.py             # SQLAlchemy models (Student, Book, BookIssue, BookRequest)
│   ├── schemas.py            # Pydantic v2 validation models
│   ├── create_tables.py      # Non-destructive table creation script
│   ├── main.py               # FastAPI application & REST endpoints
│   └── test_api.py           # Automated test suite
└── frontend/
    ├── package.json          # Node dependencies & build scripts
    ├── vite.config.js        # Vite development server config
    ├── index.html            # Single page entry point
    └── src/
        ├── api.js            # Centralized API service with JWT authorization
        ├── App.jsx           # Main UI with role-based routing
        ├── index.css         # Responsive styling
        └── main.jsx          # React DOM mounting
```

---

## 🚀 Getting Started

### 1. Database Setup
1. In MySQL Workbench or CLI, create the database:
   ```sql
   CREATE DATABASE IF NOT EXISTS library_db;
   ```
2. In `backend/`, copy `.env.example` to `.env`:
   ```powershell
   Copy-Item backend\.env.example backend\.env
   ```
3. Open `backend/.env` and enter your MySQL root password and preferred admin credentials:
   ```ini
   DB_HOST=localhost
   DB_PORT=3306
   DB_USER=root
   DB_PASSWORD=your_actual_mysql_password
   DB_NAME=library_db

   ADMIN_USERNAME=admin
   ADMIN_PASSWORD=your_secure_admin_password
   JWT_SECRET_KEY=your_random_secret_key
   ```

### 2. Backend Setup
```powershell
# Activate virtual environment
.\backend\venv\Scripts\Activate.ps1

# Install dependencies (if not already installed)
pip install -r backend\requirements.txt

# Create MySQL tables safely
python backend\create_tables.py

# Start FastAPI server
python -m uvicorn main:app --app-dir backend --reload --port 8000
```
- API root: `http://127.0.0.1:8000`
- Swagger Interactive Docs: `http://127.0.0.1:8000/docs`

### 3. Frontend Setup
In a new terminal window:
```powershell
cd frontend
npm install
npm run dev
```
- Open `http://127.0.0.1:5173` in your browser.

---

## 🧪 Running Automated Tests

Run the complete test suite verifying all 12 core workflows and security checks against MySQL:

```powershell
.\backend\venv\Scripts\python.exe backend\test_api.py
```

---

## 🔒 Security Practices
- Database passwords and admin credentials are kept strictly inside `backend/.env` and ignored by Git.
- Passwords are encrypted with salt using native `bcrypt`.
- Protected endpoints require valid signed `JWT Bearer` authorization headers.
- Student endpoints resolve the requesting user from the cryptographic token payload, never trusting request bodies.
