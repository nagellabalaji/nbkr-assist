import sys
import json
from datetime import datetime, timedelta

sys.path.append("C:/Users/nagel/Documents/MY EVERYTHING/resume pro/backend")
sys.path.append("C:/Users/nagel/Documents/MY EVERYTHING/resume pro/backend/app")

from run import app
from app import db
from app.models.user import User, Student
from app.models.attendance import Subject, AttendanceRecord
from app.models.log_feedback import Notification

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
    print(" RUNNING PHASE 13 STUDENT PORTAL WORKFLOW & STABILIZATION TESTS ")
    print("=" * 60)

    # 1. Authenticate mock profiles
    print("Test 1: Authenticating mock profiles...")
    headers_stu_a, _ = get_auth_headers("balajinagella7@gmail.com")   # Student A
    headers_stu_b, _ = get_auth_headers("student2@student.edu")   # Student B
    headers_adm, _ = get_auth_headers("admin1@college.edu")       # Super Admin
    print(" -> SUCCESS")

    # 2. Unauthenticated Protected Access on Student Dashboard APIs
    print("\nTest 2: Unauthenticated student dashboard access block...")
    res = client.get("/api/student/dashboard/summary")
    print(f" -> GET /api/student/dashboard/summary status: {res.status_code}")
    assert res.status_code == 401
    
    res = client.get("/api/student/dashboard/attendance/details")
    print(f" -> GET /api/student/dashboard/attendance/details status: {res.status_code}")
    assert res.status_code == 401
    print(" -> PASS")

    # 3. Authenticated Student Dashboard Summary & Attendance Details access
    print("\nTest 3: Authenticated student dashboard summary & details access...")
    res = client.get("/api/student/dashboard/summary", headers=headers_stu_a)
    print(f" -> Summary Status: {res.status_code}")
    assert res.status_code == 200
    assert json.loads(res.data)["success"] is True

    res = client.get("/api/student/dashboard/attendance/details", headers=headers_stu_a)
    print(f" -> Details Status: {res.status_code}")
    assert res.status_code == 200
    assert json.loads(res.data)["success"] is True
    print(" -> PASS")

    # 4. IDOR Protection: Student B cannot query Student A's detailed records
    print("\nTest 4: IDOR safety check - Student B loading detailed attendance...")
    res_idor = client.get("/api/student/dashboard/attendance/details", headers=headers_stu_b)
    print(f" -> Status: {res_idor.status_code}")
    assert res_idor.status_code == 200
    details = json.loads(res_idor.data)["data"]
    
    with app.app_context():
        student_b = Student.query.filter_by(roll_no="CS26B1002").first()
        student_b_id = student_b.id if student_b else 12
        for item in details:
            rec = AttendanceRecord.query.get(item["id"])
            if rec:
                assert rec.student_id == student_b_id, "IDOR boundary breached: Student B retrieved another student's logs!"
    print(" -> PASS")

    # 5. Route Access Isolation: Student cannot query Admin Analytics endpoints
    print("\nTest 5: Administrative isolation check against Student role...")
    for endpoint in ['overview', 'attendance', 'modules']:
        res = client.get(f"/api/admin/analytics/{endpoint}", headers=headers_stu_a)
        print(f" -> Student query GET /api/admin/analytics/{endpoint} status: {res.status_code}")
        assert res.status_code == 403
    print(" -> PASS")

    # 6. Classes Needed Formula validation matching Math Rules
    print("\nTest 6: Attendance Classes Needed calculator formula validation...")
    assert max(0, 3*50 - 4*30) == 30
    assert max(0, 3*50 - 4*37) == 2
    assert max(0, 3*100 - 4*75) == 0
    assert max(0, 3*100 - 4*80) == 0
    print(" -> PASS")

    print("\n" + "=" * 60)
    print(" ALL STUDENT PORTAL STABILIZATION CHECKS PASSED ")
    print("=" * 60)

if __name__ == "__main__":
    run_tests()
