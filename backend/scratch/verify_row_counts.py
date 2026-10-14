import sys
sys.path.append("C:/Users/nagel/Documents/MY EVERYTHING/resume pro/backend")
sys.path.append("C:/Users/nagel/Documents/MY EVERYTHING/resume pro/backend/app")

from run import app
from app import db
from app.models.user import User, Student, Staff, Admin
from app.models.complaint import ComplaintCategory, Complaint, ComplaintAssignment, ComplaintHistory
from app.models.log_feedback import Feedback, Notification

def get_row_counts():
    with app.app_context():
        print("=" * 40)
        print(" DATABASE TABLE ROW COUNTS ")
        print("=" * 40)
        tables = [
            ("users", User),
            ("students", Student),
            ("staff", Staff),
            ("admins", Admin),
            ("complaint_categories", ComplaintCategory),
            ("complaints (grievances)", Complaint),
            ("complaint_assignments", ComplaintAssignment),
            ("complaint_history", ComplaintHistory),
            ("feedback", Feedback),
            ("notifications", Notification)
        ]
        for name, model in tables:
            try:
                count = model.query.count()
                print(f" -> {name:25}: {count} rows")
            except Exception as e:
                print(f" -> {name:25}: ERROR ({str(e)})")
        print("=" * 40)

if __name__ == "__main__":
    get_row_counts()
