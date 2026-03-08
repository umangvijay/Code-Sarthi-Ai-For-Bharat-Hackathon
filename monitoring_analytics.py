"""
Monitoring and Analytics Module for Code-Sarthi

Tracks usage analytics including:
- Translation counts
- API calls by service (Bedrock, S3, Kendra, Transcribe, Polly)
- Response time metrics
- Error tracking

Requirements: 10.3
Task: 7.1 - Implement Usage Analytics
"""

import json
import os
from datetime import datetime
from typing import Dict, List, Optional
from collections import defaultdict
import time


class UsageAnalytics:
    """Track and manage usage analytics for Code-Sarthi"""
    
    def __init__(self, analytics_file: str = "analytics_data.json"):
        """
        Initialize analytics tracker
        
        Args:
            analytics_file: Path to JSON file for storing analytics data
        """
        self.analytics_file = analytics_file
        self.analytics_data = self._load_analytics()
        
        # In-memory counters for current session
        self.session_start = datetime.now().isoformat()
        self.session_counters = {
            'translations': 0,
            'code_explanations': 0,
            'pdf_uploads': 0,
            'viva_sessions': 0,
            'error_analyses': 0
        }
        
        # API call tracking by service
        self.api_calls = defaultdict(int)
        
        # Response time tracking
        self.response_times = defaultdict(list)
    
    def _load_analytics(self) -> Dict:
        """Load analytics data from JSON file"""
        if os.path.exists(self.analytics_file):
            try:
                with open(self.analytics_file, 'r') as f:
                    return json.load(f)
            except Exception as e:
                print(f"Error loading analytics: {e}")
                return self._initialize_analytics_structure()
        else:
            return self._initialize_analytics_structure()
    
    def _initialize_analytics_structure(self) -> Dict:
        """Initialize empty analytics data structure"""
        return {
            'total_translations': 0,
            'total_code_explanations': 0,
            'total_pdf_uploads': 0,
            'total_viva_sessions': 0,
            'total_error_analyses': 0,
            'api_calls_by_service': {
                'bedrock': 0,
                's3': 0,
                'kendra': 0,
                'transcribe': 0,
                'polly': 0
            },
            'response_times': {
                'translation': [],
                'code_explanation': [],
                'pdf_upload': [],
                'viva_question': [],
                'error_analysis': []
            },
            'sessions': [],
            'last_updated': datetime.now().isoformat()
        }
    
    def save_analytics(self):
        """Save analytics data to JSON file"""
        try:
            # Update totals from session counters
            self.analytics_data['total_translations'] += self.session_counters['translations']
            self.analytics_data['total_code_explanations'] += self.session_counters['code_explanations']
            self.analytics_data['total_pdf_uploads'] += self.session_counters['pdf_uploads']
            self.analytics_data['total_viva_sessions'] += self.session_counters['viva_sessions']
            self.analytics_data['total_error_analyses'] += self.session_counters['error_analyses']
            
            # Update API calls
            for service, count in self.api_calls.items():
                if service in self.analytics_data['api_calls_by_service']:
                    self.analytics_data['api_calls_by_service'][service] += count
            
            # Update response times (keep last 100 for each type)
            for operation, times in self.response_times.items():
                if operation in self.analytics_data['response_times']:
                    self.analytics_data['response_times'][operation].extend(times)
                    # Keep only last 100 measurements
                    self.analytics_data['response_times'][operation] = \
                        self.analytics_data['response_times'][operation][-100:]
            
            # Add session summary
            session_summary = {
                'start_time': self.session_start,
                'end_time': datetime.now().isoformat(),
                'counters': self.session_counters.copy(),
                'api_calls': dict(self.api_calls)
            }
            self.analytics_data['sessions'].append(session_summary)
            
            # Keep only last 50 sessions
            self.analytics_data['sessions'] = self.analytics_data['sessions'][-50:]
            
            # Update timestamp
            self.analytics_data['last_updated'] = datetime.now().isoformat()
            
            # Write to file
            with open(self.analytics_file, 'w') as f:
                json.dump(self.analytics_data, f, indent=2)
            
            return True
        except Exception as e:
            print(f"Error saving analytics: {e}")
            return False
    
    def track_translation(self):
        """Track a translation operation"""
        self.session_counters['translations'] += 1
    
    def track_code_explanation(self):
        """Track a code explanation operation"""
        self.session_counters['code_explanations'] += 1
    
    def track_pdf_upload(self):
        """Track a PDF upload operation"""
        self.session_counters['pdf_uploads'] += 1
    
    def track_viva_session(self):
        """Track a viva session"""
        self.session_counters['viva_sessions'] += 1
    
    def track_error_analysis(self):
        """Track an error analysis operation"""
        self.session_counters['error_analyses'] += 1
    
    def track_api_call(self, service: str):
        """
        Track an API call to an AWS service
        
        Args:
            service: Service name (bedrock, s3, kendra, transcribe, polly)
        """
        service = service.lower()
        if service in ['bedrock', 's3', 'kendra', 'transcribe', 'polly']:
            self.api_calls[service] += 1
    
    def track_response_time(self, operation: str, response_time_ms: float):
        """
        Track response time for an operation
        
        Args:
            operation: Operation type (translation, code_explanation, etc.)
            response_time_ms: Response time in milliseconds
        """
        if operation in ['translation', 'code_explanation', 'pdf_upload', 
                        'viva_question', 'error_analysis']:
            self.response_times[operation].append(response_time_ms)
    
    def get_statistics(self) -> Dict:
        """
        Get current statistics including session and total counts
        
        Returns:
            Dictionary with all statistics
        """
        stats = {
            'session': {
                'start_time': self.session_start,
                'duration_minutes': (datetime.now() - datetime.fromisoformat(self.session_start)).total_seconds() / 60,
                'counters': self.session_counters.copy(),
                'api_calls': dict(self.api_calls)
            },
            'total': {
                'translations': self.analytics_data['total_translations'] + self.session_counters['translations'],
                'code_explanations': self.analytics_data['total_code_explanations'] + self.session_counters['code_explanations'],
                'pdf_uploads': self.analytics_data['total_pdf_uploads'] + self.session_counters['pdf_uploads'],
                'viva_sessions': self.analytics_data['total_viva_sessions'] + self.session_counters['viva_sessions'],
                'error_analyses': self.analytics_data['total_error_analyses'] + self.session_counters['error_analyses']
            },
            'api_calls_total': self.analytics_data['api_calls_by_service'].copy()
        }
        
        # Add current session API calls to totals
        for service, count in self.api_calls.items():
            if service in stats['api_calls_total']:
                stats['api_calls_total'][service] += count
        
        # Calculate average response times
        stats['avg_response_times'] = {}
        for operation, times in self.analytics_data['response_times'].items():
            if times:
                stats['avg_response_times'][operation] = sum(times) / len(times)
            else:
                stats['avg_response_times'][operation] = 0
        
        return stats
    
    def get_response_time_stats(self, operation: str) -> Dict:
        """
        Get detailed response time statistics for an operation
        
        Args:
            operation: Operation type
            
        Returns:
            Dictionary with min, max, avg, median response times
        """
        times = self.analytics_data['response_times'].get(operation, [])
        
        if not times:
            return {
                'count': 0,
                'min': 0,
                'max': 0,
                'avg': 0,
                'median': 0
            }
        
        sorted_times = sorted(times)
        count = len(sorted_times)
        
        return {
            'count': count,
            'min': sorted_times[0],
            'max': sorted_times[-1],
            'avg': sum(sorted_times) / count,
            'median': sorted_times[count // 2]
        }


class ResponseTimeTracker:
    """Context manager for tracking response times"""
    
    def __init__(self, analytics: UsageAnalytics, operation: str):
        """
        Initialize response time tracker
        
        Args:
            analytics: UsageAnalytics instance
            operation: Operation type to track
        """
        self.analytics = analytics
        self.operation = operation
        self.start_time = None
    
    def __enter__(self):
        """Start timing"""
        self.start_time = time.time()
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Stop timing and record"""
        if self.start_time:
            elapsed_ms = (time.time() - self.start_time) * 1000
            self.analytics.track_response_time(self.operation, elapsed_ms)
        return False


# Global analytics instance
_analytics_instance = None


def get_analytics() -> UsageAnalytics:
    """Get or create global analytics instance"""
    global _analytics_instance
    if _analytics_instance is None:
        _analytics_instance = UsageAnalytics()
    return _analytics_instance
