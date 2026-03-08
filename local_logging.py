"""
Local Logging Module for Code-Sarthi

Implements local logging functionality:
- Log all API calls with timestamps
- Log errors with stack traces
- Display recent logs in admin page
- Export logs to file

Requirements: 10.1, 10.2
Task: 7.2 - Add Local Logging
"""

import json
import os
import traceback
from datetime import datetime
from typing import Dict, List, Optional
from collections import deque


class LocalLogger:
    """Local logging system for Code-Sarthi"""
    
    def __init__(self, log_file: str = "code_sarthi_logs.json", max_memory_logs: int = 1000):
        """
        Initialize local logger
        
        Args:
            log_file: Path to JSON file for storing logs
            max_memory_logs: Maximum number of logs to keep in memory
        """
        self.log_file = log_file
        self.max_memory_logs = max_memory_logs
        
        # In-memory log buffer (for quick access)
        self.memory_logs = deque(maxlen=max_memory_logs)
        
        # Load existing logs
        self._load_logs()
    
    def _load_logs(self):
        """Load recent logs from file into memory"""
        if os.path.exists(self.log_file):
            try:
                with open(self.log_file, 'r') as f:
                    logs = json.load(f)
                    # Load last N logs into memory
                    recent_logs = logs[-self.max_memory_logs:] if len(logs) > self.max_memory_logs else logs
                    self.memory_logs.extend(recent_logs)
            except Exception as e:
                print(f"Error loading logs: {e}")
    
    def _save_log_to_file(self, log_entry: Dict):
        """Append a log entry to the log file"""
        try:
            # Load existing logs
            logs = []
            if os.path.exists(self.log_file):
                with open(self.log_file, 'r') as f:
                    logs = json.load(f)
            
            # Append new log
            logs.append(log_entry)
            
            # Keep only last 10000 logs in file to prevent unbounded growth
            if len(logs) > 10000:
                logs = logs[-10000:]
            
            # Save back to file
            with open(self.log_file, 'w') as f:
                json.dump(logs, f, indent=2)
            
            return True
        except Exception as e:
            print(f"Error saving log to file: {e}")
            return False
    
    def log_api_call(self, 
                     service: str, 
                     operation: str, 
                     user_id: str = "default_user",
                     status: str = "success",
                     response_time_ms: Optional[float] = None,
                     details: Optional[Dict] = None):
        """
        Log an API call
        
        Args:
            service: AWS service name (bedrock, s3, kendra, transcribe, polly)
            operation: Operation performed (translate, upload, retrieve, etc.)
            user_id: User identifier
            status: Call status (success, error, timeout)
            response_time_ms: Response time in milliseconds
            details: Additional details about the call
        """
        log_entry = {
            'timestamp': datetime.now().isoformat(),
            'log_type': 'api_call',
            'service': service,
            'operation': operation,
            'user_id': user_id,
            'status': status,
            'response_time_ms': response_time_ms,
            'details': details or {}
        }
        
        # Add to memory buffer
        self.memory_logs.append(log_entry)
        
        # Save to file
        self._save_log_to_file(log_entry)
        
        return log_entry
    
    def log_error(self,
                  error_type: str,
                  error_message: str,
                  user_id: str = "default_user",
                  context: Optional[Dict] = None,
                  include_traceback: bool = True):
        """
        Log an error with stack trace
        
        Args:
            error_type: Type of error (e.g., "ValueError", "APIError")
            error_message: Error message
            user_id: User identifier
            context: Additional context about where error occurred
            include_traceback: Whether to include full stack trace
        """
        log_entry = {
            'timestamp': datetime.now().isoformat(),
            'log_type': 'error',
            'error_type': error_type,
            'error_message': error_message,
            'user_id': user_id,
            'context': context or {}
        }
        
        # Add stack trace if requested
        if include_traceback:
            log_entry['stack_trace'] = traceback.format_exc()
        
        # Add to memory buffer
        self.memory_logs.append(log_entry)
        
        # Save to file
        self._save_log_to_file(log_entry)
        
        return log_entry
    
    def log_event(self,
                  event_type: str,
                  event_name: str,
                  user_id: str = "default_user",
                  details: Optional[Dict] = None):
        """
        Log a general event
        
        Args:
            event_type: Type of event (session_start, feature_used, etc.)
            event_name: Name of the event
            user_id: User identifier
            details: Additional event details
        """
        log_entry = {
            'timestamp': datetime.now().isoformat(),
            'log_type': 'event',
            'event_type': event_type,
            'event_name': event_name,
            'user_id': user_id,
            'details': details or {}
        }
        
        # Add to memory buffer
        self.memory_logs.append(log_entry)
        
        # Save to file
        self._save_log_to_file(log_entry)
        
        return log_entry
    
    def get_recent_logs(self, count: int = 100, log_type: Optional[str] = None) -> List[Dict]:
        """
        Get recent logs from memory
        
        Args:
            count: Number of logs to return
            log_type: Filter by log type (api_call, error, event)
            
        Returns:
            List of log entries
        """
        logs = list(self.memory_logs)
        
        # Filter by type if specified
        if log_type:
            logs = [log for log in logs if log.get('log_type') == log_type]
        
        # Return most recent N logs
        return logs[-count:] if len(logs) > count else logs
    
    def get_error_logs(self, count: int = 50) -> List[Dict]:
        """Get recent error logs"""
        return self.get_recent_logs(count=count, log_type='error')
    
    def get_api_call_logs(self, count: int = 100, service: Optional[str] = None) -> List[Dict]:
        """
        Get recent API call logs
        
        Args:
            count: Number of logs to return
            service: Filter by service name
            
        Returns:
            List of API call log entries
        """
        logs = self.get_recent_logs(count=count, log_type='api_call')
        
        # Filter by service if specified
        if service:
            logs = [log for log in logs if log.get('service') == service]
        
        return logs
    
    def export_logs(self, 
                    output_file: str, 
                    log_type: Optional[str] = None,
                    start_date: Optional[str] = None,
                    end_date: Optional[str] = None) -> bool:
        """
        Export logs to a file
        
        Args:
            output_file: Path to output file
            log_type: Filter by log type
            start_date: Start date (ISO format)
            end_date: End date (ISO format)
            
        Returns:
            True if export successful, False otherwise
        """
        try:
            # Load all logs from file
            logs = []
            if os.path.exists(self.log_file):
                with open(self.log_file, 'r') as f:
                    logs = json.load(f)
            
            # Apply filters
            filtered_logs = logs
            
            if log_type:
                filtered_logs = [log for log in filtered_logs if log.get('log_type') == log_type]
            
            if start_date:
                filtered_logs = [log for log in filtered_logs if log.get('timestamp', '') >= start_date]
            
            if end_date:
                filtered_logs = [log for log in filtered_logs if log.get('timestamp', '') <= end_date]
            
            # Export to file
            with open(output_file, 'w') as f:
                json.dump(filtered_logs, f, indent=2)
            
            return True
        except Exception as e:
            print(f"Error exporting logs: {e}")
            return False
    
    def get_log_statistics(self) -> Dict:
        """
        Get statistics about logs
        
        Returns:
            Dictionary with log statistics
        """
        logs = list(self.memory_logs)
        
        stats = {
            'total_logs': len(logs),
            'by_type': {},
            'by_service': {},
            'error_count': 0,
            'api_call_count': 0,
            'event_count': 0
        }
        
        # Count by type
        for log in logs:
            log_type = log.get('log_type', 'unknown')
            stats['by_type'][log_type] = stats['by_type'].get(log_type, 0) + 1
            
            if log_type == 'error':
                stats['error_count'] += 1
            elif log_type == 'api_call':
                stats['api_call_count'] += 1
                service = log.get('service', 'unknown')
                stats['by_service'][service] = stats['by_service'].get(service, 0) + 1
            elif log_type == 'event':
                stats['event_count'] += 1
        
        return stats
    
    def clear_logs(self):
        """Clear all logs from memory and file"""
        self.memory_logs.clear()
        
        try:
            if os.path.exists(self.log_file):
                os.remove(self.log_file)
            return True
        except Exception as e:
            print(f"Error clearing logs: {e}")
            return False


# Global logger instance
_logger_instance = None


def get_logger() -> LocalLogger:
    """Get or create global logger instance"""
    global _logger_instance
    if _logger_instance is None:
        _logger_instance = LocalLogger()
    return _logger_instance
