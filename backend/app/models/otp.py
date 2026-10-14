from app import db
from datetime import datetime

class OTPVerification(db.Model):
    __tablename__ = 'otp_verifications'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id', ondelete='CASCADE'), nullable=True)
    email = db.Column(db.String(100), nullable=False)
    otp_hash = db.Column(db.String(255), nullable=False)
    purpose = db.Column(db.Enum('registration', 'login', 'password_reset'), nullable=False)
    expires_at = db.Column(db.DateTime, nullable=False)
    attempts = db.Column(db.Integer, default=0)
    max_attempts = db.Column(db.Integer, default=5)
    verified = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    verified_at = db.Column(db.DateTime, nullable=True)
    
    # Relationship
    user = db.relationship('User', backref=db.backref('otp_verifications', cascade="all, delete-orphan"))

    def to_dict(self):
        return {
            'id': self.id,
            'user_id': self.user_id,
            'email': self.email,
            'purpose': self.purpose,
            'expires_at': self.expires_at.isoformat() if self.expires_at else None,
            'attempts': self.attempts,
            'max_attempts': self.max_attempts,
            'verified': self.verified,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'verified_at': self.verified_at.isoformat() if self.verified_at else None
        }
