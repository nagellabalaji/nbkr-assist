from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity, get_jwt
from app import db
from app.models.user import User, Staff, Student
from app.models.attendance import Attendance, Subject, FacultySubject, AttendanceSession, AttendanceRecord
from app.models.complaint import Complaint
from app.services.notification_service import notify_attendance_shortage
from datetime import datetime

faculty_bp = Blueprint('faculty', __name__)

# Configurable attendance shortage threshold constant
ATTENDANCE_ELIGIBILITY_THRESHOLD = 75.0

def get_faculty_context():
    """Derives authenticated faculty profile from JWT identity context safely."""
    user_id = int(get_jwt_identity())
    user = User.query.get(user_id)
    if not user or user.role != 'faculty':
        return None, None
    staff_profile = user.staff_profile
    if not staff_profile:
        return None, None
    return user, staff_profile

def get_authorized_students(faculty, subject_id=None, section=None):
    """
    Returns lists of student records authorized under the faculty's subjects/sections workloads.
    Matches department, semester, year, and section.
    """
    students_query = Student.query.filter_by(department_id=faculty.department_id)
    
    # Filter by faculty subject mappings
    mappings = FacultySubject.query.filter_by(faculty_id=faculty.id)
    if subject_id:
        mappings = mappings.filter_by(subject_id=subject_id)
    if section:
        mappings = mappings.filter_by(section=section)
        
    mappings_list = mappings.all()
    if not mappings_list:
        return []

    authorized_students = []
    for fs in mappings_list:
        sub = fs.subject
        # Query students matching subject's target semester, year, and section
        matched = Student.query.filter_by(
            department_id=faculty.department_id,
            semester=sub.semester,
            year=sub.year,
            section=fs.section
        ).all()
        authorized_students.extend(matched)
        
    # De-duplicate list
    seen_ids = set()
    unique_students = []
    for s in authorized_students:
        if s.id not in seen_ids:
            seen_ids.add(s.id)
            unique_students.append(s)
            
    return unique_students

def sync_cumulative_attendance(student_id, subject_id):
    """
    Recalculates cumulative class stats for a student and updates the legacy attendance table.
    Ensures legacy attendance features remain in sync with daily session marks.
    """
    subject = Subject.query.get(subject_id)
    if not subject:
        return
        
    # Fetch all records of the student for this subject across all sessions
    records = AttendanceRecord.query.join(AttendanceSession).filter(
        AttendanceRecord.student_id == student_id,
        AttendanceSession.subject_id == subject_id
    ).all()
    
    total = len(records)
    present = sum(1 for r in records if r.status == 'Present')
    absent = sum(1 for r in records if r.status == 'Absent')
    percentage = (present / total) * 100.0 if total > 0 else 0.0

    # Sync with legacy summary table (matches subject name string)
    summary = Attendance.query.filter_by(student_id=student_id, subject=subject.name).first()
    if not summary:
        summary = Attendance(
            student_id=student_id,
            subject=subject.name,
            total_classes=total,
            present=present,
            absent=absent,
            percentage=percentage
        )
        db.session.add(summary)
    else:
        summary.total_classes = total
        summary.present = present
        summary.absent = absent
        summary.percentage = percentage
        
    db.session.commit()

    # Trigger attendance shortage warning if student's cumulative average drops below 75%
    all_summaries = Attendance.query.filter_by(student_id=student_id).all()
    total_conducted = sum(s.total_classes for s in all_summaries)
    total_present = sum(s.present for s in all_summaries)
    if total_conducted > 0:
        overall_pct = (total_present / total_conducted) * 100.0
        if overall_pct < 75.0:
            student_profile = Student.query.get(student_id)
            if student_profile:
                notify_attendance_shortage(student_profile, round(overall_pct, 2))

@faculty_bp.route('/dashboard', methods=['GET'])
@jwt_required()
def get_faculty_dashboard():
    user, faculty = get_faculty_context()
    if not faculty:
        return jsonify({'success': False, 'message': 'Forbidden. Faculty access required.', 'error': 'forbidden'}), 403

    try:
        # Grievance counters
        assigned = Complaint.query.filter_by(assigned_staff_id=faculty.id).count()
        open_count = Complaint.query.filter(
            Complaint.assigned_staff_id == faculty.id,
            Complaint.status.not_in(['Resolved', 'Closed', 'Rejected'])
        ).count()
        in_progress = Complaint.query.filter_by(assigned_staff_id=faculty.id, status='In Progress').count()
        resolved = Complaint.query.filter(
            Complaint.assigned_staff_id == faculty.id,
            Complaint.status.in_(['Resolved', 'Closed'])
        ).count()

        # Attendance stats
        today_str = datetime.utcnow().date()
        today_classes = AttendanceSession.query.filter_by(faculty_id=faculty.id, date=today_str).count()
        
        # Enrolled students count
        students_list = get_authorized_students(faculty)
        total_students = len(students_list)

        # Average attendance percentage
        # Query legacy attendance table for subjects taught by this faculty
        assigned_subjects = [fs.subject.name for fs in faculty.faculty_subjects]
        avg_percentage = "No data available"
        if assigned_subjects and students_list:
            student_ids = [s.id for s in students_list]
            summary_stats = db.session.query(db.func.avg(Attendance.percentage)).filter(
                Attendance.student_id.in_(student_ids),
                Attendance.subject.in_(assigned_subjects)
            ).scalar()
            if summary_stats is not None:
                avg_percentage = f"{round(float(summary_stats), 1)}%"

        return jsonify({
            'success': True,
            'data': {
                'assignedGrievances': assigned,
                'openGrievances': open_count,
                'inProgressGrievances': in_progress,
                'resolvedGrievances': resolved,
                'todayClasses': today_classes,
                'totalStudents': total_students,
                'averageAttendance': avg_percentage
            }
        }), 200

    except Exception as e:
        return jsonify({'success': False, 'message': 'Failed to compile faculty dashboard', 'error': str(e)}), 500

@faculty_bp.route('/profile', methods=['GET'])
@jwt_required()
def get_faculty_profile():
    user, faculty = get_faculty_context()
    if not faculty:
        return jsonify({'success': False, 'message': 'Forbidden. Faculty access required.', 'error': 'forbidden'}), 403

    subjects_taught = []
    for fs in faculty.faculty_subjects:
        subjects_taught.append({
            'subject_id': fs.subject_id,
            'name': fs.subject.name,
            'code': fs.subject.code,
            'section': fs.section,
            'semester': fs.subject.semester,
            'year': fs.subject.year
        })

    return jsonify({
        'success': True,
        'data': {
            'id': faculty.id,
            'username': user.username,
            'name': user.username.replace('_', ' ').title(),
            'email': user.email,
            'employee_id': faculty.employee_id or "Not Assigned",
            'designation': faculty.designation or "Lecturer",
            'phone': faculty.phone or "N/A",
            'department': faculty.department,
            'academic_year': faculty.academic_year or "2026",
            'subjects': subjects_taught
        }
    }), 200

@faculty_bp.route('/subjects', methods=['GET'])
@jwt_required()
def get_faculty_subjects():
    user, faculty = get_faculty_context()
    if not faculty:
        return jsonify({'success': False, 'message': 'Forbidden. Faculty access required.', 'error': 'forbidden'}), 403

    mappings = FacultySubject.query.filter_by(faculty_id=faculty.id).all()
    data = []
    for fs in mappings:
        data.append({
            'id': fs.id,
            'subject_id': fs.subject_id,
            'name': fs.subject.name,
            'code': fs.subject.code,
            'section': fs.section,
            'credits': fs.subject.credits,
            'semester': fs.subject.semester,
            'year': fs.subject.year
        })

    return jsonify({
        'success': True,
        'data': data
    }), 200

@faculty_bp.route('/students', methods=['GET'])
@jwt_required()
def get_faculty_students():
    user, faculty = get_faculty_context()
    if not faculty:
        return jsonify({'success': False, 'message': 'Forbidden. Faculty access required.', 'error': 'forbidden'}), 403

    # Filters
    filter_year = request.args.get('year')
    filter_sem = request.args.get('semester')
    filter_sec = request.args.get('section')
    filter_status = request.args.get('attendance_status') # 'Shortage', 'Eligible'
    search_query = request.args.get('search', '').strip().lower()

    # Load authorized students based on faculty workloads
    students = get_authorized_students(faculty)
    
    data = []
    subjects_list = [fs.subject.name for fs in faculty.faculty_subjects]

    for s in students:
        # Apply filters in memory for precise authorization enforcement
        if filter_year and s.year != filter_year:
            continue
        if filter_sem and s.semester != filter_sem:
            continue
        if filter_sec and s.section != filter_sec:
            continue
            
        if search_query:
            username_match = s.user.username.lower() if s.user else ""
            if search_query not in s.roll_no.lower() and search_query not in username_match:
                continue

        # Get average attendance for the subjects taught by this faculty
        attendance_records = Attendance.query.filter(
            Attendance.student_id == s.id,
            Attendance.subject.in_(subjects_list)
        ).all()
        
        avg_pct = 0.0
        if attendance_records:
            avg_pct = sum(a.percentage for a in attendance_records) / len(attendance_records)
        
        status_eligible = avg_pct >= ATTENDANCE_ELIGIBILITY_THRESHOLD
        status_label = 'Eligible' if status_eligible else 'Shortage'
        
        if filter_status and filter_status != status_label:
            continue

        data.append({
            'id': s.id,
            'roll_no': s.roll_no,
            'name': s.user.username.replace('_', ' ').title() if s.user else "Student",
            'department': s.department,
            'program': s.program,
            'year': s.year,
            'section': s.section,
            'semester': s.semester,
            'attendance_percentage': round(avg_pct, 1),
            'status': status_label
        })

    return jsonify({
        'success': True,
        'data': data
    }), 200

@faculty_bp.route('/attendance', methods=['GET'])
@jwt_required()
def get_attendance_sessions():
    user, faculty = get_faculty_context()
    if not faculty:
        return jsonify({'success': False, 'message': 'Forbidden. Faculty access required.', 'error': 'forbidden'}), 403

    sessions = AttendanceSession.query.filter_by(faculty_id=faculty.id).order_by(AttendanceSession.date.desc()).all()
    data = []
    for s in sessions:
        total_marked = len(s.records)
        present_count = sum(1 for r in s.records if r.status == 'Present')
        data.append({
            'id': s.id,
            'subject_name': s.subject.name,
            'subject_code': s.subject.code,
            'date': s.date.isoformat(),
            'session': s.session,
            'section': s.section,
            'total_students': total_marked,
            'present': present_count,
            'absent': total_marked - present_count
        })

    return jsonify({
        'success': True,
        'data': data
    }), 200

@faculty_bp.route('/attendance', methods=['POST'])
@jwt_required()
def mark_attendance():
    """Marks a daily session's attendance. Server-side validates subjects and sections workloads."""
    user, faculty = get_faculty_context()
    if not faculty:
        return jsonify({'success': False, 'message': 'Forbidden. Faculty access required.', 'error': 'forbidden'}), 403

    data = request.get_json() or {}
    subject_id = data.get('subject_id')
    date_str = data.get('date')
    session_name = data.get('session')
    section_name = data.get('section')
    records = data.get('records', [])

    if not (subject_id and date_str and session_name and section_name and records):
        return jsonify({'success': False, 'message': 'Missing parameters.', 'error': 'missing_fields'}), 400

    # 1. Strict workload verification: check if assigned to this faculty
    mapping = FacultySubject.query.filter_by(faculty_id=faculty.id, subject_id=subject_id, section=section_name).first()
    if not mapping:
        return jsonify({'success': False, 'message': 'Unauthorized section or subject assignment for this faculty', 'error': 'forbidden'}), 403

    try:
        class_date = datetime.strptime(date_str, "%Y-%m-%d").date()
    except ValueError:
        return jsonify({'success': False, 'message': 'Invalid date format (use YYYY-MM-DD)', 'error': 'invalid_date'}), 400

    # 2. Prevent duplicate session logs
    existing_session = AttendanceSession.query.filter_by(
        faculty_id=faculty.id,
        subject_id=subject_id,
        date=class_date,
        session=session_name,
        section=section_name
    ).first()
    
    if existing_session:
        return jsonify({'success': False, 'message': 'Attendance sheet already submitted for this session.', 'error': 'duplicate_session'}), 409

    try:
        # Create session
        new_session = AttendanceSession(
            faculty_id=faculty.id,
            subject_id=subject_id,
            date=class_date,
            session=session_name,
            section=section_name
        )
        db.session.add(new_session)
        db.session.commit() # Get session ID

        # Resolve student scope
        student_records = get_authorized_students(faculty, subject_id=subject_id, section=section_name)
        allowed_student_ids = set(s.id for s in student_records)

        for rec in records:
            student_id = int(rec.get('student_id'))
            status = rec.get('status')
            
            # Verify student authorization
            if student_id not in allowed_student_ids:
                # Rollback session creation
                db.session.delete(new_session)
                db.session.commit()
                return jsonify({'success': False, 'message': f'Unauthorized student ID {student_id} for this subject/section', 'error': 'forbidden'}), 403

            if status not in ['Present', 'Absent']:
                db.session.delete(new_session)
                db.session.commit()
                return jsonify({'success': False, 'message': 'Status must be Present or Absent', 'error': 'invalid_status'}), 400

            db.session.add(AttendanceRecord(
                session_id=new_session.id,
                student_id=student_id,
                status=status,
                created_by_id=user.id,
                updated_by_id=user.id
            ))
            
        db.session.commit()

        # Update cumulative summary tables
        for rec in records:
            sync_cumulative_attendance(int(rec.get('student_id')), subject_id)

        return jsonify({
            'success': True,
            'message': 'Attendance registered successfully'
        }), 201

    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'message': 'Database error occurred', 'error': str(e)}), 500

@faculty_bp.route('/attendance/<int:session_id>', methods=['PUT'])
@jwt_required()
def edit_attendance(session_id):
    """Allows faculty members to adjust recorded marks in their allocated sessions (with server-side audits)."""
    user, faculty = get_faculty_context()
    if not faculty:
        return jsonify({'success': False, 'message': 'Forbidden. Faculty access required.', 'error': 'forbidden'}), 403

    session = AttendanceSession.query.get(session_id)
    if not session:
        return jsonify({'success': False, 'message': 'Session not found', 'error': 'not_found'}), 404

    # Verify session owner
    if session.faculty_id != faculty.id:
        return jsonify({'success': False, 'message': 'Unauthorized. You did not record this session.', 'error': 'forbidden'}), 403

    data = request.get_json() or {}
    records = data.get('records', [])

    if not records:
        return jsonify({'success': False, 'message': 'Records parameter required', 'error': 'missing_records'}), 400

    try:
        for rec in records:
            student_id = int(rec.get('student_id'))
            status = rec.get('status')
            
            if status not in ['Present', 'Absent']:
                return jsonify({'success': False, 'message': 'Status must be Present or Absent', 'error': 'invalid_status'}), 400

            record = AttendanceRecord.query.filter_by(session_id=session.id, student_id=student_id).first()
            if record:
                record.status = status
                record.updated_by_id = user.id
                record.updated_at = datetime.utcnow()
            else:
                db.session.add(AttendanceRecord(
                    session_id=session.id,
                    student_id=student_id,
                    status=status,
                    created_by_id=user.id,
                    updated_by_id=user.id
                ))
                
        db.session.commit()

        # Recalculate summary tables
        for rec in records:
            sync_cumulative_attendance(int(rec.get('student_id')), session.subject_id)

        return jsonify({
            'success': True,
            'message': 'Attendance updated successfully'
        }), 200

    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'message': 'Failed to edit records', 'error': str(e)}), 500

@faculty_bp.route('/grievances', methods=['GET'])
@jwt_required()
def get_faculty_grievances():
    user, faculty = get_faculty_context()
    if not faculty:
        return jsonify({'success': False, 'message': 'Forbidden. Faculty access required.', 'error': 'forbidden'}), 403

    # Faculty can view:
    # 1. Assigned to them directly
    # 2. Within their department (if category or POLICY permits, e.g. CSE departmental academic grievances)
    query = Complaint.query.filter(
        (Complaint.assigned_staff_id == faculty.id) |
        (db.func.lower(Complaint.suggested_department) == faculty.department.lower())
    )
    
    grievances = query.all()
    return jsonify({
        'success': True,
        'data': [g.to_dict() for g in grievances]
    }), 200
