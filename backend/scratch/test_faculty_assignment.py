import sys
import json
from datetime import datetime, timedelta
import unittest

sys.path.append("C:/Users/nagel/Documents/MY EVERYTHING/resume pro/backend")
sys.path.append("C:/Users/nagel/Documents/MY EVERYTHING/resume pro/backend/app")

from run import app
from app import db
from app.models.user import User, Staff
from app.models.complaint import Complaint, ComplaintAssignment, ComplaintHistory, ComplaintCategory
from app.models.log_feedback import Notification
from app.services.email_service import EmailService
from app.utils.sla import calculate_resolution_deadline
from app.services.reminder_service import ReminderService

# Mock Email Helper
mock_email_calls = []

def mock_send_assignment_email(to_email, faculty_name, complaint_id, category_name, priority, branch=None, assigned_date=None, resolution_deadline=None):
    mock_email_calls.append({
        'to_email': to_email,
        'faculty_name': faculty_name,
        'complaint_id': complaint_id,
        'category_name': category_name,
        'priority': priority,
        'branch': branch,
        'assigned_date': assigned_date,
        'resolution_deadline': resolution_deadline
    })
    return True

def mock_send_assignment_email_fail(to_email, faculty_name, complaint_id, category_name, priority, branch=None, assigned_date=None, resolution_deadline=None):
    raise Exception("SMTP Connection Failed Mocked Error")

class TestFacultyAssignment(unittest.TestCase):
    def setUp(self):
        self.app = app.test_client()
        self.ctx = app.app_context()
        self.ctx.push()

        # Seed test category
        self.category = ComplaintCategory.query.filter_by(name="Test Category").first()
        if not self.category:
            self.category = ComplaintCategory(name="Test Category", suggested_department="Academic")
            db.session.add(self.category)
            db.session.commit()

        # Clear mock email log
        global mock_email_calls
        mock_email_calls = []
        # Backup original send_assignment_email
        self.orig_send_email = EmailService.send_assignment_email
        EmailService.send_assignment_email = mock_send_assignment_email

    def tearDown(self):
        EmailService.send_assignment_email = self.orig_send_email
        self.ctx.pop()

    def get_auth_token(self, email, password="password123"):
        res = self.app.post('/api/auth/login', json={
            'identity': email,
            'password': password
        })
        data = json.loads(res.data)
        return data['data']['token']

    def test_01_load_faculty_list_success(self):
        """1 & 2. Get faculty list loads successfully for Admin"""
        token = self.get_auth_token("admin1@college.edu")
        res = self.app.get('/api/admin/faculty', headers={
            'Authorization': f'Bearer {token}'
        })
        self.assertEqual(res.status_code, 200)
        data = json.loads(res.data)
        self.assertTrue(data['success'])
        self.assertTrue(len(data['data']) > 0)
        
        # Verify only users with Faculty/HOD role are returned
        for faculty in data['data']:
            user = User.query.get(faculty['user_id'])
            self.assertIn(user.role, ['faculty', 'hod'])

    def test_02_load_faculty_list_forbidden_for_student(self):
        """11. Student attempting to query faculty list returns 403"""
        token = self.get_auth_token("balajinagella7@gmail.com")
        res = self.app.get('/api/admin/faculty', headers={
            'Authorization': f'Bearer {token}'
        })
        self.assertEqual(res.status_code, 403)

    def test_03_missing_faculty_validation(self):
        """6. Missing faculty validation checks"""
        token = self.get_auth_token("admin1@college.edu")
        
        student = User.query.filter_by(role="student").first()
        comp = Complaint(
            id="CMP-TEST-ASSIGN-01",
            student_id=student.student_profile.id,
            title="Test Title",
            description="Test Description",
            category_id=self.category.id,
            location="Room 101",
            suggested_department="Academic"
        )
        db.session.merge(comp)
        db.session.commit()

        res = self.app.post('/api/complaints/CMP-TEST-ASSIGN-01/assign', json={
            'branch': 'CSE'
        }, headers={'Authorization': f'Bearer {token}'})
        self.assertEqual(res.status_code, 400)
        data = json.loads(res.data)
        self.assertFalse(data['success'])
        self.assertEqual(data['message'], "Please select a faculty member.")

    def test_04_missing_branch_validation(self):
        """7. Missing branch validation checks"""
        token = self.get_auth_token("admin1@college.edu")
        faculty = User.query.filter_by(role="faculty").first()

        res = self.app.post('/api/complaints/CMP-TEST-ASSIGN-01/assign', json={
            'faculty_id': faculty.staff_profile.id
        }, headers={'Authorization': f'Bearer {token}'})
        self.assertEqual(res.status_code, 400)
        data = json.loads(res.data)
        self.assertFalse(data['success'])
        self.assertEqual(data['message'], "Please select a branch.")

    def test_05_faculty_branch_mismatch_rejection(self):
        """8. Faculty/branch mismatch results in rejection"""
        token = self.get_auth_token("admin1@college.edu")
        
        cse_fac = Staff.query.filter(Staff.department.like("%Computer Science%")).first()
        self.assertIsNotNone(cse_fac, "Requires at least one CSE faculty seeded")

        res = self.app.post('/api/complaints/CMP-TEST-ASSIGN-01/assign', json={
            'faculty_id': cse_fac.id,
            'branch': 'ECE'
        }, headers={'Authorization': f'Bearer {token}'})
        self.assertEqual(res.status_code, 400)
        data = json.loads(res.data)
        self.assertFalse(data['success'])
        self.assertEqual(data['message'], "Selected faculty does not belong to this branch.")

    def test_06_non_existent_grievance(self):
        """13. Assigning a non-existent grievance returns 404"""
        token = self.get_auth_token("admin1@college.edu")
        cse_fac = Staff.query.filter(Staff.department.like("%Computer Science%")).first()

        res = self.app.post('/api/complaints/CMP-NON-EXISTENT/assign', json={
            'faculty_id': cse_fac.id,
            'branch': 'CSE'
        }, headers={'Authorization': f'Bearer {token}'})
        self.assertEqual(res.status_code, 404)

    def test_07_invalid_faculty_id(self):
        """10. Assigning to invalid/non-existent faculty ID returns 404"""
        token = self.get_auth_token("admin1@college.edu")

        res = self.app.post('/api/complaints/CMP-TEST-ASSIGN-01/assign', json={
            'faculty_id': 999999,
            'branch': 'CSE'
        }, headers={'Authorization': f'Bearer {token}'})
        self.assertEqual(res.status_code, 404)

    def test_08_student_assignment_forbidden(self):
        """11 & 12. Student role or unauthorized users blocked (returns 403)"""
        token = self.get_auth_token("balajinagella7@gmail.com")
        cse_fac = Staff.query.filter(Staff.department.like("%Computer Science%")).first()

        res = self.app.post('/api/complaints/CMP-TEST-ASSIGN-01/assign', json={
            'faculty_id': cse_fac.id,
            'branch': 'CSE'
        }, headers={'Authorization': f'Bearer {token}'})
        self.assertEqual(res.status_code, 403)

    def test_09_successful_assignment(self):
        """9, 15, 16, 17. Valid assignment updates DB, returns success, sends email"""
        token = self.get_auth_token("admin1@college.edu")
        cse_fac = Staff.query.filter(Staff.department.like("%Computer Science%")).first()
        
        res = self.app.post('/api/complaints/CMP-TEST-ASSIGN-01/assign', json={
            'faculty_id': cse_fac.id,
            'branch': 'CSE'
        }, headers={'Authorization': f'Bearer {token}'})
        
        self.assertEqual(res.status_code, 200)
        data = json.loads(res.data)
        self.assertTrue(data['success'])
        
        # 15. Verify database persistence
        comp = Complaint.query.get("CMP-TEST-ASSIGN-01")
        self.assertEqual(comp.assigned_staff_id, cse_fac.id)
        self.assertEqual(comp.status, "Assigned")

        # 16. Verify assignment details appear in complaint.to_dict() representation
        comp_dict = comp.to_dict()
        self.assertEqual(comp_dict['assigned_faculty_id'], cse_fac.id)
        self.assertEqual(comp_dict['assigned_faculty_name'], cse_fac.user.username)
        self.assertEqual(comp_dict['assigned_branch'], "CSE")
        self.assertEqual(comp_dict['assigned_faculty_phone'], cse_fac.phone or "Not available")
        self.assertIsNotNone(comp_dict['assigned_at'])
        self.assertIsNotNone(comp_dict['resolution_deadline'])
        self.assertEqual(comp_dict['assignment_status'], "ASSIGNED")

        # 17. Verify email was sent with new fields
        self.assertEqual(len(mock_email_calls), 1)
        self.assertEqual(mock_email_calls[0]['to_email'], cse_fac.user.email)
        self.assertEqual(mock_email_calls[0]['faculty_name'], cse_fac.user.username)
        self.assertEqual(mock_email_calls[0]['branch'], 'CSE')
        self.assertIsNotNone(mock_email_calls[0]['assigned_date'])
        self.assertIsNotNone(mock_email_calls[0]['resolution_deadline'])

    def test_10_email_failure_does_not_undo_assignment(self):
        """18. Email delivery failure records failure but does not rollback assignment"""
        EmailService.send_assignment_email = mock_send_assignment_email_fail

        token = self.get_auth_token("admin1@college.edu")
        cse_fac = Staff.query.filter(Staff.department.like("%Computer Science%")).first()
        
        comp = Complaint.query.get("CMP-TEST-ASSIGN-01")
        comp.assigned_staff_id = None
        comp.status = "Submitted"
        db.session.commit()

        res = self.app.post('/api/complaints/CMP-TEST-ASSIGN-01/assign', json={
            'faculty_id': cse_fac.id,
            'branch': 'CSE'
        }, headers={'Authorization': f'Bearer {token}'})
        
        self.assertEqual(res.status_code, 200)
        data = json.loads(res.data)
        self.assertTrue(data['success'])

        comp_check = Complaint.query.get("CMP-TEST-ASSIGN-01")
        self.assertEqual(comp_check.assigned_staff_id, cse_fac.id)
        self.assertEqual(comp_check.status, "Assigned")

    def test_11_sla_working_days_calculation(self):
        """4 & 5. Verify SLA deadline calculation excludes weekends"""
        # Friday assignment -> Tuesday deadline
        friday = datetime(2026, 8, 14, 16, 40) # Friday
        dl_friday = calculate_resolution_deadline(friday, 2)
        self.assertEqual(dl_friday.weekday(), 1) # Tuesday is 1
        self.assertEqual(dl_friday.day, 18)

        # Saturday assignment -> Tuesday deadline
        saturday = datetime(2026, 8, 15, 16, 40) # Saturday
        dl_saturday = calculate_resolution_deadline(saturday, 2)
        self.assertEqual(dl_saturday.weekday(), 1) # Tuesday is 1
        self.assertEqual(dl_saturday.day, 18)

        # Sunday assignment -> Tuesday deadline
        sunday = datetime(2026, 8, 16, 16, 40) # Sunday
        dl_sunday = calculate_resolution_deadline(sunday, 2)
        self.assertEqual(dl_sunday.weekday(), 1) # Tuesday is 1
        self.assertEqual(dl_sunday.day, 18)

        # Monday assignment -> Wednesday deadline
        monday = datetime(2026, 8, 17, 16, 40) # Monday
        dl_monday = calculate_resolution_deadline(monday, 2)
        self.assertEqual(dl_monday.weekday(), 2) # Wednesday is 2
        self.assertEqual(dl_monday.day, 19)

        # Tuesday assignment -> Thursday deadline
        tuesday = datetime(2026, 8, 18, 16, 40) # Tuesday
        dl_tuesday = calculate_resolution_deadline(tuesday, 2)
        self.assertEqual(dl_tuesday.weekday(), 3) # Thursday is 3
        self.assertEqual(dl_tuesday.day, 20)

    def test_12_overdue_detection(self):
        """12. Verify assignment_status detects OVERDUE when current_time > deadline"""
        student = User.query.filter_by(role="student").first()
        cse_fac = Staff.query.filter(Staff.department.like("%Computer Science%")).first()

        comp = Complaint(
            id="CMP-TEST-OVERDUE-01",
            student_id=student.student_profile.id,
            title="Overdue Test Title",
            description="Overdue Test Description",
            category_id=self.category.id,
            location="Room 101",
            suggested_department="Academic",
            assigned_staff_id=cse_fac.id,
            status='Assigned',
            sla_deadline=datetime.utcnow() - timedelta(hours=1) # Exceeded
        )
        comp = db.session.merge(comp)
        db.session.commit()

        comp_dict = comp.to_dict()
        self.assertEqual(comp_dict['assignment_status'], 'OVERDUE')

        # Clean up
        db.session.delete(comp)
        db.session.commit()

    def test_13_reminder_service(self):
        """14. Verify reminder service generates notifications and prevents duplicates"""
        student = User.query.filter_by(role="student").first()
        cse_fac = Staff.query.filter(Staff.department.like("%Computer Science%")).first()

        # Create active complaint due in 10 hours (Warning range)
        comp = Complaint(
            id="CMP-TEST-WARN-01",
            student_id=student.student_profile.id,
            title="Warning Test Title",
            description="Warning Test Description",
            category_id=self.category.id,
            location="Room 101",
            suggested_department="Academic",
            assigned_staff_id=cse_fac.id,
            status='Assigned',
            sla_deadline=datetime.utcnow() + timedelta(hours=10) # 10 hours from now
        )
        comp = db.session.merge(comp)
        db.session.commit()

        # Clean up existing test notifications
        Notification.query.filter_by(complaint_id="CMP-TEST-WARN-01").delete()
        db.session.commit()

        # Trigger Reminders
        res = ReminderService.check_and_send_reminders()
        self.assertTrue(res['reminders_sent'] >= 1)

        # Trigger Reminders again - should be 0 because it's already in Notification history
        res_dup = ReminderService.check_and_send_reminders()
        self.assertEqual(res_dup['reminders_sent'], 0)

        # Clean up
        Notification.query.filter_by(complaint_id="CMP-TEST-WARN-01").delete()
        db.session.delete(comp)
        db.session.commit()

        # Clean up CMP-TEST-ASSIGN-01
        comp_assign = Complaint.query.get("CMP-TEST-ASSIGN-01")
        if comp_assign:
            db.session.delete(comp_assign)
            db.session.commit()

if __name__ == "__main__":
    unittest.main()
