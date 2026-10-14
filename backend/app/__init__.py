import os
from flask import Flask, jsonify
from flask_sqlalchemy import SQLAlchemy
from flask_jwt_extended import JWTManager
from flask_cors import CORS
from app.config.settings import Config

# Initialize extensions
db = SQLAlchemy()
jwt = JWTManager()
cors = CORS()

def create_app(config_class=Config):
    app = Flask(__name__)
    app.config.from_object(config_class)

    # Ensure uploads directory exists
    os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

    # Initialize extensions with app
    db.init_app(app)
    jwt.init_app(app)
    # Load dynamic CORS origins from environment config, defaulting to dev URL
    cors_origins = os.getenv('CORS_ORIGINS', 'http://localhost:5173')
    allowed_origins = [o.strip() for o in cors_origins.split(',') if o.strip()]
    cors.init_app(app, resources={r"/api/*": {"origins": allowed_origins}})

    # Register blueprints (routes will be defined in Phase 4)
    from app.routes.auth import auth_bp
    from app.routes.complaints import complaints_bp, grievances_bp
    from app.routes.notifications import notifications_bp
    from app.routes.ai import ai_bp
    from app.routes.admin import admin_bp
    from app.routes.departments import departments_bp
    from app.routes.student import student_bp
    from app.routes.faculty import faculty_bp
    from app.routes.hod import hod_bp
    from app.routes.exams import exams_bp
    from app.routes.hostel import hostel_bp
    from app.routes.transport import transport_bp
    from app.routes.library import library_bp
    from app.routes.placement_routes import placement_bp

    app.register_blueprint(auth_bp, url_prefix='/api/auth')
    app.register_blueprint(complaints_bp, url_prefix='/api/complaints')
    app.register_blueprint(grievances_bp, url_prefix='/api/grievances')
    app.register_blueprint(notifications_bp, url_prefix='/api/notifications')
    app.register_blueprint(ai_bp, url_prefix='/api/ai')
    app.register_blueprint(admin_bp, url_prefix='/api/admin')
    app.register_blueprint(departments_bp, url_prefix='/api/departments')
    app.register_blueprint(student_bp, url_prefix='/api/student')
    app.register_blueprint(faculty_bp, url_prefix='/api/faculty')
    app.register_blueprint(hod_bp, url_prefix='/api/hod')
    app.register_blueprint(exams_bp, url_prefix='/api/exams')
    app.register_blueprint(hostel_bp, url_prefix='/api/hostel')
    app.register_blueprint(transport_bp, url_prefix='/api/transport')
    app.register_blueprint(library_bp, url_prefix='/api/library')
    app.register_blueprint(placement_bp, url_prefix='/api/placements')

    # Register custom JWT error handlers
    @jwt.expired_token_loader
    def my_expired_token_callback(jwt_header, jwt_payload):
        return jsonify({
            'success': False,
            'message': 'The token has expired',
            'error': 'token_expired'
        }), 401

    @jwt.invalid_token_loader
    def my_invalid_token_callback(error):
        return jsonify({
            'success': False,
            'message': 'Signature verification failed',
            'error': 'token_invalid'
        }), 401

    @jwt.unauthorized_loader
    def my_unauthorized_callback(error):
        return jsonify({
            'success': False,
            'message': 'Request does not contain an access token',
            'error': 'token_missing'
        }), 401

    # Global HTTP error handlers
    @app.errorhandler(400)
    def bad_request(error):
        return jsonify({
            'success': False,
            'message': 'Bad Request',
            'error': str(error.description)
        }), 400

    @app.errorhandler(401)
    def unauthorized(error):
        return jsonify({
            'success': False,
            'message': 'Unauthorized access',
            'error': str(error.description)
        }), 401

    @app.errorhandler(403)
    def forbidden(error):
        return jsonify({
            'success': False,
            'message': 'Forbidden resource',
            'error': str(error.description)
        }), 403

    @app.errorhandler(404)
    def not_found(error):
        return jsonify({
            'success': False,
            'message': 'Resource not found',
            'error': str(error.description)
        }), 404

    @app.errorhandler(500)
    def internal_error(error):
        return jsonify({
            'success': False,
            'message': 'Internal Server Error',
            'error': str(error)
        }), 500

    return app
