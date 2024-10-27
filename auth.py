from googleapiclient.discovery import build
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
import os
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)

# Use environment variables for paths
TOKEN_PATH = os.getenv('TOKEN_PATH', 'token.json')
CREDENTIALS_PATH = os.getenv('CREDENTIALS_PATH', 'credentials.json')

def authenticate_gmail_and_sheets(scopes):
    """
    Authenticates the user with Gmail and Google Sheets APIs using OAuth 2.0.
    Returns the Gmail and Sheets service objects.
    """
    creds = None

    try:
        # Load existing credentials if available
        if os.path.exists(TOKEN_PATH):
            creds = Credentials.from_authorized_user_file(TOKEN_PATH, scopes)

        # If credentials are not valid, refresh or obtain new ones
        if not creds or not creds.valid:
            if creds and creds.expired and creds.refresh_token:
                creds.refresh(Request())
            else:
                flow = InstalledAppFlow.from_client_secrets_file(CREDENTIALS_PATH, scopes)
                creds = flow.run_local_server(port=8080)
            # Save the credentials for future runs
            with open(TOKEN_PATH, 'w') as token:
                token.write(creds.to_json())

        # Create the Gmail and Sheets service objects
        gmail_service = build('gmail', 'v1', credentials=creds)
        sheets_service = build('sheets', 'v4', credentials=creds)

        return gmail_service, sheets_service

    except Exception as e:
        logging.error(f"An error occurred during authentication: {e}")
        raise

