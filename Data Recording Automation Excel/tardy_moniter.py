#!/usr/bin/env python3
"""
eSchool Tardy Data Recording Automation
Desktop application for monitoring and recording student tardy data from eSchoolData API
"""

import requests
import json
import pandas as pd
from datetime import datetime, timedelta
import time
import os
import logging
from pathlib import Path
import threading
import queue
from typing import Dict, List, Optional
import sys

# Handle tkinter import for different Python versions and platforms
try:
    import tkinter as tk
    from tkinter import ttk, messagebox, scrolledtext
except ImportError:
    print("Error: tkinter is not available. Please ensure you have Python with tkinter support.")
    print("On macOS, tkinter should be included with Python. Try running with python3 instead of python.")
    sys.exit(1)

class ESchoolAPIClient:
    """Handles eSchoolData API authentication and requests"""
    
    def __init__(self, client_id: str, client_secret: str, base_url: str = "https://esdguruapi.eschooldata.com"):
        self.client_id = client_id
        self.client_secret = client_secret
        self.base_url = base_url
        self.access_token = None
        self.refresh_token = None
        self.token_expiry = None
        
    def authenticate(self) -> bool:
        """Authenticate with eSchoolData API using client credentials"""
        try:
            # Prepare authentication request
            auth_url = f"{self.base_url}/v1/auth/token"
            
            # Create basic auth header
            import base64
            credentials = f"{self.client_id}:{self.client_secret}"
            encoded_credentials = base64.b64encode(credentials.encode()).decode()
            
            headers = {
                "Authorization": f"Basic {encoded_credentials}",
                "Content-Type": "application/x-www-form-urlencoded"
            }
            
            data = {
                "grant_type": "client_credentials"
            }
            
            response = requests.post(auth_url, headers=headers, data=data, timeout=30)
            response.raise_for_status()
            
            token_data = response.json()
            self.access_token = token_data.get("access_token")
            self.refresh_token = token_data.get("refresh_token")
            
            # Calculate token expiry (subtract 5 minutes for safety)
            expires_in = token_data.get("expires_in", 3600)
            self.token_expiry = datetime.now() + timedelta(seconds=expires_in - 300)
            
            logging.info("Authentication successful")
            return True
            
        except Exception as e:
            logging.error(f"Authentication failed: {str(e)}")
            return False
    
    def refresh_access_token(self) -> bool:
        """Refresh the access token using refresh token"""
        if not self.refresh_token:
            return self.authenticate()
            
        try:
            auth_url = f"{self.base_url}/v1/auth/token"
            
            import base64
            credentials = f"{self.client_id}:{self.client_secret}"
            encoded_credentials = base64.b64encode(credentials.encode()).decode()
            
            headers = {
                "Authorization": f"Basic {encoded_credentials}",
                "Content-Type": "application/x-www-form-urlencoded"
            }
            
            data = {
                "grant_type": "refresh_token",
                "refresh_token": self.refresh_token
            }
            
            response = requests.post(auth_url, headers=headers, data=data, timeout=30)
            response.raise_for_status()
            
            token_data = response.json()
            self.access_token = token_data.get("access_token")
            if token_data.get("refresh_token"):
                self.refresh_token = token_data.get("refresh_token")
            
            expires_in = token_data.get("expires_in", 3600)
            self.token_expiry = datetime.now() + timedelta(seconds=expires_in - 300)
            
            logging.info("Token refreshed successfully")
            return True
            
        except Exception as e:
            logging.error(f"Token refresh failed: {str(e)}")
            return self.authenticate()
    
    def is_token_expired(self) -> bool:
        """Check if the access token is expired"""
        return self.token_expiry is None or datetime.now() >= self.token_expiry
    
    def ensure_valid_token(self) -> bool:
        """Ensure we have a valid access token"""
        if not self.access_token or self.is_token_expired():
            return self.refresh_access_token()
        return True
    
    def make_request(self, endpoint: str, params: Dict = None) -> Optional[Dict]:
        """Make authenticated API request with retry logic"""
        max_retries = 3
        retry_delay = 1
        
        for attempt in range(max_retries):
            try:
                if not self.ensure_valid_token():
                    logging.error("Failed to obtain valid token")
                    return None
                
                headers = {
                    "Authorization": f"Bearer {self.access_token}",
                    "Content-Type": "application/json"
                }
                
                url = f"{self.base_url}{endpoint}"
                response = requests.get(url, headers=headers, params=params, timeout=30)
                
                # Handle rate limiting
                if response.status_code == 429:
                    retry_after = int(response.headers.get('Retry-After', 60))
                    logging.warning(f"Rate limited. Waiting {retry_after} seconds")
                    time.sleep(retry_after)
                    continue
                
                response.raise_for_status()
                return response.json()
                
            except requests.exceptions.RequestException as e:
                logging.warning(f"Request attempt {attempt + 1} failed: {str(e)}")
                if attempt < max_retries - 1:
                    time.sleep(retry_delay * (2 ** attempt))  # Exponential backoff
                
        logging.error(f"All retry attempts failed for endpoint: {endpoint}")
        return None

class TardyDataManager:
    """Manages tardy data collection and Excel file operations"""
    
    def __init__(self, data_directory: str = "tardy_data"):
        self.data_directory = Path(data_directory)
        self.data_directory.mkdir(exist_ok=True)
        self.processed_records = set()
        
    def get_week_filename(self, date: datetime) -> str:
        """Generate filename for the week containing the given date"""
        # Find the Monday of the week
        monday = date - timedelta(days=date.weekday())
        friday = monday + timedelta(days=4)
        
        week_str = f"{monday.strftime('%Y%m%d')}_to_{friday.strftime('%Y%m%d')}"
        return f"tardy_records_{week_str}.xlsx"
    
    def get_current_week_file(self) -> Path:
        """Get the path to the current week's Excel file"""
        filename = self.get_week_filename(datetime.now())
        return self.data_directory / filename
    
    def initialize_excel_file(self, filepath: Path) -> None:
        """Initialize Excel file with headers if it doesn't exist"""
        if not filepath.exists():
            df = pd.DataFrame(columns=["Name", "ID Number", "Grade", "Timestamp", "Date"])
            df.to_excel(filepath, index=False)
            logging.info(f"Created new Excel file: {filepath}")
    
    def append_tardy_record(self, record: Dict) -> bool:
        """Append a single tardy record to the appropriate Excel file"""
        try:
            # Create record ID for deduplication
            record_id = f"{record['ID Number']}_{record['Timestamp']}"
            if record_id in self.processed_records:
                return False  # Already processed
            
            filepath = self.get_current_week_file()
            self.initialize_excel_file(filepath)
            
            # Read existing data
            try:
                df = pd.read_excel(filepath)
            except:
                df = pd.DataFrame(columns=["Name", "ID Number", "Grade", "Timestamp", "Date"])
            
            # Append new record
            new_row = pd.DataFrame([record])
            df = pd.concat([df, new_row], ignore_index=True)
            
            # Save to Excel
            df.to_excel(filepath, index=False)
            
            # Mark as processed
            self.processed_records.add(record_id)
            
            logging.info(f"Added tardy record: {record['Name']} at {record['Timestamp']}")
            return True
            
        except Exception as e:
            logging.error(f"Failed to append tardy record: {str(e)}")
            return False

class TardyMonitorApp:
    """Main desktop application for tardy monitoring"""
    
    def __init__(self):
        self.root = tk.Tk()
        self.root.title("eSchool Tardy Monitor")
        self.root.geometry("800x600")
        
        # Configuration
        self.config = {}
        self.api_client = None
        self.data_manager = TardyDataManager()
        self.monitoring = False
        self.monitor_thread = None
        self.status_queue = queue.Queue()
        
        # Setup logging
        self.setup_logging()
        
        # Create GUI
        self.create_widgets()
        
        # Start status update timer
        self.root.after(1000, self.update_status_display)
    
    def setup_logging(self):
        """Setup logging configuration"""
        log_format = '%(asctime)s - %(levelname)s - %(message)s'
        logging.basicConfig(
            level=logging.INFO,
            format=log_format,
            handlers=[
                logging.FileHandler('tardy_monitor.log'),
                logging.StreamHandler()
            ]
        )
    
    def create_widgets(self):
        """Create the main GUI widgets"""
        # Configuration Frame
        config_frame = ttk.LabelFrame(self.root, text="API Configuration", padding="10")
        config_frame.pack(fill="x", padx=10, pady=5)
        
        ttk.Label(config_frame, text="Client ID:").grid(row=0, column=0, sticky="w", padx=5)
        self.client_id_entry = ttk.Entry(config_frame, width=50)
        self.client_id_entry.grid(row=0, column=1, padx=5, pady=2)
        
        ttk.Label(config_frame, text="Client Secret:").grid(row=1, column=0, sticky="w", padx=5)
        self.client_secret_entry = ttk.Entry(config_frame, width=50, show="*")
        self.client_secret_entry.grid(row=1, column=1, padx=5, pady=2)
        
        ttk.Label(config_frame, text="Base URL:").grid(row=2, column=0, sticky="w", padx=5)
        self.base_url_entry = ttk.Entry(config_frame, width=50)
        self.base_url_entry.insert(0, "https://esdguruapi.eschooldata.com")
        self.base_url_entry.grid(row=2, column=1, padx=5, pady=2)
        
        # Control Frame
        control_frame = ttk.Frame(self.root)
        control_frame.pack(fill="x", padx=10, pady=5)
        
        self.connect_btn = ttk.Button(control_frame, text="Connect to API", command=self.connect_api)
        self.connect_btn.pack(side="left", padx=5)
        
        self.start_btn = ttk.Button(control_frame, text="Start Monitoring", command=self.start_monitoring, state="disabled")
        self.start_btn.pack(side="left", padx=5)
        
        self.stop_btn = ttk.Button(control_frame, text="Stop Monitoring", command=self.stop_monitoring, state="disabled")
        self.stop_btn.pack(side="left", padx=5)
        
        # Status Frame
        status_frame = ttk.LabelFrame(self.root, text="Status", padding="10")
        status_frame.pack(fill="x", padx=10, pady=5)
        
        self.status_label = ttk.Label(status_frame, text="Not connected")
        self.status_label.pack(anchor="w")
        
        self.records_label = ttk.Label(status_frame, text="Records processed: 0")
        self.records_label.pack(anchor="w")
        
        # Log Frame
        log_frame = ttk.LabelFrame(self.root, text="Activity Log", padding="10")
        log_frame.pack(fill="both", expand=True, padx=10, pady=5)
        
        self.log_text = scrolledtext.ScrolledText(log_frame, height=15)
        self.log_text.pack(fill="both", expand=True)
        
        # Recent Records Frame
        recent_frame = ttk.LabelFrame(self.root, text="Recent Tardy Records", padding="10")
        recent_frame.pack(fill="x", padx=10, pady=5)
        
        # Create treeview for recent records
        columns = ("Name", "ID", "Grade", "Time", "Date")
        self.recent_tree = ttk.Treeview(recent_frame, columns=columns, show="headings", height=6)
        
        for col in columns:
            self.recent_tree.heading(col, text=col)
            self.recent_tree.column(col, width=120)
        
        scrollbar = ttk.Scrollbar(recent_frame, orient="vertical", command=self.recent_tree.yview)
        self.recent_tree.configure(yscrollcommand=scrollbar.set)
        
        self.recent_tree.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")
    
    def log_message(self, message: str, level: str = "INFO"):
        """Add message to log display"""
        timestamp = datetime.now().strftime("%H:%M:%S")
        log_entry = f"[{timestamp}] {level}: {message}\n"
        
        self.log_text.insert(tk.END, log_entry)
        self.log_text.see(tk.END)
        
        # Keep only last 1000 lines
        lines = self.log_text.get("1.0", tk.END).split("\n")
        if len(lines) > 1000:
            self.log_text.delete("1.0", f"{len(lines) - 1000}.0")
    
    def connect_api(self):
        """Connect to the eSchool API"""
        client_id = self.client_id_entry.get().strip()
        client_secret = self.client_secret_entry.get().strip()
        base_url = self.base_url_entry.get().strip()
        
        if not client_id or not client_secret:
            messagebox.showerror("Error", "Please enter both Client ID and Client Secret")
            return
        
        self.log_message("Connecting to eSchool API...")
        self.api_client = ESchoolAPIClient(client_id, client_secret, base_url)
        
        if self.api_client.authenticate():
            self.status_label.config(text="Connected to API")
            self.start_btn.config(state="normal")
            self.connect_btn.config(text="Reconnect")
            self.log_message("Successfully connected to eSchool API")
        else:
            self.status_label.config(text="Connection failed")
            self.log_message("Failed to connect to eSchool API", "ERROR")
    
    def start_monitoring(self):
        """Start monitoring for new tardy records"""
        if not self.api_client:
            messagebox.showerror("Error", "Please connect to API first")
            return
        
        self.monitoring = True
        self.start_btn.config(state="disabled")
        self.stop_btn.config(state="normal")
        self.status_label.config(text="Monitoring active")
        
        self.monitor_thread = threading.Thread(target=self.monitor_tardies, daemon=True)
        self.monitor_thread.start()
        
        self.log_message("Started tardy monitoring")
    
    def stop_monitoring(self):
        """Stop monitoring for tardy records"""
        self.monitoring = False
        self.start_btn.config(state="normal")
        self.stop_btn.config(state="disabled")
        self.status_label.config(text="Monitoring stopped")
        
        self.log_message("Stopped tardy monitoring")
    
    def monitor_tardies(self):
        """Main monitoring loop - runs in separate thread"""
        last_check = datetime.now() - timedelta(minutes=5)  # Start with recent data
        records_processed = 0
        
        while self.monitoring:
            try:
                # Get recent daily attendance records (tardies are typically in daily attendance)
                current_time = datetime.now()
                
                # Format date for API query
                date_str = current_time.strftime("%Y-%m-%d")
                
                # Get daily attendance data
                params = {
                    "attendanceDate": date_str,
                    "$filter": f"lastModified gt {last_check.isoformat()}"
                }
                
                attendance_data = self.api_client.make_request("/v1/dailyAttendance", params)
                
                if attendance_data and "value" in attendance_data:
                    new_tardies = self.process_attendance_data(attendance_data["value"])
                    
                    for tardy in new_tardies:
                        if self.data_manager.append_tardy_record(tardy):
                            records_processed += 1
                            self.status_queue.put(("record", tardy))
                            self.status_queue.put(("count", records_processed))
                
                last_check = current_time
                
                # Wait before next check (adjust based on your needs)
                time.sleep(30)  # Check every 30 seconds
                
            except Exception as e:
                self.status_queue.put(("error", f"Monitoring error: {str(e)}"))
                time.sleep(60)  # Wait longer on error
    
    def process_attendance_data(self, attendance_records: List[Dict]) -> List[Dict]:
        """Process attendance data to extract tardy records"""
        tardies = []
        
        for record in attendance_records:
            # Check if this is a tardy record (you may need to adjust this logic based on your data structure)
            if record.get("attendanceCode") == "T" or "tardy" in str(record.get("attendanceReason", "")).lower():
                try:
                    # Get student information
                    student_id = record.get("studentId")
                    if student_id:
                        student_data = self.get_student_info(student_id)
                        if student_data:
                            tardy_record = {
                                "Name": student_data.get("name", "Unknown"),
                                "ID Number": student_data.get("localId", student_id),
                                "Grade": student_data.get("grade", "Unknown"),
                                "Timestamp": datetime.now().strftime("%H:%M:%S"),
                                "Date": datetime.now().strftime("%Y-%m-%d")
                            }
                            tardies.append(tardy_record)
                            
                except Exception as e:
                    logging.error(f"Error processing attendance record: {str(e)}")
        
        return tardies
    
    def get_student_info(self, student_id: str) -> Optional[Dict]:
        """Get student information by ID"""
        try:
            student_data = self.api_client.make_request(f"/v1/students/{student_id}")
            return student_data
        except Exception as e:
            logging.error(f"Error fetching student info for ID {student_id}: {str(e)}")
            return None
    
    def update_status_display(self):
        """Update GUI with status messages from queue"""
        try:
            while True:
                msg_type, data = self.status_queue.get_nowait()
                
                if msg_type == "record":
                    # Add to recent records display
                    self.recent_tree.insert("", 0, values=(
                        data["Name"],
                        data["ID Number"],
                        data["Grade"],
                        data["Timestamp"],
                        data["Date"]
                    ))
                    
                    # Keep only last 20 records
                    items = self.recent_tree.get_children()
                    if len(items) > 20:
                        self.recent_tree.delete(items[-1])
                    
                    self.log_message(f"New tardy recorded: {data['Name']} ({data['ID Number']})")
                
                elif msg_type == "count":
                    self.records_label.config(text=f"Records processed: {data}")
                
                elif msg_type == "error":
                    self.log_message(str(data), "ERROR")
                
        except queue.Empty:
            pass
        
        # Schedule next update
        self.root.after(1000, self.update_status_display)
    
    def run(self):
        """Start the application"""
        self.root.mainloop()

if __name__ == "__main__":
    app = TardyMonitorApp()
    app.run()