import os
import requests
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.utils import formatdate, make_msgid
from flask import current_app


class EmailService:
    @staticmethod
    def send_otp_email(to_email, user_name, otp_code, purpose_text="verification"):
        """
        Dispatches a 6-digit OTP code to the user's email using Resend API or SMTP.
        Ensures secure header configuration, plain text alternatives, and high deliverability.
        """
        # Intercept and mock emails to example.com to avoid bounce-back complaints on Gmail
        # Only active in development environment (APP_ENV=development) to protect production integrity
        is_development = os.environ.get('APP_ENV') == 'development' or current_app.config.get('ENV') == 'development' or current_app.debug
        if is_development and to_email.endswith('@example.com'):
            current_app.logger.info(f"EMAIL_MOCKED | To: {to_email} | Purpose: {purpose_text} | (OTP Code hidden for security)")
            return True

        api_key = current_app.config.get('EMAIL_API_KEY')
        email_from = current_app.config.get('EMAIL_FROM') or os.environ.get('EMAIL_FROM', 'startupwithus2932@gmail.com')
        
        smtp_server = current_app.config.get('SMTP_SERVER') or os.environ.get('SMTP_SERVER', 'smtp.gmail.com')
        smtp_username = current_app.config.get('SMTP_USERNAME') or os.environ.get('SMTP_USERNAME', 'startupwithus2932@gmail.com')
        smtp_password = current_app.config.get('SMTP_PASSWORD') or os.environ.get('SMTP_PASSWORD', 'daqkbmxqmwofslsh')
        smtp_port = int(current_app.config.get('SMTP_PORT') or os.environ.get('SMTP_PORT', 587))

        # Log started event (do not log the raw OTP code!)
        method = "Unconfigured"
        if api_key:
            method = "Resend API"
        elif smtp_server:
            method = "SMTP Relay"
        
        current_app.logger.info(f"EMAIL_SEND_STARTED | To: {to_email} | Purpose: {purpose_text} | Method: {method}")

        # Deliverability optimized subject line
        subject = "NBKR Assist - Your Verification Code"
        
        # Purpose description translation
        purpose_action = "verify your registration"
        if purpose_text == "login":
            purpose_action = "authorize your login"
        elif purpose_text == "password_reset":
            purpose_action = "reset your password"

        # 1. Plain Text Alternative (Important for spam prevention)
        text_content = f"""NBKR Assist - Email Verification

Hello {user_name},

You requested a verification code to {purpose_action} on the NBKR Assist platform. 

Your 6-digit verification code is: {otp_code}

This code is valid for exactly 5 minutes and can only be used once.

⚠️ Security Warning: Never share this verification code with anyone. NBKR Assist support will never ask for this code.
If you did not request this action, you can safely ignore this email.

Regards,
NBKR Assist System Team
Made by BALAJI NAGELLA
NBKRIST Student Support & Grievance Cell
"""

        # 2. Professional HTML Layout (Optimized for spam filters: light theme, high contrast)
        html_content = f"""<!DOCTYPE html>
<html>
<head>
    <meta charset="utf-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>NBKR Assist AI - Verification Code</title>
    <style>
        body {{
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, 'Helvetica Neue', Arial, sans-serif;
            background-color: #f3f4f6;
            margin: 0;
            padding: 0;
            color: #1f2937;
            -webkit-font-smoothing: antialiased;
        }}
        .container {{
            width: 100%;
            max-width: 600px;
            margin: 0 auto;
            padding: 40px 20px;
        }}
        .card {{
            background-color: #ffffff;
            border-radius: 8px;
            border: 1px solid #e5e7eb;
            box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.05), 0 2px 4px -1px rgba(0, 0, 0, 0.03);
            padding: 40px;
            text-align: center;
        }}
        .logo {{
            font-size: 24px;
            font-weight: bold;
            color: #4f46e5;
            margin-bottom: 24px;
            letter-spacing: -0.025em;
        }}
        .logo-text {{
            background: linear-gradient(135deg, #4f46e5 0%, #0d9488 100%);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
        }}
        .heading {{
            font-size: 20px;
            font-weight: 600;
            color: #111827;
            margin-top: 0;
            margin-bottom: 16px;
        }}
        .body-text {{
            font-size: 15px;
            color: #4b5563;
            line-height: 1.6;
            margin-bottom: 32px;
            text-align: left;
        }}
        .otp-container {{
            background-color: #f9fafb;
            border: 1px solid #e5e7eb;
            border-radius: 6px;
            padding: 20px;
            margin-bottom: 32px;
            display: inline-block;
        }}
        .otp-code {{
            font-family: 'Courier New', Courier, monospace;
            font-size: 36px;
            font-weight: bold;
            color: #4f46e5;
            letter-spacing: 8px;
            margin: 0;
            padding-left: 8px;
        }}
        .alert-box {{
            background-color: #fffbeb;
            border-left: 4px solid #f59e0b;
            border-radius: 4px;
            padding: 16px;
            margin-bottom: 32px;
            text-align: left;
        }}
        .alert-text {{
            font-size: 14px;
            color: #b45309;
            margin: 0;
            line-height: 1.5;
        }}
        .notice-text {{
            font-size: 14px;
            color: #6b7280;
            margin-bottom: 32px;
            text-align: left;
        }}
        .footer {{
            border-top: 1px solid #e5e7eb;
            padding-top: 24px;
            font-size: 12px;
            color: #9ca3af;
            text-align: left;
            line-height: 1.5;
        }}
    </style>
</head>
<body>
    <div class="container">
        <div class="card">
            <div class="logo">
                <span class="logo-text">NBKR Assist</span>
            </div>
            
            <h2 class="heading">Email Verification</h2>
            
            <div class="body-text">
                Hello {user_name},<br><br>
                You requested a verification code to {purpose_action} on the NBKR Assist platform. Please use the following security code to complete this action:
            </div>
            
            <div class="otp-container">
                <div class="otp-code">{otp_code}</div>
            </div>
            
            <div class="alert-box">
                <p class="alert-text">
                    <strong>⚠️ Security Alert:</strong> This code is valid for exactly <strong>5 minutes</strong> and can only be used once. Never share this code with anyone. NBKR Assist support will never ask for this code.
                </p>
            </div>
            
            <div class="notice-text">
                If you did not initiate this request, you can safely ignore this email. No further action is required.
            </div>
            
            <div class="footer">
                This is an automated operational notification from the NBKRIST Student Support & Grievance Cell.<br>
                NBKR Assist Operations | Made by <strong>BALAJI NAGELLA</strong> | Please do not reply directly to this message.
            </div>
        </div>
    </div>
</body>
</html>
"""

        # 3. Resend API Mode
        if api_key:
            try:
                res = requests.post(
                    "https://api.resend.com/emails",
                    headers={
                        "Authorization": f"Bearer {api_key}",
                        "Content-Type": "application/json"
                    },
                    json={
                        "from": f"NBKR Assist <{email_from}>",
                        "to": [to_email],
                        "subject": subject,
                        "html": html_content,
                        "text": text_content
                    },
                    timeout=10
                )
                if res.status_code in [200, 201]:
                    current_app.logger.info(f"EMAIL_SEND_SUCCESS | To: {to_email} | Provider: Resend API")
                    return True
                else:
                    error_msg = f"Resend API error status: {res.status_code}, response: {res.text}"
                    current_app.logger.error(f"EMAIL_SEND_FAILED | To: {to_email} | Error: {error_msg}")
                    return False
            except Exception as e:
                current_app.logger.error(f"EMAIL_SEND_FAILED | To: {to_email} | Error: {str(e)}")
                return False

        # 4. SMTP Mode
        if smtp_server and smtp_username and smtp_password:
            try:
                msg = MIMEMultipart("alternative")
                msg["Subject"] = subject
                msg["From"] = f"NBKR Assist <{email_from}>"
                msg["To"] = to_email
                msg["Date"] = formatdate(localtime=True)
                msg["Message-ID"] = make_msgid(domain='nbkrist.org')
                
                # Add proper MIME parts
                part_text = MIMEText(text_content, "plain")
                part_html = MIMEText(html_content, "html")
                msg.attach(part_text)
                msg.attach(part_html)

                with smtplib.SMTP(smtp_server, smtp_port, timeout=5) as server:
                    server.starttls()
                    server.login(smtp_username, smtp_password)
                    server.sendmail(email_from, to_email, msg.as_string())
                
                current_app.logger.info(f"EMAIL_SEND_SUCCESS | To: {to_email} | Provider: SMTP Relay")
                return True
            except Exception as e:
                current_app.logger.error(f"EMAIL_SEND_FAILED | To: {to_email} | Error: {str(e)}")
                return False

        # 5. Unconfigured Error
        err_msg = "No email provider credentials configured (EMAIL_API_KEY and SMTP settings are empty)."
        current_app.logger.error(f"EMAIL_SEND_FAILED | To: {to_email} | Error: {err_msg}")
        return False

    @staticmethod
    def send_test_email(to_email, subject, message_text):
        """
        Sends a plain text / simple HTML email for diagnostic testing.
        Returns True if successful, and False otherwise.
        """
        # Intercept and mock emails to example.com to avoid bounce-back complaints on Gmail
        # Only active in development environment (APP_ENV=development) to protect production integrity
        is_development = os.environ.get('APP_ENV') == 'development' or current_app.config.get('ENV') == 'development' or current_app.debug
        if is_development and to_email.endswith('@example.com'):
            current_app.logger.info(f"EMAIL_MOCKED | To: {to_email} | Purpose: Test Email | (Content hidden for security)")
            return True

        api_key = current_app.config.get('EMAIL_API_KEY')
        email_from = current_app.config.get('EMAIL_FROM') or os.environ.get('EMAIL_FROM', 'startupwithus2932@gmail.com')
        
        smtp_server = current_app.config.get('SMTP_SERVER') or os.environ.get('SMTP_SERVER', 'smtp.gmail.com')
        smtp_username = current_app.config.get('SMTP_USERNAME') or os.environ.get('SMTP_USERNAME', 'startupwithus2932@gmail.com')
        smtp_password = current_app.config.get('SMTP_PASSWORD') or os.environ.get('SMTP_PASSWORD', 'daqkbmxqmwofslsh')
        smtp_port = int(current_app.config.get('SMTP_PORT') or os.environ.get('SMTP_PORT', 587))

        current_app.logger.info(f"EMAIL_SEND_STARTED | To: {to_email} | Purpose: Test Email")

        # Plain Text version
        text_content = f"{subject}\n\n{message_text}\n\nRegards,\nNBKR Assist AI System Team"

        # HTML version
        html_content = f"""<!DOCTYPE html>
<html>
<head>
    <meta charset="utf-8">
    <title>{subject}</title>
    <style>
        body {{ font-family: sans-serif; background-color: #f3f4f6; color: #1f2937; padding: 20px; }}
        .card {{ background-color: #ffffff; border-radius: 8px; border: 1px solid #e5e7eb; padding: 30px; max-width: 600px; margin: 0 auto; }}
        .header {{ font-size: 20px; font-weight: bold; color: #4f46e5; margin-bottom: 20px; }}
        .footer {{ border-top: 1px solid #e5e7eb; margin-top: 20px; padding-top: 15px; font-size: 12px; color: #9ca3af; }}
    </style>
</head>
<body>
    <div class="card">
        <div class="header">NBKR Assist System Diagnostic</div>
        <p>{message_text}</p>
        <div class="footer">
            This is a test notification from NBKRIST Student Support & Grievance Cell &bull; Made by BALAJI NAGELLA. Please do not reply.
        </div>
    </div>
</body>
</html>"""

        # 1. Resend API Mode
        if api_key:
            try:
                res = requests.post(
                    "https://api.resend.com/emails",
                    headers={
                        "Authorization": f"Bearer {api_key}",
                        "Content-Type": "application/json"
                    },
                    json={
                        "from": f"NBKR Assist <{email_from}>",
                        "to": [to_email],
                        "subject": subject,
                        "html": html_content,
                        "text": text_content
                    },
                    timeout=10
                )
                if res.status_code in [200, 201]:
                    current_app.logger.info(f"EMAIL_SEND_SUCCESS | To: {to_email} | Provider: Resend API")
                    return True
                else:
                    error_msg = f"Resend API error status: {res.status_code}, response: {res.text}"
                    current_app.logger.error(f"EMAIL_SEND_FAILED | To: {to_email} | Error: {error_msg}")
                    return False
            except Exception as e:
                current_app.logger.error(f"EMAIL_SEND_FAILED | To: {to_email} | Error: {str(e)}")
                return False

        # 2. SMTP Mode
        if smtp_server and smtp_username and smtp_password:
            try:
                msg = MIMEMultipart("alternative")
                msg["Subject"] = subject
                msg["From"] = f"NBKR Assist <{email_from}>"
                msg["To"] = to_email
                msg["Date"] = formatdate(localtime=True)
                msg["Message-ID"] = make_msgid(domain='nbkrist.org')
                
                part_text = MIMEText(text_content, "plain")
                part_html = MIMEText(html_content, "html")
                msg.attach(part_text)
                msg.attach(part_html)

                with smtplib.SMTP(smtp_server, smtp_port, timeout=5) as server:
                    server.starttls()
                    server.login(smtp_username, smtp_password)
                    server.sendmail(email_from, to_email, msg.as_string())
                
                current_app.logger.info(f"EMAIL_SEND_SUCCESS | To: {to_email} | Provider: SMTP Relay")
                return True
            except Exception as e:
                current_app.logger.error(f"EMAIL_SEND_FAILED | To: {to_email} | Error: {str(e)}")
                return False

        # 3. Unconfigured Error
        err_msg = "No email provider credentials configured (EMAIL_API_KEY and SMTP settings are empty)."
        current_app.logger.error(f"EMAIL_SEND_FAILED | To: {to_email} | Error: {err_msg}")
        return False

    @staticmethod
    def send_assignment_email(to_email, faculty_name, complaint_id, category_name, priority, branch=None, assigned_date=None, resolution_deadline=None):
        """
        Sends an assignment notification email to the assigned faculty.
        Returns True if successful, and False otherwise.
        """
        is_development = os.environ.get('APP_ENV') == 'development' or current_app.config.get('ENV') == 'development' or current_app.debug
        if is_development and to_email.endswith('@example.com'):
            current_app.logger.info(f"EMAIL_MOCKED | To: {to_email} | Purpose: Grievance Assignment")
            return True

        api_key = current_app.config.get('EMAIL_API_KEY')
        email_from = current_app.config.get('EMAIL_FROM', 'startupwithus2932@gmail.com')
        
        smtp_server = current_app.config.get('SMTP_SERVER')
        smtp_username = current_app.config.get('SMTP_USERNAME')
        smtp_password = current_app.config.get('SMTP_PASSWORD')
        smtp_port = current_app.config.get('SMTP_PORT', 587)

        subject = "New Grievance Assigned — NBKR Assist"

        branch_text = f"\nBranch:\n{branch}" if branch else ""
        assigned_text = f"\nAssigned:\n{assigned_date}" if assigned_date else ""
        deadline_text = f"\nResolution Deadline:\n{resolution_deadline}" if resolution_deadline else ""

        text_content = f"""Dear {faculty_name},

A new grievance has been assigned to you.

Grievance ID: {complaint_id}
Category: {category_name}
Priority: {priority}{branch_text}{assigned_text}{deadline_text}

Please login to NBKR Assist to review and resolve the grievance.

Regards,
NBKR Assist System
Made by BALAJI NAGELLA
"""

        branch_html = f"""<div class="detail-label">Branch:</div>
        <div class="detail-val">{branch}</div>""" if branch else ""
        assigned_html = f"""<div class="detail-label">Assigned:</div>
        <div class="detail-val">{assigned_date}</div>""" if assigned_date else ""
        deadline_html = f"""<div class="detail-label">Resolution Deadline:</div>
        <div class="detail-val">{resolution_deadline}</div>""" if resolution_deadline else ""

        html_content = f"""<!DOCTYPE html>
<html>
<head>
    <meta charset="utf-8">
    <title>{subject}</title>
    <style>
        body {{ font-family: sans-serif; background-color: #f3f4f6; color: #1f2937; padding: 20px; }}
        .card {{ background-color: #ffffff; border-radius: 8px; border: 1px solid #e5e7eb; padding: 30px; max-width: 600px; margin: 0 auto; }}
        .header {{ font-size: 20px; font-weight: bold; color: #4f46e5; margin-bottom: 20px; }}
        .detail-label {{ font-weight: bold; color: #4b5563; }}
        .detail-val {{ margin-bottom: 15px; color: #111827; }}
        .footer {{ border-top: 1px solid #e5e7eb; margin-top: 20px; padding-top: 15px; font-size: 12px; color: #9ca3af; }}
    </style>
</head>
<body>
    <div class="card">
        <div class="header">New Grievance Assigned</div>
        <p>Dear {faculty_name},</p>
        <p>A new student grievance has been assigned to you.</p>
        
        <div class="detail-label">Grievance ID:</div>
        <div class="detail-val">{complaint_id}</div>
        
        <div class="detail-label">Category:</div>
        <div class="detail-val">{category_name}</div>
        
        <div class="detail-label">Priority:</div>
        <div class="detail-val">{priority}</div>
        {branch_html}
        {assigned_html}
        {deadline_html}
        
        <p>Please login to NBKR Assist to review and resolve the grievance.</p>
        
        <div class="footer">
            Regards,<br>
            NBKR Assist System &bull; Made by <strong>BALAJI NAGELLA</strong>
        </div>
    </div>
</body>
</html>"""

        if api_key:
            try:
                res = requests.post(
                    "https://api.resend.com/emails",
                    headers={
                        "Authorization": f"Bearer {api_key}",
                        "Content-Type": "application/json"
                    },
                    json={
                        "from": f"NBKR Assist <{email_from}>",
                        "to": [to_email],
                        "subject": subject,
                        "html": html_content,
                        "text": text_content
                    },
                    timeout=10
                )
                if res.status_code in [200, 201]:
                    current_app.logger.info(f"EMAIL_SEND_SUCCESS | To: {to_email} | Provider: Resend API")
                    return True
                return False
            except Exception as e:
                current_app.logger.error(f"EMAIL_SEND_FAILED | To: {to_email} | Error: {str(e)}")
                return False

        if smtp_server and smtp_username and smtp_password:
            try:
                msg = MIMEMultipart("alternative")
                msg["Subject"] = subject
                msg["From"] = f"NBKR Assist <{email_from}>"
                msg["To"] = to_email
                msg["Date"] = formatdate(localtime=True)
                msg["Message-ID"] = make_msgid(domain='nbkrist.org')
                
                part_text = MIMEText(text_content, "plain")
                part_html = MIMEText(html_content, "html")
                msg.attach(part_text)
                msg.attach(part_html)

                with smtplib.SMTP(smtp_server, smtp_port, timeout=5) as server:
                    server.starttls()
                    server.login(smtp_username, smtp_password)
                    server.sendmail(email_from, to_email, msg.as_string())
                
                current_app.logger.info(f"EMAIL_SEND_SUCCESS | To: {to_email} | Provider: SMTP Relay")
                return True
            except Exception as e:
                current_app.logger.error(f"EMAIL_SEND_FAILED | To: {to_email} | Error: {str(e)}")
                return False

        return False
