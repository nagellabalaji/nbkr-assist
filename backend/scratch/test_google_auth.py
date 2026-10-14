import sys
import json
import os
from unittest.mock import patch

sys.path.append("C:/Users/nagel/Documents/MY EVERYTHING/resume pro/backend")
sys.path.append("C:/Users/nagel/Documents/MY EVERYTHING/resume pro/backend/app")

from run import app
from app import db
from app.models.user import User, Student
from app.models.department import Department

client = app.test_client()

def run_google_auth_tests():
    print("=" * 60)
    print(" RUNNING GOOGLE OAUTH 2.0 ONBOARDING & REGISTRATION TESTS ")
    print("=" * 60)

    test_client_id = "test-client-id-123.apps.googleusercontent.com"
    app.config["GOOGLE_CLIENT_ID"] = test_client_id

    test_sub_new = "google_sub_test_2001"
    test_email_new = "newgoogleuser_onboard@test.edu"
    test_name_new = "Balaji Nagella Student"
    test_pic_new = "https://lh3.googleusercontent.com/a/test_pic_onboard"
    test_roll_new = "21CS999"

    test_sub_link = "google_sub_test_2002"
    test_email_link = "linkuser_onboard@test.edu"

    with app.app_context():
        # Cleanup any existing test users
        for email in [test_email_new, test_email_link]:
            u = User.query.filter_by(email=email).first()
            if u:
                student = Student.query.filter_by(user_id=u.id).first()
                if student:
                    db.session.delete(student)
                db.session.delete(u)
        # Also clean test_roll_new if exists
        st = Student.query.filter_by(roll_no=test_roll_new).first()
        if st:
            u_st = User.query.get(st.user_id)
            db.session.delete(st)
            if u_st:
                db.session.delete(u_st)
        db.session.commit()

    # 1. Missing credential
    print("\nTest 1: Missing credential returns 400...")
    res = client.post("/api/auth/google", json={})
    assert res.status_code == 400
    data = json.loads(res.data)
    assert data["success"] is False
    assert "required" in data["message"].lower()
    print(" -> PASS: 400 Bad Request returned for missing credential.")

    # 2. Server missing GOOGLE_CLIENT_ID returns 500
    print("\nTest 2: Missing server GOOGLE_CLIENT_ID returns 500...")
    app.config["GOOGLE_CLIENT_ID"] = None
    res = client.post("/api/auth/google", json={"credential": "some_token"})
    assert res.status_code == 500
    data = json.loads(res.data)
    assert data["error"] == "google_not_configured"
    print(" -> PASS: 500 returned with clear instructions when GOOGLE_CLIENT_ID is unset.")
    app.config["GOOGLE_CLIENT_ID"] = test_client_id

    # 3. Invalid token returns 401
    print("\nTest 3: Invalid/expired token returns 401...")
    with patch("app.routes.auth.id_token.verify_oauth2_token", side_effect=ValueError("Token expired")):
        res = client.post("/api/auth/google", json={"credential": "invalid_dummy_token"})
        assert res.status_code == 401
        data = json.loads(res.data)
        assert data["success"] is False
        assert "invalid or expired google token" in data["message"].lower()
    print(" -> PASS: 401 Unauthorized returned for invalid token.")

    # 4. Unverified email returns 403
    print("\nTest 4: Unverified email returns 403...")
    with patch("app.routes.auth.id_token.verify_oauth2_token", return_value={
        "sub": "sub_unverified",
        "email": "unverified@test.edu",
        "email_verified": False
    }):
        res = client.post("/api/auth/google", json={"credential": "unverified_token"})
        assert res.status_code == 403
        data = json.loads(res.data)
        assert "not verified" in data["message"].lower()
    print(" -> PASS: 403 Forbidden returned for unverified Google email.")

    # 5. First-time Google user -> returns needs_registration: True
    print("\nTest 5: First-time Google user prompts for registration details...")
    mock_new_claims = {
        "sub": test_sub_new,
        "email": test_email_new,
        "email_verified": True,
        "name": test_name_new,
        "picture": test_pic_new
    }
    with patch("app.routes.auth.id_token.verify_oauth2_token", return_value=mock_new_claims):
        res = client.post("/api/auth/google", json={"credential": "mock_valid_token_new"})
        assert res.status_code == 200
        data = json.loads(res.data)
        assert data["success"] is True
        assert data["needs_registration"] is True
        assert data["data"]["email"] == test_email_new
        assert data["data"]["name"] == test_name_new
        assert data["data"]["avatar_url"] == test_pic_new
    print(" -> PASS: First-time Google login returns needs_registration: True with pre-filled details.")

    # 6. Complete registration validation checks
    print("\nTest 6: Complete registration validation (missing roll_no -> 400)...")
    with patch("app.routes.auth.id_token.verify_oauth2_token", return_value=mock_new_claims):
        res_fail = client.post("/api/auth/google/complete-registration", json={
            "credential": "mock_valid_token_new",
            "username": "Test Student",
            "department_id": 1
            # missing roll_no
        })
        assert res_fail.status_code == 400
        assert "roll number is required" in json.loads(res_fail.data)["message"].lower()
    print(" -> PASS: 400 returned when required roll_no is missing.")

    # 7. Complete registration with full details creates User & Student profile
    print("\nTest 7: Complete registration with full student details...")
    with app.app_context():
        dept = Department.query.first()
        dept_id = dept.id if dept else 1

    with patch("app.routes.auth.id_token.verify_oauth2_token", return_value=mock_new_claims):
        res_reg = client.post("/api/auth/google/complete-registration", json={
            "credential": "mock_valid_token_new",
            "username": test_name_new,
            "roll_no": test_roll_new,
            "department_id": dept_id,
            "hostel_no": "Ramanujan Hall",
            "room_no": "B-204",
            "contact_no": "+91 9876543210"
        })
        assert res_reg.status_code == 201, f"Expected 201, got {res_reg.status_code}: {res_reg.data}"
        reg_data = json.loads(res_reg.data)
        assert reg_data["success"] is True
        assert "token" in reg_data["data"]
        user_info = reg_data["data"]["user"]
        assert user_info["email"] == test_email_new
        assert user_info["username"] == test_name_new
        assert user_info["google_id"] == test_sub_new
        assert user_info["profile"]["roll_no"] == test_roll_new
        assert user_info["profile"]["hostel_no"] == "Ramanujan Hall"

    with app.app_context():
        created_user = User.query.filter_by(google_id=test_sub_new).first()
        assert created_user is not None
        assert created_user.status == "active"
        assert created_user.email_verified is True
        st = Student.query.filter_by(user_id=created_user.id).first()
        assert st is not None
        assert st.roll_no == test_roll_new
        assert st.department_id == dept_id
        print(f" -> Account & Student Profile created: Roll No={st.roll_no}, Dept={st.department}")
    print(" -> PASS: Complete registration successfully created account & student profile.")

    # 8. Returning existing registered Google user login -> needs_registration: False
    print("\nTest 8: Returning registered Google user logs in directly...")
    with patch("app.routes.auth.id_token.verify_oauth2_token", return_value=mock_new_claims):
        res_ret = client.post("/api/auth/google", json={"credential": "mock_valid_token_returning"})
        assert res_ret.status_code == 200
        ret_data = json.loads(res_ret.data)
        assert ret_data["success"] is True
        assert ret_data["needs_registration"] is False
        assert "token" in ret_data["data"]
        assert ret_data["data"]["user"]["id"] == created_user.id
        assert ret_data["data"]["user"]["profile"]["roll_no"] == test_roll_new
    print(" -> PASS: Returning user logs in directly without prompting for registration details again.")

    # 9. Duplicate roll_no rejection
    print("\nTest 9: Duplicate roll_no rejection on registration...")
    mock_other_claims = {
        "sub": "google_sub_test_2003",
        "email": "other_google_user@test.edu",
        "email_verified": True,
        "name": "Other Student",
        "picture": "https://lh3.googleusercontent.com/a/other"
    }
    with patch("app.routes.auth.id_token.verify_oauth2_token", return_value=mock_other_claims):
        res_dup = client.post("/api/auth/google/complete-registration", json={
            "credential": "mock_token_other",
            "username": "Other Student",
            "roll_no": test_roll_new, # Same roll_no as test 7
            "department_id": dept_id
        })
        assert res_dup.status_code == 409
        dup_data = json.loads(res_dup.data)
        assert dup_data["error"] == "duplicate_roll_no"
    print(" -> PASS: 409 Conflict returned when attempting to register duplicate roll number.")

    # Cleanup test data
    with app.app_context():
        for email in [test_email_new, test_email_link, "other_google_user@test.edu"]:
            u = User.query.filter_by(email=email).first()
            if u:
                student = Student.query.filter_by(user_id=u.id).first()
                if student:
                    db.session.delete(student)
                db.session.delete(u)
        db.session.commit()

    print("\n" + "=" * 60)
    print(" ALL GOOGLE OAUTH ONBOARDING TESTS PASSED (9/9) ")
    print("=" * 60)

if __name__ == "__main__":
    run_google_auth_tests()
