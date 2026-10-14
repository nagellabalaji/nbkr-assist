from app import db
from datetime import datetime

class LibraryBook(db.Model):
    __tablename__ = 'library_books'

    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(200), nullable=False)
    author = db.Column(db.String(150), nullable=False)
    isbn = db.Column(db.String(30), unique=True, nullable=False)
    quantity = db.Column(db.Integer, default=1)
    available_quantity = db.Column(db.Integer, default=1)
    location = db.Column(db.String(100), nullable=False)

    def to_dict(self):
        return {
            'id': self.id,
            'title': self.title,
            'author': self.author,
            'isbn': self.isbn,
            'quantity': self.quantity,
            'available_quantity': self.available_quantity,
            'location': self.location
        }

class LibraryRequest(db.Model):
    __tablename__ = 'library_requests'

    id = db.Column(db.Integer, primary_key=True)
    student_id = db.Column(db.Integer, db.ForeignKey('students.id', ondelete='CASCADE'), nullable=False)
    book_id = db.Column(db.Integer, db.ForeignKey('library_books.id', ondelete='CASCADE'), nullable=False)
    request_type = db.Column(db.Enum('borrow', 'return'), nullable=False)
    status = db.Column(db.Enum('submitted', 'approved', 'rejected', 'returned'), default='submitted')
    issued_at = db.Column(db.DateTime, default=None, nullable=True)
    due_date = db.Column(db.DateTime, default=None, nullable=True)
    returned_at = db.Column(db.DateTime, default=None, nullable=True)
    admin_notes = db.Column(db.Text, default=None)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    student = db.relationship('Student', backref=db.backref('library_requests', lazy=True, cascade="all, delete-orphan"))
    book = db.relationship('LibraryBook', backref=db.backref('requests', lazy=True))

    def to_dict(self):
        return {
            'id': self.id,
            'student_id': self.student_id,
            'student_name': self.student.user.username if self.student and self.student.user else 'Unknown',
            'roll_no': self.student.roll_no if self.student else '',
            'book_id': self.book_id,
            'book_title': self.book.title if self.book else 'Unknown',
            'book_author': self.book.author if self.book else 'Unknown',
            'request_type': self.request_type,
            'status': self.status,
            'issued_at': self.issued_at.isoformat() if self.issued_at else None,
            'due_date': self.due_date.isoformat() if self.due_date else None,
            'returned_at': self.returned_at.isoformat() if self.returned_at else None,
            'admin_notes': self.admin_notes,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }
