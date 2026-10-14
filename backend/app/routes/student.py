from flask import Blueprint, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from app import db
from app.models.user import User, Student
from app.models.complaint import Complaint
from app.models.log_feedback import Notification
from app.models.attendance import Attendance
from app.models.exam import ExamNotification
from app.models.placement import PlacementDrive
from datetime import datetime

student_bp = Blueprint('student_portal', __name__)

@student_bp.route('/dashboard/summary', methods=['GET'])
@jwt_required()
def get_student_dashboard_summary():
    """Retrieve personal student profile, metrics summary, and active status indicators."""
    user_id = int(get_jwt_identity())
    user = User.query.get(user_id)
    
    if not user or user.role != 'student':
        return jsonify({'success': False, 'message': 'Forbidden. Student access required.', 'error': 'forbidden'}), 403

    student = user.student_profile
    if not student:
        return jsonify({'success': False, 'message': 'Student profile details not found', 'error': 'profile_missing'}), 404

    try:
        # 1. Grievance Metrics
        open_grievances = Complaint.query.filter(
            Complaint.student_id == student.id,
            Complaint.status.notin_(['Resolved', 'Closed', 'Rejected'])
        ).count()
        
        resolved_grievances = Complaint.query.filter(
            Complaint.student_id == student.id,
            Complaint.status.in_(['Resolved', 'Closed'])
        ).count()

        # 2. Attendance Metric
        attendance_records = Attendance.query.filter_by(student_id=student.id).all()
        avg_attendance = 0.0
        if attendance_records:
            total_classes = sum(a.total_classes for a in attendance_records)
            present_classes = sum(a.present for a in attendance_records)
            if total_classes > 0:
                avg_attendance = (present_classes / total_classes) * 100

        # 3. Exams Metric (Upcoming exams for student's department or college-wide)
        upcoming_exams = ExamNotification.query.filter(
            ExamNotification.exam_date >= datetime.utcnow(),
            (ExamNotification.department_id == student.department_id) | (ExamNotification.department_id.is_(None))
        ).count()

        # 4. Placements Metric (Upcoming/ongoing placement drives)
        upcoming_placements = PlacementDrive.query.filter(
            PlacementDrive.drive_date >= datetime.utcnow(),
            PlacementDrive.status == 'Upcoming'
        ).count()

        # 5. Unread Notifications Count
        unread_notifications = Notification.query.filter_by(user_id=user.id, is_read=False).count()

        return jsonify({
            'success': True,
            'data': {
                'profile': student.to_dict(),
                'metrics': {
                    'open_grievances': open_grievances,
                    'resolved_grievances': resolved_grievances,
                    'average_attendance': round(avg_attendance, 1),
                    'upcoming_exams': upcoming_exams,
                    'upcoming_placements': upcoming_placements,
                    'unread_notifications': unread_notifications
                }
            }
        }), 200

    except Exception as e:
        return jsonify({'success': False, 'message': 'Failed to compile dashboard summary', 'error': str(e)}), 500


@student_bp.route('/dashboard/attendance', methods=['GET'])
@jwt_required()
def get_student_attendance():
    """Retrieve attendance record sheet for the logged-in student."""
    user_id = int(get_jwt_identity())
    user = User.query.get(user_id)
    
    if not user or user.role != 'student':
        return jsonify({'success': False, 'message': 'Forbidden. Student access required.', 'error': 'forbidden'}), 403

    student = user.student_profile
    if not student:
        return jsonify({'success': False, 'message': 'Student profile not found', 'error': 'profile_missing'}), 404

    try:
        records = Attendance.query.filter_by(student_id=student.id).all()
        return jsonify({
            'success': True,
            'data': [r.to_dict() for r in records]
        }), 200
    except Exception as e:
        return jsonify({'success': False, 'message': 'Failed to fetch attendance logs', 'error': str(e)}), 500


@student_bp.route('/dashboard/exams', methods=['GET'])
@jwt_required()
def get_student_exams():
    """Retrieve upcoming exams list for student's department."""
    user_id = int(get_jwt_identity())
    user = User.query.get(user_id)
    
    if not user or user.role != 'student':
        return jsonify({'success': False, 'message': 'Forbidden. Student access required.', 'error': 'forbidden'}), 403

    student = user.student_profile
    if not student:
        return jsonify({'success': False, 'message': 'Student profile not found', 'error': 'profile_missing'}), 404

    try:
        # Load active department specific or college-wide exam schedules
        exams = ExamNotification.query.filter(
            ExamNotification.exam_date >= datetime.utcnow(),
            (ExamNotification.department_id == student.department_id) | (ExamNotification.department_id.is_(None))
        ).order_by(ExamNotification.exam_date.asc()).all()
        
        return jsonify({
            'success': True,
            'data': [e.to_dict() for e in exams]
        }), 200
    except Exception as e:
        return jsonify({'success': False, 'message': 'Failed to load exam schedules', 'error': str(e)}), 500


@student_bp.route('/dashboard/placements', methods=['GET'])
@jwt_required()
def get_student_placements():
    """Retrieve upcoming and ongoing placement drives listing."""
    user_id = int(get_jwt_identity())
    user = User.query.get(user_id)
    
    if not user or user.role != 'student':
        return jsonify({'success': False, 'message': 'Forbidden. Student access required.', 'error': 'forbidden'}), 403

    try:
        # Load upcoming placement recruitment drives
        drives = PlacementDrive.query.filter(
            PlacementDrive.status != 'Completed'
        ).order_by(PlacementDrive.drive_date.asc()).all()
        
        return jsonify({
            'success': True,
            'data': [d.to_dict() for d in drives]
        }), 200
    except Exception as e:
        return jsonify({'success': False, 'message': 'Failed to load placement listings', 'error': str(e)}), 500


@student_bp.route('/dashboard/grievances', methods=['GET'])
@jwt_required()
def get_student_grievances():
    """Retrieve the student's logged grievances only (isolated)."""
    user_id = int(get_jwt_identity())
    user = User.query.get(user_id)
    
    if not user or user.role != 'student':
        return jsonify({'success': False, 'message': 'Forbidden. Student access required.', 'error': 'forbidden'}), 403

    student = user.student_profile
    if not student:
        return jsonify({'success': False, 'message': 'Student profile not found', 'error': 'profile_missing'}), 404

    try:
        complaints = Complaint.query.filter_by(student_id=student.id).order_by(Complaint.created_at.desc()).all()
        return jsonify({
            'success': True,
            'data': [c.to_dict() for c in complaints]
        }), 200
    except Exception as e:
        return jsonify({'success': False, 'message': 'Failed to load user grievances', 'error': str(e)}), 500


@student_bp.route('/dashboard/notifications', methods=['GET'])
@jwt_required()
def get_student_notifications():
    """Retrieve the student's personal notification alerts inbox (isolated)."""
    user_id = int(get_jwt_identity())
    user = User.query.get(user_id)
    
    if not user or user.role != 'student':
        return jsonify({'success': False, 'message': 'Forbidden. Student access required.', 'error': 'forbidden'}), 403

    try:
        notifications = Notification.query.filter_by(user_id=user.id).order_by(Notification.created_at.desc()).all()
        return jsonify({
            'success': True,
            'data': [n.to_dict() for n in notifications]
        }), 200
    except Exception as e:
        return jsonify({'success': False, 'message': 'Failed to load inbox alerts', 'error': str(e)}), 500

@student_bp.route('/dashboard/attendance/details', methods=['GET'])
@jwt_required()
def get_student_attendance_details():
    """Retrieve detailed day-by-day session-wise attendance log sheet for the logged-in student (isolated)."""
    user_id = int(get_jwt_identity())
    user = User.query.get(user_id)
    
    if not user or user.role != 'student':
        return jsonify({'success': False, 'message': 'Forbidden. Student access required.', 'error': 'forbidden'}), 403

    student = user.student_profile
    if not student:
        return jsonify({'success': False, 'message': 'Student profile not found', 'error': 'profile_missing'}), 404

    try:
        from app.models.attendance import AttendanceRecord, AttendanceSession, Subject
        records = AttendanceRecord.query.join(AttendanceSession).join(Subject).filter(
            AttendanceRecord.student_id == student.id
        ).order_by(AttendanceSession.date.desc(), AttendanceSession.session.desc()).all()
        
        details = []
        for r in records:
            details.append({
                'id': r.id,
                'date': r.session.date,
                'subject_name': r.session.subject.name if r.session.subject else 'General',
                'session': r.session.session,
                'section': r.session.section,
                'status': r.status
            })
            
        return jsonify({
            'success': True,
            'data': details
        }), 200
    except Exception as e:
        return jsonify({'success': False, 'message': 'Failed to load attendance session details', 'error': str(e)}), 500
