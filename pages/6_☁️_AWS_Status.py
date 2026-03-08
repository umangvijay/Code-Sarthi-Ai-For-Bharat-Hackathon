"""
AWS Status Page
Monitor AWS service health and connectivity
"""

import streamlit as st
from utils.theme_manager import apply_theme

# Apply theme globally
apply_theme()


def render():
    """Enhanced AWS status page"""
    st.markdown("## ☁️ AWS Status")
    st.markdown("Monitor the health and connectivity of AWS services.")
    
    st.markdown("<br>", unsafe_allow_html=True)
    
    if st.session_state.aws_config is None:
        st.markdown("""
            <div class='status-box status-error'>
                ⚠️ AWS services not initialized yet. Please refresh the page or check your configuration.
            </div>
        """, unsafe_allow_html=True)
        return

    try:
        with st.spinner("🔍 Checking AWS services..."):
            status = st.session_state.aws_config.check_all_services()
        
        st.markdown("### Service Status")
        
        col1, col2, col3 = st.columns(3)
        
        services = [
            ("Credentials", status.get("credentials", False), "🔑"),
            ("Bedrock", status.get("bedrock", False), "🤖"),
            ("S3", status.get("s3", False), "📦"),
        ]
        
        for idx, (service, is_ok, icon) in enumerate(services):
            with [col1, col2, col3][idx]:
                status_class = "status-success" if is_ok else "status-error"
                status_text = "✅ Active" if is_ok else "❌ Inactive"
                st.markdown(f"""
                    <div class='feature-card' style='text-align: center;'>
                        <div style='font-size: 2rem;'>{icon}</div>
                        <div class='feature-title' style='font-size: 1.2rem; font-weight: 600; margin: 0.5rem 0; text-align: center;'>{service}</div>
                        <div class='status-box {status_class}' style='margin: 0;'>{status_text}</div>
                    </div>
                """, unsafe_allow_html=True)
        
        st.markdown("<br>", unsafe_allow_html=True)
        st.markdown("### Detailed Status")
        st.json(status)
        
    except Exception as exc:
        st.markdown(f"""
            <div class='status-box status-error'>
                ❌ Could not fetch AWS status: {exc}
            </div>
        """, unsafe_allow_html=True)


if __name__ == "__main__":
    render()
else:
    render()
