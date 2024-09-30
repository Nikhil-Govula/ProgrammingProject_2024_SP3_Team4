# src/services/email_service.py

from flask import url_for
from email.mime.text import MIMEText
import base64
import logging
from .google_auth_service import GoogleAuthService

def send_reset_email(email, token, was_locked, role='user'):
    """
    Send a password reset email using the Gmail API.
    :param email: Recipient's email address.
    :param token: Reset token.
    :param was_locked: Boolean indicating if the account was locked.
    :param role: 'user' or 'employer' to customize the reset link.
    """
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
