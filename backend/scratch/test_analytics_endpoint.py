import sys
import json

sys.path.append("C:/Users/nagel/Documents/MY EVERYTHING/resume pro/backend")
sys.path.append("C:/Users/nagel/Documents/MY EVERYTHING/resume pro/backend/app")

from run import app

client = app.test_client()

def get_auth_headers(email):
    with app.app_context():
        from app.models.user import User
        user = User.query.filter_by(email=email).first()
        from flask_jwt_extended import create_access_token
        token = create_access_token(identity=str(user.id), additional_claims={"role": user.role})
        return {"Authorization": f"Bearer {token}"}

headers = get_auth_headers("admin1@college.edu")

for url in [
    "/api/admin/analytics",
    "/api/admin/analytics/overview",
    "/api/admin/analytics/attendance",
    "/api/admin/analytics/modules"
]:
    res = client.get(url, headers=headers)
    print(f"URL: {url} -> Status: {res.status_code}")
    try:
        data = json.loads(res.data)
        print(f"  Success: {data.get('success')}")
        if not data.get('success'):
            print(f"  Error message: {data.get('message')}")
            print(f"  Error details: {data.get('error')}")
    except Exception as e:
        print("  Parse error:", str(e))
