import sys
import json
import os
from datetime import datetime, timedelta

sys.path.append("C:/Users/nagel/Documents/MY EVERYTHING/resume pro/backend")
sys.path.append("C:/Users/nagel/Documents/MY EVERYTHING/resume pro/backend/app")

from run import app
from app import db
from app.models.user import User
from app.models.otp import OTPVerification
from app.routes.auth import hash_otp

client = app.test_client()

def run_tests():
    print("=" * 60)
    print(" RUNNING FORGOT PASSWORD SECURITY & OTP TESTS ")
    print("=" * 60)

    test_email = "balajinagella7@gmail.com" # Exists in DB (student1)
    
    # 1. Trigger forgot password OTP request
    print("\nTest 1: Triggering forgot password OTP request...")
    res = client.post("/api/auth/forgot-password/send-otp", json={"email": test_email})
    assert res.status_code == 200
    print(" -> Success: OTP sent message returned.")

    # 2. Extract and mock the OTP value securely in DB
    with app.app_context():
        otp_rec = OTPVerification.query.filter_by(
            email=test_email, purpose='password_reset', verified=False
        ).order_by(OTPVerification.created_at.desc()).first()
        assert otp_rec is not None
        
        mock_otp = "888888"
        otp_rec.otp_hash = hash_otp(mock_otp)
        db.session.commit()

    # 3. Verify wrong OTP -> FAIL
    print("\nTest 2: Verifying wrong forgot password OTP (expect 400)...")
    res_wrong = client.post("/api/auth/forgot-password/verify-otp", json={
        "email": test_email,
        "otp": "999999" # Wrong code
    })
    assert res_wrong.status_code == 400
    print(" -> PASS: Wrong OTP rejected.")

    # 4. Verify valid OTP -> PASS
    print("\nTest 3: Verifying valid forgot password OTP (expect 200)...")
    res_valid = client.post("/api/auth/forgot-password/verify-otp", json={
        "email": test_email,
        "otp": mock_otp
    })
    assert res_valid.status_code == 200
    print(" -> PASS: Valid OTP accepted.")

    # 5. Reset password with unverified OTP -> FAIL
    print("\nTest 4: Resetting password using wrong/reused OTP or email (expect 400)...")
    res_bad_reset = client.post("/api/auth/reset-password", json={
        "email": test_email,
        "otp": "999999", # Non-matching
        "new_password": "NewSecurePassword123"
    })
    assert res_bad_reset.status_code == 400
    print(" -> PASS: Reset rejected.")

    # 6. Reset password with verified OTP -> PASS
    print("\nTest 5: Resetting password with verified OTP (expect 200)...")
    res_reset = client.post("/api/auth/reset-password", json={
        "email": test_email,
        "otp": mock_otp,
        "new_password": "NewSecurePassword123"
    })
    assert res_reset.status_code == 200
    print(" -> PASS: Password reset successfully completed.")

    # 7. Verify login with the NEW password -> PASS
    print("\nTest 6: Verify login with the NEW password...")
    res_new_login = client.post("/api/auth/login", json={
        "identity": test_email,
        "password": "NewSecurePassword123"
    })
    assert res_new_login.status_code == 200
    assert json.loads(res_new_login.data)["success"] is True
    print(" -> PASS: Login with new password succeeded.")

    # 8. Restore the original password for demo account stability (password123)
    print("\nRestoring original demo password...")
    with app.app_context():
        user = User.query.filter_by(email=test_email).first()
        if user:
            user.set_password("password123")
            db.session.commit()
    print(" -> Demo password restored successfully.")

    print("\n" + "=" * 60)
    print(" ALL FORGOT PASSWORD OTP SECURITY TESTS PASSED ")
    print("=" * 60)

if __name__ == "__main__":
    run_tests()
