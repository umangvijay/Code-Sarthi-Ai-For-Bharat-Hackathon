"""
Personalized Learning Path Page
AI-powered study plan based on user history
"""

import streamlit as st
import json
from datetime import datetime
from monitoring_analytics import ResponseTimeTracker
from utils.theme_manager import apply_theme

# Apply theme globally
apply_theme()


def analyze_learning_history() -> dict:
    """
    Analyze user's conversation history to identify weak areas
    
    Returns:
        dict with analysis results
    """
    history = st.session_state.get('conversation_history', [])
    
    if not history:
        return {
            'status': 'no_data',
            'message': 'No learning history available yet. Start using Code Explanation or Voice Viva features!'
        }
    
    # Analyze interaction patterns
    code_explanations = [h for h in history if h['type'] == 'code_explanation']
    translations = [h for h in history if h['type'] == 'translation']
    viva_sessions = [h for h in history if h['type'] == 'viva']
    
    return {
        'status': 'success',
        'total_interactions': len(history),
        'code_explanations': len(code_explanations),
        'translations': len(translations),
        'viva_sessions': len(viva_sessions),
        'recent_topics': _extract_topics(history[-10:])  # Last 10 interactions
    }


def _extract_topics(history: list) -> list:
    """Extract programming topics from history"""
    topics = []
    keywords = {
        'loop': 'Loops & Iteration',
        'function': 'Functions',
        'class': 'Object-Oriented Programming',
        'array': 'Data Structures',
        'recursion': 'Recursion',
        'variable': 'Variables & Data Types',
        'if': 'Conditional Statements',
        'error': 'Error Handling',
        'algorithm': 'Algorithms'
    }
    
    for item in history:
        input_text = item.get('input', '').lower()
        for keyword, topic in keywords.items():
            if keyword in input_text and topic not in topics:
                topics.append(topic)
    
    return topics


def generate_study_plan(analysis: dict) -> str:
    """
    Generate personalized study plan using AWS Bedrock
    
    Args:
        analysis: Learning history analysis
        
    Returns:
        Hinglish study plan
    """
    if not st.session_state.translation_engine:
        return "⚠️ Translation engine not ready. Please check AWS Status page."
    
    # Build prompt for study plan generation
    prompt = f"""You are Code-Sarthi, an AI tutor for Indian engineering students. Based on the student's learning history, create a personalized study plan in Hinglish.

STUDENT LEARNING HISTORY:
- Total interactions: {analysis['total_interactions']}
- Code explanations requested: {analysis['code_explanations']}
- Translations done: {analysis['translations']}
- Viva sessions: {analysis['viva_sessions']}
- Recent topics studied: {', '.join(analysis['recent_topics']) if analysis['recent_topics'] else 'None'}

TASK:
Create a personalized 7-day study plan in Hinglish that:
1. Identifies weak areas based on the topics they've studied
2. Suggests specific topics to review
3. Recommends practice exercises
4. Provides motivation in natural Hinglish

Format the plan with clear sections:
- 📊 Analysis (unke strong aur weak points)
- 🎯 Focus Areas (kis topic par zyada dhyan dena chahiye)
- 📅 7-Day Plan (day-wise breakdown)
- 💡 Practice Recommendations
- 🚀 Motivation

Keep it encouraging and practical for Indian engineering students."""
    
    with st.spinner("🤖 AI tutor aapke liye personalized study plan bana raha hai..."):
        with ResponseTimeTracker(st.session_state.analytics, "learning_path"):
            st.session_state.analytics.track_api_call("bedrock")
            study_plan = st.session_state.translation_engine.translate(prompt)
    
    return study_plan


def render():
    """Personalized Learning Path page"""
    st.markdown("## 🎯 Personalized Learning Path")
    st.markdown("AI-powered study plan based on your learning history")
    
    st.markdown("<br>", unsafe_allow_html=True)
    
    # Analyze learning history
    analysis = analyze_learning_history()
    
    if analysis['status'] == 'no_data':
        st.markdown(f"""
            <div class='status-box status-info'>
                ℹ️ {analysis['message']}
            </div>
        """, unsafe_allow_html=True)
        
        st.markdown("""
            <div class='feature-card' style='text-align: center; padding: 3rem;'>
                <div class='feature-icon' style='font-size: 4rem;'>📚</div>
                <div class='feature-title' style='font-size: 1.8rem;'>Start Your Learning Journey</div>
                <div class='feature-description' style='font-size: 1.1rem; margin-top: 1rem;'>
                    Use Code Explanation, Text Translation, or Voice Viva features to build your learning history.
                    Once you have some interactions, come back here for a personalized study plan!
                </div>
            </div>
        """, unsafe_allow_html=True)
        return
    
    # Display learning statistics
    st.markdown("### 📊 Your Learning Statistics")
    
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.markdown(f"""
            <div class='metric-card'>
                <div class='metric-value'>{analysis['total_interactions']}</div>
                <div class='metric-label'>Total</div>
            </div>
        """, unsafe_allow_html=True)
    
    with col2:
        st.markdown(f"""
            <div class='metric-card'>
                <div class='metric-value'>{analysis['code_explanations']}</div>
                <div class='metric-label'>Code</div>
            </div>
        """, unsafe_allow_html=True)
    
    with col3:
        st.markdown(f"""
            <div class='metric-card'>
                <div class='metric-value'>{analysis['translations']}</div>
                <div class='metric-label'>Trans</div>
            </div>
        """, unsafe_allow_html=True)
    
    with col4:
        st.markdown(f"""
            <div class='metric-card'>
                <div class='metric-value'>{analysis['viva_sessions']}</div>
                <div class='metric-label'>Viva</div>
            </div>
        """, unsafe_allow_html=True)
    
    # Display recent topics
    if analysis['recent_topics']:
        st.markdown("<br>", unsafe_allow_html=True)
        st.markdown("### 📖 Recent Topics You've Studied")
        
        cols = st.columns(min(len(analysis['recent_topics']), 3))
        for idx, topic in enumerate(analysis['recent_topics'][:6]):
            with cols[idx % 3]:
                st.markdown(f"""
                    <div class='feature-card' style='padding: 1rem; text-align: center;'>
                        <div style='font-size: 1.5rem;'>✓</div>
                        <div style='font-size: 0.9rem; margin-top: 0.5rem;'>{topic}</div>
                    </div>
                """, unsafe_allow_html=True)
    
    # Generate study plan button
    st.markdown("<br><br>", unsafe_allow_html=True)
    
    col_btn1, col_btn2, col_btn3 = st.columns([1, 2, 1])
    with col_btn2:
        generate_btn = st.button("🚀 Generate My Personalized Study Plan", use_container_width=True)
    
    if generate_btn:
        study_plan = generate_study_plan(analysis)
        
        st.markdown("<br>", unsafe_allow_html=True)
        st.markdown("### 📋 Your Personalized Study Plan")
        
        st.markdown(f"""
            <div class='output-container' style='max-height: none;'>
{study_plan}
            </div>
        """, unsafe_allow_html=True)
        
        # Download button
        st.markdown("<br>", unsafe_allow_html=True)
        col_dl1, col_dl2, col_dl3 = st.columns([1, 2, 1])
        with col_dl2:
            plan_data = {
                'generated_at': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                'analysis': analysis,
                'study_plan': study_plan
            }
            st.download_button(
                label="📥 Download Study Plan",
                data=json.dumps(plan_data, indent=2, ensure_ascii=False),
                file_name=f"study_plan_{datetime.now().strftime('%Y%m%d')}.json",
                mime="application/json",
                use_container_width=True
            )


if __name__ == "__main__":
    render()
else:
    render()
