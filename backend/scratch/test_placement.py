import sys
import json
from datetime import datetime, timedelta

sys.path.append("C:/Users/nagel/Documents/MY EVERYTHING/resume pro/backend")
sys.path.append("C:/Users/nagel/Documents/MY EVERYTHING/resume pro/backend/app")

from run import app
from app import db
from app.models.user import User, Student
from app.models.placement import PlacementDrive, PlacementApplication
from app.models.attendance import Attendance
from flask_jwt_extended import create_access_token

client = app.test_client()

def get_auth_headers(email):
    """Bypasses OTP verification for testing by returning JWT headers directly."""
    with app.app_context():
        user = User.query.filter_by(email=email).first()
        if not user:
            raise Exception(f"User {email} not found")
        token = create_access_token(identity=str(user.id), additional_claims={"role": user.role})
        return {"Authorization": f"Bearer {token}"}, token

def run_tests():
    print("=" * 60)
    print(" RUNNING PHASE 9 PLACEMENT CELL WORKFLOW & SECURITY TESTS ")
    print("=" * 60)

    # Resolve credentials
    headers_stu_a, _ = get_auth_headers("balajinagella7@gmail.com") # CSE Student 1
    headers_stu_b, _ = get_auth_headers("student2@student.edu") # ECE Student 2
    headers_fac, _ = get_auth_headers("faculty01@example.com")   # CSE Faculty
    headers_hod, _ = get_auth_headers("hod01@example.com")         # CSE HOD
    headers_po, _ = get_auth_headers("placement@example.com")   # Placement Officer

    with app.app_context():
        student_a = Student.query.filter_by(roll_no="CS26B1001").first()
        student_b = Student.query.filter_by(roll_no="CS26B1002").first()
        
        student_a_id = student_a.id if student_a else 1
        student_b_id = student_b.id if student_b else 2
        
        # Pre-seed sample attendance to ensure Student A has >= 75% average attendance
        att_a = Attendance.query.filter_by(student_id=student_a_id).first()
        if not att_a:
            att_a = Attendance(student_id=student_a_id, subject="Software Engineering", percentage=80.0)
            db.session.add(att_a)
        else:
            att_a.percentage = 80.0
            
        # Give Student B attendance shortage (<75%) to verify eligibility rejection
        att_b = Attendance.query.filter_by(student_id=student_b_id).first()
        if not att_b:
            att_b = Attendance(student_id=student_b_id, subject="Embedded Systems", percentage=60.0)
            db.session.add(att_b)
        else:
            att_b.percentage = 60.0
            
        db.session.commit()
        print(" -> Seeding test student attendance data SUCCESS.")

    # 1. Unauthenticated checks
    print("\nTest 1: Unauthenticated protected API should return 401...")
    res = client.get("/api/placements/drives")
    print(f" -> Status: {res.status_code}")
    assert res.status_code == 401

    # 2. RBAC check for creating drives
    print("\nTest 2: Students, Faculty, and HODs attempting to create drive (expect 403)...")
    payload = {
        "company_name": "TestCorp",
        "job_role": "Software Developer Intern",
        "eligibility_criteria": "B.Tech CSE/IT",
        "salary_package": "6 LPA",
        "drive_date": (datetime.utcnow() + timedelta(days=5)).isoformat()
    }
    
    for headers, role in [(headers_stu_a, "Student"), (headers_fac, "Faculty"), (headers_hod, "HOD")]:
        res = client.post("/api/placements/drives", headers=headers, json=payload)
        print(f" -> {role} creation Status: {res.status_code}")
        assert res.status_code == 403

    # 3. Create drive success (Placement Officer)
    print("\nTest 3: Placement Officer creating a placement drive...")
    res = client.post("/api/placements/drives", headers=headers_po, json=payload)
    print(f" -> Status: {res.status_code}")
    assert res.status_code == 201
    drive_id = json.loads(res.data)["data"]["id"]
    print(f" -> Drive ID: {drive_id}")

    # 4. Update drive success (Placement Officer)
    print("\nTest 4: Placement Officer updating the placement drive parameters...")
    res = client.put(f"/api/placements/drives/{drive_id}", headers=headers_po, json={
        "salary_package": "7.5 LPA",
        "status": "Ongoing"
    })
    print(f" -> Status: {res.status_code}")
    assert res.status_code == 200
    assert json.loads(res.data)["data"]["salary_package"] == "7.5 LPA"
    assert json.loads(res.data)["data"]["status"] == "Ongoing"

    # 5. Invalid / nonexistent drive checks
    print("\nTest 5: Student applying to non-existent drive_id (expect 404)...")
    res = client.post("/api/placements/applications", headers=headers_stu_a, json={"drive_id": 99999})
    print(f" -> Status: {res.status_code}")
    assert res.status_code == 404

    # 6. Student applying for drive
    print("\nTest 6: Student A applying for the published drive...")
    res = client.post("/api/placements/applications", headers=headers_stu_a, json={"drive_id": drive_id})
    print(f" -> Status: {res.status_code}")
    assert res.status_code == 201
    app_id = json.loads(res.data)["data"]["id"]

    # 7. Duplicate application block
    print("\nTest 7: Student A re-applying for the same drive (expect 409 duplicate rejection)...")
    res = client.post("/api/placements/applications", headers=headers_stu_a, json={"drive_id": drive_id})
    print(f" -> Status: {res.status_code}")
    assert res.status_code == 409

    # 8. Eligibility restriction check (Attendance Shortage)
    print("\nTest 8: Dayscholar Student B with shortage (<75% attendance) applying (expect 400 rejection)...")
    res = client.post("/api/placements/applications", headers=headers_stu_b, json={"drive_id": drive_id})
    print(f" -> Status: {res.status_code}")
    assert res.status_code == 400
    assert "attendance" in json.loads(res.data)["error"]

    # 9. Server-side student_id ownership & protection checks
    print("\nTest 9: Student A attempting to manipulate student_id payload fields to apply for Student B...")
    res = client.post("/api/placements/applications", headers=headers_stu_a, json={
        "drive_id": drive_id,
        "student_id": student_b_id  # payload injection attempt
    })
    print(f" -> Status: {res.status_code}")
    # The endpoint should ignore the body's student_id and derive it from token, resulting in 409 duplicate check
    assert res.status_code == 409, "Server trusted student_id payload parameter!"

    # 10. Student IDOR checking
    print("\nTest 10: IDOR check - Student B attempting to read Student A's application log roster...")
    res = client.get("/api/placements/applications", headers=headers_stu_b)
    print(f" -> Status: {res.status_code}")
    assert res.status_code == 200
    apps = json.loads(res.data)["data"]
    assert all(a["id"] != app_id for a in apps), "Student B breached IDOR to read Student A's application!"

    # 11. Student updating status block (expect 403)
    print("\nTest 11: Student attempting to update their own application status to selected (expect 403)...")
    res = client.put(f"/api/placements/applications/{app_id}", headers=headers_stu_a, json={"status": "selected"})
    print(f" -> Status: {res.status_code}")
    assert res.status_code == 403

    # 12. Placement Officer updating status (expect 200)
    print("\nTest 12: Placement Officer shortlisting Student A's application...")
    res = client.put(f"/api/placements/applications/{app_id}", headers=headers_po, json={"status": "shortlisted"})
    print(f" -> Status: {res.status_code}")
    assert res.status_code == 200
    assert json.loads(res.data)["data"]["status"] == "shortlisted"

    # Cleanup test drive and applications
    print("\nCleaning up test drive and applications from database...")
    with app.app_context():
        PlacementApplication.query.filter_by(drive_id=drive_id).delete()
        PlacementDrive.query.filter_by(id=drive_id).delete()
        db.session.commit()
    print(" -> Cleanup SUCCESS")

    print("\n" + "=" * 60)
    print(" ALL PLACEMENT CELL PORTAL TESTS PASSED ")
    print("=" * 60)

if __name__ == "__main__":
    run_tests()
