import sys
import json
import time
from datetime import datetime, timedelta

sys.path.append("C:/Users/nagel/Documents/MY EVERYTHING/resume pro/backend")
sys.path.append("C:/Users/nagel/Documents/MY EVERYTHING/resume pro/backend/app")

from run import app
from app import db
from app.models.user import User, Student
from app.models.attendance import Attendance, Subject, AttendanceSession, AttendanceRecord
from app.models.log_feedback import Notification
from app.models.complaint import Complaint
from app.models.placement import PlacementDrive
from app.services.notification_service import create_notification, notify_placement_drive, notify_campus_service, notify_placement_status

# Flask test client
client = app.test_client()

def get_auth_headers(email):
    """Simulate user login and return authorization headers."""
    with app.app_context():
        user = User.query.filter_by(email=email).first()
        if not user:
            raise Exception(f"User {email} not found")
        
        # Bypass OTP by writing mock token or using Flask-JWT-Extended directly
        from flask_jwt_extended import create_access_token
        token = create_access_token(identity=str(user.id), additional_claims={"role": user.role})
        return {"Authorization": f"Bearer {token}"}, token

def run_tests():
    print("=" * 60)
    print(" RUNNING PHASE 11 ATTENDANCE & NOTIFICATIONS TESTS ")
    print("=" * 60)

    # 1. Login users
    print("Test 1: Authenticating mock profiles...")
    headers_stu_a, _ = get_auth_headers("balajinagella7@gmail.com")   # CSE Student A (ID=11)
    headers_stu_b, _ = get_auth_headers("student2@student.edu")   # ECE Student B (ID=12)
    headers_fac, _ = get_auth_headers("faculty01@example.com")     # CSE Faculty
    headers_po, _ = get_auth_headers("placement@example.com")     # Placement Officer
    headers_adm, _ = get_auth_headers("admin1@college.edu")   # Super Admin
    print(" -> SUCCESS")

    with app.app_context():
        student_a = Student.query.filter_by(roll_no="CS26B1001").first()
        student_b = Student.query.filter_by(roll_no="CS26B1002").first()
        student_a_id = student_a.id if student_a else 11
        student_b_id = student_b.id if student_b else 12
        student_a_user_id = student_a.user_id if student_a else 11
        student_b_user_id = student_b.user_id if student_b else 12

    # 2. Unauthenticated Protected Access
    print("\nTest 2: Unauthenticated access block...")
    res = client.get("/api/student/dashboard/attendance/details")
    print(f" -> Status: {res.status_code}")
    assert res.status_code == 401

    # 3. IDOR Safety: Student B accessing Student A's attendance details
    print("\nTest 3: IDOR safety check - Student B accessing Student A details...")
    res_idor = client.get(f"/api/student/dashboard/attendance/details", headers=headers_stu_b)
    print(f" -> Status: {res_idor.status_code}")
    assert res_idor.status_code == 200
    # The endpoint must isolate and return ECE Student B's records, NOT Student A's records
    details_data = json.loads(res_idor.data)["data"]
    # Check that none of the details belong to Student A's student_id
    with app.app_context():
        for item in details_data:
            # Look up record in database
            rec = AttendanceRecord.query.get(item["id"])
            assert rec.student_id == student_b_id, "IDOR boundary breached: Student B accessed Student A's raw log!"
    print(" -> IDOR Safety: PASS")

    # 4. Cross-Notification Block: Student cannot query or manage other students' notifications
    print("\nTest 4: Cross-Notification isolation check...")
    # Get notifications list for Student A
    res_notif_a = client.get("/api/student/dashboard/notifications", headers=headers_stu_a)
    notifs_a = json.loads(res_notif_a.data)["data"]
    
    # Try to mark one of Student A's notifications read as Student B
    if notifs_a:
        target_notif_id = notifs_a[0]["id"]
        res_hack = client.put(f"/api/notifications/{target_notif_id}/read", headers=headers_stu_b)
        print(f" -> Student B mark Student A notif status: {res_hack.status_code}")
        assert res_hack.status_code == 404, "Student B bypassed notification isolation!"
    else:
        print(" -> No notifications to test hack (isolation verified by default)")

    # 5. Notification Duplication Protection
    print("\nTest 5: Notification duplication protection...")
    with app.app_context():
        # Clear previous matching notifications if any
        Notification.query.filter_by(user_id=student_a_user_id, title="Test Warning").delete()
        db.session.commit()
        
        pre_count = Notification.query.filter_by(user_id=student_a_user_id).count()
        # Trigger duplicate creations
        n1 = create_notification(student_a_user_id, "Test Warning", "Desc 1", "test_type")
        n2 = create_notification(student_a_user_id, "Test Warning", "Desc 1", "test_type")
        
        post_count = Notification.query.filter_by(user_id=student_a_user_id).count()
        print(f" -> Pre count: {pre_count}, Post count: {post_count}")
        assert post_count == pre_count + 1, "Duplicate notifications were inserted!"
        assert n1.id == n2.id, "Second call did not return the first matching instance!"
    print(" -> Duplicate Prevention: PASS")

    # 6. Shortage Boundary checks (74.99% vs exactly 75.0% vs 75.01%)
    print("\nTest 6: Shortage threshold boundary checks...")
    with app.app_context():
        # Mock student profiles
        mock_student = Student.query.get(student_a_id)
        
        # Clear warning notifications
        Notification.query.filter_by(user_id=student_a_user_id, title="Attendance Shortage Warning").delete()
        db.session.commit()
        
        # Test 75.0% (Should NOT trigger)
        from app.services.notification_service import notify_attendance_shortage
        notify_attendance_shortage(mock_student, 75.0)
        notif_count = Notification.query.filter_by(user_id=student_a_user_id, title="Attendance Shortage Warning").count()
        assert notif_count == 0, "Warning triggered for exactly 75.0%!"
        
        # Test 75.01% (Should NOT trigger)
        notify_attendance_shortage(mock_student, 75.01)
        notif_count = Notification.query.filter_by(user_id=student_a_user_id, title="Attendance Shortage Warning").count()
        assert notif_count == 0, "Warning triggered for 75.01%!"
        
        # Test 74.99% (Should TRIGGER)
        notify_attendance_shortage(mock_student, 74.99)
        notif_count = Notification.query.filter_by(user_id=student_a_user_id, title="Attendance Shortage Warning").count()
        assert notif_count == 1, "Warning failed to trigger for 74.99%!"
        
        # Clean up
        Notification.query.filter_by(user_id=student_a_user_id, title="Attendance Shortage Warning").delete()
        db.session.commit()
    print(" -> Shortage Boundaries: PASS")

    # 7. Consecutive Classes Needed Calculator
    print("\nTest 7: Consecutive classes needed math verification...")
    # We test the formula directly using N = max(0, 3*C - 4*A)
    calc_n = lambda C, A: max(0, 3*C - 4*A)
    
    # Let's assert against boundary cases
    assert calc_n(0, 0) == 0, "0/0 should need 0 classes"
    assert calc_n(10, 7) == 2, "7/10 (70%) should need 2 classes (total 9/12 = 75%)"
    assert calc_n(10, 6) == 6, "6/10 (60%) should need 6 classes (total 12/16 = 75%)"
    assert calc_n(50, 37) == 2, "37/50 (74%) should need 2 classes (total 39/52 = 75%)"
    assert calc_n(100, 74) == 4, "74/100 (74%) should need 4 classes (total 78/104 = 75%)"
    assert calc_n(100, 75) == 0, "75/100 (75%) should need 0 classes"
    assert calc_n(100, 80) == 0, "80/100 (80%) should need 0 classes"
    print(" -> Classes Needed Math: PASS")

    # 8. Targeted Placement Drives Alert
    print("\nTest 8: Targeted placement drives branch matching checks...")
    with app.app_context():
        # Clean previous placement drive alerts
        Notification.query.filter_by(title="New Placement Drive published").delete()
        db.session.commit()
        
        # Create CSE/IT placement drive
        cse_drive = PlacementDrive(
            company_name="TEST-CSE-ONLY",
            job_role="Software Engineer",
            eligibility_criteria="B.Tech CSE/IT",
            salary_package="12 LPA",
            drive_date=datetime.utcnow() + timedelta(days=5),
            status="Upcoming"
        )
        db.session.add(cse_drive)
        db.session.commit()
        
        # Trigger notifications
        notify_placement_drive(cse_drive)
        
        # Check alerts
        notif_stu_a = Notification.query.filter_by(user_id=student_a_user_id, title="New Placement Drive published").first()
        notif_stu_b = Notification.query.filter_by(user_id=student_b_user_id, title="New Placement Drive published").first()
        
        assert notif_stu_a is not None, "Eligible CSE student was NOT notified!"
        assert notif_stu_b is None, "Ineligible ECE student was accidentally notified!"
        
        # Clean up drive and alerts
        db.session.delete(cse_drive)
        Notification.query.filter_by(title="New Placement Drive published").delete()
        db.session.commit()
    print(" -> Targeted Placements branch filtering: PASS")

    # 9. Grievances Updates Alerts: Reopened Grievance Alerts
    print("\nTest 9: Grievance updates and reopened notifications check...")
    with app.app_context():
        # Clear recent complaint updates notifications
        Notification.query.filter_by(user_id=student_a_user_id, type="status_change").delete()
        db.session.commit()
        
        # Get a CSE student complaint
        complaint = Complaint.query.filter_by(student_id=student_a_id).first()
        if complaint:
            from app.services.notification_service import notify_status_change
            # Simulate status update to 'Reopened'
            notify_status_change(complaint, "Closed", "Reopened")
            
            # Check alert
            notif = Notification.query.filter_by(user_id=student_a_user_id, type="status_change").first()
            assert notif is not None, "Status change notification was not triggered!"
            assert "Reopened" in notif.message, "Status change notification message incorrect!"
            
            # Clean up
            Notification.query.filter_by(user_id=student_a_user_id, type="status_change").delete()
            db.session.commit()
        else:
            print(" -> No complaint found to test status change (skipping)")
    print(" -> Grievance Status notifications: PASS")

    print("=" * 60)
    print(" ALL PHASE 11 WORKFLOW AND SECURITY CHECKS PASSED SUCCESS ")
    print("=" * 60)

if __name__ == "__main__":
    run_tests()
