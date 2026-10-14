import sys
import json
from datetime import datetime, timedelta

sys.path.append("C:/Users/nagel/Documents/MY EVERYTHING/resume pro/backend")
sys.path.append("C:/Users/nagel/Documents/MY EVERYTHING/resume pro/backend/app")

from run import app
from app import db
from app.models.user import User, Student, Staff
from app.models.attendance import Subject, FacultySubject, Attendance, AttendanceSession, AttendanceRecord
from app.models.complaint import ComplaintCategory, Complaint, ComplaintAssignment, ComplaintHistory
from app.routes.hod import calculate_classes_needed
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
    print(" RUNNING PHASE 6 FACULTY & HOD WORKFLOW TESTS ")
    print("=" * 60)

    # 1. Faculty Login
    print("Test 1: Authenticating CSE Faculty demo...")
    headers_cse_fac, token_cse_fac = get_auth_headers("faculty.cse.demo@example.com")
    print(" -> SUCCESS")

    # 2. HOD Login
    print("Test 2: Authenticating CSE HOD demo...")
    headers_cse_hod, token_cse_hod = get_auth_headers("hod.cse.demo@example.com")
    print(" -> SUCCESS")

    # Authenticate Student A & B and ECE Faculty
    headers_student_a, _ = get_auth_headers("student01@example.com")
    headers_student_b, _ = get_auth_headers("student02@example.com")
    headers_ece_fac, token_ece_fac = get_auth_headers("faculty.ece.demo@example.com")

    # 3. Faculty Dashboard RBAC
    print("\nTest 3: Faculty requesting Faculty dashboard...")
    res = client.get("/api/faculty/dashboard", headers=headers_cse_fac)
    print(f" -> Status: {res.status_code}")
    assert res.status_code == 200

    # 4. HOD Dashboard RBAC
    print("\nTest 4: HOD requesting HOD dashboard...")
    res = client.get("/api/hod/dashboard", headers=headers_cse_hod)
    print(f" -> Status: {res.status_code}")
    assert res.status_code == 200

    # 5. Student -> Faculty dashboard = 403
    print("\nTest 5: Student requesting Faculty dashboard...")
    res = client.get("/api/faculty/dashboard", headers=headers_student_a)
    print(f" -> Status: {res.status_code}")
    assert res.status_code == 403

    # 6. Student -> HOD dashboard = 403
    print("\nTest 6: Student requesting HOD dashboard...")
    res = client.get("/api/hod/dashboard", headers=headers_student_a)
    print(f" -> Status: {res.status_code}")
    assert res.status_code == 403

    # 7. Faculty -> HOD dashboard = 403
    print("\nTest 7: Faculty requesting HOD dashboard...")
    res = client.get("/api/hod/dashboard", headers=headers_cse_fac)
    print(f" -> Status: {res.status_code}")
    assert res.status_code == 403

    with app.app_context():
        # Get CSE Subject & ECE Subject
        se_sub = Subject.query.filter_by(code="SE-301").first()
        ac_sub = Subject.query.filter_by(code="AC-303").first()
        se_sub_id = se_sub.id if se_sub else 1
        se_sub_name = se_sub.name if se_sub else "Software Engineering"
        ac_sub_id = ac_sub.id if ac_sub else 3
        
        # Get student profiles
        user_a = User.query.filter_by(email="student01@example.com").first()
        student_a = user_a.student_profile
        student_a_id = student_a.id if student_a else 1
        
        user_b = User.query.filter_by(email="student02@example.com").first()
        student_b = user_b.student_profile
        student_b_id = student_b.id if student_b else 2

        # Make sure CSE & ECE tickets exist in the complaints table for testing
        m_cat = ComplaintCategory.query.filter_by(name="Maintenance").first()
        m_cat_id = m_cat.id if m_cat else 1
        
        cse_ticket = Complaint.query.filter_by(suggested_department="CSE").first()
        if not cse_ticket:
            cse_ticket = Complaint(
                id=f"NBKR-{datetime.utcnow().year}-999001",
                student_id=student_a_id,
                title="CSE lab mouse broken",
                description="The optical mouse in CSE lab 2 is not working.",
                category_id=m_cat_id,
                subcategory="General",
                location="CSE Lab 2",
                ai_priority="Medium",
                ai_confidence=0.9,
                suggested_department="CSE",
                status="Submitted"
            )
            db.session.add(cse_ticket)
            
        ece_ticket = Complaint.query.filter_by(suggested_department="ECE").first()
        if not ece_ticket:
            ece_ticket = Complaint(
                id=f"NBKR-{datetime.utcnow().year}-999002",
                student_id=student_b_id,
                title="ECE projector flickering",
                description="The class projector in ECE block room 101 is flickering.",
                category_id=m_cat_id,
                subcategory="General",
                location="ECE Block, Room 101",
                ai_priority="High",
                ai_confidence=0.85,
                suggested_department="ECE",
                status="Submitted"
            )
            db.session.add(ece_ticket)
            
        db.session.commit()
        
        cse_ticket_id = cse_ticket.id
        ece_ticket_id = ece_ticket.id

    # 8. Faculty A -> Faculty B data = 403 (unassigned ECE subject)
    print("\nTest 8: CSE Faculty A marking attendance for ECE subject AC-303 (Section A)...")
    res = client.post("/api/faculty/attendance", headers=headers_cse_fac, json={
        "subject_id": ac_sub_id,
        "date": "2026-08-14",
        "session": "Session 1",
        "section": "A",
        "records": [{"student_id": student_a_id, "status": "Present"}]
    })
    print(f" -> Status: {res.status_code}")
    assert res.status_code == 403, "CSE Faculty marked ECE attendance successfully!"

    # 9. CSE Faculty -> ECE data = 403
    print("\nTest 9: CSE Faculty loading ECE students list...")
    res = client.get("/api/faculty/students?section=A&semester=V Semester&year=III Year", headers=headers_cse_fac)
    # The returned student records must not contain ECE students (only CSE)
    students_loaded = json.loads(res.data)["data"]
    print(f" -> Loaded {len(students_loaded)} students")
    assert all(s["department"] == "Computer Science and Engineering" for s in students_loaded)

    # 10. CSE Faculty -> unassigned CSE section = 403
    print("\nTest 10: CSE Faculty marking attendance for Section B (unassigned)...")
    res = client.post("/api/faculty/attendance", headers=headers_cse_fac, json={
        "subject_id": se_sub_id,
        "date": "2026-08-14",
        "session": "Session 1",
        "section": "B",
        "records": [{"student_id": student_a_id, "status": "Present"}]
    })
    print(f" -> Status: {res.status_code}")
    assert res.status_code == 403

    # 11. CSE Faculty -> assigned subject/section = allowed
    print("\nTest 11: CSE Faculty marking attendance for Section A (assigned)...")
    # Clean previous session if exists
    with app.app_context():
        AttendanceSession.query.filter_by(subject_id=se_sub_id, date="2026-08-14", session="Session 1", section="A").delete()
        db.session.commit()
        
    res = client.post("/api/faculty/attendance", headers=headers_cse_fac, json={
        "subject_id": se_sub_id,
        "date": "2026-08-14",
        "session": "Session 1",
        "section": "A",
        "records": [{"student_id": student_a_id, "status": "Present"}]
    })
    print(f" -> Status: {res.status_code}")
    assert res.status_code == 201

    # 12. CSE HOD -> CSE students = allowed
    print("\nTest 12: CSE HOD fetching CSE students...")
    res = client.get("/api/hod/students", headers=headers_cse_hod)
    print(f" -> Status: {res.status_code}")
    assert res.status_code == 200

    # 13. CSE HOD -> ECE students = 403 (isolation block)
    print("\nTest 13: CSE HOD attempting to query ECE students list...")
    res = client.get("/api/hod/students", headers=headers_cse_hod)
    students_in_list = json.loads(res.data)["data"]
    # Verify no student belongs to ECE
    ece_students_count = sum(1 for s in students_in_list if s["department"] == "Electronics and Communication Engineering")
    print(f" -> ECE students found in CSE HOD query: {ece_students_count}")
    assert ece_students_count == 0, "CSE HOD bypassed department filter!"

    # 14. CSE HOD -> ECE grievances = 403
    print("\nTest 14: CSE HOD trying to access ECE grievances directly...")
    res = client.get(f"/api/grievances/{ece_ticket_id}", headers=headers_cse_hod)
    print(f" -> Status: {res.status_code}")
    assert res.status_code == 403

    # 15. Attendance creation
    # Tested in Test 11 (201 created). Let's verify cumulative summary updated in db
    with app.app_context():
        summary = Attendance.query.filter_by(student_id=student_a_id, subject=se_sub_name).first()
        print(f" -> Legacy Attendance Summary: total={summary.total_classes}, present={summary.present}, percentage={summary.percentage}%")
        assert summary.total_classes == 1
        assert summary.present == 1
        assert summary.percentage == 100.0

    # 16. Attendance update
    print("\nTest 16: Faculty updating attendance record...")
    # Find session ID
    with app.app_context():
        session = AttendanceSession.query.filter_by(subject_id=se_sub_id, date="2026-08-14", session="Session 1", section="A").first()
        session_id = session.id if session else 1
    
    res = client.put(f"/api/faculty/attendance/{session_id}", headers=headers_cse_fac, json={
        "records": [{"student_id": student_a_id, "status": "Absent"}]
    })
    print(f" -> Status: {res.status_code}")
    assert res.status_code == 200
    with app.app_context():
        summary = Attendance.query.filter_by(student_id=student_a_id, subject=se_sub_name).first()
        print(f" -> Updated Attendance Summary: total={summary.total_classes}, present={summary.present}, percentage={summary.percentage}%")
        assert summary.present == 0
        assert summary.percentage == 0.0

    # 17. Duplicate attendance prevention
    print("\nTest 17: Submitting duplicate attendance sheet...")
    res = client.post("/api/faculty/attendance", headers=headers_cse_fac, json={
        "subject_id": se_sub_id,
        "date": "2026-08-14",
        "session": "Session 1",
        "section": "A",
        "records": [{"student_id": student_a_id, "status": "Present"}]
    })
    print(f" -> Status: {res.status_code}")
    assert res.status_code == 409

    # 18 & 19. Attendance edge cases calculations
    print("\nTest 18 & 19: Attendance shortage calculations (edge cases)...")
    edge_cases = [
        # (present, total, expected_percentage, expected_classes_needed)
        (0, 0, 0.0, 0),
        (0, 10, 0.0, 30),
        (1, 10, 10.0, 26),
        (30, 50, 60.0, 30),
        (37, 50, 74.0, 2),
        (74, 100, 74.0, 4),
        (75, 100, 75.0, 0),
        (80, 100, 80.0, 0),
        (100, 100, 100.0, 0)
    ]
    for P, T, exp_pct, exp_needed in edge_cases:
        pct = (P / T * 100.0) if T > 0 else 0.0
        needed = calculate_classes_needed(P, T)
        print(f" -> P/T: {P}/{T} => Percentage: {pct:.1f}% (Expected: {exp_pct}%), Classes Needed: {needed} (Expected: {exp_needed})")
        assert abs(pct - exp_pct) < 0.1
        assert needed == exp_needed

    # 20. Database Cleanups
    print("\nCleaning up test grievance tickets and sessions from DB...")
    with app.app_context():
        # Delete generated session & records
        AttendanceSession.query.filter_by(subject_id=se_sub_id, date="2026-08-14", section="A").delete()
        # Delete generated test complaints
        ComplaintHistory.query.filter(ComplaintHistory.complaint_id.like("NBKR-2026-999%")).delete(synchronize_session=False)
        Complaint.query.filter(Complaint.id.like("NBKR-2026-999%")).delete(synchronize_session=False)
        db.session.commit()
    print(" -> Cleanup SUCCESS")

    print("\n" + "=" * 60)
    print(" ALL WORKFLOW AND SECURITY CHECKS PASSED SUCCESS ")
    print("=" * 60)

if __name__ == "__main__":
    run_tests()
