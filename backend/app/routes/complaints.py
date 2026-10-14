from flask import Blueprint, request, jsonify, current_app, send_from_directory
from flask_jwt_extended import jwt_required, get_jwt_identity, get_jwt, decode_token
from app import db
from app.models.user import User, Student, Staff, Admin
from app.models.complaint import ComplaintCategory, Complaint, ComplaintAssignment, ComplaintHistory
from app.models.log_feedback import Notification, Feedback
from app.utils.file_handler import save_uploaded_file, delete_file
from app.services.ai_service import classify_complaint
from app.services.notification_service import (
    create_notification, notify_status_change, notify_assignment, notify_priority_change
)
from datetime import datetime, timedelta
import os
from app.services.email_service import EmailService

complaints_bp = Blueprint('complaints', __name__)
grievances_bp = Blueprint('grievances', __name__)

# Centralized categories and subcategories schema
CATEGORIES_SCHEMA = {
    'Academic': ['Faculty', 'Attendance', 'Timetable', 'Subject', 'Assignment', 'Laboratory', 'Internal Marks'],
    'Exam Cell': ['Hall Ticket', 'Exam Timetable', 'Results', 'Revaluation', 'Supplementary Exam'],
    'Placement': ['Placement Drive', 'Training', 'Internship', 'Interview', 'Resume Support'],
    'Hostel': ['Room', 'Food', 'Water', 'Electricity', 'Internet', 'Cleanliness'],
    'Transport': ['Bus Route', 'Bus Timing', 'Driver', 'Bus Pass', 'Vehicle'],
    'Library': ['Book', 'Availability', 'Issue/Return', 'Library Access'],
    'Maintenance': ['Electrical', 'Plumbing', 'Furniture', 'AC/Fan', 'Projector', 'Classroom', 'Infrastructure'],
    'IT / Wi-Fi': ['Internet', 'Wi-Fi', 'Computer', 'Software', 'Network'],
    'Student Support': ['General'],
    'General': ['General']
}

# SLA Durations (in hours)
SLA_HOURS = {
    'Critical': 4,
    'High': 24,
    'Medium': 48,
    'Low': 72,
    'Urgent': 4 # Map legacy/database 'Urgent' to 'Critical' SLA rules
}

def generate_complaint_id():
    """Generates unique collision-free ID format like: NBKR-YYYY-XXXXXX"""
    year = datetime.utcnow().year
    prefix = f"NBKR-{year}-"
    # Query database for max ID matching prefix to avoid concurrent collisions
    max_id_row = db.session.query(db.func.max(Complaint.id)).filter(Complaint.id.like(f"{prefix}%")).scalar()
    if max_id_row:
        try:
            suffix = max_id_row.replace(prefix, "")
            count = int(suffix)
        except ValueError:
            count = 0
    else:
        count = 0
    return f"{prefix}{(count + 1):06d}"

def check_grievance_access(user, complaint):
    """
    Validates user's authorization to access the specific grievance.
    Returns True if allowed, False otherwise.
    """
    if not user:
        return False
    if user.role == 'super_admin':
        return True
    if user.role == 'student':
        return complaint.student_id == user.student_profile.id
    if user.role == 'hod':
        # HOD can access grievances belonging to their department
        if user.staff_profile:
            return complaint.suggested_department.lower() == user.staff_profile.department.lower()
        return False
    # Other staff roles (faculty, maintenance_staff, etc.) can only view assigned tickets
    if user.staff_profile:
        return complaint.assigned_staff_id == user.staff_profile.id
    return False

@complaints_bp.route('/categories-schema', methods=['GET'])
@grievances_bp.route('/categories-schema', methods=['GET'])
@jwt_required()
def get_categories_schema():
    """Returns the centralized categories and subcategories mapping."""
    return jsonify({
        'success': True,
        'data': CATEGORIES_SCHEMA
    }), 200

@complaints_bp.route('/uploads/<string:filename>', methods=['GET'])
@grievances_bp.route('/uploads/<string:filename>', methods=['GET'])
def serve_uploads_secure(filename):
    """
    Serves uploaded attachment files securely after performing token validation and IDOR check.
    Supports JWT inside Authorization header or as a query parameter (?token=).
    """
    auth_header = request.headers.get('Authorization')
    token = None
    if auth_header and auth_header.startswith('Bearer '):
        token = auth_header.split(' ')[1]
    else:
        token = request.args.get('token')

    if not token:
        return jsonify({'success': False, 'message': 'Missing authentication token', 'error': 'token_missing'}), 401

    try:
        decoded = decode_token(token)
        user_id = int(decoded['sub'])
    except Exception:
        return jsonify({'success': False, 'message': 'Invalid token signature', 'error': 'token_invalid'}), 401

    user = User.query.get(user_id)
    if not user:
        return jsonify({'success': False, 'message': 'User profile not found', 'error': 'user_not_found'}), 404

    image_path = f"uploads/{filename}"
    complaint = Complaint.query.filter_by(image_path=image_path).first()
    if not complaint:
        if user.role == 'super_admin':
            return send_from_directory(current_app.config['UPLOAD_FOLDER'], filename)
        return jsonify({'success': False, 'message': 'File not found or unregistered', 'error': 'not_found'}), 404

    if not check_grievance_access(user, complaint):
        return jsonify({'success': False, 'message': 'Access forbidden to this file', 'error': 'forbidden'}), 403

    return send_from_directory(current_app.config['UPLOAD_FOLDER'], filename)

@complaints_bp.route('/categories', methods=['GET'])
@grievances_bp.route('/categories', methods=['GET'])
@jwt_required()
def get_categories():
    """Fetches all complaint categories (only parent/top-level categories)."""
    categories = ComplaintCategory.query.filter_by(parent_category_id=None).all()
    return jsonify({
        'success': True,
        'data': [c.to_dict() for c in categories]
    }), 200

@complaints_bp.route('', methods=['POST'])
@grievances_bp.route('', methods=['POST'])
@jwt_required()
def create_complaint():
    """Submit a new grievance ticket. Performs duplicate detection and dynamic SLA assignment."""
    user_id = int(get_jwt_identity())
    user = User.query.get(user_id)
    
    if not user or user.role != 'student':
        return jsonify({'success': False, 'message': 'Only students can submit grievances', 'error': 'forbidden'}), 403

    student = user.student_profile
    if not student:
        return jsonify({'success': False, 'message': 'Student profile not found', 'error': 'profile_missing'}), 404

    title = request.form.get('title', '').strip()
    description = request.form.get('description', '').strip()
    category_id_raw = request.form.get('category_id')
    subcategory = request.form.get('subcategory', '').strip()
    location = request.form.get('location', '').strip()
    priority_requested = request.form.get('priority', 'Medium').strip()
    force_submit = request.args.get('force', 'false').lower() == 'true'

    if not (title and description and category_id_raw and location):
        return jsonify({'success': False, 'message': 'Title, description, category_id, and location are required', 'error': 'missing_fields'}), 400

    try:
        category_id = int(category_id_raw)
    except ValueError:
        return jsonify({'success': False, 'message': 'Invalid category ID', 'error': 'invalid_category'}), 400

    category = ComplaintCategory.query.get(category_id)
    if not category:
        return jsonify({'success': False, 'message': 'Category does not exist', 'error': 'category_not_found'}), 400

    if priority_requested in ['Critical', 'Urgent']:
        priority_requested = 'High'

    ai_results = classify_complaint(description)
    final_priority = ai_results['priority']
    
    if priority_requested == 'High' and final_priority in ['Low', 'Medium']:
        final_priority = 'High'

    final_subcategory = subcategory if subcategory else ai_results.get('subcategory', 'General')

    image_path = None
    if 'image' in request.files:
        file = request.files['image']
        try:
            image_path = save_uploaded_file(file, current_app.config['UPLOAD_FOLDER'])
        except ValueError as e:
            return jsonify({'success': False, 'message': str(e), 'error': 'invalid_file'}), 400

    if not force_submit:
        seven_days_ago = datetime.utcnow() - timedelta(days=7)
        recent_open_grievances = Complaint.query.filter(
            Complaint.student_id == student.id,
            Complaint.created_at >= seven_days_ago,
            ~Complaint.status.in_(['Resolved', 'Closed', 'Rejected'])
        ).all()

        STOP_WORDS = {'is', 'and', 'the', 'in', 'for', 'with', 'room', 'block', 'to', 'of', 'at', 'a', 'an', 'my', 'on', 'this', 'that', 'it', 'is', 'making', 'slowly', 'rotating'}
        for g in recent_open_grievances:
            tokens_new = set(w for w in (title.lower().split() + description.lower().split()) if w not in STOP_WORDS)
            tokens_old = set(w for w in (g.title.lower().split() + g.description.lower().split()) if w not in STOP_WORDS)
            intersection = tokens_new.intersection(tokens_old)
            if len(intersection) >= 4 or g.title.lower() == title.lower():
                if image_path:
                    delete_file(image_path, current_app.config['UPLOAD_FOLDER'])
                return jsonify({
                    'success': False,
                    'message': 'Similar grievance already exists.',
                    'error': 'duplicate_detected',
                    'duplicate': {
                        'id': g.id,
                        'title': g.title,
                        'status': g.status,
                        'created_at': g.created_at.isoformat()
                    }
                }), 409

    try:
        complaint_id = generate_complaint_id()
        now = datetime.utcnow()
        sla_hours = SLA_HOURS.get(final_priority, 48)
        sla_deadline = now + timedelta(hours=sla_hours)

        complaint = Complaint(
            id=complaint_id,
            student_id=student.id,
            title=title,
            description=description,
            category_id=category_id,
            subcategory=final_subcategory,
            location=location,
            image_path=image_path,
            ai_priority=final_priority,
            ai_confidence=ai_results['confidence'],
            suggested_department=ai_results['department'],
            sla_deadline=sla_deadline,
            sla_status='Normal',
            status='Submitted'
        )

        db.session.add(complaint)

        history = ComplaintHistory(
            complaint_id=complaint_id,
            user_id=user_id,
            action='Created',
            new_value='Submitted',
            comments=f"Grievance raised. AI mapped category: {category.name}, subcategory: {final_subcategory}, priority: {final_priority}."
        )
        db.session.add(history)

        db.session.commit()

        create_notification(
            user_id=user_id,
            title="Grievance Raised Successfully",
            message=f"Your grievance {complaint_id} has been logged. SLA response time: {sla_hours} hours.",
            notif_type="status_change",
            complaint_id=complaint_id
        )

        return jsonify({
            'success': True,
            'message': 'Grievance submitted successfully',
            'data': complaint.to_dict()
        }), 201

    except Exception as e:
        db.session.rollback()
        if image_path:
            delete_file(image_path, current_app.config['UPLOAD_FOLDER'])
        return jsonify({'success': False, 'message': 'Failed to submit grievance', 'error': str(e)}), 500

@complaints_bp.route('', methods=['GET'])
@grievances_bp.route('', methods=['GET'])
@jwt_required()
def get_complaints():
    """Retrieves all grievances with role-based visibility, query searches, and pagination."""
    claims = get_jwt()
    user_id = int(get_jwt_identity())
    user = User.query.get(user_id)
    role = (user.role if user else None) or claims.get('role')

    query = Complaint.query

    if role == 'student':
        if user and user.student_profile:
            query = query.filter(Complaint.student_id == user.student_profile.id)
        else:
            return jsonify({'success': True, 'data': [], 'total_count': 0})
    elif role == 'hod':
        if user and user.staff_profile:
            query = query.filter(db.func.lower(Complaint.suggested_department) == user.staff_profile.department.lower())
        else:
            return jsonify({'success': True, 'data': [], 'total_count': 0})
    elif role in ['faculty', 'maintenance_staff', 'librarian']:
        if user and user.staff_profile:
            query = query.filter(Complaint.assigned_staff_id == user.staff_profile.id)
        else:
            return jsonify({'success': True, 'data': [], 'total_count': 0})

    status_filter = request.args.get('status')
    priority_filter = request.args.get('priority')
    category_filter = request.args.get('category_id')
    subcategory_filter = request.args.get('subcategory')
    department_filter = request.args.get('department')
    sla_status_filter = request.args.get('sla_status')
    search_query = request.args.get('search', '').strip()

    if status_filter:
        query = query.filter(Complaint.status == status_filter)
    if priority_filter:
        query = query.filter(Complaint.ai_priority == priority_filter)
    if category_filter:
        query = query.filter(Complaint.category_id == category_filter)
    if subcategory_filter:
        query = query.filter(Complaint.subcategory == subcategory_filter)
    if department_filter:
        query = query.filter(Complaint.suggested_department == department_filter)
    if sla_status_filter:
        if sla_status_filter == 'Breached':
            query = query.filter(
                Complaint.status.not_in(['Resolved', 'Closed', 'Rejected']),
                Complaint.sla_deadline < datetime.utcnow()
            )
        else:
            query = query.filter(
                (Complaint.sla_status == 'Normal') | 
                (Complaint.status.in_(['Resolved', 'Closed', 'Rejected'])) |
                (Complaint.sla_deadline >= datetime.utcnow())
            )

    if search_query:
        query = query.join(Student, isouter=True).filter(
            (Complaint.id.like(f"%{search_query}%")) |
            (Complaint.title.like(f"%{search_query}%")) |
            (Complaint.description.like(f"%{search_query}%")) |
            (Student.roll_no.like(f"%{search_query}%"))
        )

    sort_by = request.args.get('sort_by', 'created_at')
    order = request.args.get('order', 'desc')
    if order == 'asc':
        query = query.order_by(getattr(Complaint, sort_by).asc())
    else:
        query = query.order_by(getattr(Complaint, sort_by).desc())

    try:
        page = max(1, int(request.args.get('page', 1)))
        per_page = min(500, max(1, int(request.args.get('per_page', 100))))
    except ValueError:
        page = 1
        per_page = 100

    total_count = query.count()
    paginated = query.offset((page - 1) * per_page).limit(per_page).all()

    return jsonify({
        'success': True,
        'data': [c.to_dict() for c in paginated],
        'total_count': total_count,
        'page': page,
        'per_page': per_page
    }), 200

@complaints_bp.route('/<string:id>', methods=['GET'])
@grievances_bp.route('/<string:id>', methods=['GET'])
@jwt_required()
def get_complaint_by_id(id):
    """Fetches a detailed record of the grievance with timeline and access validations (IDOR)."""
    user_id = int(get_jwt_identity())
    user = User.query.get(user_id)
    complaint = Complaint.query.get(id)

    if not complaint:
        return jsonify({'success': False, 'message': 'Grievance not found', 'error': 'not_found'}), 404

    if not check_grievance_access(user, complaint):
        return jsonify({'success': False, 'message': 'Access forbidden to this grievance', 'error': 'forbidden'}), 403

    histories = [h.to_dict() for h in complaint.histories]
    assignments = [a.to_dict() for a in complaint.assignments]

    return jsonify({
        'success': True,
        'data': {
            **complaint.to_dict(),
            'history': histories,
            'assignments': assignments
        }
    }), 200

@complaints_bp.route('/<string:id>', methods=['PUT'])
@grievances_bp.route('/<string:id>', methods=['PUT'])
@jwt_required()
def update_complaint(id):
    """Updates grievance metadata (Admin updates priority/category, Staff updates notes)."""
    user_id = int(get_jwt_identity())
    user = User.query.get(user_id)
    complaint = Complaint.query.get(id)

    if not complaint:
        return jsonify({'success': False, 'message': 'Grievance not found', 'error': 'not_found'}), 404

    if not check_grievance_access(user, complaint):
        return jsonify({'success': False, 'message': 'Forbidden update request', 'error': 'forbidden'}), 403

    data = request.get_json() or {}

    try:
        if user.role == 'super_admin':
            if 'category_id' in data:
                old_val = complaint.category.name if complaint.category else 'None'
                new_cat = ComplaintCategory.query.get(data['category_id'])
                if new_cat:
                    complaint.category_id = new_cat.id
                    db.session.add(ComplaintHistory(
                        complaint_id=id, user_id=user_id, action='Category Change',
                        previous_value=old_val, new_value=new_cat.name,
                        comments="Category updated manually by Administrator"
                    ))

            if 'ai_priority' in data:
                old_val = complaint.ai_priority
                new_val = data['ai_priority']
                if old_val != new_val:
                    complaint.ai_priority = new_val
                    sla_hours = SLA_HOURS.get(new_val, 48)
                    complaint.sla_deadline = complaint.created_at + timedelta(hours=sla_hours)
                    
                    db.session.add(ComplaintHistory(
                        complaint_id=id, user_id=user_id, action='Priority Change',
                        previous_value=old_val, new_value=new_val,
                        comments=f"Priority adjusted to {new_val} by Admin. SLA deadline adjusted."
                    ))
                    notify_priority_change(complaint, old_val, new_val)

            if 'suggested_department' in data:
                old_val = complaint.suggested_department
                new_val = data['suggested_department']
                if old_val != new_val:
                    complaint.suggested_department = new_val
                    db.session.add(ComplaintHistory(
                        complaint_id=id, user_id=user_id, action='Department Change',
                        previous_value=old_val, new_value=new_val,
                        comments="Department updated manually by Administrator"
                    ))

        if user.role in ['faculty', 'hod', 'maintenance_staff', 'librarian'] and complaint.assigned_staff_id == user.staff_profile.id:
            if 'work_notes' in data:
                complaint.work_notes = data['work_notes']
                db.session.add(ComplaintHistory(
                    complaint_id=id, user_id=user_id, action='Note Added',
                    comments=f"Staff notes: {data['work_notes']}"
                ))

        db.session.commit()
        return jsonify({
            'success': True,
            'message': 'Grievance updated successfully',
            'data': complaint.to_dict()
        }), 200

    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'message': 'Failed to update grievance', 'error': str(e)}), 500

@complaints_bp.route('/<string:id>', methods=['DELETE'])
@grievances_bp.route('/<string:id>', methods=['DELETE'])
@jwt_required()
def delete_complaint(id):
    """Admin-only hard delete."""
    user_id = int(get_jwt_identity())
    user = User.query.get(user_id)

    if not user or user.role != 'super_admin':
        return jsonify({'success': False, 'message': 'Only Admins can delete grievances', 'error': 'forbidden'}), 403

    complaint = Complaint.query.get(id)
    if not complaint:
        return jsonify({'success': False, 'message': 'Grievance not found', 'error': 'not_found'}), 404

    try:
        if complaint.image_path:
            delete_file(complaint.image_path, current_app.config['UPLOAD_FOLDER'])

        db.session.delete(complaint)
        db.session.commit()
        return jsonify({
            'success': True,
            'message': f'Grievance {id} deleted successfully'
        }), 200

    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'message': 'Failed to delete grievance', 'error': str(e)}), 500

@complaints_bp.route('/<string:id>/assign', methods=['POST'])
@grievances_bp.route('/<string:id>/assign', methods=['POST'])
@jwt_required()
def assign_complaint(id):
    """Assigns grievance to a staff member. Transition status to 'Assigned'."""
    user_id = int(get_jwt_identity())
    user = User.query.get(user_id)
    complaint = Complaint.query.get(id)

    if not complaint:
        return jsonify({'success': False, 'message': 'Grievance not found', 'error': 'not_found'}), 404

    is_authorized = False
    admin_id = None
    if user.role == 'super_admin':
        is_authorized = True
        admin = user.admin_profile
        admin_id = admin.id if admin else None
    elif user.role == 'hod':
        if user.staff_profile and complaint.suggested_department.lower() == user.staff_profile.department.lower():
            is_authorized = True
            admin_id = user.staff_profile.id

    if not is_authorized:
        return jsonify({'success': False, 'message': 'Unauthorized to assign staff', 'error': 'forbidden'}), 403

    data = request.get_json() or {}
    faculty_id = data.get('faculty_id') or data.get('staff_id')
    branch = data.get('branch')

    if not faculty_id:
        return jsonify({'success': False, 'message': 'Please select a faculty member.', 'error': 'missing_faculty'}), 400
    if not branch:
        return jsonify({'success': False, 'message': 'Please select a branch.', 'error': 'missing_branch'}), 400

    staff = Staff.query.get(faculty_id) or Staff.query.filter_by(user_id=faculty_id).first()
    if not staff:
        return jsonify({'success': False, 'message': 'Faculty member not found', 'error': 'faculty_not_found'}), 404

    # Verify that user has Faculty/HOD role
    if staff.user.role not in ['faculty', 'hod']:
        return jsonify({'success': False, 'message': 'Selected staff member is not a faculty member.', 'error': 'invalid_role'}), 400

    # Verify that selected faculty belongs to the selected branch
    from app.models.department import Department
    is_branch_match = False
    if staff.department_id:
        dept = Department.query.get(staff.department_id)
        if dept and dept.code:
            d_code = dept.code.lower()
            b_code = branch.lower()
            if d_code == b_code or (d_code == 'ce' and b_code == 'civil') or (d_code == 'civil' and b_code == 'ce'):
                is_branch_match = True
    
    if not is_branch_match:
        dept_name = staff.department.lower()
        b_name = branch.lower()
        if (b_name in dept_name or
            (b_name == 'cse' and 'computer science' in dept_name) or
            (b_name == 'ece' and 'electronics' in dept_name and 'communication' in dept_name) or
            (b_name == 'eee' and 'electrical' in dept_name and 'electronics' in dept_name) or
            (b_name == 'me' and 'mechanical' in dept_name) or
            (b_name in ['civil', 'ce'] and 'civil' in dept_name) or
            (b_name == 'it' and 'information technology' in dept_name) or
            (b_name in ['ai & ds', 'ai', 'ds'] and ('artificial intelligence' in dept_name or 'data science' in dept_name))):
            is_branch_match = True

    if not is_branch_match:
        return jsonify({'success': False, 'message': 'Selected faculty does not belong to this branch.', 'error': 'branch_mismatch'}), 400

    if user.role == 'hod' and staff.department.lower() != user.staff_profile.department.lower():
        return jsonify({'success': False, 'message': 'HOD cannot assign staff from another department', 'error': 'forbidden'}), 403

    try:
        assigned_time = datetime.utcnow()
        assignment = ComplaintAssignment(
            complaint_id=id,
            staff_id=staff.id,
            assigned_by=admin_id or 1,
            status='Assigned',
            assigned_at=assigned_time
        )
        db.session.add(assignment)

        old_status = complaint.status
        old_staff = complaint.assigned_staff.user.username if complaint.assigned_staff and complaint.assigned_staff.user else 'None'
        
        from app.utils.sla import calculate_resolution_deadline
        resolution_dl = calculate_resolution_deadline(assigned_time, 2)

        complaint.assigned_staff_id = staff.id
        complaint.status = 'Assigned'
        complaint.sla_deadline = resolution_dl

        db.session.add(ComplaintHistory(
            complaint_id=id, user_id=user_id, action='Assigned',
            previous_value=old_staff, new_value=staff.user.username,
            comments=f"Grievance assigned to faculty {staff.user.username}."
        ))

        if old_status != 'Assigned':
            db.session.add(ComplaintHistory(
                complaint_id=id, user_id=user_id, action='Status Update',
                previous_value=old_status, new_value='Assigned'
            ))

        db.session.commit()

        notify_assignment(complaint, staff)

        # Dispatch email assignment notification (separately to ensure robustness)
        try:
            assigned_date_str = assigned_time.strftime("%d %b %Y, ") + str(int(assigned_time.strftime("%I"))) + assigned_time.strftime(":%M %p")
            resolution_deadline_str = resolution_dl.strftime("%d %b %Y")
            EmailService.send_assignment_email(
                to_email=staff.user.email,
                faculty_name=staff.user.username,
                complaint_id=complaint.id,
                category_name=complaint.category.name if complaint.category else 'General',
                priority=complaint.ai_priority,
                branch=branch,
                assigned_date=assigned_date_str,
                resolution_deadline=resolution_deadline_str
            )
        except Exception as email_err:
            current_app.logger.error(f"Failed to dispatch assignment email: {str(email_err)}")

        return jsonify({
            'success': True,
            'message': f'Grievance assigned to {staff.user.username} successfully',
            'data': complaint.to_dict()
        }), 200

    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'message': 'Assignment failed', 'error': str(e)}), 500

@complaints_bp.route('/<string:id>/status', methods=['PUT'])
@grievances_bp.route('/<string:id>/status', methods=['PUT'])
@jwt_required()
def change_complaint_status(id):
    """Workflow state transitions checks."""
    user_id = int(get_jwt_identity())
    user = User.query.get(user_id)
    complaint = Complaint.query.get(id)

    if not complaint:
        return jsonify({'success': False, 'message': 'Grievance not found', 'error': 'not_found'}), 404

    data = request.get_json() or {}
    new_status = data.get('status')
    comments = data.get('comments', '').strip()

    if not new_status:
        return jsonify({'success': False, 'message': 'Status parameter is required', 'error': 'missing_status'}), 400

    allowed = False
    
    if user.role == 'super_admin':
        allowed = new_status in ['Under Review', 'Assigned', 'In Progress', 'Resolved', 'Rejected']
    elif user.role == 'hod' and user.staff_profile and complaint.suggested_department.lower() == user.staff_profile.department.lower():
        allowed = new_status in ['Under Review', 'Assigned', 'In Progress', 'Resolved', 'Rejected']
    elif user.role in ['faculty', 'maintenance_staff', 'librarian'] and complaint.assigned_staff_id == user.staff_profile.id:
        allowed = new_status in ['In Progress', 'Resolved']
    elif user.role == 'student' and complaint.student_id == user.student_profile.id:
        allowed = new_status in ['Closed', 'Reopened']

    if not allowed:
        return jsonify({'success': False, 'message': f'Unauthorized status transition to {new_status}', 'error': 'forbidden'}), 403

    try:
        old_status = complaint.status
        complaint.status = new_status

        if new_status == 'Resolved':
            complaint.resolved_at = datetime.utcnow()
        elif new_status == 'Reopened':
            complaint.resolved_at = None

        if comments:
            complaint.work_notes = f"{complaint.work_notes or ''}\n[{new_status} - {datetime.utcnow().strftime('%Y-%m-%d %H:%M')}] {comments}".strip()

        db.session.add(ComplaintHistory(
            complaint_id=id, user_id=user_id, action='Status Update',
            previous_value=old_status, new_value=new_status,
            comments=comments or f"Status changed from {old_status} to {new_status}."
        ))

        db.session.commit()

        notify_status_change(complaint, old_status, new_status)

        return jsonify({
            'success': True,
            'message': f'Status updated to {new_status} successfully',
            'data': complaint.to_dict()
        }), 200

    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'message': 'Status transition failed', 'error': str(e)}), 500

@complaints_bp.route('/<string:id>/feedback', methods=['POST'])
@grievances_bp.route('/<string:id>/feedback', methods=['POST'])
@jwt_required()
def submit_feedback(id):
    """Submits student feedback on a resolved/closed ticket and auto-closes resolved tickets."""
    user_id = int(get_jwt_identity())
    user = User.query.get(user_id)
    complaint = Complaint.query.get(id)

    if not complaint:
        return jsonify({'success': False, 'message': 'Grievance not found', 'error': 'not_found'}), 404

    if user.role != 'student' or complaint.student_id != user.student_profile.id:
        return jsonify({'success': False, 'message': 'Access forbidden to feedback submission', 'error': 'forbidden'}), 403

    if complaint.status not in ['Resolved', 'Closed']:
        return jsonify({'success': False, 'message': 'Feedback is allowed only on resolved or closed grievances', 'error': 'invalid_ticket_state'}), 400

    data = request.get_json() or {}
    rating = data.get('rating')
    comments = data.get('comments', '').strip()

    if not rating or not isinstance(rating, int) or rating < 1 or rating > 5:
        return jsonify({'success': False, 'message': 'Rating must be an integer between 1 and 5', 'error': 'invalid_rating'}), 400

    try:
        feedback = Feedback.query.filter_by(complaint_id=id).first()
        if feedback:
            feedback.rating = rating
            feedback.comments = comments
            message = 'Feedback updated successfully'
        else:
            feedback = Feedback(complaint_id=id, rating=rating, comments=comments)
            db.session.add(feedback)
            message = 'Feedback submitted successfully'

        if complaint.status == 'Resolved':
            complaint.status = 'Closed'
            db.session.add(ComplaintHistory(
                complaint_id=id, user_id=user_id, action='Status Update',
                previous_value='Resolved', new_value='Closed',
                comments="Ticket automatically closed after student submitted feedback."
            ))

        db.session.commit()

        return jsonify({
            'success': True,
            'message': message,
            'data': feedback.to_dict()
        }), 201

    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'message': 'Failed to save feedback', 'error': str(e)}), 500
