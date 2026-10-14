from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt
from app import db
from app.models.department import Department
from app.models.user import User

departments_bp = Blueprint('departments', __name__)

@departments_bp.route('', methods=['GET'])
def get_departments():
    """Fetches list of active academic departments."""
    try:
        depts = Department.query.filter_by(is_active=True).all()
        return jsonify({
            'success': True,
            'data': [d.to_dict() for d in depts]
        }), 200
    except Exception as e:
        return jsonify({'success': False, 'message': 'Failed to load departments', 'error': str(e)}), 500


@departments_bp.route('', methods=['POST'])
@jwt_required()
def create_department():
    """Create a new department (super_admin only)."""
    claims = get_jwt()
    if claims.get('role') != 'super_admin':
        return jsonify({'success': False, 'message': 'Forbidden. Admin access required.', 'error': 'forbidden'}), 403

    data = request.get_json() or {}
    name = data.get('name', '').strip()
    code = data.get('code', '').strip().upper()
    description = data.get('description', '').strip()
    hod_id = data.get('hod_id')

    if not (name and code):
        return jsonify({'success': False, 'message': 'Department name and code are required', 'error': 'missing_fields'}), 400

    try:
        # Check unique code
        if Department.query.filter_by(code=code).first():
            return jsonify({'success': False, 'message': 'Department code already exists', 'error': 'code_exists'}), 400

        # Validate HOD user if supplied
        if hod_id:
            hod_user = User.query.get(hod_id)
            if not hod_user or hod_user.role != 'hod':
                return jsonify({'success': False, 'message': 'Selected HOD user is invalid or not registered as HOD', 'error': 'invalid_hod'}), 400

        dept = Department(
            name=name,
            code=code,
            description=description,
            hod_id=hod_id,
            is_active=True
        )
        db.session.add(dept)
        db.session.commit()

        return jsonify({
            'success': True,
            'message': f'Department {code} created successfully',
            'data': dept.to_dict()
        }), 201

    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'message': 'Failed to create department', 'error': str(e)}), 500


@departments_bp.route('/<int:id>', methods=['PUT'])
@jwt_required()
def update_department(id):
    """Updates department details (super_admin only)."""
    claims = get_jwt()
    if claims.get('role') != 'super_admin':
        return jsonify({'success': False, 'message': 'Forbidden. Admin access required.', 'error': 'forbidden'}), 403

    dept = Department.query.get(id)
    if not dept:
        return jsonify({'success': False, 'message': 'Department not found', 'error': 'not_found'}), 404

    data = request.get_json() or {}
    name = data.get('name', '').strip()
    code = data.get('code', '').strip().upper()
    description = data.get('description', '').strip()
    hod_id = data.get('hod_id')

    if not (name and code):
        return jsonify({'success': False, 'message': 'Department name and code are required', 'error': 'missing_fields'}), 400

    try:
        # Check unique code if changed
        existing = Department.query.filter_by(code=code).first()
        if existing and existing.id != id:
            return jsonify({'success': False, 'message': 'Department code already exists', 'error': 'code_exists'}), 400

        if hod_id:
            hod_user = User.query.get(hod_id)
            if not hod_user or hod_user.role != 'hod':
                return jsonify({'success': False, 'message': 'Selected HOD user is invalid or not registered as HOD', 'error': 'invalid_hod'}), 400

        dept.name = name
        dept.code = code
        dept.description = description
        dept.hod_id = hod_id

        db.session.commit()

        return jsonify({
            'success': True,
            'message': f'Department {code} updated successfully',
            'data': dept.to_dict()
        }), 200

    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'message': 'Failed to update department', 'error': str(e)}), 500


@departments_bp.route('/<int:id>/status', methods=['PATCH'])
@jwt_required()
def patch_department_status(id):
    """Toggles department active/inactive status (super_admin only)."""
    claims = get_jwt()
    if claims.get('role') != 'super_admin':
        return jsonify({'success': False, 'message': 'Forbidden. Admin access required.', 'error': 'forbidden'}), 403

    dept = Department.query.get(id)
    if not dept:
        return jsonify({'success': False, 'message': 'Department not found', 'error': 'not_found'}), 404

    data = request.get_json() or {}
    is_active = data.get('is_active')

    if is_active is None or not isinstance(is_active, bool):
        return jsonify({'success': False, 'message': 'is_active parameter must be a boolean', 'error': 'invalid_parameter'}), 400

    try:
        dept.is_active = is_active
        db.session.commit()

        return jsonify({
            'success': True,
            'message': f"Department status updated to {'active' if is_active else 'inactive'}",
            'data': dept.to_dict()
        }), 200

    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'message': 'Failed to update status', 'error': str(e)}), 500
