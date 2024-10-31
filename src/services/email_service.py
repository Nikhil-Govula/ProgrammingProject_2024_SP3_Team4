from flask import url_for
from email.mime.text import MIMEText
import base64
import logging
from .google_auth_service import GoogleAuthService

def send_reset_email(email, token, was_locked, role='user'):
    logging.info("send_reset_email in email_service called")
    try:
        service = GoogleAuthService.get_gmail_service()

        if role == 'user':
            reset_link = url_for('user_views.reset_with_token', token=token, _external=True)
            subject = 'User Password Reset Request'
            prefix = "To reset your password"
        elif role == 'employer':
            reset_link = url_for('employer_views.reset_with_token', token=token, _external=True)
            subject = 'Employer Password Reset Request'
            prefix = "To reset your password"
        elif role == 'admin':
            reset_link = url_for('admin_views.reset_with_token', token=token, _external=True)
            subject = 'Admin Password Reset Request'
            prefix = "To reset your password"
        else:
            reset_link = url_for('landing.landing', _external=True)
            subject = 'Password Reset Request'
            prefix = "To reset your password"

        unlock_message = " and unlock your account" if was_locked else ""
        body = f'''{prefix}{unlock_message}, visit the following link:
{reset_link}

If you did not make this request then simply ignore this email and no changes will be made.
'''

        message = MIMEText(body)
        message['to'] = email
        message['subject'] = subject
        raw_message = base64.urlsafe_b64encode(message.as_bytes()).decode('utf-8')

        service.users().messages().send(userId='me', body={'raw': raw_message}).execute()
        logging.info("Email sent successfully via Gmail API")
        return True
    except Exception as e:
        logging.error(f"Error sending email via Gmail API: {str(e)}")
        logging.exception("Full traceback:")
        return False

def send_verification_email(email, verification_link, role='user'):
    logging.info("send_verification_email in email_service called")
    try:
        service = GoogleAuthService.get_gmail_service()

        if role == 'user':
            subject = 'Activate Your JobTrunk Account'
            body = f'''Hello,

Thank you for registering at JobTrunk! Please click the link below to verify your account:

{verification_link}

If you did not register for this account, please ignore this email.

Best regards,
JobTrunk Team
'''
        elif role == 'employer':
            subject = 'Activate Your Employer Account'
            body = f'''Hello,

Thank you for registering as an employer at JobTrunk! Please click the link below to verify your account:

{verification_link}

If you did not register for this account, please ignore this email.

Best regards,
JobTrunk Team
'''
        elif role == 'admin':
            subject = 'Activate Your Admin Account'
            body = f'''Hello,

Please click the link below to verify your admin account:

{verification_link}

Best regards,
JobTrunk Team
'''
        else:
            subject = 'Account Verification'
            body = f'''Hello,

Please verify your account by clicking the link below:

{verification_link}

Best regards,
JobTrunk Team
'''

        message = MIMEText(body)
        message['to'] = email
        message['subject'] = subject
        raw_message = base64.urlsafe_b64encode(message.as_bytes()).decode('utf-8')

        service.users().messages().send(userId='me', body={'raw': raw_message}).execute()
        logging.info("Verification email sent successfully via Gmail API")
        return True
    except Exception as e:
        logging.error(f"Error sending verification email via Gmail API: {str(e)}")
        logging.exception("Full traceback:")
        return False