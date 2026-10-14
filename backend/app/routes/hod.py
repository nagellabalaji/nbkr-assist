from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from app import db
from app.models.user import User, Staff, Student
from app.models.attendance import Attendance, Subject, FacultySubject, AttendanceSession
from app.models.complaint import Complaint, ComplaintAssignment, ComplaintHistory
from app.models.department import Department
import math

hod_bp = Blueprint('hod', __name__)

ATTENDANCE_ELIGIBILITY_THRESHOLD = 0.75

def get_hod_context():
    """Derives authenticated HOD user and staff profile from JWT identity safely."""
    user_id = int(get_jwt_identity())
    user = User.query.get(user_id)
    if not user or user.role != 'hod':
        return None, None
    staff_profile = user.staff_profile
    if not staff_profile:
        return None, None
    return user, staff_profile

def calculate_classes_needed(present, total):
    """
    Calculates the minimum additional classes needed to reach 75% attendance.
    Correctly handles edge cases like 0/0 and 0/10.
    """
    if total == 0:
        return 0
    if (present / total) >= ATTENDANCE_ELIGIBILITY_THRESHOLD:
        return 0
    
    # Mathematical derivation: (P + x) / (T + x) >= 0.75 -> 4(P + x) >= 3(T + x) -> x >= 3T - 4P
    x = 3 * total - 4 * present
    x = max(0, x)
    
    # Double-check mathematically before returning
    while (present + x) / (total + x) < ATTENDANCE_ELIGIBILITY_THRESHOLD:
        x += 1
        
    return x

@hod_bp.route('/dashboard', methods=['GET'])
@jwt_required()
def get_hod_dashboard():
    user, hod = get_hod_context()
    if not hod:
        return jsonify({'success': False, 'message': 'Forbidden. HOD access required.', 'error': 'forbidden'}), 403

    try:
        # 1. Total Students in Department
        total_students = Student.query.filter_by(department_id=hod.department_id).count()

        # 2. Faculty Count in Department
        faculty_count = Staff.query.filter_by(department_id=hod.department_id).join(User).filter(User.role == 'faculty').count()

        # 3. Grievances in Department
        open_grievances = Complaint.query.filter(
            db.func.lower(Complaint.suggested_department) == hod.department.lower(),
            Complaint.status.not_in(['Resolved', 'Closed', 'Rejected'])
        ).count()

        critical_grievances = Complaint.query.filter(
            db.func.lower(Complaint.suggested_department) == hod.department.lower(),
            Complaint.status.not_in(['Resolved', 'Closed', 'Rejected']),
            Complaint.ai_priority.in_(['Critical', 'Urgent', 'High'])
        ).count()

        sla_breaches = Complaint.query.filter(
            db.func.lower(Complaint.suggested_department) == hod.department.lower(),
            Complaint.status.not_in(['Resolved', 'Closed', 'Rejected']),
            Complaint.sla_deadline < db.func.now()
        ).count()

        resolved_grievances = Complaint.query.filter(
            db.func.lower(Complaint.suggested_department) == hod.department.lower(),
            Complaint.status.in_(['Resolved', 'Closed'])
        ).count()

        # 4. Average Attendance
        avg_att = 0.0
        students_in_dept = Student.query.filter_by(department_id=hod.department_id).all()
        student_ids = [s.id for s in students_in_dept]
        
        shortage_count = 0
        if student_ids:
            # Average cumulative percentage
            summary_stats = db.session.query(db.func.avg(Attendance.percentage)).filter(
                Attendance.student_id.in_(student_ids)
            ).scalar()
            if summary_stats is not None:
                avg_att = round(float(summary_stats), 1)

            # Count of students with overall shortage (< 75%)
            shortages = db.session.query(Attendance.student_id).filter(
                Attendance.student_id.in_(student_ids)
            ).group_by(Attendance.student_id).having(db.func.avg(Attendance.percentage) < 75.0).all()
            shortage_count = len(shortages)

        return jsonify({
            'success': True,
            'data': {
                'totalStudents': total_students,
                'facultyCount': faculty_count,
                'openGrievances': open_grievances,
                'criticalGrievances': critical_grievances,
                'slaBreaches': sla_breaches,
                'resolvedGrievances': resolved_grievances,
                'averageAttendance': f"{avg_att}%",
                'attendanceShortage': shortage_count
            }
        }), 200

    except Exception as e:
        return jsonify({'success': False, 'message': 'Failed to compile HOD dashboard', 'error': str(e)}), 500

@hod_bp.route('/overview', methods=['GET'])
@jwt_required()
def get_hod_overview():
    user, hod = get_hod_context()
    if not hod:
        return jsonify({'success': False, 'message': 'Forbidden. HOD access required.', 'error': 'forbidden'}), 403

    dept = Department.query.get(hod.department_id)
    if not dept:
        return jsonify({'success': False, 'message': 'Department not found.', 'error': 'not_found'}), 404

    faculty_count = Staff.query.filter_by(department_id=hod.department_id).join(User).filter(User.role == 'faculty').count()
    students_count = Student.query.filter_by(department_id=hod.department_id).count()
    subjects_count = Subject.query.filter_by(department_id=hod.department_id).count()

    return jsonify({
        'success': True,
        'data': {
            'department_name': dept.name,
            'department_code': dept.code,
            'hod_name': user.username.replace('_', ' ').title(),
            'number_of_faculty': faculty_count,
            'number_of_students': students_count,
            'number_of_subjects': subjects_count
        }
    }), 200

@hod_bp.route('/students', methods=['GET'])
@jwt_required()
def get_hod_students():
    user, hod = get_hod_context()
    if not hod:
        return jsonify({'success': False, 'message': 'Forbidden. HOD access required.', 'error': 'forbidden'}), 403

    filter_year = request.args.get('year')
    filter_sem = request.args.get('semester')
    filter_sec = request.args.get('section')
    filter_shortage = request.args.get('attendance_shortage', 'false').lower() == 'true'
    search_query = request.args.get('search', '').strip().lower()

    # Enforce department isolation
    query = Student.query.filter_by(department_id=hod.department_id)

    if filter_year:
        query = query.filter(Student.year == filter_year)
    if filter_sem:
        query = query.filter(Student.semester == filter_sem)
    if filter_sec:
        query = query.filter(Student.section == filter_sec)

    students = query.all()
    data = []

    for s in students:
        if search_query:
            username = s.user.username.lower() if s.user else ""
            if search_query not in s.roll_no.lower() and search_query not in username:
                continue

        # Calculate average attendance percentage
        summary_recs = Attendance.query.filter_by(student_id=s.id).all()
        avg_pct = 0.0
        if summary_recs:
            avg_pct = sum(a.percentage for a in summary_recs) / len(summary_recs)

        if filter_shortage and avg_pct >= 75.0:
            continue

        data.append({
            'id': s.id,
            'roll_no': s.roll_no,
            'name': s.user.username.replace('_', ' ').title() if s.user else "Student",
            'department': s.department,
            'year': s.year,
            'semester': s.semester,
            'section': s.section,
            'attendance_percentage': round(avg_pct, 1),
            'hostel_status': s.hostel_status,
            'transport_status': s.transport_status
        })

    return jsonify({
        'success': True,
        'data': data
    }), 200

@hod_bp.route('/faculty', methods=['GET'])
@jwt_required()
def get_hod_faculty():
    user, hod = get_hod_context()
    if not hod:
        return jsonify({'success': False, 'message': 'Forbidden. HOD access required.', 'error': 'forbidden'}), 403

    # Enforce department isolation
    faculty_list = Staff.query.filter_by(department_id=hod.department_id).join(User).filter(User.role == 'faculty').all()
    
    data = []
    for f in faculty_list:
        subjects_mapped = []
        for fs in f.faculty_subjects:
            subjects_mapped.append(f"{fs.subject.name} (Sec {fs.section})")

        data.append({
            'id': f.id,
            'employee_id': f.employee_id or "Not Assigned",
            'name': f.user.username.replace('_', ' ').title(),
            'designation': f.designation or "Lecturer",
            'specialization': f.specialization,
            'phone': f.phone or "N/A",
            'email': f.user.email,
            'is_available': f.is_available,
            'subjects': subjects_mapped
        })

    return jsonify({
        'success': True,
        'data': data
    }), 200

@hod_bp.route('/faculty/assign-subject', methods=['POST'])
@jwt_required()
def assign_faculty_subject():
    user, hod = get_hod_context()
    if not hod:
        return jsonify({'success': False, 'message': 'Forbidden. HOD access required.', 'error': 'forbidden'}), 403

    data = request.get_json() or {}
    faculty_id = data.get('faculty_id')
    subject_id = data.get('subject_id')
    section_name = data.get('section', 'A')

    if not (faculty_id and subject_id):
        return jsonify({'success': False, 'message': 'Faculty ID and Subject ID are required.', 'error': 'missing_fields'}), 400

    faculty = Staff.query.get(faculty_id) or Staff.query.filter_by(user_id=faculty_id).first()
    subject = Subject.query.get(subject_id)

    if not faculty or not subject:
        return jsonify({'success': False, 'message': 'Faculty or subject not found.', 'error': 'not_found'}), 404

    # 1. Enforce HOD department isolation check
    if faculty.department_id != hod.department_id or subject.department_id != hod.department_id:
        return jsonify({'success': False, 'message': 'Forbidden. Department isolation breach.', 'error': 'forbidden'}), 403

    # 2. Check if already exists
    existing = FacultySubject.query.filter_by(faculty_id=faculty.id, subject_id=subject.id, section=section_name).first()
    if existing:
        return jsonify({'success': False, 'message': 'Subject section already mapped to this faculty member.', 'error': 'duplicate_mapping'}), 400

    try:
        new_mapping = FacultySubject(
            faculty_id=faculty.id,
            subject_id=subject.id,
            section=section_name
        )
        db.session.add(new_mapping)
        db.session.commit()
        return jsonify({
            'success': True,
            'message': 'Subject workload mapped to faculty successfully',
            'data': new_mapping.to_dict()
        }), 201
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'message': 'Mapping failed', 'error': str(e)}), 500

@hod_bp.route('/attendance', methods=['GET'])
@jwt_required()
def get_hod_attendance_analytics():
    user, hod = get_hod_context()
    if not hod:
        return jsonify({'success': False, 'message': 'Forbidden. HOD access required.', 'error': 'forbidden'}), 403

    # Enforce department isolation
    students = Student.query.filter_by(department_id=hod.department_id).all()
    student_ids = [s.id for s in students]

    if not student_ids:
        return jsonify({'success': True, 'data': {'shortages': []}}), 200

    # Fetch cumulative summaries for department students
    attendance_data = Attendance.query.filter(Attendance.student_id.in_(student_ids)).all()
    
    shortages_list = []
    for a in attendance_data:
        if a.percentage < 75.0:
            student = Student.query.get(a.student_id)
            classes_needed = calculate_classes_needed(a.present, a.total_classes)
            shortages_list.append({
                'student_name': student.user.username.replace('_', ' ').title() if student and student.user else "Student",
                'roll_no': student.roll_no if student else "N/A",
                'subject': a.subject,
                'total_classes': a.total_classes,
                'present': a.present,
                'absent': a.absent,
                'percentage': round(a.percentage, 1),
                'classes_required_to_clear': classes_needed
            })

    return jsonify({
        'success': True,
        'data': {
            'shortages': shortages_list
        }
    }), 200

@hod_bp.route('/grievances', methods=['GET'])
@jwt_required()
def get_hod_grievances():
    user, hod = get_hod_context()
    if not hod:
        return jsonify({'success': False, 'message': 'Forbidden. HOD access required.', 'error': 'forbidden'}), 403

    # Enforce department isolation: HOD only sees department specific tickets
    query = Complaint.query.filter(db.func.lower(Complaint.suggested_department) == hod.department.lower())
    
    grievances = query.all()
    return jsonify({
        'success': True,
        'data': [g.to_dict() for g in grievances]
    }), 200

@hod_bp.route('/subjects', methods=['GET'])
@jwt_required()
def get_hod_subjects():
    user, hod = get_hod_context()
    if not hod:
        return jsonify({'success': False, 'message': 'Forbidden. HOD access required.', 'error': 'forbidden'}), 403

    subjects = Subject.query.filter_by(department_id=hod.department_id).all()
    return jsonify({
        'success': True,
        'data': [s.to_dict() for s in subjects]
    }), 200
