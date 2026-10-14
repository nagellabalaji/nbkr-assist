from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity, get_jwt
from app import db
from app.models.user import User, Student
from app.models.transport import TransportRoute, TransportRequest
from app.services.notification_service import notify_campus_service
from datetime import datetime

transport_bp = Blueprint('transport', __name__)

def get_student_context():
    """Retrieves student profile from token claims."""
    user_id = int(get_jwt_identity())
    user = User.query.get(user_id)
    if not user or user.role != 'student':
        return None
    return user.student_profile

@transport_bp.route('/routes', methods=['GET'])
@jwt_required()
def get_routes():
    """Exposes active bus routes list."""
    routes = TransportRoute.query.filter_by(is_active=True).all()
    return jsonify({
        'success': True,
        'data': [r.to_dict() for r in routes]
    }), 200

@transport_bp.route('/status', methods=['GET'])
@jwt_required()
def get_status():
    """Retrieves student-specific bus transit settings."""
    student = get_student_context()
    if not student:
        return jsonify({'success': False, 'message': 'Only student accounts can access transport status.', 'error': 'not_a_student'}), 403

    return jsonify({
        'success': True,
        'data': {
            'transport_status': student.transport_status
        }
    }), 200

@transport_bp.route('/requests', methods=['GET'])
@jwt_required()
def get_transport_requests():
    """Lists student bus requests. Restricts query based on student credentials."""
    user_id = int(get_jwt_identity())
    user = User.query.get(user_id)
    if not user:
        return jsonify({'success': False, 'message': 'User not found.', 'error': 'user_not_found'}), 404

    query = TransportRequest.query

    if user.role == 'student':
        student = user.student_profile
        if not student:
            return jsonify({'success': False, 'message': 'Student profile not found.', 'error': 'profile_missing'}), 404
        query = query.filter_by(student_id=student.id)
    elif user.role in ['transport_admin', 'super_admin', 'admin']:
        pass
    else:
        # HOD, Faculty, etc. cannot access private student bus data
        return jsonify({'success': False, 'message': 'Forbidden. Access restricted.', 'error': 'forbidden'}), 403

    requests = query.order_by(TransportRequest.created_at.desc()).all()
    return jsonify({
        'success': True,
        'data': [r.to_dict() for r in requests]
    }), 200

@transport_bp.route('/requests', methods=['POST'])
@jwt_required()
def create_transport_request():
    """Publishes a new transport request."""
    student = get_student_context()
    if not student:
        return jsonify({'success': False, 'message': 'Only student accounts can raise transport requests.', 'error': 'forbidden'}), 403

    data = request.get_json() or {}
    request_type = data.get('request_type', '').strip().lower()
    route_id_val = data.get('route_id')
    description = data.get('description', '').strip()

    if request_type not in ['new_pass', 'renew_pass', 'route_change', 'grievance']:
        return jsonify({'success': False, 'message': 'Invalid transport request type.', 'error': 'invalid_type'}), 400

    if not description:
        return jsonify({'success': False, 'message': 'Request description cannot be empty.', 'error': 'missing_fields'}), 400

    route_id = None
    if route_id_val:
        try:
            route_id = int(route_id_val)
            route = TransportRoute.query.get(route_id)
            if not route:
                return jsonify({'success': False, 'message': 'Selected bus route not found.', 'error': 'route_not_found'}), 400
        except ValueError:
            return jsonify({'success': False, 'message': 'Invalid route ID.', 'error': 'route_not_found'}), 400

    try:
        new_req = TransportRequest(
            student_id=student.id,
            request_type=request_type,
            route_id=route_id,
            description=description,
            status='submitted'
        )
        db.session.add(new_req)
        db.session.commit()

        return jsonify({
            'success': True,
            'message': 'Transport request raised successfully.',
            'data': new_req.to_dict()
        }), 201
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'message': 'Database error.', 'error': str(e)}), 500

@transport_bp.route('/requests/<int:req_id>', methods=['PUT'])
@jwt_required()
def update_transport_request(req_id):
    """Updates a transport request. Students can edit submitted requests; Admins can update status."""
    user_id = int(get_jwt_identity())
    user = User.query.get(user_id)
    if not user:
        return jsonify({'success': False, 'message': 'User not found.', 'error': 'user_not_found'}), 404

    req = TransportRequest.query.get(req_id)
    if not req:
        return jsonify({'success': False, 'message': 'Transport request not found.', 'error': 'not_found'}), 404

    data = request.get_json() or {}

    # Enforce IDOR protection: Student can only edit their own submitted requests
    if user.role == 'student':
        student = user.student_profile
        if not student or req.student_id != student.id:
            return jsonify({'success': False, 'message': 'Forbidden. Access isolated.', 'error': 'forbidden'}), 403

        if req.status != 'submitted':
            return jsonify({'success': False, 'message': 'Request is already processed and cannot be edited.', 'error': 'request_locked'}), 400

        req.description = data.get('description', req.description).strip()
        req.request_type = data.get('request_type', req.request_type).strip().lower()
        if req.request_type not in ['new_pass', 'renew_pass', 'route_change', 'grievance']:
            return jsonify({'success': False, 'message': 'Invalid transport request type.', 'error': 'invalid_type'}), 400

        route_id_val = data.get('route_id')
        if route_id_val:
            try:
                route_id = int(route_id_val)
                route = TransportRoute.query.get(route_id)
                if not route:
                    return jsonify({'success': False, 'message': 'Selected bus route not found.', 'error': 'route_not_found'}), 400
                req.route_id = route_id
            except ValueError:
                return jsonify({'success': False, 'message': 'Invalid route ID.', 'error': 'route_not_found'}), 400

    elif user.role in ['transport_admin', 'super_admin', 'admin']:
        # Admin can update status and notes
        new_status = data.get('status')
        if new_status:
            if new_status not in ['submitted', 'approved', 'rejected']:
                return jsonify({'success': False, 'message': 'Invalid request status.', 'error': 'invalid_status'}), 400
            req.status = new_status
            
            # If approved, update student transport status in profile
            if new_status == 'approved' and req.request_type in ['new_pass', 'renew_pass', 'route_change']:
                req.student.transport_status = 'College Bus'
                db.session.add(req.student)
                
        req.admin_notes = data.get('admin_notes', req.admin_notes)
    else:
        return jsonify({'success': False, 'message': 'Forbidden.', 'error': 'forbidden'}), 403

    try:
        db.session.commit()
        if user.role in ['transport_admin', 'super_admin', 'admin'] and req.student and req.student.user:
            notify_campus_service(req.student.user_id, "Transport", req.id, req.status, req.admin_notes)
        return jsonify({
            'success': True,
            'message': 'Transport request updated successfully.',
            'data': req.to_dict()
        }), 200
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'message': 'Update failed.', 'error': str(e)}), 500
