import os
from pathlib import Path
from dotenv import load_dotenv

# Load .env file
load_dotenv()

BASE_DIR = Path(__file__).resolve().parent.parent.parent

class Config:
    SECRET_KEY = os.environ.get('SECRET_KEY', 'default-fallback-secret-key-98765')
    JWT_SECRET_KEY = os.environ.get('JWT_SECRET_KEY', 'default-jwt-secret-key-98765')
    
    # Database
    _raw_db_url = os.environ.get('DATABASE_URL', '')
    if not _raw_db_url or '@host' in _raw_db_url or 'your_' in _raw_db_url or (os.environ.get('FLASK_ENV') == 'production' and 'localhost' in _raw_db_url):
        _raw_db_url = 'mysql+pymysql://sql12838873:ynwhwp3Ebq@sql12.freesqldatabase.com:3306/sql12838873'
    if _raw_db_url.startswith('postgres://'):
        _raw_db_url = _raw_db_url.replace('postgres://', 'postgresql://', 1)
    SQLALCHEMY_DATABASE_URI = _raw_db_url
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    SQLALCHEMY_ENGINE_OPTIONS = {
        'pool_recycle': 280,
        'pool_pre_ping': True
    }
    
    # Uploads
    UPLOAD_FOLDER = os.path.join(BASE_DIR, os.environ.get('UPLOAD_FOLDER', 'uploads'))
    MAX_CONTENT_LENGTH = int(os.environ.get('MAX_CONTENT_LENGTH', 16 * 1024 * 1024)) # Default 16MB
    
    # AI API keys
    GEMINI_API_KEY = os.environ.get('GEMINI_API_KEY', None)

    # JWT configuration
    JWT_ACCESS_TOKEN_EXPIRES = 3600 * 24 * 7 # 7 days for development/demo ease

    # Email & OTP configurations (HTTPS API keys for cloud deployment like Render)
    EMAIL_API_KEY = os.environ.get('EMAIL_API_KEY', None)
    RESEND_API_KEY = os.environ.get('RESEND_API_KEY', None)
    BREVO_API_KEY = os.environ.get('BREVO_API_KEY', None)
    EMAIL_FROM = os.environ.get('EMAIL_FROM', 'startupwithus2932@gmail.com')
    OTP_EXPIRY_MINUTES = int(os.environ.get('OTP_EXPIRY_MINUTES', 5))
    OTP_RESEND_COOLDOWN = int(os.environ.get('OTP_RESEND_COOLDOWN', 60))
    
    # MAIL_* keys — primary names used by email_service.py
    MAIL_SERVER   = os.environ.get('MAIL_SERVER')   or os.environ.get('SMTP_SERVER',   'smtp.gmail.com')
    MAIL_PORT     = int(os.environ.get('MAIL_PORT') or os.environ.get('SMTP_PORT',     587))
    MAIL_USERNAME = os.environ.get('MAIL_USERNAME') or os.environ.get('SMTP_USERNAME', 'startupwithus2932@gmail.com')
    MAIL_PASSWORD = os.environ.get('MAIL_PASSWORD') or os.environ.get('SMTP_PASSWORD', 'daqkbmxqmwofslsh')
    MAIL_DEFAULT_SENDER = (
        os.environ.get('MAIL_DEFAULT_SENDER') or
        os.environ.get('EMAIL_FROM') or
        os.environ.get('SMTP_USERNAME') or
        'startupwithus2932@gmail.com'
    )
    MAIL_USE_TLS = True
    MAIL_USE_SSL = False

    # Legacy SMTP_* keys (kept for backward compat)
    SMTP_SERVER   = os.environ.get('SMTP_SERVER',   'smtp.gmail.com')
    SMTP_PORT     = int(os.environ.get('SMTP_PORT', 587))
    SMTP_USERNAME = os.environ.get('SMTP_USERNAME', 'startupwithus2932@gmail.com')
    SMTP_PASSWORD = os.environ.get('SMTP_PASSWORD', 'daqkbmxqmwofslsh')

    # Google OAuth 2.0 configurations
    GOOGLE_CLIENT_ID = os.environ.get('GOOGLE_CLIENT_ID', '613136878082-3smuudupve843groiq4fhkvmkblqit9p.apps.googleusercontent.com')
    GOOGLE_CLIENT_SECRET = os.environ.get('GOOGLE_CLIENT_SECRET', None)
