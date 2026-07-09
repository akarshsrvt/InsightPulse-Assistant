# Global styles and settings for the Streamlit app

PAGE_TITLE = "InsightPulse Assistant"
PAGE_ICON = "🧠"
LAYOUT = "wide"
INITIAL_SIDEBAR_STATE = "expanded"

# Custom CSS for the high-end premium light theme
CUSTOM_CSS = """
<style>
    /* Google Fonts */
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&family=Outfit:wght@300;400;500;600;700&display=swap');
    
    /* Global Styles */
    .stApp {
        background: radial-gradient(circle at top right, #f0f3ff, #f8fafc, #ffffff);
        color: #0f172a !important;
        font-family: 'Inter', sans-serif;
    }
    
    h1, h2, h3, .stHeader, .stMarkdown h1, .stMarkdown h2, .stMarkdown h3 {
        font-family: 'Outfit', sans-serif;
        color: #0f172a !important;
    }
    
    p, span, label, li, ul, ol {
        color: #334155 !important;
    }
    
    /* Header Gradient Banner */
    .header-banner {
        background: linear-gradient(135deg, rgba(79, 70, 229, 0.08) 0%, rgba(147, 51, 234, 0.08) 100%);
        border: 1px solid rgba(79, 70, 229, 0.15);
        border-radius: 16px;
        padding: 24px;
        margin-bottom: 24px;
        box-shadow: 0 4px 20px rgba(0, 0, 0, 0.03);
    }
    
    .header-banner h1 {
        margin: 0;
        font-size: 2.2rem;
        font-weight: 700;
        background: linear-gradient(to right, #4f46e5, #9333ea);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
    }
    
    .header-banner p {
        margin: 8px 0 0 0;
        color: #475569 !important;
        font-size: 1.05rem;
    }
    
    /* Sidebar Styling */
    section[data-testid="stSidebar"] {
        background-color: #f8fafc !important;
        border-right: 1px solid #e2e8f0 !important;
    }
    
    section[data-testid="stSidebar"] .stMarkdown h1, 
    section[data-testid="stSidebar"] .stMarkdown h2, 
    section[data-testid="stSidebar"] .stMarkdown h3 {
        color: #0f172a !important;
        font-weight: 600;
    }
    
    section[data-testid="stSidebar"] label,
    section[data-testid="stSidebar"] p,
    section[data-testid="stSidebar"] span {
        color: #334155 !important;
    }
    
    /* Input field styling */
    div[data-baseweb="input"] {
        background-color: #ffffff !important;
        border: 1px solid #cbd5e1 !important;
        color: #0f172a !important;
        border-radius: 8px !important;
    }
    
    textarea, input {
        color: #0f172a !important;
    }
    
    /* Buttons in Sidebar styling */
    .stButton>button {
        background: #ffffff !important;
        border: 1px solid #e2e8f0 !important;
        color: #475569 !important;
        border-radius: 8px !important;
        transition: all 0.2s ease-in-out !important;
        text-align: left !important;
        padding: 10px 16px !important;
        width: 100% !important;
        box-shadow: 0 1px 2px rgba(0, 0, 0, 0.05) !important;
    }
    
    .stButton>button:hover {
        background: linear-gradient(135deg, rgba(79, 70, 229, 0.06) 0%, rgba(147, 51, 234, 0.06) 100%) !important;
        border-color: #818cf8 !important;
        color: #4f46e5 !important;
        transform: translateY(-1px);
        box-shadow: 0 4px 12px rgba(79, 70, 229, 0.08) !important;
    }
    
    /* Custom style for native chat messages */
    div[data-testid="stChatMessage"] {
        background-color: #ffffff !important;
        border: 1px solid #e2e8f0 !important;
        border-radius: 16px !important;
        margin-bottom: 12px !important;
        padding: 16px !important;
        box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.03), 0 2px 4px -1px rgba(0, 0, 0, 0.02) !important;
    }
    
    div[data-testid="stChatMessage"] p, 
    div[data-testid="stChatMessage"] li, 
    div[data-testid="stChatMessage"] span,
    div[data-testid="stChatMessage"] h3,
    div[data-testid="stChatMessage"] strong {
        color: #1e293b !important;
    }
    
    div[data-testid="stChatMessage"][aria-label="Chat message from user"] {
        background-color: #e0e7ff !important;
        border: 1px solid #c7d2fe !important;
    }
    
    div[data-testid="stChatMessage"][aria-label="Chat message from user"] p,
    div[data-testid="stChatMessage"][aria-label="Chat message from user"] span,
    div[data-testid="stChatMessage"][aria-label="Chat message from user"] strong {
        color: #1e1b4b !important;
    }
</style>
"""
