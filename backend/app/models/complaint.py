from app import db
from datetime import datetime

class ComplaintCategory(db.Model):
    __tablename__ = 'complaint_categories'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False, unique=True)
    description = db.Column(db.Text)
    suggested_department = db.Column(db.String(100), nullable=False)
    parent_category_id = db.Column(db.Integer, db.ForeignKey('complaint_categories.id', ondelete='SET NULL'), nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    # Relationships
    complaints = db.relationship('Complaint', backref='category')
    # Self-referential child categories list
    children = db.relationship('ComplaintCategory', backref=db.backref('parent', remote_side=[id]))

    def to_dict(self):
        return {
            'id': self.id,
            'name': self.name,
            'description': self.description,
            'suggested_department': self.suggested_department,
            'parent_category_id': self.parent_category_id
        }


class Complaint(db.Model):
    __tablename__ = 'complaints'

    id = db.Column(db.String(30), primary_key=True) # CMP-YYYY-XXXXX or NBKR-YYYY-XXXXXX
    student_id = db.Column(db.Integer, db.ForeignKey('students.id', ondelete='CASCADE'), nullable=False)
    title = db.Column(db.String(150), nullable=False)
    description = db.Column(db.Text, nullable=False)
    category_id = db.Column(db.Integer, db.ForeignKey('complaint_categories.id'), nullable=False)
    subcategory = db.Column(db.String(100), nullable=True)
    location = db.Column(db.String(255), nullable=False)
    image_path = db.Column(db.String(255), default=None)
    ai_priority = db.Column(db.Enum('Low', 'Medium', 'High', 'Urgent'), default='Medium')
    ai_confidence = db.Column(db.Float, default=0.0)
    suggested_department = db.Column(db.String(100), nullable=False)
    assigned_staff_id = db.Column(db.Integer, db.ForeignKey('staff.id', ondelete='SET NULL'), default=None)
    status = db.Column(db.Enum('Submitted', 'Under Review', 'Assigned', 'In Progress', 'Resolved', 'Closed', 'Reopened', 'Rejected'), default='Submitted')
    sla_deadline = db.Column(db.DateTime, default=None, nullable=True)
    sla_status = db.Column(db.Enum('Normal', 'Breached'), default='Normal')
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    resolved_at = db.Column(db.DateTime, default=None, nullable=True)
    work_notes = db.Column(db.Text, default=None)

    # Relationships
    assignments = db.relationship('ComplaintAssignment', backref='complaint', cascade="all, delete-orphan")
    histories = db.relationship('ComplaintHistory', backref='complaint', cascade="all, delete-orphan")
    feedback = db.relationship('Feedback', backref='complaint', uselist=False, cascade="all, delete-orphan")
    notifications = db.relationship('Notification', backref='complaint', cascade="all, delete-orphan")

    def to_dict(self):
        # Dynamically compute if SLA is breached
        is_breached = self.sla_status
        if self.status not in ['Resolved', 'Closed', 'Rejected'] and self.sla_deadline:
            if datetime.utcnow() > self.sla_deadline:
                is_breached = 'Breached'

        assigned_branch_val = None
        if self.assigned_staff:
            if self.assigned_staff.department_id:
                from app.models.department import Department
                dept = Department.query.get(self.assigned_staff.department_id)
                assigned_branch_val = dept.code if dept else self.assigned_staff.department
            else:
                assigned_branch_val = self.assigned_staff.department

        # Determine assignment_status dynamically
        assignment_status = None
        if self.status:
            s_upper = self.status.upper()
            if s_upper == 'SUBMITTED':
                assignment_status = 'PENDING'
            elif s_upper == 'UNDER REVIEW':
                assignment_status = 'UNDER REVIEW'
            elif s_upper == 'REOPENED':
                assignment_status = 'REOPENED'
            elif s_upper == 'REJECTED':
                assignment_status = 'REJECTED'
            elif s_upper == 'RESOLVED':
                assignment_status = 'RESOLVED'
            elif s_upper == 'CLOSED':
                assignment_status = 'CLOSED'
            elif s_upper == 'IN PROGRESS':
                assignment_status = 'IN_PROGRESS'
            elif s_upper == 'ASSIGNED':
                assignment_status = 'ASSIGNED'
            else:
                assignment_status = s_upper

        # If assigned / in progress, check if it has exceeded deadline
        if self.status not in ['Resolved', 'Closed', 'Rejected'] and self.sla_deadline:
            if datetime.utcnow() > self.sla_deadline:
                assignment_status = 'OVERDUE'

        return {
            'id': self.id,
            'student_id': self.student_id,
            'student_name': self.student.user.username if self.student and self.student.user else 'Unknown',
            'roll_no': self.student.roll_no if self.student else 'N/A',
            'title': self.title,
            'description': self.description,
            'category_id': self.category_id,
            'category_name': self.category.name if self.category else 'Unknown',
            'subcategory': self.subcategory,
            'location': self.location,
            'image_path': self.image_path,
            'ai_priority': self.ai_priority,
            'ai_confidence': self.ai_confidence,
            'suggested_department': self.suggested_department,
            'assigned_staff_id': self.assigned_staff_id,
            'assigned_staff_name': self.assigned_staff.user.username if self.assigned_staff and self.assigned_staff.user else None,
            'assigned_faculty_id': self.assigned_staff_id,
            'assigned_faculty_name': self.assigned_staff.user.username if self.assigned_staff and self.assigned_staff.user else None,
            'assigned_faculty_phone': self.assigned_staff.phone if (self.assigned_staff and self.assigned_staff.phone) else "Not available",
            'assigned_branch': assigned_branch_val,
            'assigned_at': self.assignments[-1].assigned_at.isoformat() if self.assignments else None,
            'status': self.status,
            'sla_deadline': self.sla_deadline.isoformat() if self.sla_deadline else None,
            'resolution_deadline': self.sla_deadline.isoformat() if self.sla_deadline else None,
            'sla_status': is_breached,
            'assignment_status': assignment_status,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None,
            'resolved_at': self.resolved_at.isoformat() if self.resolved_at else None,
            'work_notes': self.work_notes,
            'has_feedback': self.feedback is not None,
            'feedback_rating': self.feedback.rating if self.feedback else None,
            'feedback_comments': self.feedback.comments if self.feedback else None
        }


class ComplaintAssignment(db.Model):
    __tablename__ = 'complaint_assignments'

    id = db.Column(db.Integer, primary_key=True)
    complaint_id = db.Column(db.String(30), db.ForeignKey('complaints.id', ondelete='CASCADE'), nullable=False)
    staff_id = db.Column(db.Integer, db.ForeignKey('staff.id', ondelete='CASCADE'), nullable=False)
    assigned_by = db.Column(db.Integer, db.ForeignKey('admins.id', ondelete='CASCADE'), nullable=False)
    status = db.Column(db.Enum('Assigned', 'Accepted', 'Completed'), default='Assigned')
    assigned_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    def to_dict(self):
        return {
            'id': self.id,
            'complaint_id': self.complaint_id,
            'staff_id': self.staff_id,
            'staff_name': self.staff.user.username if self.staff and self.staff.user else 'Unknown',
            'assigned_by': self.assigned_by,
            'assigned_by_name': self.assigned_by_admin.user.username if self.assigned_by_admin and self.assigned_by_admin.user else 'Unknown',
            'status': self.status,
            'assigned_at': self.assigned_at.isoformat() if self.assigned_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }


class ComplaintHistory(db.Model):
    __tablename__ = 'complaint_history'

    id = db.Column(db.Integer, primary_key=True)
    complaint_id = db.Column(db.String(30), db.ForeignKey('complaints.id', ondelete='CASCADE'), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id', ondelete='CASCADE'), nullable=False)
    action = db.Column(db.String(100), nullable=False)
    previous_value = db.Column(db.String(255), default=None)
    new_value = db.Column(db.String(255), default=None)
    comments = db.Column(db.Text, default=None)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def to_dict(self):
        return {
            'id': self.id,
            'complaint_id': self.complaint_id,
            'user_id': self.user_id,
            'username': self.user.username if self.user else 'Unknown',
            'role': self.user.role if self.user else 'Unknown',
            'action': self.action,
            'previous_value': self.previous_value,
            'new_value': self.new_value,
            'comments': self.comments,
            'created_at': self.created_at.isoformat() if self.created_at else None
        }
