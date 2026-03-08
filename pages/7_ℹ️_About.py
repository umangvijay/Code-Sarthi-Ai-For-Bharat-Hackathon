"""
About Page
Information about Code-Sarthi
"""

import streamlit as st
from utils.theme_manager import apply_theme

# Apply theme globally
apply_theme()


def render():
    """Enhanced about page"""
    st.markdown("## ℹ️ About Code-Sarthi")
    
    st.markdown("<br>", unsafe_allow_html=True)
    
    st.markdown("""
        <div class='feature-card' style='padding: 2.5rem;'>
            <div class='feature-title' style='font-size: 2rem; text-align: center; margin-bottom: 1.5rem;'>
                🎓 Code-Sarthi
            </div>
            <div class='feature-description' style='font-size: 1.1rem; line-height: 1.8; text-align: center;'>
                Code-Sarthi is an AI-powered Hinglish coding assistant designed specifically for Indian engineering students.
                We bridge the language gap in technical education by providing explanations and translations that mix
                Hindi and English naturally, just like how students think and communicate.
            </div>
        </div>
    """, unsafe_allow_html=True)
    
    st.markdown("<br>", unsafe_allow_html=True)
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("""
            <div class='feature-card'>
                <div class='feature-icon'>🎯</div>
                <div class='feature-title'>Our Mission</div>
                <div class='feature-description'>
                    To make programming education accessible and comfortable for every Indian student
                    by supporting their natural way of thinking and communicating.
                </div>
            </div>
        """, unsafe_allow_html=True)
    
    with col2:
        st.markdown("""
            <div class='feature-card'>
                <div class='feature-icon'>⚡</div>
                <div class='feature-title'>Powered By</div>
                <div class='feature-description'>
                    Built with Streamlit and powered by AWS Bedrock AI for enterprise-grade
                    performance, reliability, and security.
                </div>
            </div>
        """, unsafe_allow_html=True)
    
    st.markdown("<br>", unsafe_allow_html=True)
    
    st.markdown("### 🚀 Production-Ready Architecture")
    
    st.markdown("""
        <div class='feature-card'>
            <div class='feature-description' style='text-align: left;'>
                <ul style='padding-left: 1.5rem; line-height: 2;'>
                    <li><strong>Multi-Page Structure:</strong> Modular architecture for scalability</li>
                    <li><strong>Performance Optimizations:</strong> LRU caching, tiktoken for accurate chunking</li>
                    <li><strong>Cost Optimizations:</strong> RAG heuristics, intelligent API usage</li>
                    <li><strong>Resilience:</strong> Retry logic with exponential backoff</li>
                    <li><strong>Theme System:</strong> Light/Dark/System modes with smooth transitions</li>
                    <li><strong>AI-Powered Learning:</strong> Personalized study plans based on history</li>
                </ul>
            </div>
        </div>
    """, unsafe_allow_html=True)


if __name__ == "__main__":
    render()
else:
    render()
