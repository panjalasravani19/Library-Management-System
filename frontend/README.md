# Library Management System - Frontend

A clean, responsive, and beginner-friendly React + Vite web application for the Library Management System.

---

## 🛠️ Tech Stack
- **Framework:** React 18 + Vite
- **Language:** JavaScript (JSX)
- **Styling:** Custom Clean CSS (no heavy UI frameworks, mobile responsive)
- **Backend API:** FastAPI (`http://127.0.0.1:8000`)

---

## 🚀 How to Run the Frontend

### 1. Open Terminal in the `frontend` folder
```powershell
cd D:\Library_Management_System\frontend
```

### 2. Install Dependencies
```powershell
npm.cmd install
```
*(or `npm install` if PowerShell script execution is enabled)*

### 3. Start the Development Server
```powershell
npm.cmd run dev
```

### 4. Open in Browser
Visit: 👉 **`http://127.0.0.1:5173`** (or `http://localhost:5173`)

---

## 📌 Available Sections

| Section | Description |
| :--- | :--- |
| **Home** | Dashboard displaying live statistics (total books, available inventory, registered students, active loans) and backend connectivity status. |
| **Catalogue** | Browse all cataloged books with stock indicators. |
| **Search** | Real-time search by title, author, or category. |
| **Admin Books** | Add new books, edit existing inventory, or delete books safely. |
| **Issue Book** | Check out a book to a student with automatic 14-day return due date. |
| **Return Book** | View active loans, process returns, and calculate late fines automatically. |
| **Borrow History** | Look up full borrowing history for any student. |
| **Student Register & Login** | Register student accounts with encrypted passwords or sign in. |

---

## ⚙️ Backend Connection
The frontend connects directly to your FastAPI backend at:
`http://127.0.0.1:8000`

Make sure the FastAPI server is running before opening the frontend:
```powershell
.\backend\venv\Scripts\python.exe -m uvicorn main:app --app-dir backend --reload --port 8000
```
