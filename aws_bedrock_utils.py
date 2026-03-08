"""
AWS Bedrock Utilities for Code-Sarthi
Handles AI reasoning and Hinglish translation using Claude 3.5 Sonnet
Supports Hybrid Mode for offline operation
Includes retry logic for API resilience
"""

import boto3
import json
import os
from typing import Optional
from tenacity import retry, stop_after_attempt, wait_exponential, retry_if_exception_type
from botocore.exceptions import ClientError

# Hybrid Mode Configuration
USE_AWS = os.getenv("USE_AWS", "False") == "True"


class BedrockClient:
    """Client for interacting with Amazon Bedrock (Claude 3.5 Sonnet) with Hybrid Mode support"""
    
    def __init__(self, region_name: str = "us-west-2"):
        """
        Initialize Bedrock client with Hybrid Mode support
        
        Args:
            region_name: AWS region where Bedrock is available
        """
        self.use_aws = USE_AWS
        self.region_name = region_name
        # Model ID for code explanation
        # self.model_id = "amazon.nova-lite-v1:0"  # Previous: Nova Lite (commented out due to throttling)
        # self.model_id = "amazon.titan-text-express-v1"  # Previous: Titan Text Express
        # self.model_id = "google.gemma-3-12b-it-v1:0"  # Previous: Google Gemma 3 12B (AWS event requirement)
        # self.model_id = "amazon.nova-micro-v1:0"  # Previous: Nova Micro (global)
        # self.model_id = "us.amazon.nova-micro-v1:0"  # Previous: Nova Micro regional for us-west-2
        self.model_id = "us.amazon.nova-pro-v1:0"  # Current: Nova Pro regional for us-west-2 (better quality)
        
        if self.use_aws:
            # Use IAM roles via boto3.Session() for security
            session = boto3.Session()
            self.client = session.client(
                service_name='bedrock-runtime',
                region_name=region_name
            )
        else:
            self.client = None
    
    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=2, max=10),
        retry=retry_if_exception_type(ClientError)
    )
    def explain_code_in_hinglish(
        self, 
        code_snippet: str, 
        context: str = "",
        complexity_level: str = "beginner"
    ) -> dict:
        """
        Generate Hinglish explanation for code snippet using Claude 3.5 Sonnet (Hybrid Mode aware)
        Includes retry logic with exponential backoff for API resilience
        
        Args:
            code_snippet: The code to explain
            context: Additional context from lab manual (optional)
            complexity_level: "beginner", "intermediate", or "advanced"
            
        Returns:
            dict with 'explanation' and 'language_detected' keys
        """
        # Local mode - return mock response
        if not self.use_aws:
            language = self._detect_language(code_snippet)
            return {
                "status": "success",
                "explanation": f"🔵 Local Mode: AI simulation\n\nYeh code {language} mein likha gaya hai. Local mode mein detailed explanation available nahi hai. AWS mode enable karne ke liye USE_AWS=True environment variable set karein.\n\nCode snippet:\n{code_snippet[:200]}...",
                "language_detected": language,
                "mode": "local"
            }
        
        # Construct the prompt for Hinglish explanation
        prompt = self._build_hinglish_prompt(code_snippet, context, complexity_level)
        
        # Prepare request body
        request_body = {
            "anthropic_version": "bedrock-2023-05-31",
            "max_tokens": 2000,
            "messages": [
                {
                    "role": "user",
                    "content": prompt
                }
            ],
            "temperature": 0.7
        }
        
        try:
            # Invoke Bedrock (retry decorator handles failures)
            response = self.client.invoke_model(
                modelId=self.model_id,
                body=json.dumps(request_body)
            )
            
            # Parse response
            response_body = json.loads(response['body'].read())
            explanation = response_body['content'][0]['text']
            
            # Detect programming language
            language = self._detect_language(code_snippet)
            
            return {
                "status": "success",
                "explanation": explanation,
                "language_detected": language,
                "mode": "aws"
            }
            
        except Exception as e:
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
