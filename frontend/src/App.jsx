import React, { useState, useEffect } from 'react';
import { api } from './api';

export default function App() {
  // Session / User State: null | { role: 'admin', username: string } | { role: 'student', id, name, email, roll_number }
  const [currentUser, setCurrentUser] = useState(() => {
    try {
      const saved = localStorage.getItem('library_user_session');
      return saved ? JSON.parse(saved) : null;
    } catch {
      return null;
    }
  });

  // Navigation tab:
  // Non-logged: 'welcome' | 'admin-login' | 'student-login' | 'student-register' | 'books' | 'search'
  // Student:    'books' | 'search' | 'my-history' | 'my-requests'
  // Admin:      'home' | 'books' | 'search' | 'admin-books' | 'admin-requests' | 'issue' | 'return' | 'students-list'
  const [activeTab, setActiveTab] = useState(() => {
    const saved = localStorage.getItem('library_user_session');
    if (!saved) return 'welcome';
    const user = JSON.parse(saved);
    return user.role === 'admin' ? 'home' : 'books';
  });

  // Global alert message
  const [alert, setAlert] = useState(null); // { type: 'success' | 'error', message: '' }

  // Shared Data
  const [books, setBooks] = useState([]);
  const [students, setStudents] = useState([]);
  const [issues, setIssues] = useState([]);
  const [systemHealth, setSystemHealth] = useState(null);
  const [loading, setLoading] = useState(false);

  // Book Requests State
  const [myRequests, setMyRequests] = useState([]);
  const [adminRequests, setAdminRequests] = useState([]);

  // Search state
  const [searchKeyword, setSearchKeyword] = useState('');
  const [searchResults, setSearchResults] = useState([]);

  // Login & Registration Form States
  const [adminLoginForm, setAdminLoginForm] = useState({ username: '', password: '' });
  const [studentLoginForm, setStudentLoginForm] = useState({ email: '', password: '' });
  const [studentRegForm, setStudentRegForm] = useState({
    name: '',
    email: '',
    roll_number: '',
    phone: '',
    password: '',
  });

  // Admin Book Form State
  const [bookForm, setBookForm] = useState({
    title: '',
    author: '',
    isbn: '',
    category: '',
    total_copies: 1,
  });
  const [editingBookId, setEditingBookId] = useState(null);

  // Admin Issue Form State
  const [issueForm, setIssueForm] = useState({ student_id: '', book_id: '' });

  // Student history state
  const [myHistory, setMyHistory] = useState([]);

  // Helper to show alert with auto-dismiss
  const showAlert = (type, message) => {
    setAlert({ type, message });
    setTimeout(() => {
      setAlert((curr) => (curr?.message === message ? null : curr));
    }, 6000);
  };

  // Initial load
  useEffect(() => {
    fetchHealth();
    fetchPublicBooks();
    if (currentUser?.role === 'admin') {
      fetchAdminData();
      fetchAdminRequests();
    } else if (currentUser?.role === 'student') {
      fetchStudentHistory(currentUser.id);
      fetchStudentRequests();
    }
  }, [currentUser]);

  const fetchHealth = async () => {
    try {
      const res = await api.getHealth();
      setSystemHealth(res.status);
    } catch {
      setSystemHealth('offline');
    }
  };

  const fetchPublicBooks = async () => {
    try {
      const data = await api.getBooks();
      setBooks(data);
    } catch (err) {
      console.error(err);
    }
  };

  const fetchAdminData = async () => {
    setLoading(true);
    try {
      const [booksData, studentsData, issuesData] = await Promise.all([
        api.getBooks().catch(() => []),
        api.getStudents().catch(() => []),
        api.getIssues().catch(() => []),
      ]);
      setBooks(booksData);
      setStudents(studentsData);
      setIssues(issuesData);
    } catch (err) {
      showAlert('error', err.message);
    } finally {
      setLoading(false);
    }
  };

  const fetchStudentHistory = async (studentId) => {
    if (!studentId) return;
    try {
      const history = await api.getStudentIssues(studentId);
      setMyHistory(history);
    } catch (err) {
      showAlert('error', err.message);
    }
  };

  const fetchStudentRequests = async () => {
    try {
      const reqs = await api.getMyBookRequests();
      setMyRequests(reqs);
    } catch (err) {
      console.error(err);
    }
  };

  const fetchAdminRequests = async () => {
    try {
      const reqs = await api.getAdminBookRequests();
      setAdminRequests(reqs);
    } catch (err) {
      console.error(err);
    }
  };

  // -------------------------------------------------------------------------
  // Authentication Actions
  // -------------------------------------------------------------------------
  const handleAdminLogin = async (e) => {
    e.preventDefault();
    try {
      const res = await api.adminLogin(adminLoginForm);
      api.setAuthToken(res.access_token);

      const userSession = { role: 'admin', username: res.username };
      setCurrentUser(userSession);
      localStorage.setItem('library_user_session', JSON.stringify(userSession));

      showAlert('success', `Logged in successfully as Administrator (${res.username})`);
      setAdminLoginForm({ username: '', password: '' });
      setActiveTab('home');
    } catch (err) {
      showAlert('error', err.message);
    }
  };

  const handleStudentLogin = async (e) => {
    e.preventDefault();
    try {
      const res = await api.loginStudent(studentLoginForm);
      api.setAuthToken(res.access_token);

      const userSession = { role: 'student', ...res.student };
      setCurrentUser(userSession);
      localStorage.setItem('library_user_session', JSON.stringify(userSession));

      showAlert('success', `Welcome back, ${res.student.name}!`);
      setStudentLoginForm({ email: '', password: '' });
      setActiveTab('books');
    } catch (err) {
      showAlert('error', err.message);
    }
  };

  const handleStudentRegister = async (e) => {
    e.preventDefault();
    try {
      const newStudent = await api.registerStudent(studentRegForm);
      showAlert('success', `Registration successful for '${newStudent.name}'. Please log in!`);
      setStudentRegForm({ name: '', email: '', roll_number: '', phone: '', password: '' });
      setActiveTab('student-login');
    } catch (err) {
      showAlert('error', err.message);
    }
  };

  const handleLogout = () => {
    api.setAuthToken(null);
    setCurrentUser(null);
    localStorage.removeItem('library_user_session');
    setMyHistory([]);
    setMyRequests([]);
    setAdminRequests([]);
    showAlert('success', 'You have been logged out.');
    setActiveTab('welcome');
  };

  // -------------------------------------------------------------------------
  // Student Book Request Action
  // -------------------------------------------------------------------------
  const handleRequestBook = async (bookId) => {
    try {
      await api.requestBook(bookId);
      showAlert('success', 'Book request submitted successfully! Awaiting admin approval.');
      fetchStudentRequests();
      fetchPublicBooks();
    } catch (err) {
      showAlert('error', err.message);
    }
  };

  // -------------------------------------------------------------------------
  // Admin Book Request Actions (Approve / Reject)
  // -------------------------------------------------------------------------
  const handleApproveRequest = async (requestId) => {
    if (!window.confirm(`Are you sure you want to approve request #${requestId}? This will issue the book to the student.`)) {
      return;
    }
    try {
      await api.approveBookRequest(requestId);
      showAlert('success', `Request #${requestId} approved! The book has been issued.`);
      fetchAdminRequests();
      fetchAdminData();
    } catch (err) {
      showAlert('error', err.message);
    }
  };

  const handleRejectRequest = async (requestId) => {
    const remarks = window.prompt('Enter reason / remarks for rejection (optional):', 'Currently reserved or unavailable');
    if (remarks === null) return; // User clicked cancel

    try {
      await api.rejectBookRequest(requestId, remarks);
      showAlert('success', `Request #${requestId} has been rejected.`);
      fetchAdminRequests();
    } catch (err) {
      showAlert('error', err.message);
    }
  };

  // -------------------------------------------------------------------------
  // Book CRUD Actions (Admin Protected)
  // -------------------------------------------------------------------------
  const handleSaveBook = async (e) => {
    e.preventDefault();
    try {
      if (editingBookId) {
        await api.updateBook(editingBookId, bookForm);
        showAlert('success', 'Book updated successfully!');
        setEditingBookId(null);
      } else {
        await api.addBook(bookForm);
        showAlert('success', 'New book added to library catalog!');
      }
      setBookForm({ title: '', author: '', isbn: '', category: '', total_copies: 1 });
      fetchAdminData();
    } catch (err) {
      showAlert('error', err.message);
    }
  };

  const handleEditBook = (book) => {
    setEditingBookId(book.id);
    setBookForm({
      title: book.title,
      author: book.author,
      isbn: book.isbn || '',
      category: book.category || '',
      total_copies: book.total_copies,
    });
    setActiveTab('admin-books');
  };

  const handleDeleteBook = async (bookId) => {
    if (!window.confirm('Are you sure you want to delete this book?')) return;
    try {
      const res = await api.deleteBook(bookId);
      showAlert('success', res.message);
      fetchAdminData();
    } catch (err) {
      showAlert('error', err.message);
    }
  };

  const handleSearch = async (e) => {
    e.preventDefault();
    if (!searchKeyword.trim()) {
      setSearchResults([]);
      return;
    }
    try {
      const results = await api.searchBooks(searchKeyword);
      setSearchResults(results);
    } catch (err) {
      showAlert('error', err.message);
    }
  };

  // -------------------------------------------------------------------------
  // Issue & Return Actions (Admin Protected)
  // -------------------------------------------------------------------------
  const handleIssueBook = async (e) => {
    e.preventDefault();
    try {
      await api.issueBook({
        student_id: parseInt(issueForm.student_id, 10),
        book_id: parseInt(issueForm.book_id, 10),
      });
      showAlert('success', 'Book issued successfully! Due in 14 days.');
      setIssueForm({ student_id: '', book_id: '' });
      fetchAdminData();
      setActiveTab('return');
    } catch (err) {
      showAlert('error', err.message);
    }
  };

  const handleReturnBook = async (issueId) => {
    try {
      const res = await api.returnBook(issueId);
      const fineMsg = res.fine > 0 ? ` (Overdue fine: ₹${res.fine})` : ' (No late fine)';
      showAlert('success', `Book returned successfully!${fineMsg}`);
      fetchAdminData();
    } catch (err) {
      showAlert('error', err.message);
    }
  };

  // Set of book IDs that the current student has pending requests for
  const pendingBookIds = new Set(
    myRequests.filter((r) => r.status === 'Pending').map((r) => r.book_id)
  );

  return (
    <div>
      {/* Navbar with Role-Based Navigation */}
      <nav className="navbar">
        <div className="navbar-inner">
          <div
            className="brand"
            onClick={() => setActiveTab(currentUser ? (currentUser.role === 'admin' ? 'home' : 'books') : 'welcome')}
            style={{ cursor: 'pointer' }}
          >
            📚 <span>Library System</span>
          </div>

          <div className="nav-links">
            {/* 1. Unauthenticated Navigation */}
            {!currentUser && (
              <>
                <button
                  className={`nav-btn ${activeTab === 'welcome' ? 'active' : ''}`}
                  onClick={() => setActiveTab('welcome')}
                >
                  Welcome
                </button>
                <button
                  className={`nav-btn ${activeTab === 'books' ? 'active' : ''}`}
                  onClick={() => {
                    setActiveTab('books');
                    fetchPublicBooks();
                  }}
                >
                  Catalogue
                </button>
                <button
                  className={`nav-btn ${activeTab === 'search' ? 'active' : ''}`}
                  onClick={() => setActiveTab('search')}
                >
                  Search
                </button>
                <button
                  className={`nav-btn ${activeTab === 'student-login' ? 'active' : ''}`}
                  onClick={() => setActiveTab('student-login')}
                >
                  Student Login
                </button>
                <button
                  className={`nav-btn ${activeTab === 'admin-login' ? 'active' : ''}`}
                  onClick={() => setActiveTab('admin-login')}
                >
                  Admin Login
                </button>
              </>
            )}

            {/* 2. Student Navigation */}
            {currentUser?.role === 'student' && (
              <>
                <button
                  className={`nav-btn ${activeTab === 'books' ? 'active' : ''}`}
                  onClick={() => {
                    setActiveTab('books');
                    fetchPublicBooks();
                    fetchStudentRequests();
                  }}
                >
                  Catalogue
                </button>
                <button
                  className={`nav-btn ${activeTab === 'search' ? 'active' : ''}`}
                  onClick={() => setActiveTab('search')}
                >
                  Search
                </button>
                <button
                  className={`nav-btn ${activeTab === 'my-requests' ? 'active' : ''}`}
                  onClick={() => {
                    setActiveTab('my-requests');
                    fetchStudentRequests();
                  }}
                >
                  My Book Requests
                </button>
                <button
                  className={`nav-btn ${activeTab === 'my-history' ? 'active' : ''}`}
                  onClick={() => {
                    setActiveTab('my-history');
                    fetchStudentHistory(currentUser.id);
                  }}
                >
                  My Borrow History
                </button>
                <div className="user-bar">
                  <span>🎓 Student: {currentUser.name}</span>
                  <button className="user-logout-btn" onClick={handleLogout}>
                    Logout
                  </button>
                </div>
              </>
            )}

            {/* 3. Admin Navigation */}
            {currentUser?.role === 'admin' && (
              <>
                <button
                  className={`nav-btn ${activeTab === 'home' ? 'active' : ''}`}
                  onClick={() => {
                    setActiveTab('home');
                    fetchAdminData();
                    fetchAdminRequests();
                  }}
                >
                  Dashboard
                </button>
                <button
                  className={`nav-btn ${activeTab === 'books' ? 'active' : ''}`}
                  onClick={() => {
                    setActiveTab('books');
                    fetchPublicBooks();
                  }}
                >
                  Catalogue
                </button>
                <button
                  className={`nav-btn ${activeTab === 'admin-requests' ? 'active' : ''}`}
                  onClick={() => {
                    setActiveTab('admin-requests');
                    fetchAdminRequests();
                  }}
                >
                  Book Requests ({adminRequests.filter((r) => r.status === 'Pending').length})
                </button>
                <button
                  className={`nav-btn ${activeTab === 'admin-books' ? 'active' : ''}`}
                  onClick={() => setActiveTab('admin-books')}
                >
                  Manage Books
                </button>
                <button
                  className={`nav-btn ${activeTab === 'issue' ? 'active' : ''}`}
                  onClick={() => setActiveTab('issue')}
                >
                  Issue Book
                </button>
                <button
                  className={`nav-btn ${activeTab === 'return' ? 'active' : ''}`}
                  onClick={() => setActiveTab('return')}
                >
                  Return Book
                </button>
                <button
                  className={`nav-btn ${activeTab === 'students-list' ? 'active' : ''}`}
                  onClick={() => setActiveTab('students-list')}
                >
                  Students List
                </button>
                <div className="user-bar">
                  <span>🛡️ Admin: {currentUser.username}</span>
                  <button className="user-logout-btn" onClick={handleLogout}>
                    Logout
                  </button>
                </div>
              </>
            )}
          </div>
        </div>
      </nav>

      {/* Main Content Area */}
      <main className="app-container">
        {/* Global Alert Notification */}
        {alert && (
          <div className={`alert alert-${alert.type}`}>
            <span>{alert.message}</span>
            <button className="alert-close" onClick={() => setAlert(null)}>
              ×
            </button>
          </div>
        )}

        {/* ------------------------------------------------------------------ */}
        {/* WELCOME LANDING PAGE                                               */}
        {/* ------------------------------------------------------------------ */}
        {activeTab === 'welcome' && !currentUser && (
          <div>
            <div className="card" style={{ textAlign: 'center', padding: '48px 24px' }}>
              <h1 style={{ fontSize: '2.2rem', marginBottom: '12px', color: 'var(--text)' }}>
                Library Management System
              </h1>
              <p style={{ fontSize: '1.1rem', color: 'var(--text-muted)', maxWidth: '600px', margin: '0 auto' }}>
                Please select your login portal to access system features:
              </p>

              {/* Two Option Portal Cards */}
              <div className="portal-grid">
                <div className="portal-card" onClick={() => setActiveTab('admin-login')}>
                  <div className="portal-icon">🛡️</div>
                  <h3>Admin Portal</h3>
                  <p>For library staff to approve book requests, manage catalog, loans, and returns.</p>
                  <button className="btn btn-primary" style={{ width: '100%' }}>
                    Admin Login
                  </button>
                </div>

                <div className="portal-card" onClick={() => setActiveTab('student-login')}>
                  <div className="portal-icon">🎓</div>
                  <h3>Student Portal</h3>
                  <p>For registered students to browse catalog, submit book requests, and view loans.</p>
                  <button className="btn btn-secondary" style={{ width: '100%' }}>
                    Student Login
                  </button>
                </div>
              </div>

              <div style={{ marginTop: '24px' }}>
                <span style={{ color: 'var(--text-muted)' }}>Not a registered student yet? </span>
                <button
                  className="btn btn-sm btn-secondary"
                  onClick={() => setActiveTab('student-register')}
                  style={{ marginLeft: '6px' }}
                >
                  Register Here
                </button>
              </div>
            </div>
          </div>
        )}

        {/* ------------------------------------------------------------------ */}
        {/* ADMIN LOGIN PAGE                                                  */}
        {/* ------------------------------------------------------------------ */}
        {activeTab === 'admin-login' && !currentUser && (
          <div className="card" style={{ maxWidth: '480px', margin: '20px auto' }}>
            <div className="card-header">
              <h2 className="card-title">🛡️ Admin Login</h2>
            </div>
            <p style={{ color: 'var(--text-muted)', marginBottom: '18px', fontSize: '0.9rem' }}>
              Administrator credentials are authenticated securely via signed JWT tokens.
            </p>

            <form onSubmit={handleAdminLogin}>
              <div className="form-group" style={{ marginBottom: '14px' }}>
                <label>Admin Username *</label>
                <input
                  type="text"
                  required
                  placeholder="e.g. admin"
                  value={adminLoginForm.username}
                  onChange={(e) => setAdminLoginForm({ ...adminLoginForm, username: e.target.value })}
                />
              </div>

              <div className="form-group" style={{ marginBottom: '22px' }}>
                <label>Admin Password *</label>
                <input
                  type="password"
                  required
                  placeholder="Enter admin password"
                  value={adminLoginForm.password}
                  onChange={(e) => setAdminLoginForm({ ...adminLoginForm, password: e.target.value })}
                />
              </div>

              <button type="submit" className="btn btn-primary" style={{ width: '100%' }}>
                Sign In as Admin
              </button>
            </form>

            <div style={{ marginTop: '16px', textAlign: 'center' }}>
              <button
                className="btn btn-secondary btn-sm"
                onClick={() => setActiveTab('student-login')}
              >
                Go to Student Login
              </button>
            </div>
          </div>
        )}

        {/* ------------------------------------------------------------------ */}
        {/* STUDENT LOGIN PAGE                                                */}
        {/* ------------------------------------------------------------------ */}
        {activeTab === 'student-login' && !currentUser && (
          <div className="card" style={{ maxWidth: '480px', margin: '20px auto' }}>
            <div className="card-header">
              <h2 className="card-title">🎓 Student Login</h2>
            </div>
            <p style={{ color: 'var(--text-muted)', marginBottom: '18px', fontSize: '0.9rem' }}>
              Students must be registered before logging in.
            </p>

            <form onSubmit={handleStudentLogin}>
              <div className="form-group" style={{ marginBottom: '14px' }}>
                <label>Email Address *</label>
                <input
                  type="email"
                  required
                  placeholder="e.g. student@example.com"
                  value={studentLoginForm.email}
                  onChange={(e) => setStudentLoginForm({ ...studentLoginForm, email: e.target.value })}
                />
              </div>

              <div className="form-group" style={{ marginBottom: '22px' }}>
                <label>Password *</label>
                <input
                  type="password"
                  required
                  placeholder="Enter your student password"
                  value={studentLoginForm.password}
                  onChange={(e) => setStudentLoginForm({ ...studentLoginForm, password: e.target.value })}
                />
              </div>

              <button type="submit" className="btn btn-primary" style={{ width: '100%' }}>
                Sign In as Student
              </button>
            </form>

            <div style={{ marginTop: '18px', textAlign: 'center' }}>
              <span style={{ fontSize: '0.9rem', color: 'var(--text-muted)' }}>
                Don't have an account?{' '}
              </span>
              <button
                className="btn btn-secondary btn-sm"
                onClick={() => setActiveTab('student-register')}
              >
                Register Here
              </button>
            </div>
          </div>
        )}

        {/* ------------------------------------------------------------------ */}
        {/* STUDENT REGISTRATION PAGE                                         */}
        {/* ------------------------------------------------------------------ */}
        {activeTab === 'student-register' && !currentUser && (
          <div className="card" style={{ maxWidth: '580px', margin: '20px auto' }}>
            <div className="card-header">
              <h2 className="card-title">📝 Student Registration</h2>
            </div>

            <form onSubmit={handleStudentRegister}>
              <div className="form-group" style={{ marginBottom: '12px' }}>
                <label>Full Name *</label>
                <input
                  type="text"
                  required
                  placeholder="e.g. Alice Johnson"
                  value={studentRegForm.name}
                  onChange={(e) => setStudentRegForm({ ...studentRegForm, name: e.target.value })}
                />
              </div>

              <div className="form-group" style={{ marginBottom: '12px' }}>
                <label>Email Address *</label>
                <input
                  type="email"
                  required
                  placeholder="e.g. alice@university.edu"
                  value={studentRegForm.email}
                  onChange={(e) => setStudentRegForm({ ...studentRegForm, email: e.target.value })}
                />
              </div>

              <div className="form-group" style={{ marginBottom: '12px' }}>
                <label>Roll Number / Student ID *</label>
                <input
                  type="text"
                  required
                  placeholder="e.g. CS2026-45"
                  value={studentRegForm.roll_number}
                  onChange={(e) => setStudentRegForm({ ...studentRegForm, roll_number: e.target.value })}
                />
              </div>

              <div className="form-group" style={{ marginBottom: '12px' }}>
                <label>Phone Number (Optional)</label>
                <input
                  type="tel"
                  placeholder="e.g. 9876543210"
                  value={studentRegForm.phone}
                  onChange={(e) => setStudentRegForm({ ...studentRegForm, phone: e.target.value })}
                />
              </div>

              <div className="form-group" style={{ marginBottom: '22px' }}>
                <label>Password * (Minimum 6 characters)</label>
                <input
                  type="password"
                  required
                  minLength={6}
                  placeholder="Create a secure password"
                  value={studentRegForm.password}
                  onChange={(e) => setStudentRegForm({ ...studentRegForm, password: e.target.value })}
                />
              </div>

              <button type="submit" className="btn btn-primary" style={{ width: '100%' }}>
                Register Account
              </button>
            </form>

            <div style={{ marginTop: '16px', textAlign: 'center' }}>
              <span style={{ fontSize: '0.9rem', color: 'var(--text-muted)' }}>
                Already registered?{' '}
              </span>
              <button
                className="btn btn-secondary btn-sm"
                onClick={() => setActiveTab('student-login')}
              >
                Log In
              </button>
            </div>
          </div>
        )}

        {/* ------------------------------------------------------------------ */}
        {/* ADMIN DASHBOARD (Home)                                            */}
        {/* ------------------------------------------------------------------ */}
        {activeTab === 'home' && currentUser?.role === 'admin' && (
          <div>
            <div className="card">
              <h2 style={{ marginBottom: '6px' }}>🛡️ Administrator Dashboard</h2>
              <p style={{ color: 'var(--text-muted)' }}>
                Welcome back, <strong>{currentUser.username}</strong>! Complete library controls are enabled.
              </p>
              <div style={{ marginTop: '12px' }}>
                <span
                  className={`badge ${
                    systemHealth === 'healthy' ? 'badge-success' : 'badge-danger'
                  }`}
                >
                  System Status: {systemHealth === 'healthy' ? '● Online & Connected' : '○ Offline'}
                </span>
              </div>
            </div>

            <div className="stats-grid">
              <div className="stat-card">
                <div className="stat-label">Total Books Cataloged</div>
                <div className="stat-value">{books.length}</div>
              </div>
              <div className="stat-card">
                <div className="stat-label">Pending Book Requests</div>
                <div className="stat-value" style={{ color: '#2563eb' }}>
                  {adminRequests.filter((r) => r.status === 'Pending').length}
                </div>
              </div>
              <div className="stat-card">
                <div className="stat-label">Available Copies</div>
                <div className="stat-value" style={{ color: 'var(--success)' }}>
                  {books.reduce((acc, b) => acc + b.available_copies, 0)}
                </div>
              </div>
              <div className="stat-card">
                <div className="stat-label">Active Loans</div>
                <div className="stat-value" style={{ color: 'var(--warning)' }}>
                  {issues.filter((i) => !i.is_returned).length}
                </div>
              </div>
            </div>

            <div className="card">
              <div className="card-header">
                <h3 className="card-title">Admin Quick Operations</h3>
              </div>
              <div style={{ display: 'flex', gap: '12px', flexWrap: 'wrap' }}>
                <button className="btn btn-primary" onClick={() => setActiveTab('admin-requests')}>
                  Review Book Requests ({adminRequests.filter((r) => r.status === 'Pending').length})
                </button>
                <button className="btn btn-secondary" onClick={() => setActiveTab('admin-books')}>
                  + Add / Manage Books
                </button>
                <button className="btn btn-secondary" onClick={() => setActiveTab('issue')}>
                  Issue Book to Student
                </button>
                <button className="btn btn-secondary" onClick={() => setActiveTab('return')}>
                  Process Returns
                </button>
                <button className="btn btn-secondary" onClick={() => setActiveTab('students-list')}>
                  View Student Directory
                </button>
              </div>
            </div>
          </div>
        )}

        {/* ------------------------------------------------------------------ */}
        {/* STUDENT: MY BOOK REQUESTS (PART 4)                                 */}
        {/* ------------------------------------------------------------------ */}
        {activeTab === 'my-requests' && currentUser?.role === 'student' && (
          <div className="card">
            <div className="card-header">
              <h2 className="card-title">📬 My Book Requests</h2>
              <button
                className="btn btn-secondary btn-sm"
                onClick={() => fetchStudentRequests()}
              >
                Refresh
              </button>
            </div>

            {myRequests.length === 0 ? (
              <div className="empty-state">
                <h3>No book requests submitted!</h3>
                <p>Browse the book catalogue and click "Request Book" to borrow books.</p>
                <button
                  className="btn btn-primary btn-sm"
                  style={{ marginTop: '12px' }}
                  onClick={() => setActiveTab('books')}
                >
                  Browse Catalogue
                </button>
              </div>
            ) : (
              <div className="table-responsive">
                <table>
                  <thead>
                    <tr>
                      <th>Request ID</th>
                      <th>Book Title</th>
                      <th>Author</th>
                      <th>Request Date</th>
                      <th>Status</th>
                      <th>Admin Remarks</th>
                    </tr>
                  </thead>
                  <tbody>
                    {myRequests.map((req) => (
                      <tr key={req.id}>
                        <td>#{req.id}</td>
                        <td><strong>{req.book_title}</strong></td>
                        <td>{req.book_author}</td>
                        <td>{new Date(req.request_date).toLocaleString()}</td>
                        <td>
                          {req.status === 'Pending' && (
                            <span className="badge badge-warning">Pending Review</span>
                          )}
                          {req.status === 'Approved' && (
                            <span className="badge badge-success">Approved (Issued)</span>
                          )}
                          {req.status === 'Rejected' && (
                            <span className="badge badge-danger">Rejected</span>
                          )}
                        </td>
                        <td>{req.remarks || '—'}</td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            )}
          </div>
        )}

        {/* ------------------------------------------------------------------ */}
        {/* ADMIN: BOOK REQUESTS MANAGEMENT (PART 5)                           */}
        {/* ------------------------------------------------------------------ */}
        {activeTab === 'admin-requests' && currentUser?.role === 'admin' && (
          <div className="card">
            <div className="card-header">
              <h2 className="card-title">📬 Student Book Requests ({adminRequests.length})</h2>
              <button
                className="btn btn-secondary btn-sm"
                onClick={() => fetchAdminRequests()}
              >
                Refresh
              </button>
            </div>

            {adminRequests.length === 0 ? (
              <div className="empty-state">
                <h3>No book requests on file!</h3>
                <p>Student requests will appear here for review.</p>
              </div>
            ) : (
              <div className="table-responsive">
                <table>
                  <thead>
                    <tr>
                      <th>ID</th>
                      <th>Student Name</th>
                      <th>Roll Number</th>
                      <th>Book Title</th>
                      <th>Request Date</th>
                      <th>Status</th>
                      <th>Actions</th>
                    </tr>
                  </thead>
                  <tbody>
                    {adminRequests.map((req) => (
                      <tr key={req.id}>
                        <td>#{req.id}</td>
                        <td><strong>{req.student_name}</strong></td>
                        <td><code>{req.student_roll_number}</code></td>
                        <td>{req.book_title}</td>
                        <td>{new Date(req.request_date).toLocaleString()}</td>
                        <td>
                          {req.status === 'Pending' && (
                            <span className="badge badge-warning">Pending</span>
                          )}
                          {req.status === 'Approved' && (
                            <span className="badge badge-success">Approved</span>
                          )}
                          {req.status === 'Rejected' && (
                            <span className="badge badge-danger">Rejected</span>
                          )}
                        </td>
                        <td>
                          {req.status === 'Pending' ? (
                            <div style={{ display: 'flex', gap: '8px' }}>
                              <button
                                className="btn btn-primary btn-sm"
                                onClick={() => handleApproveRequest(req.id)}
                              >
                                Approve
                              </button>
                              <button
                                className="btn btn-danger btn-sm"
                                onClick={() => handleRejectRequest(req.id)}
                              >
                                Reject
                              </button>
                            </div>
                          ) : (
                            <span style={{ fontSize: '0.85rem', color: 'var(--text-muted)' }}>
                              Reviewed {req.reviewed_at ? new Date(req.reviewed_at).toLocaleDateString() : ''}
                            </span>
                          )}
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            )}
          </div>
        )}

        {/* ------------------------------------------------------------------ */}
        {/* STUDENT BORROW HISTORY (Student View)                              */}
        {/* ------------------------------------------------------------------ */}
        {activeTab === 'my-history' && currentUser?.role === 'student' && (
          <div className="card">
            <div className="card-header">
              <h2 className="card-title">📖 My Borrowing History</h2>
              <span className="badge badge-info">Roll No: {currentUser.roll_number}</span>
            </div>

            {myHistory.length === 0 ? (
              <div className="empty-state">
                <h3>No borrowed books!</h3>
                <p>You currently do not have any borrowing history on file.</p>
                <button
                  className="btn btn-primary btn-sm"
                  style={{ marginTop: '12px' }}
                  onClick={() => setActiveTab('books')}
                >
                  Browse Catalogue
                </button>
              </div>
            ) : (
              <div className="table-responsive">
                <table>
                  <thead>
                    <tr>
                      <th>Loan ID</th>
                      <th>Book ID</th>
                      <th>Issue Date</th>
                      <th>Due Date</th>
                      <th>Return Date</th>
                      <th>Late Fine</th>
                      <th>Status</th>
                    </tr>
                  </thead>
                  <tbody>
                    {myHistory.map((item) => (
                      <tr key={item.id}>
                        <td>#{item.id}</td>
                        <td>Book #{item.book_id}</td>
                        <td>{item.issue_date}</td>
                        <td>
                          <strong>{item.due_date}</strong>
                        </td>
                        <td>{item.return_date || 'Currently borrowed'}</td>
                        <td>₹{item.fine}</td>
                        <td>
                          {item.is_returned ? (
                            <span className="badge badge-success">Returned</span>
                          ) : (
                            <span className="badge badge-warning">Active Loan</span>
                          )}
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            )}
          </div>
        )}

        {/* ------------------------------------------------------------------ */}
        {/* BOOK CATALOGUE (Visible to all, with Request button for Students)  */}
        {/* ------------------------------------------------------------------ */}
        {activeTab === 'books' && (
          <div className="card">
            <div className="card-header">
              <h2 className="card-title">Library Book Catalogue ({books.length})</h2>
              {currentUser?.role === 'admin' && (
                <button className="btn btn-primary btn-sm" onClick={() => setActiveTab('admin-books')}>
                  + Add New Book
                </button>
              )}
            </div>

            {books.length === 0 ? (
              <div className="empty-state">
                <h3>No books found in the library.</h3>
              </div>
            ) : (
              <div className="table-responsive">
                <table>
                  <thead>
                    <tr>
                      <th>ID</th>
                      <th>Title</th>
                      <th>Author</th>
                      <th>Category</th>
                      <th>ISBN</th>
                      <th>Available Copies</th>
                      <th>Status</th>
                      <th>Action</th>
                    </tr>
                  </thead>
                  <tbody>
                    {books.map((b) => {
                      const isPending = pendingBookIds.has(b.id);
                      return (
                        <tr key={b.id}>
                          <td>#{b.id}</td>
                          <td>
                            <strong>{b.title}</strong>
                          </td>
                          <td>{b.author}</td>
                          <td>{b.category || '—'}</td>
                          <td><code>{b.isbn || '—'}</code></td>
                          <td>
                            {b.available_copies} / {b.total_copies}
                          </td>
                          <td>
                            {b.available_copies > 0 ? (
                              <span className="badge badge-success">Available</span>
                            ) : (
                              <span className="badge badge-danger">Out of Stock</span>
                            )}
                          </td>
                          <td>
                            {/* Student View: Request Book */}
                            {currentUser?.role === 'student' && (
                              <button
                                className="btn btn-primary btn-sm"
                                disabled={b.available_copies <= 0 || isPending}
                                onClick={() => handleRequestBook(b.id)}
                                title={
                                  b.available_copies <= 0
                                    ? 'Book is out of stock'
                                    : isPending
                                    ? 'You already have a pending request for this book'
                                    : 'Submit request to borrow this book'
                                }
                              >
                                {isPending ? 'Request Pending' : 'Request Book'}
                              </button>
                            )}

                            {/* Admin View: Manual Issue */}
                            {currentUser?.role === 'admin' && (
                              <button
                                className="btn btn-secondary btn-sm"
                                disabled={b.available_copies <= 0}
                                onClick={() => {
                                  setIssueForm((prev) => ({ ...prev, book_id: b.id.toString() }));
                                  setActiveTab('issue');
                                }}
                              >
                                Issue
                              </button>
                            )}

                            {/* Visitor: Prompt login to borrow */}
                            {!currentUser && (
                              <button
                                className="btn btn-secondary btn-sm"
                                onClick={() => setActiveTab('student-login')}
                              >
                                Log in to Request
                              </button>
                            )}
                          </td>
                        </tr>
                      );
                    })}
                  </tbody>
                </table>
              </div>
            )}
          </div>
        )}

        {/* ------------------------------------------------------------------ */}
        {/* SEARCH BOOKS                                                      */}
        {/* ------------------------------------------------------------------ */}
        {activeTab === 'search' && (
          <div className="card">
            <div className="card-header">
              <h2 className="card-title">Search Book Catalogue</h2>
            </div>

            <form onSubmit={handleSearch} className="search-bar">
              <input
                type="text"
                placeholder="Search by book title, author, or category..."
                value={searchKeyword}
                onChange={(e) => setSearchKeyword(e.target.value)}
              />
              <button type="submit" className="btn btn-primary">
                Search
              </button>
            </form>

            {searchResults.length > 0 && (
              <div className="table-responsive">
                <table>
                  <thead>
                    <tr>
                      <th>ID</th>
                      <th>Title</th>
                      <th>Author</th>
                      <th>Category</th>
                      <th>Copies</th>
                      <th>Status</th>
                      {currentUser?.role === 'student' && <th>Action</th>}
                    </tr>
                  </thead>
                  <tbody>
                    {searchResults.map((b) => {
                      const isPending = pendingBookIds.has(b.id);
                      return (
                        <tr key={b.id}>
                          <td>#{b.id}</td>
                          <td><strong>{b.title}</strong></td>
                          <td>{b.author}</td>
                          <td>{b.category || '—'}</td>
                          <td>
                            {b.available_copies} / {b.total_copies}
                          </td>
                          <td>
                            {b.available_copies > 0 ? (
                              <span className="badge badge-success">Available</span>
                            ) : (
                              <span className="badge badge-danger">Out of Stock</span>
                            )}
                          </td>
                          {currentUser?.role === 'student' && (
                            <td>
                              <button
                                className="btn btn-primary btn-sm"
                                disabled={b.available_copies <= 0 || isPending}
                                onClick={() => handleRequestBook(b.id)}
                              >
                                {isPending ? 'Request Pending' : 'Request Book'}
                              </button>
                            </td>
                          )}
                        </tr>
                      );
                    })}
                  </tbody>
                </table>
              </div>
            )}
          </div>
        )}

        {/* ------------------------------------------------------------------ */}
        {/* ADMIN BOOK MANAGEMENT (Admin Only)                                 */}
        {/* ------------------------------------------------------------------ */}
        {activeTab === 'admin-books' && currentUser?.role === 'admin' && (
          <div>
            <div className="card">
              <div className="card-header">
                <h2 className="card-title">
                  {editingBookId ? `Edit Book (#${editingBookId})` : 'Add New Book to Library'}
                </h2>
                {editingBookId && (
                  <button
                    className="btn btn-secondary btn-sm"
                    onClick={() => {
                      setEditingBookId(null);
                      setBookForm({ title: '', author: '', isbn: '', category: '', total_copies: 1 });
                    }}
                  >
                    Cancel Edit
                  </button>
                )}
              </div>

              <form onSubmit={handleSaveBook}>
                <div className="form-grid">
                  <div className="form-group">
                    <label>Book Title *</label>
                    <input
                      type="text"
                      required
                      placeholder="e.g. Python Crash Course"
                      value={bookForm.title}
                      onChange={(e) => setBookForm({ ...bookForm, title: e.target.value })}
                    />
                  </div>
                  <div className="form-group">
                    <label>Author *</label>
                    <input
                      type="text"
                      required
                      placeholder="e.g. Eric Matthes"
                      value={bookForm.author}
                      onChange={(e) => setBookForm({ ...bookForm, author: e.target.value })}
                    />
                  </div>
                  <div className="form-group">
                    <label>ISBN (Optional)</label>
                    <input
                      type="text"
                      placeholder="e.g. 978-1593279288"
                      value={bookForm.isbn}
                      onChange={(e) => setBookForm({ ...bookForm, isbn: e.target.value })}
                    />
                  </div>
                  <div className="form-group">
                    <label>Category (Optional)</label>
                    <input
                      type="text"
                      placeholder="e.g. Programming"
                      value={bookForm.category}
                      onChange={(e) => setBookForm({ ...bookForm, category: e.target.value })}
                    />
                  </div>
                  <div className="form-group">
                    <label>Total Copies *</label>
                    <input
                      type="number"
                      required
                      min="1"
                      value={bookForm.total_copies}
                      onChange={(e) =>
                        setBookForm({ ...bookForm, total_copies: parseInt(e.target.value, 10) || 1 })
                      }
                    />
                  </div>
                </div>

                <button type="submit" className="btn btn-primary">
                  {editingBookId ? 'Save Changes' : 'Add Book'}
                </button>
              </form>
            </div>

            {/* Existing Books Admin Table */}
            <div className="card">
              <div className="card-header">
                <h3 className="card-title">Manage Books Catalog</h3>
              </div>
              <div className="table-responsive">
                <table>
                  <thead>
                    <tr>
                      <th>ID</th>
                      <th>Title</th>
                      <th>Author</th>
                      <th>Copies (Avail/Total)</th>
                      <th>Actions</th>
                    </tr>
                  </thead>
                  <tbody>
                    {books.map((b) => (
                      <tr key={b.id}>
                        <td>#{b.id}</td>
                        <td>{b.title}</td>
                        <td>{b.author}</td>
                        <td>{b.available_copies} / {b.total_copies}</td>
                        <td>
                          <div style={{ display: 'flex', gap: '8px' }}>
                            <button
                              className="btn btn-secondary btn-sm"
                              onClick={() => handleEditBook(b)}
                            >
                              Edit
                            </button>
                            <button
                              className="btn btn-danger btn-sm"
                              onClick={() => handleDeleteBook(b.id)}
                            >
                              Delete
                            </button>
                          </div>
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </div>
          </div>
        )}

        {/* ------------------------------------------------------------------ */}
        {/* ISSUE BOOK (Admin Only)                                           */}
        {/* ------------------------------------------------------------------ */}
        {activeTab === 'issue' && currentUser?.role === 'admin' && (
          <div className="card" style={{ maxWidth: '650px', margin: '0 auto' }}>
            <div className="card-header">
              <h2 className="card-title">Manual Book Checkout</h2>
            </div>

            <form onSubmit={handleIssueBook}>
              <div className="form-group" style={{ marginBottom: '16px' }}>
                <label>Select Student *</label>
                <select
                  required
                  value={issueForm.student_id}
                  onChange={(e) => setIssueForm({ ...issueForm, student_id: e.target.value })}
                >
                  <option value="">-- Choose Student --</option>
                  {students.map((s) => (
                    <option key={s.id} value={s.id}>
                      #{s.id} - {s.name} ({s.roll_number})
                    </option>
                  ))}
                </select>
              </div>

              <div className="form-group" style={{ marginBottom: '20px' }}>
                <label>Select Book *</label>
                <select
                  required
                  value={issueForm.book_id}
                  onChange={(e) => setIssueForm({ ...issueForm, book_id: e.target.value })}
                >
                  <option value="">-- Choose Book --</option>
                  {books.map((b) => (
                    <option
                      key={b.id}
                      value={b.id}
                      disabled={b.available_copies <= 0}
                    >
                      #{b.id} - {b.title} by {b.author} ({b.available_copies} available)
                    </option>
                  ))}
                </select>
              </div>

              <button type="submit" className="btn btn-primary" style={{ width: '100%' }}>
                Confirm Issue (14-day checkout)
              </button>
            </form>
          </div>
        )}

        {/* ------------------------------------------------------------------ */}
        {/* RETURN BOOK (Admin Only)                                          */}
        {/* ------------------------------------------------------------------ */}
        {activeTab === 'return' && currentUser?.role === 'admin' && (
          <div className="card">
            <div className="card-header">
              <h2 className="card-title">Active Borrowing Records & Returns</h2>
            </div>

            {issues.filter((i) => !i.is_returned).length === 0 ? (
              <div className="empty-state">
                <h3>No active loans!</h3>
                <p>All issued books have been returned.</p>
              </div>
            ) : (
              <div className="table-responsive">
                <table>
                  <thead>
                    <tr>
                      <th>Loan ID</th>
                      <th>Student ID</th>
                      <th>Book ID</th>
                      <th>Issue Date</th>
                      <th>Due Date</th>
                      <th>Status</th>
                      <th>Action</th>
                    </tr>
                  </thead>
                  <tbody>
                    {issues
                      .filter((i) => !i.is_returned)
                      .map((i) => {
                        const isOverdue = new Date(i.due_date) < new Date();
                        return (
                          <tr key={i.id}>
                            <td>#{i.id}</td>
                            <td>Student #{i.student_id}</td>
                            <td>Book #{i.book_id}</td>
                            <td>{i.issue_date}</td>
                            <td><strong>{i.due_date}</strong></td>
                            <td>
                              {isOverdue ? (
                                <span className="badge badge-danger">Overdue</span>
                              ) : (
                                <span className="badge badge-warning">Active</span>
                              )}
                            </td>
                            <td>
                              <button
                                className="btn btn-primary btn-sm"
                                onClick={() => handleReturnBook(i.id)}
                              >
                                Process Return
                              </button>
                            </td>
                          </tr>
                        );
                      })}
                  </tbody>
                </table>
              </div>
            )}
          </div>
        )}

        {/* ------------------------------------------------------------------ */}
        {/* REGISTERED STUDENTS LIST (Admin Only)                             */}
        {/* ------------------------------------------------------------------ */}
        {activeTab === 'students-list' && currentUser?.role === 'admin' && (
          <div className="card">
            <div className="card-header">
              <h2 className="card-title">Registered Students Directory ({students.length})</h2>
            </div>

            {students.length === 0 ? (
              <div className="empty-state">
                <p>No students registered yet.</p>
              </div>
            ) : (
              <div className="table-responsive">
                <table>
                  <thead>
                    <tr>
                      <th>ID</th>
                      <th>Name</th>
                      <th>Email</th>
                      <th>Roll Number</th>
                      <th>Phone</th>
                      <th>Registered On</th>
                    </tr>
                  </thead>
                  <tbody>
                    {students.map((s) => (
                      <tr key={s.id}>
                        <td>#{s.id}</td>
                        <td><strong>{s.name}</strong></td>
                        <td>{s.email}</td>
                        <td><code>{s.roll_number}</code></td>
                        <td>{s.phone || '—'}</td>
                        <td>{new Date(s.created_at).toLocaleDateString()}</td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            )}
          </div>
        )}
      </main>
    </div>
  );
}
