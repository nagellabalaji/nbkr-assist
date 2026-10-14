from app import db
from datetime import datetime

class Notification(db.Model):
    __tablename__ = 'notifications'

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id', ondelete='CASCADE'), nullable=False)
    title = db.Column(db.String(150), nullable=False)
    message = db.Column(db.Text, nullable=False)
    is_read = db.Column(db.Boolean, default=False)
    type = db.Column(db.String(50), nullable=False) # status_change, assignment, priority_change
    complaint_id = db.Column(db.String(30), db.ForeignKey('complaints.id', ondelete='SET NULL'), default=None, nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def to_dict(self):
        return {
            'id': self.id,
            'user_id': self.user_id,
            'title': self.title,
            'message': self.message,
            'is_read': self.is_read,
            'type': self.type,
            'complaint_id': self.complaint_id,
            'created_at': self.created_at.isoformat() if self.created_at else None
        }


class Feedback(db.Model):
    __tablename__ = 'feedback'

    id = db.Column(db.Integer, primary_key=True)
    complaint_id = db.Column(db.String(30), db.ForeignKey('complaints.id', ondelete='CASCADE'), nullable=False, unique=True)
    rating = db.Column(db.Integer, nullable=False)
    comments = db.Column(db.Text, default=None)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def to_dict(self):
        return {
            'id': self.id,
            'complaint_id': self.complaint_id,
            'rating': self.rating,
            'comments': self.comments,
            'created_at': self.created_at.isoformat() if self.created_at else None
        }


class ChatbotMessage(db.Model):
    __tablename__ = 'chatbot_messages'

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id', ondelete='CASCADE'), nullable=False)
    sender = db.Column(db.Enum('user', 'bot'), nullable=False)
    message = db.Column(db.Text, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def to_dict(self):
        return {
            'id': self.id,
            'user_id': self.user_id,
            'sender': self.sender,
            'message': self.message,
            'created_at': self.created_at.isoformat() if self.created_at else None
        }
