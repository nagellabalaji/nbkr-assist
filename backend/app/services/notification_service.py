from app import db
from app.models.log_feedback import Notification
from datetime import datetime, timedelta

def create_notification(user_id, title, message, notif_type, complaint_id=None):
    """
    Creates an in-app notification in the database with duplication protection.
    """
    try:
        # Determine unique check: check if exact notification was sent to this user in the last 5 minutes
        recent_limit = datetime.utcnow() - timedelta(minutes=5)
        existing = Notification.query.filter(
            Notification.user_id == user_id,
            Notification.title == title,
            Notification.type == notif_type,
            Notification.complaint_id == complaint_id,
            Notification.created_at >= recent_limit
        ).first()
        if existing:
            return existing

        notification = Notification(
            user_id=user_id,
            title=title,
            message=message,
            type=notif_type,
            complaint_id=complaint_id,
            is_read=False
        )
        db.session.add(notification)
        db.session.commit()
        return notification
    except Exception as e:
        db.session.rollback()
        # Non-fatal error; log it
        print(f"Failed to create notification for user {user_id}: {str(e)}")
        return None

def notify_status_change(complaint, old_status, new_status):
    """
    Triggers notifications to Students and Staff based on status updates.
    """
    complaint_id = complaint.id
    
    # 1. Notify Student
    student_user_id = complaint.student.user_id if complaint.student and complaint.student.user else None
    if student_user_id:
        create_notification(
            user_id=student_user_id,
            title=f"Complaint {new_status}",
            message=f"Your complaint ticket '{complaint.title}' ({complaint_id}) status was updated from '{old_status}' to '{new_status}'.",
            notif_type="status_change",
            complaint_id=complaint_id
        )

    # 2. Notify Staff (if assigned)
    staff_user_id = complaint.assigned_staff.user_id if complaint.assigned_staff and complaint.assigned_staff.user else None
    if staff_user_id and new_status != 'Assigned':
        create_notification(
            user_id=staff_user_id,
            title="Ticket Status Updated",
            message=f"Ticket '{complaint.title}' ({complaint_id}) assigned to you is now: '{new_status}'.",
            notif_type="status_change",
            complaint_id=complaint_id
        )

def notify_assignment(complaint, staff):
    """
    Notifies staff of a new assignment, and notifies the student.
    """
    complaint_id = complaint.id
    
    # Notify Staff
    staff_user_id = staff.user_id
    create_notification(
        user_id=staff_user_id,
        title="New Complaint Assigned",
        message=f"A new ticket '{complaint.title}' ({complaint_id}) in location '{complaint.location}' has been assigned to you by Administration.",
        notif_type="assignment",
        complaint_id=complaint_id
    )

    # Notify Student
    student_user_id = complaint.student.user_id if complaint.student and complaint.student.user else None
    if student_user_id:
        create_notification(
            user_id=student_user_id,
            title="Maintenance Staff Assigned",
            message=f"Your complaint '{complaint.title}' ({complaint_id}) has been assigned to '{staff.user.username}' from the {staff.specialization} department.",
            notif_type="assignment",
            complaint_id=complaint_id
        )

def notify_priority_change(complaint, old_priority, new_priority):
    """
    Notifies Student and Staff of manual priority adjustments.
    """
    complaint_id = complaint.id

    # Notify Student
    student_user_id = complaint.student.user_id if complaint.student and complaint.student.user else None
    if student_user_id:
        create_notification(
            user_id=student_user_id,
            title="Complaint Priority Escalated" if new_priority in ['High', 'Urgent'] else "Complaint Priority Updated",
            message=f"The priority of your ticket '{complaint.title}' ({complaint_id}) was updated from '{old_priority}' to '{new_priority}'.",
            notif_type="priority_change",
            complaint_id=complaint_id
        )

    # Notify Staff
    staff_user_id = complaint.assigned_staff.user_id if complaint.assigned_staff and complaint.assigned_staff.user else None
    if staff_user_id:
        create_notification(
            user_id=staff_user_id,
            title="Assigned Ticket Priority Updated",
            message=f"Ticket '{complaint.title}' ({complaint_id}) priority changed to '{new_priority}'.",
            notif_type="priority_change",
            complaint_id=complaint_id
        )

def notify_attendance_shortage(student, overall_percentage):
    """
    Triggers a warning notification if student's cumulative attendance drops below 75%.
    """
    student_user_id = student.user_id if student and student.user else None
    if student_user_id and overall_percentage < 75.0:
        create_notification(
            user_id=student_user_id,
            title="Attendance Shortage Warning",
            message=f"Attendance Shortage Warning: Your cumulative attendance has dropped to {overall_percentage}%, which is below the 75% eligibility threshold.",
            notif_type="attendance_shortage"
        )

def notify_campus_service(user_id, service_name, request_id, status, details=""):
    """
    Triggers notifications to Students for updates on hostel, transport, or library desks.
    """
    title = f"{service_name} Request Update"
    message = f"Your {service_name.lower()} request ({request_id}) status was updated to: '{status}'."
    if details:
        message += f" Details: {details}"
    create_notification(
        user_id=user_id,
        title=title,
        message=message,
        notif_type="campus_service"
    )

def notify_placement_drive(drive):
    """
    Notifies all students whose branch code matches the drive's eligibility criteria.
    """
    from app.models.user import Student
    criteria_lower = drive.eligibility_criteria.lower() if drive.eligibility_criteria else ""
    
    # Check keywords deterministically
    cse_keywords = ['cse', 'computer science', 'it', 'information technology']
    ece_keywords = ['ece', 'electronics', 'communication']
    mech_keywords = ['mech', 'mechanical']
    civil_keywords = ['civil']
    
    all_students = Student.query.all()
    for s in all_students:
        branch_from_profile = s.department.lower() if s.department else ""
        dept_code = s.department_ref.code.lower() if s.department_ref else ""
        dept_name = s.department_ref.name.lower() if s.department_ref else ""
        
        is_eligible = False
        if not criteria_lower:
            is_eligible = True # default eligible if no criteria specified
        else:
            # 1. Check keywords matching
            if any(k in criteria_lower for k in cse_keywords) and ('computer' in branch_from_profile or 'information' in branch_from_profile or 'it' in branch_from_profile or 'cse' in dept_code):
                is_eligible = True
            elif any(k in criteria_lower for k in ece_keywords) and ('electronics' in branch_from_profile or 'ece' in branch_from_profile or 'ece' in dept_code):
                is_eligible = True
            elif any(k in criteria_lower for k in mech_keywords) and ('mechanical' in branch_from_profile or 'mech' in branch_from_profile or 'mech' in dept_code):
                is_eligible = True
            elif any(k in criteria_lower for k in civil_keywords) and ('civil' in branch_from_profile or 'civil' in dept_code):
                is_eligible = True
            
            # 2. Direct string checking fallback
            if dept_code and dept_code in criteria_lower:
                is_eligible = True
            if dept_name and any(word in criteria_lower for word in dept_name.split()):
                is_eligible = True
        
        if is_eligible and s.user_id:
            create_notification(
                user_id=s.user_id,
                title="New Placement Drive published",
                message=f"New Placement Drive published: {drive.company_name} is hiring for {drive.job_role}. Check eligibility and register.",
                notif_type="placement_drive"
            )

def notify_placement_status(application):
    """
    Notifies the student of a change in their placement application status.
    """
    student_user_id = application.student.user_id if application.student and application.student.user else None
    if student_user_id:
        company_name = application.drive.company_name if application.drive else "Placement Cell"
        status_msg = f"Your application for the {company_name} drive has been updated to: '{application.status}'."
        create_notification(
            user_id=student_user_id,
            title=f"Placement Update - {company_name}",
            message=status_msg,
            notif_type="placement_status"
        )
