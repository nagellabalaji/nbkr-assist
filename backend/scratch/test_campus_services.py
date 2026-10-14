import sys
import json
from datetime import datetime

sys.path.append("C:/Users/nagel/Documents/MY EVERYTHING/resume pro/backend")
sys.path.append("C:/Users/nagel/Documents/MY EVERYTHING/resume pro/backend/app")

from run import app
from app import db
from app.models.user import User, Student
from app.models.hostel import HostelRequest
from app.models.transport import TransportRoute, TransportRequest
from app.models.library import LibraryBook, LibraryRequest
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
    print(" RUNNING PHASE 8 CAMPUS SERVICES WORKFLOW & SECURITY TESTS ")
    print("=" * 60)

    # 1. Admin Authentication checks
    print("Test 1: Authenticating administrators and students...")
    headers_stu_a, _ = get_auth_headers("student01@example.com") # Hostel student (Hosteller, CSE)
    headers_stu_b, _ = get_auth_headers("student2@student.edu") # Dayscholar student (ECE)
    headers_ha, _ = get_auth_headers("hostel@example.com") # Hostel Admin
    headers_ta, _ = get_auth_headers("transport@example.com") # Transport Admin
    headers_lib, _ = get_auth_headers("librarian@example.com") # Librarian
    print(" -> SUCCESS")

    with app.app_context():
        student_a = Student.query.filter_by(roll_no="CSE-2026-0001").first()
        student_a_id = student_a.id if student_a else 1
        print(f" -> Student A (Hosteller) DB ID resolved to: {student_a_id}")

    # 2. Hostel Service Workflows & Security
    print("\nTest 2: Creating a new hostel request from Student A (CSE Hosteller)...")
    res = client.post("/api/hostel/requests", headers=headers_stu_a, json={
        "request_type": "electrical",
        "description": "Fan speed regulator broken."
    })
    print(f" -> Status: {res.status_code}")
    assert res.status_code == 201
    req_a_id = json.loads(res.data)["data"]["id"]

    print("\nTest 3: Dayscholar Student B attempting to raise room maintenance request...")
    res = client.post("/api/hostel/requests", headers=headers_stu_b, json={
        "request_type": "plumbing",
        "description": "Pipe leaking."
    })
    print(f" -> Status: {res.status_code}")
    assert res.status_code == 400, "Dayscholar allowed to raise room maintenance requests!"

    print("\nTest 4: IDOR check - Student B attempting to read Student A's hostel request list...")
    res = client.get("/api/hostel/requests", headers=headers_stu_b)
    data = json.loads(res.data)["data"]
    print(f" -> Student B sees requests count: {len(data)}")
    assert all(r["id"] != req_a_id for r in data), "Student B breached IDOR to view Student A's hostel request!"

    print("\nTest 5: RBAC check - Transport Admin attempting to approve hostel request...")
    res = client.put(f"/api/hostel/requests/{req_a_id}", headers=headers_ta, json={
        "status": "in_progress",
        "admin_notes": "Assigned to transport worker."
    })
    print(f" -> Status: {res.status_code}")
    assert res.status_code == 403

    print("\nTest 6: Hostel Admin updating hostel request status to in_progress...")
    res = client.put(f"/api/hostel/requests/{req_a_id}", headers=headers_ha, json={
        "status": "in_progress",
        "admin_notes": "Electrician has been dispatched."
    })
    print(f" -> Status: {res.status_code}")
    assert res.status_code == 200

    # 3. Transport Service Workflows & Security
    print("\nTest 7: Fetching bus routes...")
    res = client.get("/api/transport/routes", headers=headers_stu_a)
    print(f" -> Status: {res.status_code}")
    assert res.status_code == 200
    routes = json.loads(res.data)["data"]
    assert len(routes) > 0
    route_id = routes[0]["id"]

    print("\nTest 8: Student A raising a new transport pass request...")
    res = client.post("/api/transport/requests", headers=headers_stu_a, json={
        "request_type": "new_pass",
        "route_id": route_id,
        "description": "Req new college bus pass for Nellore route."
    })
    print(f" -> Status: {res.status_code}")
    assert res.status_code == 201
    trans_req_id = json.loads(res.data)["data"]["id"]

    print("\nTest 9: IDOR check - Student B trying to edit Student A's transport request...")
    res = client.put(f"/api/transport/requests/{trans_req_id}", headers=headers_stu_b, json={
        "description": "Malicious edit description."
    })
    print(f" -> Status: {res.status_code}")
    assert res.status_code == 403

    print("\nTest 10: Transport Admin approving the transport request...")
    res = client.put(f"/api/transport/requests/{trans_req_id}", headers=headers_ta, json={
        "status": "approved",
        "admin_notes": "Pass issued."
    })
    print(f" -> Status: {res.status_code}")
    assert res.status_code == 200

    # 4. Library Service Workflows & Security
    print("\nTest 11: Fetching library books catalog...")
    res = client.get("/api/library/books?search=web", headers=headers_stu_a)
    print(f" -> Status: {res.status_code}")
    assert res.status_code == 200
    books = json.loads(res.data)["data"]
    assert len(books) > 0
    book_id = books[0]["id"]

    print("\nTest 12: Student A requesting to borrow a book...")
    res = client.post("/api/library/requests", headers=headers_stu_a, json={
        "book_id": book_id,
        "request_type": "borrow"
    })
    print(f" -> Status: {res.status_code}")
    assert res.status_code == 201
    borrow_req_id = json.loads(res.data)["data"]["id"]

    print("\nTest 13: Librarian approving the book borrow request...")
    res = client.put(f"/api/library/requests/{borrow_req_id}", headers=headers_lib, json={
        "status": "approved",
        "admin_notes": "Book issued."
    })
    print(f" -> Status: {res.status_code}")
    assert res.status_code == 200

    print("\nTest 14: Student A submitting return request...")
    res = client.post("/api/library/requests", headers=headers_stu_a, json={
        "book_id": book_id,
        "request_type": "return"
    })
    print(f" -> Status: {res.status_code}")
    assert res.status_code == 201
    return_req_id = json.loads(res.data)["data"]["id"]

    print("\nTest 15: Librarian approving the return request (closing transaction)...")
    res = client.put(f"/api/library/requests/{return_req_id}", headers=headers_lib, json={
        "status": "returned",
        "admin_notes": "Returned in perfect condition."
    })
    print(f" -> Status: {res.status_code}")
    assert res.status_code == 200

    # Clean up test transactions from DB
    print("\nCleaning up test requests from DB...")
    with app.app_context():
        HostelRequest.query.filter_by(student_id=student_a_id).delete()
        TransportRequest.query.filter_by(student_id=student_a_id).delete()
        LibraryRequest.query.filter_by(student_id=student_a_id).delete()
        db.session.commit()
    print(" -> Cleanup SUCCESS")

    print("\n" + "=" * 60)
    print(" ALL CAMPUS SERVICES SECURITY CHECKS PASSED ")
    print("=" * 60)

if __name__ == "__main__":
    run_tests()
