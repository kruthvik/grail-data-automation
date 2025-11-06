from datetime import datetime as dt
import os

class Logger:
    def __init__(self, log_file=None, log_folder="./logs", date_format="%m/%d/%Y - %H:%M:%S", init=True):
        self.log_file = log_file
        self.date_format = date_format
        self.current_date = dt.now().strftime(self.date_format)
        self.log_entries = []
        self.log_folder = log_folder
        
        os.makedirs(self.log_folder, exist_ok=True)

        if log_file is None:
            self.log_file = dt.now().strftime("%Y%m%d_%H%M%S.log")
        
        self.file_path = f"{self.log_folder}/{self.log_file}" if self.log_file else None
        with open(self.file_path, "w", encoding="utf-8", errors='replace') as f:
            f.write("")  # Initialize/clear the log file
        
        if init:
            self.log("Logger initialized.", level="INFO")

    def send_log(self, message, level="INFO"):
        currentDate = dt.now().strftime(self.date_format)
        return f"{currentDate} - [{level}] - {message}"
    
    def log(self, message, level="INFO"):
        # Sanitize message to handle Unicode encoding issues
        if not isinstance(message, str):
            message = str(message)
        
        # Replace problematic characters before logging
        try:
            message = message.encode('utf-8', errors='replace').decode('utf-8')
        except Exception:
            # If encoding fails, replace problematic chars
            message = message.encode('ascii', errors='replace').decode('ascii')
        
        log_entry = self.send_log(message, level)
        self.log_entries.append(log_entry)

        with open(self.file_path, 'a', encoding="utf-8", errors='replace') as f:
            f.write(log_entry + "\n")