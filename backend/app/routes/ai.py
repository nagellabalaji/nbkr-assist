from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from app import db
from app.models.log_feedback import ChatbotMessage
from app.services.ai_service import classify_complaint, get_chatbot_response, summarize_complaint

ai_bp = Blueprint('ai', __name__)

@ai_bp.route('/classify', methods=['POST'])
@jwt_required()
def classify_complaint_text():
    """Dry-run classification testing endpoint."""
    data = request.get_json() or {}
    description = data.get('description', '').strip()

    if not description:
        return jsonify({'success': False, 'message': 'Description is required', 'error': 'missing_description'}), 400

    results = classify_complaint(description)
    return jsonify({
        'success': True,
        'message': 'AI analysis completed successfully',
        'data': results
    }), 200


@ai_bp.route('/chat', methods=['POST'])
@jwt_required()
def chatbot_message():
    """CollegeAssist AI Chatbot conversation endpoint."""
    user_id = int(get_jwt_identity())
    data = request.get_json() or {}
    message = data.get('message', '').strip()

    if not message:
        return jsonify({'success': False, 'message': 'Message cannot be empty', 'error': 'missing_message'}), 400

    try:
        # 1. Fetch recent chat history for context (last 5 messages)
        recent_chats = ChatbotMessage.query.filter_by(user_id=user_id)\
            .order_by(ChatbotMessage.created_at.desc())\
            .limit(5).all()
        
        # Build contextual history string for Gemini prompt
        history_str = ""
        for chat in reversed(recent_chats):
            role_name = "Student" if chat.sender == 'user' else "CollegeAssist AI"
            history_str += f"{role_name}: {chat.message}\n"

        # 2. Get chatbot response (dispatched to LLM or Local FAQ matching)
        ai_response_pkg = get_chatbot_response(message, history_str)
        response_text = ai_response_pkg['response']

        # 3. Log chat transaction to database
        user_msg = ChatbotMessage(user_id=user_id, sender='user', message=message)
        bot_msg = ChatbotMessage(user_id=user_id, sender='bot', message=response_text)
        
        db.session.add(user_msg)
        db.session.add(bot_msg)
        db.session.commit()

        return jsonify({
            'success': True,
            'message': 'Message processed successfully',
            'data': {
                'user_message': message,
                'bot_response': response_text,
                'engine': ai_response_pkg['engine']
            }
        }), 200

    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'message': 'Chatbot transaction failed', 'error': str(e)}), 500


@ai_bp.route('/chat/history', methods=['GET'])
@jwt_required()
def get_chat_history():
    """Retrieves full chat history for the logged-in user."""
    user_id = int(get_jwt_identity())
    chats = ChatbotMessage.query.filter_by(user_id=user_id).order_by(ChatbotMessage.created_at.asc()).all()
    return jsonify({
        'success': True,
        'data': [c.to_dict() for c in chats]
    }), 200


@ai_bp.route('/summarize', methods=['POST'])
@jwt_required()
def summarize_complaint_data():
    """Provides structured short summaries of ticket data for admin convenience."""
    data = request.get_json() or {}
    complaint_id = data.get('complaint_id')

    if not complaint_id:
        return jsonify({'success': False, 'message': 'complaint_id is required', 'error': 'missing_id'}), 400

    from app.models.complaint import Complaint
    complaint = Complaint.query.get(complaint_id)
    
    if not complaint:
        return jsonify({'success': False, 'message': 'Complaint not found', 'error': 'not_found'}), 404

    summary = summarize_complaint(complaint.to_dict())
    return jsonify({
        'success': True,
        'data': summary
    }), 200
