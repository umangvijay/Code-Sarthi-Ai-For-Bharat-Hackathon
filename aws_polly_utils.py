"""
AWS Polly Text-to-Speech Utilities
Converts text to speech using AWS Polly with Hindi and Hinglish support
Supports Hybrid Mode for offline operation
"""

import boto3
import hashlib
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
        # If not in Streamlit context or any error, return False
        return False


class PollyTTS:
    """AWS Polly Text-to-Speech Engine with Hybrid Mode support"""
    
    # Voice configurations for Hindi and Hinglish
    VOICE_CONFIGS = {
        'hindi': {
            'VoiceId': 'Aditi',  # Indian English female voice (supports Hindi)
            'LanguageCode': 'hi-IN',
            'Engine': 'neural'
        },
        'hinglish': {
            'VoiceId': 'Aditi',  # Best for Hinglish (Indian English)
            'LanguageCode': 'en-IN',
            'Engine': 'neural'
        },
        'english': {
            'VoiceId': 'Kajal',  # Indian English female voice
            'LanguageCode': 'en-IN',
            'Engine': 'neural'
        }
    }
    
    def __init__(self, region_name="us-east-1", cache_dir=".polly_cache"):
        """
        Initialize Polly TTS engine with Hybrid Mode support
        
        Args:
            region_name: AWS region
            cache_dir: Directory to cache audio files
        """
        self.use_aws = USE_AWS
        self.region_name = region_name
        
        if self.use_aws:
            # Use IAM roles via boto3.Session() for security
            session = boto3.Session()
            self.polly_client = session.client('polly', region_name=region_name)
        else:
            self.polly_client = None
        
        # Setup cache directory
        self.cache_dir = Path(cache_dir)
        self.cache_dir.mkdir(exist_ok=True)
        
        mode_str = "AWS Cloud" if self.use_aws else "Local Offline"
        print(f"✅ Polly TTS initialized ({mode_str}, cache: {cache_dir})")
    
    def _get_cache_key(self, text: str, voice_type: str) -> str:
        """
        Generate cache key for text and voice combination
        
        Args:
            text: Text to convert
            voice_type: Voice type (hindi/hinglish/english)
            
        Returns:
            Cache key (hash)
        """
        content = f"{text}_{voice_type}"
        return hashlib.md5(content.encode()).hexdigest()
    
    def _get_cache_path(self, cache_key: str) -> Path:
        """Get cache file path for a cache key"""
        return self.cache_dir / f"{cache_key}.mp3"
    
    def synthesize_speech(
        self,
        text: str,
        voice_type: str = 'hinglish',
        use_cache: bool = True
    ) -> bytes:
        """
        Convert text to speech using AWS Polly (Hybrid Mode aware)
        
        Args:
            text: Text to convert to speech
            voice_type: Voice type - 'hindi', 'hinglish', or 'english'
            use_cache: Whether to use cached audio files
            
        Returns:
            Audio bytes (MP3 format) or mock data in local mode
            
        Raises:
            ValueError: If voice_type is invalid
            ClientError: If AWS Polly API call fails
        """
        if voice_type not in self.VOICE_CONFIGS:
            raise ValueError(f"Invalid voice_type: {voice_type}. Must be one of {list(self.VOICE_CONFIGS.keys())}")
        
        # Check AWS mode and readiness
        if self.use_aws and is_aws_ready():
            print(f"🟢 AWS Mode: Using Polly TTS for: {text[:50]}...")
        else:
            if self.use_aws and not is_aws_ready():
                print(f"🔴 AWS not ready, falling back to Local Mode for: {text[:50]}...")
            else:
                print(f"🔵 Local Mode: TTS simulation for: {text[:50]}...")
            # Return minimal valid MP3 header (silent audio)
            return b'\xff\xfb\x90\x00' + b'\x00' * 100
        
        # Check cache first
        if use_cache:
            cache_key = self._get_cache_key(text, voice_type)
            cache_path = self._get_cache_path(cache_key)
            
            if cache_path.exists():
                print(f"📦 Using cached audio for: {text[:50]}...")
                with open(cache_path, 'rb') as f:
                    return f.read()
        
        # Get voice configuration
        voice_config = self.VOICE_CONFIGS[voice_type]
        
        try:
            print(f"🎤 Synthesizing speech with {voice_config['VoiceId']} ({voice_type})...")
            
            # Call AWS Polly
            response = self.polly_client.synthesize_speech(
                Text=text,
                OutputFormat='mp3',
                VoiceId=voice_config['VoiceId'],
                LanguageCode=voice_config['LanguageCode'],
                Engine=voice_config['Engine']
            )
            
            # Read audio stream
            audio_bytes = response['AudioStream'].read()
            
            # Cache the audio
            if use_cache:
                cache_key = self._get_cache_key(text, voice_type)
                cache_path = self._get_cache_path(cache_key)
                
                with open(cache_path, 'wb') as f:
                    f.write(audio_bytes)
                
                print(f"💾 Cached audio: {cache_path.name}")
            
            print(f"✅ Speech synthesized successfully ({len(audio_bytes)} bytes)")
            return audio_bytes
        
        except ClientError as e:
            error_code = e.response['Error']['Code']
            error_msg = e.response['Error']['Message']
            
            if error_code == 'AccessDeniedException':
                raise ClientError(
                    {
                        'Error': {
                            'Code': 'AccessDeniedException',
                            'Message': 'AWS Polly access denied. Please check IAM permissions for polly:SynthesizeSpeech'
                        }
                    },
                    'synthesize_speech'
                )
            
            raise ClientError(
                {
                    'Error': {
                        'Code': error_code,
                        'Message': f"Polly error: {error_msg}"
                    }
                },
                'synthesize_speech'
            )
    
    def get_available_voices(self) -> list:
        """
        Get list of available Polly voices
        
        Returns:
            List of voice dictionaries
        """
        try:
            response = self.polly_client.describe_voices()
            return response.get('Voices', [])
        except ClientError as e:
            print(f"❌ Error fetching voices: {str(e)}")
            return []
    
    def clear_cache(self):
        """Clear all cached audio files"""
        count = 0
        for cache_file in self.cache_dir.glob("*.mp3"):
            cache_file.unlink()
            count += 1
        
        print(f"🗑️  Cleared {count} cached audio files")
        return count
    
    def get_cache_size(self) -> int:
        """
        Get total size of cached audio files
        
        Returns:
            Size in bytes
        """
        total_size = 0
        for cache_file in self.cache_dir.glob("*.mp3"):
            total_size += cache_file.stat().st_size
        
        return total_size
    
    def get_cache_stats(self) -> dict:
        """
        Get cache statistics
        
        Returns:
            Dictionary with cache stats
        """
        cache_files = list(self.cache_dir.glob("*.mp3"))
        total_size = sum(f.stat().st_size for f in cache_files)
        
        return {
            'file_count': len(cache_files),
            'total_size_bytes': total_size,
            'total_size_mb': round(total_size / (1024 * 1024), 2),
            'cache_dir': str(self.cache_dir)
        }


def test_polly():
    """Test AWS Polly integration"""
    print("🧪 Testing AWS Polly TTS...")
    print("-" * 60)
    
    # Initialize Polly
    polly = PollyTTS()
    
    # Test texts
    test_cases = [
        ("Hello, this is a test in English.", "english"),
        ("Yeh ek Hinglish test hai. This is mixing Hindi and English.", "hinglish"),
        ("नमस्ते, यह एक हिंदी परीक्षण है।", "hindi")
    ]
    
    for text, voice_type in test_cases:
        print(f"\n📝 Text: {text}")
        print(f"🎤 Voice: {voice_type}")
        
        try:
            audio_bytes = polly.synthesize_speech(text, voice_type)
            print(f"✅ Generated {len(audio_bytes)} bytes of audio")
        except Exception as e:
            print(f"❌ Error: {str(e)}")
    
    # Show cache stats
    print("\n" + "-" * 60)
    stats = polly.get_cache_stats()
    print(f"📊 Cache Stats:")
    print(f"   Files: {stats['file_count']}")
    print(f"   Size: {stats['total_size_mb']} MB")
    print(f"   Location: {stats['cache_dir']}")


if __name__ == "__main__":
    test_polly()
