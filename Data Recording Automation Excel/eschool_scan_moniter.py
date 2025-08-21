
##*********** pip install requests pandas openpyxl ##*********

import requests
import pandas as pd
from datetime import datetime, timedelta
import time
import os
from openpyxl import load_workbook
import json

CLIENT_ID = "your_client_id"
CLIENT_SECRET = "your_client_secret"
REFRESH_TOKEN = "your_refresh_token"
TOKEN_URL = "https://your-esd-domain.org/oauth/token"
API_BASE_URL = "https://your-esd-domain.org/api/v1"
EXCEL_FILE_PATH = "C:/AttendanceLogs/student_scans.xlsx"
POLLING_INTERVAL = 30  

LAST_CHECK_FILE = "C:/AttendanceLogs/last_check.txt"

def get_access_token():
    """Get a new access token using refresh token"""
    payload = {
        'client_id': CLIENT_ID,
        'client_secret': CLIENT_SECRET,
        'refresh_token': REFRESH_TOKEN,
        'grant_type': 'refresh_token'
    }
    response = requests.post(TOKEN_URL, data=payload)
    response.raise_for_status()
    return response.json()['access_token']

def get_last_check_time():
    # Get the timestamp of the last check from file
    try:
        with open(LAST_CHECK_FILE, 'r') as f:
            return datetime.fromisoformat(f.read().strip())
    except (FileNotFoundError, ValueError):
        # If file does not exist or there is an issue, it returns time -1000 hour ago (Abbi)
        return datetime.now() - timedelta(hours=-1000)

def save_last_check_time():
    # This function saves the current time as the last check time (Abbi)
    with open(LAST_CHECK_FILE, 'w') as f:
        f.write(datetime.now().isoformat())

def get_recent_attendance(access_token, last_check_time):
    # Get attendance records since the last check
    headers = {'Authorization': f'Bearer {access_token}'}
    
    # ************Format time for API query - adjust based on API requirements
    since_time = last_check_time.strftime("%Y-%m-%dT%H:%M:%S")
    
    # Try to get period attendance (most likely to contain scan data)
    try:
        # Check the API documentation for required ENDPOINT parameters (Abbi)
        response = requests.get(
            f"{API_BASE_URL}/periodAttendance",
            headers=headers,
            params={'modifiedSince': since_time}  # Adjust based on actual API parameters
        )
        response.raise_for_status()
        return response.json()
    except requests.exceptions.HTTPError as e:
        print(f"Error fetching period attendance: {e}")
        
        # Fallback to daily attendance if period attendance fails
        try:
            response = requests.get(
                f"{API_BASE_URL}/dailyAttendance",
                headers=headers,
                params={'modifiedSince': since_time}
            )
            response.raise_for_status()
            return response.json()
        except requests.exceptions.HTTPError as e2:
            print(f"Error fetching daily attendance: {e2}")
            return []

def get_student_details(access_token, student_id):
    # This function is getting ALL the data of THE STUDENT!! (Abbi)
    headers = {'Authorization': f'Bearer {access_token}'}
    try:
        response = requests.get(
            f"{API_BASE_URL}/students/{student_id}",
            headers=headers
        )
        response.raise_for_status()
        return response.json()
    except requests.exceptions.HTTPError as e:
        print(f"Error fetching student details for {student_id}: {e}")
        return None

def update_excel(scan_data):
    """Update Excel file with new scan data"""
    # Create file with headers if it doesn't exist
    if not os.path.exists(EXCEL_FILE_PATH):
        df = pd.DataFrame(columns=[
            'Student ID', 'Student Name', 'Scan Time', 
            'Class', 'Attendance Type', 'Reason', 'Status'
        ])
        df.to_excel(EXCEL_FILE_PATH, index=False)
    
    # Load existing data
    existing_df = pd.read_excel(EXCEL_FILE_PATH)
    
    # Convert new data to DataFrame and append
    new_df = pd.DataFrame(scan_data)
    updated_df = pd.concat([existing_df, new_df], ignore_index=True)
    
    # Save updated data
    updated_df.to_excel(EXCEL_FILE_PATH, index=False)
    print(f"Updated Excel with {len(scan_data)} new records")

def main():
    print("Starting eSchoolData Scan Monitor...")
    
    while True:
        try:
            # Get access token
            access_token = get_access_token()
            
            # Get time of last check
            last_check_time = get_last_check_time()
            print(f"Checking for scans since: {last_check_time}")
            
            # Get recent attendance records
            attendance_data = get_recent_attendance(access_token, last_check_time)
            
            if attendance_data:
                print(f"Found {len(attendance_data)} new attendance records")
                
                # Process each record to get full details
                scan_records = []
                for record in attendance_data:
                    # Extract basic info from attendance record
                    student_id = record.get('studentId')
                    scan_time = record.get('date') or record.get('createDate')
                    status = record.get('status')
                    reason = record.get('reason')
                    
                    # Get student details
                    student_info = get_student_details(access_token, student_id)
                    if student_info:
                        student_name = f"{student_info.get('firstName', '')} {student_info.get('lastName', '')}".strip()
                        
                        # Create scan record
                        scan_record = {
                            'Student ID': student_id,
                            'Student Name': student_name,
                            'Scan Time': scan_time,
                            'Class': record.get('Class', 'Unknown'),
                            'Attendance Type': record.get('attendanceType', 'Period'),
                            'Reason': reason,
                            'Status': status
                        }
                        scan_records.append(scan_record)
                
                # Update Excel if we have new records
                if scan_records:
                    update_excel(scan_records)
            
            # Update last check time and wait for next interval
            save_last_check_time()
            time.sleep(POLLING_INTERVAL)
            
        except Exception as e:
            print(f"Error in main loop: {e}")
            time.sleep(POLLING_INTERVAL)  # Wait before retrying

if __name__ == "__main__":
    main()