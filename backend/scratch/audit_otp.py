import os
import re

print("="*60)
print(" AUDITING BACKEND FOR OTP PLAIN TEXT LEAKS ")
print("="*60)

BACKEND_DIR = r"c:\Users\nagel\Desktop\resume pro\backend\app"

patterns = [
    r"print\(.*otp.*\)",
    r"print\(.*code.*\)",
    r"logger\..*otp.*",
    r"logger\..*code.*",
    r"log\..*otp.*",
    r"log\..*code.*",
    r"OTP:",
    r"verification_code",
    r"otp_code"
]

compiled_patterns = [re.compile(p, re.IGNORECASE) for p in patterns]

leaks_found = 0

for root, dirs, files in os.walk(BACKEND_DIR):
    for file in files:
        if file.endswith(".py"):
            filepath = os.path.join(root, file)
            try:
                with open(filepath, "r", encoding="utf-8") as f:
                    lines = f.readlines()
                for line_idx, line in enumerate(lines, 1):
                    for pattern, raw_pat in zip(compiled_patterns, patterns):
                        if pattern.search(line):
                            # Exclude normal function/variable definitions or database fields
                            # We only care about printing, logging, or returning in response
                            is_leak_suspect = False
                            
                            # Checks
                            if "print(" in line or "logger." in line or "log(" in line:
                                # Make sure it's not a generic log without the actual variable
                                # E.g., logger.info("OTP sent successfully") is fine.
                                # But logger.info(f"OTP is {otp}") is a leak!
                                if "{" in line or "%" in line or "+" in line or "," in line or "f\"" in line or "f'" in line:
                                    is_leak_suspect = True
                            
                            if "return" in line and ("otp" in line or "code" in line):
                                # E.g., return jsonify({"otp": otp}) is a leak!
                                # E.g., return jsonify({"require_otp": True}) is fine.
                                if "otp" in line.lower() and "require_otp" not in line:
                                    is_leak_suspect = True
                            
                            if is_leak_suspect:
                                print(f"Suspect Leak in {file}:{line_idx}")
                                print(f"  Line: {line.strip()}")
                                print(f"  Pattern: {raw_pat}")
                                print("-" * 40)
                                leaks_found += 1
            except Exception as e:
                print(f"Error reading {filepath}: {str(e)}")

print(f"Audit complete. Suspect leaks found: {leaks_found}")
print("="*60)
