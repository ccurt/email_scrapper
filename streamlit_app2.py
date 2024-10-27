import streamlit as st
from auth import authenticate_gmail_and_sheets
from gmail_scraper import fetch_and_sort_email_data
from sheets_manager import get_last_saved_date, append_to_google_sheet_bulk, get_sheet_data, analyze_communication
from config import SHEET_NAME, SCOPES, email_accounts
from datetime import datetime
import time
import pandas as pd

def convert_to_epoch(date_string):
    """
    Converts a date string in '%m/%d/%Y %H:%M:%S' format to exact epoch time (in seconds).
    """
    try:
        dt = datetime.strptime(date_string, '%m/%d/%Y %H:%M:%S')
        epoch_time = int(time.mktime(dt.timetuple()))  # Return exact Unix time in seconds
        return epoch_time
    except ValueError as e:
        print(f"Error converting date to epoch: {e}")  # Send the log to terminal, not Streamlit
        return None

def display_communication_report(report):
    """
    Displays the communication report in a neat table format using Streamlit.
    """
    st.write("### Two-Way Communication Report")

    if not report:
        st.write("No communication data available.")
        return

    # Prepare data for the table
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

    # Convert the report data to a pandas DataFrame for better display
    report_df = pd.DataFrame(report_data)

    # Use st.table to display the DataFrame in a clean format
    st.table(report_df)

# Streamlit App Interface
st.title("ChatterTracker")

# Input for Google Sheet ID
sheet_id = st.text_input("Enter Google Sheet ID", value="", key="sheet_id")

if sheet_id:
    # Authenticate with Gmail and Google Sheets
    gmail_service, sheets_service = authenticate_gmail_and_sheets(SCOPES)

    # **Create a placeholder for the report**
    communication_placeholder = st.empty()  # The placeholder that will hold and update the report

    # **Get the data from the Google Sheet and display the initial report in the placeholder**
    sheet_data = get_sheet_data(sheets_service, sheet_id, SHEET_NAME)
    report = analyze_communication(sheet_data)

    # **Initial Report**: Display the existing communication report inside the placeholder
    communication_placeholder.empty()  # Clear the placeholder before using it
    with communication_placeholder.container():  # Using the placeholder to display the report
        display_communication_report(report)

    # Add button to scrape new emails
    if st.button("Start Scraping Emails"):
        # Get the last saved date from the Google Sheet
        last_saved_date = get_last_saved_date(sheets_service, sheet_id, SHEET_NAME)
        
        # Log the last saved date to the terminal
        print(f"Last saved date: {last_saved_date}")
        
        # Convert the last saved date to exact Unix epoch time
        since_epoch_time = convert_to_epoch(last_saved_date)
        
        if since_epoch_time:
            # Increment by 1 second to avoid fetching the last saved email again
            since_epoch_time += 1
            
            # Construct the Gmail queries for sent and inbox emails
            query_sent = f'from:me to:({" OR ".join(email_accounts)}) after:{since_epoch_time}'
            query_inbox = f'to:me from:({" OR ".join(email_accounts)}) after:{since_epoch_time}'

            # Fetch, filter, and sort emails
            sorted_email_data = fetch_and_sort_email_data(gmail_service, query_sent, query_inbox, last_saved_date)

            # Check if there are any new emails to save
            if sorted_email_data:
                # Append sorted emails to Google Sheet
                append_to_google_sheet_bulk(sheets_service, sheet_id, SHEET_NAME, sorted_email_data)
                st.write(f"Fetched and saved {len(sorted_email_data)} emails.")
            else:
                st.write("No new emails to save.")
        
        # After fetching new emails, regenerate the report
        sheet_data = get_sheet_data(sheets_service, sheet_id, SHEET_NAME)
        report = analyze_communication(sheet_data)
        
        # **Update the report in the same placeholder** after scraping
        communication_placeholder.empty()  # Clear the placeholder before updating
        with communication_placeholder.container():  # Use the same placeholder for update
            display_communication_report(report)