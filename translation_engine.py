"""
Translation Engine for Code-Sarthi
Converts technical English explanations to natural Hinglish while preserving technical terms
Supports Hybrid Mode for offline operation

This module implements the TranslationEngine class which is responsible for:
1. Translating technical English explanations to natural Hinglish
2. Detecting and preserving programming keywords and technical terms
3. Applying translation rules using Amazon Bedrock (Claude 3.5 Sonnet)
4. Caching translations to reduce API costs and latency

Requirements Implemented:
- Requirement 5.1: Maintains technical accuracy when converting English to Hinglish
- Requirement 5.2: Uses common Hindi words for general concepts
- Requirement 5.3: Keeps programming keywords and syntax in English
- Requirement 5.6: Uses English with Hindi explanation for terms lacking Hindi equivalents

Key Features:
- Comprehensive technical term detection using regex patterns
- Bedrock integration for high-quality Hinglish translation
- Preservation of code syntax, function names, and variable names
- Natural code-switching patterns common in Indian English
- Error handling with graceful fallback
- Hybrid Mode support for offline operation
- LRU caching for repetitive translations (cost optimization)
- Retry logic with exponential backoff for API resilience

Usage Example:
    engine = TranslationEngine()
    english_text = "This function returns the sum of array elements"
    hinglish_text = engine.translate(english_text)
    # Output: "Yeh function array elements ka sum return karta hai"
"""

import re
import json
import boto3
import os
import hashlib
from typing import List, Optional
from tenacity import retry, stop_after_attempt, wait_exponential, retry_if_exception_type
from botocore.exceptions import ClientError

# Hybrid Mode Configuration
USE_AWS = os.getenv("USE_AWS", "False") == "True"


class TranslationEngine:
    """
    Converts technical English explanations to natural Hinglish with Hybrid Mode support
    
    Maintains technical accuracy while using common Hindi words for general concepts.
    Preserves programming keywords and syntax in English.
    """
    
    # Programming keywords and technical terms to preserve in English
    TECHNICAL_TERMS = {
        # Control flow
        'if', 'else', 'elif', 'switch', 'case', 'for', 'while', 'do', 'break', 'continue',
        'return', 'yield', 'try', 'catch', 'finally', 'throw', 'raise',
        
        # Data types
        'int', 'float', 'double', 'char', 'string', 'bool', 'boolean', 'void', 'null',
        'array', 'list', 'dict', 'dictionary', 'set', 'tuple', 'object',
        
        # OOP concepts
        'class', 'interface', 'struct', 'enum', 'public', 'private', 'protected',
        'static', 'final', 'const', 'abstract', 'virtual', 'override',
        
        # Functions
        'function', 'method', 'constructor', 'destructor', 'lambda', 'callback',
        'async', 'await', 'promise', 'thread',
        
        # Operations
        'variable', 'parameter', 'argument', 'pointer', 'reference', 'index',
        'loop', 'iteration', 'recursion', 'algorithm', 'syntax', 'compile',
        'runtime', 'exception', 'error', 'debug', 'import', 'export', 'module',
        
        # Common programming terms
        'api', 'json', 'xml', 'http', 'url', 'database', 'query', 'sql',
        'git', 'commit', 'push', 'pull', 'merge', 'branch'
    }
    
    def __init__(self, bedrock_client=None, region_name: str = "us-east-1"):
        """
        Initialize Translation Engine with Hybrid Mode support
        
        Args:
            bedrock_client: Optional boto3 Bedrock client (for testing/mocking)
            region_name: AWS region for Bedrock
        """
        self.use_aws = USE_AWS
        
        if bedrock_client:
            self.bedrock_client = bedrock_client
        elif self.use_aws:
            # Use IAM roles via boto3.Session() for security
            session = boto3.Session()
            self.bedrock_client = session.client(
                service_name='bedrock-runtime',
                region_name=region_name
            )
        else:
            self.bedrock_client = None
            
        # Model ID for text generation
        # self.model_id = "amazon.nova-lite-v1:0"  # Previous: Nova Lite (commented out due to throttling)
        # self.model_id = "amazon.titan-text-express-v1"  # Previous: Titan Text Express
        # self.model_id = "google.gemma-3-12b-it-v1:0"  # Previous: Google Gemma 3 12B (AWS event requirement)
        # self.model_id = "amazon.nova-micro-v1:0"  # Previous: Nova Micro in ap-northeast-3
        # self.model_id = "anthropic.claude-3-5-sonnet-20241022-v2:0"  # Previous: Raw model ID (doesn't support on-demand)
        # self.model_id = "us.anthropic.claude-3-5-sonnet-20241022-v2:0"  # Previous: Claude inference profile in ap-northeast-1
        # self.model_id = "amazon.nova-2-lite-v1:0"  # Previous: Nova 2 Lite raw model ID
        self.model_id = "us.amazon.nova-lite-v1:0"  # Current: Nova Lite cross-region inference profile in us-east-1
        
        # Simple dictionary cache instead of LRU cache
        self._translation_cache = {}
    
    def translate(self, text: str, preserve_terms: Optional[List[str]] = None) -> str:
        """
        Translates English text to Hinglish while preserving technical terms
        Uses caching to reduce API costs for repetitive translations
        
        Args:
            text: English explanation text
            preserve_terms: Additional terms to keep in English (beyond default technical terms)
            
        Returns:
            Hinglish translation with preserved technical terms
        """
        if not text or not text.strip():
            return text
        
        # Generate cache key from text
        cache_key = self._generate_cache_key(text)
        
        # Try to get from cache
        cached_result = self._get_from_cache(cache_key)
        if cached_result:
            return cached_result
        
        # Detect technical terms in the text
        detected_terms = self.detect_technical_terms(text)
        
        # Combine with user-provided terms
        all_preserve_terms = detected_terms
        if preserve_terms:
            all_preserve_terms.extend(preserve_terms)
        
        # Apply translation rules using Bedrock
        translated = self.apply_translation_rules(text, all_preserve_terms)
        
        # Store in cache
        self._store_in_cache(cache_key, translated)
        
        return translated
    
    def _generate_cache_key(self, text: str) -> str:
        """Generate a hash key for caching"""
        return hashlib.md5(text.encode('utf-8')).hexdigest()
    
    def _get_from_cache(self, cache_key: str) -> Optional[str]:
        """Get translation from simple dictionary cache"""
        return self._translation_cache.get(cache_key)
    
    def _store_in_cache(self, cache_key: str, translation: str) -> None:
        """Store translation in simple dictionary cache"""
        # Limit cache size to prevent memory issues
        if len(self._translation_cache) > 100:
            # Remove oldest entry (first key)
            first_key = next(iter(self._translation_cache))
            del self._translation_cache[first_key]
        
        self._translation_cache[cache_key] = translation
    
    def detect_technical_terms(self, text: str) -> List[str]:
        """
        Identifies programming keywords and technical terms that should remain in English
        
        Args:
            text: Text to analyze
            
        Returns:
            List of terms that should remain in English
        """
        detected = []
        text_lower = text.lower()
        
        # Check for known technical terms (including word forms like "returns" for "return")
        for term in self.TECHNICAL_TERMS:
            # Use word boundaries to match whole words only
            # Also match common word forms (e.g., "returns" contains "return")
            pattern = r'\b' + re.escape(term) + r's?\b'  # Optional 's' for plural/verb forms
            if re.search(pattern, text_lower):
                detected.append(term)
        
        # Detect code blocks (anything between backticks or in code-like patterns)
        code_patterns = [
            r'`[^`]+`',  # Inline code
            r'```[\s\S]+?```',  # Code blocks
            r'\b[a-zA-Z_][a-zA-Z0-9_]*\(',  # Function calls
        ]
        
        for pattern in code_patterns:
            matches = re.findall(pattern, text)
            for match in matches:
                # Clean up the match (remove backticks, parentheses)
                clean_match = re.sub(r'[`()]', '', match).strip()
                if clean_match and clean_match not in detected:
                    detected.append(clean_match)
        
        return detected
    
    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=2, max=10),
        retry=retry_if_exception_type(ClientError)
    )
    def apply_translation_rules(self, text: str, terms: List[str]) -> str:
        """
        Applies Hinglish translation rules using Bedrock (Hybrid Mode aware)
        Includes retry logic with exponential backoff for resilience
        
        Args:
            text: English text to translate
            terms: List of technical terms to preserve in English
            
        Returns:
            Translated text with natural Hindi phrasing
        """
        # Local mode - return simple mock translation
        if not self.use_aws:
            return f"🔵 Local Mode: Translation simulation\n\n{text}\n\n(Enable AWS mode for full Hinglish translation)"
        
        # Build the translation prompt
        prompt = self._build_translation_prompt(text, terms)
        
        # Prepare request body for Bedrock
        request_body = {
            "anthropic_version": "bedrock-2023-05-31",
            "max_tokens": 3000,
            "messages": [
                {
                    "role": "user",
                    "content": prompt
                }
            ],
            "temperature": 0.5  # Lower temperature for more consistent translations
        }
        
        try:
            # Invoke Bedrock (retry decorator handles failures)
            response = self.bedrock_client.invoke_model(
                modelId=self.model_id,
                body=json.dumps(request_body)
            )
            
            # Parse response
            response_body = json.loads(response['body'].read())
            translated_text = response_body['content'][0]['text']
            
            return translated_text.strip()
            
        except Exception as e:
            # If translation fails after retries, return original text with error note
            return f"{text}\n\n[Translation error: {str(e)}]"
    
    def _build_translation_prompt(self, text: str, preserve_terms: List[str]) -> str:
        """
        Build the prompt for Hinglish translation
        
        Args:
            text: Text to translate
            preserve_terms: Terms to keep in English
            
        Returns:
            Formatted prompt for Bedrock
        """
        terms_list = ", ".join(preserve_terms) if preserve_terms else "none"
        
        prompt = f"""You are a translation expert for Code-Sarthi, an AI lab assistant for Indian engineering students. Your task is to translate technical English explanations into natural Hinglish (Hindi-English mix) that Indian students commonly use.

CRITICAL TRANSLATION RULES:
1. Translate general concepts to common Hindi words:
   - "understand" → "samajhna"
   - "create" → "banana"
   - "process" → "process karna"
   - "work" → "kaam karna"
   - "use" → "use karna" or "istemal karna"
   - "need" → "zaroorat hai" or "chahiye"
   - "this" → "yeh"
   - "that" → "woh"

2. Keep ALL programming keywords and technical terms in English EXACTLY as they appear:
   - Programming keywords: function, variable, loop, if, else, return, class, etc.
   - Code syntax: parentheses, brackets, operators, etc.
   - Technical terms: {terms_list}

3. Use natural code-switching patterns common in Indian English:
   - Mix Hindi and English naturally in the same sentence
   - Use Hindi for explanations, English for technical terms
   - Example: "Yeh function ek value return karta hai"

4. Preserve code blocks, function names, and variable names EXACTLY as-is

5. Use Roman script (not Devanagari) for Hindi words

6. When technical terms lack Hindi equivalents, keep them in English and add a brief Hindi explanation if needed

TEXT TO TRANSLATE:
{text}

IMPORTANT: Provide ONLY the translated text. Do not add any explanations, notes, or meta-commentary about the translation."""
        
        return prompt


# Convenience function for testing
def test_translation():
    """Test function to verify translation works"""
    engine = TranslationEngine()
    
    test_text = """This function iterates over the array and returns the sum of all elements. 
The variable 'total' stores the accumulated value. If the array is empty, it returns 0."""
    
    print("Testing Translation Engine...")
    print(f"\nOriginal text:\n{test_text}")
    
    translated = engine.translate(test_text)
    print(f"\nTranslated to Hinglish:\n{translated}")
    
    # Test technical term detection
    terms = engine.detect_technical_terms(test_text)
    print(f"\nDetected technical terms: {terms}")
    
    return translated


if __name__ == "__main__":
    test_translation()
