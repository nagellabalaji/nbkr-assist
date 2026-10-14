# OTP Validation Unit Test Script
import sys
import os
from datetime import datetime, timedelta

# Adjust path to import app package
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), 'app')))
sys.path.append(os.path.abspath(os.path.dirname(__file__)))

from run import app
from app import db
from app.models.otp import OTPVerification
from app.routes.auth import hash_otp

def run_otp_test():
    print("=" * 60)
    print(" EXECUTE OTP VERIFICATION SCHEMA & LOGIC ASSERTION TESTS ")
    print("=" * 60)

    with app.app_context():
        test_email = "testuser@college.edu"
        test_otp = "889900"
        hashed = hash_otp(test_otp)

        # Clear existing test entries
        OTPVerification.query.filter_by(email=test_email).delete()
        db.session.commit()

        # Test Case 1: Create OTPVerification
        print("\nTest Case 1: Inserting verification token...")
        db_otp = OTPVerification(
            email=test_email,
            otp_hash=hashed,
            purpose='registration',
            expires_at=datetime.utcnow() + timedelta(minutes=5)
        )
        db.session.add(db_otp)
        db.session.commit()
        print(" -> OTP record inserted successfully!")

        # Test Case 2: Verify Match
        print("\nTest Case 2: Matching hash verification...")
        queried = OTPVerification.query.filter_by(email=test_email, verified=False).first()
        if queried and queried.otp_hash == hash_otp(test_otp):
            print(" -> Match successful: Code verified correctly!")
        else:
            print(" -> Error: Code match failed.")
            sys.exit(1)

        # Test Case 3: Test Expiry Assertions
        print("\nTest Case 3: Testing expiration bounds...")
        expired_otp = OTPVerification(
            email=test_email,
            otp_hash=hashed,
            purpose='login',
            expires_at=datetime.utcnow() - timedelta(minutes=1) # Set in the past
        )
        db.session.add(expired_otp)
        db.session.commit()
        
        check_expired = OTPVerification.query.filter_by(email=test_email, purpose='login').order_by(OTPVerification.created_at.desc()).first()
        if check_expired and check_expired.expires_at < datetime.utcnow():
            print(" -> Expiry bounds checked successfully: Past timestamp detected as expired!")
        else:
            print(" -> Error: Expiration bounds check failed.")
            sys.exit(1)

        # Cleanup
        OTPVerification.query.filter_by(email=test_email).delete()
        db.session.commit()
        print("\nAll OTP DB & Hashing assertions PASSED successfully!")
        print("=" * 60)

if __name__ == '__main__':
    run_otp_test()
