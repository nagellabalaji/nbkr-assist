import sys
import json

sys.path.append("C:/Users/nagel/Documents/MY EVERYTHING/resume pro/backend")
sys.path.append("C:/Users/nagel/Documents/MY EVERYTHING/resume pro/backend/app")

from run import app
from app import db
from app.models.user import User, Student, Staff, Admin
from app.models.complaint import ComplaintCategory, Complaint, ComplaintAssignment, ComplaintHistory
from app.models.log_feedback import Feedback, Notification
from app.models.exam import ExamNotification
from app.models.hostel import HostelRequest
from app.models.transport import TransportRoute, TransportRequest
from app.models.library import LibraryBook, LibraryRequest
from app.models.placement import PlacementDrive, PlacementApplication

def run_backup():
    with app.app_context():
        backup_data = {
            "users": [u.to_dict() for u in User.query.all()],
            "students": [s.to_dict() for s in Student.query.all()],
            "staff": [s.to_dict() for s in Staff.query.all()],
            "admins": [a.to_dict() for a in Admin.query.all()],
            "categories": [c.to_dict() for c in ComplaintCategory.query.all()],
            "complaints": [c.to_dict() for c in Complaint.query.all()],
            "assignments": [a.to_dict() for a in ComplaintAssignment.query.all()],
            "history": [h.to_dict() for h in ComplaintHistory.query.all()],
            "feedback": [f.to_dict() for f in Feedback.query.all()],
            "notifications": [n.to_dict() for n in Notification.query.all()],
            "exam_notifications": [e.to_dict() for e in ExamNotification.query.all()],
            "hostel_requests": [h.to_dict() for h in HostelRequest.query.all()],
            "transport_routes": [t.to_dict() for t in TransportRoute.query.all()],
            "transport_requests": [t.to_dict() for t in TransportRequest.query.all()],
            "library_books": [l.to_dict() for l in LibraryBook.query.all()],
            "library_requests": [l.to_dict() for l in LibraryRequest.query.all()],
            "placement_drives": [p.to_dict() for p in PlacementDrive.query.all()],
            "placement_applications": [p.to_dict() for p in PlacementApplication.query.all()]
        }
        
        try:
            from sqlalchemy import text
            res = db.session.execute(text("SHOW TABLES"))
            tables = [r[0] for r in res.fetchall()]
            
            if "attendance" in tables:
                res_att = db.session.execute(text("SELECT * FROM attendance"))
                backup_data["attendance"] = [dict(r._mapping) for r in res_att.fetchall()]
            if "attendance_sessions" in tables:
                res_sess = db.session.execute(text("SELECT * FROM attendance_sessions"))
                backup_data["attendance_sessions"] = [dict(r._mapping) for r in res_sess.fetchall()]
            if "attendance_records" in tables:
                res_recs = db.session.execute(text("SELECT * FROM attendance_records"))
                backup_data["attendance_records"] = [dict(r._mapping) for r in res_recs.fetchall()]
        except Exception as e:
            print("Dynamic table inspect warning:", str(e))
            
        backup_path = r"C:\Users\nagel\.gemini\antigravity\brain\a4f2b897-f349-4362-b286-ba42084aa554\backup\db_backup_phase12_pre.json"
        with open(backup_path, "w") as f:
            json.dump(backup_data, f, indent=2, default=str)
            
        print("Fresh database backup created successfully at:", backup_path)

if __name__ == "__main__":
    run_backup()
