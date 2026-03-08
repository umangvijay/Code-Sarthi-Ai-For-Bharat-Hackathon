"""
Text Translation Page
Converts technical English to Hinglish
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
    """Enhanced text translation page"""
    st.markdown("## 🌐 Text Translation")
    st.markdown("Convert technical English content to natural Hinglish while preserving accuracy.")
    
    st.markdown("<br>", unsafe_allow_html=True)
    
    text = st.text_area(
        "English Technical Text",
        height=200,
        placeholder="Enter your technical text here...\n\nExample: A variable is a container that stores data values.",
        help="Enter any technical English text"
    )
    
    st.markdown("<br>", unsafe_allow_html=True)
    
    col_btn1, col_btn2, col_btn3 = st.columns([1, 2, 1])
    with col_btn2:
        translate_btn = st.button("🔄 Translate to Hinglish", use_container_width=True)

    if translate_btn:
        if not text.strip():
            st.markdown("""
                <div class='status-box status-error'>
                    ⚠️ Please enter some text first!
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

        with st.spinner("🔮 Translating..."):
            with ResponseTimeTracker(st.session_state.analytics, "translation"):
                st.session_state.analytics.track_api_call("bedrock")
                translated = st.session_state.translation_engine.translate(text)

        st.session_state.translation_count += 1
        _record_history("translation", text, translated)
        
        st.markdown("<br>", unsafe_allow_html=True)
        st.markdown("### 📝 Hinglish Output")
        st.markdown(f"""
            <div class='output-container'>
{translated}
            </div>
        """, unsafe_allow_html=True)


if __name__ == "__main__":
    render()
else:
    render()
