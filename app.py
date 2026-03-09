"""
Code-Sarthi: Production-Ready SaaS Application
Enterprise Streamlit Web Application with Modern Architecture

Architecture:
- Multi-page structure for modularity
- Centralized state management
- Theme system with Light/Dark/System modes
- Performance optimizations (caching, retry logic)
- Cost optimizations (RAG heuristics, LRU cache)
"""

from datetime import datetime
import json

import streamlit as st
from streamlit_option_menu import option_menu

from aws_config import AWSConfig, USE_AWS
from monitoring_analytics import get_analytics
from translation_engine import TranslationEngine
from utils.theme_manager import ThemeManager

# Initialize aws_ready flag IMMEDIATELY to prevent AttributeError
if "aws_ready" not in st.session_state:
    st.session_state.aws_ready = False

# Page configuration
st.set_page_config(
    page_title="Code-Sarthi - Hinglish Code Assistant",
    page_icon="🎓",
    layout="wide",
    initial_sidebar_state="collapsed",  # Start collapsed to respect user preference
)


@st.cache_resource
def initialize_aws_config():
    """Initialize AWS configuration (cached per session)"""
    config = AWSConfig(region_name="us-east-1")
    return config


@st.cache_resource
def initialize_aws():
    """Initialize and validate AWS services (cached per session)"""
    config = initialize_aws_config()
    valid, message = config.validate_aws()
    print(f"AWS Validation: {message}")
    return valid, message


@st.cache_resource
def initialize_rag():
    """Initialize RAG engine (cached per session)"""
    try:
        from rag_engine import RAGEngine
        rag = RAGEngine()
        print("🟢 RAG Engine initialized successfully")
        return rag
    except Exception as e:
        print(f"🔴 Failed to initialize RAG Engine: {e}")
        return None


# Run AWS validation immediately and update session state
try:
    valid, message = initialize_aws()
    st.session_state.aws_ready = valid
    if valid:
        print("🟢 AWS services ready")
    else:
        print(f"🔴 AWS not ready: {message}")
except Exception as e:
    st.session_state.aws_ready = False
    print(f"🔴 AWS initialization failed: {e}")


# Initialize RAG engine immediately after AWS
if "rag_engine" not in st.session_state or st.session_state.rag_engine is None:
    try:
        st.session_state.rag_engine = initialize_rag()
        if st.session_state.rag_engine is None:
            print("⚠️ RAG Engine initialization returned None")
    except Exception as e:
        st.session_state.rag_engine = None
        print(f"🔴 RAG Engine initialization failed: {e}")


def initialize_session_state() -> None:
    """Initialize all session state variables"""
    defaults = {
        "theme_mode": "system",
        "detected_system_theme": "light",
        "theme_manager": None,
        "translation_engine": None,
        "aws_config": None,
        "aws_ready": False,
        "services_checked": False,
        "translation_count": 0,
        "pdf_count": 0,
        "conversation_history": [],
        "analytics": get_analytics(),
        "pdf_documents": [],
        "rag_engine": None,
        "viva_history": [],
    }
    for key, value in defaults.items():
        if key not in st.session_state:
            st.session_state[key] = value
    
    # Initialize theme manager
    if st.session_state.theme_manager is None:
        st.session_state.theme_manager = ThemeManager()


def check_aws_services():
    """Check AWS service availability and initialize clients"""
    if st.session_state.services_checked:
        return st.session_state.aws_ready, "Services already checked"

    try:
        # AWS validation already ran at module load
        # Just initialize the config and translation engine
        st.session_state.aws_config = initialize_aws_config()
        st.session_state.translation_engine = TranslationEngine()
        st.session_state.services_checked = True
        
        if st.session_state.aws_ready:
            return True, "✅ All required AWS services ready"
        else:
            return False, "⚠️ AWS services not available, using local mode"
            
    except Exception as exc:
        st.session_state.services_checked = True
        print(f"🔴 Service initialization failed: {exc}")
        # Try to initialize translation engine for local mode fallback
        try:
            st.session_state.translation_engine = TranslationEngine()
        except:
            pass
        return False, f"Service initialization failed: {exc}"


def render_sidebar() -> None:
    """Render sidebar with branding, theme toggle, and statistics"""
    with st.sidebar:
        # Branding
        st.markdown("""
            <div style='text-align: center; padding: 1rem 0 2rem 0;'>
                <div style='font-size: 2rem;'>🎓</div>
                <div style='font-size: 1.5rem; font-weight: 700; color: #FF8A00; margin-top: 0.5rem;'>Code-Sarthi</div>
                <div style='font-size: 0.9rem; color: #A0A0A0;'>Hinglish Code Assistant</div>
            </div>
        """, unsafe_allow_html=True)
        
        # Theme Toggle
        if st.session_state.theme_manager:
            st.session_state.theme_manager.render_theme_toggle()
            st.markdown("<hr style='margin: 1rem 0; border-color: #2A2A2A;'>", unsafe_allow_html=True)
        
        # Mode Indicator
        if st.session_state.aws_config:
            mode_display = st.session_state.aws_config.get_mode_display()
            aws_ready = st.session_state.get("aws_ready", False)
            
            if aws_ready:
                mode_class = "status-success"
                status_text = "🟢 AWS Cloud Mode"
            elif USE_AWS:
                mode_class = "status-error"
                status_text = "🔴 AWS Not Ready"
            else:
                mode_class = "status-info"
                status_text = "🔵 Local Mode"
                
            st.markdown(f"""
                <div class='status-box {mode_class}' style='text-align: center; margin-bottom: 1rem;'>
                    <strong>Mode:</strong> {status_text}
                </div>
            """, unsafe_allow_html=True)
        
        st.markdown("<hr style='margin: 2rem 0 1rem 0; border-color: #2A2A2A;'>", unsafe_allow_html=True)
        
        # Statistics
        st.markdown("### 📊 Stats")
        
        col1, col2 = st.columns(2)
        with col1:
            st.markdown(f"""
                <div class='metric-card'>
                    <div class='metric-value'>{st.session_state.translation_count}</div>
                    <div class='metric-label'>Trans</div>
                </div>
            """, unsafe_allow_html=True)
        
        with col2:
            st.markdown(f"""
                <div class='metric-card'>
                    <div class='metric-value'>{st.session_state.pdf_count}</div>
                    <div class='metric-label'>PDFs</div>
                </div>
            """, unsafe_allow_html=True)


def home_page() -> None:
    """Modern home page with hero section and feature cards"""
    st.markdown("""
        <div class='hero-header'>Welcome to Code-Sarthi</div>
        <div class='hero-subtitle'>Your AI-powered Hinglish coding companion for seamless learning</div>
    """, unsafe_allow_html=True)
    
    st.markdown("""
        <div class='status-box status-info' style='text-align: center; margin-bottom: 2rem;'>
            <strong>👇 Click any card below to get started!</strong>
        </div>
    """, unsafe_allow_html=True)
    
    # Feature cards with navigation buttons
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.markdown("""
            <div class='feature-card'>
                <div class='feature-icon'>💡</div>
                <div class='feature-title'>Code Explanation</div>
                <div class='feature-description'>
                    Get instant explanations of complex code in natural Hinglish, making programming concepts crystal clear.
                </div>
            </div>
        """, unsafe_allow_html=True)
        if st.button("Open Code Explanation", key="nav_code", use_container_width=True):
            st.switch_page("pages/1_💡_Code_Explanation.py")
    
    with col2:
        st.markdown("""
            <div class='feature-card'>
                <div class='feature-icon'>🌐</div>
                <div class='feature-title'>Smart Translation</div>
                <div class='feature-description'>
                    Convert technical English content to Hinglish while preserving accuracy and technical terminology.
                </div>
            </div>
        """, unsafe_allow_html=True)
        if st.button("Open Text Translation", key="nav_translation", use_container_width=True):
            st.switch_page("pages/2_🌐_Text_Translation.py")
    
    with col3:
        st.markdown("""
            <div class='feature-card'>
                <div class='feature-icon'>🎯</div>
                <div class='feature-title'>Learning Path</div>
                <div class='feature-description'>
                    Get personalized study plans based on your learning history and weak areas.
                </div>
            </div>
        """, unsafe_allow_html=True)
        if st.button("Open Learning Path", key="nav_learning", use_container_width=True):
            st.switch_page("pages/5_🎯_Learning_Path.py")
    
    # Second row
    col4, col5, col6 = st.columns(3)
    
    with col4:
        st.markdown("""
            <div class='feature-card'>
                <div class='feature-icon'>📚</div>
                <div class='feature-title'>PDF Processing</div>
                <div class='feature-description'>
                    Upload lab manuals and documentation for intelligent indexing and quick reference.
                </div>
            </div>
        """, unsafe_allow_html=True)
        if st.button("Open PDF Upload", key="nav_pdf", use_container_width=True):
            st.switch_page("pages/3_📚_PDF_Upload.py")
    
    with col5:
        st.markdown("""
            <div class='feature-card'>
                <div class='feature-icon'>🎤</div>
                <div class='feature-title'>Voice Viva</div>
                <div class='feature-description'>
                    Practice technical interviews with AI-powered voice interactions in your preferred language.
                </div>
            </div>
        """, unsafe_allow_html=True)
        if st.button("Open Voice Viva", key="nav_viva", use_container_width=True):
            st.switch_page("pages/4_🎤_Voice_Viva.py")
    
    with col6:
        st.markdown("""
            <div class='feature-card'>
                <div class='feature-icon'>⚡</div>
                <div class='feature-title'>Real-time AI</div>
                <div class='feature-description'>
                    Powered by AWS Bedrock for lightning-fast responses and enterprise-grade reliability.
                </div>
            </div>
        """, unsafe_allow_html=True)
        if st.button("View AWS Status", key="nav_aws", use_container_width=True):
            st.switch_page("pages/6_☁️_AWS_Status.py")
    
    # Export section
    if st.session_state.conversation_history:
        st.markdown("<hr>", unsafe_allow_html=True)
        st.markdown("### 📥 Export Your Work")
        
        col_export1, col_export2, col_export3 = st.columns([1, 2, 1])
        with col_export2:
            json_data = json.dumps(st.session_state.conversation_history, indent=2, ensure_ascii=False)
            st.download_button(
                label="📄 Download Conversation History",
                data=json_data,
                file_name=f"code_sarthi_history_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json",
                mime="application/json",
                use_container_width=True,
            )
    else:
        st.markdown("<hr>", unsafe_allow_html=True)
        st.markdown("""
            <div class='status-box status-success' style='text-align: center;'>
                <strong>🚀 Ready to Start:</strong> Choose a feature from the sidebar to begin your learning journey!
            </div>
        """, unsafe_allow_html=True)


def main() -> None:
    """Main application entry point"""
    # Initialize session state
    initialize_session_state()
    
    # Inject theme CSS
    if st.session_state.theme_manager:
        st.session_state.theme_manager.inject_theme_css()

    # Check AWS services on first load
    if not st.session_state.services_checked:
        with st.spinner("🔍 Checking AWS services..."):
            ok, msg = check_aws_services()
            if not ok:
                st.markdown(f"""
                    <div class='status-box status-error'>
                        ❌ {msg}
                    </div>
                """, unsafe_allow_html=True)
                st.markdown("""
                    <div class='status-box status-info'>
                        ℹ️ <strong>Setup Instructions:</strong><br>
                        1. Run <code>aws configure</code> in your terminal<br>
                        2. Enable Bedrock model access in AWS Console<br>
                        3. Refresh this page
                    </div>
                """, unsafe_allow_html=True)

    # Render sidebar
    render_sidebar()
    
    # Render home page
    home_page()


if __name__ == "__main__":
    main()
