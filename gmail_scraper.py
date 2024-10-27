import base64  # Import base64 for decoding email content
from datetime import datetime
from googleapiclient.errors import HttpError
from email.utils import parsedate_to_datetime
from config import BODY_CHAR_LIMIT


def format_gmail_date(gmail_date):
    """
    Converts Gmail's date string to standard datetime format: '%m/%d/%Y %H:%M:%S'.
    """
    try:
        date_obj = parsedate_to_datetime(gmail_date)
        return date_obj.strftime('%m/%d/%Y %H:%M:%S')
    except Exception as e:
        print(f"Error parsing date: {e}")
        return None

def extract_email_body(msg_payload):
    """
    Extracts the email body from the payload, limiting to `BODY_CHAR_LIMIT` characters.
    """
    body = None
    if 'parts' in msg_payload:
        for part in msg_payload['parts']:
            if part['mimeType'] == 'text/plain':
                body = base64.urlsafe_b64decode(part['body']['data']).decode('utf-8')[:BODY_CHAR_LIMIT]
                break
    elif msg_payload.get('mimeType') == 'text/plain':
        body = base64.urlsafe_b64decode(msg_payload['body']['data']).decode('utf-8')[:BODY_CHAR_LIMIT]
    return body

def search_emails(service, query):
    """
    Searches for emails using the Gmail API with the given query.
    """
    try:
        results = service.users().messages().list(userId='me', q=query).execute()
        return results.get('messages', [])
    except HttpError as error:
        print(f"An error occurred: {error}")
        return []

def batch_fetch_email_details(service, messages, last_saved_date):
    """
    Fetches and returns email details (date, sender, receiver, body), filtering by last saved timestamp.
    """
    email_data = []
    last_saved_dt = datetime.strptime(last_saved_date, '%m/%d/%Y %H:%M:%S')

    for msg in messages:
        msg_id = msg['id']
        try:
            msg_data = service.users().messages().get(userId='me', id=msg_id, format='full').execute()
            msg_payload = msg_data.get('payload', {})
            headers = {header['name']: header['value'] for header in msg_payload.get("headers", [])}

            date = format_gmail_date(headers.get('Date'))
            sender = headers.get('From')
            receiver = headers.get('To')
            body = extract_email_body(msg_payload)

            # Filter emails that are strictly after the last saved timestamp
            if date and sender and receiver:
                email_date = datetime.strptime(date, '%m/%d/%Y %H:%M:%S')
                if email_date > last_saved_dt:
                    email_data.append([date, sender, receiver, body])
        except HttpError as e:
            print(f"Error fetching email {msg_id}: {e}")

    return email_data

def sort_emails_by_date(email_data):
    """
    Sorts email data by the date in ascending order (oldest first).
    """
    return sorted(email_data, key=lambda x: datetime.strptime(x[0], '%m/%d/%Y %H:%M:%S'))

def fetch_and_sort_email_data(service, query_sent, query_inbox, last_saved_date):
    """
    Fetches sent and inbox emails, combines them, and sorts by date.
    Returns sorted email data.
    """
    # Fetch sent emails
    sent_messages = search_emails(service, query_sent)
    print(f"Found {len(sent_messages)} sent emails.")

    # Fetch inbox emails
    inbox_messages = search_emails(service, query_inbox)
    print(f"Found {len(inbox_messages)} inbox emails.")

    # Combine sent and inbox messages
    all_messages = sent_messages + inbox_messages

    if all_messages:
        # Fetch and filter email details
        email_data = batch_fetch_email_details(service, all_messages, last_saved_date)
        if email_data:
            return sort_emails_by_date(email_data)

    return []