import sys

sys.path.append("C:/Users/nagel/Documents/MY EVERYTHING/resume pro/backend")
sys.path.append("C:/Users/nagel/Documents/MY EVERYTHING/resume pro/backend/app")

from run import app
from app import db
from app.models.user import User, Staff
from app.models.department import Department

faculty_seeding = [
    {"name": "Balaji", "branch": "ECE", "email": "balaji@college.edu", "phone": "9876543001"},
    {"name": "Sainadh", "branch": "CSE", "email": "sainadh@college.edu", "phone": "9876543002"},
    {"name": "Gopi", "branch": "IT", "email": "gopi@college.edu", "phone": "9876543003"},
    {"name": "Nani", "branch": "ECE", "email": "nani@college.edu", "phone": "9876543004"},
    {"name": "Sai", "branch": "CSE", "email": "sai@college.edu", "phone": "9876543005"},
    {"name": "Pravven", "branch": "IT", "email": "pravven@college.edu", "phone": "9876543006"},
    {"name": "Mohini", "branch": "ECE", "email": "mohini@college.edu", "phone": "9876543007"},
    {"name": "Rahul", "branch": "CSE", "email": "rahul@college.edu", "phone": "9876543008"}
]

def seed_faculty():
    with app.app_context():
        # Get department mappings
        depts = {d.code: d for d in Department.query.all()}
        
        for idx, item in enumerate(faculty_seeding, start=1):
            name = item["name"]
            branch_code = item["branch"]
            email = item["email"]
            phone = item["phone"]
            
            # Check if user already exists
            existing_user = User.query.filter_by(username=name).first()
            if existing_user:
                print(f"User {name} already exists. Skipping creation.")
                # Verify or update staff department id if not set
                if existing_user.staff_profile:
                    dept = depts.get(branch_code)
                    if dept and existing_user.staff_profile.department_id != dept.id:
                        existing_user.staff_profile.department_id = dept.id
                        existing_user.staff_profile.department = dept.name
                        db.session.commit()
                continue
                
            # Find department
            dept = depts.get(branch_code)
            if not dept:
                print(f"Department code {branch_code} not found. Skipping {name}.")
                continue
                
            # Create user
            user = User(
                username=name,
                email=email,
                role='faculty',
                status='active',
                email_verified=True
            )
            user.set_password('password123')
            db.session.add(user)
            db.session.flush() # Populate user.id
            
            # Create staff profile
            staff = Staff(
                user_id=user.id,
                department=dept.name,
                specialization=f"{branch_code} Specialist",
                is_available=True,
                department_id=dept.id,
                employee_id=f"EMP-{name.upper()}-{100+idx}",
                designation='Assistant Professor',
                phone=phone
            )
            db.session.add(staff)
            db.session.commit()
            print(f"Seeded faculty: {name} ({branch_code}) successfully.")

if __name__ == "__main__":
    seed_faculty()
