from flask import Blueprint, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from app import db
from app.models.log_feedback import Notification

notifications_bp = Blueprint('notifications', __name__)

@notifications_bp.route('', methods=['GET'])
@jwt_required()
def get_user_notifications():
    """Gets all notifications for the logged-in user."""
    user_id = int(get_jwt_identity())
    notifications = Notification.query.filter_by(user_id=user_id).order_by(Notification.created_at.desc()).all()
    
    # Calculate unread count
    unread_count = Notification.query.filter_by(user_id=user_id, is_read=False).count()

    return jsonify({
        'success': True,
        'data': {
            'notifications': [n.to_dict() for n in notifications],
            'unread_count': unread_count
        }
    }), 200


@notifications_bp.route('/<int:id>/read', methods=['PUT'])
@jwt_required()
def mark_notification_read(id):
    """Marks a specific notification as read."""
    user_id = int(get_jwt_identity())
    notification = Notification.query.filter_by(id=id, user_id=user_id).first()

    if not notification:
        return jsonify({'success': False, 'message': 'Notification not found', 'error': 'not_found'}), 404

    try:
        notification.is_read = True
        db.session.commit()
        return jsonify({
            'success': True,
            'message': 'Notification marked as read',
            'data': notification.to_dict()
        }), 200
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'message': 'Database error occurred', 'error': str(e)}), 500


@notifications_bp.route('/read-all', methods=['PUT'])
@jwt_required()
def mark_all_notifications_read():
    """Marks all notifications for the current user as read."""
    user_id = int(get_jwt_identity())
    
    try:
        unread_notifs = Notification.query.filter_by(user_id=user_id, is_read=False).all()
        for notif in unread_notifs:
            notif.is_read = True
        
        db.session.commit()
        return jsonify({
            'success': True,
            'message': 'All notifications marked as read'
        }), 200
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'message': 'Database error occurred', 'error': str(e)}), 500
