import sys
import json
import os
from datetime import datetime, timedelta

sys.path.append("C:/Users/nagel/Documents/MY EVERYTHING/resume pro/backend")
sys.path.append("C:/Users/nagel/Documents/MY EVERYTHING/resume pro/backend/app")

from run import app
from app import db
from app.models.user import User, Student
from app.models.otp import OTPVerification
from app.routes.auth import hash_otp

client = app.test_client()

def run_tests():
    print("=" * 60)
    print(" RUNNING REGISTRATION & LOGIN AUTHENTICATION FLOW TESTS ")
    print("=" * 60)

    test_username = "teststudent_reg"
    test_email = "teststudent_reg@student.edu"
    test_roll = "REG-TEST-001"
    test_pass = "TestPassword123"

    # Clean up any leftover test data first
    with app.app_context():
        u = User.query.filter_by(email=test_email).first()
        if u:
            db.session.delete(u)
        db_otps = OTPVerification.query.filter_by(email=test_email).all()
        for o in db_otps:
            db.session.delete(o)
        db.session.commit()

    # 1. Registration step 1: Request OTP (Registration without verification -> FAIL, user is inactive)
    print("\nTest 1: Registration step 1 - create unverified pending account...")
    res1 = client.post("/api/auth/register/send-otp", json={
        "username": test_username,
        "email": test_email,
        "password": test_pass,
        "roll_no": test_roll,
        "department_id": 1, # CSE
        "hostel_no": "Block A",
        "room_no": "101",
        "contact_no": "9999999999"
    })
    assert res1.status_code == 200
    print(" -> OTP Sent. Pending account created in database.")

    # Verify unverified registration account cannot login
    print("\nTest 2: Unverified registration account cannot login (expect 403)...")
    res_login_fail = client.post("/api/auth/login", json={
        "identity": test_email,
        "password": test_pass
    })
    assert res_login_fail.status_code == 403
    assert json.loads(res_login_fail.data)["error"] == "account_inactive"
    print(" -> PASS: Unverified account login blocked.")

    # 2. Registration with wrong OTP -> FAIL
    print("\nTest 3: Verify registration with WRONG OTP (expect 400)...")
    res_wrong = client.post("/api/auth/register/verify-otp", json={
        "email": test_email,
        "otp": "999999" # wrong OTP
    })
    assert res_wrong.status_code == 400
    assert json.loads(res_wrong.data)["error"] == "otp_invalid"
    print(" -> PASS: Registration verification with wrong OTP blocked.")

    # 3. Registration with expired OTP -> FAIL
    print("\nTest 4: Verify registration with EXPIRED OTP (expect 400)...")
    with app.app_context():
        otp_rec = OTPVerification.query.filter_by(email=test_email, purpose='registration').first()
        if otp_rec:
            otp_rec.expires_at = datetime.utcnow() - timedelta(minutes=1)
            db.session.commit()
    res_exp = client.post("/api/auth/register/verify-otp", json={
        "email": test_email,
        "otp": "123456" # Any code
    })
    assert res_exp.status_code == 400
    assert json.loads(res_exp.data)["error"] == "otp_expired"
    print(" -> PASS: Expired OTP rejected.")

    # 4. Resend OTP -> PASS
    print("\nTest 5: Resend OTP (creates new OTP and invalidates old ones)...")
    # Reset expires_at to clean status first for rate-limiting bypass
    with app.app_context():
        otp_rec = OTPVerification.query.filter_by(email=test_email, purpose='registration').first()
        if otp_rec:
            otp_rec.created_at = datetime.utcnow() - timedelta(seconds=70)
            db.session.commit()

    res_resend = client.post("/api/auth/register/send-otp", json={
        "username": test_username,
        "email": test_email,
        "password": test_pass,
        "roll_no": test_roll,
        "department_id": 1,
        "hostel_no": "Block A",
        "room_no": "101",
        "contact_no": "9999999999"
    })
    assert res_resend.status_code == 200
    print(" -> PASS: OTP Resent successfully.")

    # Extract the new OTP from DB for successful verification
    with app.app_context():
        # Find latest OTP verification record
        db_otp = OTPVerification.query.filter_by(
            email=test_email, purpose='registration', verified=False
        ).order_by(OTPVerification.created_at.desc()).first()
        
        # We need to bypass secure hashing by retrieving the generated value or mocking it
        # Since we hash it, let's inject a known hash to verify
        mock_otp = "123456"
        db_otp.otp_hash = hash_otp(mock_otp)
        db.session.commit()

    # 5. Registration with valid OTP -> PASS
    print("\nTest 6: Verify registration with VALID OTP (expect 201)...")
    res_verify = client.post("/api/auth/register/verify-otp", json={
        "email": test_email,
        "otp": mock_otp
    })
    assert res_verify.status_code == 201
    assert json.loads(res_verify.data)["success"] is True
    print(" -> PASS: Registration verified successfully, account activated.")

    # 6. Registration with reused OTP -> FAIL
    print("\nTest 7: Verify registration with REUSED OTP (expect 400)...")
    res_reuse = client.post("/api/auth/register/verify-otp", json={
        "email": test_email,
        "otp": mock_otp
    })
    assert res_reuse.status_code == 400
    print(" -> PASS: Reused OTP rejected.")

    # 7. Normal login with verified email + password -> PASS
    print("\nTest 8: Normal login with verified credentials...")
    res_login = client.post("/api/auth/login", json={
        "identity": test_email,
        "password": test_pass
    })
    assert res_login.status_code == 200
    login_data = json.loads(res_login.data)
    assert login_data["success"] is True
    assert "token" in login_data["data"]
    # Verify that login response does NOT ask for OTP
    assert "require_otp" not in login_data
    print(" -> PASS: Login successful directly with JWT returned. NO OTP required.")

    # 8. Normal login with wrong password -> FAIL
    print("\nTest 9: Normal login with WRONG password (expect 401)...")
    res_login_wrong = client.post("/api/auth/login", json={
        "identity": test_email,
        "password": "WrongPassword123"
    })
    assert res_login_wrong.status_code == 401
    print(" -> PASS: Login with wrong password rejected.")

    # 9. Clean up test user
    with app.app_context():
        u = User.query.filter_by(email=test_email).first()
        if u:
            db.session.delete(u)
        db_otps = OTPVerification.query.filter_by(email=test_email).all()
        for o in db_otps:
            db.session.delete(o)
        db.session.commit()
    print("\n" + "=" * 60)
    print(" ALL REGISTRATION & LOGIN AUTHENTICATION TESTS PASSED ")
    print("=" * 60)

if __name__ == "__main__":
    run_tests()
