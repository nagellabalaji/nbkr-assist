from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity, get_jwt
from app import db
from app.models.user import User, Student, Staff
from app.models.exam import ExamNotification
from app.models.department import Department
from app.models.log_feedback import Notification
from datetime import datetime

exams_bp = Blueprint('exams', __name__)

def get_user_context():
    """Derives authenticated user and their profile record safely from JWT."""
    user_id = int(get_jwt_identity())
    user = User.query.get(user_id)
    if not user:
        return None, None
    profile = None
    if user.role == 'student':
        profile = user.student_profile
    elif user.role in ['faculty', 'hod', 'staff']:
        profile = user.staff_profile
    return user, profile

@exams_bp.route('', methods=['GET'])
@jwt_required()
def get_exams():
    """
    Exposes exam notifications list. Enforces strict department isolation
    based on the authenticated user profile.
    """
    user, profile = get_user_context()
    if not user:
        return jsonify({'success': False, 'message': 'User not found', 'error': 'user_not_found'}), 404

    # Filters
    search_query = request.args.get('search', '').strip().lower()
    upcoming_only = request.args.get('upcoming', 'false').lower() == 'true'
    date_start_str = request.args.get('date_start')
    date_end_str = request.args.get('date_end')

    query = ExamNotification.query

    # 1. Enforce strict visibility rules / department isolation
    if user.role == 'student':
        # Students only see their department's exams or general exams (where department_id is null)
        dept_id = profile.department_id if profile else None
        query = query.filter((ExamNotification.department_id == dept_id) | (ExamNotification.department_id.is_(None)))
    elif user.role in ['faculty', 'hod']:
        # Faculty & HOD only see their department's exams or general exams
        dept_id = profile.department_id if profile else None
        query = query.filter((ExamNotification.department_id == dept_id) | (ExamNotification.department_id.is_(None)))
    else:
        # Exam Cell and Admin see all exams, but can optionally filter by department
        filter_dept_id = request.args.get('department_id')
        if filter_dept_id:
            if filter_dept_id.lower() == 'null' or filter_dept_id == '':
                query = query.filter(ExamNotification.department_id.is_(None))
            else:
                try:
                    query = query.filter(ExamNotification.department_id == int(filter_dept_id))
                except ValueError:
                    pass

    # 2. Text Search (title, subject, location)
    if search_query:
        query = query.filter(
            (db.func.lower(ExamNotification.title).like(f"%{search_query}%")) |
            (db.func.lower(ExamNotification.subject).like(f"%{search_query}%")) |
            (db.func.lower(ExamNotification.location).like(f"%{search_query}%"))
        )

    # 3. Upcoming Filter
    if upcoming_only:
        query = query.filter(ExamNotification.exam_date >= datetime.utcnow())

    # 4. Date Range Filters
    if date_start_str:
        try:
            date_start = datetime.fromisoformat(date_start_str)
            query = query.filter(ExamNotification.exam_date >= date_start)
        except ValueError:
            pass
    if date_end_str:
        try:
            date_end = datetime.fromisoformat(date_end_str)
            query = query.filter(ExamNotification.exam_date <= date_end)
        except ValueError:
            pass

    # Order by date
    exams = query.order_by(ExamNotification.exam_date.asc()).all()
    
    return jsonify({
        'success': True,
        'data': [e.to_dict() for e in exams]
    }), 200

@exams_bp.route('/<int:exam_id>', methods=['GET'])
@jwt_required()
def get_exam_by_id(exam_id):
    """Fetches a single exam notification by ID. Enforces department visibility rules."""
    user, profile = get_user_context()
    if not user:
        return jsonify({'success': False, 'message': 'User not found', 'error': 'user_not_found'}), 404

    exam = ExamNotification.query.get(exam_id)
    if not exam:
        return jsonify({'success': False, 'message': 'Exam notification not found', 'error': 'not_found'}), 404

    # Department Isolation check
    if user.role in ['student', 'faculty', 'hod']:
        user_dept_id = profile.department_id if profile else None
        if exam.department_id is not None and exam.department_id != user_dept_id:
            return jsonify({'success': False, 'message': 'Forbidden. Department isolation block.', 'error': 'forbidden'}), 403

    return jsonify({
        'success': True,
        'data': exam.to_dict()
    }), 200

@exams_bp.route('', methods=['POST'])
@jwt_required()
def create_exam():
    """Publishes a new exam notification. Restricted to Exam Cell and Admin roles."""
    claims = get_jwt()
    if claims.get('role') not in ['exam_cell', 'admin', 'super_admin']:
        return jsonify({'success': False, 'message': 'Forbidden. Exam Cell permissions required.', 'error': 'forbidden'}), 403

    data = request.get_json() or {}
    title = data.get('title', '').strip()
    subject = data.get('subject', '').strip()
    exam_date_str = data.get('exam_date')
    duration_mins = data.get('duration_mins')
    location = data.get('location', '').strip()
    department_id = data.get('department_id')

    # Validations
    if not (title and subject and exam_date_str and duration_mins and location):
        return jsonify({'success': False, 'message': 'Missing required fields.', 'error': 'missing_fields'}), 400

    try:
        exam_date = datetime.fromisoformat(exam_date_str.replace('Z', ''))
    except ValueError:
        return jsonify({'success': False, 'message': 'Invalid date format (ISO expected).', 'error': 'invalid_date'}), 400

    try:
        duration_mins = int(duration_mins)
        if duration_mins <= 0:
            raise ValueError()
    except ValueError:
        return jsonify({'success': False, 'message': 'Duration must be a positive integer.', 'error': 'invalid_duration'}), 400

    # Validate department if supplied
    final_dept_id = None
    if department_id is not None and department_id != '' and str(department_id).lower() != 'all':
        try:
            final_dept_id = int(department_id)
            dept = Department.query.get(final_dept_id)
            if not dept or not dept.is_active:
                return jsonify({'success': False, 'message': 'Active department not found for the given ID.', 'error': 'invalid_department'}), 400
        except ValueError:
            return jsonify({'success': False, 'message': 'Invalid department ID value.', 'error': 'invalid_department'}), 400

    try:
        # Create exam record
        new_exam = ExamNotification(
            title=title,
            subject=subject,
            exam_date=exam_date,
            duration_mins=duration_mins,
            location=location,
            department_id=final_dept_id
        )
        db.session.add(new_exam)
        db.session.commit()

        # Send notifications to students
        # Fetch target student list
        student_query = Student.query
        if final_dept_id:
            student_query = student_query.filter_by(department_id=final_dept_id)
        students = student_query.all()

        for s in students:
            # Create notifications
            db.session.add(Notification(
                user_id=s.user_id,
                title=f"New Exam Scheduled: {subject}",
                message=f"Exam '{title}' has been scheduled for {subject} on {exam_date.strftime('%d-%m-%Y %I:%M %p')}. Location: {location}.",
                type="exam"
            ))
        db.session.commit()

        return jsonify({
            'success': True,
            'message': 'Exam notification published successfully.',
            'data': new_exam.to_dict()
        }), 201

    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'message': 'Database execution failed.', 'error': str(e)}), 500

@exams_bp.route('/<int:exam_id>', methods=['PUT'])
@jwt_required()
def update_exam(exam_id):
    """Updates an existing exam notification with change audit logs."""
    claims = get_jwt()
    if claims.get('role') not in ['exam_cell', 'admin', 'super_admin']:
        return jsonify({'success': False, 'message': 'Forbidden. Exam Cell permissions required.', 'error': 'forbidden'}), 403

    exam = ExamNotification.query.get(exam_id)
    if not exam:
        return jsonify({'success': False, 'message': 'Exam notification not found.', 'error': 'not_found'}), 404

    data = request.get_json() or {}
    title = data.get('title', '').strip()
    subject = data.get('subject', '').strip()
    exam_date_str = data.get('exam_date')
    duration_mins = data.get('duration_mins')
    location = data.get('location', '').strip()
    department_id = data.get('department_id')

    # Validations
    if not (title and subject and exam_date_str and duration_mins and location):
        return jsonify({'success': False, 'message': 'Missing required fields.', 'error': 'missing_fields'}), 400

    try:
        exam_date = datetime.fromisoformat(exam_date_str.replace('Z', ''))
    except ValueError:
        return jsonify({'success': False, 'message': 'Invalid date format (ISO expected).', 'error': 'invalid_date'}), 400

    try:
        duration_mins = int(duration_mins)
        if duration_mins <= 0:
            raise ValueError()
    except ValueError:
        return jsonify({'success': False, 'message': 'Duration must be a positive integer.', 'error': 'invalid_duration'}), 400

    # Validate department if supplied
    final_dept_id = None
    if department_id is not None and department_id != '' and str(department_id).lower() != 'all':
        try:
            final_dept_id = int(department_id)
            dept = Department.query.get(final_dept_id)
            if not dept or not dept.is_active:
                return jsonify({'success': False, 'message': 'Active department not found for the given ID.', 'error': 'invalid_department'}), 400
        except ValueError:
            return jsonify({'success': False, 'message': 'Invalid department ID value.', 'error': 'invalid_department'}), 400

    # Detect meaningful changes to trigger notifications
    date_changed = exam.exam_date != exam_date
    loc_changed = exam.location != location
    sub_changed = exam.subject != subject
    dur_changed = exam.duration_mins != duration_mins

    try:
        # Update record
        exam.title = title
        exam.subject = subject
        exam.exam_date = exam_date
        exam.duration_mins = duration_mins
        exam.location = location
        exam.department_id = final_dept_id
        db.session.commit()

        # If meaningful changes are detected, notify target students
        if date_changed or loc_changed or sub_changed or dur_changed:
            student_query = Student.query
            if final_dept_id:
                student_query = student_query.filter_by(department_id=final_dept_id)
            students = student_query.all()

            for s in students:
                db.session.add(Notification(
                    user_id=s.user_id,
                    title=f"Exam Schedule Updated: {subject}",
                    message=f"The schedule for exam '{title}' ({subject}) has changed. New Details: Date: {exam_date.strftime('%d-%m-%Y %I:%M %p')}, Location: {location}, Duration: {duration_mins} mins.",
                    type="exam"
                ))
            db.session.commit()

        return jsonify({
            'success': True,
            'message': 'Exam notification updated successfully.',
            'data': exam.to_dict()
        }), 200

    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'message': 'Update failed.', 'error': str(e)}), 500

@exams_bp.route('/<int:exam_id>', methods=['DELETE'])
@jwt_required()
def delete_exam(exam_id):
    """Deletes an exam notification from the database."""
    claims = get_jwt()
    if claims.get('role') not in ['exam_cell', 'admin', 'super_admin']:
        return jsonify({'success': False, 'message': 'Forbidden. Exam Cell permissions required.', 'error': 'forbidden'}), 403

    exam = ExamNotification.query.get(exam_id)
    if not exam:
        return jsonify({'success': False, 'message': 'Exam notification not found.', 'error': 'not_found'}), 404

    try:
        db.session.delete(exam)
        db.session.commit()
        return jsonify({
            'success': True,
            'message': 'Exam notification deleted successfully.'
        }), 200
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'message': 'Deletion failed.', 'error': str(e)}), 500
