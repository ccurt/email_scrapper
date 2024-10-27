# config.py

# Google Sheets configuration
    # To get the SHEET_ID for a Google Sheet, follow these steps:
    # 1) Open the Google Sheet in your web browser.
    # 2) Look at the URL in the address bar. It will look something like this: 
    #    https://docs.google.com/spreadsheets/d/1BxiMVs0XRA5nFMdKvBdBZjgmUUqptlbs74OgvE2upms/edit#gid=0
    # 3)  The SHEET_ID is the part of the URL between /d/ and /edit. In this example, the SHEET_ID is 1BxiMVs0XRA5nFMdKvBdBZjgmUUqptlbs74OgvE2upms.
# SHEET_ID = ''  # Replace with your Google Sheet ID -->now entered in the streamlit app
# SHEET_NAME = '' # Replace with the name of the sheet in the Google Sheet -->now entered in the streamlit app

# Gmail API scopes
SCOPES = ['https://www.googleapis.com/auth/gmail.readonly',  # Read-only access to the authenticated user's Gmail inbox
          'https://www.googleapis.com/auth/spreadsheets']    # Read/write access to Google Sheets

# TEACHER_EMAIL = ''  # Replace with the teacher's email address -> now entered in the streamlit app

# Define the maximum number of characters to fetch from the email body
BODY_CHAR_LIMIT = 200