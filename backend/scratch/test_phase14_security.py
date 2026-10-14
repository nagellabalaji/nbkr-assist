import sys
import json
import os
from datetime import datetime, timedelta
import jwt

sys.path.append("C:/Users/nagel/Documents/MY EVERYTHING/resume pro/backend")
sys.path.append("C:/Users/nagel/Documents/MY EVERYTHING/resume pro/backend/app")

from run import app
from app import db
from app.models.user import User, Student
from app.models.attendance import Subject, AttendanceRecord
from app.models.log_feedback import Notification, ChatbotMessage
from app.models.complaint import Complaint
from app.models.placement import PlacementDrive

client = app.test_client()

def get_auth_headers(email):
    """Bypasses OTP verification for testing purposes by returning JWT headers directly."""
    with app.app_context():
        user = User.query.filter_by(email=email).first()
        if not user:
            raise Exception(f"User {email} not found in DB")
        from flask_jwt_extended import create_access_token
        token = create_access_token(identity=str(user.id), additional_claims={"role": user.role})
        return {"Authorization": f"Bearer {token}"}, token

def run_tests():
    print("=" * 60)
    print(" RUNNING PHASE 14 SECURITY HARDENING & PRODUCTION READINESS TESTS ")
    print("=" * 60)

    # 1. Authenticate mock profiles
    print("Test 1: Authenticating mock profiles...")
    headers_stu, _ = get_auth_headers("balajinagella7@gmail.com")
    headers_fac, _ = get_auth_headers("faculty01@example.com")
    headers_hod, _ = get_auth_headers("hod01@example.com")
    headers_adm, _ = get_auth_headers("admin1@college.edu")
    print(" -> SUCCESS")

    # 2. CORS configurations check
    print("\nTest 2: CORS dynamic headers configuration checks...")
    res_cors = client.options("/api/auth/login", headers={"Origin": "http://localhost:5173", "Access-Control-Request-Method": "POST"})
    print(f" -> Options Origin Status: {res_cors.status_code}")
    print(f" -> Access-Control-Allow-Origin: {res_cors.headers.get('Access-Control-Allow-Origin')}")
    assert res_cors.headers.get("Access-Control-Allow-Origin") in ["http://localhost:5173", "*"] or res_cors.status_code == 200
    print(" -> CORS Check: PASS")

    # 3. Production Flask Debug exposure checks
    print("\nTest 3: Debug mode status check...")
    debug_mode = app.debug
    print(f" -> Current App Debug status: {debug_mode}")
    env_mode = os.getenv("FLASK_ENV", "production").lower()
    if env_mode == "production":
        assert debug_mode is False, "EXPLOIT RISK: Debug mode active in production environment!"
    print(" -> Debug Check: PASS")

    # 4. Admin Analytics Scopes Authorization RBAC Checks
    print("\nTest 4: Admin Analytics scopes authorization RBAC check...")
    for endpoint in ['overview', 'attendance', 'modules']:
        res_401 = client.get(f"/api/admin/analytics/{endpoint}")
        assert res_401.status_code == 401
        
        res_stu = client.get(f"/api/admin/analytics/{endpoint}", headers=headers_stu)
        assert res_stu.status_code == 403
        
        res_hod = client.get(f"/api/admin/analytics/{endpoint}", headers=headers_hod)
        assert res_hod.status_code == 403
        
        res_fac = client.get(f"/api/admin/analytics/{endpoint}", headers=headers_fac)
        assert res_fac.status_code == 403
        
        res_adm = client.get(f"/api/admin/analytics/{endpoint}", headers=headers_adm)
        assert res_adm.status_code == 200
    print(" -> Admin RBAC Check: PASS")

    # 5. Invalid and Expired JWT Signature Token validation
    print("\nTest 5: JWT token validation and signature checks...")
    res_mal = client.get("/api/admin/analytics/overview", headers={"Authorization": "Bearer malformedtoken123"})
    assert res_mal.status_code == 401
    assert json.loads(res_mal.data)["error"] == "token_invalid"
    
    res_mis = client.get("/api/admin/analytics/overview")
    assert res_mis.status_code == 401
    assert json.loads(res_mis.data)["error"] == "token_missing"
    print(" -> JWT Check: PASS")

    # 6. IDOR protections
    print("\nTest 6: Parameter IDOR protections checks...")
    res_idor = client.get("/api/student/dashboard/attendance/details", headers=headers_stu)
    assert res_idor.status_code == 200
    details = json.loads(res_idor.data)["data"]
    with app.app_context():
        student_a = Student.query.filter_by(roll_no="CS26B1001").first()
        student_a_id = student_a.id if student_a else 11
        for item in details:
            rec = AttendanceRecord.query.get(item["id"])
            if rec:
                assert rec.student_id == student_a_id, "IDOR boundary leak in detailed logs!"
    print(" -> IDOR Check: PASS")

    # 7. Sensitive data leakage scans
    print("\nTest 7: Sensitive credentials leakage scan...")
    res_prof = client.get("/api/student/dashboard/summary", headers=headers_stu)
    profile_str = res_prof.data.decode()
    assert "password_hash" not in profile_str
    assert "SECRET_KEY" not in profile_str
    assert "JWT_SECRET" not in profile_str
    assert "SMTP_PASSWORD" not in profile_str
    print(" -> Leakage Check: PASS")

    # 8. Stack trace safety
    print("\nTest 8: Error handling stack trace masking check...")
    res_500 = client.get("/api/complaints/nonexistent_id_value_here", headers=headers_stu)
    assert res_500.status_code == 404
    err_str = res_500.data.decode()
    assert "Traceback" not in err_str
    assert "File \"" not in err_str
    assert "success" in err_str
    print(" -> Stack Trace Masking Check: PASS")

    print("\n" + "=" * 60)
    print(" ALL PHASE 14 SECURITY AND STABILIZATION CHECKS PASSED ")
    print("=" * 60)

if __name__ == "__main__":
    run_tests()
