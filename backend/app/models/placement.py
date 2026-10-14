from app import db
from datetime import datetime

class PlacementDrive(db.Model):
    __tablename__ = 'placement_drives'

    id = db.Column(db.Integer, primary_key=True)
    company_name = db.Column(db.String(100), nullable=False)
    job_role = db.Column(db.String(100), nullable=False)
    eligibility_criteria = db.Column(db.String(255), nullable=True)
    salary_package = db.Column(db.String(50), nullable=True)
    drive_date = db.Column(db.DateTime, nullable=False)
    status = db.Column(db.Enum('Upcoming', 'Ongoing', 'Completed'), default='Upcoming')
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    def to_dict(self):
        return {
            'id': self.id,
            'company_name': self.company_name,
            'job_role': self.job_role,
            'eligibility_criteria': self.eligibility_criteria,
            'salary_package': self.salary_package,
            'drive_date': self.drive_date.isoformat() if self.drive_date else None,
            'status': self.status,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }

class PlacementApplication(db.Model):
    __tablename__ = 'placement_applications'

    id = db.Column(db.Integer, primary_key=True)
    student_id = db.Column(db.Integer, db.ForeignKey('students.id', ondelete='CASCADE'), nullable=False)
    drive_id = db.Column(db.Integer, db.ForeignKey('placement_drives.id', ondelete='CASCADE'), nullable=False)
    status = db.Column(db.Enum('applied', 'shortlisted', 'selected', 'rejected'), default='applied')
    applied_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    student = db.relationship('Student', backref=db.backref('placement_apps', lazy=True, cascade="all, delete-orphan"))
    drive = db.relationship('PlacementDrive', backref=db.backref('apps', lazy=True, cascade="all, delete-orphan"))

    def to_dict(self):
        return {
            'id': self.id,
            'student_id': self.student_id,
            'student_name': self.student.user.username if self.student and self.student.user else 'Unknown',
            'roll_no': self.student.roll_no if self.student else '',
            'department': self.student.department if self.student else '',
            'drive_id': self.drive_id,
            'company_name': self.drive.company_name if self.drive else 'Unknown',
            'job_role': self.drive.job_role if self.drive else 'Unknown',
            'status': self.status,
            'applied_at': self.applied_at.isoformat() if self.applied_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }
