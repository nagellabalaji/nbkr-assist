import sys
import json
import hashlib
import time
from datetime import datetime, timedelta

sys.path.append("C:/Users/nagel/Documents/MY EVERYTHING/resume pro/backend")
sys.path.append("C:/Users/nagel/Documents/MY EVERYTHING/resume pro/backend/app")

from run import app
from app import db
from app.models.user import User, Student, Staff
from app.models.complaint import ComplaintCategory, Complaint, ComplaintAssignment, ComplaintHistory
from app.models.log_feedback import Feedback, Notification

# Flask test client
client = app.test_client()

def get_auth_headers(email):
    """Simulate user login and return authorization headers."""
    # We bypass OTP validation in tests by setting it verified in DB or using direct token generation
    from flask_jwt_extended import create_access_token
    with app.app_context():
        user = User.query.filter_by(email=email).first()
        if not user:
            raise Exception(f"User {email} not found")
        # Generate token with proper role and identity claims
        token = create_access_token(identity=str(user.id), additional_claims={"role": user.role})
        return {"Authorization": f"Bearer {token}"}

def run_tests():
    print("=" * 60)
    print(" RUNNING PHASE 5 GRIEVANCE DESK TESTS ")
    print("=" * 60)

    # 1. Login student01
    headers_student_a = get_auth_headers("student01@example.com")
    print("Student A Login: SUCCESS")

    # 2. Login student02
    headers_student_b = get_auth_headers("student02@example.com")
    print("Student B Login: SUCCESS")
    
    # 3. Login super admin
    headers_admin = get_auth_headers("admin@example.com")
    print("Super Admin Login: SUCCESS")

    with app.app_context():
        # Get category CSE/Academic/Maintenance IDs
        maintenance_cat = ComplaintCategory.query.filter_by(name="Maintenance").first()
        academic_cat = ComplaintCategory.query.filter_by(name="Academic").first()
        
        maintenance_cat_id = maintenance_cat.id if maintenance_cat else 1
        academic_cat_id = academic_cat.id if academic_cat else 2

    # 4. Test Grievance Creation with AI Classification fallback
    print("\nTest 1: Creating a new grievance...")
    unique_title = f"Peeling plaster in classroom - {time.time()}"
    unique_desc = f"Plaster from the ceiling is peeling off and falling onto the students desks in room 305. {time.time()}"
    res = client.post("/api/grievances", headers=headers_student_a, data={
        "title": unique_title,
        "description": unique_desc,
        "category_id": str(maintenance_cat_id),
        "subcategory": "Ceiling Repair",
        "location": "Academic Block A, Room 305",
        "priority": "Medium"
    })
    print(f" -> Status: {res.status_code}")
    print(res.data.decode())
    res_data = json.loads(res.data)
    assert res.status_code == 201, f"Grievance creation failed: {res.data.decode()}"
    ticket_id = res_data["data"]["id"]
    print(f" -> New Ticket ID: {ticket_id}")
    assert ticket_id.startswith("NBKR-"), "Ticket ID must start with NBKR-"
    assert res_data["data"]["subcategory"] == "Ceiling Repair", "Subcategory not set correctly"
    assert res_data["data"]["sla_deadline"] is not None, "SLA deadline not set"
    assert res_data["data"]["sla_status"] == "Normal", "SLA status should be Normal initially"

    # 5. Test Duplicate Detection
    print("\nTest 2: Submitting duplicate grievance...")
    res_dup = client.post("/api/grievances", headers=headers_student_a, data={
        "title": unique_title,
        "description": unique_desc,
        "category_id": str(maintenance_cat_id),
        "subcategory": "AC/Fan",
        "location": "Hostel Block B, Room 203"
    })
    print(f" -> Status: {res_dup.status_code}")
    assert res_dup.status_code == 409, "Duplicate check failed to reject matching grievance"
    dup_data = json.loads(res_dup.data)
    print(f" -> Duplicate check message: {dup_data['message']}")
    assert dup_data["error"] == "duplicate_detected"
    assert dup_data["duplicate"]["id"] == ticket_id

    # 6. Test Force Submission
    print("\nTest 3: Force submitting duplicate...")
    res_force = client.post(f"/api/grievances?force=true", headers=headers_student_a, data={
        "title": unique_title,
        "description": unique_desc,
        "category_id": str(maintenance_cat_id),
        "subcategory": "AC/Fan",
        "location": "Hostel Block B, Room 203"
    })
    print(f" -> Status: {res_force.status_code}")
    assert res_force.status_code == 201, "Force submit failed"
    force_ticket_id = json.loads(res_force.data)["data"]["id"]
    print(f" -> Forced Ticket ID: {force_ticket_id}")

    # 7. Test IDOR Protection: Student B requesting Student A's ticket details
    print("\nTest 4: IDOR check - Student B accessing Student A's ticket...")
    res_idor = client.get(f"/api/grievances/{ticket_id}", headers=headers_student_b)
    print(f" -> Status: {res_idor.status_code}")
    assert res_idor.status_code == 403, "IDOR check failed to prevent unauthorized access"

    # 8. Test Legacy Ticket ID Reading Support (using an existing ticket from database)
    print("\nTest 5: Accessing legacy ticket ID...")
    with app.app_context():
        legacy_ticket = Complaint.query.filter(Complaint.id.like("CMP-%")).first()
        legacy_id = legacy_ticket.id if legacy_ticket else None
    
    if legacy_id:
        res_legacy = client.get(f"/api/grievances/{legacy_id}", headers=headers_admin)
        print(f" -> Legacy Ticket {legacy_id} Status: {res_legacy.status_code}")
        assert res_legacy.status_code == 200, "Failed to retrieve legacy CMP ticket ID"
    else:
        print(" -> No legacy ticket found to test.")

    # 9. Test Unauthorized Assignment: Student A trying to assign ticket
    print("\nTest 6: Student trying to assign ticket...")
    res_assign_stu = client.post(f"/api/grievances/{ticket_id}/assign", headers=headers_student_a, json={
        "staff_id": 1
    })
    print(f" -> Status: {res_assign_stu.status_code}")
    assert res_assign_stu.status_code == 403, "Student assignment block failed"

    # 10. Test Authorized Assignment by Admin
    print("\nTest 7: Admin assigning ticket to staff...")
    with app.app_context():
        from app.models.user import User
        # Get first faculty member
        staff_rec = Staff.query.join(User).filter(User.role == 'faculty').first()
        staff_id = staff_rec.id if staff_rec else 1
        staff_username = staff_rec.user.username if staff_rec else "staff"
        branch_name = staff_rec.department if staff_rec else "Computer Science and Engineering"
    
    res_assign_admin = client.post(f"/api/grievances/{ticket_id}/assign", headers=headers_admin, json={
        "staff_id": staff_id,
        "faculty_id": staff_id,
        "branch": branch_name
    })
    print(f" -> Status: {res_assign_admin.status_code}")
    assert res_assign_admin.status_code == 200, "Admin assignment failed"
    assign_data = json.loads(res_assign_admin.data)
    assert assign_data["data"]["status"] == "Assigned", "Status did not update to Assigned"
    assert assign_data["data"]["assigned_staff_id"] == staff_id

    # 11. Test SLA Expiry Breach Check (mock deadline to past)
    print("\nTest 8: SLA Breach computation check...")
    with app.app_context():
        comp_rec = Complaint.query.get(ticket_id)
        # Mock deadline to 5 hours in the past
        comp_rec.sla_deadline = datetime.utcnow() - timedelta(hours=5)
        db.session.commit()
    
    res_breach = client.get(f"/api/grievances/{ticket_id}", headers=headers_student_a)
    breach_data = json.loads(res_breach.data)
    print(f" -> SLA Status (after mocking past deadline): {breach_data['data']['sla_status']}")
    assert breach_data["data"]["sla_status"] == "Breached", "SLA breach check failed to reflect Breached state"

    # 12. Test Feedback and Auto-Closure
    print("\nTest 9: Submitting feedback and checking auto-closure...")
    # First, staff resolves ticket
    headers_staff = get_auth_headers("maintenance@example.com") # verify staff exists in config
    client.put(f"/api/grievances/{ticket_id}/status", headers=headers_admin, json={
        "status": "Resolved",
        "comments": "Resolved by fixing ceiling fan connection."
    })
    
    res_feedback = client.post(f"/api/grievances/{ticket_id}/feedback", headers=headers_student_a, json={
        "rating": 5,
        "comments": "Excellent service!"
    })
    print(f" -> Feedback status: {res_feedback.status_code}")
    assert res_feedback.status_code == 201, "Feedback submission failed"
    
    # Check ticket is closed
    res_closed = client.get(f"/api/grievances/{ticket_id}", headers=headers_student_a)
    closed_data = json.loads(res_closed.data)
    print(f" -> Ticket Status after feedback: {closed_data['data']['status']}")
    assert closed_data["data"]["status"] == "Closed", "Ticket did not auto-close after feedback"

    # 13. Test Unauthenticated access
    print("\nTest 10: Unauthenticated access block...")
    res_unauth = client.get(f"/api/grievances/{ticket_id}")
    print(f" -> Status: {res_unauth.status_code}")
    assert res_unauth.status_code == 401, "Unauthenticated access check failed"

    print("\n" + "=" * 60)
    print(" ALL GRIEVANCE DESK TESTS COMPLETED SUCCESS ")
    print("=" * 60)

if __name__ == "__main__":
    run_tests()
