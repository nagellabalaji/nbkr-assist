from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity, get_jwt
from app import db
from app.models.user import User, Student
from app.models.hostel import HostelRequest
from app.services.notification_service import notify_campus_service
from datetime import datetime

hostel_bp = Blueprint('hostel', __name__)

def get_student_context():
    """Retrieves student profile from token claims."""
    user_id = int(get_jwt_identity())
    user = User.query.get(user_id)
    if not user or user.role != 'student':
        return None
    return user.student_profile

@hostel_bp.route('/room-info', methods=['GET'])
@jwt_required()
def get_room_info():
    """Retrieves student-specific hostel details."""
    student = get_student_context()
    if not student:
        return jsonify({'success': False, 'message': 'Only student accounts can access room info.', 'error': 'not_a_student'}), 403

    return jsonify({
        'success': True,
        'data': {
            'hostel_status': student.hostel_status,
            'hostel_no': student.hostel_no,
            'room_no': student.room_no
        }
    }), 200

@hostel_bp.route('/requests', methods=['GET'])
@jwt_required()
def get_hostel_requests():
    """Lists hostel maintenance requests. Restricts query based on student credentials."""
    user_id = int(get_jwt_identity())
    user = User.query.get(user_id)
    if not user:
        return jsonify({'success': False, 'message': 'User not found.', 'error': 'user_not_found'}), 404

    query = HostelRequest.query

    if user.role == 'student':
        student = user.student_profile
        if not student:
            return jsonify({'success': False, 'message': 'Student profile not found.', 'error': 'profile_missing'}), 404
        query = query.filter_by(student_id=student.id)
    elif user.role in ['hostel_admin', 'super_admin', 'admin']:
        # Admins see all requests
        pass
    else:
        # Non-authorized roles (HOD, Faculty, etc.) are forbidden from viewing students' private details
        return jsonify({'success': False, 'message': 'Forbidden. Access restricted.', 'error': 'forbidden'}), 403

    # Sorting
    requests = query.order_by(HostelRequest.created_at.desc()).all()
    return jsonify({
        'success': True,
        'data': [r.to_dict() for r in requests]
    }), 200

@hostel_bp.route('/requests', methods=['POST'])
@jwt_required()
def create_hostel_request():
    """Publishes a new hostel maintenance request."""
    student = get_student_context()
    if not student:
        return jsonify({'success': False, 'message': 'Only student accounts can raise hostel requests.', 'error': 'forbidden'}), 403

    if student.hostel_status != 'Hosteller':
        return jsonify({'success': False, 'message': 'Only registered hostellers can lodge room maintenance requests.', 'error': 'not_a_hosteller'}), 400

    data = request.get_json() or {}
    request_type = data.get('request_type', '').strip().lower()
    description = data.get('description', '').strip()

    if request_type not in ['electrical', 'plumbing', 'room_repair', 'dining', 'other']:
        return jsonify({'success': False, 'message': 'Invalid maintenance request type.', 'error': 'invalid_type'}), 400

    if not description:
        return jsonify({'success': False, 'message': 'Request description cannot be empty.', 'error': 'missing_fields'}), 400

    try:
        new_req = HostelRequest(
            student_id=student.id,
            request_type=request_type,
            description=description,
            status='submitted'
        )
        db.session.add(new_req)
        db.session.commit()

        return jsonify({
            'success': True,
            'message': 'Hostel request raised successfully.',
            'data': new_req.to_dict()
        }), 201
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'message': 'Database error.', 'error': str(e)}), 500

@hostel_bp.route('/requests/<int:req_id>', methods=['PUT'])
@jwt_required()
def update_hostel_request(req_id):
    """Updates a hostel request. Students can edit submitted requests; Admins can update status."""
    user_id = int(get_jwt_identity())
    user = User.query.get(user_id)
    if not user:
        return jsonify({'success': False, 'message': 'User not found.', 'error': 'user_not_found'}), 404

    req = HostelRequest.query.get(req_id)
    if not req:
        return jsonify({'success': False, 'message': 'Hostel request not found.', 'error': 'not_found'}), 404

    data = request.get_json() or {}

    # Enforce IDOR protection: Student can only edit their own submitted requests
    if user.role == 'student':
        student = user.student_profile
        if not student or req.student_id != student.id:
            return jsonify({'success': False, 'message': 'Forbidden. Access isolated.', 'error': 'forbidden'}), 403

        if req.status != 'submitted':
            return jsonify({'success': False, 'message': 'Request is already in progress and cannot be edited.', 'error': 'request_locked'}), 400

        req.description = data.get('description', req.description).strip()
        req.request_type = data.get('request_type', req.request_type).strip().lower()
        if req.request_type not in ['electrical', 'plumbing', 'room_repair', 'dining', 'other']:
            return jsonify({'success': False, 'message': 'Invalid maintenance request type.', 'error': 'invalid_type'}), 400

    elif user.role in ['hostel_admin', 'super_admin', 'admin']:
        # Admin can update status and notes
        new_status = data.get('status')
        if new_status:
            if new_status not in ['submitted', 'in_progress', 'resolved', 'rejected']:
                return jsonify({'success': False, 'message': 'Invalid request status.', 'error': 'invalid_status'}), 400
            req.status = new_status
        req.admin_notes = data.get('admin_notes', req.admin_notes)
    else:
        return jsonify({'success': False, 'message': 'Forbidden.', 'error': 'forbidden'}), 403

    try:
        db.session.commit()
        if user.role in ['hostel_admin', 'super_admin', 'admin'] and req.student and req.student.user:
            notify_campus_service(req.student.user_id, "Hostel", req.id, req.status, req.admin_notes)
        return jsonify({
            'success': True,
            'message': 'Hostel request updated successfully.',
            'data': req.to_dict()
        }), 200
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'message': 'Update failed.', 'error': str(e)}), 500
