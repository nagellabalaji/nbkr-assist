from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity, get_jwt
from app import db
from app.models.user import User, Student
from app.models.library import LibraryBook, LibraryRequest
from app.services.notification_service import notify_campus_service
from datetime import datetime, timedelta

library_bp = Blueprint('library', __name__)

def get_student_context():
    """Retrieves student profile from token claims."""
    user_id = int(get_jwt_identity())
    user = User.query.get(user_id)
    if not user or user.role != 'student':
        return None
    return user.student_profile

@library_bp.route('/books', methods=['GET'])
@jwt_required()
def get_books():
    """Exposes current books catalogue. Supports text search filters."""
    search_query = request.args.get('search', '').strip().lower()
    
    query = LibraryBook.query
    if search_query:
        query = query.filter(
            (db.func.lower(LibraryBook.title).like(f"%{search_query}%")) |
            (db.func.lower(LibraryBook.author).like(f"%{search_query}%")) |
            (db.func.lower(LibraryBook.isbn).like(f"%{search_query}%"))
        )
        
    books = query.all()
    return jsonify({
        'success': True,
        'data': [b.to_dict() for b in books]
    }), 200

@library_bp.route('/books', methods=['POST'])
@jwt_required()
def add_book():
    """Adds a new book circular to the catalog. Restricted to Librarians/Admins."""
    claims = get_jwt()
    if claims.get('role') not in ['librarian', 'super_admin', 'admin']:
        return jsonify({'success': False, 'message': 'Forbidden. Librarian privileges required.', 'error': 'forbidden'}), 403

    data = request.get_json() or {}
    title = data.get('title', '').strip()
    author = data.get('author', '').strip()
    isbn = data.get('isbn', '').strip()
    quantity = data.get('quantity', 1)
    location = data.get('location', '').strip()

    if not (title and author and isbn and location):
        return jsonify({'success': False, 'message': 'Missing required fields.', 'error': 'missing_fields'}), 400

    # ISBN duplicates check
    existing = LibraryBook.query.filter_by(isbn=isbn).first()
    if existing:
        return jsonify({'success': False, 'message': 'A book with this ISBN already exists in the registry.', 'error': 'isbn_duplicate'}), 409

    try:
        qty = int(quantity)
        if qty <= 0:
            raise ValueError()
    except ValueError:
        return jsonify({'success': False, 'message': 'Quantity must be a positive integer.', 'error': 'invalid_quantity'}), 400

    try:
        new_book = LibraryBook(
            title=title,
            author=author,
            isbn=isbn,
            quantity=qty,
            available_quantity=qty,
            location=location
        )
        db.session.add(new_book)
        db.session.commit()
        return jsonify({
            'success': True,
            'message': 'Book added successfully.',
            'data': new_book.to_dict()
        }), 201
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'message': 'Database error.', 'error': str(e)}), 500

@library_bp.route('/books/<int:book_id>', methods=['PUT'])
@jwt_required()
def update_book(book_id):
    """Updates book details in catalog. Restricted to Librarians/Admins."""
    claims = get_jwt()
    if claims.get('role') not in ['librarian', 'super_admin', 'admin']:
        return jsonify({'success': False, 'message': 'Forbidden.', 'error': 'forbidden'}), 403

    book = LibraryBook.query.get(book_id)
    if not book:
        return jsonify({'success': False, 'message': 'Book not found.', 'error': 'not_found'}), 404

    data = request.get_json() or {}
    
    book.title = data.get('title', book.title).strip()
    book.author = data.get('author', book.author).strip()
    book.location = data.get('location', book.location).strip()

    new_qty = data.get('quantity')
    if new_qty is not None:
        try:
            qty = int(new_qty)
            if qty <= 0:
                raise ValueError()
            diff = qty - book.quantity
            book.quantity = qty
            book.available_quantity += diff
            if book.available_quantity < 0:
                book.available_quantity = 0
        except ValueError:
            return jsonify({'success': False, 'message': 'Quantity must be positive.', 'error': 'invalid_quantity'}), 400

    try:
        db.session.commit()
        return jsonify({
            'success': True,
            'message': 'Book updated successfully.',
            'data': book.to_dict()
        }), 200
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'message': 'Database update error.', 'error': str(e)}), 500

@library_bp.route('/books/<int:book_id>', methods=['DELETE'])
@jwt_required()
def delete_book(book_id):
    """Removes a book from catalogue. Restricted to Librarians/Admins."""
    claims = get_jwt()
    if claims.get('role') not in ['librarian', 'super_admin', 'admin']:
        return jsonify({'success': False, 'message': 'Forbidden.', 'error': 'forbidden'}), 403

    book = LibraryBook.query.get(book_id)
    if not book:
        return jsonify({'success': False, 'message': 'Book not found.', 'error': 'not_found'}), 404

    try:
        db.session.delete(book)
        db.session.commit()
        return jsonify({
            'success': True,
            'message': 'Book deleted successfully.'
        }), 200
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'message': 'Deletion failed.', 'error': str(e)}), 500

@library_bp.route('/requests', methods=['GET'])
@jwt_required()
def get_library_requests():
    """Lists student library requests. Restricts query based on student credentials."""
    user_id = int(get_jwt_identity())
    user = User.query.get(user_id)
    if not user:
        return jsonify({'success': False, 'message': 'User not found.', 'error': 'user_not_found'}), 404

    query = LibraryRequest.query

    if user.role == 'student':
        student = user.student_profile
        if not student:
            return jsonify({'success': False, 'message': 'Student profile not found.', 'error': 'profile_missing'}), 404
        query = query.filter_by(student_id=student.id)
    elif user.role in ['librarian', 'super_admin', 'admin']:
        pass
    else:
        # HOD, Faculty, etc. cannot access private student book loans
        return jsonify({'success': False, 'message': 'Forbidden. Access restricted.', 'error': 'forbidden'}), 403

    requests = query.order_by(LibraryRequest.created_at.desc()).all()
    return jsonify({
        'success': True,
        'data': [r.to_dict() for r in requests]
    }), 200

@library_bp.route('/requests', methods=['POST'])
@jwt_required()
def create_library_request():
    """Publishes a new borrow or return request for a book."""
    student = get_student_context()
    if not student:
        return jsonify({'success': False, 'message': 'Only student accounts can raise library requests.', 'error': 'forbidden'}), 403

    data = request.get_json() or {}
    book_id_val = data.get('book_id')
    request_type = data.get('request_type', 'borrow').strip().lower()

    if request_type not in ['borrow', 'return']:
        return jsonify({'success': False, 'message': 'Invalid library request type.', 'error': 'invalid_type'}), 400

    if not book_id_val:
        return jsonify({'success': False, 'message': 'Book ID is required.', 'error': 'missing_fields'}), 400

    try:
        book_id = int(book_id_val)
        book = LibraryBook.query.get(book_id)
        if not book:
            return jsonify({'success': False, 'message': 'Selected book not found.', 'error': 'book_not_found'}), 400
    except ValueError:
        return jsonify({'success': False, 'message': 'Invalid book ID.', 'error': 'book_not_found'}), 400

    # Logic: If request_type is borrow, check availability
    if request_type == 'borrow':
        if book.available_quantity <= 0:
            return jsonify({'success': False, 'message': 'This book is currently out of stock.', 'error': 'out_of_stock'}), 400

        # Check if they already have an active request for this book
        active_req = LibraryRequest.query.filter_by(
            student_id=student.id,
            book_id=book.id,
            status='submitted'
        ).first()
        if active_req:
            return jsonify({'success': False, 'message': 'You already have a pending borrow request for this book.', 'error': 'request_duplicate'}), 400

    try:
        new_req = LibraryRequest(
            student_id=student.id,
            book_id=book.id,
            request_type=request_type,
            status='submitted'
        )
        db.session.add(new_req)
        db.session.commit()

        return jsonify({
            'success': True,
            'message': 'Library request submitted successfully.',
            'data': new_req.to_dict()
        }), 201
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'message': 'Database error.', 'error': str(e)}), 500

@library_bp.route('/requests/<int:req_id>', methods=['PUT'])
@jwt_required()
def update_library_request(req_id):
    """Updates a library request status. Enforces stock changes when approved."""
    user_id = int(get_jwt_identity())
    user = User.query.get(user_id)
    if not user:
        return jsonify({'success': False, 'message': 'User not found.', 'error': 'user_not_found'}), 404

    req = LibraryRequest.query.get(req_id)
    if not req:
        return jsonify({'success': False, 'message': 'Library request not found.', 'error': 'not_found'}), 404

    data = request.get_json() or {}

    # Enforce IDOR protection: Student can only cancel their own submitted requests
    if user.role == 'student':
        student = user.student_profile
        if not student or req.student_id != student.id:
            return jsonify({'success': False, 'message': 'Forbidden. Access isolated.', 'error': 'forbidden'}), 403

        if req.status != 'submitted':
            return jsonify({'success': False, 'message': 'Request has already been processed and cannot be cancelled.', 'error': 'request_locked'}), 400

        # Students cancel requests by setting status to rejected/cancelled
        req.status = 'rejected'
        req.admin_notes = 'Cancelled by student.'

    elif user.role in ['librarian', 'super_admin', 'admin']:
        # Librarian can approve, reject or return requests
        new_status = data.get('status')
        if new_status:
            if new_status not in ['submitted', 'approved', 'rejected', 'returned']:
                return jsonify({'success': False, 'message': 'Invalid request status.', 'error': 'invalid_status'}), 400

            # Logic transitions:
            # 1. Borrow request approved: decrement available_quantity, record issued_at and due_date
            if new_status == 'approved' and req.request_type == 'borrow' and req.status != 'approved':
                if req.book.available_quantity <= 0:
                    return jsonify({'success': False, 'message': 'Cannot approve. Book is currently out of stock.', 'error': 'out_of_stock'}), 400
                req.book.available_quantity -= 1
                req.issued_at = datetime.utcnow()
                req.due_date = datetime.utcnow() + timedelta(days=14) # 14 days loan period
                db.session.add(req.book)

            # 2. Book returned: increment available_quantity, record returned_at
            if new_status == 'returned' and (req.status == 'approved' or (req.request_type == 'return' and req.status == 'submitted')):
                req.book.available_quantity += 1
                req.returned_at = datetime.utcnow()
                db.session.add(req.book)

            # 3. Borrow request rejected: keep stock, set status
            # 4. If request is borrow and goes from approved -> returned:
            req.status = new_status

        req.admin_notes = data.get('admin_notes', req.admin_notes)
    else:
        return jsonify({'success': False, 'message': 'Forbidden.', 'error': 'forbidden'}), 403

    try:
        db.session.commit()
        if user.role in ['librarian', 'super_admin', 'admin'] and req.student and req.student.user:
            notify_campus_service(req.student.user_id, "Library", req.id, req.status, req.admin_notes)
        return jsonify({
            'success': True,
            'message': 'Library request updated successfully.',
            'data': req.to_dict()
        }), 200
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'message': 'Update failed.', 'error': str(e)}), 500
