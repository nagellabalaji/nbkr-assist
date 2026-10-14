import logging
from flask import current_app
from app.ai.classifier import LocalNLPClassifier
from app.ai.chatbot import CollegeAssistChatbot
from app.ai.llm_wrapper import LLMAPIWrapper

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize local NLP instances once
local_classifier = LocalNLPClassifier()
local_chatbot = CollegeAssistChatbot()

def get_llm_wrapper():
    """Returns LLMAPIWrapper instance if API key is configured, else None."""
    api_key = current_app.config.get('GEMINI_API_KEY')
    if api_key and api_key.strip():
        try:
            return LLMAPIWrapper(api_key=api_key)
        except Exception as e:
            logger.error(f"Failed to initialize Gemini LLM API: {str(e)}")
    return None

def classify_complaint(description):
    """
    Classifies a complaint. Uses Gemini if configured,
    otherwise falls back to local TF-IDF Cosine Similarity engine.
    """
    llm = get_llm_wrapper()
    if llm:
        try:
            logger.info("Routing complaint classification to Gemini AI API...")
            result = llm.classify_complaint(description)
            return {
                'category': result.get('category', 'General'),
                'subcategory': result.get('subcategory', 'General'),
                'priority': result.get('priority', 'Medium'),
                'department': result.get('department', 'General Administration'),
                'suggested_action': result.get('suggested_action', 'Forward to Admin Office'),
                'confidence': float(result.get('confidence', 0.9)),
                'engine': 'Gemini AI'
            }
        except Exception as e:
            logger.warning(f"Gemini classification failed ({str(e)}). Falling back to local NLP...")
            
    # Fallback to local NLP
    category, subcategory, priority, department, suggested_action, confidence = local_classifier.classify_complaint(description)
    return {
        'category': category,
        'subcategory': subcategory,
        'priority': priority,
        'department': department,
        'suggested_action': suggested_action,
        'confidence': confidence,
        'engine': 'Local NLP Engine'
    }

def get_chatbot_response(user_query, chat_history_str=""):
    """
    Handles chatbot conversations. Uses Gemini if configured,
    otherwise falls back to local FAQ cosine matcher.
    """
    llm = get_llm_wrapper()
    if llm:
        try:
            logger.info("Routing chatbot message to Gemini AI API...")
            response = llm.chatbot_respond(user_query, chat_history_str)
            return {
                'response': response,
                'engine': 'Gemini AI'
            }
        except Exception as e:
            logger.warning(f"Gemini chatbot failed ({str(e)}). Falling back to local FAQ...")

    # Fallback to local chatbot
    response = local_chatbot.get_response(user_query)
    return {
        'response': response,
        'engine': 'Local FAQ Engine'
    }

def summarize_complaint(complaint_data):
    """
    Summarizes complaint logs.
    """
    summary_text = f"Title: {complaint_data.get('title')}. Description: {complaint_data.get('description')}. Status: {complaint_data.get('status')}. Location: {complaint_data.get('location')}."
    
    llm = get_llm_wrapper()
    if llm:
        try:
            logger.info("Routing complaint summarization to Gemini AI...")
            summary = llm.summarize_complaint(summary_text)
            return {
                'summary': summary,
                'engine': 'Gemini AI'
            }
        except Exception as e:
            logger.warning(f"Gemini summarization failed: {str(e)}")

    # Local fallback summary
    summary = f"Complaint is in {complaint_data.get('status')} state. Location: {complaint_data.get('location')}. Priority is {complaint_data.get('ai_priority')}."
    return {
        'summary': summary,
        'engine': 'Local Summary Engine'
    }

def detect_duplicates(new_description, existing_complaints):
    """
    Wraps local NLP duplicate detection (done locally to prevent API quota/latency issues).
    """
    return local_classifier.detect_duplicates(new_description, existing_complaints)
