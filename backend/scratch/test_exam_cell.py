import sys
import json
from datetime import datetime, timedelta

sys.path.append("C:/Users/nagel/Documents/MY EVERYTHING/resume pro/backend")
sys.path.append("C:/Users/nagel/Documents/MY EVERYTHING/resume pro/backend/app")

from run import app
from app import db
from app.models.user import User, Student, Staff
from app.models.exam import ExamNotification
from app.models.department import Department
from app.models.log_feedback import Notification
from flask_jwt_extended import create_access_token

client = app.test_client()

def get_auth_headers(email):
    """Bypasses OTP verification for testing purposes by returning JWT headers directly."""
    with app.app_context():
        user = User.query.filter_by(email=email).first()
        if not user:
            raise Exception(f"User {email} not found in DB")
        token = create_access_token(identity=str(user.id), additional_claims={"role": user.role})
        return {"Authorization": f"Bearer {token}"}, token

def run_tests():
    print("=" * 60)
    print(" RUNNING PHASE 7 EXAM CELL WORKFLOW TESTS ")
    print("=" * 60)

    # 1. Exam Cell Login
    print("Test 1: Authenticating Exam Cell demo...")
    headers_ec, token_ec = get_auth_headers("examcell@example.com")
    print(" -> SUCCESS")

    # Authenticate other roles
    headers_stu_a, _ = get_auth_headers("student01@example.com") # CSE student
    headers_stu_b, _ = get_auth_headers("student2@student.edu") # ECE student
    headers_fac_cse, _ = get_auth_headers("faculty.cse.demo@example.com") # CSE Faculty
    headers_hod_cse, _ = get_auth_headers("hod.cse.demo@example.com") # CSE HOD
    headers_fac_ece, _ = get_auth_headers("faculty.ece.demo@example.com") # ECE Faculty

    with app.app_context():
        # Get CSE department & ECE department
        cse_dept = Department.query.filter_by(code="CSE").first()
        ece_dept = Department.query.filter_by(code="ECE").first()
        cse_dept_id = cse_dept.id if cse_dept else 1
        ece_dept_id = ece_dept.id if ece_dept else 2

        # Record notification count baseline
        initial_notif_count = Notification.query.count()
        print(f" -> Baseline notifications count: {initial_notif_count}")

    # 2. Student Exam Access
    print("\nTest 2: Student fetching exams list...")
    res = client.get("/api/exams", headers=headers_stu_a)
    print(f" -> Status: {res.status_code}")
    assert res.status_code == 200

    # 3. Faculty Exam Access
    print("\nTest 3: Faculty fetching exams list...")
    res = client.get("/api/exams", headers=headers_fac_cse)
    print(f" -> Status: {res.status_code}")
    assert res.status_code == 200

    # 4. HOD Exam Access
    print("\nTest 4: HOD fetching exams list...")
    res = client.get("/api/exams", headers=headers_hod_cse)
    print(f" -> Status: {res.status_code}")
    assert res.status_code == 200

    # 5 & 6. Department Visibility and General Exam Visibility
    # We will create test exams to verify isolation
    print("\nTest 5 & 6: Pre-seeding test exams for isolation verification...")
    with app.app_context():
        # Delete old test records if any left
        ExamNotification.query.filter(ExamNotification.title.like("TEST-%")).delete(synchronize_session=False)
        db.session.commit()

        # Create CSE Exam
        cse_exam = ExamNotification(
            title="TEST-CSE Exam",
            subject="Compiler Design",
            exam_date=datetime.utcnow() + timedelta(days=2),
            duration_mins=180,
            location="LHC-301",
            department_id=cse_dept_id
        )
        db.session.add(cse_exam)
        
        # Create ECE Exam
        ece_exam = ExamNotification(
            title="TEST-ECE Exam",
            subject="Digital Signal Processing",
            exam_date=datetime.utcnow() + timedelta(days=3),
            duration_mins=180,
            location="LHC-302",
            department_id=ece_dept_id
        )
        db.session.add(ece_exam)

        # Create General Exam
        general_exam = ExamNotification(
            title="TEST-General Exam",
            subject="Technical Communication",
            exam_date=datetime.utcnow() + timedelta(days=5),
            duration_mins=120,
            location="Main Hall",
            department_id=None
        )
        db.session.add(general_exam)
        db.session.commit()

        cse_exam_id = cse_exam.id
        ece_exam_id = ece_exam.id
        general_exam_id = general_exam.id

    # 7. CSE/ECE isolation
    print("\nTest 7: ECE student loading exams...")
    res = client.get("/api/exams", headers=headers_stu_b)
    ece_student_exams = json.loads(res.data)["data"]
    ece_student_exam_ids = [e["id"] for e in ece_student_exams]
    
    print(f" -> ECE Student sees exams: {[e['title'] for e in ece_student_exams]}")
    # ECE Student must see ECE Exam and General Exam, but NOT CSE Exam!
    assert cse_exam_id not in ece_student_exam_ids, "ECE Student bypassed department isolation to see CSE exam!"
    assert ece_exam_id in ece_student_exam_ids, "ECE Student cannot see ECE exam!"
    assert general_exam_id in ece_student_exam_ids, "ECE Student cannot see General exam!"

    # 8. Query parameter manipulation
    print("\nTest 8: CSE student trying to force ECE filter via parameter manipulation...")
    res = client.get(f"/api/exams?department_id={ece_dept_id}&all=true", headers=headers_stu_a)
    cse_student_exams = json.loads(res.data)["data"]
    cse_student_exam_ids = [e["id"] for e in cse_student_exams]
    print(f" -> CSE Student sees exams under ECE query: {[e['title'] for e in cse_student_exams]}")
    # CSE Student must still see CSE Exam and General Exam, and ECE exam must be isolated/blocked!
    assert ece_exam_id not in cse_student_exam_ids, "CSE Student bypassed isolation using query params!"

    # 9. Direct exam ID manipulation (IDOR check)
    print("\nTest 9: CSE student fetching ECE exam details directly by ID...")
    res = client.get(f"/api/exams/{ece_exam_id}", headers=headers_stu_a)
    print(f" -> Status: {res.status_code}")
    assert res.status_code == 403, "CSE Student loaded ECE exam detail workspace!"

    # 10. Student create exam = 403
    print("\nTest 10: Student trying to publish exam...")
    res = client.post("/api/exams", headers=headers_stu_a, json={
        "title": "TEST-Malicious",
        "subject": "Hacking",
        "exam_date": "2026-08-20T10:00:00",
        "duration_mins": 60,
        "location": "Dark Room"
    })
    print(f" -> Status: {res.status_code}")
    assert res.status_code == 403

    # 11. Faculty create exam = 403
    print("\nTest 11: Faculty trying to publish exam...")
    res = client.post("/api/exams", headers=headers_fac_cse, json={
        "title": "TEST-Malicious",
        "subject": "Hacking",
        "exam_date": "2026-08-20T10:00:00",
        "duration_mins": 60,
        "location": "Dark Room"
    })
    print(f" -> Status: {res.status_code}")
    assert res.status_code == 403

    # 12. HOD create exam = 403
    print("\nTest 12: HOD trying to publish exam...")
    res = client.post("/api/exams", headers=headers_hod_cse, json={
        "title": "TEST-Malicious",
        "subject": "Hacking",
        "exam_date": "2026-08-20T10:00:00",
        "duration_mins": 60,
        "location": "Dark Room"
    })
    print(f" -> Status: {res.status_code}")
    assert res.status_code == 403

    # 13. Student update exam = 403
    print("\nTest 13: Student trying to update exam...")
    res = client.put(f"/api/exams/{cse_exam_id}", headers=headers_stu_a, json={
        "title": "TEST-Altered",
        "subject": "Compiler Design",
        "exam_date": "2026-08-20T10:00:00",
        "duration_mins": 180,
        "location": "LHC-301"
    })
    print(f" -> Status: {res.status_code}")
    assert res.status_code == 403

    # 14. Student delete exam = 403
    print("\nTest 14: Student trying to delete exam...")
    res = client.delete(f"/api/exams/{cse_exam_id}", headers=headers_stu_a)
    print(f" -> Status: {res.status_code}")
    assert res.status_code == 403

    # 15. Exam Cell create = success
    print("\nTest 15: Exam Cell publishing a valid exam...")
    res = client.post("/api/exams", headers=headers_ec, json={
        "title": "TEST-New Published Exam",
        "subject": "Distributed Systems",
        "exam_date": "2026-08-22T10:00:00",
        "duration_mins": 180,
        "location": "LHC-104",
        "department_id": cse_dept_id
    })
    print(f" -> Status: {res.status_code}")
    assert res.status_code == 201
    new_exam_id = json.loads(res.data)["data"]["id"]

    # 16. Exam Cell update = success
    print("\nTest 16: Exam Cell updating the published exam...")
    res = client.put(f"/api/exams/{new_exam_id}", headers=headers_ec, json={
        "title": "TEST-New Published Exam",
        "subject": "Distributed Systems",
        "exam_date": "2026-08-23T14:00:00", # Changed date/time
        "duration_mins": 180,
        "location": "LHC-204", # Changed location
        "department_id": cse_dept_id
    })
    print(f" -> Status: {res.status_code}")
    assert res.status_code == 200

    # 17. Exam Cell delete = success
    print("\nTest 17: Exam Cell deleting the published exam...")
    res = client.delete(f"/api/exams/{new_exam_id}", headers=headers_ec)
    print(f" -> Status: {res.status_code}")
    assert res.status_code == 200

    # 18. Invalid department = validation failure
    print("\nTest 18: Exam Cell publishing exam with invalid department ID...")
    res = client.post("/api/exams", headers=headers_ec, json={
        "title": "TEST-Invalid",
        "subject": "Distributed Systems",
        "exam_date": "2026-08-22T10:00:00",
        "duration_mins": 180,
        "location": "LHC-104",
        "department_id": 99999
    })
    print(f" -> Status: {res.status_code}")
    assert res.status_code == 400

    # 19. Notification generation
    print("\nTest 19: Checking if student notifications were generated upon creation...")
    with app.app_context():
        # Get count of student notifications
        user_a = User.query.filter_by(email="student01@example.com").first()
        student_notifs = Notification.query.filter_by(user_id=user_a.id, type="exam").all()
        print(f" -> CSE Student has {len(student_notifs)} exam notifications")
        assert len(student_notifs) > 0, "No notifications created for target student!"

    # 20. Notification duplication protection
    print("\nTest 20: Testing update without changes doesn't duplicate notifications...")
    # Since dates might have minor variations in iso formats, let's fetch current and submit exact same
    with app.app_context():
        pre_update_count = Notification.query.count()
        curr_exam = ExamNotification.query.get(cse_exam_id)
        curr_exam_date = curr_exam.exam_date.isoformat()
        
    res = client.put(f"/api/exams/{cse_exam_id}", headers=headers_ec, json={
        "title": curr_exam.title,
        "subject": curr_exam.subject,
        "exam_date": curr_exam_date,
        "duration_mins": curr_exam.duration_mins,
        "location": curr_exam.location,
        "department_id": curr_exam.department_id
    })
    
    with app.app_context():
        post_update_count = Notification.query.count()
        print(f" -> Notifications count before: {pre_update_count}, after: {post_update_count}")
        assert pre_update_count == post_update_count, "Duplicate notifications sent on identical detail update!"

    # Clean up test exams
    print("\nCleaning up test exam notifications from DB...")
    with app.app_context():
        ExamNotification.query.filter(ExamNotification.title.like("TEST-%")).delete(synchronize_session=False)
        db.session.commit()
    print(" -> Cleanup SUCCESS")

    print("\n" + "=" * 60)
    print(" ALL EXAM CELL WORKFLOW AND SECURITY CHECKS PASSED ")
    print("=" * 60)

if __name__ == "__main__":
    run_tests()
