"""
Theme Manager Module
Manages application theme state and CSS injection for Light/Dark/System modes
"""

import streamlit as st


class ThemeManager:
    """Manages application theme state and CSS injection for Light/Dark/System modes"""
    
    # Theme color configuration
    THEME_COLORS = {
        'light': {
            'background': '#F4F5F7',
            'sidebar': '#FFFFFF',
            'text': '#1E1E1E',
            'text_secondary': '#666666',
            'border': '#E5E7EB',
            'card_bg': '#FFFFFF',
            'card_shadow': 'rgba(0, 0, 0, 0.05)',
            'hover_shadow': 'rgba(255, 138, 0, 0.15)',
            'gradient_bg': '#F4F5F7',
            'sidebar_gradient': '#FFFFFF',
        },
        'dark': {
            'background': '#0F0F0F',
            'sidebar': '#161616',
            'text': '#E0E0E0',
            'text_secondary': '#A0A0A0',
            'border': '#2A2A2A',
            'card_bg': '#1C1C1E',
            'card_shadow': 'rgba(0, 0, 0, 0.3)',
            'hover_shadow': 'rgba(255, 138, 0, 0.4)',
            'gradient_bg': 'linear-gradient(135deg, #0F0F0F 0%, #1A1A1A 100%)',
            'sidebar_gradient': 'linear-gradient(180deg, #161616 0%, #0F0F0F 100%)',
        },
        'accent': {
            'primary': '#FF8A00',
            'secondary': '#FF5E00',
            'gradient': 'linear-gradient(135deg, #FF8A00 0%, #FF5E00 100%)',
        }
    }
    
    def __init__(self):
        """Initialize theme manager with session state"""
        if 'theme_mode' not in st.session_state:
            st.session_state.theme_mode = 'system'
        if 'detected_system_theme' not in st.session_state:
            st.session_state.detected_system_theme = 'light'
    
    def detect_system_theme(self) -> str:
        """
        Detect operating system theme preference
        Returns 'light' or 'dark' based on stored preference
        Note: System theme detection via JavaScript has been simplified to avoid rendering issues
        """
        # Default to light theme if not detected
        return st.session_state.get('detected_system_theme', 'light')
    
    def get_current_theme(self) -> str:
        """
        Determine the active theme based on mode selection
        Returns 'light' or 'dark' based on mode and system preference
        """
        mode = st.session_state.get('theme_mode', 'system')
        
        if mode == 'system':
            return self.detect_system_theme()
        else:
            return mode
    
    def inject_theme_css(self) -> None:
        """
        Inject CSS styles for the current theme into Streamlit app
        Uses st.markdown with unsafe_allow_html=True
        """
        current_theme = self.get_current_theme()
        colors = self.THEME_COLORS[current_theme]
        accent = self.THEME_COLORS['accent']
        
        css = f"""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap');
    
    #MainMenu {{visibility: hidden;}}
    footer {{visibility: hidden;}}
    
    html, body, [class*="css"] {{
        font-family: 'Inter', -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
    }}
    
    * {{
        transition: background-color 300ms ease-in-out, 
                    color 300ms ease-in-out, 
                    border-color 300ms ease-in-out,
                    box-shadow 300ms ease-in-out;
    }}
    
    /* Root Streamlit containers - Force theme colors */
    [data-testid="stAppViewContainer"],
    .stApp {{
        background-color: {colors['background']} !important;
    }}
    
    .main {{
        background: {colors['gradient_bg']} !important;
        padding: 2rem;
        max-width: 100%;
        width: 100%;
    }}
    
    /* Responsive layout for sidebar collapse */
    @media (max-width: 768px) {{
        .main {{
            padding: 1rem;
        }}
    }}
    
    /* Ensure content container adjusts properly */
    .main .block-container {{
        max-width: 100%;
        padding-left: 2rem;
        padding-right: 2rem;
        transition: all 300ms ease-in-out;
    }}
    
    @keyframes fadeInUp {{
        from {{ opacity: 0; transform: translateY(30px); }}
        to {{ opacity: 1; transform: translateY(0); }}
    }}
    
    .main > div {{
        animation: fadeInUp 0.8s cubic-bezier(0.4, 0, 0.2, 1);
    }}
    
    .hero-header {{
        font-size: 3.5rem;
        font-weight: 700;
        background: {accent['gradient']};
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        background-clip: text;
        margin-bottom: 0.5rem;
        letter-spacing: -0.02em;
    }}
    
    .hero-subtitle {{
        font-size: 1.3rem;
        color: {colors['text_secondary']} !important;
        font-weight: 400;
        margin-bottom: 2rem;
    }}
    
    .feature-card {{
        background-color: {colors['card_bg']} !important;
        border: 1px solid {colors['border']} !important;
        border-radius: 16px;
        padding: 2rem;
        margin: 1rem 0;
        transition: all 0.4s cubic-bezier(0.4, 0, 0.2, 1);
        box-shadow: 0 4px 6px {colors['card_shadow']} !important;
        cursor: pointer;
        width: 100%;
        box-sizing: border-box;
    }}
    
    .feature-card:hover {{
        transform: translateY(-4px);
        border-color: {accent['primary']} !important;
        box-shadow: 0 12px 24px {colors['hover_shadow']} !important;
    }}
    
    /* Ensure columns stay responsive and properly sized */
    [data-testid="column"] {{
        min-width: 0;
        flex: 1 1 0;
        transition: all 300ms ease-in-out;
        padding: 0 0.5rem;
    }}
    
    /* Ensure horizontal layout stays intact */
    [data-testid="stHorizontalBlock"] {{
        display: flex !important;
        flex-direction: row !important;
        gap: 1rem;
        width: 100%;
        transition: all 300ms ease-in-out;
        align-items: stretch;
    }}
    
    /* Ensure feature cards fill their columns properly */
    [data-testid="column"] > div {{
        height: 100%;
    }}
    
    .feature-icon {{
        font-size: 2.5rem;
        margin-bottom: 1rem;
    }}
    
    .feature-title {{
        font-size: 1.25rem;
        font-weight: 600;
        color: {colors['text']} !important;
        margin-bottom: 0.5rem;
    }}
    
    .feature-description {{
        font-size: 0.95rem;
        color: {colors['text_secondary']} !important;
        line-height: 1.6;
    }}
    
    .metric-card {{
        background: {accent['gradient']};
        border-radius: 12px;
        padding: 1rem 0.5rem;
        text-align: center;
        transition: transform 0.3s ease;
        min-height: 80px;
        display: flex;
        flex-direction: column;
        justify-content: center;
        align-items: center;
    }}
    
    .metric-card:hover {{
        transform: scale(1.05);
    }}
    
    .metric-value {{
        font-size: 2rem;
        font-weight: 700;
        color: white;
        line-height: 1.2;
    }}
    
    .metric-label {{
        font-size: 0.75rem;
        color: rgba(255, 255, 255, 0.9);
        text-transform: uppercase;
        letter-spacing: 0.05em;
        margin-top: 0.25rem;
        white-space: nowrap;
        overflow: hidden;
        text-overflow: ellipsis;
        max-width: 100%;
    }}
    
    .status-box {{
        padding: 1rem;
        border-radius: 12px;
        margin: 1rem 0;
        border-left: 4px solid;
    }}
    
    .status-success {{
        background: rgba(72, 187, 120, 0.1);
        border-color: #48bb78;
        color: #2F855A;
    }}
    
    .status-error {{
        background: rgba(245, 101, 101, 0.1);
        border-color: #f56565;
        color: #C53030;
    }}
    
    .status-info {{
        background: rgba(0, 115, 187, 0.1);
        border-color: #0073BB;
        color: #2C5282;
    }}
    
    .stButton > button {{
        background: {accent['gradient']};
        color: white;
        border: none;
        border-radius: 8px;
        padding: 0.75rem 2rem;
        font-weight: 600;
        font-size: 1rem;
        transition: all 0.3s ease;
        box-shadow: 0 4px 6px rgba(255, 138, 0, 0.3);
    }}
    
    .stButton > button:hover {{
        transform: translateY(-2px);
        box-shadow: 0 6px 12px rgba(255, 138, 0, 0.4);
    }}
    
    .stTextArea textarea, .stTextInput input {{
        background: {colors['card_bg']} !important;
        border: 2px solid {colors['border']} !important;
        border-radius: 8px !important;
        color: {colors['text']} !important;
        font-family: 'Inter', monospace !important;
    }}
    
    .stTextArea textarea:focus, .stTextInput input:focus {{
        border-color: {accent['primary']} !important;
        box-shadow: 0 0 0 3px rgba(255, 138, 0, 0.1) !important;
    }}
    
    .output-container {{
        background: {colors['card_bg']} !important;
        border: 2px solid {colors['border']} !important;
        border-radius: 8px;
        padding: 1.5rem;
        margin: 1rem 0;
        color: {colors['text']} !important;
        font-family: 'Inter', monospace;
        line-height: 1.6;
        white-space: pre-wrap;
        word-wrap: break-word;
        max-height: 400px;
        overflow-y: auto;
    }}
    
    [data-testid="stSidebar"] {{
        background-color: {colors['sidebar_gradient']} !important;
        border-right: 1px solid {colors['border']} !important;
    }}
    
    h1, h2, h3 {{
        color: {colors['text']} !important;
        font-weight: 600;
    }}
    
    hr {{
        border-color: {colors['border']} !important;
        margin: 2rem 0;
    }}
    
    [data-testid="stFileUploader"] {{
        background: {colors['card_bg']} !important;
        border: 2px dashed {colors['border']} !important;
        border-radius: 12px;
        padding: 2rem;
    }}
    
    .stDownloadButton > button {{
        background: linear-gradient(135deg, #48bb78 0%, #38a169 100%) !important;
    }}
    
    [data-testid="stSidebar"] h1, 
    [data-testid="stSidebar"] h2, 
    [data-testid="stSidebar"] h3 {{
        color: {colors['text']} !important;
    }}
    
    [data-testid="stSidebar"] p,
    [data-testid="stSidebar"] label,
    [data-testid="stSidebar"] span {{
        color: {colors['text']} !important;
    }}
    
    .stCodeBlock {{
        background-color: {colors['card_bg']} !important;
        border: 1px solid {colors['border']} !important;
        border-radius: 8px;
    }}
    
    /* Fix text visibility for specific Streamlit components - TARGETED ONLY */
    
    /* Markdown content */
    [data-testid="stMarkdownContainer"] p,
    [data-testid="stMarkdownContainer"] li,
    [data-testid="stMarkdownContainer"] span:not([class*="css"]) {{
        color: {colors['text']} !important;
    }}
    
    .stMarkdown p,
    .stMarkdown li {{
        color: {colors['text']} !important;
    }}
    
    /* Widget labels - specific targeting */
    [data-testid="stWidgetLabel"] label,
    [data-testid="stWidgetLabel"] p {{
        color: {colors['text']} !important;
    }}
    
    /* File uploader */
    [data-testid="stFileUploader"] label,
    [data-testid="stFileUploader"] > div > div > div > small {{
        color: {colors['text']} !important;
    }}
    
    /* Selectbox */
    .stSelectbox > label,
    .stSelectbox > div > label {{
        color: {colors['text']} !important;
    }}
    
    /* Radio buttons */
    .stRadio > label,
    .stRadio > div > label {{
        color: {colors['text']} !important;
    }}
    
    /* Checkbox */
    .stCheckbox > label,
    .stCheckbox span {{
        color: {colors['text']} !important;
    }}
    
    /* Text input and textarea labels */
    .stTextInput > label,
    .stTextArea > label {{
        color: {colors['text']} !important;
    }}
    
    /* Multiselect */
    .stMultiSelect > label {{
        color: {colors['text']} !important;
    }}
    
    /* Expander */
    [data-testid="stExpander"] summary,
    [data-testid="stExpander"] p {{
        color: {colors['text']} !important;
    }}
    
    /* JSON display */
    [data-testid="stJson"],
    [data-testid="stJson"] * {{
        color: {colors['text']} !important;
    }}
    
    /* Spinner text */
    [data-testid="stSpinner"] > div {{
        color: {colors['text']} !important;
    }}
    
    /* Placeholder text */
    .stTextArea textarea::placeholder,
    .stTextInput input::placeholder {{
        color: {colors['text_secondary']} !important;
        opacity: 0.6;
    }}
    
    /* Caption text */
    .stCaption {{
        color: {colors['text_secondary']} !important;
    }}
</style>
"""
        st.markdown(css, unsafe_allow_html=True)
    
    def render_theme_toggle(self) -> None:
        """Render theme toggle control in sidebar with visual indicators"""
        st.sidebar.markdown("### 🎨 Theme")
        
        theme_options = {
            '☀️ Light': 'light',
            '🌙 Dark': 'dark',
            '💻 System': 'system'
        }
        
        current_mode = st.session_state.get('theme_mode', 'system')
        current_label = [k for k, v in theme_options.items() if v == current_mode][0]
        
        selected = st.sidebar.radio(
            "Select Theme",
            options=list(theme_options.keys()),
            index=list(theme_options.keys()).index(current_label),
            label_visibility="collapsed",
            key="theme_selector"
        )
        
        new_mode = theme_options[selected]
        if new_mode != current_mode:
            st.session_state.theme_mode = new_mode
            st.rerun()


# Global utility function for applying theme across all pages
def apply_theme() -> None:
    """
    Apply theme globally across all pages
    
    This function should be called at the top of every page file
    to ensure consistent theming throughout the application.
    
    Usage in page files:
        from utils.theme_manager import apply_theme
        apply_theme()
    """
    # Initialize theme manager if not exists
    if 'theme_manager' not in st.session_state or st.session_state.theme_manager is None:
        st.session_state.theme_manager = ThemeManager()
    
    # Inject theme CSS
    st.session_state.theme_manager.inject_theme_css()

