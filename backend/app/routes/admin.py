from flask import Blueprint, jsonify, request
from flask_jwt_extended import jwt_required, get_jwt, get_jwt_identity
from app import db
from app.models.user import User, Staff, Student
from app.models.complaint import Complaint, ComplaintCategory
from app.models.log_feedback import Feedback
from sqlalchemy import func
from datetime import datetime, timedelta

admin_bp = Blueprint('admin', __name__)

@admin_bp.route('/analytics', methods=['GET'])
@jwt_required()
def get_analytics():
    """Aggregates system-wide analytics metrics for the Admin Dashboard."""
    claims = get_jwt()
    if claims.get('role') != 'super_admin':
        return jsonify({'success': False, 'message': 'Forbidden. Admin access required.', 'error': 'forbidden'}), 403

    try:
        # 1. Total counts by status
        total_complaints = Complaint.query.count()
        pending = Complaint.query.filter(Complaint.status.in_(['Submitted', 'Under Review', 'Assigned', 'In Progress', 'Reopened'])).count()
        in_progress = Complaint.query.filter_by(status='In Progress').count()
        resolved = Complaint.query.filter(Complaint.status.in_(['Resolved', 'Closed'])).count()
        urgent_high = Complaint.query.filter(Complaint.ai_priority.in_(['High', 'Urgent'])).count()

        # 2. Average Resolution Time (in Hours)
        resolved_tickets = Complaint.query.filter(Complaint.resolved_at.isnot(None)).all()
        avg_res_hours = 0.0
        if resolved_tickets:
            total_duration_seconds = 0
            for ticket in resolved_tickets:
                diff = ticket.resolved_at - ticket.created_at
                total_duration_seconds += diff.total_seconds()
            
            avg_res_hours = round((total_duration_seconds / len(resolved_tickets)) / 3600.0, 1)

        # 3. Complaints by Category
        categories_data = db.session.query(
            ComplaintCategory.name,
            func.count(Complaint.id)
        ).join(Complaint, Complaint.category_id == ComplaintCategory.id, isouter=True)\
         .group_by(ComplaintCategory.name).all()
        
        category_chart = [{'category': name, 'count': count} for name, count in categories_data]

        # 4. Complaints by Status
        status_data = db.session.query(
            Complaint.status,
            func.count(Complaint.id)
        ).group_by(Complaint.status).all()
        
        status_chart = [{'status': status, 'count': count} for status, count in status_data]

        # 5. Complaints by Priority
        priority_data = db.session.query(
            Complaint.ai_priority,
            func.count(Complaint.id)
        ).group_by(Complaint.ai_priority).all()
        
        priority_chart = [{'priority': priority, 'count': count} for priority, count in priority_data]

        # 6. Complaints Trend (Last 7 Days)
        today = datetime.utcnow()
        trend_chart = []
        for i in range(6, -1, -1):
            date_val = today - timedelta(days=i)
            date_str = date_val.strftime('%Y-%m-%d')
            
            # Count complaints created on this date
            day_count = Complaint.query.filter(
                func.date(Complaint.created_at) == date_val.date()
            ).count()
            
            trend_chart.append({'date': date_str, 'count': day_count})

        # 7. Customer Satisfaction Rating (Average star rating)
        avg_feedback_rating = db.session.query(func.avg(Feedback.rating)).scalar()
        avg_rating = round(float(avg_feedback_rating), 1) if avg_feedback_rating else 0.0

        return jsonify({
            'success': True,
            'message': 'Analytics data computed successfully',
            'data': {
                'metrics': {
                    'totalComplaints': total_complaints,
                    'pendingComplaints': pending,
                    'inProgressComplaints': in_progress,
                    'resolvedComplaints': resolved,
                    'urgentHighComplaints': urgent_high,
                    'avgResolutionTimeHours': avg_res_hours,
                    'averageRating': avg_rating
                },
                'charts': {
                    'byCategory': category_chart,
                    'byStatus': status_chart,
                    'byPriority': priority_chart,
                    'trend': trend_chart
                }
            }
        }), 200

    except Exception as e:
        return jsonify({'success': False, 'message': 'Failed to compile metrics', 'error': str(e)}), 500


@admin_bp.route('/staff', methods=['GET'])
@jwt_required()
def get_staff_list():
    """Fetches a list of maintenance/academic staff for assignment selection. HOD sees department-only staff."""
    claims = get_jwt()
    role = claims.get('role')
    user_id = int(get_jwt_identity())
    
    if role not in ['super_admin', 'hod']:
        return jsonify({'success': False, 'message': 'Forbidden. Admin or HOD access required.', 'error': 'forbidden'}), 403

    try:
        if role == 'super_admin':
            staff_members = Staff.query.all()
        else:
            # HOD role filters staff in their same department
            user = User.query.get(user_id)
            if user and user.staff_profile:
                staff_members = Staff.query.filter_by(department=user.staff_profile.department).all()
            else:
                staff_members = []
                
        return jsonify({
            'success': True,
            'data': [s.to_dict() for s in staff_members]
        }), 200
    except Exception as e:
        return jsonify({'success': False, 'message': 'Failed to fetch staff list', 'error': str(e)}), 500


@admin_bp.route('/faculty', methods=['GET'])
@jwt_required()
def get_faculty_list():
    """Fetches a list of faculty members (role='faculty' or 'hod') for assignment selection."""
    claims = get_jwt()
    role = claims.get('role')
    user_id = int(get_jwt_identity())
    
    if role not in ['super_admin', 'hod']:
        return jsonify({'success': False, 'message': 'Forbidden. Admin or HOD access required.', 'error': 'forbidden'}), 403

    try:
        query = Staff.query.join(User).filter(User.role.in_(['faculty', 'hod']))
        if role == 'hod':
            user = User.query.get(user_id)
            if user and user.staff_profile:
                query = query.filter(Staff.department == user.staff_profile.department)
            else:
                return jsonify({'success': True, 'data': []}), 200
                
        faculty_members = query.all()
        return jsonify({
            'success': True,
            'data': [s.to_dict() for s in faculty_members]
        }), 200
    except Exception as e:
        return jsonify({'success': False, 'message': 'Failed to fetch faculty list', 'error': str(e)}), 500


@admin_bp.route('/users', methods=['GET'])
@jwt_required()
def get_users_list():
    """Fetches a list of all students and staff members in the system."""
    claims = get_jwt()
    if claims.get('role') != 'super_admin':
        return jsonify({'success': False, 'message': 'Forbidden. Admin access required.', 'error': 'forbidden'}), 403

    try:
        users = User.query.filter(User.role != 'super_admin').order_by(User.id.desc()).all()
        users_list = []
        for u in users:
            profile = {}
            if u.role == 'student' and u.student_profile:
                profile = u.student_profile.to_dict()
            elif u.role in ['faculty', 'hod', 'exam_cell', 'placement_officer', 'hostel_admin', 'transport_admin', 'maintenance_staff', 'librarian'] and u.staff_profile:
                profile = u.staff_profile.to_dict()
            
            users_list.append({
                'id': u.id,
                'username': u.username,
                'email': u.email,
                'role': u.role,
                'status': u.status,
                'created_at': u.created_at.isoformat() if u.created_at else None,
                'profile': profile
            })

        return jsonify({
            'success': True,
            'data': users_list
        }), 200
    except Exception as e:
        return jsonify({'success': False, 'message': 'Failed to fetch user lists', 'error': str(e)}), 500


@admin_bp.route('/users/<int:id>/status', methods=['PUT'])
@jwt_required()
def update_user_status(id):
    """Admin-only status toggle (active/inactive) to freeze accounts."""
    claims = get_jwt()
    if claims.get('role') != 'super_admin':
        return jsonify({'success': False, 'message': 'Forbidden. Admin access required.', 'error': 'forbidden'}), 403

    user = User.query.get(id)
    if not user:
        return jsonify({'success': False, 'message': 'User not found', 'error': 'not_found'}), 404

    if user.role == 'super_admin':
         return jsonify({'success': False, 'message': 'Cannot modify Admin accounts', 'error': 'bad_request'}), 400

    data = request.get_json() or {}
    new_status = data.get('status')

    if new_status not in ['active', 'inactive']:
        return jsonify({'success': False, 'message': 'Status must be active or inactive', 'error': 'invalid_status'}), 400

    try:
        user.status = new_status
        db.session.commit()
        return jsonify({
            'success': True,
            'message': f'User {user.username} account status is now {new_status}',
            'data': user.to_dict()
        }), 200
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'message': 'Database error occurred', 'error': str(e)}), 500

@admin_bp.route('/analytics/overview', methods=['GET'])
@jwt_required()
def get_analytics_overview():
    """Aggregates high-level telemetry counts for the Admin Dashboard."""
    claims = get_jwt()
    if claims.get('role') not in ['super_admin', 'admin']:
        return jsonify({'success': False, 'message': 'Forbidden. Admin access required.', 'error': 'forbidden'}), 403

    try:
        from app.models.user import Student, Staff, User
        from app.models.complaint import Complaint
        from app.models.exam import ExamNotification
        from app.models.placement import PlacementDrive, PlacementApplication
        from app.models.hostel import HostelRequest
        from app.models.transport import TransportRequest
        from app.models.library import LibraryRequest
        from app.models.log_feedback import Notification

        total_students = Student.query.count()
        total_staff = Staff.query.count()
        total_admins = User.query.filter(User.role.in_(['super_admin', 'admin', 'hostel_admin', 'transport_admin', 'librarian', 'exam_cell', 'placement_officer'])).count()
        active_students = User.query.filter_by(role='student', status='active').count()

        open_grievances = Complaint.query.filter(Complaint.status.notin_(['Resolved', 'Closed', 'Rejected'])).count()
        resolved_grievances = Complaint.query.filter(Complaint.status.in_(['Resolved', 'Closed'])).count()

        total_hostel = HostelRequest.query.count()
        total_transport = TransportRequest.query.count()
        total_library = LibraryRequest.query.count()

        active_placements = PlacementDrive.query.filter_by(status='Ongoing').count()
        placement_apps = PlacementApplication.query.count()
        selected_candidates = PlacementApplication.query.filter_by(status='selected').count()

        total_exams = ExamNotification.query.count()
        unread_notifications = Notification.query.filter_by(is_read=False).count()

        return jsonify({
            'success': True,
            'data': {
                'total_students': total_students,
                'total_staff': total_staff,
                'total_admins': total_admins,
                'active_students': active_students,
                'open_grievances': open_grievances,
                'resolved_grievances': resolved_grievances,
                'total_hostel': total_hostel,
                'total_transport': total_transport,
                'total_library': total_library,
                'active_placements': active_placements,
                'placement_applications': placement_apps,
                'selected_candidates': selected_candidates,
                'total_exams': total_exams,
                'unread_notifications': unread_notifications
            }
        }), 200
    except Exception as e:
        return jsonify({'success': False, 'message': 'Failed to load overview analytics', 'error': str(e)}), 500

@admin_bp.route('/analytics/attendance', methods=['GET'])
@jwt_required()
def get_analytics_attendance():
    """Computes course attendance percentage benchmarks and shortage telemetry."""
    claims = get_jwt()
    if claims.get('role') not in ['super_admin', 'admin']:
        return jsonify({'success': False, 'message': 'Forbidden. Admin access required.', 'error': 'forbidden'}), 403

    try:
        from app.models.attendance import Attendance
        from app.models.user import Student
        from app.models.department import Department

        # Overall average attendance across all summaries
        avg_attendance_raw = db.session.query(func.avg(Attendance.percentage)).scalar()
        avg_attendance = round(float(avg_attendance_raw), 2) if avg_attendance_raw else 0.0

        # Department-wise average attendance
        dept_avgs = db.session.query(
            Department.code,
            func.avg(Attendance.percentage)
        ).join(Student, Student.department_id == Department.id)\
         .join(Attendance, Attendance.student_id == Student.id)\
         .group_by(Department.code).all()
        
        department_chart = [{'department': code, 'average': round(float(avg), 2)} for code, avg in dept_avgs]

        # Shortage counts: students whose overall cumulative average across all their courses is < 75%
        student_averages = db.session.query(
            Attendance.student_id,
            func.avg(Attendance.percentage).label('avg_pct')
        ).group_by(Attendance.student_id).all()
        
        students_shortage = sum(1 for sid, avg_pct in student_averages if avg_pct < 75.0)
        students_eligible = sum(1 for sid, avg_pct in student_averages if avg_pct >= 75.0)

        dist_ranges = {
            'below_50': 0,
            '50_to_75': 0,
            'above_75': 0
        }
        for sid, avg_pct in student_averages:
            if avg_pct < 50.0:
                dist_ranges['below_50'] += 1
            elif avg_pct < 75.0:
                dist_ranges['50_to_75'] += 1
            else:
                dist_ranges['above_75'] += 1

        distribution_chart = [
            {'range': 'Below 50%', 'count': dist_ranges['below_50']},
            {'range': '50% to 75%', 'count': dist_ranges['50_to_75']},
            {'range': 'Above 75%', 'count': dist_ranges['above_75']}
        ]

        return jsonify({
            'success': True,
            'data': {
                'average_attendance': avg_attendance,
                'students_shortage': students_shortage,
                'students_eligible': students_eligible,
                'by_department': department_chart,
                'distribution': distribution_chart
            }
        }), 200
    except Exception as e:
        return jsonify({'success': False, 'message': 'Failed to load attendance analytics', 'error': str(e)}), 500

@admin_bp.route('/analytics/modules', methods=['GET'])
@jwt_required()
def get_analytics_modules():
    """Computes module-specific activity summaries for hostel, transport, library, placements, and exams."""
    claims = get_jwt()
    if claims.get('role') not in ['super_admin', 'admin']:
        return jsonify({'success': False, 'message': 'Forbidden. Admin access required.', 'error': 'forbidden'}), 403

    try:
        from app.models.hostel import HostelRequest
        from app.models.transport import TransportRequest, TransportRoute
        from app.models.library import LibraryRequest
        from app.models.placement import PlacementDrive, PlacementApplication
        from app.models.exam import ExamNotification
        from app.models.department import Department

        # 1. Hostel request distribution
        hostel_status_counts = db.session.query(
            HostelRequest.status,
            func.count(HostelRequest.id)
        ).group_by(HostelRequest.status).all()
        hostel_chart = [{'status': status, 'count': count} for status, count in hostel_status_counts]

        # 2. Transport requests by status and routes usage
        transport_status_counts = db.session.query(
            TransportRequest.status,
            func.count(TransportRequest.id)
        ).group_by(TransportRequest.status).all()
        transport_chart = [{'status': status, 'count': count} for status, count in transport_status_counts]

        route_counts = db.session.query(
            TransportRoute.route_name,
            func.count(TransportRequest.id)
        ).join(TransportRequest, TransportRequest.route_id == TransportRoute.id)\
         .filter(TransportRequest.status == 'approved')\
         .group_by(TransportRoute.route_name).all()
        route_chart = [{'route': name, 'passengers': count} for name, count in route_counts]

        # 3. Library checkout activities
        total_active_loans = LibraryRequest.query.filter_by(status='approved', request_type='borrow').count()
        total_returns = LibraryRequest.query.filter_by(status='returned').count()
        overdue_loans = LibraryRequest.query.filter(
            LibraryRequest.status == 'approved',
            LibraryRequest.request_type == 'borrow',
            LibraryRequest.due_date < datetime.utcnow()
        ).count()

        # 4. Placements analytics
        placement_status_counts = db.session.query(
            PlacementApplication.status,
            func.count(PlacementApplication.id)
        ).group_by(PlacementApplication.status).all()
        placement_chart = [{'status': status, 'count': count} for status, count in placement_status_counts]

        # 5. Exam department-wise upcoming exams
        exam_dept_counts = db.session.query(
            Department.code,
            func.count(ExamNotification.id)
        ).join(ExamNotification, ExamNotification.department_id == Department.id)\
         .filter(ExamNotification.exam_date >= datetime.utcnow())\
         .group_by(Department.code).all()
        exam_chart = [{'department': code, 'exams': count} for code, count in exam_dept_counts]

        return jsonify({
            'success': True,
            'data': {
                'hostel': {
                    'status_distribution': hostel_chart
                },
                'transport': {
                    'status_distribution': transport_chart,
                    'route_passengers': route_chart
                },
                'library': {
                    'active_loans': total_active_loans,
                    'total_returns': total_returns,
                    'overdue_loans': overdue_loans
                },
                'placements': {
                    'status_distribution': placement_chart
                },
                'exams': {
                    'department_distribution': exam_chart
                }
            }
        }), 200
    except Exception as e:
        return jsonify({'success': False, 'message': 'Failed to load modules analytics', 'error': str(e)}), 500


@admin_bp.route('/reminders/trigger', methods=['POST'])
@jwt_required()
def trigger_reminders():
    claims = get_jwt()
    if claims.get('role') != 'super_admin':
        return jsonify({'success': False, 'message': 'Forbidden. Admin access required.', 'error': 'forbidden'}), 403

    from app.services.reminder_service import ReminderService
    res = ReminderService.check_and_send_reminders()
    return jsonify({
        'success': True,
        'message': 'Reminders processed successfully',
        'data': res
    }), 200
