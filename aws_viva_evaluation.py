"""
AWS Viva Answer Evaluation for Code-Sarthi
Evaluates student answers for correctness, completeness, and clarity using AWS Bedrock

This module implements answer evaluation for the Voice Viva Bot:
1. Evaluates answers across three dimensions: correctness, completeness, clarity
2. Generates Hinglish feedback for students
3. Creates intelligent follow-up questions based on student answers

Requirements Implemented:
- Requirement 4.4: Evaluate answer for correctness and completeness within 3 seconds
- Requirement 4.5: Provide feedback in Hinglish covering correctness, completeness, and clarity
- Requirement 4.6: Ask follow-up questions based on user's answer to simulate real viva scenarios

Key Features:
- Three-dimensional scoring (0.0 to 1.0 scale)
- Natural Hinglish feedback
- Context-aware follow-up question generation
- Detailed evaluation breakdown

Usage Example:
    evaluator = VivaAnswerEvaluator()
    result = evaluator.evaluate_answer(
        question="What is a function?",
        answer="Function ek code block hai jo specific task karta hai",
        expected_concepts=["reusable code", "parameters", "return value"]
    )
    # Returns: scores, feedback, follow_up_question
"""

import boto3
import json
from typing import Dict, List, Optional


class VivaAnswerEvaluator:
    """
    Evaluates viva answers using AWS Bedrock (Claude 3.5 Sonnet)
    
    Provides three-dimensional scoring:
    - Correctness: Technical accuracy of the answer
    - Completeness: Coverage of key concepts
    - Clarity: How well the answer is explained
    """
    
    def __init__(self, region_name: str = "us-east-1"):
        """
        Initialize Viva Answer Evaluator
        
        Args:
            region_name: AWS region for Bedrock
        """
        self.bedrock_client = boto3.client(
            service_name='bedrock-runtime',
            region_name=region_name
        )
        self.model_id = "us.anthropic.claude-3-haiku-20240307-v1:0"
    
    def evaluate_answer(
        self,
        question: str,
        answer: str,
        expected_concepts: Optional[List[str]] = None,
        context: Optional[str] = None
    ) -> Dict:
        """
        Evaluate a viva answer across three dimensions
        
        Args:
            question: The viva question that was asked
            answer: The student's answer
            expected_concepts: List of key concepts that should be covered (optional)
            context: Additional context from lab manual (optional)
            
        Returns:
            dict with:
                - correctness_score: float (0.0 to 1.0)
                - completeness_score: float (0.0 to 1.0)
                - clarity_score: float (0.0 to 1.0)
                - overall_score: float (0.0 to 1.0)
                - feedback: str (Hinglish feedback)
                - follow_up_question: str (Next question based on answer)
                - evaluation_details: dict (detailed breakdown)
        """
        # Build evaluation prompt
        prompt = self._build_evaluation_prompt(
            question, answer, expected_concepts, context
        )
        
        # Prepare request body for Bedrock
        request_body = {
            "anthropic_version": "bedrock-2023-05-31",
            "max_tokens": 2000,
            "messages": [
                {
                    "role": "user",
                    "content": prompt
                }
            ],
            "temperature": 0.3  # Lower temperature for consistent evaluation
        }
        
        try:
            # Invoke Bedrock
            response = self.bedrock_client.invoke_model(
                modelId=self.model_id,
                body=json.dumps(request_body)
            )
            
            # Parse response
            response_body = json.loads(response['body'].read())
            evaluation_text = response_body['content'][0]['text']
            
            # Parse the structured evaluation
            result = self._parse_evaluation_response(evaluation_text)
            
            return {
                "status": "success",
                **result
            }
            
        except Exception as e:
            return {
                "status": "error",
                "message": f"Evaluation mein error aaya: {str(e)}",
                "correctness_score": 0.0,
                "completeness_score": 0.0,
                "clarity_score": 0.0,
                "overall_score": 0.0,
                "feedback": "Answer evaluate nahi ho paya. Kripya dobara try karein.",
                "follow_up_question": question
            }
    
    def _build_evaluation_prompt(
        self,
        question: str,
        answer: str,
        expected_concepts: Optional[List[str]],
        context: Optional[str]
    ) -> str:
        """Build the evaluation prompt for Bedrock"""
        
        concepts_text = ""
        if expected_concepts:
            concepts_text = f"\n\nKey concepts to look for:\n" + "\n".join(f"- {concept}" for concept in expected_concepts)
        
        context_text = ""
        if context:
            context_text = f"\n\nLab manual context:\n{context}"
        
        prompt = f"""You are an expert viva examiner for Indian engineering students. Your task is to evaluate a student's answer to a viva question.

QUESTION ASKED:
{question}

STUDENT'S ANSWER:
{answer}
{concepts_text}
{context_text}

EVALUATION TASK:
Evaluate the answer across THREE dimensions and provide scores from 0.0 to 1.0:

1. CORRECTNESS (0.0 to 1.0):
   - Is the answer technically accurate?
   - Are there any factual errors or misconceptions?
   - Score: 1.0 = completely correct, 0.5 = partially correct, 0.0 = incorrect

2. COMPLETENESS (0.0 to 1.0):
   - Does the answer cover all key concepts?
   - Are important points missing?
   - Score: 1.0 = fully complete, 0.5 = partially complete, 0.0 = incomplete

3. CLARITY (0.0 to 1.0):
   - Is the explanation clear and well-structured?
   - Can someone easily understand the answer?
   - Score: 1.0 = very clear, 0.5 = somewhat clear, 0.0 = unclear

RESPONSE FORMAT (MUST FOLLOW EXACTLY):
```json
{{
  "correctness_score": <float between 0.0 and 1.0>,
  "completeness_score": <float between 0.0 and 1.0>,
  "clarity_score": <float between 0.0 and 1.0>,
  "feedback": "<Hinglish feedback in 2-3 sentences explaining the scores. Use natural Hindi-English mix. Be encouraging but honest. Example: 'Tumhara answer sahi direction mein hai! Function ka basic concept samajh aa gaya, lekin parameters aur return values ke baare mein thoda aur detail chahiye tha. Overall achha effort hai!'>"
  "follow_up_question": "<Generate a follow-up question in Hinglish based on the student's answer. If answer was weak, ask a simpler related question. If answer was strong, ask a deeper question. Example: 'Achha, ab yeh batao - function mein parameters ka kya role hota hai?'>"
  "strengths": ["<list of 1-2 things done well>"],
  "improvements": ["<list of 1-2 areas to improve>"]
}}
```

IMPORTANT:
- Provide ONLY the JSON response, no additional text
- Use natural Hinglish in feedback and follow-up question
- Be encouraging and constructive
- Scores must be between 0.0 and 1.0
- Follow-up question should be related to the topic and appropriate for the student's level"""
        
        return prompt
    
    def _parse_evaluation_response(self, evaluation_text: str) -> Dict:
        """Parse the structured evaluation response from Bedrock"""
        
        try:
            # Extract JSON from response (handle markdown code blocks)
            json_text = evaluation_text
            if "```json" in evaluation_text:
                json_text = evaluation_text.split("```json")[1].split("```")[0].strip()
            elif "```" in evaluation_text:
                json_text = evaluation_text.split("```")[1].split("```")[0].strip()
            
            # Parse JSON
            evaluation = json.loads(json_text)
            
            # Calculate overall score (weighted average)
            overall_score = (
                evaluation.get("correctness_score", 0.0) * 0.4 +  # 40% weight
                evaluation.get("completeness_score", 0.0) * 0.35 +  # 35% weight
                evaluation.get("clarity_score", 0.0) * 0.25  # 25% weight
            )
            
            return {
                "correctness_score": float(evaluation.get("correctness_score", 0.0)),
                "completeness_score": float(evaluation.get("completeness_score", 0.0)),
                "clarity_score": float(evaluation.get("clarity_score", 0.0)),
                "overall_score": round(overall_score, 2),
                "feedback": evaluation.get("feedback", "Evaluation complete."),
                "follow_up_question": evaluation.get("follow_up_question", ""),
                "evaluation_details": {
                    "strengths": evaluation.get("strengths", []),
                    "improvements": evaluation.get("improvements", [])
                }
            }
            
        except (json.JSONDecodeError, KeyError, ValueError) as e:
            # Fallback if parsing fails
            return {
                "correctness_score": 0.5,
                "completeness_score": 0.5,
                "clarity_score": 0.5,
                "overall_score": 0.5,
                "feedback": "Answer achha tha, lekin evaluation mein thodi problem aayi. Kripya dobara try karein.",
                "follow_up_question": "Kya aap apne answer ko thoda aur detail mein explain kar sakte ho?",
                "evaluation_details": {
                    "strengths": ["Answer diya"],
                    "improvements": ["Thoda aur detail chahiye"]
                }
            }


# Convenience function for testing
def test_viva_evaluation():
    """Test function to verify viva evaluation works"""
    evaluator = VivaAnswerEvaluator()
    
    # Test case 1: Good answer
    print("=" * 60)
    print("TEST CASE 1: Good Answer")
    print("=" * 60)
    
    result1 = evaluator.evaluate_answer(
        question="What is a function in programming?",
        answer="Function ek reusable code block hai jo specific task perform karta hai. Hum function ko define karte hain aur phir jab chahein call kar sakte hain. Function parameters le sakta hai aur value return kar sakta hai.",
        expected_concepts=["reusable code", "parameters", "return value", "code block"]
    )
    
    print(f"Status: {result1['status']}")
    print(f"Correctness: {result1['correctness_score']:.2f}")
    print(f"Completeness: {result1['completeness_score']:.2f}")
    print(f"Clarity: {result1['clarity_score']:.2f}")
    print(f"Overall: {result1['overall_score']:.2f}")
    print(f"\nFeedback: {result1['feedback']}")
    print(f"\nFollow-up: {result1['follow_up_question']}")
    
    # Test case 2: Weak answer
    print("\n" + "=" * 60)
    print("TEST CASE 2: Weak Answer")
    print("=" * 60)
    
    result2 = evaluator.evaluate_answer(
        question="What is a function in programming?",
        answer="Function code hai jo kaam karta hai.",
        expected_concepts=["reusable code", "parameters", "return value", "code block"]
    )
    
    print(f"Status: {result2['status']}")
    print(f"Correctness: {result2['correctness_score']:.2f}")
    print(f"Completeness: {result2['completeness_score']:.2f}")
    print(f"Clarity: {result2['clarity_score']:.2f}")
    print(f"Overall: {result2['overall_score']:.2f}")
    print(f"\nFeedback: {result2['feedback']}")
    print(f"\nFollow-up: {result2['follow_up_question']}")
    
    return result1, result2


if __name__ == "__main__":
    test_viva_evaluation()
