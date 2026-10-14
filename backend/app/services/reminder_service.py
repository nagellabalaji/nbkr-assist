import os
from datetime import datetime, timedelta
from app import db
from app.models.complaint import Complaint
from app.models.log_feedback import Notification
from app.services.email_service import EmailService

class ReminderService:
    @staticmethod
    def check_and_send_reminders():
        """
        Scans all active (Assigned, In Progress) complaints and dispatches reminders:
        - 1 day before deadline: Warning reminder
        - Past deadline: Overdue reminder
        Checks the Notification table to prevent duplicate reminders.
        """
        now = datetime.utcnow()
        active_complaints = Complaint.query.filter(Complaint.status.in_(['Assigned', 'In Progress'])).all()
        reminders_sent = 0
        overdue_sent = 0

        for comp in active_complaints:
            if not comp.sla_deadline or not comp.assigned_staff:
                continue

            faculty = comp.assigned_staff
            to_email = faculty.user.email if faculty.user else None
            faculty_name = faculty.user.username if faculty.user else "Faculty"
            if not to_email:
                continue

            time_left = comp.sla_deadline - now

            # 1. Check if due within 24 hours (1 day) and not yet sent
            if timedelta(seconds=0) < time_left <= timedelta(hours=24):
                # Check for existing warning notification
                dup_notif = Notification.query.filter_by(
                    complaint_id=comp.id,
                    type='deadline_reminder_due'
                ).first()

                if not dup_notif:
                    # Create notification
                    notif = Notification(
                        user_id=faculty.user_id,
                        title=f"Reminder: Grievance #{comp.id} is due tomorrow.",
                        message=f"Reminder: Grievance #{comp.id} is due tomorrow ({comp.sla_deadline.strftime('%d %b %Y')}). Please login to NBKR Assist AI to resolve it.",
                        type='deadline_reminder_due',
                        complaint_id=comp.id
                    )
                    db.session.add(notif)
                    db.session.commit()

                    # Send email
                    try:
                        subject = f"Reminder: Grievance #{comp.id} is due tomorrow"
                        ReminderService._dispatch_reminder_email(to_email, faculty_name, subject, notif.message)
                    except Exception as err:
                        from flask import current_app
                        current_app.logger.error(f"Failed to send deadline reminder email to {to_email}: {str(err)}")
                    
                    reminders_sent += 1

            # 2. Check if overdue and not yet sent
            elif time_left < timedelta(seconds=0):
                # Check for existing overdue notification
                dup_notif = Notification.query.filter_by(
                    complaint_id=comp.id,
                    type='deadline_reminder_overdue'
                ).first()

                if not dup_notif:
                    # Create notification
                    notif = Notification(
                        user_id=faculty.user_id,
                        title=f"Overdue: Grievance #{comp.id} has exceeded its resolution deadline.",
                        message=f"Overdue: Grievance #{comp.id} has exceeded its resolution deadline. Please resolve it immediately.",
                        type='deadline_reminder_overdue',
                        complaint_id=comp.id
                    )
                    db.session.add(notif)
                    db.session.commit()

                    # Send email
                    try:
                        subject = f"Overdue: Grievance #{comp.id} has exceeded its resolution deadline"
                        ReminderService._dispatch_reminder_email(to_email, faculty_name, subject, notif.message)
                    except Exception as err:
                        from flask import current_app
                        current_app.logger.error(f"Failed to send overdue email to {to_email}: {str(err)}")
                    
                    overdue_sent += 1

        return {
            'reminders_sent': reminders_sent,
            'overdue_sent': overdue_sent
        }

    @staticmethod
    def _dispatch_reminder_email(to_email, faculty_name, subject, message_body):
        from flask import current_app
        import smtplib
        from email.mime.text import MIMEText
        from email.mime.multipart import MIMEMultipart
        from email.utils import formatdate, make_msgid
        import requests

        is_development = os.environ.get('APP_ENV') == 'development' or current_app.config.get('ENV') == 'development' or current_app.debug
        if is_development and to_email.endswith('@example.com'):
            current_app.logger.info(f"EMAIL_MOCKED | To: {to_email} | Subject: {subject}")
            return True

        api_key = current_app.config.get('EMAIL_API_KEY')
        email_from = current_app.config.get('EMAIL_FROM', 'startupwithus2932@gmail.com')
        
        smtp_server = current_app.config.get('SMTP_SERVER')
        smtp_username = current_app.config.get('SMTP_USERNAME')
        smtp_password = current_app.config.get('SMTP_PASSWORD')
        smtp_port = current_app.config.get('SMTP_PORT', 587)

        text_content = f"""Dear {faculty_name},

{message_body}

Regards,
NBKR Assist AI
"""

        html_content = f"""<!DOCTYPE html>
<html>
<head>
    <meta charset="utf-8">
    <title>{subject}</title>
    <style>
        body {{ font-family: sans-serif; background-color: #f3f4f6; color: #1f2937; padding: 20px; }}
        .card {{ background-color: #ffffff; border-radius: 8px; border: 1px solid #e5e7eb; padding: 30px; max-width: 600px; margin: 0 auto; }}
        .header {{ font-size: 20px; font-weight: bold; color: #dc2626; margin-bottom: 20px; }}
        .body-text {{ font-size: 14px; line-height: 1.5; color: #4b5563; }}
        .footer {{ border-top: 1px solid #e5e7eb; margin-top: 20px; padding-top: 15px; font-size: 12px; color: #9ca3af; }}
    </style>
</head>
<body>
    <div class="card">
        <div class="header">{subject}</div>
        <p class="body-text">Dear {faculty_name},</p>
        <p class="body-text">{message_body}</p>
        <div class="footer">
            Regards,<br>
            NBKR Assist AI
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
                        "from": f"NBKR Assist AI <{email_from}>",
                        "to": [to_email],
                        "subject": subject,
                        "html": html_content,
                        "text": text_content
                    },
                    timeout=10
                )
                if res.status_code in [200, 201]:
                    current_app.logger.info(f"EMAIL_SEND_SUCCESS | To: {to_email} | Subject: {subject} | Provider: Resend API")
                    return True
            except Exception as e:
                current_app.logger.error(f"EMAIL_SEND_FAILED | To: {to_email} | Error: {str(e)}")
                return False

        if smtp_server and smtp_username and smtp_password:
            try:
                msg = MIMEMultipart("alternative")
                msg["Subject"] = subject
                msg["From"] = f"NBKR Assist AI <{email_from}>"
                msg["To"] = to_email
                msg["Date"] = formatdate(localtime=True)
                msg["Message-ID"] = make_msgid(domain='nbkrist.org')
                
                part_text = MIMEText(text_content, "plain")
                part_html = MIMEText(html_content, "html")
                msg.attach(part_text)
                msg.attach(part_html)

                with smtplib.SMTP(smtp_server, smtp_port) as server:
                    server.starttls()
                    server.login(smtp_username, smtp_password)
                    server.sendmail(email_from, [to_email], msg.as_string())
                current_app.logger.info(f"EMAIL_SEND_SUCCESS | To: {to_email} | Subject: {subject} | Provider: SMTP Relay")
                return True
            except Exception as e:
                current_app.logger.error(f"EMAIL_SEND_FAILED | To: {to_email} | Error: {str(e)}")
                return False
        return False
