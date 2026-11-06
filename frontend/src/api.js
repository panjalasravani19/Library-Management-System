/**
 * API Service for communicating with the FastAPI backend.
 * Base URL defaults to http://127.0.0.1:8000.
 * Handles JWT Bearer token authentication for both Administrator and Student sessions.
 */

const API_BASE_URL =
  import.meta.env.VITE_API_BASE_URL || 'http://127.0.0.1:8000';

// Store token in memory and synchronize with localStorage
let authToken =
  localStorage.getItem('library_token') ||
  localStorage.getItem('library_admin_token') ||
  null;

/**
 * Generic fetch wrapper that handles JSON headers, serialization,
 * adds Authorization header when present, and formats error messages.
 */
async function request(endpoint, options = {}) {
  const url = `${API_BASE_URL}${endpoint}`;
  const headers = {
    'Content-Type': 'application/json',
    ...(authToken ? { Authorization: `Bearer ${authToken}` } : {}),
    ...(options.headers || {}),
  };

  const config = {
    ...options,
    headers,
  };

  try {
    const response = await fetch(url, config);
    const data = await response.json().catch(() => null);

    if (!response.ok) {
      const errorMessage = data?.detail || `Server error (${response.status})`;
      throw new Error(errorMessage);
    }

    return data;
  } catch (error) {
    if (error.name === 'TypeError' && error.message.includes('fetch')) {
      throw new Error(
  'Unable to connect to the backend server. Please check your internet connection or try again later.'
);
    }
    throw error;
  }
}

export const api = {
  // Token Management
  setAuthToken: (token) => {
    authToken = token;
    if (token) {
      localStorage.setItem('library_token', token);
    } else {
      localStorage.removeItem('library_token');
      localStorage.removeItem('library_admin_token');
    }
  },
  getAuthToken: () => authToken,

  // General
  getHealth: () => request('/health'),

  // Admin Authentication
  adminLogin: (credentials) =>
    request('/admin/login', {
      method: 'POST',
      body: JSON.stringify(credentials),
    }),

  // Students Authentication & Management
  registerStudent: (studentData) =>
    request('/students/register', {
      method: 'POST',
      body: JSON.stringify(studentData),
    }),

  loginStudent: (credentials) =>
    request('/students/login', {
      method: 'POST',
      body: JSON.stringify(credentials),
    }),

  getStudents: () => request('/students'),

  getStudent: (id) => request(`/students/${id}`),

  getStudentIssues: (studentId) => request(`/students/${studentId}/issues`),

  // Books
  getBooks: () => request('/books'),

  getBook: (id) => request(`/books/${id}`),

  addBook: (bookData) =>
    request('/books', {
      method: 'POST',
      body: JSON.stringify(bookData),
    }),

  updateBook: (id, bookData) =>
    request(`/books/${id}`, {
      method: 'PUT',
      body: JSON.stringify(bookData),
    }),

  deleteBook: (id) =>
    request(`/books/${id}`, {
      method: 'DELETE',
    }),

  searchBooks: (keyword) =>
    request(`/books/search/${encodeURIComponent(keyword)}`),

  // Book Issue & Return (Admin Protected)
  issueBook: (issueData) =>
    request('/issues', {
      method: 'POST',
      body: JSON.stringify(issueData),
    }),

  getIssues: () => request('/issues'),

  returnBook: (issueId) =>
    request(`/issues/${issueId}/return`, {
      method: 'PUT',
    }),

  // Book Requests (Student & Admin)
  requestBook: (bookId) =>
    request('/book-requests', {
      method: 'POST',
      body: JSON.stringify({ book_id: bookId }),
    }),

  getMyBookRequests: () => request('/book-requests/my'),

  getAdminBookRequests: () => request('/admin/book-requests'),

  approveBookRequest: (requestId) =>
    request(`/admin/book-requests/${requestId}/approve`, {
      method: 'PUT',
    }),

  rejectBookRequest: (requestId, remarks) =>
    request(`/admin/book-requests/${requestId}/reject`, {
      method: 'PUT',
      body: JSON.stringify({ remarks: remarks || null }),
    }),
};
