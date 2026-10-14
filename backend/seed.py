import os
import random
from datetime import datetime, timedelta
from app import create_app, db
from app.models.user import User, Student, Staff, Admin
from app.models.complaint import ComplaintCategory, Complaint, ComplaintAssignment, ComplaintHistory
from app.models.log_feedback import Notification, Feedback, ChatbotMessage

app = create_app()

def seed_database():
    with app.app_context():
        # Ensure database exists before connecting to it
        db_url = app.config['SQLALCHEMY_DATABASE_URI']
        import re
        import pymysql
        match = re.match(r'mysql\+pymysql://([^:]*):([^@]*)@([^/:]*)(?::(\d+))?/([^?]*)', db_url)
        if match:
            user, password, host, port, db_name = match.groups()
            port = int(port) if port else 3306
            try:
                print(f"Connecting to MySQL server at {host}:{port} to check for database '{db_name}'...")
                conn = pymysql.connect(host=host, user=user, password=password, port=port)
                cursor = conn.cursor()
                cursor.execute(f"CREATE DATABASE IF NOT EXISTS {db_name} CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci")
                conn.commit()
                conn.close()
                print(f"Database '{db_name}' verified/created.")
            except Exception as e:
                print(f"Warning: Could not auto-create database '{db_name}'. Continuing with standard connection: {str(e)}")

        print("Recreating database tables...")
        # Create database and tables if not exist
        db.create_all()

        # 1. Seed Complaint Categories if empty
        if ComplaintCategory.query.count() == 0:
            print("Seeding Complaint Categories...")
            categories = [
                ComplaintCategory(name='Electrical', description='Issues related to fans, lights, switches, sockets, short circuits, or other electrical appliances.', suggested_department='Electrical Maintenance'),
                ComplaintCategory(name='Plumbing', description='Issues with water taps, leakage, clogged drains, pipes, toilets, or water tanks.', suggested_department='Plumbing Maintenance'),
                ComplaintCategory(name='Classroom', description='Issues inside classrooms such as broken projector, blackboards, screens, podiums, or ACs.', suggested_department='Academic Facilities'),
                ComplaintCategory(name='Hostel', description='Hostel-specific issues like hot water, warden services, room keys, or common area maintenance.', suggested_department='Hostel Administration'),
                ComplaintCategory(name='Internet/Wi-Fi', description='Issues with college Wi-Fi connectivity, LAN ports, login portal, or internet speed.', suggested_department='IT & Network Support'),
                ComplaintCategory(name='Cleaning', description='Request for cleaning or sweeping classrooms, hostels, washrooms, corridors, or trash removal.', suggested_department='Housekeeping Services'),
                ComplaintCategory(name='Furniture', description='Issues with desk repairs, broken chairs, tables, cabinets, cupboards, or doors.', suggested_department='Carpentry & Furniture Department'),
                ComplaintCategory(name='Laboratory', description='Issues inside labs such as non-functional equipment, software errors, or lab bench repairs.', suggested_department='Lab Management Support'),
                ComplaintCategory(name='Transport', description='Issues related to college bus service, scheduling, pass systems, or parking facilities.', suggested_department='Transport Department'),
                ComplaintCategory(name='Other', description='Any general college-related complaint that does not fit into other standard categories.', suggested_department='General Administration')
            ]
            db.session.add_all(categories)
            db.session.commit()
        
        # Load categories into dict for quick reference
        cats = {c.name: c for c in ComplaintCategory.query.all()}

        # 2. Seed Users
        if User.query.count() > 0:
            print("Database already seeded with users. Skipping user seeding...")
            return

        print("Seeding Users (Admins, Staff, Students)...")

        # 2a. Admins (2)
        admin_users = []
        for i in range(1, 3):
            u = User(username=f"admin{i}", email=f"admin{i}@college.edu", role='admin')
            u.set_password("admin123")
            db.session.add(u)
            admin_users.append(u)
        db.session.flush()

        admins = []
        for i, u in enumerate(admin_users):
            a = Admin(user_id=u.id, department="Facilities & Estates Management")
            db.session.add(a)
            admins.append(a)

        # 2b. Staff (5)
        staff_specs = [
            ("Electrical", "Electrical Maintenance"),
            ("Plumbing", "Plumbing Maintenance"),
            ("IT/Internet", "IT & Network Support"),
            ("Cleaning", "Housekeeping Services"),
            ("Furniture", "Carpentry & Furniture Department")
        ]
        staff_users = []
        for i, (spec, dept) in enumerate(staff_specs, 1):
            u = User(username=f"staff{i}", email=f"staff{i}@maintenance.edu", role='staff')
            u.set_password("staff123")
            db.session.add(u)
            staff_users.append((u, spec, dept))
        db.session.flush()

        staff_members = []
        for u, spec, dept in staff_users:
            s = Staff(user_id=u.id, department=dept, specialization=spec, is_available=True)
            db.session.add(s)
            staff_members.append(s)

        # 2c. Students (10)
        depts = ["Computer Science", "Information Technology", "Electronics", "Mechanical", "Civil"]
        hostels = ["Block A", "Block B", "Block C", "Block D", "Girls Hostel"]
        student_users = []
        for i in range(1, 11):
            u = User(username=f"student{i}", email=f"student{i}@student.edu", role='student')
            u.set_password("student123")
            db.session.add(u)
            student_users.append(u)
        db.session.flush()

        students = []
        for i, u in enumerate(student_users, 1):
            std = Student(
                user_id=u.id,
                roll_no=f"CS26B10{i:02d}",
                department=random.choice(depts),
                hostel_no=random.choice(hostels),
                room_no=f"{random.randint(100, 310)}",
                contact_no=f"98765432{i:02d}"
            )
            db.session.add(std)
            students.append(std)

        db.session.flush()

        # 3. Seed 30 Complaints
        print("Seeding 30 Complaints...")
        complaint_templates = [
            # Electrical
            ("Classroom 102 fan regulator is broken and rotating at max speed.", "Electrical", "Classroom 102", "High"),
            ("Tubelight in hostel Room 204 is flickering constantly.", "Electrical", "Hostel Block A Room 204", "Medium"),
            ("Water dispenser socket sparking when plugged in. Dangerous!", "Electrical", "Block 2 Canteen Lobby", "Urgent"),
            ("Washing machine in laundry room has no power supply.", "Electrical", "Hostel Block B Laundry", "Medium"),
            
            # Plumbing
            ("Washbasin water tap leaking heavily, wasting water.", "Plumbing", "Main Library Washroom", "High"),
            ("Toilet flush tank is clogged and not draining.", "Plumbing", "Block 1 Ground Floor Restroom", "High"),
            ("Water logging in the bathroom due to blocked drain.", "Plumbing", "Hostel Block C Room 108", "High"),
            ("Overhead water tank overflowing on the corridor.", "Plumbing", "Hostel Block A Terrace", "Urgent"),
            
            # Classroom
            ("Projector remote is missing in Room 304.", "Classroom", "Block 3 Room 304", "Medium"),
            ("AC filter clogged, classroom 402 is very hot.", "Classroom", "Block 4 Room 402", "High"),
            ("Whiteboard frame is loose and about to fall.", "Classroom", "Block 2 Room 201", "Low"),
            
            # Hostel
            ("Room door lock key is getting stuck, needs lubrication.", "Hostel", "Hostel Block B Room 302", "Low"),
            ("No hot water from geyser in the morning shower.", "Hostel", "Hostel Block C Common Bathroom", "High"),
            ("Wardrobe wooden door hinges are broken.", "Hostel", "Hostel Block A Room 112", "Medium"),
            
            # Internet/Wi-Fi
            ("Wi-Fi network signal is extremely low in room 210.", "Internet/Wi-Fi", "Hostel Block B Room 210", "Medium"),
            ("LAN port in computer lab 2 has broken clip.", "Internet/Wi-Fi", "Computer Lab 2, Block 3", "Low"),
            ("Cannot authenticate on college portal page (Timeout error).", "Internet/Wi-Fi", "Campus-wide", "High"),
            
            # Cleaning
            ("Washroom is smelling bad, cleaning not done today.", "Cleaning", "Block 2, Second Floor Washroom", "Medium"),
            ("Dustbin overflowing in library corridor.", "Cleaning", "Library Block", "Low"),
            ("Spiderwebs and dust on windows of classroom 205.", "Cleaning", "Block 2 Room 205", "Low"),
            
            # Furniture
            ("Lecture hall seat cushion is torn and wooden board exposed.", "Furniture", "Seminar Hall 1", "Low"),
            ("Study table leg is broken and wobbling.", "Furniture", "Hostel Block C Room 215", "Medium"),
            ("Library bookshelf drawer is jammed.", "Furniture", "Central Library Ground Floor", "Low"),
            
            # Laboratory
            ("Microscope fine adjustment knob is missing.", "Laboratory", "Biology Lab, Block 1", "Medium"),
            ("Software license expired for MATLAB on workstation 14.", "Laboratory", "DSP Lab, Block 3", "High"),
            ("Bunsen burner gas nozzle is leaking slightly (smell of gas).", "Laboratory", "Chemistry Lab, Block 1", "Urgent"),
            
            # Transport
            ("College bus route 7 arriving 30 minutes late consistently.", "Transport", "Route 7 Bus Stop", "Medium"),
            ("Bus number 4 air vent is broken and blowing hot air.", "Transport", "Bus #4", "Low"),
            
            # Other
            ("Canteen Billing machine is out of paper, long queues.", "Other", "Canteen Counter", "Low"),
            ("Library card barcode is not scanning at gate.", "Other", "Library Entrance", "Low")
        ]

        statuses = ['Submitted', 'Under Review', 'Assigned', 'In Progress', 'Resolved', 'Closed', 'Reopened', 'Rejected']

        # Generate 30 tickets
        now = datetime.utcnow()
        for idx, (desc, cat_name, loc, priority) in enumerate(complaint_templates, 1):
            student = random.choice(students)
            category = cats[cat_name]
            
            # Stagger creation dates over last 15 days
            created_date = now - timedelta(days=random.randint(1, 14), hours=random.randint(1, 23))
            
            # Generate ticket ID
            comp_id = f"CMP-{created_date.year}-{idx:05d}"
            
            # Determine status based on index (distribute status values realistically)
            if idx <= 5:
                status = 'Submitted'
            elif idx <= 10:
                status = 'Under Review'
            elif idx <= 18:
                status = 'Assigned'
            elif idx <= 23:
                status = 'In Progress'
            elif idx <= 27:
                status = 'Resolved'
            elif idx <= 29:
                status = 'Closed'
            else:
                status = 'Reopened'

            # Build complaint
            complaint = Complaint(
                id=comp_id,
                student_id=student.id,
                title=f"Fix {cat_name} Issue in {loc}",
                description=desc,
                category_id=category.id,
                location=loc,
                ai_priority=priority,
                ai_confidence=round(random.uniform(0.70, 0.98), 2),
                suggested_department=category.suggested_department,
                status=status,
                created_at=created_date,
                updated_at=created_date
            )

            # Assign staff for Assigned/In Progress/Resolved/Closed states
            if status in ['Assigned', 'In Progress', 'Resolved', 'Closed']:
                # Find matching staff for specialization
                matching_staff = [s for s in staff_members if s.specialization.lower() in cat_name.lower()]
                if not matching_staff:
                    matching_staff = staff_members
                staff = random.choice(matching_staff)
                
                complaint.assigned_staff_id = staff.id
                
                # Add assignment record
                admin = random.choice(admins)
                assigned_date = created_date + timedelta(hours=random.randint(1, 4))
                assignment = ComplaintAssignment(
                    complaint_id=comp_id,
                    staff_id=staff.id,
                    assigned_by=admin.id,
                    status='Completed' if status in ['Resolved', 'Closed'] else ('Accepted' if status == 'In Progress' else 'Assigned'),
                    assigned_at=assigned_date
                )
                db.session.add(assignment)

            # Handle resolved dates and feedback
            if status in ['Resolved', 'Closed']:
                res_date = complaint.created_at + timedelta(days=random.randint(1, 3), hours=random.randint(1, 12))
                complaint.resolved_at = res_date
                complaint.work_notes = f"Issue fixed. Replaced damaged parts. Tested OK. Done by {staff.user.username}."
                
                # Add feedback if closed
                if status == 'Closed':
                    rating = random.randint(3, 5)
                    comments = random.choice(["Great quick service!", "Fixed on time, thanks.", "Worker was polite and fast.", "Satisfactory resolution."])
                    feedback = Feedback(
                        complaint_id=comp_id,
                        rating=rating,
                        comments=comments,
                        created_at=res_date + timedelta(hours=random.randint(1, 6))
                    )
                    db.session.add(feedback)

            db.session.add(complaint)

            # 4. Generate history logs
            # Created log
            db.session.add(ComplaintHistory(
                complaint_id=comp_id,
                user_id=student.user_id,
                action='Created',
                new_value='Submitted',
                comments="Complaint submitted via student portal.",
                created_at=created_date
            ))

            # Additional logs based on state transitions
            if status in ['Under Review', 'Assigned', 'In Progress', 'Resolved', 'Closed', 'Reopened']:
                # Under review
                review_date = created_date + timedelta(minutes=random.randint(10, 60))
                db.session.add(ComplaintHistory(
                    complaint_id=comp_id,
                    user_id=random.choice(admins).user_id,
                    action='Status Update',
                    previous_value='Submitted',
                    new_value='Under Review',
                    comments="Ticket details verified.",
                    created_at=review_date
                ))

            if status in ['Assigned', 'In Progress', 'Resolved', 'Closed']:
                assign_date = created_date + timedelta(hours=random.randint(1, 3))
                db.session.add(ComplaintHistory(
                    complaint_id=comp_id,
                    user_id=random.choice(admins).user_id,
                    action='Assigned',
                    previous_value='None',
                    new_value=staff.user.username,
                    comments="Estates admin routed the ticket to specialized staff.",
                    created_at=assign_date
                ))
            
            if status in ['In Progress', 'Resolved', 'Closed']:
                accept_date = complaint.created_at + timedelta(hours=random.randint(4, 12))
                db.session.add(ComplaintHistory(
                    complaint_id=comp_id,
                    user_id=staff.user_id,
                    action='Status Update',
                    previous_value='Assigned',
                    new_value='In Progress',
                    comments="Worker accepted task and visited location.",
                    created_at=accept_date
                ))

            if status in ['Resolved', 'Closed']:
                res_date = complaint.resolved_at
                db.session.add(ComplaintHistory(
                    complaint_id=comp_id,
                    user_id=staff.user_id,
                    action='Status Update',
                    previous_value='In Progress',
                    new_value='Resolved',
                    comments="Work completed. Verification done.",
                    created_at=res_date
                ))

            if status == 'Closed':
                close_date = complaint.resolved_at + timedelta(hours=6)
                db.session.add(ComplaintHistory(
                    complaint_id=comp_id,
                    user_id=student.user_id,
                    action='Status Update',
                    previous_value='Resolved',
                    new_value='Closed',
                    comments="Student provided feedback. Ticket closed.",
                    created_at=close_date
                ))

            if status == 'Reopened':
                reopen_date = created_date + timedelta(days=2)
                db.session.add(ComplaintHistory(
                    complaint_id=comp_id,
                    user_id=student.user_id,
                    action='Status Update',
                    previous_value='Resolved',
                    new_value='Reopened',
                    comments="Issue came back. Fan is still making noise.",
                    created_at=reopen_date
                ))

        db.session.commit()
        print("Database seeded with 30 complaints and associated histories successfully.")

if __name__ == '__main__':
    seed_database()
