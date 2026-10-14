import sys
import json

sys.path.append("C:/Users/nagel/Documents/MY EVERYTHING/resume pro/backend")
sys.path.append("C:/Users/nagel/Documents/MY EVERYTHING/resume pro/backend/app")

from run import app

# Flask test client
client = app.test_client()

def get_auth_headers(email):
    """Simulate user login and return authorization headers."""
    with app.app_context():
        from app.models.user import User
        user = User.query.filter_by(email=email).first()
        if not user:
            raise Exception(f"User {email} not found")
        
        from flask_jwt_extended import create_access_token
        token = create_access_token(identity=str(user.id), additional_claims={"role": user.role})
        return {"Authorization": f"Bearer {token}"}, token

def run_tests():
    print("=" * 60)
    print(" RUNNING PHASE 12 ADMIN ANALYTICS WORKFLOW & RBAC TESTS ")
    print("=" * 60)

    # 1. Authenticate users
    print("Test 1: Authenticating role profiles...")
    headers_adm, _ = get_auth_headers("admin1@college.edu")   # Super Admin
    headers_stu, _ = get_auth_headers("balajinagella7@gmail.com")   # Student
    headers_fac, _ = get_auth_headers("faculty01@example.com") # Faculty
    headers_hod, _ = get_auth_headers("hod01@example.com")   # HOD (CSE)
    print(" -> SUCCESS")

    # 2. Unauthenticated Protected Access
    print("\nTest 2: Unauthenticated access block...")
    for endpoint in ['overview', 'attendance', 'modules']:
        res = client.get(f"/api/admin/analytics/{endpoint}")
        print(f" -> GET /api/admin/analytics/{endpoint} status: {res.status_code}")
        assert res.status_code == 401
    print(" -> PASS")

    # 3. Student RBAC Block
    print("\nTest 3: Student RBAC block check...")
    for endpoint in ['overview', 'attendance', 'modules']:
        res = client.get(f"/api/admin/analytics/{endpoint}", headers=headers_stu)
        print(f" -> Student access GET /api/admin/analytics/{endpoint} status: {res.status_code}")
        assert res.status_code == 403
    print(" -> PASS")

    # 4. Faculty RBAC Block
    print("\nTest 4: Faculty RBAC block check...")
    for endpoint in ['overview', 'attendance', 'modules']:
        res = client.get(f"/api/admin/analytics/{endpoint}", headers=headers_fac)
        print(f" -> Faculty access GET /api/admin/analytics/{endpoint} status: {res.status_code}")
        assert res.status_code == 403
    print(" -> PASS")

    # 5. HOD initial restriction check (HOD analytics excluded from Phase 12)
    print("\nTest 5: HOD initial analytics access block check...")
    for endpoint in ['overview', 'attendance', 'modules']:
        res = client.get(f"/api/admin/analytics/{endpoint}", headers=headers_hod)
        print(f" -> HOD access GET /api/admin/analytics/{endpoint} status: {res.status_code}")
        assert res.status_code == 403
    print(" -> PASS")

    # 6. Authorized Admin Access
    print("\nTest 6: Admin analytics query check...")
    
    # Overview
    res_ov = client.get("/api/admin/analytics/overview", headers=headers_adm)
    print(f" -> Admin GET overview status: {res_ov.status_code}")
    assert res_ov.status_code == 200
    ov_data = json.loads(res_ov.data)["data"]
    assert "total_students" in ov_data
    assert "total_staff" in ov_data
    assert "open_grievances" in ov_data
    
    # Attendance
    res_att = client.get("/api/admin/analytics/attendance", headers=headers_adm)
    print(f" -> Admin GET attendance status: {res_att.status_code}")
    assert res_att.status_code == 200
    att_data = json.loads(res_att.data)["data"]
    assert "average_attendance" in att_data
    assert "students_shortage" in att_data
    assert "by_department" in att_data
    
    # Modules
    res_mod = client.get("/api/admin/analytics/modules", headers=headers_adm)
    print(f" -> Admin GET modules status: {res_mod.status_code}")
    assert res_mod.status_code == 200
    mod_data = json.loads(res_mod.data)["data"]
    assert "hostel" in mod_data
    assert "transport" in mod_data
    assert "library" in mod_data
    assert "placements" in mod_data
    assert "exams" in mod_data
    print(" -> PASS")

    # 7. Credential exposure safety check
    print("\nTest 7: Credential leakage check...")
    for data_dict in [ov_data, att_data, mod_data]:
        data_str = json.dumps(data_dict).lower()
        for secret_kw in ["password", "secret", "smtp", "token", "key"]:
            assert secret_kw not in data_str or secret_kw == "key" and "range" in data_str, f"Leaked potential sensitive term '{secret_kw}' in analytics payload!"
    print(" -> Leak check: PASS")

    print("=" * 60)
    print(" ALL PHASE 12 WORKFLOW AND RBAC CHECKS PASSED SUCCESS ")
    print("=" * 60)

if __name__ == "__main__":
    run_tests()
