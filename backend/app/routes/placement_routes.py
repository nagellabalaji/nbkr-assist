from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity, get_jwt
from app import db
from app.models.user import User, Student
from app.models.placement import PlacementDrive, PlacementApplication
from app.models.attendance import Attendance
from app.services.notification_service import notify_placement_drive, notify_placement_status
from datetime import datetime

placement_bp = Blueprint('placements', __name__)

def get_student_context():
    """Retrieves student profile from token claims."""
    user_id = int(get_jwt_identity())
    user = User.query.get(user_id)
    if not user or user.role != 'student':
        return None
    return user.student_profile

@placement_bp.route('/drives', methods=['GET'])
@jwt_required()
def get_drives():
    """Retrieves scheduled placement drives list."""
    drives = PlacementDrive.query.order_by(PlacementDrive.drive_date.asc()).all()
    return jsonify({
        'success': True,
        'data': [d.to_dict() for d in drives]
    }), 200

@placement_bp.route('/drives', methods=['POST'])
@jwt_required()
def create_drive():
    """Creates a new placement drive circular. Restricted to placement officers/admins."""
    claims = get_jwt()
    if claims.get('role') not in ['placement_officer', 'super_admin', 'admin']:
        return jsonify({'success': False, 'message': 'Forbidden. Placement officer authorization required.', 'error': 'forbidden'}), 403

    data = request.get_json() or {}
    company_name = data.get('company_name', '').strip()
    job_role = data.get('job_role', '').strip()
    eligibility_criteria = data.get('eligibility_criteria', '').strip()
    salary_package = data.get('salary_package', '').strip()
    drive_date_raw = data.get('drive_date')

    if not (company_name and job_role and drive_date_raw):
        return jsonify({'success': False, 'message': 'Missing required fields (company_name, job_role, drive_date).', 'error': 'missing_fields'}), 400

    try:
        drive_date = datetime.fromisoformat(drive_date_raw.replace('Z', ''))
    except ValueError:
        return jsonify({'success': False, 'message': 'Invalid drive_date format. Expecting ISO-8601 string.', 'error': 'invalid_date'}), 400

    try:
        new_drive = PlacementDrive(
            company_name=company_name,
            job_role=job_role,
            eligibility_criteria=eligibility_criteria,
            salary_package=salary_package,
            drive_date=drive_date,
            status='Upcoming'
        )
        db.session.add(new_drive)
        db.session.commit()
        notify_placement_drive(new_drive)
        return jsonify({
            'success': True,
            'message': 'Placement drive published successfully.',
            'data': new_drive.to_dict()
        }), 201
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'message': 'Database insertion error.', 'error': str(e)}), 500

@placement_bp.route('/drives/<int:drive_id>', methods=['PUT'])
@jwt_required()
def update_drive(drive_id):
    """Updates a drive's parameters. Restricted to placement officers/admins."""
    claims = get_jwt()
    if claims.get('role') not in ['placement_officer', 'super_admin', 'admin']:
        return jsonify({'success': False, 'message': 'Forbidden.', 'error': 'forbidden'}), 403

    drive = PlacementDrive.query.get(drive_id)
    if not drive:
        return jsonify({'success': False, 'message': 'Placement drive not found.', 'error': 'not_found'}), 404

    data = request.get_json() or {}
    
    drive.company_name = data.get('company_name', drive.company_name).strip()
    drive.job_role = data.get('job_role', drive.job_role).strip()
    drive.eligibility_criteria = data.get('eligibility_criteria', drive.eligibility_criteria).strip()
    drive.salary_package = data.get('salary_package', drive.salary_package).strip()
    
    drive_date_raw = data.get('drive_date')
    if drive_date_raw:
        try:
            drive.drive_date = datetime.fromisoformat(drive_date_raw.replace('Z', ''))
        except ValueError:
            return jsonify({'success': False, 'message': 'Invalid drive_date format.', 'error': 'invalid_date'}), 400

    new_status = data.get('status')
    if new_status:
        if new_status not in ['Upcoming', 'Ongoing', 'Completed']:
            return jsonify({'success': False, 'message': 'Invalid status.', 'error': 'invalid_status'}), 400
        drive.status = new_status

    try:
        db.session.commit()
        return jsonify({
            'success': True,
            'message': 'Placement drive updated successfully.',
            'data': drive.to_dict()
        }), 200
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'message': 'Database update failed.', 'error': str(e)}), 500

@placement_bp.route('/drives/<int:drive_id>', methods=['DELETE'])
@jwt_required()
def delete_drive(drive_id):
    """Removes a placement drive circular. Restricted to placement officers/admins."""
    claims = get_jwt()
    if claims.get('role') not in ['placement_officer', 'super_admin', 'admin']:
        return jsonify({'success': False, 'message': 'Forbidden.', 'error': 'forbidden'}), 403

    drive = PlacementDrive.query.get(drive_id)
    if not drive:
        return jsonify({'success': False, 'message': 'Placement drive not found.', 'error': 'not_found'}), 404

    try:
        db.session.delete(drive)
        db.session.commit()
        return jsonify({
            'success': True,
            'message': 'Placement drive deleted successfully.'
        }), 200
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'message': 'Database deletion failed.', 'error': str(e)}), 500

@placement_bp.route('/applications', methods=['GET'])
@jwt_required()
def get_applications():
    """Lists registered applications, filtered by role constraints."""
    user_id = int(get_jwt_identity())
    user = User.query.get(user_id)
    if not user:
        return jsonify({'success': False, 'message': 'User not found.', 'error': 'user_not_found'}), 404

    query = PlacementApplication.query

    if user.role == 'student':
        student = user.student_profile
        if not student:
            return jsonify({'success': False, 'message': 'Student profile not found.', 'error': 'profile_missing'}), 404
        query = query.filter_by(student_id=student.id)
    elif user.role in ['placement_officer', 'super_admin', 'admin']:
        # Placements officer can optionally filter by drive
        drive_id = request.args.get('drive_id')
        if drive_id:
            try:
                query = query.filter_by(drive_id=int(drive_id))
            except ValueError:
                pass
    else:
        # HOD, Faculty, other roles cannot access candidates' applications
        return jsonify({'success': False, 'message': 'Forbidden. Access restricted.', 'error': 'forbidden'}), 403

    apps = query.order_by(PlacementApplication.applied_at.desc()).all()
    return jsonify({
        'success': True,
        'data': [a.to_dict() for a in apps]
    }), 200

@placement_bp.route('/applications', methods=['POST'])
@jwt_required()
def apply_for_drive():
    """Registers the authenticated student to a recruitment campaign. Enforces attendance bounds."""
    student = get_student_context()
    if not student:
        return jsonify({'success': False, 'message': 'Only student accounts can apply for placement drives.', 'error': 'forbidden'}), 403

    data = request.get_json() or {}
    drive_id_raw = data.get('drive_id')

    if not drive_id_raw:
        return jsonify({'success': False, 'message': 'drive_id is required.', 'error': 'missing_fields'}), 400

    try:
        drive_id = int(drive_id_raw)
    except ValueError:
        return jsonify({'success': False, 'message': 'Invalid drive_id format.', 'error': 'invalid_drive'}), 400

    drive = PlacementDrive.query.get(drive_id)
    if not drive:
        return jsonify({'success': False, 'message': 'Placement drive not found.', 'error': 'not_found'}), 404

    if drive.status == 'Completed':
        return jsonify({'success': False, 'message': 'Cannot apply. This drive is already completed.', 'error': 'drive_closed'}), 400

    # Prevent duplicate registrations
    existing = PlacementApplication.query.filter_by(student_id=student.id, drive_id=drive.id).first()
    if existing:
        return jsonify({'success': False, 'message': 'You have already applied for this placement drive.', 'error': 'duplicate_application'}), 409

    # Enforce Attendance bounds >= 75%
    attendance_records = Attendance.query.filter_by(student_id=student.id).all()
    avg_attendance = sum(a.percentage for a in attendance_records) / len(attendance_records) if attendance_records else 100.0
    if avg_attendance < 75.0:
        return jsonify({
            'success': False,
            'message': f'You do not meet the minimum 75% attendance criteria (Your Attendance: {round(avg_attendance, 1)}%).',
            'error': 'attendance_shortage'
        }), 400

    try:
        new_app = PlacementApplication(
            student_id=student.id,
            drive_id=drive.id,
            status='applied'
        )
        db.session.add(new_app)
        db.session.commit()
        return jsonify({
            'success': True,
            'message': 'Applied for placement drive successfully.',
            'data': new_app.to_dict()
        }), 201
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'message': 'Database error.', 'error': str(e)}), 500

@placement_bp.route('/applications/<int:app_id>', methods=['PUT'])
@jwt_required()
def update_application_status(app_id):
    """Updates candidate registration status. Restricted to placement officers/admins."""
    claims = get_jwt()
    if claims.get('role') not in ['placement_officer', 'super_admin', 'admin']:
        return jsonify({'success': False, 'message': 'Forbidden. Student accounts cannot edit application status.', 'error': 'forbidden'}), 403

    app_rec = PlacementApplication.query.get(app_id)
    if not app_rec:
        return jsonify({'success': False, 'message': 'Placement application not found.', 'error': 'not_found'}), 404

    data = request.get_json() or {}
    new_status = data.get('status')

    if new_status not in ['applied', 'shortlisted', 'selected', 'rejected']:
        return jsonify({'success': False, 'message': 'Invalid status.', 'error': 'invalid_status'}), 400

    app_rec.status = new_status
    try:
        db.session.commit()
        notify_placement_status(app_rec)
        return jsonify({
            'success': True,
            'message': 'Application status updated successfully.',
            'data': app_rec.to_dict()
        }), 200
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'message': 'Update failed.', 'error': str(e)}), 500
