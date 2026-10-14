import React, { useEffect, useState } from 'react';
import { Search, PlusCircle, Book, Edit2, Trash2, Award, FileText, CheckCircle, Clock, AlertCircle } from 'lucide-react';
import { Loader } from '../components/Common/Loader';
import { Toast } from '../components/Common/Toast';
import './LibrarianDashboard.css';

export const LibrarianDashboard = () => {
  const [books, setBooks] = useState([]);
  const [requests, setRequests] = useState([]);
  const [loading, setLoading] = useState(true);
  const [submitting, setSubmitting] = useState(false);
  const [toast, setToast] = useState({ show: false, message: '', type: 'success' });

  // View state: 'requests' or 'books'
  const [viewMode, setViewMode] = useState('requests'); // 'requests' | 'books'

  // Filter and Search states
  const [searchRequests, setSearchRequests] = useState('');
  const [searchBooks, setSearchBooks] = useState('');
  const [statusFilter, setStatusFilter] = useState('all');

  // Book Form states
  const [showBookModal, setShowBookModal] = useState(false);
  const [editingBookId, setEditingBookId] = useState(null);
  const [bookTitle, setBookTitle] = useState('');
  const [bookAuthor, setBookAuthor] = useState('');
  const [bookIsbn, setBookIsbn] = useState('');
  const [bookQty, setBookQty] = useState(1);
  const [bookLocation, setBookLocation] = useState('');

  // Request Manage states
  const [editingReqId, setEditingReqId] = useState(null);
  const [editStatus, setEditStatus] = useState('');
  const [editNotes, setEditNotes] = useState('');
  const [savingReq, setSavingReq] = useState(false);

  const fetchData = async () => {
    try {
      const token = localStorage.getItem('token');
      
      // Fetch books list
      const booksRes = await fetch('/api/library/books', {
        headers: { 'Authorization': `Bearer ${token}` }
      });
      const booksJson = await booksRes.json();
      if (booksJson.success) {
        setBooks(booksJson.data);
      }

      // Fetch requests list
      const reqRes = await fetch('/api/library/requests', {
        headers: { 'Authorization': `Bearer ${token}` }
      });
      const reqJson = await reqRes.json();
      if (reqJson.success) {
        setRequests(reqJson.data);
      }
    } catch (err) {
      setToast({ show: true, message: 'Failed to access library records.', type: 'error' });
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchData();
  }, []);

  const handleOpenBookModal = (book = null) => {
    if (book) {
      setEditingBookId(book.id);
      setBookTitle(book.title);
      setBookAuthor(book.author);
      setBookIsbn(book.isbn);
      setBookQty(book.quantity);
      setBookLocation(book.location);
    } else {
      setEditingBookId(null);
      setBookTitle('');
      setBookAuthor('');
      setBookIsbn('');
      setBookQty(1);
      setBookLocation('');
    }
    setShowBookModal(true);
  };

  const handleBookSubmit = async (e) => {
    e.preventDefault();
    if (!bookTitle || !bookAuthor || !bookIsbn || !bookLocation) {
      setToast({ show: true, message: 'Please input all required book fields.', type: 'error' });
      return;
    }

    setSubmitting(true);
    try {
      const token = localStorage.getItem('token');
      const payload = {
        title: bookTitle,
        author: bookAuthor,
        isbn: bookIsbn,
        quantity: parseInt(bookQty),
        location: bookLocation
      };

      const method = editingBookId ? 'PUT' : 'POST';
      const endpoint = editingBookId ? `/api/library/books/${editingBookId}` : '/api/library/books';

      const res = await fetch(endpoint, {
        method,
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${token}`
        },
        body: JSON.stringify(payload)
      });
      const json = await res.json();
      if (json.success) {
        setToast({ show: true, message: editingBookId ? 'Book details updated successfully!' : 'Book added to catalog successfully!', type: 'success' });
        setShowBookModal(false);
        fetchData();
      } else {
        setToast({ show: true, message: json.message || 'Operation failed.', type: 'error' });
      }
    } catch (err) {
      setToast({ show: true, message: 'Server communication error.', type: 'error' });
    } finally {
      setSubmitting(false);
    }
  };

  const handleDeleteBook = async (bookId) => {
    if (!window.confirm("Are you sure you want to permanently remove this book from the catalog?")) return;

    try {
      const token = localStorage.getItem('token');
      const res = await fetch(`/api/library/books/${bookId}`, {
        method: 'DELETE',
        headers: { 'Authorization': `Bearer ${token}` }
      });
      const json = await res.json();
      if (json.success) {
        setToast({ show: true, message: 'Book deleted from catalog successfully.', type: 'success' });
        fetchData();
      } else {
        setToast({ show: true, message: json.message || 'Deletion failed.', type: 'error' });
      }
    } catch (err) {
      setToast({ show: true, message: 'Server error.', type: 'error' });
    }
  };

  const handleOpenManageReq = (req) => {
    setEditingReqId(req.id);
    setEditStatus(req.status);
    setEditNotes(req.admin_notes || '');
  };

  const handleSaveReqUpdate = async (e) => {
    e.preventDefault();
    setSavingReq(true);
    try {
      const token = localStorage.getItem('token');
      const res = await fetch(`/api/library/requests/${editingReqId}`, {
        method: 'PUT',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${token}`
        },
        body: JSON.stringify({
          status: editStatus,
          admin_notes: editNotes
        })
      });
      const json = await res.json();
      if (json.success) {
        setToast({ show: true, message: 'Transaction status updated successfully!', type: 'success' });
        setEditingReqId(null);
        fetchData();
      } else {
        setToast({ show: true, message: json.message || 'Update failed.', type: 'error' });
      }
    } catch (err) {
      setToast({ show: true, message: 'Server communication error.', type: 'error' });
    } finally {
      setSavingReq(false);
    }
  };

  // Metrics
  const getPendingCount = () => requests.filter(r => r.status === 'submitted').length;
  const getIssuedCount = () => requests.filter(r => r.status === 'approved' && r.request_type === 'borrow').length;
  const getTotalBooksCount = () => books.reduce((acc, curr) => acc + curr.quantity, 0);

  // Filters mapping
  const filteredRequests = requests.filter(r => {
    const matchSearch = r.student_name.toLowerCase().includes(searchRequests.toLowerCase()) ||
                        r.roll_no.toLowerCase().includes(searchRequests.toLowerCase()) ||
                        r.book_title.toLowerCase().includes(searchRequests.toLowerCase());
    const matchStatus = statusFilter === 'all' || r.status === statusFilter;
    return matchSearch && matchStatus;
  });

  const filteredBooks = books.filter(b => {
    return b.title.toLowerCase().includes(searchBooks.toLowerCase()) ||
           b.author.toLowerCase().includes(searchBooks.toLowerCase()) ||
           b.isbn.toLowerCase().includes(searchBooks.toLowerCase());
  });

  const getStatusBadgeClass = (status) => {
    switch (status?.toLowerCase()) {
      case 'approved': return 'status-approved';
      case 'returned': return 'status-returned';
      case 'rejected': return 'status-rejected';
      default: return 'status-submitted';
    }
  };

  if (loading) return <Loader message="Accessing Library registers..." />;

  return (
    <div className="librarian-dashboard-container animate-fade-in">
      <div className="dashboard-header">
        <div>
          <h1>Library Management Workspace</h1>
          <p>Schedule issues, manage returns, and catalog new books circulars.</p>
        </div>
        
        <div className="header-actions">
          <button 
            className={`btn btn-outline ${viewMode === 'requests' ? 'active' : ''}`}
            onClick={() => setViewMode('requests')}
          >
            Manage Transactions
          </button>
          <button 
            className={`btn btn-outline ${viewMode === 'books' ? 'active' : ''}`}
            onClick={() => setViewMode('books')}
          >
            Manage Catalog
          </button>
          {viewMode === 'books' && (
            <button className="btn btn-primary add-book-btn" onClick={() => handleOpenBookModal()}>
              <PlusCircle size={18} />
              <span>Catalog Book</span>
            </button>
          )}
        </div>
      </div>

      {/* Metrics Row */}
      <div className="admin-metrics-row">
        <div className="metric-card glass-card">
          <Book className="m-icon" />
          <div className="m-val">{getTotalBooksCount()}</div>
          <div className="m-lbl">Total Catalog Books</div>
        </div>
        <div className="metric-card glass-card warning">
          <Clock className="m-icon" />
          <div className="m-val">{getPendingCount()}</div>
          <div className="m-lbl">Pending Borrow/Return</div>
        </div>
        <div className="metric-card glass-card success">
          <CheckCircle className="m-icon" />
          <div className="m-val">{getIssuedCount()}</div>
          <div className="m-lbl">Books Currently Borrowed</div>
        </div>
      </div>

      {viewMode === 'requests' ? (
        /* Transactions list view */
        <div className="transactions-workspace">
          <div className="roster-controls-card glass-card">
            <div className="search-box-wrapper">
              <Search size={18} className="search-icon" />
              <input 
                type="text" 
                placeholder="Search transaction by student name, roll number, or book title..." 
                value={searchRequests}
                onChange={(e) => setSearchRequests(e.target.value)}
                className="search-input"
              />
            </div>

            <div className="filter-item">
              <select value={statusFilter} onChange={(e) => setStatusFilter(e.target.value)} className="status-select-filter">
                <option value="all">All Request Statuses</option>
                <option value="submitted">Submitted</option>
                <option value="approved">Approved / Issued</option>
                <option value="returned">Returned</option>
                <option value="rejected">Rejected</option>
              </select>
            </div>
          </div>

          <div className="table-responsive glass-card">
            {filteredRequests.length === 0 ? (
              <div className="empty-roster">No library request logs found mapping your search filters.</div>
            ) : (
              <table className="roster-table">
                <thead>
                  <tr>
                    <th>ID</th>
                    <th>Student Details</th>
                    <th>Book Details</th>
                    <th>Request Type</th>
                    <th>Status</th>
                    <th>Dates</th>
                    <th className="center-text">Actions</th>
                  </tr>
                </thead>
                <tbody>
                  {filteredRequests.map(r => (
                    <tr key={r.id}>
                      <td className="monospace-cell">LIB-{String(r.id).padStart(4, '0')}</td>
                      <td>
                        <div className="student-details-meta">
                          <strong>{r.student_name}</strong>
                          <span>Roll: {r.roll_no}</span>
                        </div>
                      </td>
                      <td>
                        <div className="book-details-meta">
                          <strong>{r.book_title}</strong>
                          <span>by {r.book_author}</span>
                        </div>
                      </td>
                      <td><span className="type-badge">{r.request_type.toUpperCase()}</span></td>
                      <td>
                        <span className={`status-pill ${getStatusBadgeClass(r.status)}`}>
                          {r.status}
                        </span>
                      </td>
                      <td>
                        <div className="dates-meta">
                          {r.issued_at && <span>Issued: {new Date(r.issued_at).toLocaleDateString()}</span>}
                          {r.due_date && r.status === 'approved' && <span className="red">Due: {new Date(r.due_date).toLocaleDateString()}</span>}
                          {r.returned_at && <span>Returned: {new Date(r.returned_at).toLocaleDateString()}</span>}
                        </div>
                      </td>
                      <td className="actions-cell">
                        <button className="btn btn-outline edit-action-btn" onClick={() => handleOpenManageReq(r)}>
                          Manage
                        </button>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            )}
          </div>
        </div>
      ) : (
        /* Books Catalog view */
        <div className="catalog-workspace">
          <div className="roster-controls-card glass-card">
            <div className="search-box-wrapper">
              <Search size={18} className="search-icon" />
              <input 
                type="text" 
                placeholder="Search catalog books by title, author, or ISBN..." 
                value={searchBooks}
                onChange={(e) => setSearchBooks(e.target.value)}
                className="search-input"
              />
            </div>
          </div>

          <div className="table-responsive glass-card">
            {filteredBooks.length === 0 ? (
              <div className="empty-roster">No books found in the catalog mapping your search.</div>
            ) : (
              <table className="roster-table">
                <thead>
                  <tr>
                    <th>ISBN</th>
                    <th>Book Title</th>
                    <th>Author</th>
                    <th>Location</th>
                    <th>Stock (Avail/Total)</th>
                    <th className="center-text">Actions</th>
                  </tr>
                </thead>
                <tbody>
                  {filteredBooks.map(b => (
                    <tr key={b.id}>
                      <td className="monospace-cell">{b.isbn}</td>
                      <td><strong>{b.title}</strong></td>
                      <td>{b.author}</td>
                      <td>{b.location}</td>
                      <td>{b.available_quantity} / {b.quantity} copies</td>
                      <td className="actions-cell">
                        <button className="icon-btn edit-btn" onClick={() => handleOpenBookModal(b)}>
                          <Edit2 size={16} />
                        </button>
                        <button className="icon-btn delete-btn" onClick={() => handleDeleteBook(b.id)}>
                          <Trash2 size={16} />
                        </button>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            )}
          </div>
        </div>
      )}

      {/* Book Form Modal */}
      {showBookModal && (
        <div className="modal-backdrop">
          <div className="modal-content glass-card animate-zoom-in">
            <h3>{editingBookId ? 'Edit Catalogue Book' : 'Catalog New Book'}</h3>
            <hr />
            <form onSubmit={handleBookSubmit} className="book-form">
              <div className="form-group">
                <label>Book Title</label>
                <input 
                  type="text" 
                  value={bookTitle} 
                  onChange={(e) => setBookTitle(e.target.value)} 
                  placeholder="e.g. Introduction to Algorithms" 
                  required
                />
              </div>

              <div className="form-group">
                <label>Author</label>
                <input 
                  type="text" 
                  value={bookAuthor} 
                  onChange={(e) => setBookAuthor(e.target.value)} 
                  placeholder="e.g. Thomas H. Cormen" 
                  required
                />
              </div>

              <div className="form-group">
                <label>ISBN Number</label>
                <input 
                  type="text" 
                  value={bookIsbn} 
                  onChange={(e) => setBookIsbn(e.target.value)} 
                  placeholder="e.g. 9780262033848" 
                  required
                  disabled={!!editingBookId}
                />
              </div>

              <div className="form-row-grid">
                <div className="form-group">
                  <label>Total Quantity</label>
                  <input 
                    type="number" 
                    value={bookQty} 
                    onChange={(e) => setBookQty(e.target.value)} 
                    min="1" 
                    required
                  />
                </div>

                <div className="form-group">
                  <label>Library Location / Rack</label>
                  <input 
                    type="text" 
                    value={bookLocation} 
                    onChange={(e) => setBookLocation(e.target.value)} 
                    placeholder="e.g. Rack A-4" 
                    required
                  />
                </div>
              </div>

              <div className="modal-actions-footer">
                <button type="button" className="btn btn-outline" onClick={() => setShowBookModal(false)}>
                  Cancel
                </button>
                <button type="submit" className="btn btn-primary" disabled={submitting}>
                  {submitting ? 'Cataloging...' : editingBookId ? 'Save Changes' : 'Catalog Book'}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}

      {/* Request Update Modal */}
      {editingReqId && (
        <div className="modal-backdrop">
          <div className="modal-content glass-card animate-zoom-in">
            <h3>Manage Transaction Request LIB-{String(editingReqId).padStart(4, '0')}</h3>
            <hr />
            <form onSubmit={handleSaveReqUpdate} className="admin-update-form">
              <div className="form-group">
                <label>Update Status</label>
                <select value={editStatus} onChange={(e) => setEditStatus(e.target.value)}>
                  <option value="submitted">Submitted</option>
                  <option value="approved">Approved (Issue Book)</option>
                  <option value="returned">Returned (Record Return)</option>
                  <option value="rejected">Rejected</option>
                </select>
              </div>

              <div className="form-group">
                <label>Librarian Notes</label>
                <textarea 
                  value={editNotes}
                  onChange={(e) => setEditNotes(e.target.value)}
                  placeholder="Specify issue condition, return remarks, or rejection grounds..."
                  rows={4}
                />
              </div>

              <div className="modal-actions-footer">
                <button type="button" className="btn btn-outline" onClick={() => setEditingReqId(null)}>
                  Cancel
                </button>
                <button type="submit" className="btn btn-primary" disabled={savingReq}>
                  {savingReq ? 'Processing...' : 'Save Changes'}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}

      {toast.show && (
        <Toast 
          message={toast.message} 
          type={toast.type} 
          onClose={() => setToast({ ...toast, show: false })} 
        />
      )}
    </div>
  );
};
export default LibrarianDashboard;
