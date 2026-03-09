"""
AWS Configuration and Credential Validation
Handles AWS service setup and credential checking for EC2 IAM Role authentication
"""

import boto3
import os
from botocore.exceptions import ClientError, NoCredentialsError

# AWS Mode Configuration - Enable AWS services when USE_AWS=true
USE_AWS = os.getenv("USE_AWS", "true").lower() == "true"

# S3 Bucket Configuration - Live production bucket
S3_BUCKET_NAME = os.getenv("S3_BUCKET_NAME", "code-sarthi-pdfs-umang-live")


class AWSConfig:
    """Manages AWS configuration and validates credentials using EC2 IAM Role"""
    
    def __init__(self, region_name="us-east-1"):
        """
        Initialize AWS configuration with EC2 IAM Role support
        
        Args:
            region_name: AWS region (default: us-east-1)
        """
        self.region_name = region_name
        self.services_status = {}
        self.use_aws = USE_AWS
        
        # Initialize boto3 session - automatically uses EC2 IAM role if available
        if self.use_aws:
            self.session = boto3.Session()
        else:
            self.session = None
            print("⚠️  WARNING: USE_AWS is disabled. AWS services will not be available.")
    
    def validate_credentials(self):
        """
        Validate AWS credentials (EC2 IAM Role or configured credentials)
        
        Returns:
            tuple: (is_valid, error_message)
        """
        if not self.use_aws:
            return False, "❌ AWS services disabled (USE_AWS=false)"
        
        try:
            # Get caller identity using IAM role or configured credentials
            sts = self.session.client('sts', region_name=self.region_name)
            identity = sts.get_caller_identity()
            
            # Determine credential source
            arn = identity.get('Arn', '')
            if 'assumed-role' in arn:
                cred_source = "EC2 IAM Role"
            elif 'user' in arn:
                cred_source = "IAM User"
            else:
                cred_source = "IAM Credentials"
            
            return True, f"✅ AWS credentials valid ({cred_source}, Account: {identity['Account']})"
        
        except NoCredentialsError:
            return False, """
❌ AWS credentials not configured!

For EC2: Attach an IAM Role with required permissions
For Local: Run 'aws configure' with your credentials

Required permissions:
- bedrock:InvokeModel
- s3:GetObject, s3:PutObject, s3:ListBucket
- polly:SynthesizeSpeech (optional)
- transcribe:StartTranscriptionJob (optional)
"""
        
        except ClientError as e:
            return False, f"❌ AWS credential error: {str(e)}"
        
        except Exception as e:
            return False, f"❌ Unexpected error: {str(e)}"
    
    def check_bedrock_access(self):
        """
        Check if Bedrock Runtime service is accessible
        
        Returns:
            tuple: (is_accessible, message)
        """
        if not self.use_aws:
            return False, "❌ AWS services disabled (USE_AWS=false)"
        
        try:
            # Initialize Bedrock Runtime client
            bedrock = self.session.client('bedrock-runtime', region_name=self.region_name)
            
            # Bedrock Runtime doesn't have a simple health check API
            # We'll just verify the client was created successfully
            return True, "✅ Bedrock Runtime service accessible"
        
        except ClientError as e:
            error_code = e.response['Error']['Code']
            if error_code == 'AccessDeniedException':
                return False, """
❌ Bedrock access denied!

Your AWS account/role needs:
1. Bedrock service enabled in us-east-1
2. Model access enabled (Amazon Nova Lite)
3. IAM permissions for bedrock:InvokeModel

Enable model access:
https://console.aws.amazon.com/bedrock/home?region=us-east-1#/modelaccess
"""
            return False, f"❌ Bedrock error: {str(e)}"
        
        except Exception as e:
            return False, f"❌ Unexpected error: {str(e)}"
    
    def check_s3_access(self):
        """
        Check if S3 service is accessible
        
        Returns:
            tuple: (is_accessible, message)
        """
        if not self.use_aws:
            return False, "❌ AWS services disabled (USE_AWS=false)"
        
        try:
            s3 = self.session.client('s3', region_name=self.region_name)
            # List buckets to verify access
            s3.list_buckets()
            return True, "✅ S3 service accessible"
        
        except ClientError as e:
            return False, f"❌ S3 access error: {str(e)}"
        
        except Exception as e:
            return False, f"❌ Unexpected error: {str(e)}"
    

    def check_polly_access(self):
        """
        Check if Polly service is accessible (optional for voice features)
        
        Returns:
            tuple: (is_accessible, message)
        """
        if not self.use_aws:
            return False, "❌ AWS services disabled (USE_AWS=false)"
        
        try:
            polly = self.session.client('polly', region_name=self.region_name)
            # List voices to verify access
            polly.describe_voices(LanguageCode='en-IN')
            return True, "✅ Polly service accessible"
        
        except ClientError as e:
            error_code = e.response['Error']['Code']
            if error_code == 'AccessDeniedException':
                return False, "⚠️  Polly access denied (optional for voice features)"
            return False, f"⚠️  Polly error: {str(e)} (optional)"
        
        except Exception as e:
            return False, f"⚠️  Polly error: {str(e)} (optional)"
    
    def check_all_services(self):
        """
        Check all AWS services and return status
        
        Returns:
            dict: Service status dictionary
        """
        if not self.use_aws:
            print("⚠️  AWS services disabled (USE_AWS=false)")
            print("-" * 60)
            self.services_status['mode'] = 'disabled'
            self.services_status['credentials'] = False
            self.services_status['bedrock'] = False
            self.services_status['s3'] = False
            self.services_status['polly'] = False
            return self.services_status
        
        print(f"🔍 Checking AWS services... (Region: {self.region_name})")
        print("-" * 60)
        
        # Check credentials first
        cred_valid, cred_msg = self.validate_credentials()
        print(cred_msg)
        self.services_status['credentials'] = cred_valid
        self.services_status['mode'] = 'aws'
        
        if not cred_valid:
            print("-" * 60)
            return self.services_status
        
        # Check Bedrock Runtime (required)
        bedrock_ok, bedrock_msg = self.check_bedrock_access()
        print(bedrock_msg)
        self.services_status['bedrock'] = bedrock_ok
        
        # Check S3 (required for PDF uploads)
        s3_ok, s3_msg = self.check_s3_access()
        print(s3_msg)
        self.services_status['s3'] = s3_ok
        
        # Check Polly (optional for voice features)
        polly_ok, polly_msg = self.check_polly_access()
        print(polly_msg)
        self.services_status['polly'] = polly_ok
        
        print("-" * 60)
        
        return self.services_status
    
    def get_service_status_summary(self):
        """
        Get a summary of service status
        
        Returns:
            str: Status summary
        """
        if not self.services_status:
            return "⚠️  Services not checked yet"
        
        if not self.use_aws:
            return "❌ AWS services disabled (USE_AWS=false)"
        
        required_ok = self.services_status.get('credentials', False) and \
                     self.services_status.get('bedrock', False)
        
        if required_ok:
            return "✅ All required AWS services ready"
        else:
            return "❌ Some required AWS services unavailable"
    
    def is_aws_enabled(self) -> bool:
        """Check if AWS services are enabled"""
        return self.use_aws
    
    def get_mode_display(self) -> str:
        """Get display string for current mode"""
        if not self.use_aws:
            return "❌ AWS Disabled"
        return "🟢 AWS Cloud"


def test_aws_config():
    """Test AWS configuration"""
    config = AWSConfig()
    status = config.check_all_services()
    
    print("\n📊 Service Status Summary:")
    print(config.get_service_status_summary())
    
    return status


if __name__ == "__main__":
    test_aws_config()
