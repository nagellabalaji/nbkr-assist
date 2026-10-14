from app import db
from datetime import datetime
from werkzeug.security import generate_password_hash, check_password_hash
from app.models.department import Department

class User(db.Model):
    __tablename__ = 'users'
    
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(50), nullable=False, unique=True)
    email = db.Column(db.String(100), nullable=False, unique=True)
    password_hash = db.Column(db.String(255), nullable=False)
    role = db.Column(db.Enum(
        'student', 'faculty', 'hod', 'exam_cell', 'placement_officer',
        'hostel_admin', 'transport_admin', 'maintenance_staff', 'librarian', 'super_admin'
    ), nullable=False)
    status = db.Column(db.Enum('active', 'inactive'), default='active')
    email_verified = db.Column(db.Boolean, default=True)
    google_id = db.Column(db.String(100), unique=True, nullable=True)
    avatar_url = db.Column(db.String(255), nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    student_profile = db.relationship('Student', backref='user', uselist=False, cascade="all, delete-orphan")
    staff_profile = db.relationship('Staff', backref='user', uselist=False, cascade="all, delete-orphan")
    admin_profile = db.relationship('Admin', backref='user', uselist=False, cascade="all, delete-orphan")
    histories = db.relationship('ComplaintHistory', backref='user', cascade="all, delete-orphan")
    notifications = db.relationship('Notification', backref='user', cascade="all, delete-orphan")
    chatbot_messages = db.relationship('ChatbotMessage', backref='user', cascade="all, delete-orphan")

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

    def to_dict(self):
        return {
            'id': self.id,
            'username': self.username,
            'email': self.email,
            'role': self.role,
            'status': self.status,
            'email_verified': self.email_verified,
            'google_id': self.google_id,
            'avatar_url': self.avatar_url,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }


class Student(db.Model):
    __tablename__ = 'students'

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id', ondelete='CASCADE'), nullable=False, unique=True)
    roll_no = db.Column(db.String(20), nullable=False, unique=True)
    department = db.Column(db.String(100), nullable=False)
    hostel_no = db.Column(db.String(50), default=None)
    room_no = db.Column(db.String(20), default=None)
    contact_no = db.Column(db.String(20), default=None)
    program = db.Column(db.String(50), default='B.Tech')
    year = db.Column(db.String(10), default='I Year')
    semester = db.Column(db.String(10), default='I Semester')
    section = db.Column(db.String(10), default='A')
    batch = db.Column(db.String(20), default='2026')
    admission_year = db.Column(db.Integer, default=2026)
    parent_name = db.Column(db.String(100), default=None)
    parent_phone = db.Column(db.String(20), default=None)
    hostel_status = db.Column(db.Enum('Hosteller', 'Dayscholar'), default='Dayscholar')
    transport_status = db.Column(db.Enum('College Bus', 'Own Transport'), default='Own Transport')
    profile_photo = db.Column(db.String(255), default=None)
    department_id = db.Column(db.Integer, db.ForeignKey('departments.id', ondelete='SET NULL'), default=None)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    complaints = db.relationship('Complaint', backref='student', cascade="all, delete-orphan")

    def to_dict(self):
        user_data = self.user.to_dict() if self.user else {}
        return {
            **user_data,
            'id': self.id,
            'user_id': self.user_id,
            'roll_no': self.roll_no,
            'department': self.department,
            'hostel_no': self.hostel_no,
            'room_no': self.room_no,
            'contact_no': self.contact_no,
            'program': self.program,
            'year': self.year,
            'semester': self.semester,
            'section': self.section,
            'batch': self.batch,
            'admission_year': self.admission_year,
            'parent_name': self.parent_name,
            'parent_phone': self.parent_phone,
            'hostel_status': self.hostel_status,
            'transport_status': self.transport_status,
            'profile_photo': self.profile_photo,
            'department_id': self.department_id
        }


class Staff(db.Model):
    __tablename__ = 'staff'

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id', ondelete='CASCADE'), nullable=False, unique=True)
    department = db.Column(db.String(100), nullable=False)
    specialization = db.Column(db.String(100), nullable=False)
    is_available = db.Column(db.Boolean, default=True)
    department_id = db.Column(db.Integer, db.ForeignKey('departments.id', ondelete='SET NULL'), default=None)
    employee_id = db.Column(db.String(50), nullable=True)
    designation = db.Column(db.String(50), nullable=True)
    phone = db.Column(db.String(20), nullable=True)
    academic_year = db.Column(db.String(20), default='2026')
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    complaints = db.relationship('Complaint', backref='assigned_staff')
    assignments = db.relationship('ComplaintAssignment', backref='staff', cascade="all, delete-orphan")
    faculty_subjects = db.relationship('FacultySubject', backref='faculty', cascade="all, delete-orphan")
    attendance_sessions = db.relationship('AttendanceSession', backref='faculty', cascade="all, delete-orphan")

    def to_dict(self):
        user_data = self.user.to_dict() if self.user else {}
        return {
            **user_data,
            'id': self.id,
            'user_id': self.user_id,
            'department': self.department,
            'specialization': self.specialization,
            'is_available': self.is_available,
            'department_id': self.department_id,
            'employee_id': self.employee_id,
            'designation': self.designation,
            'phone': self.phone,
            'academic_year': self.academic_year
        }


class Admin(db.Model):
    __tablename__ = 'admins'

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id', ondelete='CASCADE'), nullable=False, unique=True)
    department = db.Column(db.String(100), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    assignments = db.relationship('ComplaintAssignment', backref='assigned_by_admin', cascade="all, delete-orphan")

    def to_dict(self):
        user_data = self.user.to_dict() if self.user else {}
        return {
            **user_data,
            'id': self.id,
            'user_id': self.user_id,
            'department': self.department
        }
