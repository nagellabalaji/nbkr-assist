import requests
import json

url = "http://localhost:5000/api/auth/register/send-otp"
headers = {"Content-Type": "application/json"}

print("=" * 60)
print(" TESTING DUPLICATE REGISTRATION CHECKS ")
print("=" * 60)

# Case 1: Same email duplicate registration check
payload_email = {
    "username": "differentusername",
    "email": "balajinagella7@gmail.com", # Exists in DB
    "password": "Password123",
    "role": "student",
    "roll_no": "NEWROLL123",
    "department_id": 1
}
print("[1] Requesting OTP with duplicate email...")
res_email = requests.post(url, headers=headers, json=payload_email)
print(f" -> Status Code: {res_email.status_code}")
print(f" -> Response JSON: {res_email.json()}")
if res_email.status_code == 400 and res_email.json().get("error") == "email_exists":
    print(" -> SUCCESS: Duplicate email correctly rejected with 'Email already registered'.")
else:
    print(" -> FAIL: Duplicate email was not correctly rejected.")

print("\n" + "=" * 60)

# Case 2: Same student ID duplicate registration check
payload_roll = {
    "username": "differentusername2",
    "email": "differentemail@college.edu",
    "password": "Password123",
    "role": "student",
    "roll_no": "CS26B1001", # Exists in DB (belongs to student1)
    "department_id": 1
}
print("[2] Requesting OTP with duplicate Student ID...")
res_roll = requests.post(url, headers=headers, json=payload_roll)
print(f" -> Status Code: {res_roll.status_code}")
print(f" -> Response JSON: {res_roll.json()}")
if res_roll.status_code == 400 and res_roll.json().get("error") == "roll_no_exists":
    print(" -> SUCCESS: Duplicate Student ID correctly rejected with 'Roll number already exists'.")
else:
    print(" -> FAIL: Duplicate Student ID was not correctly rejected.")
    
print("=" * 60)
