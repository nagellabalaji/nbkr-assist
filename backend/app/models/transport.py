from app import db
from datetime import datetime

class TransportRoute(db.Model):
    __tablename__ = 'transport_routes'

    id = db.Column(db.Integer, primary_key=True)
    route_name = db.Column(db.String(150), nullable=False)
    bus_number = db.Column(db.String(30), nullable=False)
    timings = db.Column(db.String(100), nullable=False)
    stops = db.Column(db.Text, nullable=False) # comma-separated stops
    is_active = db.Column(db.Boolean, default=True)

    def to_dict(self):
        return {
            'id': self.id,
            'route_name': self.route_name,
            'bus_number': self.bus_number,
            'timings': self.timings,
            'stops': [s.strip() for s in self.stops.split(',')] if self.stops else [],
            'is_active': self.is_active
        }

class TransportRequest(db.Model):
    __tablename__ = 'transport_requests'

    id = db.Column(db.Integer, primary_key=True)
    student_id = db.Column(db.Integer, db.ForeignKey('students.id', ondelete='CASCADE'), nullable=False)
    request_type = db.Column(db.Enum('new_pass', 'renew_pass', 'route_change', 'grievance'), nullable=False)
    route_id = db.Column(db.Integer, db.ForeignKey('transport_routes.id', ondelete='SET NULL'), nullable=True)
    description = db.Column(db.Text, nullable=False)
    status = db.Column(db.Enum('submitted', 'approved', 'rejected'), default='submitted')
    admin_notes = db.Column(db.Text, default=None)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    student = db.relationship('Student', backref=db.backref('transport_requests', lazy=True, cascade="all, delete-orphan"))
    route = db.relationship('TransportRoute', backref=db.backref('requests', lazy=True))

    def to_dict(self):
        return {
            'id': self.id,
            'student_id': self.student_id,
            'student_name': self.student.user.username if self.student and self.student.user else 'Unknown',
            'roll_no': self.student.roll_no if self.student else '',
            'request_type': self.request_type,
            'route_id': self.route_id,
            'route_name': self.route.route_name if self.route else 'None',
            'bus_number': self.route.bus_number if self.route else 'None',
            'description': self.description,
            'status': self.status,
            'admin_notes': self.admin_notes,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }
