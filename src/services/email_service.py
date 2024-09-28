from flask import url_for
from email.mime.text import MIMEText
import base64
import json
import logging
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build
from config import get_secret  # Ensure this imports the module-level function

def send_reset_email(email, token, was_locked):
    logging.info("send_reset_email in email_service called")
    try:
        token_json = get_secret('/your-app/token')
        if not token_json:
            raise ValueError("No token found in SSM Parameter Store")

        credentials = Credentials.from_authorized_user_info(json.loads(token_json))
        service = build('gmail', 'v1', credentials=credentials)

        reset_link = url_for('logins.reset_with_token', token=token, _external=True)
        subject = 'Password Reset Request'
        unlock_message = " and unlock your account" if was_locked else ""
        body = f'''To reset your password{unlock_message}, visit the following link:
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
