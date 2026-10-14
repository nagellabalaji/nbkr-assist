from flask import Blueprint, request, jsonify, current_app
from flask_jwt_extended import (
    create_access_token, jwt_required, get_jwt_identity, get_jwt
)
from google.oauth2 import id_token
from google.auth.transport import requests as google_requests
from app import db
from app.models.user import User, Student, Staff, Admin
from app.models.department import Department
from app.models.otp import OTPVerification
from app.services.email_service import EmailService
import re
import secrets
import hashlib
from datetime import datetime, timedelta

auth_bp = Blueprint('auth', __name__)

EMAIL_REGEX = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'

def hash_otp(otp_str):
    """Computes a SHA-256 hash of the OTP code for secure storage."""
    return hashlib.sha256(otp_str.encode('utf-8')).hexdigest()

def check_cooldown(email, purpose):
    """Checks if another OTP request is made within the cooldown window (60s)."""
    last_otp = OTPVerification.query.filter_by(
        email=email, purpose=purpose
    ).order_by(OTPVerification.created_at.desc()).first()
    
    if last_otp:
        elapsed = (datetime.utcnow() - last_otp.created_at).total_seconds()
        if elapsed < 60:
            return True, int(60 - elapsed)
    return False, 0

# --- REGISTRATION OTP FLOW ---

@auth_bp.route('/register/send-otp', methods=['POST'])
def register_send_otp():
    """Validates registration details and registers a pending unverified account, then dispatches email OTP code."""
    data = request.get_json() or {}
    username = (data.get('username') or '').strip()
    email = (data.get('email') or '').strip()
    password = (data.get('password') or '').strip()
    roll_no = (data.get('roll_no') or '').strip().upper()
    role = 'student'
    department_id = data.get('department_id')
    hostel_no = (data.get('hostel_no') or '').strip() or None
    room_no = (data.get('room_no') or '').strip() or None
    contact_no = (data.get('contact_no') or '').strip() or None

    if not (username and email and password):
        return jsonify({'success': False, 'message': 'Username, email and password are required', 'error': 'missing_fields'}), 400

    if not department_id:
        return jsonify({'success': False, 'message': 'Department selection is required', 'error': 'missing_department'}), 400

    dept = Department.query.get(department_id)
    if not dept:
        return jsonify({'success': False, 'message': 'Invalid department selection', 'error': 'invalid_department'}), 400

    if not re.match(EMAIL_REGEX, email):
        return jsonify({'success': False, 'message': 'Invalid email format', 'error': 'invalid_email'}), 400

    # Check request rate limit/cooldown
    on_cooldown, remain = check_cooldown(email, 'registration')
    if on_cooldown:
        return jsonify({
            'success': False, 
            'message': f'Please wait {remain} seconds before requesting a new code.',
            'error': 'cooldown_active',
            'remain': remain
        }), 429

    if len(password) < 6:
        return jsonify({'success': False, 'message': 'Password must be at least 6 characters long', 'error': 'password_too_short'}), 400

    # Length validations matching MySQL constraints
    if len(username) > 50:
        return jsonify({'success': False, 'message': 'Full name must not exceed 50 characters', 'error': 'invalid_username_length'}), 400
    if len(email) > 100:
        return jsonify({'success': False, 'message': 'Email address must not exceed 100 characters', 'error': 'invalid_email_length'}), 400

    # Duplicate checks
    user_by_email = User.query.filter_by(email=email).first()
    if user_by_email and user_by_email.email_verified:
        return jsonify({'success': False, 'message': 'Email already registered', 'error': 'email_exists'}), 400

    user_by_name = User.query.filter_by(username=username).first()
    if user_by_name and user_by_name.email_verified:
        return jsonify({'success': False, 'message': 'Username already exists', 'error': 'username_exists'}), 400

    if role == 'student':
        if not roll_no:
            return jsonify({'success': False, 'message': 'Roll number is required for students', 'error': 'missing_profile_fields'}), 400
        if len(roll_no) > 20:
            return jsonify({'success': False, 'message': 'Student ID must not exceed 20 characters', 'error': 'invalid_roll_no_length'}), 400
        
        student_by_roll = Student.query.filter_by(roll_no=roll_no).first()
        if student_by_roll and student_by_roll.user.email_verified:
            return jsonify({'success': False, 'message': 'Roll number already exists', 'error': 'roll_no_exists'}), 400

    # Clean up any stale unverified attempts to allow fresh registry parameters
    try:
        if user_by_email:
            db.session.delete(user_by_email)
        if user_by_name and user_by_name != user_by_email:
            db.session.delete(user_by_name)
        if role == 'student' and student_by_roll and student_by_roll.user != user_by_email and student_by_roll.user != user_by_name:
            db.session.delete(student_by_roll.user)
        db.session.commit()
    except Exception as cleanup_err:
        db.session.rollback()
        return jsonify({'success': False, 'message': 'Failed to verify unique fields', 'error': str(cleanup_err)}), 500

    # Generate secure 6-digit OTP
    otp = f"{secrets.randbelow(900000) + 100000}"
    otp_hash = hash_otp(otp)
    
    # Store verification record
    db_otp = OTPVerification(
        email=email,
        otp_hash=otp_hash,
        purpose='registration',
        expires_at=datetime.utcnow() + timedelta(minutes=5)
    )
    
    try:
        # Create unverified user and student profile
        user = User(username=username, email=email, role=role, status='inactive', email_verified=False)
        user.set_password(password)
        db.session.add(user)
        db.session.flush()

        student = Student(
            user_id=user.id,
            roll_no=roll_no,
            department=dept.name,
            department_id=dept.id,
            hostel_no=hostel_no,
            room_no=room_no,
            contact_no=contact_no
        )
        db.session.add(student)
        db.session.add(db_otp)
        db.session.commit()
        
        # Dispatch email
        sent = False
        try:
            sent = EmailService.send_otp_email(email, username, otp, 'registration')
        except Exception as mail_err:
            current_app.logger.warning(f"Email dispatch exception: {str(mail_err)}")

        if not sent:
            # Cloud outbound SMTP (ports 587/465) may be blocked on free tiers.
            # Gracefully provide code so the user is never locked out of registering!
            return jsonify({
                'success': True,
                'message': f'Verification code generated! Code: {otp}',
                'demo_otp': otp,
                'email_sent': False
            }), 200
            
        return jsonify({
            'success': True,
            'message': 'Verification code sent successfully to your email.',
            'demo_otp': otp,
            'email_sent': True
        }), 200
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'message': 'Failed to save verification token', 'error': str(e)}), 500


@auth_bp.route('/register/verify-otp', methods=['POST'])
def register_verify_otp():
    """Verifies registration OTP. If valid, activates the student account."""
    data = request.get_json() or {}
    email = (data.get('email') or '').strip()
    otp = (data.get('otp') or '').strip()

    if not (email and otp):
        return jsonify({'success': False, 'message': 'Missing email or verification code', 'error': 'missing_fields'}), 400

    # Retrieve matching OTP verification record
    db_otp = OTPVerification.query.filter_by(
        email=email, purpose='registration', verified=False
    ).order_by(OTPVerification.created_at.desc()).first()

    if not db_otp:
        return jsonify({'success': False, 'message': 'No verification code requested for this email', 'error': 'otp_missing'}), 400

    if db_otp.expires_at < datetime.utcnow():
        return jsonify({'success': False, 'message': 'Verification code has expired. Request a new code.', 'error': 'otp_expired'}), 400

    if db_otp.attempts >= db_otp.max_attempts:
        return jsonify({'success': False, 'message': 'Too many wrong verification attempts. Code locked.', 'error': 'otp_locked'}), 403

    # Check match
    hashed_input = hash_otp(otp)
    if db_otp.otp_hash != hashed_input:
        db_otp.attempts += 1
        db.session.commit()
        remaining = db_otp.max_attempts - db_otp.attempts
        return jsonify({
            'success': False, 
            'message': f'Invalid verification code. {remaining} attempts remaining.',
            'error': 'otp_invalid',
            'attempts_remaining': remaining
        }), 400

    try:
        # Mark OTP as verified
        db_otp.verified = True
        db_otp.verified_at = datetime.utcnow()
        
        # Activate User
        user = User.query.filter_by(email=email).first()
        if not user:
            return jsonify({'success': False, 'message': 'Student profile not found', 'error': 'user_not_found'}), 404

        user.status = 'active'
        user.email_verified = True
        db.session.commit()
        
        return jsonify({
            'success': True,
            'message': 'Account verification successful! You can now log in.',
            'data': user.to_dict()
        }), 201

    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'message': 'Database error during account activation.', 'error': str(e)}), 500


# --- LOGIN FLOW (NO OTP REQUIRED) ---

@auth_bp.route('/login', methods=['POST'])
def login():
    """Validates login credentials and immediately issues final JWT token."""
    data = request.get_json() or {}
    identity = (data.get('identity') or '').strip()
    password = (data.get('password') or '').strip()

    if not (identity and password):
        return jsonify({'success': False, 'message': 'Username/Email and password are required', 'error': 'missing_fields'}), 400

    # Search user by email, username, or student roll number
    user = User.query.filter((User.username == identity) | (User.email == identity)).first()
    if not user:
        # Check student roll number
        student = Student.query.filter_by(roll_no=identity).first()
        if student:
            user = student.user

    if not user or not user.check_password(password):
        return jsonify({'success': False, 'message': 'Invalid username/email or password', 'error': 'unauthorized'}), 401

    if not user.email_verified or user.status == 'inactive':
        return jsonify({'success': False, 'message': 'Account is unverified or inactive. Please complete email verification.', 'error': 'account_inactive'}), 403

    # Load profile details
    profile_info = {}
    if user.role == 'student':
        profile_info = user.student_profile.to_dict() if user.student_profile else {}
    elif user.role in ['faculty', 'hod', 'exam_cell', 'placement_officer', 'hostel_admin', 'transport_admin', 'maintenance_staff', 'librarian']:
        profile_info = user.staff_profile.to_dict() if user.staff_profile else {}
    elif user.role == 'super_admin':
        profile_info = user.admin_profile.to_dict() if user.admin_profile else {}

    # Issue JWT token directly
    additional_claims = {
        'role': user.role,
        'username': user.username,
        'email': user.email
    }
    
    access_token = create_access_token(
        identity=str(user.id),
        additional_claims=additional_claims
    )

    return jsonify({
        'success': True,
        'message': 'Login successful',
        'data': {
            'token': access_token,
            'user': {
                'id': user.id,
                'username': user.username,
                'email': user.email,
                'role': user.role,
                'profile': profile_info
            }
        }
    }), 200


@auth_bp.route('/login/verify-otp', methods=['POST'])
def login_verify_otp():
    """Fallback endpoint for legacy tests/interfaces. Simply routes to direct login validation."""
    return login()


# --- GOOGLE OAUTH 2.0 / GOOGLE SIGN-IN FLOW ---

@auth_bp.route('/google', methods=['POST'])
def google_auth():
    """
    Verifies Google ID Token via Google Identity Services and logs in or creates user account.
    """
    data = request.get_json() or {}
    credential = (data.get('credential') or '').strip()

    if not credential:
        return jsonify({'success': False, 'message': 'Google credential token is required', 'error': 'missing_credential'}), 400

    google_client_id = current_app.config.get('GOOGLE_CLIENT_ID')
    if not google_client_id:
        return jsonify({'success': False, 'message': 'Google OAuth Client ID is not configured on the server. Please set GOOGLE_CLIENT_ID in your environment variables.', 'error': 'google_not_configured'}), 500

    try:
        idinfo = id_token.verify_oauth2_token(
            credential,
            google_requests.Request(),
            google_client_id
        )
    except ValueError as e:
        return jsonify({'success': False, 'message': 'Invalid or expired Google token', 'error': 'invalid_token'}), 401
    except Exception as e:
        return jsonify({'success': False, 'message': f'Google token verification failed: {str(e)}', 'error': 'verification_failed'}), 401

    google_sub = idinfo.get('sub')
    email = (idinfo.get('email') or '').strip().lower()
    name = (idinfo.get('name') or '').strip()
    picture = idinfo.get('picture')
    email_verified = idinfo.get('email_verified', False)

    if not google_sub or not email:
        return jsonify({'success': False, 'message': 'Google token is missing essential user identity claims', 'error': 'invalid_claims'}), 400

    if not email_verified:
        return jsonify({'success': False, 'message': 'Google account email is not verified. Please verify your Google email address first.', 'error': 'email_unverified'}), 403

    try:
        # Check if user already exists
        user = User.query.filter_by(google_id=google_sub).first()
        if not user:
            user = User.query.filter_by(email=email).first()
            if user:
                user.google_id = google_sub
                if not user.email_verified:
                    user.email_verified = True
                if picture and not user.avatar_url:
                    user.avatar_url = picture
                db.session.commit()

        # Check if registration details (roll_no, department) are needed
        needs_registration = False
        if not user:
            needs_registration = True
        elif user.role == 'student':
            if not user.student_profile or not user.student_profile.roll_no:
                needs_registration = True

        if needs_registration:
            return jsonify({
                'success': True,
                'needs_registration': True,
                'message': 'Google verification successful. Please complete your student registration details.',
                'data': {
                    'credential': credential,
                    'email': email,
                    'name': name,
                    'avatar_url': picture,
                    'suggested_username': name if name else email.split('@')[0]
                }
            }), 200

        # Existing user with completed profile
        if user.status == 'inactive':
            return jsonify({'success': False, 'message': 'Account is inactive. Please contact administration.', 'error': 'account_inactive'}), 403

        # Load profile details
        profile_info = {}
        if user.role == 'student':
            profile_info = user.student_profile.to_dict() if user.student_profile else {}
        elif user.role in ['faculty', 'hod', 'exam_cell', 'placement_officer', 'hostel_admin', 'transport_admin', 'maintenance_staff', 'librarian']:
            profile_info = user.staff_profile.to_dict() if user.staff_profile else {}
        elif user.role == 'super_admin':
            profile_info = user.admin_profile.to_dict() if user.admin_profile else {}

        # Issue JWT token
        additional_claims = {
            'role': user.role,
            'username': user.username,
            'email': user.email
        }
        
        access_token = create_access_token(
            identity=str(user.id),
            additional_claims=additional_claims
        )

        return jsonify({
            'success': True,
            'needs_registration': False,
            'message': 'Google login successful',
            'data': {
                'token': access_token,
                'access_token': access_token,
                'user': {
                    'id': user.id,
                    'username': user.username,
                    'email': user.email,
                    'role': user.role,
                    'google_id': user.google_id,
                    'avatar_url': user.avatar_url,
                    'profile': profile_info
                }
            }
        }), 200

    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'message': f'Database error during Google login: {str(e)}', 'error': 'db_error'}), 500


@auth_bp.route('/google/complete-registration', methods=['POST'])
def google_complete_registration():
    """
    Finalizes registration for a Google-authenticated user with their student details
    (roll_no, department, hostel, contact, etc.).
    """
    data = request.get_json() or {}
    credential = (data.get('credential') or '').strip()
    username = (data.get('username') or '').strip()
    roll_no = (data.get('roll_no') or '').strip().upper()
    department_id = data.get('department_id')
    hostel_no = (data.get('hostel_no') or '').strip() or None
    room_no = (data.get('room_no') or '').strip() or None
    contact_no = (data.get('contact_no') or '').strip() or None

    if not credential:
        return jsonify({'success': False, 'message': 'Google credential token is required', 'error': 'missing_credential'}), 400

    if not username:
        return jsonify({'success': False, 'message': 'Full name / username is required', 'error': 'missing_username'}), 400

    if not roll_no:
        return jsonify({'success': False, 'message': 'Student ID / Roll number is required', 'error': 'missing_roll_no'}), 400

    if not department_id:
        return jsonify({'success': False, 'message': 'Academic department is required', 'error': 'missing_department'}), 400

    google_client_id = current_app.config.get('GOOGLE_CLIENT_ID')
    if not google_client_id:
        return jsonify({'success': False, 'message': 'Google OAuth Client ID is not configured on the server.', 'error': 'google_not_configured'}), 500

    try:
        idinfo = id_token.verify_oauth2_token(
            credential,
            google_requests.Request(),
            google_client_id
        )
    except ValueError as e:
        return jsonify({'success': False, 'message': 'Invalid or expired Google token', 'error': 'invalid_token'}), 401
    except Exception as e:
        return jsonify({'success': False, 'message': f'Google token verification failed: {str(e)}', 'error': 'verification_failed'}), 401

    google_sub = idinfo.get('sub')
    email = (idinfo.get('email') or '').strip().lower()
    picture = idinfo.get('picture')
    email_verified = idinfo.get('email_verified', False)

    if not google_sub or not email:
        return jsonify({'success': False, 'message': 'Google token is missing essential user identity claims', 'error': 'invalid_claims'}), 400

    if not email_verified:
        return jsonify({'success': False, 'message': 'Google account email is not verified.', 'error': 'email_unverified'}), 403

    try:
        # Validate department
        dept = Department.query.get(int(department_id))
        if not dept:
            return jsonify({'success': False, 'message': 'Selected academic department does not exist', 'error': 'invalid_department'}), 400

        # Find existing user by google_id or email
        user = User.query.filter_by(google_id=google_sub).first()
        if not user:
            user = User.query.filter_by(email=email).first()

        # Check for duplicate roll_no across other students
        existing_student = Student.query.filter_by(roll_no=roll_no).first()
        if existing_student and (not user or existing_student.user_id != user.id):
            return jsonify({'success': False, 'message': f"Student ID / Roll number '{roll_no}' is already registered.", 'error': 'duplicate_roll_no'}), 409

        if not user:
            # Check unique username
            base_username = username[:40]
            unique_username = base_username
            counter = 1
            while User.query.filter_by(username=unique_username).first():
                suffix = str(counter)
                unique_username = f"{base_username[:40-len(suffix)]}_{suffix}"
                counter += 1

            random_password = secrets.token_urlsafe(32)
            user = User(
                username=unique_username,
                email=email,
                role='student',
                status='active',
                email_verified=True,
                google_id=google_sub,
                avatar_url=picture
            )
            user.set_password(random_password)
            db.session.add(user)
            db.session.flush()
        else:
            user.google_id = google_sub
            user.username = username[:50]
            user.status = 'active'
            user.email_verified = True
            if picture:
                user.avatar_url = picture
            db.session.add(user)
            db.session.flush()

        # Create or update Student profile
        student = user.student_profile
        if not student:
            student = Student(
                user_id=user.id,
                roll_no=roll_no,
                department=dept.name,
                department_id=dept.id,
                hostel_no=hostel_no,
                room_no=room_no,
                contact_no=contact_no,
                profile_photo=picture
            )
            db.session.add(student)
        else:
            student.roll_no = roll_no
            student.department = dept.name
            student.department_id = dept.id
            student.hostel_no = hostel_no
            student.room_no = room_no
            student.contact_no = contact_no
            if picture and not student.profile_photo:
                student.profile_photo = picture
            db.session.add(student)

        db.session.commit()

        # Issue JWT token
        additional_claims = {
            'role': user.role,
            'username': user.username,
            'email': user.email
        }
        
        access_token = create_access_token(
            identity=str(user.id),
            additional_claims=additional_claims
        )

        return jsonify({
            'success': True,
            'message': 'Student registration completed successfully',
            'data': {
                'token': access_token,
                'access_token': access_token,
                'user': {
                    'id': user.id,
                    'username': user.username,
                    'email': user.email,
                    'role': user.role,
                    'google_id': user.google_id,
                    'avatar_url': user.avatar_url,
                    'profile': student.to_dict()
                }
            }
        }), 201

    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'message': f'Error completing registration: {str(e)}', 'error': 'db_error'}), 500



# --- FORGOT / RESET PASSWORD OTP FLOW ---

@auth_bp.route('/forgot-password/send-otp', methods=['POST'])
def forgot_password_send_otp():
    """Generates and sends password reset verification code."""
    data = request.get_json() or {}
    email = (data.get('email') or '').strip()

    if not email or not re.match(EMAIL_REGEX, email):
        return jsonify({'success': False, 'message': 'Valid email is required', 'error': 'invalid_email'}), 400

    # Rate limiting cooldown check
    on_cooldown, remain = check_cooldown(email, 'password_reset')
    if on_cooldown:
        return jsonify({
            'success': False, 
            'message': f'Please wait {remain} seconds before requesting a new code.',
            'error': 'cooldown_active',
            'remain': remain
        }), 429

    user = User.query.filter_by(email=email).first()
    
    # Check account active
    if user and user.status == 'inactive':
        return jsonify({'success': False, 'message': 'Account is inactive. Contact Administrator', 'error': 'account_inactive'}), 403

    # Generate OTP
    otp = f"{secrets.randbelow(900000) + 100000}"
    otp_hash = hash_otp(otp)

    db_otp = OTPVerification(
        user_id=user.id if user else None,
        email=email,
        otp_hash=otp_hash,
        purpose='password_reset',
        expires_at=datetime.utcnow() + timedelta(minutes=5)
    )

    try:
        db.session.add(db_otp)
        db.session.commit()

        # Send email only if the user exists (prevents information exposure while remaining functional)
        if user:
            sent = False
            try:
                sent = EmailService.send_otp_email(user.email, user.username, otp, 'password_reset')
            except Exception as mail_err:
                current_app.logger.warning(f"Password reset email dispatch exception: {str(mail_err)}")

            if not sent:
                return jsonify({
                    'success': True,
                    'message': f'Verification code generated! Code: {otp}',
                    'demo_otp': otp,
                    'email_sent': False
                }), 200
            
        return jsonify({
            'success': True,
            'message': 'If the email exists, a verification code has been dispatched.',
            'demo_otp': otp,
            'email_sent': True
        }), 200
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'message': 'Failed to issue verification code', 'error': str(e)}), 500


@auth_bp.route('/forgot-password/verify-otp', methods=['POST'])
def forgot_password_verify_otp():
    """Verifies password reset OTP code and returns verification state."""
    data = request.get_json() or {}
    email = (data.get('email') or '').strip()
    otp = (data.get('otp') or '').strip()

    if not (email and otp):
        return jsonify({'success': False, 'message': 'Email and verification code are required', 'error': 'missing_fields'}), 400

    db_otp = OTPVerification.query.filter_by(
        email=email, purpose='password_reset', verified=False
    ).order_by(OTPVerification.created_at.desc()).first()

    if not db_otp:
        return jsonify({'success': False, 'message': 'Verification code missing or already verified', 'error': 'otp_missing'}), 400

    if db_otp.expires_at < datetime.utcnow():
        return jsonify({'success': False, 'message': 'Verification code has expired. Request a new code.', 'error': 'otp_expired'}), 400

    if db_otp.attempts >= db_otp.max_attempts:
        return jsonify({'success': False, 'message': 'Too many wrong verification attempts. Code locked.', 'error': 'otp_locked'}), 403

    # Check hash match
    hashed_input = hash_otp(otp)
    if db_otp.otp_hash != hashed_input:
        db_otp.attempts += 1
        db.session.commit()
        remaining = db_otp.max_attempts - db_otp.attempts
        return jsonify({
            'success': False,
            'message': f'Invalid verification code. {remaining} attempts remaining.',
            'error': 'otp_invalid',
            'attempts_remaining': remaining
        }), 400

    # Mark OTP verified
    db_otp.verified = True
    db_otp.verified_at = datetime.utcnow()
    db.session.commit()

    return jsonify({'success': True, 'message': 'Verification code approved successfully.'}), 200


@auth_bp.route('/reset-password', methods=['POST'])
def reset_password():
    """Resets user password if OTP has been successfully verified."""
    data = request.get_json() or {}
    email = (data.get('email') or '').strip()
    otp = (data.get('otp') or '').strip()
    new_password = (data.get('new_password') or '').strip()

    if not (email and otp and new_password):
        return jsonify({'success': False, 'message': 'Missing email, code, or new password fields', 'error': 'missing_fields'}), 400

    if len(new_password) < 6:
        return jsonify({'success': False, 'message': 'Password must be at least 6 characters long', 'error': 'password_too_short'}), 400

    # Confirm that a verified OTP exists for this email within the last 15 minutes and matches
    db_otp = OTPVerification.query.filter_by(
        email=email, purpose='password_reset', verified=True
    ).order_by(OTPVerification.verified_at.desc()).first()

    if not db_otp or db_otp.otp_hash != hash_otp(otp):
        return jsonify({'success': False, 'message': 'OTP verification not completed for this password change', 'error': 'otp_unverified'}), 400

    # Check verification timeframe window (15 minutes)
    elapsed = (datetime.utcnow() - db_otp.verified_at).total_seconds()
    if elapsed > 900: # 15 minutes
        return jsonify({'success': False, 'message': 'OTP verification session expired. Re-verify.', 'error': 'session_expired'}), 400

    user = User.query.filter_by(email=email).first()
    if not user:
        return jsonify({'success': False, 'message': 'User profile matching email not found', 'error': 'user_not_found'}), 404

    try:
        user.set_password(new_password)
        
        # Revoke the OTP to prevent reuse
        db.session.delete(db_otp)
        db.session.commit()
        
        return jsonify({'success': True, 'message': 'Your password has been reset successfully. Please log in.'}), 200
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'message': 'Database error during password reset', 'error': str(e)}), 500


# --- SESSION LOGOUT & PROFILES ---

@auth_bp.route('/logout', methods=['POST'])
@jwt_required()
def logout():
    """Logs out current user. In client, token is deleted."""
    return jsonify({
        'success': True,
        'message': 'Logged out successfully'
    }), 200


@auth_bp.route('/profile', methods=['GET'])
@jwt_required()
def get_profile():
    """Gets the profile of the current logged-in user."""
    user_id = int(get_jwt_identity())
    user = User.query.get(user_id)
    if not user:
        return jsonify({'success': False, 'message': 'User not found', 'error': 'user_not_found'}), 404

    if user.role == 'student':
        data = user.student_profile.to_dict() if user.student_profile else user.to_dict()
    elif user.staff_profile:
        data = user.staff_profile.to_dict()
    elif user.admin_profile:
        data = user.admin_profile.to_dict()
    else:
        data = user.to_dict()

    return jsonify({
        'success': True,
        'message': 'Profile retrieved successfully',
        'data': data
    }), 200


@auth_bp.route('/profile', methods=['PUT'])
@jwt_required()
def update_profile():
    """Updates user-specific profile fields."""
    user_id = int(get_jwt_identity())
    user = User.query.get(user_id)
    if not user:
        return jsonify({'success': False, 'message': 'User not found', 'error': 'user_not_found'}), 404

    data = request.get_json() or {}

    try:
        if user.role == 'student':
            student = user.student_profile
            if not student:
                return jsonify({'success': False, 'message': 'Student profile not found', 'error': 'profile_missing'}), 404
            
            student.hostel_no = data.get('hostel_no', student.hostel_no)
            student.room_no = data.get('room_no', student.room_no)
            student.contact_no = data.get('contact_no', student.contact_no)
            db.session.add(student)

        elif user.role == 'staff':
            staff = user.staff_profile
            if not staff:
                return jsonify({'success': False, 'message': 'Staff profile not found', 'error': 'profile_missing'}), 404
            
            staff.specialization = data.get('specialization', staff.specialization)
            staff.is_available = data.get('is_available', staff.is_available)
            db.session.add(staff)

        db.session.commit()
        
        # Return updated profile info
        if user.role == 'student':
            res_data = user.student_profile.to_dict()
        elif user.role in ['faculty', 'hod', 'exam_cell', 'placement_officer', 'hostel_admin', 'transport_admin', 'maintenance_staff', 'librarian']:
            res_data = user.staff_profile.to_dict()
        else:
            res_data = user.admin_profile.to_dict()

        return jsonify({
            'success': True,
            'message': 'Profile updated successfully',
            'data': res_data
        }), 200

    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'message': 'Error updating profile', 'error': str(e)}), 500


@auth_bp.route('/test-email', methods=['POST'])
def test_email():
    """Independent diagnostic test endpoint to verify email credentials settings."""
    data = request.get_json() or {}
    to_email = data.get('email', '').strip()
    
    if not to_email or not re.match(EMAIL_REGEX, to_email):
        return jsonify({'success': False, 'message': 'A valid test email address is required.', 'error': 'invalid_email'}), 400
        
    sent = EmailService.send_test_email(
        to_email, 
        "CampusFix AI — Email Service Test", 
        "Your CampusFix AI email service is configured successfully."
    )
    
    if sent:
        return jsonify({'success': True, 'message': f'Diagnostic test email dispatched successfully to {to_email}.'}), 200
    else:
        return jsonify({'success': False, 'message': 'Email delivery failed. Please check server configuration.', 'error': 'email_delivery_failed'}), 500


@auth_bp.route('/departments', methods=['GET'])
def get_public_departments():
    """Public endpoint to fetch active academic departments for registration forms."""
    try:
        depts = Department.query.filter_by(is_active=True).all()
        return jsonify({
            'success': True,
            'data': [d.to_dict() for d in depts]
        }), 200
    except Exception as e:
        return jsonify({'success': False, 'message': 'Failed to load academic divisions list', 'error': str(e)}), 500


