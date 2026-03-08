"""
Code Explanation Page
Provides Hinglish explanations for code snippets
"""

import streamlit as st
from datetime import datetime
from monitoring_analytics import ResponseTimeTracker
from utils.theme_manager import apply_theme

# Apply theme globally
apply_theme()


def _record_history(kind: str, user_text: str, output_text: str) -> None:
    """Record interaction in conversation history"""
    st.session_state.conversation_history.append(
        {
            "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "type": kind,
            "input": user_text,
            "output": output_text,
        }
    )


def render():
    """Enhanced code explanation page with modern UI"""
    # --- SAFETY INITIALIZATION ---
    if "translation_engine" not in st.session_state:
        from translation_engine import TranslationEngine
        st.session_state.translation_engine = TranslationEngine()
    # -----------------------------
    
    st.markdown("## 💡 Code Explanation")
    st.markdown("Paste your code below and get an instant explanation in natural Hinglish.")
    
    st.markdown("<br>", unsafe_allow_html=True)
    
    col1, col2 = st.columns([3, 2])
    
    with col1:
        code_input = st.text_area(
            "Your Code",
            height=300,
            placeholder="def factorial(n):\n    if n == 0:\n        return 1\n    return n * factorial(n-1)",
            help="Paste any code snippet here"
        )
    
    with col2:
        st.markdown("""
            <div class='feature-card' style='height: 280px;'>
                <div class='feature-icon' style='font-size: 2rem;'>✨</div>
                <div class='feature-title' style='font-size: 1.2rem;'>How it works</div>
                <div class='feature-description'>
                    <ol style='text-align: left; padding-left: 1.5rem;'>
                        <li>Paste your code in the editor</li>
                        <li>Click "Explain in Hinglish"</li>
                        <li>Get a clear explanation mixing Hindi & English</li>
                        <li>Technical terms stay in English</li>
                    </ol>
                </div>
            </div>
        """, unsafe_allow_html=True)
    
    st.markdown("<br>", unsafe_allow_html=True)
    
    col_btn1, col_btn2, col_btn3 = st.columns([1, 2, 1])
    with col_btn2:
        explain_btn = st.button("🚀 Explain in Hinglish", use_container_width=True)
    
    if explain_btn:
        if not code_input.strip():
            st.markdown("""
                <div class='status-box status-error'>
                    ⚠️ Please enter some code first!
                </div>
            """, unsafe_allow_html=True)
            return

        if st.session_state.translation_engine is None:
            st.markdown("""
                <div class='status-box status-error'>
                    ❌ Translation engine not ready. Please check the AWS Status page.
                </div>
            """, unsafe_allow_html=True)
            return

        prompt = (
            "Explain this code for an Indian engineering student in simple English first, "
            "then convert to natural Hinglish while preserving technical terms:\n\n"
            f"{code_input}"
        )

        with st.spinner("🔮 Generating explanation..."):
            with ResponseTimeTracker(st.session_state.analytics, "code_explanation"):
                st.session_state.analytics.track_api_call("bedrock")
                result = st.session_state.translation_engine.translate(prompt)

        st.session_state.translation_count += 1
        _record_history("code_explanation", code_input, result)
        
        st.markdown("<br>", unsafe_allow_html=True)
        st.markdown("### 📝 Explanation")
        st.markdown(f"""
            <div class='output-container'>
{result}
            </div>
        """, unsafe_allow_html=True)


# Streamlit multi-page apps call the script directly
if __name__ == "__main__":
    render()
else:
    render()
