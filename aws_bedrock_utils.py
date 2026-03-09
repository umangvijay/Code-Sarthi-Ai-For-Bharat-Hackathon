"""
AWS Bedrock Utilities for Code-Sarthi
Handles AI reasoning and Hinglish translation using Claude 3.5 Sonnet
Supports Hybrid Mode for offline operation
Includes retry logic for API resilience and throttling protection
Includes response caching and request deduplication
"""

import boto3
import json
import os
import time
import hashlib
import threading
from typing import Optional, Dict, Any
from tenacity import retry, stop_after_attempt, wait_exponential, retry_if_exception_type
from botocore.exceptions import ClientError

# Force AWS Mode - EC2 with IAM Role
# Set USE_AWS=False in environment to disable (for local development only)
USE_AWS = os.getenv("USE_AWS", "true").lower() == "true"

# Global throttling state
LAST_BEDROCK_CALL = 0
THROTTLE_DELAY = 1.5  # 1.5 second delay between Bedrock calls (max ~40 calls/min)

# Global request lock to prevent parallel calls
REQUEST_LOCK = threading.Lock()

# Maximum prompt length to reduce token usage
MAX_PROMPT_LENGTH = 1500  # Reduced for Nova 2 Lite quota management


def throttle_bedrock():
    """Throttle Bedrock API calls to prevent rate limiting"""
    global LAST_BEDROCK_CALL
    now = time.time()
    elapsed = now - LAST_BEDROCK_CALL
    if elapsed < THROTTLE_DELAY:
        sleep_time = THROTTLE_DELAY - elapsed
        print(f"⏱️  Throttling Bedrock call ({sleep_time:.2f}s)")
        time.sleep(sleep_time)
    LAST_BEDROCK_CALL = time.time()


def get_prompt_hash(prompt: str) -> str:
    """Generate a hash for prompt deduplication"""
    return hashlib.md5(prompt.encode()).hexdigest()


def is_aws_ready():
    """Check if AWS services are ready from session state"""
    try:
        import streamlit as st
        if "aws_ready" in st.session_state:
            return st.session_state["aws_ready"]
        return False
    except Exception:
        return False


class BedrockClient:
    """Client for interacting with Amazon Bedrock (Claude 3.5 Sonnet) with Hybrid Mode support"""
    
    def __init__(self, region_name: str = "ap-south-1"):
        """
        Initialize Bedrock client with Hybrid Mode support
        
        Args:
            region_name: AWS region where Bedrock is available
        """
        self.use_aws = USE_AWS
        self.region_name = region_name
        # Model ID: Cross-region inference profile for Amazon Nova 2 Lite
        # This enables cross-region inference routing and resolves ValidationException
        self.model_id = "us.amazon.nova-2-lite-v1:0"
        
        if self.use_aws:
            # Use IAM roles via boto3.Session() for security
            session = boto3.Session()
            self.client = session.client(
                service_name='bedrock-runtime',
                region_name=region_name
            )
        else:
            self.client = None
    
    def explain_code_in_hinglish(
        self, 
        code_snippet: str, 
        context: str = "",
        complexity_level: str = "beginner"
    ) -> dict:
        """
        Generate Hinglish explanation for code snippet using Nova 2 Lite (Hybrid Mode aware)
        Single request per prompt with comprehensive protections
        
        Args:
            code_snippet: The code to explain
            context: Additional context from lab manual (optional)
            complexity_level: "beginner", "intermediate", or "advanced"
            
        Returns:
            dict with 'explanation' and 'language_detected' keys
        """
        # Validate code snippet is not empty
        if not code_snippet or len(code_snippet.strip()) == 0:
            return {
                "status": "error",
                "explanation": "⚠️ Please enter valid code to explain.",
                "language_detected": "unknown",
                "mode": "error"
            }
        
        # Check AWS mode and readiness
        if self.use_aws and is_aws_ready():
            print("🟢 AWS Mode: Using Bedrock for code explanation")
        else:
            if self.use_aws and not is_aws_ready():
                print("🔴 AWS not ready, falling back to Local Mode")
            else:
                print("🔵 Local Mode: AI simulation")
            language = self._detect_language(code_snippet)
            return {
                "status": "success",
                "explanation": f"🔵 Local Mode: AI simulation\n\nYeh code {language} mein likha gaya hai. Local mode mein detailed explanation available nahi hai. AWS mode enable karne ke liye USE_AWS=true environment variable set karein.\n\nCode snippet:\n{code_snippet[:200]}...",
                "language_detected": language,
                "mode": "local"
            }
        
        # Construct the prompt for Hinglish explanation
        prompt = self._build_hinglish_prompt(code_snippet, context, complexity_level)
        
        # Check for duplicate request
        try:
            import streamlit as st
            prompt_hash = get_prompt_hash(prompt)
            
            if "bedrock_code_cache" not in st.session_state:
                st.session_state.bedrock_code_cache = {}
            
            if prompt_hash in st.session_state.bedrock_code_cache:
                print("📦 Using cached code explanation response")
                return st.session_state.bedrock_code_cache[prompt_hash]
        except:
            pass  # If not in Streamlit context, skip caching
        
        # Limit prompt size to reduce token usage
        if len(prompt) > MAX_PROMPT_LENGTH:
            prompt = prompt[:MAX_PROMPT_LENGTH]
            print(f"⚠️  Prompt truncated to {MAX_PROMPT_LENGTH} characters")
            return {
                "status": "success",
                "explanation": f"🔵 Local Mode: AI simulation\n\nYeh code {language} mein likha gaya hai. Local mode mein detailed explanation available nahi hai. AWS mode enable karne ke liye USE_AWS=true environment variable set karein.\n\nCode snippet:\n{code_snippet[:200]}...",
                "language_detected": language,
                "mode": "local"
            }
        
        # Construct the prompt for Hinglish explanation
        prompt = self._build_hinglish_prompt(code_snippet, context, complexity_level)
        
        # Limit prompt size to prevent token overuse
        if len(prompt) > MAX_PROMPT_LENGTH:
            prompt = prompt[:MAX_PROMPT_LENGTH]
            print(f"⚠️  Prompt truncated to {MAX_PROMPT_LENGTH} characters")
        
        # Single request with lock - NO RETRIES
        try:
            # Throttle to prevent rate limiting
            throttle_bedrock()
            
            print("🔒 Bedrock request triggered (SINGLE REQUEST - NO RETRIES)")
            
            # Use request lock to prevent parallel calls
            with REQUEST_LOCK:
                # Use Converse API with Nova 2 Lite optimized settings
                response = self.client.converse(
                    modelId=self.model_id,
                    messages=[
                        {
                            "role": "user",
                            "content": [{"text": prompt}]
                        }
                    ],
                    inferenceConfig={
                        "maxTokens": 600,
                        "temperature": 0.3
                    }
                )
            
            # Parse response from Converse API
            explanation = response['output']['message']['content'][0]['text']
            
            # Detect programming language
            language = self._detect_language(code_snippet)
            
            result = {
                "status": "success",
                "explanation": explanation,
                "language_detected": language,
                "mode": "aws"
            }
            
            # Cache the response
            try:
                import streamlit as st
                if "bedrock_code_cache" in st.session_state:
                    st.session_state.bedrock_code_cache[prompt_hash] = result
                    print("💾 Response cached for future use")
            except:
                pass
            
            return result
            
        except ClientError as e:
            error_code = e.response.get('Error', {}).get('Code', '')
            print(f"❌ Bedrock error: {error_code} - {str(e)}")
            return {
                "status": "error",
                "message": f"Bedrock API error: {error_code}",
                "mode": "aws"
            }
        except Exception as e:
            print(f"❌ Unexpected error: {str(e)}")
            return {
                "status": "error",
                "message": f"Bedrock API call mein error aaya: {str(e)}",
                "mode": "aws"
            }

    
    def _build_hinglish_prompt(
        self, 
        code_snippet: str, 
        context: str, 
        complexity_level: str
    ) -> str:
        """Build the prompt for Hinglish code explanation"""
        
        complexity_instructions = {
            "beginner": "Bahut simple language mein samjhao, jaise kisi naye student ko samjha rahe ho.",
            "intermediate": "Thoda technical detail ke saath samjhao, student ko basic programming aati hai.",
            "advanced": "Advanced concepts aur best practices ke saath detailed explanation do."
        }
        
        prompt = f"""You are Code-Sarthi, an AI lab assistant for Indian engineering students. Your job is to explain code in Hinglish (Hindi-English mix) that Indian students commonly use.

IMPORTANT RULES:
1. Explain in natural Hinglish - mix Hindi and English naturally
2. Keep ALL programming keywords in English (function, variable, loop, if, else, return, etc.)
3. Keep ALL code syntax exactly as-is
4. Use Hindi for general explanations (samajhna, karna, hona, etc.)
5. Use technical analogies that Indian students relate to
6. {complexity_instructions.get(complexity_level, complexity_instructions["beginner"])}

"""
        
        if context:
            prompt += f"""LAB MANUAL CONTEXT:
{context}

"""
        
        prompt += f"""CODE TO EXPLAIN:
```
{code_snippet}
```

Please explain this code in Hinglish. Start with what the code does, then explain line-by-line if needed."""
        
        return prompt
    
    def _detect_language(self, code_snippet: str) -> str:
        """
        Detect programming language from code snippet
        
        Args:
            code_snippet: Code to analyze
            
        Returns:
            Detected language name
        """
        code_lower = code_snippet.lower()
        
        # Python indicators
        if 'def ' in code_snippet or 'import ' in code_snippet or ':' in code_snippet and 'print(' in code_lower:
            return "python"
        
        # Java indicators
        if 'public class' in code_snippet or 'public static void main' in code_snippet:
            return "java"
        
        # C/C++ indicators
        if '#include' in code_snippet or 'int main()' in code_snippet:
            if 'cout' in code_snippet or 'cin' in code_snippet or 'std::' in code_snippet:
                return "cpp"
            return "c"
        
        # JavaScript indicators
        if 'const ' in code_snippet or 'let ' in code_snippet or 'var ' in code_snippet or '=>' in code_snippet:
            return "javascript"
        
        return "unknown"


# Convenience function for quick testing
def test_bedrock_connection():
    """Test function to verify Bedrock connection works"""
    client = BedrockClient()
    
    test_code = """
def factorial(n):
    if n == 0:
        return 1
    return n * factorial(n-1)
"""
    
    print("Testing Bedrock connection...")
    result = client.explain_code_in_hinglish(test_code)
    
    if result["status"] == "success":
        print(f"\n✓ Connection successful!")
        print(f"Language detected: {result['language_detected']}")
        print(f"\nExplanation:\n{result['explanation']}")
    else:
        print(f"\n✗ Connection failed: {result['message']}")
    
    return result


if __name__ == "__main__":
    test_bedrock_connection()
