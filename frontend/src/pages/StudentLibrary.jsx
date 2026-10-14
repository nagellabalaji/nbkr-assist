import React, { useEffect, useState } from 'react';
import { Book, Search, PlusCircle, AlertCircle, BookOpen, User, MapPin } from 'lucide-react';
import { Loader } from '../components/Common/Loader';
import { Toast } from '../components/Common/Toast';
import './StudentLibrary.css';

export const StudentLibrary = () => {
  const [books, setBooks] = useState([]);
  const [requests, setRequests] = useState([]);
  const [loading, setLoading] = useState(true);
  const [submitting, setSubmitting] = useState(false);
  const [toast, setToast] = useState({ show: false, message: '', type: 'success' });

  // Filter and Search states
  const [search, setSearch] = useState('');

  const fetchData = async () => {
    try {
      const token = localStorage.getItem('token');
      
      // Fetch books
      const booksRes = await fetch(`/api/library/books?search=${search}`, {
        headers: { 'Authorization': `Bearer ${token}` }
      });
      const booksJson = await booksRes.json();
      if (booksJson.success) {
        setBooks(booksJson.data);
      }

      // Fetch requests
      const reqRes = await fetch('/api/library/requests', {
        headers: { 'Authorization': `Bearer ${token}` }
      });
      const reqJson = await reqRes.json();
      if (reqJson.success) {
        setRequests(reqJson.data);
      }
    } catch (err) {
      setToast({ show: true, message: 'Failed to access library register.', type: 'error' });
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    const delayDebounce = setTimeout(() => {
      fetchData();
    }, 300);
    return () => clearTimeout(delayDebounce);
  }, [search]);

  const handleBorrowRequest = async (bookId) => {
    setSubmitting(true);
    try {
      const token = localStorage.getItem('token');
      const res = await fetch('/api/library/requests', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${token}`
        },
        body: JSON.stringify({
          book_id: bookId,
          request_type: 'borrow'
        })
      });
      const json = await res.json();
      if (json.success) {
        setToast({ show: true, message: 'Borrow request submitted successfully! Wait for Librarian approval.', type: 'success' });
        fetchData();
      } else {
        setToast({ show: true, message: json.message || 'Request failed.', type: 'error' });
      }
    } catch (err) {
      setToast({ show: true, message: 'Server communication error.', type: 'error' });
    } finally {
      setSubmitting(false);
    }
  };

  const handleReturnRequest = async (bookId) => {
    setSubmitting(true);
    try {
      const token = localStorage.getItem('token');
      const res = await fetch('/api/library/requests', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${token}`
        },
        body: JSON.stringify({
          book_id: bookId,
          request_type: 'return'
        })
      });
      const json = await res.json();
      if (json.success) {
        setToast({ show: true, message: 'Return request submitted successfully!', type: 'success' });
        fetchData();
      } else {
        setToast({ show: true, message: json.message || 'Request failed.', type: 'error' });
      }
    } catch (err) {
      setToast({ show: true, message: 'Server communication error.', type: 'error' });
    } finally {
      setSubmitting(false);
    }
  };

  const getStatusBadgeClass = (status) => {
    switch (status?.toLowerCase()) {
      case 'approved': return 'status-approved';
      case 'returned': return 'status-returned';
      case 'rejected': return 'status-rejected';
      default: return 'status-submitted';
    }
  };

  return (
    <div className="student-library-container animate-fade-in">
      <div className="library-header">
        <h1>Library & Books Catalogue</h1>
        <p>Browse active library collections, check availability, and request book loans.</p>
      </div>

      <div className="library-layout-grid">
        {/* Left: Catalogue list */}
        <div className="catalogue-section">
          <div className="search-box-wrapper glass-card">
            <Search size={18} className="search-icon" />
            <input 
              type="text" 
              placeholder="Search books by title, author, or ISBN..." 
              value={search}
              onChange={(e) => setSearch(e.target.value)}
              className="search-input"
            />
          </div>

          <div className="books-grid">
            {books.length === 0 ? (
              <div className="empty-books glass-card">
                <Book size={36} />
                <p>No books matched your search query.</p>
              </div>
            ) : (
              books.map(b => {
                const isOutOfStock = b.available_quantity <= 0;
                
                // Check if there is an active borrow request approved for this book
                const hasBorrowed = requests.some(r => r.book_id === b.id && r.status === 'approved' && r.request_type === 'borrow');
                const hasPendingBorrow = requests.some(r => r.book_id === b.id && r.status === 'submitted' && r.request_type === 'borrow');
                const hasPendingReturn = requests.some(r => r.book_id === b.id && r.status === 'submitted' && r.request_type === 'return');

                return (
                  <div key={b.id} className="book-card glass-card">
                    <div className="book-card-header">
                      <BookOpen size={20} className="book-icon" />
                      <span className="book-isbn">ISBN: {b.isbn}</span>
                    </div>

                    <div className="book-details">
                      <h3 className="book-title">{b.title}</h3>
                      <span className="book-author"><User size={12} /> {b.author}</span>
                      <span className="book-location"><MapPin size={12} /> {b.location}</span>
                    </div>

                    <div className="book-availability-row">
                      <span className="stock-label">Available:</span>
                      <span className={`stock-value ${isOutOfStock ? 'red' : 'green'}`}>
                        {b.available_quantity} / {b.quantity} copies
                      </span>
                    </div>

                    <div className="book-card-actions">
                      {hasPendingReturn ? (
                        <button className="btn btn-outline" disabled>
                          Return Under Review
                        </button>
                      ) : hasBorrowed ? (
                        <button className="btn btn-primary return-btn" onClick={() => handleReturnRequest(b.id)} disabled={submitting}>
                          Request to Return Book
                        </button>
                      ) : hasPendingBorrow ? (
                        <button className="btn btn-outline" disabled>
                          Borrow Under Review
                        </button>
                      ) : (
                        <button 
                          className="btn btn-primary borrow-btn" 
                          onClick={() => handleBorrowRequest(b.id)} 
                          disabled={submitting || isOutOfStock}
                        >
                          {isOutOfStock ? 'Out of Stock' : 'Request to Borrow'}
                        </button>
                      )}
                    </div>
                  </div>
                );
              })
            )}
          </div>
        </div>

        {/* Right: Book loan history list */}
        <div className="loans-section glass-card">
          <h3>Your Book Loans & History</h3>
          {requests.length === 0 ? (
            <div className="empty-requests">
              <AlertCircle size={36} />
              <p>No borrow/loan transaction records found.</p>
            </div>
          ) : (
            <div className="loans-list">
              {requests.map(r => {
                const dueDateStr = r.due_date ? new Date(r.due_date).toLocaleDateString() : 'N/A';
                return (
                  <div key={r.id} className="loan-item-card glass-card">
                    <div className="loan-item-header">
                      <span className="loan-type">{r.request_type.toUpperCase()}</span>
                      <span className={`status-pill ${getStatusBadgeClass(r.status)}`}>
                        {r.status}
                      </span>
                    </div>
                    <h4 className="loan-book-title">{r.book_title}</h4>
                    <span className="loan-book-author">by {r.book_author}</span>
                    
                    <div className="loan-dates-info">
                      {r.issued_at && (
                        <span>Issued: <strong>{new Date(r.issued_at).toLocaleDateString()}</strong></span>
                      )}
                      {r.due_date && r.status === 'approved' && (
                        <span className="due-date">Due: <strong>{dueDateStr}</strong></span>
                      )}
                      {r.returned_at && (
                        <span>Returned: <strong>{new Date(r.returned_at).toLocaleDateString()}</strong></span>
                      )}
                    </div>
                  </div>
                );
              })}
            </div>
          )}
        </div>
      </div>

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
export default StudentLibrary;
