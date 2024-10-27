import streamlit as st
from auth import authenticate_gmail_and_sheets
from gmail_scraper import fetch_and_sort_email_data
from sheets_manager import get_last_saved_date, append_to_google_sheet_bulk, get_sheet_data, analyze_communication, get_student_emails
from config import SCOPES
from datetime import datetime
import time
import pandas as pd

# Initialize all session state variables at the start
if 'submitted' not in st.session_state:
    st.session_state.submitted = False
if 'sheet_id' not in st.session_state:
    st.session_state.sheet_id = ""
if 'sheet_name' not in st.session_state:
    st.session_state.sheet_name = "Email Summary"
if 'student_email_sheet_name' not in st.session_state:
    st.session_state.student_email_sheet_name = "Student Info"
if 'teacher_email' not in st.session_state:
    st.session_state.teacher_email = ""

def convert_to_epoch(date_string):
    """
    Converts a date string in '%m/%d/%Y %H:%M:%S' format to exact epoch time (in seconds).
    """
    try:
        dt = datetime.strptime(date_string, '%m/%d/%Y %H:%M:%S')
        epoch_time = int(time.mktime(dt.timetuple()))
        return epoch_time
    except ValueError as e:
        print(f"Error converting date to epoch: {e}")
        return None

def display_communication_report(report):
    """
    Displays the communication report in a neat table format using Streamlit.
    """
    st.write("### Two-Way Communication Report")

    if not report:
        st.write("No communication data available.")
        return

    report_data = {
        "Student Email": [],
        "#Teacher Emails": [],
        "#Student Emails": [],
        "Two-Way Communication (Y/N)": []
    }

    for student_email, data in report.items():
        report_data["Student Email"].append(student_email)
        report_data["#Teacher Emails"].append(data["teacher_emails"])
        report_data["#Student Emails"].append(data["student_emails"])
        report_data["Two-Way Communication (Y/N)"].append(data["two_way"])

    report_df = pd.DataFrame(report_data)
    st.table(report_df)

def handle_form_submit():
    if all([st.session_state.sheet_id_input, 
            st.session_state.sheet_name_input,
            st.session_state.student_email_sheet_name_input,
            st.session_state.teacher_email_input]):
        st.session_state.sheet_id = st.session_state.sheet_id_input
        st.session_state.sheet_name = st.session_state.sheet_name_input
        st.session_state.student_email_sheet_name = st.session_state.student_email_sheet_name_input
        st.session_state.teacher_email = st.session_state.teacher_email_input
        st.session_state.submitted = True
    else:
        st.error("Please provide all inputs before submitting.")

# Streamlit App Interface
st.title("ChatterTracker")

# Input fields and submit button
if not st.session_state.submitted:
    with st.form("input_form"):
        # Input fields with keys for session state
        st.text_input("Enter Google Sheet ID", 
                     value=st.session_state.sheet_id,
                     key="sheet_id_input")
        
        st.text_input("Enter email summary Sheet Name",
                     value=st.session_state.sheet_name,
                     key="sheet_name_input")
        
        st.text_input("Enter student email Sheet Name",
                     value=st.session_state.student_email_sheet_name,
                     key="student_email_sheet_name_input")
        
        st.text_input("Enter Teacher Email",
                     value=st.session_state.teacher_email,
                     key="teacher_email_input")

        # Submit button
        submitted = st.form_submit_button("Submit", on_click=handle_form_submit)

# Proceed with the rest of the app if submitted
if st.session_state.submitted:
    # Authenticate with Gmail and Google Sheets
    gmail_service, sheets_service = authenticate_gmail_and_sheets(SCOPES)

    # Create a placeholder for the report
    communication_placeholder = st.empty()

    # Get the data and display initial report
    sheet_data = get_sheet_data(sheets_service, st.session_state.sheet_id, st.session_state.sheet_name)
    report = analyze_communication(sheet_data, teacher_email=st.session_state.teacher_email)

    # Get student email accounts
    student_email_accounts = get_student_emails(sheets_service, st.session_state.sheet_id, st.session_state.student_email_sheet_name)

    # Display initial report
    with communication_placeholder.container():
        display_communication_report(report)

    # Email scraping button
    if st.button("Start Scraping Emails"):
        last_saved_date = get_last_saved_date(sheets_service, st.session_state.sheet_id, st.session_state.sheet_name)
        print(f"Last saved date: {last_saved_date}")
        
        since_epoch_time = convert_to_epoch(last_saved_date)
        
        if since_epoch_time:
            since_epoch_time += 1
            
            query_sent = f'from:me to:({" OR ".join(student_email_accounts)}) after:{since_epoch_time}'
            query_inbox = f'to:me from:({" OR ".join(student_email_accounts)}) after:{since_epoch_time}'

            sorted_email_data = fetch_and_sort_email_data(gmail_service, query_sent, query_inbox, last_saved_date)

            if sorted_email_data:
                append_to_google_sheet_bulk(sheets_service, st.session_state.sheet_id, st.session_state.sheet_name, sorted_email_data)
                st.write(f"Fetched and saved {len(sorted_email_data)} emails.")
            else:
                st.write("No new emails to save.")
        
            # Update report after scraping
            sheet_data = get_sheet_data(sheets_service, st.session_state.sheet_id, st.session_state.sheet_name)
            report = analyze_communication(sheet_data, teacher_email=st.session_state.teacher_email)
            
            with communication_placeholder.container():
                display_communication_report(report)