from googleapiclient.errors import HttpError
from datetime import datetime, timedelta
import re

def get_last_saved_date(sheets_service, sheet_id, sheet_name):
    """
    Fetch the last saved date from the Google Sheet, starting from row 2.
    If no data exists, return a default date (1 week ago).
    """
    try:
        result = sheets_service.spreadsheets().values().get(
            spreadsheetId=sheet_id,
            range=f'{sheet_name}!A2:A',  # Start from row 2
            majorDimension='COLUMNS'
        ).execute()

        values = result.get('values', [])
        if not values or not values[0]:
            print("No saved dates found. Defaulting to 1 week ago.")
            return (datetime.now() - timedelta(days=7)).strftime('%m/%m/%Y %H:%M:%S')

        last_date_str = values[0][-1]
        return last_date_str
    except HttpError as error:
        print(f"Error fetching the last saved date: {error}")
        return (datetime.now() - timedelta(days=7)).strftime('%m/%m/%Y  %H:%M:%S')

def append_to_google_sheet_bulk(sheets_service, sheet_id, sheet_name, email_data):
    """
    Append email data in bulk to the Google Sheet.
    """
    if not email_data:
        print("No email data to append.")
        return

    try:
        body = {'values': email_data}
        sheets_service.spreadsheets().values().append(
            spreadsheetId=sheet_id,
            range=sheet_name,
            valueInputOption="RAW",
            body=body
        ).execute()
        print(f"Successfully appended {len(email_data)} emails to Google Sheet.")
    except HttpError as error:
        print(f"Error appending to Google Sheet: {error}")
    except Exception as e:
        print(f"An unknown error occurred: {e}")

def get_sheet_data(sheets_service, sheet_id, sheet_name):
    """
    Fetches email data from the Google Sheet.
    """
    result = sheets_service.spreadsheets().values().get(
        spreadsheetId=sheet_id,
        range=f'{sheet_name}!A:D'  # Assuming columns are Date, From, To, Body
    ).execute()

    # Debugging output: show fetched data
    values = result.get('values', [])
    print(f"Fetched sheet data: {values}")
    
    return values


def extract_email(address):
    """
    Extracts email from a string of the form 'Name <email@example.com>'.
    If the string is already an email, returns it as-is.
    """
    match = re.search(r'[\w\.-]+@[\w\.-]+', address)
    return match.group(0) if match else address

def analyze_communication(sheet_data, teacher_email):
    """
    Analyzes two-way communication between teacher and students.
    """
    student_data = {}
    
    # Debugging output: check the raw sheet data
    print(f"Analyzing communication data: {sheet_data}")

    if not sheet_data or len(sheet_data) <= 1:  # No data or only header
        return {}

    for row in sheet_data[1:]:  # Skip the header row
        if len(row) < 3:
            continue  # Skip rows that don't have enough columns
        date, sender, receiver, body = row

        # Extract just the email addresses
        sender_email = extract_email(sender)
        receiver_email = extract_email(receiver)

        # Check if the email is from the teacher or from a student
        if teacher_email in sender_email:  # From teacher to student
            student_email = receiver_email
            if student_email not in student_data:
                student_data[student_email] = {"teacher_emails": 0, "student_emails": 0}
            student_data[student_email]["teacher_emails"] += 1

        elif teacher_email in receiver_email:  # From student to teacher
            student_email = sender_email
            if student_email not in student_data:
                student_data[student_email] = {"teacher_emails": 0, "student_emails": 0}
            student_data[student_email]["student_emails"] += 1

    # Debugging output: show processed student data
    print(f"Processed student data: {student_data}")

    # Add two-way communication flag (Y/N)
    for student_email, data in student_data.items():
        data["two_way"] = "Y" if data["teacher_emails"] > 0 and data["student_emails"] > 0 else "N"

    return student_data

def get_student_emails(sheets_service, sheet_id, sheet_name):
    """
    Fetches student email accounts from the specified sheet in the Google Sheet.
    Assumes the email addresses are in column A with a header in row 1.
    """
    try:
        result = sheets_service.spreadsheets().values().get(
            spreadsheetId=sheet_id,
            range=f'{sheet_name}!A2:A',  # Column A, starting from row 2 to skip the header
            majorDimension='COLUMNS'
        ).execute()

        values = result.get('values', [])
        if not values or not values[0]:
            print("No student emails found.")
            return []

        # Return the list of student emails
        student_emails = values[0]  # Already skipping the header by starting from row 2
        return student_emails
    except HttpError as error:
        print(f"Error fetching student emails: {error}")
        return []