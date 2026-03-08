"""
CloudWatch Integration Module for Code-Sarthi

Implements CloudWatch integration for:
- Sending logs to CloudWatch
- Emitting custom metrics
- Setting up alarms

Requirements: 10.3, 10.4
Task: 7.3 - Add CloudWatch Integration (Optional)

Note: This module requires AWS CloudWatch permissions and proper IAM role configuration.
"""

import boto3
import json
from datetime import datetime
from typing import Dict, List, Optional
import traceback


class CloudWatchIntegration:
    """CloudWatch integration for logging and metrics"""
    
    def __init__(self, 
                 log_group_name: str = "/code-sarthi/application",
                 log_stream_name: str = None,
                 region_name: str = "us-east-1"):
        """
        Initialize CloudWatch integration
        
        Args:
            log_group_name: CloudWatch log group name
            log_stream_name: CloudWatch log stream name (auto-generated if None)
            region_name: AWS region
        """
        self.log_group_name = log_group_name
        self.region_name = region_name
        
        # Generate log stream name if not provided
        if log_stream_name is None:
            self.log_stream_name = f"stream-{datetime.now().strftime('%Y%m%d-%H%M%S')}"
        else:
            self.log_stream_name = log_stream_name
        
        # Initialize AWS clients
        try:
            self.logs_client = boto3.client('logs', region_name=region_name)
            self.cloudwatch_client = boto3.client('cloudwatch', region_name=region_name)
            self.enabled = True
            self._ensure_log_group_exists()
            self._ensure_log_stream_exists()
        except Exception as e:
            print(f"CloudWatch initialization failed: {e}")
            print("CloudWatch integration will be disabled.")
            self.enabled = False
    
    def _ensure_log_group_exists(self):
        """Create log group if it doesn't exist"""
        if not self.enabled:
            return
        
        try:
            self.logs_client.create_log_group(logGroupName=self.log_group_name)
            print(f"Created CloudWatch log group: {self.log_group_name}")
        except self.logs_client.exceptions.ResourceAlreadyExistsException:
            pass  # Log group already exists
        except Exception as e:
            print(f"Error creating log group: {e}")
            self.enabled = False
    
    def _ensure_log_stream_exists(self):
        """Create log stream if it doesn't exist"""
        if not self.enabled:
            return
        
        try:
            self.logs_client.create_log_stream(
                logGroupName=self.log_group_name,
                logStreamName=self.log_stream_name
            )
            print(f"Created CloudWatch log stream: {self.log_stream_name}")
        except self.logs_client.exceptions.ResourceAlreadyExistsException:
            pass  # Log stream already exists
        except Exception as e:
            print(f"Error creating log stream: {e}")
            self.enabled = False
    
    def send_log(self, 
                 message: str, 
                 log_level: str = "INFO",
                 metadata: Optional[Dict] = None):
        """
        Send a log message to CloudWatch
        
        Args:
            message: Log message
            log_level: Log level (INFO, WARNING, ERROR)
            metadata: Additional metadata to include
        """
        if not self.enabled:
            return False
        
        try:
            # Prepare log entry
            log_entry = {
                'timestamp': datetime.now().isoformat(),
                'level': log_level,
                'message': message
            }
            
            if metadata:
                log_entry['metadata'] = metadata
            
            # Send to CloudWatch
            self.logs_client.put_log_events(
                logGroupName=self.log_group_name,
                logStreamName=self.log_stream_name,
                logEvents=[
                    {
                        'timestamp': int(datetime.now().timestamp() * 1000),
                        'message': json.dumps(log_entry)
                    }
                ]
            )
            
            return True
        except Exception as e:
            print(f"Error sending log to CloudWatch: {e}")
            return False
    
    def send_api_call_log(self,
                          service: str,
                          operation: str,
                          user_id: str,
                          status: str,
                          response_time_ms: Optional[float] = None):
        """
        Send API call log to CloudWatch
        
        Args:
            service: AWS service name
            operation: Operation performed
            user_id: User identifier
            status: Call status
            response_time_ms: Response time in milliseconds
        """
        metadata = {
            'service': service,
            'operation': operation,
            'user_id': user_id,
            'status': status,
            'response_time_ms': response_time_ms
        }
        
        message = f"API Call: {service}.{operation} - {status}"
        log_level = "INFO" if status == "success" else "ERROR"
        
        return self.send_log(message, log_level, metadata)
    
    def send_error_log(self,
                       error_type: str,
                       error_message: str,
                       user_id: str,
                       stack_trace: Optional[str] = None):
        """
        Send error log to CloudWatch
        
        Args:
            error_type: Type of error
            error_message: Error message
            user_id: User identifier
            stack_trace: Stack trace
        """
        metadata = {
            'error_type': error_type,
            'error_message': error_message,
            'user_id': user_id
        }
        
        if stack_trace:
            metadata['stack_trace'] = stack_trace
        
        message = f"Error: {error_type} - {error_message}"
        
        return self.send_log(message, "ERROR", metadata)
    
    def emit_metric(self,
                    metric_name: str,
                    value: float,
                    unit: str = "None",
                    dimensions: Optional[List[Dict]] = None):
        """
        Emit a custom metric to CloudWatch
        
        Args:
            metric_name: Name of the metric
            value: Metric value
            unit: Unit of measurement (Seconds, Milliseconds, Count, etc.)
            dimensions: Metric dimensions
        """
        if not self.enabled:
            return False
        
        try:
            metric_data = {
                'MetricName': metric_name,
                'Value': value,
                'Unit': unit,
                'Timestamp': datetime.now()
            }
            
            if dimensions:
                metric_data['Dimensions'] = dimensions
            
            self.cloudwatch_client.put_metric_data(
                Namespace='CodeSarthi',
                MetricData=[metric_data]
            )
            
            return True
        except Exception as e:
            print(f"Error emitting metric to CloudWatch: {e}")
            return False
    
    def emit_response_time_metric(self, operation: str, response_time_ms: float):
        """
        Emit response time metric
        
        Args:
            operation: Operation type
            response_time_ms: Response time in milliseconds
        """
        return self.emit_metric(
            metric_name='ResponseTime',
            value=response_time_ms,
            unit='Milliseconds',
            dimensions=[{'Name': 'Operation', 'Value': operation}]
        )
    
    def emit_error_rate_metric(self, error_count: int, total_requests: int):
        """
        Emit error rate metric
        
        Args:
            error_count: Number of errors
            total_requests: Total number of requests
        """
        error_rate = (error_count / total_requests * 100) if total_requests > 0 else 0
        
        return self.emit_metric(
            metric_name='ErrorRate',
            value=error_rate,
            unit='Percent'
        )
    
    def emit_api_usage_metric(self, service: str, call_count: int):
        """
        Emit API usage metric
        
        Args:
            service: AWS service name
            call_count: Number of API calls
        """
        return self.emit_metric(
            metric_name='APIUsage',
            value=call_count,
            unit='Count',
            dimensions=[{'Name': 'Service', 'Value': service}]
        )
    
    def create_error_rate_alarm(self,
                                alarm_name: str = "CodeSarthi-HighErrorRate",
                                threshold: float = 5.0,
                                evaluation_periods: int = 2,
                                sns_topic_arn: Optional[str] = None):
        """
        Create CloudWatch alarm for high error rate
        
        Args:
            alarm_name: Name of the alarm
            threshold: Error rate threshold (percentage)
            evaluation_periods: Number of periods to evaluate
            sns_topic_arn: SNS topic ARN for notifications
        """
        if not self.enabled:
            return False
        
        try:
            alarm_config = {
                'AlarmName': alarm_name,
                'ComparisonOperator': 'GreaterThanThreshold',
                'EvaluationPeriods': evaluation_periods,
                'MetricName': 'ErrorRate',
                'Namespace': 'CodeSarthi',
                'Period': 300,  # 5 minutes
                'Statistic': 'Average',
                'Threshold': threshold,
                'ActionsEnabled': True,
                'AlarmDescription': f'Triggers when error rate exceeds {threshold}%',
                'TreatMissingData': 'notBreaching'
            }
            
            if sns_topic_arn:
                alarm_config['AlarmActions'] = [sns_topic_arn]
            
            self.cloudwatch_client.put_metric_alarm(**alarm_config)
            
            print(f"Created CloudWatch alarm: {alarm_name}")
            return True
        except Exception as e:
            print(f"Error creating alarm: {e}")
            return False
    
    def create_response_time_alarm(self,
                                   alarm_name: str = "CodeSarthi-SlowResponseTime",
                                   threshold_ms: float = 5000.0,
                                   evaluation_periods: int = 2,
                                   sns_topic_arn: Optional[str] = None):
        """
        Create CloudWatch alarm for slow response times
        
        Args:
            alarm_name: Name of the alarm
            threshold_ms: Response time threshold in milliseconds
            evaluation_periods: Number of periods to evaluate
            sns_topic_arn: SNS topic ARN for notifications
        """
        if not self.enabled:
            return False
        
        try:
            alarm_config = {
                'AlarmName': alarm_name,
                'ComparisonOperator': 'GreaterThanThreshold',
                'EvaluationPeriods': evaluation_periods,
                'MetricName': 'ResponseTime',
                'Namespace': 'CodeSarthi',
                'Period': 300,  # 5 minutes
                'Statistic': 'Average',
                'Threshold': threshold_ms,
                'ActionsEnabled': True,
                'AlarmDescription': f'Triggers when average response time exceeds {threshold_ms}ms',
                'TreatMissingData': 'notBreaching'
            }
            
            if sns_topic_arn:
                alarm_config['AlarmActions'] = [sns_topic_arn]
            
            self.cloudwatch_client.put_metric_alarm(**alarm_config)
            
            print(f"Created CloudWatch alarm: {alarm_name}")
            return True
        except Exception as e:
            print(f"Error creating alarm: {e}")
            return False


# Global CloudWatch instance
_cloudwatch_instance = None


def get_cloudwatch() -> Optional[CloudWatchIntegration]:
    """Get or create global CloudWatch instance"""
    global _cloudwatch_instance
    if _cloudwatch_instance is None:
        try:
            _cloudwatch_instance = CloudWatchIntegration()
        except Exception as e:
            print(f"Failed to initialize CloudWatch: {e}")
            return None
    return _cloudwatch_instance if _cloudwatch_instance.enabled else None
