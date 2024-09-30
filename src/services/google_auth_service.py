# src/services/google_auth_service.py

import json
import logging
from google.auth.exceptions import RefreshError
from google.oauth2.credentials import Credentials
from google.auth.transport.requests import Request
from googleapiclient.discovery import build
from config import get_secret, store_secret
from datetime import datetime

class GoogleAuthService:
    TOKEN_PARAMETER = '/your-app/token'

    @staticmethod
    def get_credentials():
        """
        Retrieve credentials from AWS SSM Parameter Store, refresh if necessary,
        and update the store with new tokens.
        """
        try:
            token_json = get_secret(GoogleAuthService.TOKEN_PARAMETER)
            if not token_json:
                raise ValueError("No token found in SSM Parameter Store")

            credentials = Credentials.from_authorized_user_info(json.loads(token_json))

            if not credentials.valid:
                if credentials.expired and credentials.refresh_token:
                    try:
                        credentials.refresh(Request())
                        logging.info("Credentials refreshed successfully.")
                    except RefreshError as e:
                        if 'Token has been expired or revoked' in str(e):
                            raise TokenExpiredError("Re-authentication required")
                        raise

                    # Update the token in SSM Parameter Store
                    new_token_data = {
                        "token": credentials.token,
                        "refresh_token": credentials.refresh_token,
                        "token_uri": credentials.token_uri,
                        "client_id": credentials.client_id,
                        "client_secret": credentials.client_secret,
                        "scopes": credentials.scopes,
                        "expiry": credentials.expiry.isoformat() if credentials.expiry else None
                    }
                    store_secret(GoogleAuthService.TOKEN_PARAMETER, json.dumps(new_token_data))
                    logging.info("Stored refreshed credentials in SSM Parameter Store.")
                else:
                    raise ValueError("Credentials are invalid and cannot be refreshed.")

            return credentials

        except Exception as e:
            logging.error(f"Error obtaining credentials: {str(e)}")
            logging.exception("Full traceback:")
            raise e

    @staticmethod
    def get_gmail_service():
        """
        Build and return a Gmail API service using valid credentials.
        """
        try:
            credentials = GoogleAuthService.get_credentials()
            service = build('gmail', 'v1', credentials=credentials)
            return service
        except Exception as e:
            logging.error(f"Error building Gmail service: {str(e)}")
            raise e

class TokenExpiredError(Exception):
    pass
