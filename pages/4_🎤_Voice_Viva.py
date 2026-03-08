"""
Voice Viva Practice Page
AI-powered text-based interview practice with real-time evaluation
"""

import streamlit as st
from datetime import datetime
from aws_viva_evaluation import VivaAnswerEvaluator
from monitoring_analytics import ResponseTimeTracker
from utils.theme_manager import apply_theme

# Apply theme globally
apply_theme()


def _record_history(question: str, answer: str, evaluation: dict) -> None:
    """Record viva interaction in conversation history"""
    st.session_state.conversation_history.append({
        "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "type": "viva",
        "input": f"Q: {question}\nA: {answer}",
        "output": f"Score: {evaluation.get('overall_score', 0):.2f} | {evaluation.get('feedback', '')}"
    })


def get_sample_questions():
    """Get sample viva questions by topic"""
    return {
        "Python Basics": [
            "What is a function in Python?",
            "Explain the difference between list and tuple",
            "What is a dictionary and when would you use it?",
            "How does a for loop work in Python?"
        ],
        "Data Structures": [
            "What is an array and how is it different from a linked list?",
            "Explain what a stack is and give a real-world example",
            "What is recursion? Give an example",
            "How does a binary search work?"
        ],
        "OOP Concepts": [
            "What is a class in object-oriented programming?",
            "Explain inheritance with an example",
            "What is the difference between public and private variables?",
            "What is polymorphism?"
        ],
        "Web Development": [
            "What is HTTP and how does it work?",
            "Explain the difference between GET and POST requests",
            "What is a database and why do we need it?",
            "What is an API?"
        ]
    }


def render():
    """Text-based viva practice page with AI evaluation"""
    st.markdown("## 🎤 Voice Viva Practice")
    st.markdown("Practice technical interviews with AI-powered evaluation and feedback in Hinglish.")
    
    st.markdown("<br>", unsafe_allow_html=True)
    
    # Initialize session state for viva
    if 'current_question' not in st.session_state:
        st.session_state.current_question = None
    if 'viva_history' not in st.session_state:
        st.session_state.viva_history = []
    
    # Topic selection
    col1, col2 = st.columns([2, 1])
    
    with col1:
        st.markdown("### 📚 Select Topic")
        topics = get_sample_questions()
        selected_topic = st.selectbox(
            "Choose a topic",
            options=list(topics.keys()),
            label_visibility="collapsed"
        )
    
    with col2:
        st.markdown("### 🎯 Your Stats")
        total_attempts = len(st.session_state.viva_history)
        avg_score = sum([h['score'] for h in st.session_state.viva_history]) / total_attempts if total_attempts > 0 else 0
        
        st.markdown(f"""
            <div class='metric-card' style='padding: 0.5rem;'>
                <div class='metric-value' style='font-size: 1.5rem;'>{total_attempts}</div>
                <div class='metric-label'>Attempts</div>
            </div>
        """, unsafe_allow_html=True)
        
        if total_attempts > 0:
            st.markdown(f"""
                <div class='metric-card' style='padding: 0.5rem; margin-top: 0.5rem;'>
                    <div class='metric-value' style='font-size: 1.5rem;'>{avg_score:.1f}</div>
                    <div class='metric-label'>Avg Score</div>
                </div>
            """, unsafe_allow_html=True)
    
    st.markdown("<br>", unsafe_allow_html=True)
    
    # Question selection
    col_q1, col_q2, col_q3 = st.columns([2, 1, 1])
    
    with col_q1:
        question = st.selectbox(
            "Select a question",
            options=topics[selected_topic],
            key="question_selector"
        )
    
    with col_q2:
        if st.button("🎲 Random Question", use_container_width=True):
            import random
            all_questions = [q for qs in topics.values() for q in qs]
            st.session_state.current_question = random.choice(all_questions)
            st.rerun()
    
    with col_q3:
        if st.button("🔄 Reset", use_container_width=True):
            st.session_state.current_question = None
            st.rerun()
    
    # Use random question if set
    if st.session_state.current_question:
        question = st.session_state.current_question
    
    # Display current question
    st.markdown("### 💬 Question")
    st.markdown(f"""
        <div class='feature-card' style='background: linear-gradient(135deg, #FF8A00 0%, #FF5E00 100%); color: white; padding: 1.5rem;'>
            <div style='font-size: 1.2rem; font-weight: 600;'>{question}</div>
        </div>
    """, unsafe_allow_html=True)
    
    st.markdown("<br>", unsafe_allow_html=True)
    
    # Answer input
    st.markdown("### ✍️ Your Answer")
    answer = st.text_area(
        "Type your answer in English, Hindi, or Hinglish",
        height=150,
        placeholder="Example: Function ek reusable code block hai jo specific task perform karta hai...",
        help="Answer in your own words - mix Hindi and English naturally!",
        key="answer_input"
    )
    
    st.markdown("<br>", unsafe_allow_html=True)
    
    # Submit button
    col_btn1, col_btn2, col_btn3 = st.columns([1, 2, 1])
    with col_btn2:
        submit_btn = st.button("🚀 Submit Answer for Evaluation", use_container_width=True)
    
    if submit_btn:
        if not answer.strip():
            st.markdown("""
                <div class='status-box status-error'>
                    ⚠️ Please write your answer first!
                </div>
            """, unsafe_allow_html=True)
            return
        
        if not st.session_state.get('aws_config'):
            st.markdown("""
                <div class='status-box status-error'>
                    ❌ AWS services not ready. Please check the AWS Status page.
                </div>
            """, unsafe_allow_html=True)
            return
        
        # Evaluate answer
        with st.spinner("🤖 AI interviewer aapka answer evaluate kar raha hai..."):
            try:
                evaluator = VivaAnswerEvaluator()
                
                with ResponseTimeTracker(st.session_state.analytics, "viva_evaluation"):
                    st.session_state.analytics.track_api_call("bedrock")
                    result = evaluator.evaluate_answer(
                        question=question,
                        answer=answer
                    )
                
                if result.get('status') == 'success':
                    # Store in history
                    st.session_state.viva_history.append({
                        'question': question,
                        'answer': answer,
                        'score': result['overall_score'],
                        'timestamp': datetime.now()
                    })
                    
                    _record_history(question, answer, result)
                    
                    # Display results
                    st.markdown("<br>", unsafe_allow_html=True)
                    st.markdown("### 📊 Evaluation Results")
                    
                    # Score cards
                    col_s1, col_s2, col_s3, col_s4 = st.columns(4)
                    
                    with col_s1:
                        score_color = "#48bb78" if result['overall_score'] >= 0.7 else "#FF8A00" if result['overall_score'] >= 0.5 else "#f56565"
                        st.markdown(f"""
                            <div class='metric-card' style='background: {score_color};'>
                                <div class='metric-value'>{result['overall_score']:.2f}</div>
                                <div class='metric-label'>Overall</div>
                            </div>
                        """, unsafe_allow_html=True)
                    
                    with col_s2:
                        st.markdown(f"""
                            <div class='metric-card'>
                                <div class='metric-value'>{result['correctness_score']:.2f}</div>
                                <div class='metric-label'>Correct</div>
                            </div>
                        """, unsafe_allow_html=True)
                    
                    with col_s3:
                        st.markdown(f"""
                            <div class='metric-card'>
                                <div class='metric-value'>{result['completeness_score']:.2f}</div>
                                <div class='metric-label'>Complete</div>
                            </div>
                        """, unsafe_allow_html=True)
                    
                    with col_s4:
                        st.markdown(f"""
                            <div class='metric-card'>
                                <div class='metric-value'>{result['clarity_score']:.2f}</div>
                                <div class='metric-label'>Clear</div>
                            </div>
                        """, unsafe_allow_html=True)
                    
                    # Feedback
                    st.markdown("<br>", unsafe_allow_html=True)
                    st.markdown("### 💬 Feedback")
                    st.markdown(f"""
                        <div class='output-container'>
{result['feedback']}
                        </div>
                    """, unsafe_allow_html=True)
                    
                    # Detailed evaluation
                    if result.get('evaluation_details'):
                        details = result['evaluation_details']
                        
                        col_d1, col_d2 = st.columns(2)
                        
                        with col_d1:
                            if details.get('strengths'):
                                st.markdown("#### ✅ Strengths")
                                for strength in details['strengths']:
                                    st.markdown(f"- {strength}")
                        
                        with col_d2:
                            if details.get('improvements'):
                                st.markdown("#### 💡 Areas to Improve")
                                for improvement in details['improvements']:
                                    st.markdown(f"- {improvement}")
                    
                    # Follow-up question
                    if result.get('follow_up_question'):
                        st.markdown("<br>", unsafe_allow_html=True)
                        st.markdown("### 🔄 Follow-up Question")
                        st.markdown(f"""
                            <div class='feature-card' style='background: linear-gradient(135deg, #0073BB 0%, #005A8C 100%); color: white; padding: 1.5rem;'>
                                <div style='font-size: 1.1rem;'>{result['follow_up_question']}</div>
                            </div>
                        """, unsafe_allow_html=True)
                        
                        if st.button("📝 Answer This Question", use_container_width=True):
                            st.session_state.current_question = result['follow_up_question']
                            st.rerun()
                
                else:
                    st.markdown(f"""
                        <div class='status-box status-error'>
                            ❌ {result.get('message', 'Evaluation failed')}
                        </div>
                    """, unsafe_allow_html=True)
            
            except Exception as e:
                st.markdown(f"""
                    <div class='status-box status-error'>
                        ❌ Error during evaluation: {str(e)}
                    </div>
                """, unsafe_allow_html=True)


if __name__ == "__main__":
    render()
else:
    render()
