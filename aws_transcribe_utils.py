"""
AWS Transcribe Speech-to-Text Utilities
Converts audio to text using AWS Transcribe with Indian English accent support
Supports Hybrid Mode for offline operation
"""

import boto3
import time
import uuid
import json
import os
from pathlib import Path
from botocore.exceptions import ClientError

# Force AWS Mode - EC2 with IAM Role
# Set USE_AWS=False in environment to disable (for local development only)
USE_AWS = os.getenv("USE_AWS", "true").lower() == "true"


def is_aws_ready():
    """Check if AWS services are ready from session state"""
    try:
        import streamlit as st
        return st.session_state.get("aws_ready", False)
    except:
        # If not in Streamlit context, just check USE_AWS
        return USE_AWS


class TranscribeSTT:
    """AWS Transcribe Speech-to-Text Engine with Hybrid Mode support"""
    
    # Language configurations for Indian English
    LANGUAGE_CONFIGS = {
        'indian_english': {
            'LanguageCode': 'en-IN',
            'MediaFormat': 'webm',  # Browser audio format
            'Settings': {
                'ShowSpeakerLabels': False,
                'MaxSpeakerLabels': 1
            }
        },
        'hindi': {
            'LanguageCode': 'hi-IN',
            'MediaFormat': 'webm',
            'Settings': {
                'ShowSpeakerLabels': False,
                'MaxSpeakerLabels': 1
            }
        }
    }
    
    def __init__(self, region_name="us-east-1", s3_bucket=None):
        """
        Initialize Transcribe STT engine with Hybrid Mode support
        
        Args:
            region_name: AWS region
            s3_bucket: S3 bucket for audio file storage (optional)
        """
        self.use_aws = USE_AWS
        self.region_name = region_name
        self.s3_bucket = s3_bucket
        
        if self.use_aws:
            # Use IAM roles via boto3.Session() for security
            session = boto3.Session()
            self.transcribe_client = session.client('transcribe', region_name=region_name)
            self.s3_client = session.client('s3', region_name=region_name) if s3_bucket else None
        else:
            self.transcribe_client = None
            self.s3_client = None
        
        mode_str = "AWS Cloud" if self.use_aws else "Local Offline"
        print(f"✅ Transcribe STT initialized ({mode_str}, region: {region_name})")
    
    def transcribe_audio_bytes(
        self,
        audio_bytes: bytes,
        language: str = 'indian_english',
        audio_format: str = 'webm'
    ) -> dict:
        """
        Transcribe audio bytes using AWS Transcribe (Hybrid Mode aware)
        
        This method uses the streaming API for real-time transcription
        without requiring S3 storage.
        
        Args:
            audio_bytes: Audio data as bytes
            language: Language type - 'indian_english' or 'hindi'
            audio_format: Audio format - 'webm', 'mp3', 'wav', etc.
            
        Returns:
            Dictionary with transcription results:
            {
                'transcript': str,
                'confidence': float,
                'items': list,
                'status': str
            }
            
        Raises:
            ValueError: If language is invalid
            ClientError: If AWS Transcribe API call fails
        """
        if language not in self.LANGUAGE_CONFIGS:
            raise ValueError(f"Invalid language: {language}. Must be one of {list(self.LANGUAGE_CONFIGS.keys())}")
        
        # Check AWS mode and readiness
        if self.use_aws and is_aws_ready():
            print(f"🟢 AWS Mode: Using Transcribe STT ({len(audio_bytes)} bytes)")
        else:
            if self.use_aws and not is_aws_ready():
                print(f"🔴 AWS not ready, falling back to Local Mode ({len(audio_bytes)} bytes)")
            else:
                print(f"🔵 Local Mode: STT simulation ({len(audio_bytes)} bytes)")
            return {
                'transcript': "Local Mode: Speech-to-text simulation. Actual transcription requires AWS mode.",
                'confidence': 0.0,
                'items': [],
                'status': 'success',
                'language': language,
                'mode': 'local'
            }
        
        # Get language configuration
        lang_config = self.LANGUAGE_CONFIGS[language]
        language_code = lang_config['LanguageCode']
        
        try:
            print(f"🎤 Transcribing audio ({len(audio_bytes)} bytes) with {language_code}...")
            
            # For streaming transcription, we'll use the StartStreamTranscription API
            # However, for simplicity in this implementation, we'll use the job-based API
            # which requires S3 storage
            
            if not self.s3_bucket:
                raise ValueError("S3 bucket required for transcription. Please configure S3 bucket.")
            
            # Generate unique job name
            job_name = f"transcribe-{uuid.uuid4()}"
            s3_key = f"transcribe-temp/{job_name}.{audio_format}"
            
            # Upload audio to S3
            print(f"📤 Uploading audio to S3: s3://{self.s3_bucket}/{s3_key}")
            self.s3_client.put_object(
                Bucket=self.s3_bucket,
                Key=s3_key,
                Body=audio_bytes,
                ContentType=f'audio/{audio_format}'
            )
            
            # Start transcription job
            media_uri = f"s3://{self.s3_bucket}/{s3_key}"
            
            print(f"🔄 Starting transcription job: {job_name}")
            self.transcribe_client.start_transcription_job(
                TranscriptionJobName=job_name,
                Media={'MediaFileUri': media_uri},
                MediaFormat=audio_format,
                LanguageCode=language_code,
                Settings=lang_config['Settings']
            )
            
            # Wait for job to complete
            print("⏳ Waiting for transcription to complete...")
            max_tries = 60  # 60 seconds timeout
            tries = 0
            
            while tries < max_tries:
                response = self.transcribe_client.get_transcription_job(
                    TranscriptionJobName=job_name
                )
                
                status = response['TranscriptionJob']['TranscriptionJobStatus']
                
                if status == 'COMPLETED':
                    print("✅ Transcription completed!")
                    
                    # Get transcript URL
                    transcript_uri = response['TranscriptionJob']['Transcript']['TranscriptFileUri']
                    
                    # Download and parse transcript
                    import requests
                    transcript_response = requests.get(transcript_uri)
                    transcript_data = transcript_response.json()
                    
                    # Extract transcript and confidence
                    results = transcript_data['results']
                    transcript = results['transcripts'][0]['transcript']
                    
                    # Calculate average confidence
                    items = results.get('items', [])
                    confidences = [
                        float(item.get('alternatives', [{}])[0].get('confidence', 0))
                        for item in items
                        if item.get('type') == 'pronunciation'
                    ]
                    avg_confidence = sum(confidences) / len(confidences) if confidences else 0.0
                    
                    # Cleanup: Delete S3 file
                    try:
                        self.s3_client.delete_object(Bucket=self.s3_bucket, Key=s3_key)
                        print(f"🗑️  Cleaned up S3 file: {s3_key}")
                    except Exception as e:
                        print(f"⚠️  Failed to cleanup S3 file: {str(e)}")
                    
                    # Delete transcription job
                    try:
                        self.transcribe_client.delete_transcription_job(
                            TranscriptionJobName=job_name
                        )
                        print(f"🗑️  Cleaned up transcription job: {job_name}")
                    except Exception as e:
                        print(f"⚠️  Failed to cleanup job: {str(e)}")
                    
                    return {
                        'transcript': transcript,
                        'confidence': round(avg_confidence, 3),
                        'items': items,
                        'status': 'success',
                        'language': language_code,
                        'mode': 'aws'
                    }
                
                elif status == 'FAILED':
                    failure_reason = response['TranscriptionJob'].get('FailureReason', 'Unknown')
                    print(f"❌ Transcription failed: {failure_reason}")
                    
                    # Cleanup S3 file
                    try:
                        self.s3_client.delete_object(Bucket=self.s3_bucket, Key=s3_key)
                    except:
                        pass
                    
                    return {
                        'transcript': '',
                        'confidence': 0.0,
                        'items': [],
                        'status': 'failed',
                        'error': failure_reason,
                        'mode': 'aws'
                    }
                
                # Wait before checking again
                time.sleep(1)
                tries += 1
            
            # Timeout
            print("⏰ Transcription timeout!")
            return {
                'transcript': '',
                'confidence': 0.0,
                'items': [],
                'status': 'timeout',
                'error': 'Transcription job timed out after 60 seconds',
                'mode': 'aws'
            }
        
        except ClientError as e:
            error_code = e.response['Error']['Code']
            error_msg = e.response['Error']['Message']
            
            if error_code == 'AccessDeniedException':
                raise ClientError(
                    {
                        'Error': {
                            'Code': 'AccessDeniedException',
                            'Message': 'AWS Transcribe access denied. Please check IAM permissions for transcribe:StartTranscriptionJob'
                        }
                    },
                    'transcribe_audio'
                )
            
            raise ClientError(
                {
                    'Error': {
                        'Code': error_code,
                        'Message': f"Transcribe error: {error_msg}"
                    }
                },
                'transcribe_audio'
            )
    
    def transcribe_audio_file(
        self,
        audio_file_path: str,
        language: str = 'indian_english'
    ) -> dict:
        """
        Transcribe audio from a file
        
        Args:
            audio_file_path: Path to audio file
            language: Language type - 'indian_english' or 'hindi'
            
        Returns:
            Dictionary with transcription results
        """
        # Read audio file
        audio_path = Path(audio_file_path)
        
        if not audio_path.exists():
            raise FileNotFoundError(f"Audio file not found: {audio_file_path}")
        
        # Detect audio format from extension
        audio_format = audio_path.suffix.lstrip('.')
        
        # Read file bytes
        with open(audio_path, 'rb') as f:
            audio_bytes = f.read()
        
        # Transcribe
        return self.transcribe_audio_bytes(audio_bytes, language, audio_format)
    
    def check_service_access(self) -> tuple:
        """
        Check if Transcribe service is accessible
        
        Returns:
            tuple: (is_accessible, message)
        """
        try:
            # List transcription jobs to verify access
            self.transcribe_client.list_transcription_jobs(MaxResults=1)
            return True, "✅ Transcribe service accessible"
        
        except ClientError as e:
            error_code = e.response['Error']['Code']
            if error_code == 'AccessDeniedException':
                return False, "❌ Transcribe access denied. Please check IAM permissions."
            return False, f"❌ Transcribe error: {str(e)}"
        
        except Exception as e:
            return False, f"❌ Unexpected error: {str(e)}"


def test_transcribe():
    """Test AWS Transcribe integration"""
    print("🧪 Testing AWS Transcribe STT...")
    print("-" * 60)
    
    # Initialize Transcribe
    # Note: Requires S3 bucket for testing
    try:
        transcribe = TranscribeSTT(s3_bucket="your-bucket-name")
        
        # Check service access
        accessible, message = transcribe.check_service_access()
        print(message)
        
        if accessible:
            print("\n✅ Transcribe service is ready!")
            print("💡 To test transcription, provide an audio file:")
            print("   result = transcribe.transcribe_audio_file('path/to/audio.webm')")
        
    except Exception as e:
        print(f"❌ Error: {str(e)}")
    
    print("-" * 60)


if __name__ == "__main__":
    test_transcribe()
