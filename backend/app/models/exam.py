from app import db
from datetime import datetime

class ExamNotification(db.Model):
    __tablename__ = 'exam_notifications'

    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(150), nullable=False)
    subject = db.Column(db.String(100), nullable=False)
    exam_date = db.Column(db.DateTime, nullable=False)
    duration_mins = db.Column(db.Integer, default=180)
    location = db.Column(db.String(100), nullable=False)
    department_id = db.Column(db.Integer, db.ForeignKey('departments.id', ondelete='SET NULL'), nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationship to department
    department = db.relationship('Department', backref=db.backref('exams', lazy=True))

    def to_dict(self):
        return {
            'id': self.id,
            'title': self.title,
            'subject': self.subject,
            'exam_date': self.exam_date.isoformat() if self.exam_date else None,
            'duration_mins': self.duration_mins,
            'location': self.location,
            'department_id': self.department_id,
            'department_code': self.department.code if self.department else 'All',
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }
