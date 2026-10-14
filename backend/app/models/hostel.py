from app import db
from datetime import datetime

class HostelRequest(db.Model):
    __tablename__ = 'hostel_requests'

    id = db.Column(db.Integer, primary_key=True)
    student_id = db.Column(db.Integer, db.ForeignKey('students.id', ondelete='CASCADE'), nullable=False)
    request_type = db.Column(db.Enum('electrical', 'plumbing', 'room_repair', 'dining', 'other'), nullable=False)
    description = db.Column(db.Text, nullable=False)
    status = db.Column(db.Enum('submitted', 'in_progress', 'resolved', 'rejected'), default='submitted')
    admin_notes = db.Column(db.Text, default=None)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    student = db.relationship('Student', backref=db.backref('hostel_requests', lazy=True, cascade="all, delete-orphan"))

    def to_dict(self):
        return {
            'id': self.id,
            'student_id': self.student_id,
            'student_name': self.student.user.username if self.student and self.student.user else 'Unknown',
            'roll_no': self.student.roll_no if self.student else '',
            'hostel_no': self.student.hostel_no if self.student else '',
            'room_no': self.student.room_no if self.student else '',
            'request_type': self.request_type,
            'description': self.description,
            'status': self.status,
            'admin_notes': self.admin_notes,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }
