import streamlit as st
import pandas as pd
import gspread
from google.oauth2.service_account import Credentials
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import numpy as np
from datetime import datetime, timedelta
import warnings
warnings.filterwarnings('ignore')

# --- KONFIGURASI HALAMAN ---
st.set_page_config(
    page_title="🚀 PPSA Analytics Dashboard",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded"
)

# --- FUNGSI HELPER UNTUK SVG ICON ---
def get_svg_icon(icon_name, size=24, color="#667eea"):
    icons = {
        "dashboard": f'<svg width="{size}" height="{size}" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg"><path d="M3 13h2v8H3zm4-8h2v16H7zm4-2h2v18h-2zm4 4h2v14h-2zm4-2h2v16h-2z" fill="{color}"/></svg>',
        "psm": f'<svg width="{size}" height="{size}" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg"><path d="M12 2L2 7v10c0 5.55 3.84 10.74 9 12 5.16-1.26 9-6.45 9-12V7l-10-5z" fill="{color}"/></svg>',
        "pwp": f'<svg width="{size}" height="{size}" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg"><path d="M7 18c-1.1 0-1.99.9-1.99 2S5.9 22 7 22s2-.9 2-2-.9-2-2-2zM1 2v2h2l3.6 7.59-1.35 2.45c-.16.28-.25.61-.25.96 0 1.1.9 2 2 2h12v-2H7.42c-.14 0-.25-.11-.25-.25l.03-.12.9-1.63h7.45c.75 0 1.41-.41 1.75-1.03l3.58-6.49c.08-.14.12-.31.12-.48 0-.55-.45-1-1-1H5.21l-.94-2H1zm16 16c-1.1 0-1.99.9-1.99 2s.89 2 1.99 2 2-.9 2-2-.9-2-2-2z" fill="{color}"/></svg>',
        "sg": f'<svg width="{size}" height="{size}" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg"><path d="M12 2C6.48 2 2 6.48 2 12s4.48 10 10 10 10-4.48 10-10S17.52 2 12 2zm-2 15l-5-5 1.41-1.41L10 14.17l7.59-7.59L19 8l-9 9z" fill="{color}"/></svg>',
        "apc": f'<svg width="{size}" height="{size}" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg"><path d="M20 4H4c-1.11 0-1.99.89-1.99 2L2 18c0 1.11.89 2 2 2h16c1.11 0 2-.89 2-2V6c0-1.11-.89-2-2-2zm0 14H4v-6h16v6zm0-10H4V6h16v2z" fill="{color}"/></svg>',
        "tebus": f'<svg width="{size}" height="{size}" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg"><path d="M11.8 10.9c-2.27-.59-3-1.2-3-2.15 0-1.09 1.01-1.85 2.7-1.85 1.78 0 2.44.85 2.5 2.1h2.21c-.07-1.72-1.12-3.3-3.21-3.81V3h-3v2.16c-1.94.42-3.5 1.68-3.5 3.61 0 2.31 1.91 3.46 4.7 4.13 2.5.6 3 1.48 3 2.41 0 .69-.49 1.79-2.7 1.79-2.06 0-2.87-.92-2.98-2.1h-2.2c.12 2.19 1.76 3.42 3.68 3.83V21h3v-2.15c1.95-.37 3.5-1.5 3.5-3.55 0-2.84-2.43-3.81-4.7-4.4z" fill="{color}"/></svg>',
        "trophy": f'<svg width="{size}" height="{size}" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg"><path d="M19 5h-2V3H7v2H5c-1.1 0-2 .9-2 2v1c0 2.55 1.92 4.63 4.39 4.94A5.01 5.01 0 0 0 11 15.9V19H7v2h10v-2h-4v-3.1a5.01 5.01 0 0 0 3.61-2.96C19.08 12.63 21 10.55 21 8V7c0-1.1-.9-2-2-2zM5 8V7h2v3.82C5.84 10.4 5 9.3 5 8zm14 0c0 1.3-.84 2.4-2 2.82V7h2v1z" fill="{color}"/></svg>',
        "gold": f'<svg width="{size}" height="{size}" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg"><path d="M12 2l3.09 6.26L22 9.27l-5 4.87 1.18 6.88L12 17.77l-6.18 3.25L7 14.14 2 9.27l6.91-1.01L12 2z" fill="#FFD700"/></svg>',
        "silver": f'<svg width="{size}" height="{size}" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg"><path d="M12 2l3.09 6.26L22 9.27l-5 4.87 1.18 6.88L12 17.77l-6.18 3.25L7 14.14 2 9.27l6.91-1.01L12 2z" fill="#C0C0C0"/></svg>',
        "bronze": f'<svg width="{size}" height="{size}" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg"><path d="M12 2l3.09 6.26L22 9.27l-5 4.87 1.18 6.88L12 17.77l-6.18 3.25L7 14.14 2 9.27l6.91-1.01L12 2z" fill="#CD7F32"/></svg>',
        "alert": f'<svg width="{size}" height="{size}" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg"><path d="M1 21h22L12 2 1 21zm12-3h-2v-2h2v2zm0-4h-2v-4h2v4z" fill="{color}"/></svg>',
        "insights": f'<svg width="{size}" height="{size}" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg"><path d="M9 11H7v9h2v-9zm4-4h-2v13h2V7zm4-4h-2v17h2V3z" fill="{color}"/></svg>',
        "correlation": f'<svg width="{size}" height="{size}" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg"><path d="M19 3H5c-1.1 0-2 .9-2 2v14c0 1.1.9 2 2 2h14c1.1 0 2-.9 2-2V5c0-1.1-.9-2-2-2zM9 17H7v-7h2v7zm4 0h-2V7h2v10zm4 0h-2v-4h2v4z" fill="{color}"/></svg>',
        "shift": f'<svg width="{size}" height="{size}" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg"><path d="M11.99 2C6.47 2 2 6.48 2 12s4.47 10 9.99 10C17.52 22 22 17.52 22 12S17.52 2 11.99 2zM12 20c-4.42 0-8-3.58-8-8s3.58-8 8-8 8 3.58 8 8-3.58 8-8 8zm.5-13H11v6l5.25 3.15.75-1.23-4.5-2.67z" fill="{color}"/></svg>',
        "calendar": f'<svg width="{size}" height="{size}" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg"><path d="M19 3h-1V1h-2v2H8V1H6v2H5c-1.11 0-1.99.9-1.99 2L3 19c0 1.1.89 2 2 2h14c1.1 0 2-.9 2-2V5c0-1.1-.9-2-2-2zm0 16H5V8h14v11zM7 10h5v5H7z" fill="{color}"/></svg>',
        "users": f'<svg width="{size}" height="{size}" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg"><path d="M16 11c1.66 0 2.99-1.34 2.99-3S17.66 5 16 5c-1.66 0-3 1.34-3 3s1.34 3 3 3zm-8 0c1.66 0 2.99-1.34 2.99-3S9.66 5 8 5C6.34 5 5 6.34 5 8s1.34 3 3 3zm0 2c-2.33 0-7 1.17-7 3.5V19h14v-2.5c0-2.33-4.67-3.5-7-3.5zm8 0c-.29 0-.62.02-.97.05 1.16.84 1.97 1.97 1.97 3.45V19h6v-2.5c0-2.33-4.67-3.5-7-3.5z" fill="{color}"/></svg>',
        "trending": f'<svg width="{size}" height="{size}" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg"><path d="M16 6l2.29 2.29-4.88 4.88-4-4L2 16.59 3.41 18l6-6 4 4 6.3-6.29L22 12V6z" fill="{color}"/></svg>',
        "star": f'<svg width="{size}" height="{size}" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg"><path d="M12 17.27L18.18 21l-1.64-7.03L22 9.24l-7.19-.61L12 2 9.19 8.63 2 9.24l5.46 4.73L5.82 21z" fill="{color}"/></svg>',
        "target": f'<svg width="{size}" height="{size}" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg"><path d="M12 2C6.48 2 2 6.48 2 12s4.48 10 10 10 10-4.48 10-10S17.52 2 12 2zm0 18c-4.41 0-8-3.59-8-8s3.59-8 8-8 8 3.59 8 8-3.59 8-8 8zm0-14c-3.31 0-6 2.69-6 6s2.69 6 6 6 6-2.69 6-6-2.69-6-6-6zm0 10c-2.21 0-4-1.79-4-4s1.79-4 4-4 4 1.79 4 4-1.79 4-4 4zm0-6c-1.1 0-2 .9-2 2s.9 2 2 2 2-.9 2-2-.9-2-2-2z" fill="{color}"/></svg>',
        "chart": f'<svg width="{size}" height="{size}" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg"><path d="M3.5 18.49l6-6.01 4 4L22 6.92l-1.41-1.41-7.09 7.97-4-4L2 16.99z" fill="{color}"/></svg>',
        "growth": f'<svg width="{size}" height="{size}" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg"><path d="M16 6l2.29 2.29-4.88 4.88-4-4L2 16.59 3.41 18l6-6 4 4 6.3-6.29L22 12V6z" fill="{color}"/></svg>',
        "analytics": f'<svg width="{size}" height="{size}" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg"><path d="M19 3H5c-1.1 0-2 .9-2 2v14c0 1.1.9 2 2 2h14c1.1 0 2-.9 2-2V5c0-1.1-.9-2-2-2zM9 17H7v-7h2v7zm4 0h-2V7h2v10zm4 0h-2v-4h2v4z" fill="{color}"/></svg>'
    }
    return icons.get(icon_name, "")

# --- CSS KUSTOM YANG LEBIH MODERN ---
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;800&display=swap');

:root {
    --primary-gradient: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
    --secondary-gradient: linear-gradient(135deg, #f093fb 0%, #f5576c 100%);
    --success-gradient: linear-gradient(135deg, #4facfe 0%, #00f2fe 100%);
    --warning-gradient: linear-gradient(135deg, #fa709a 0%, #fee140 100%);
    --card-shadow: 0 10px 40px rgba(0, 0, 0, 0.1);
    --card-shadow-hover: 0 20px 60px rgba(102, 126, 234, 0.25);
    --border-radius: 20px;
    --border-radius-sm: 12px;
}

* {
    font-family: 'Inter', -apple-system, BlinkMacSystemFont, sans-serif;
}

.stApp {
    background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
    background-attachment: fixed;
}

.main .block-container {
    padding: 2rem 1rem;
    max-width: 1600px;
    margin: 0 auto;
}

/* DASHBOARD HEADER */
.dashboard-header {
    background: linear-gradient(135deg, rgba(255,255,255,0.95) 0%, rgba(248,249,255,0.95) 100%);
    backdrop-filter: blur(20px);
    padding: 3rem;
    border-radius: var(--border-radius);
    box-shadow: var(--card-shadow);
    margin-bottom: 2rem;
    border: 1px solid rgba(255, 255, 255, 0.3);
    text-align: center;
    position: relative;
    overflow: hidden;
}

.dashboard-header::before {
    content: '';
    position: absolute;
    top: 0;
    left: 0;
    right: 0;
    height: 5px;
    background: var(--primary-gradient);
}

.main-title {
    font-size: 3.5rem;
    background: var(--primary-gradient);
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
    background-clip: text;
    font-weight: 800;
    margin-bottom: 1rem;
    letter-spacing: -1px;
    display: flex;
    align-items: center;
    justify-content: center;
    gap: 1rem;
    animation: slideInFromTop 0.8s ease-out;
}

.subtitle {
    color: #64748b;
    font-size: 1.2rem;
    font-weight: 500;
    line-height: 1.6;
    max-width: 900px;
    margin: 0 auto;
    animation: fadeInUp 0.8s ease-out 0.2s both;
}

/* METRIC CARDS */
.metric-card {
    background: linear-gradient(135deg, rgba(255,255,255,0.95) 0%, rgba(248,249,255,0.95) 100%);
    backdrop-filter: blur(20px);
    border-radius: var(--border-radius-sm);
    padding: 2rem 1.5rem;
    box-shadow: var(--card-shadow);
    border: 1px solid rgba(102, 126, 234, 0.1);
    transition: all 0.4s cubic-bezier(0.175, 0.885, 0.32, 1.275);
    position: relative;
    overflow: hidden;
    height: 100%;
}

.metric-card::before {
    content: '';
    position: absolute;
    top: 0;
    left: 0;
    width: 4px;
    height: 100%;
    background: var(--primary-gradient);
}

.metric-card:hover {
    transform: translateY(-10px) scale(1.02);
    box-shadow: var(--card-shadow-hover);
}

.metric-label {
    font-size: 0.875rem;
    color: #64748b;
    font-weight: 700;
    text-transform: uppercase;
    letter-spacing: 1px;
    margin-bottom: 1rem;
    display: flex;
    align-items: center;
    gap: 0.75rem;
}

.metric-value {
    font-size: 2.75rem;
    font-weight: 800;
    background: var(--primary-gradient);
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
    background-clip: text;
    line-height: 1.1;
}

/* SPECIAL CARDS */
.total-ppsa-card {
    background: var(--primary-gradient);
    border-radius: var(--border-radius);
    padding: 3rem 2rem;
    box-shadow: 0 25px 70px rgba(102, 126, 234, 0.4);
    text-align: center;
    position: relative;
    overflow: hidden;
    transition: all 0.3s ease;
}

.total-ppsa-card:hover {
    transform: translateY(-5px);
    box-shadow: 0 35px 90px rgba(102, 126, 234, 0.5);
}

.total-ppsa-card::before {
    content: '';
    position: absolute;
    top: -50%;
    right: -50%;
    width: 200%;
    height: 200%;
    background: radial-gradient(circle, rgba(255,255,255,0.15) 0%, transparent 70%);
    animation: pulse 4s ease-in-out infinite;
}

.total-ppsa-label {
    font-size: 1.1rem;
    color: rgba(255, 255, 255, 0.95);
    font-weight: 700;
    text-transform: uppercase;
    letter-spacing: 2px;
    margin-bottom: 1.5rem;
    display: flex;
    align-items: center;
    justify-content: center;
    gap: 1rem;
}

.total-ppsa-value {
    font-size: 4.5rem;
    font-weight: 900;
    color: #ffffff;
    text-shadow: 0 4px 20px rgba(0, 0, 0, 0.3);
    position: relative;
    z-index: 1;
}

/* CONTENT CONTAINERS */
.content-container {
    background: linear-gradient(135deg, rgba(255,255,255,0.95) 0%, rgba(248,249,255,0.95) 100%);
    backdrop-filter: blur(20px);
    padding: 2.5rem;
    border-radius: var(--border-radius);
    box-shadow: var(--card-shadow);
    margin-bottom: 2rem;
    border: 1px solid rgba(255, 255, 255, 0.3);
    animation: fadeInUp 0.6s ease-out;
}

.section-header {
    font-size: 2rem;
    font-weight: 800;
    color: #1e293b;
    margin-bottom: 2rem;
    padding-bottom: 1rem;
    border-bottom: 3px solid transparent;
    background: linear-gradient(90deg, #667eea, #764ba2) bottom / 100% 3px no-repeat;
    position: relative;
}

.section-header::before {
    content: '';
    position: absolute;
    bottom: -3px;
    left: 0;
    width: 80px;
    height: 3px;
    background: var(--secondary-gradient);
    border-radius: 2px;
}

/* TOP PERFORMER CARDS */
.top-performer-card {
    background: linear-gradient(135deg, rgba(255,255,255,0.95) 0%, rgba(248,249,255,0.95) 100%);
    backdrop-filter: blur(20px);
    border-radius: var(--border-radius-sm);
    padding: 2rem 1.5rem;
    box-shadow: var(--card-shadow);
    border: 1px solid rgba(102, 126, 234, 0.1);
    transition: all 0.4s cubic-bezier(0.175, 0.885, 0.32, 1.275);
    position: relative;
    overflow: hidden;
    text-align: center;
    height: 100%;
}

.top-performer-card:hover {
    transform: translateY(-8px) scale(1.05);
    box-shadow: var(--card-shadow-hover);
}

.top-performer-icon {
    font-size: 3.5rem;
    margin-bottom: 1.5rem;
    filter: drop-shadow(0 4px 12px rgba(0,0,0,0.15));
}

.top-performer-name {
    font-size: 1.3rem;
    font-weight: 700;
    color: #1e293b;
    margin-bottom: 0.75rem;
}

.top-performer-score {
    font-size: 2.2rem;
    font-weight: 800;
    background: var(--primary-gradient);
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
    background-clip: text;
}

/* INSIGHTS CARDS */
.insight-card {
    background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
    border-radius: var(--border-radius-sm);
    padding: 1.5rem;
    color: white;
    margin-bottom: 1rem;
    box-shadow: var(--card-shadow);
    transition: all 0.3s ease;
}

.insight-card:hover {
    transform: translateX(10px);
    box-shadow: var(--card-shadow-hover);
}

.insight-title {
    font-weight: 700;
    font-size: 1.1rem;
    margin-bottom: 0.5rem;
    display: flex;
    align-items: center;
    gap: 0.5rem;
}

.insight-text {
    font-size: 0.95rem;
    opacity: 0.9;
    line-height: 1.5;
}

/* ALERT CARDS */
.alert-card {
    background: linear-gradient(135deg, #fa709a 0%, #fee140 100%);
    border-radius: var(--border-radius-sm);
    padding: 1.5rem;
    color: #1e293b;
    margin-bottom: 1rem;
    box-shadow: var(--card-shadow);
    border-left: 5px solid #ef4444;
}

.alert-title {
    font-weight: 700;
    font-size: 1.1rem;
    margin-bottom: 0.5rem;
    display: flex;
    align-items: center;
    gap: 0.5rem;
}

/* SIDEBAR STYLING */
.css-1d391kg, [data-testid="stSidebar"] {
    background: linear-gradient(180deg, rgba(255,255,255,0.95) 0%, rgba(248,249,255,0.95) 100%);
    backdrop-filter: blur(20px);
    border-right: 1px solid rgba(102, 126, 234, 0.2);
}

/* BUTTONS */
.stButton > button {
    background: var(--primary-gradient);
    color: white;
    border: none;
    border-radius: var(--border-radius-sm);
    padding: 0.75rem 2rem;
    font-weight: 600;
    font-size: 1rem;
    transition: all 0.3s ease;
    box-shadow: 0 4px 15px rgba(102, 126, 234, 0.3);
}

.stButton > button:hover {
    transform: translateY(-3px);
    box-shadow: 0 8px 25px rgba(102, 126, 234, 0.4);
}

/* ANIMATIONS */
@keyframes fadeInUp {
    from {
        opacity: 0;
        transform: translateY(30px);
    }
    to {
        opacity: 1;
        transform: translateY(0);
    }
}

@keyframes slideInFromTop {
    from {
        opacity: 0;
        transform: translateY(-50px);
    }
    to {
        opacity: 1;
        transform: translateY(0);
    }
}

@keyframes pulse {
    0%, 100% {
        transform: scale(1);
        opacity: 0.6;
    }
    50% {
        transform: scale(1.1);
        opacity: 0.8;
    }
}

/* SCROLLBAR */
::-webkit-scrollbar {
    width: 12px;
    height: 12px;
}

::-webkit-scrollbar-track {
    background: rgba(241, 245, 249, 0.5);
    border-radius: 10px;
}

::-webkit-scrollbar-thumb {
    background: var(--primary-gradient);
    border-radius: 10px;
    border: 2px solid transparent;
    background-clip: content-box;
}

::-webkit-scrollbar-thumb:hover {
    background: var(--secondary-gradient);
    background-clip: content-box;
}

/* HIDE STREAMLIT ELEMENTS */
#MainMenu, footer, header {
    visibility: hidden;
}

/* RESPONSIVE */
@media (max-width: 768px) {
    .main-title {
        font-size: 2.5rem;
        flex-direction: column;
        gap: 0.5rem;
    }
    
    .metric-card {
        padding: 1.5rem 1rem;
    }
    
    .content-container {
        padding: 1.5rem;
    }
}
</style>
""", unsafe_allow_html=True)

# --- FUNGSI DATA ---
@st.cache_data(ttl=600)
def load_data_from_gsheet():
    """Load data from Google Sheets dengan error handling yang lebih baik"""
    try:
        scopes = ['https://www.googleapis.com/auth/spreadsheets', 'https://www.googleapis.com/auth/drive']
        creds = Credentials.from_service_account_info(st.secrets["gcp_service_account"], scopes=scopes)
        client = gspread.authorize(creds)
        spreadsheet = client.open("Dashboard")
        worksheet = spreadsheet.get_worksheet(0)
        data = worksheet.get_all_values()
        
        if not data:
            return pd.DataFrame()
            
        df = pd.DataFrame(data[1:], columns=data[0])
        return df
    except Exception as e:
        st.error(f"❌ Gagal mengambil data: {str(e)}")
        return pd.DataFrame()

def process_data(df):
    """Process data dengan validasi dan cleaning yang lebih baik"""
    if df.empty:
        return df
    
    # Process dates
    if 'TANGGAL' in df.columns:
        df['TANGGAL'] = pd.to_datetime(df['TANGGAL'], format='%d/%m/%Y', errors='coerce')
        df['HARI'] = df['TANGGAL'].dt.day_name()
        df['BULAN'] = df['TANGGAL'].dt.month_name()
        df['MINGGU'] = df['TANGGAL'].dt.isocalendar().week
        
        hari_map = {
            'Monday': 'Senin', 'Tuesday': 'Selasa', 'Wednesday': 'Rabu',
            'Thursday': 'Kamis', 'Friday': 'Jumat', 'Saturday': 'Sabtu', 'Sunday': 'Minggu'
        }
        df['HARI'] = df['HARI'].map(hari_map)
    
    # Process shift column - PERBAIKAN UTAMA
    if 'SHIFT' in df.columns:
        # Convert shift to string if it's not already
        df['SHIFT'] = df['SHIFT'].astype(str)
        
        # Map shift values to meaningful names
        shift_map = {
            '1': 'Shift 1 (Pagi)',
            '2': 'Shift 2 (Siang)',
            '3': 'Shift 3 (Malam)'
        }
        df['SHIFT'] = df['SHIFT'].map(shift_map)
        
        # Handle any unmapped values
        df['SHIFT'] = df['SHIFT'].fillna('Unknown')
    elif 'shift' in df.columns:
        # Convert shift to numeric if it's not already
        df['shift'] = pd.to_numeric(df['shift'], errors='coerce')
        
        # Map shift values to meaningful names
        shift_map = {
            1: 'Shift 1 (Pagi)',
            2: 'Shift 2 (Siang)',
            3: 'Shift 3 (Malam)'
        }
        df['SHIFT'] = df['shift'].map(shift_map)
        
        # Handle any unmapped values
        df['SHIFT'] = df['SHIFT'].fillna('Unknown')
    else:
        # If no shift column, create a default shift based on random assignment for demo
        np.random.seed(42)
        df['SHIFT'] = np.random.choice(['Shift 1 (Pagi)', 'Shift 2 (Siang)', 'Shift 3 (Malam)'], size=len(df))

    # Process numeric columns
    numeric_cols = [
        'PSM Target', 'PSM Actual', 'BOBOT PSM',
        'PWP Target', 'PWP Actual', 'BOBOT PWP',
        'SG Target', 'SG Actual', 'BOBOT SG',
        'APC Target', 'APC Actual', 'BOBOT APC',
        'TARGET TEBUS 2500', 'ACTUAL TEBUS 2500'
    ]
    
    for col in numeric_cols:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors='coerce').fillna(0)

    # Calculate ACV (Achievement vs Target)
    def calculate_acv(actual, target):
        return (actual / target * 100) if target != 0 else 0.0

    df['(%) PSM ACV'] = df.apply(lambda row: calculate_acv(row['PSM Actual'], row['PSM Target']), axis=1)
    df['(%) PWP ACV'] = df.apply(lambda row: calculate_acv(row['PWP Actual'], row['PWP Target']), axis=1)
    df['(%) SG ACV'] = df.apply(lambda row: calculate_acv(row['SG Actual'], row['SG Target']), axis=1)
    df['(%) APC ACV'] = df.apply(lambda row: calculate_acv(row['APC Actual'], row['APC Target']), axis=1)
    df['(%) ACV TEBUS 2500'] = df.apply(lambda row: calculate_acv(row['ACTUAL TEBUS 2500'], row['TARGET TEBUS 2500']), axis=1)

    # Calculate weighted scores
    df['SCORE PSM'] = (df['(%) PSM ACV'] * df['BOBOT PSM']) / 100
    df['SCORE PWP'] = (df['(%) PWP ACV'] * df['BOBOT PWP']) / 100
    df['SCORE SG'] = (df['(%) SG ACV'] * df['BOBOT SG']) / 100
    df['SCORE APC'] = (df['(%) APC ACV'] * df['BOBOT APC']) / 100

    # Calculate total PPSA score
    score_cols = ['SCORE PSM', 'SCORE PWP', 'SCORE SG', 'SCORE APC']
    df['TOTAL SCORE PPSA'] = df[score_cols].sum(axis=1)
    
    # Remove rows with NaN in critical columns
    df = df.dropna(subset=['SHIFT', 'TOTAL SCORE PPSA'])
    
    return df

def calculate_overall_ppsa_breakdown(df):
    """
    Calculate overall PPSA breakdown dengan metode yang benar:
    - PSM, PWP, SG: Menggunakan SUM (kumulatif)
    - APC: Menggunakan AVERAGE (rata-rata)
    """
    if df.empty:
        return {'total': 0.0, 'psm': 0.0, 'pwp': 0.0, 'sg': 0.0, 'apc': 0.0}
    
    weights = {'PSM': 20, 'PWP': 25, 'SG': 30, 'APC': 25}
    scores = {'psm': 0.0, 'pwp': 0.0, 'sg': 0.0, 'apc': 0.0}
    
    # For PSM, PWP, SG - use SUM aggregation (metrik kumulatif)
    for comp in ['PSM', 'PWP', 'SG']:
        total_target = df[f'{comp} Target'].sum()
        total_actual = df[f'{comp} Actual'].sum()
        if total_target > 0:
            acv = (total_actual / total_target) * 100
            scores[comp.lower()] = (acv * weights[comp]) / 100
    
    # For APC - use AVERAGE aggregation (metrik rata-rata)
    avg_target_apc = df['APC Target'].mean()
    avg_actual_apc = df['APC Actual'].mean()
    if avg_target_apc > 0:
        acv_apc = (avg_actual_apc / avg_target_apc) * 100
        scores['apc'] = (acv_apc * weights['APC']) / 100
    
    scores['total'] = sum(scores.values())
    return scores

def calculate_aggregate_scores_per_cashier(df):
    """
    Calculate aggregate scores per cashier dengan metode yang benar:
    - PSM, PWP, SG: Menggunakan SUM (kumulatif)
    - APC: Menggunakan AVERAGE (rata-rata)
    """
    if df.empty or 'NAMA KASIR' not in df.columns:
        return pd.DataFrame()
    
    weights = {'PSM': 20, 'PWP': 25, 'SG': 30, 'APC': 25}
    
    # Define aggregation methods for each component
    agg_cols = {
        'PSM Target': 'sum', 'PSM Actual': 'sum',
        'PWP Target': 'sum', 'PWP Actual': 'sum',
        'SG Target': 'sum', 'SG Actual': 'sum',
        'APC Target': 'mean', 'APC Actual': 'mean'  # APC menggunakan mean
    }
    
    # Filter only available columns
    valid_agg_cols = {col: func for col, func in agg_cols.items() if col in df.columns}
    aggregated_df = df.groupby('NAMA KASIR')[list(valid_agg_cols.keys())].agg(valid_agg_cols).reset_index()

    def calculate_score_from_agg(row, comp):
        total_target = row[f'{comp} Target']
        total_actual = row[f'{comp} Actual']
        if total_target == 0:
            return 0.0
        acv = (total_actual / total_target) * 100
        return (acv * weights[comp]) / 100

    # Calculate scores for each component
    for comp in ['PSM', 'PWP', 'SG', 'APC']:
        if f'{comp} Target' in aggregated_df.columns and f'{comp} Actual' in aggregated_df.columns:
            aggregated_df[f'SCORE {comp}'] = aggregated_df.apply(
                lambda row: calculate_score_from_agg(row, comp), axis=1
            )
    
    # Calculate total score
    score_cols = [f'SCORE {comp}' for comp in ['PSM', 'PWP', 'SG', 'APC'] 
                 if f'SCORE {comp}' in aggregated_df.columns]
    if score_cols:
        aggregated_df['TOTAL SCORE PPSA'] = aggregated_df[score_cols].sum(axis=1)
    
    # Add performance consistency metrics
    if 'TOTAL SCORE PPSA' in df.columns:
        individual_scores = df.groupby('NAMA KASIR')['TOTAL SCORE PPSA'].agg(['std', 'count']).reset_index()
        individual_scores.columns = ['NAMA KASIR', 'SCORE_STD', 'RECORD_COUNT']
        aggregated_df = aggregated_df.merge(individual_scores, on='NAMA KASIR', how='left')
        aggregated_df['CONSISTENCY'] = aggregated_df['SCORE_STD'].fillna(0)
    
    return aggregated_df.sort_values(by='TOTAL SCORE PPSA', ascending=False).reset_index(drop=True)

def calculate_performance_insights(df):
    """Generate automated insights dari data"""
    insights = []
    
    if df.empty:
        return insights
    
    # Overall performance insight
    overall_scores = calculate_overall_ppsa_breakdown(df)
    if overall_scores['total'] >= 100:
        insights.append({
            'type': 'success',
            'title': '🎉 Target Tercapai!',
            'text': f"Total PPSA Score {overall_scores['total']:.1f} telah melampaui target 100."
        })
    else:
        gap = 100 - overall_scores['total']
        insights.append({
            'type': 'warning',
            'title': '⚠️ Gap Performa',
            'text': f"Masih kurang {gap:.1f} poin untuk mencapai target. Fokus pada komponen dengan gap terbesar."
        })
    
    # Component analysis
    components = {'PSM': overall_scores['psm'], 'PWP': overall_scores['pwp'], 
                 'SG': overall_scores['sg'], 'APC': overall_scores['apc']}
    targets = {'PSM': 20, 'PWP': 25, 'SG': 30, 'APC': 25}
    
    best_component = max(components, key=lambda x: components[x]/targets[x])
    worst_component = min(components, key=lambda x: components[x]/targets[x])
    
    insights.append({
        'type': 'info',
        'title': f'🏆 Komponen Terbaik: {best_component}',
        'text': f"Achievement {(components[best_component]/targets[best_component]*100):.1f}% dari target."
    })
    
    if components[worst_component] < targets[worst_component]:
        insights.append({
            'type': 'alert',
            'title': f'🎯 Perlu Perbaikan: {worst_component}',
            'text': f"Hanya mencapai {(components[worst_component]/targets[worst_component]*100):.1f}% dari target."
        })
    
    # Cashier performance insights
    if 'NAMA KASIR' in df.columns:
        cashier_scores = calculate_aggregate_scores_per_cashier(df)
        if not cashier_scores.empty:
            top_performer = cashier_scores.iloc[0]
            insights.append({
                'type': 'success',
                'title': f'🌟 Top Performer: {top_performer["NAMA KASIR"]}',
                'text': f"Dengan total score {top_performer['TOTAL SCORE PPSA']:.1f}"
            })
            
            # Consistency analysis
            if 'CONSISTENCY' in cashier_scores.columns:
                most_consistent = cashier_scores.loc[cashier_scores['CONSISTENCY'].idxmin()]
                insights.append({
                    'type': 'info',
                    'title': f'🎯 Paling Konsisten: {most_consistent["NAMA KASIR"]}',
                    'text': f"Dengan variasi performa terendah (std: {most_consistent['CONSISTENCY']:.1f})"
                })
    
    return insights

def calculate_correlation_matrix(df):
    """Calculate correlation matrix untuk komponen PPSA"""
    if df.empty:
        return pd.DataFrame()
    
    score_cols = ['SCORE PSM', 'SCORE PWP', 'SCORE SG', 'SCORE APC', 'TOTAL SCORE PPSA']
    available_cols = [col for col in score_cols if col in df.columns]
    
    if len(available_cols) < 2:
        return pd.DataFrame()
    
    return df[available_cols].corr()

def detect_outliers(df):
    """Detect outliers dalam performa"""
    if df.empty or 'TOTAL SCORE PPSA' not in df.columns:
        return pd.DataFrame()
    
    Q1 = df['TOTAL SCORE PPSA'].quantile(0.25)
    Q3 = df['TOTAL SCORE PPSA'].quantile(0.75)
    IQR = Q3 - Q1
    
    lower_bound = Q1 - 1.5 * IQR
    upper_bound = Q3 + 1.5 * IQR
    
    outliers = df[(df['TOTAL SCORE PPSA'] < lower_bound) | (df['TOTAL SCORE PPSA'] > upper_bound)]
    
    if 'NAMA KASIR' in outliers.columns:
        outliers = outliers[['NAMA KASIR', 'TOTAL SCORE PPSA', 'TANGGAL']].copy()
        outliers['OUTLIER_TYPE'] = outliers['TOTAL SCORE PPSA'].apply(
            lambda x: 'Exceptional High' if x > upper_bound else 'Concerning Low'
        )
    
    return outliers.sort_values('TOTAL SCORE PPSA', ascending=False)

def calculate_shift_performance(df):
    """Calculate performance metrics by shift dengan metode perhitungan yang benar"""
    if df.empty or 'SHIFT' not in df.columns:
        return pd.DataFrame()
    
    weights = {'PSM': 20, 'PWP': 25, 'SG': 30, 'APC': 25}
    
    # Group by shift and calculate raw metrics
    shift_performance = df.groupby('SHIFT').agg({
        'PSM Target': 'sum', 'PSM Actual': 'sum',
        'PWP Target': 'sum', 'PWP Actual': 'sum',
        'SG Target': 'sum', 'SG Actual': 'sum',
        'APC Target': 'mean', 'APC Actual': 'mean',  # APC menggunakan mean
        'ACTUAL TEBUS 2500': 'sum',
        'TARGET TEBUS 2500': 'sum',
        'TOTAL SCORE PPSA': ['mean', 'median', 'std', 'count']
    }).reset_index()
    
    # Flatten column names
    shift_performance.columns = ['_'.join(col).strip() if col[1] else col[0] for col in shift_performance.columns.values]
    
    # Calculate ACV for each component
    for comp in ['PSM', 'PWP', 'SG']:
        target_col = f'{comp} Target_sum'
        actual_col = f'{comp} Actual_sum'
        if target_col in shift_performance.columns and actual_col in shift_performance.columns:
            acv_col = f'ACV {comp} (%)'
            shift_performance[acv_col] = (shift_performance[actual_col] / 
                                        shift_performance[target_col] * 100).fillna(0)
            score_col = f'SCORE {comp}'
            shift_performance[score_col] = (shift_performance[acv_col] * weights[comp]) / 100
    
    # For APC - use average
    if 'APC Target_mean' in shift_performance.columns and 'APC Actual_mean' in shift_performance.columns:
        shift_performance['ACV APC (%)'] = (shift_performance['APC Actual_mean'] / 
                                          shift_performance['APC Target_mean'] * 100).fillna(0)
        shift_performance['SCORE APC'] = (shift_performance['ACV APC (%)'] * weights['APC']) / 100
    
    # Calculate total PPSA score correctly
    score_cols = [f'SCORE {comp}' for comp in ['PSM', 'PWP', 'SG', 'APC'] 
                 if f'SCORE {comp}' in shift_performance.columns]
    if score_cols:
        shift_performance['TOTAL SCORE PPSA'] = shift_performance[score_cols].sum(axis=1)
    
    # Calculate ACV for Tebus - PERBAIKAN: Pastikan format persentase benar
    shift_performance['ACV TEBUS (%)'] = (shift_performance['ACTUAL TEBUS 2500_sum'] / 
                                        shift_performance['TARGET TEBUS 2500_sum'] * 100).fillna(0)
    
    # Rename columns for clarity
    shift_performance = shift_performance.rename(columns={
        'TOTAL SCORE PPSA_mean': 'Avg Original Score',
        'TOTAL SCORE PPSA_median': 'Median Score',
        'TOTAL SCORE PPSA_std': 'Score Std Dev',
        'TOTAL SCORE PPSA_count': 'Record Count',
    })
    
    # Remove any rows with NaN in SHIFT column
    shift_performance = shift_performance.dropna(subset=['SHIFT'])
    
    # Sort by shift order: Shift 1 (Pagi), Shift 2 (Siang), Shift 3 (Malam)
    shift_order = ['Shift 1 (Pagi)', 'Shift 2 (Siang)', 'Shift 3 (Malam)']
    shift_performance['SHIFT'] = pd.Categorical(shift_performance['SHIFT'], categories=shift_order, ordered=True)
    shift_performance = shift_performance.sort_values('SHIFT')
    
    return shift_performance

def calculate_daily_performance(df):
    """Calculate performance metrics by day dengan metode perhitungan yang benar"""
    if df.empty or 'TANGGAL' not in df.columns:
        return pd.DataFrame()
    
    weights = {'PSM': 20, 'PWP': 25, 'SG': 30, 'APC': 25}
    
    # Group by date and calculate raw metrics
    daily_performance = df.groupby('TANGGAL').agg({
        'PSM Target': 'sum', 'PSM Actual': 'sum',
        'PWP Target': 'sum', 'PWP Actual': 'sum',
        'SG Target': 'sum', 'SG Actual': 'sum',
        'APC Target': 'mean', 'APC Actual': 'mean',  # APC menggunakan mean
        'ACTUAL TEBUS 2500': 'sum',
        'TARGET TEBUS 2500': 'sum',
        'TOTAL SCORE PPSA': ['mean', 'median', 'std', 'count']
    }).reset_index()
    
    # Flatten column names
    daily_performance.columns = ['_'.join(col).strip() if col[1] else col[0] for col in daily_performance.columns.values]
    
    # Calculate ACV for each component
    for comp in ['PSM', 'PWP', 'SG']:
        target_col = f'{comp} Target_sum'
        actual_col = f'{comp} Actual_sum'
        if target_col in daily_performance.columns and actual_col in daily_performance.columns:
            acv_col = f'ACV {comp} (%)'
            daily_performance[acv_col] = (daily_performance[actual_col] / 
                                        daily_performance[target_col] * 100).fillna(0)
            score_col = f'SCORE {comp}'
            daily_performance[score_col] = (daily_performance[acv_col] * weights[comp]) / 100
    
    # For APC - use average
    if 'APC Target_mean' in daily_performance.columns and 'APC Actual_mean' in daily_performance.columns:
        daily_performance['ACV APC (%)'] = (daily_performance['APC Actual_mean'] / 
                                          daily_performance['APC Target_mean'] * 100).fillna(0)
        daily_performance['SCORE APC'] = (daily_performance['ACV APC (%)'] * weights['APC']) / 100
    
    # Calculate total PPSA score correctly
    score_cols = [f'SCORE {comp}' for comp in ['PSM', 'PWP', 'SG', 'APC'] 
                 if f'SCORE {comp}' in daily_performance.columns]
    if score_cols:
        daily_performance['TOTAL SCORE PPSA'] = daily_performance[score_cols].sum(axis=1)
    
    # Calculate ACV for Tebus - PERBAIKAN: Pastikan format persentase benar
    daily_performance['ACV TEBUS (%)'] = (daily_performance['ACTUAL TEBUS 2500_sum'] / 
                                        daily_performance['TARGET TEBUS 2500_sum'] * 100).fillna(0)
    
    # Add day of week
    daily_performance['Day of Week'] = daily_performance['TANGGAL'].dt.day_name()
    
    # Rename columns for clarity
    daily_performance = daily_performance.rename(columns={
        'TOTAL SCORE PPSA_mean': 'Avg Original Score',
        'TOTAL SCORE PPSA_median': 'Median Score',
        'TOTAL SCORE PPSA_std': 'Score Std Dev',
        'TOTAL SCORE PPSA_count': 'Record Count',
    })
    
    return daily_performance.sort_values('TANGGAL')

def calculate_day_of_week_performance(df):
    """Calculate performance metrics by day of week"""
    if df.empty or 'HARI' not in df.columns:
        return pd.DataFrame()
    
    # Define order for days
    day_order = ['Senin', 'Selasa', 'Rabu', 'Kamis', 'Jumat', 'Sabtu', 'Minggu']
    
    # Group by day and calculate metrics
    day_performance = df.groupby('HARI').agg({
        'TOTAL SCORE PPSA': ['mean', 'median', 'std', 'count'],
        'SCORE PSM': 'mean',
        'SCORE PWP': 'mean',
        'SCORE SG': 'mean',
        'SCORE APC': 'mean',
        'ACTUAL TEBUS 2500': 'sum',
        'TARGET TEBUS 2500': 'sum'
    }).reset_index()
    
    # Flatten column names
    day_performance.columns = ['_'.join(col).strip() if col[1] else col[0] for col in day_performance.columns.values]
    
    # Calculate ACV for Tebus - PERBAIKAN: Pastikan format persentase benar
    day_performance['ACV TEBUS (%)'] = (day_performance['ACTUAL TEBUS 2500_sum'] / 
                                      day_performance['TARGET TEBUS 2500_sum'] * 100).fillna(0)
    
    # Rename columns for clarity
    day_performance = day_performance.rename(columns={
        'HARI': 'Day',
        'TOTAL SCORE PPSA_mean': 'Avg Score',
        'TOTAL SCORE PPSA_median': 'Median Score',
        'TOTAL SCORE PPSA_std': 'Score Std Dev',
        'TOTAL SCORE PPSA_count': 'Record Count',
        'SCORE PSM_mean': 'Avg PSM Score',
        'SCORE PWP_mean': 'Avg PWP Score',
        'SCORE SG_mean': 'Avg SG Score',
        'SCORE APC_mean': 'Avg APC Score'
    })
    
    # Sort by day order
    day_performance['Day'] = pd.Categorical(day_performance['Day'], categories=day_order, ordered=True)
    day_performance = day_performance.sort_values('Day')
    
    return day_performance

def calculate_team_metrics(df):
    """Calculate team-wide metrics for display"""
    if df.empty:
        return {}
    
    metrics = {}
    
    # Total records
    metrics['total_records'] = len(df)
    
    # Unique cashiers
    if 'NAMA KASIR' in df.columns:
        metrics['unique_cashiers'] = df['NAMA KASIR'].nunique()
    else:
        metrics['unique_cashiers'] = 0
    
    # Performance metrics
    metrics['avg_score'] = df['TOTAL SCORE PPSA'].mean()
    metrics['median_score'] = df['TOTAL SCORE PPSA'].median()
    metrics['max_score'] = df['TOTAL SCORE PPSA'].max()
    metrics['min_score'] = df['TOTAL SCORE PPSA'].min()
    
    # Achievement rates
    metrics['above_target'] = (df['TOTAL SCORE PPSA'] >= 100).sum()
    metrics['below_target'] = (df['TOTAL SCORE PPSA'] < 100).sum()
    metrics['achievement_rate'] = (metrics['above_target'] / metrics['total_records']) * 100
    
    # Component performance
    components = ['PSM', 'PWP', 'SG', 'APC']
    for comp in components:
        if f'SCORE {comp}' in df.columns:
            metrics[f'avg_{comp.lower()}_score'] = df[f'SCORE {comp}'].mean()
    
    # Tebus performance
    if 'ACTUAL TEBUS 2500' in df.columns and 'TARGET TEBUS 2500' in df.columns:
        total_target = df['TARGET TEBUS 2500'].sum()
        total_actual = df['ACTUAL TEBUS 2500'].sum()
        metrics['tebus_acv'] = (total_actual / total_target * 100) if total_target > 0 else 0
    
    return metrics

def calculate_tebus_insights(df):
    """Generate insights specifically for Tebus performance"""
    insights = []
    
    if df.empty:
        return insights
    
    # Overall Tebus performance
    total_target = df['TARGET TEBUS 2500'].sum()
    total_actual = df['ACTUAL TEBUS 2500'].sum()
    overall_acv = (total_actual / total_target * 100) if total_target > 0 else 0
    
    if overall_acv >= 100:
        insights.append({
            'type': 'success',
            'title': '🎉 Target Tebus Tercapai!',
            'text': f"Total ACV Tebus {overall_acv:.1f}% telah melampaui target 100%."
        })
    else:
        gap = 100 - overall_acv
        insights.append({
            'type': 'warning',
            'title': '⚠️ Gap Tebus Performance',
            'text': f"Masih kurang {gap:.1f}% untuk mencapai target. Perlu peningkatan performa."
        })
    
    # Top Tebus performers
    if 'NAMA KASIR' in df.columns:
        tebus_summary = df.groupby('NAMA KASIR').agg({
            'TARGET TEBUS 2500': 'sum',
            'ACTUAL TEBUS 2500': 'sum'
        }).reset_index()
        
        tebus_summary['ACV TEBUS (%)'] = (tebus_summary['ACTUAL TEBUS 2500'] / tebus_summary['TARGET TEBUS 2500'] * 100).fillna(0)
        tebus_summary = tebus_summary.sort_values('ACV TEBUS (%)', ascending=False)
        
        if not tebus_summary.empty:
            top_performer = tebus_summary.iloc[0]
            insights.append({
                'type': 'success',
                'title': f'🌟 Top Tebus Performer: {top_performer["NAMA KASIR"]}',
                'text': f"Dengan ACV {top_performer['ACV TEBUS (%)']:.1f}%"
            })
            
            # Consistency analysis
            if len(tebus_summary) > 1:
                std_acv = tebus_summary['ACV TEBUS (%)'].std()
                if std_acv < 10:
                    insights.append({
                        'type': 'info',
                        'title': '📊 Performa Tebus Konsisten',
                        'text': f"Standar deviasi ACV rendah ({std_acv:.1f}%) menunjukkan performa stabil."
                    })
    
    # Shift performance for Tebus
    if 'SHIFT' in df.columns:
        shift_tebus = df.groupby('SHIFT').agg({
            'TARGET TEBUS 2500': 'sum',
            'ACTUAL TEBUS 2500': 'sum'
        }).reset_index()
        
        shift_tebus['ACV TEBUS (%)'] = (shift_tebus['ACTUAL TEBUS 2500'] / shift_tebus['TARGET TEBUS 2500'] * 100).fillna(0)
        shift_tebus = shift_tebus.sort_values('ACV TEBUS (%)', ascending=False)
        
        if not shift_tebus.empty:
            best_shift = shift_tebus.iloc[0]
            insights.append({
                'type': 'info',
                'title': f'🕐 Best Shift for Tebus: {best_shift["SHIFT"]}',
                'text': f"Dengan ACV {best_shift['ACV TEBUS (%)']:.1f}%"
            })
    
    # Day of week performance for Tebus
    if 'HARI' in df.columns:
        day_tebus = df.groupby('HARI').agg({
            'TARGET TEBUS 2500': 'sum',
            'ACTUAL TEBUS 2500': 'sum'
        }).reset_index()
        
        day_tebus['ACV TEBUS (%)'] = (day_tebus['ACTUAL TEBUS 2500'] / day_tebus['TARGET TEBUS 2500'] * 100).fillna(0)
        day_tebus = day_tebus.sort_values('ACV TEBUS (%)', ascending=False)
        
        if not day_tebus.empty:
            best_day = day_tebus.iloc[0]
            insights.append({
                'type': 'info',
                'title': f'📅 Best Day for Tebus: {best_day["HARI"]}',
                'text': f"Dengan ACV {best_day['ACV TEBUS (%)']:.1f}%"
            })
    
    return insights

# --- MAIN DASHBOARD ---
def main():
    # Dashboard Header
    st.markdown(f"""
    <div class="dashboard-header">
        <h1 class="main-title">
            {get_svg_icon("dashboard", size=60, color="#667eea")}
            PPSA Analytics Dashboard
        </h1>
        <p class="subtitle">
            Platform <strong>analytics</strong> komprehensif untuk monitoring real-time 
            performa <strong>PPSA</strong> (PSM, PWP, SG, APC) dan <strong>Tebus Suuegerr</strong> 
            dengan insights AI-powered untuk optimasi performa tim.
        </p>
    </div>
    """, unsafe_allow_html=True)

    # Load and process data
    raw_df = load_data_from_gsheet()
    
    if raw_df.empty:
        st.error("❌ Tidak dapat memuat data. Silakan periksa koneksi Google Sheets Anda.")
        return

    processed_df = process_data(raw_df.copy())
    
    # Sidebar filters
    with st.sidebar:
        st.markdown("### ⚙️ Filter & Pengaturan")
        
        # Cashier filter
        if 'NAMA KASIR' in processed_df.columns:
            all_cashiers = sorted(processed_df['NAMA KASIR'].unique())
            selected_cashiers = st.multiselect(
                "🧑‍💼 Pilih Kasir:",
                options=all_cashiers,
                default=all_cashiers,
                help="Pilih kasir yang ingin dianalisis"
            )
            filtered_df = processed_df[processed_df['NAMA KASIR'].isin(selected_cashiers)]
        else:
            filtered_df = processed_df
            selected_cashiers = []
        
        # Date filter
        if 'TANGGAL' in filtered_df.columns:
            filtered_df = filtered_df.dropna(subset=['TANGGAL'])
            if not filtered_df.empty:
                min_date = filtered_df['TANGGAL'].min().to_pydatetime()
                max_date = filtered_df['TANGGAL'].max().to_pydatetime()
                
                selected_date_range = st.date_input(
                    "📅 Rentang Tanggal:",
                    value=[min_date, max_date],
                    min_value=min_date,
                    max_value=max_date,
                    help="Pilih periode analisis"
                )
                
                if len(selected_date_range) == 2:
                    start_date, end_date = pd.to_datetime(selected_date_range[0]), pd.to_datetime(selected_date_range[1])
                    mask = (filtered_df['TANGGAL'] >= start_date) & (filtered_df['TANGGAL'] <= end_date)
                    filtered_df = filtered_df.loc[mask]
        
        # Shift filter - PERBAIKAN: Menggunakan kolom SHIFT yang sudah diproses
        if 'SHIFT' in filtered_df.columns:
            all_shifts = sorted(filtered_df['SHIFT'].unique())
            selected_shifts = st.multiselect(
                "🕐 Pilih Shift:",
                options=all_shifts,
                default=all_shifts,
                help="Pilih shift yang ingin dianalisis"
            )
            filtered_df = filtered_df[filtered_df['SHIFT'].isin(selected_shifts)]
        
        # Performance threshold
        st.markdown("---")
        perf_threshold = st.slider(
            "🎯 Minimum Performance Threshold:",
            min_value=50.0,
            max_value=150.0,
            value=100.0,
            step=5.0,
            help="Threshold untuk mengidentifikasi performa"
        )
        
        # Summary info
        st.markdown("---")
        st.markdown("### 📊 Ringkasan Data")
        st.info(f"""
        **Total Records:** {len(filtered_df):,}  
        **Kasir Terpilih:** {len(selected_cashiers)}  
        **Periode:** {len(filtered_df['TANGGAL'].dt.date.unique()) if 'TANGGAL' in filtered_df.columns and not filtered_df.empty else 0} hari  
        **Avg Score:** {filtered_df['TOTAL SCORE PPSA'].mean():.1f} 
        """)

    # Main tabs
    tab1, tab2, tab3, tab4, tab5, tab6 = st.tabs([
        "📈 PPSA Analytics", 
        "🛒 Tebus Analytics", 
        "🔍 Deep Insights",
        "🎯 Performance Alerts",
        "🕐 Performance Shift",
        "📅 Performance Per Hari"
    ])

    with tab1:
        # Overall Performance Summary
        overall_scores = calculate_overall_ppsa_breakdown(filtered_df)
        
        # KPI Metrics (Direct without extra container)
        col1, col2, col3, col4 = st.columns(4, gap="medium")
        
        metrics = [
            {"label": "PSM Score", "value": overall_scores['psm'], "target": 20, "icon": "psm", "col": col1},
            {"label": "PWP Score", "value": overall_scores['pwp'], "target": 25, "icon": "pwp", "col": col2},
            {"label": "SG Score", "value": overall_scores['sg'], "target": 30, "icon": "sg", "col": col3},
            {"label": "APC Score", "value": overall_scores['apc'], "target": 25, "icon": "apc", "col": col4}
        ]
        
        for metric in metrics:
            with metric["col"]:
                achievement = (metric['value'] / metric['target']) * 100
                color = "#10b981" if achievement >= 100 else "#f59e0b" if achievement >= 80 else "#ef4444"
                
                st.markdown(f"""
                <div class="metric-card">
                    <div class="metric-label">
                        {get_svg_icon(metric['icon'], size=20, color=color)} 
                        {metric['label']}
                    </div>
                    <div class="metric-value" style="color: {color};">
                        {metric['value']:.1f}
                    </div>
                    <div style="font-size: 0.8rem; color: #64748b; margin-top: 0.5rem;">
                        Target: {metric['target']} ({achievement:.0f}%)
                    </div>
                </div>
                """, unsafe_allow_html=True)

        # Total PPSA Card (Centered)
        st.markdown('<div style="display: flex; justify-content: center; margin: 2rem 0;">', unsafe_allow_html=True)
        
        gap_value = overall_scores['total'] - 100
        gap_color = '#10b981' if gap_value >= 0 else '#ef4444'
        
        st.markdown(f"""
        <div class="total-ppsa-card" style="max-width: 500px;">
            <div class="total-ppsa-label">
                {get_svg_icon("trophy", size=40, color="white")} 
                TOTAL PPSA SCORE
            </div>
            <div class="total-ppsa-value">{overall_scores['total']:.1f}</div>
            <div style="font-size: 1.2rem; margin-top: 1rem; opacity: 0.9;">
                Gap: <span style="color: {'#90EE90' if gap_value >= 0 else '#FFB6C1'};">{gap_value:+.1f}</span>
            </div>
        </div>
        """, unsafe_allow_html=True)
        
        st.markdown('</div>', unsafe_allow_html=True)

        # Team Performance Metrics Section
        st.markdown('<div class="content-container">', unsafe_allow_html=True)
        st.markdown('<h2 class="section-header">👥 Team Performance Metrics</h2>', unsafe_allow_html=True)
        
        # Calculate team metrics
        team_metrics = calculate_team_metrics(filtered_df)
        
        # Display team metrics in a grid
        col1, col2, col3, col4 = st.columns(4, gap="medium")
        
        with col1:
            st.markdown(f"""
            <div class="metric-card">
                <div class="metric-label">
                    {get_svg_icon("users", size=20, color="#667eea")} 
                    Total Team Members
                </div>
                <div class="metric-value" style="color: #667eea; font-size: 2rem;">
                    {team_metrics.get('unique_cashiers', 0)}
                </div>
                <div style="font-size: 0.8rem; color: #64748b; margin-top: 0.5rem;">
                    Active Members
                </div>
            </div>
            """, unsafe_allow_html=True)
        
        with col2:
            st.markdown(f"""
            <div class="metric-card">
                <div class="metric-label">
                    {get_svg_icon("trending", size=20, color="#10b981")} 
                    Achievement Rate
                </div>
                <div class="metric-value" style="color: #10b981; font-size: 2rem;">
                    {team_metrics.get('achievement_rate', 0):.1f}%
                </div>
                <div style="font-size: 0.8rem; color: #64748b; margin-top: 0.5rem;">
                    Above Target
                </div>
            </div>
            """, unsafe_allow_html=True)
        
        with col3:
            st.markdown(f"""
            <div class="metric-card">
                <div class="metric-label">
                    {get_svg_icon("star", size=20, color="#f59e0b")} 
                    Average Score
                </div>
                <div class="metric-value" style="color: #f59e0b; font-size: 2rem;">
                    {team_metrics.get('avg_score', 0):.1f}
                </div>
                <div style="font-size: 0.8rem; color: #64748b; margin-top: 0.5rem;">
                    Team Average
                </div>
            </div>
            """, unsafe_allow_html=True)
        
        with col4:
            st.markdown(f"""
            <div class="metric-card">
                <div class="metric-label">
                    {get_svg_icon("tebus", size=20, color="#764ba2")} 
                    Tebus ACV
                </div>
                <div class="metric-value" style="color: #764ba2; font-size: 2rem;">
                    {team_metrics.get('tebus_acv', 0):.1f}%
                </div>
                <div style="font-size: 0.8rem; color: #64748b; margin-top: 0.5rem;">
                    Overall Achievement
                </div>
            </div>
            """, unsafe_allow_html=True)
        
        # Additional team metrics in second row
        col1, col2, col3, col4 = st.columns(4, gap="medium")
        
        with col1:
            max_score = team_metrics.get('max_score', 0)
            st.markdown(f"""
            <div class="metric-card">
                <div class="metric-label">
                    {get_svg_icon("trophy", size=20, color="#FFD700")} 
                    Highest Score
                </div>
                <div class="metric-value" style="color: #FFD700; font-size: 2rem;">
                    {max_score:.1f}
                </div>
                <div style="font-size: 0.8rem; color: #64748b; margin-top: 0.5rem;">
                    Peak Performance
                </div>
            </div>
            """, unsafe_allow_html=True)
        
        with col2:
            min_score = team_metrics.get('min_score', 0)
            st.markdown(f"""
            <div class="metric-card">
                <div class="metric-label">
                    {get_svg_icon("alert", size=20, color="#ef4444")} 
                    Lowest Score
                </div>
                <div class="metric-value" style="color: #ef4444; font-size: 2rem;">
                    {min_score:.1f}
                </div>
                <div style="font-size: 0.8rem; color: #64748b; margin-top: 0.5rem;">
                    Needs Attention
                </div>
            </div>
            """, unsafe_allow_html=True)
        
        with col3:
            median_score = team_metrics.get('median_score', 0)
            st.markdown(f"""
            <div class="metric-card">
                <div class="metric-label">
                    {get_svg_icon("analytics", size=20, color="#667eea")} 
                    Median Score
                </div>
                <div class="metric-value" style="color: #667eea; font-size: 2rem;">
                    {median_score:.1f}
                </div>
                <div style="font-size: 0.8rem; color: #64748b; margin-top: 0.5rem;">
                    Center Point
                </div>
            </div>
            """, unsafe_allow_html=True)
        
        with col4:
            total_records = team_metrics.get('total_records', 0)
            st.markdown(f"""
            <div class="metric-card">
                <div class="metric-label">
                    {get_svg_icon("chart", size=20, color="#764ba2")} 
                    Total Records
                </div>
                <div class="metric-value" style="color: #764ba2; font-size: 2rem;">
                    {total_records:,}
                </div>
                <div style="font-size: 0.8rem; color: #64748b; margin-top: 0.5rem;">
                    Data Points
                </div>
            </div>
            """, unsafe_allow_html=True)
        
        st.markdown('</div>', unsafe_allow_html=True)

        # Penjelasan Metode Perhitungan
        st.markdown('<div class="content-container">', unsafe_allow_html=True)
        st.markdown('<h2 class="section-header">📐 Metode Perhitungan PPSA</h2>', unsafe_allow_html=True)
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.markdown("""
            ### 📊 Komponen Kumulatif (SUM)
            **PSM, PWP, SG** menggunakan metode SUM karena:
            - Merupakan metrik kumulatif/akumulasi
            - Semakin besar nilai semakin baik
            - Total performa dari seluruh transaksi
            
            **Formula:**
            ```
            ACV = (Total Actual / Total Target) × 100
            Score = (ACV × Bobot) / 100
            ```
            """)
        
        with col2:
            st.markdown("""
            ### 📈 Komponen Rata-rata (AVERAGE)
            **APC** menggunakan metode AVERAGE karena:
            - Merupakan metrik rata-rata per transaksi
            - Konsistensi lebih penting dari total
            - Mengukur efisiensi per customer
            
            **Formula:**
            ```
            ACV = (Avg Actual / Avg Target) × 100
            Score = (ACV × Bobot) / 100
            ```
            """)
        
        st.markdown('</div>', unsafe_allow_html=True)

        # AI Insights Section
        st.markdown('<div class="content-container">', unsafe_allow_html=True)
        st.markdown('<h2 class="section-header">🤖 AI-Powered Insights</h2>', unsafe_allow_html=True)
        
        insights = calculate_performance_insights(filtered_df)
        for insight in insights:
            card_class = "insight-card" if insight['type'] in ['success', 'info'] else "alert-card"
            st.markdown(f"""
            <div class="{card_class}">
                <div class="{'insight-title' if insight['type'] in ['success', 'info'] else 'alert-title'}">
                    {insight['title']}
                </div>
                <div class="{'insight-text' if insight['type'] in ['success', 'info'] else 'insight-text'}">
                    {insight['text']}
                </div>
            </div>
            """, unsafe_allow_html=True)
        
        st.markdown('</div>', unsafe_allow_html=True)

        # Top Performers Section
        st.markdown('<div class="content-container">', unsafe_allow_html=True)
        st.markdown('<h2 class="section-header">🏅 Hall of Fame - Top Performers</h2>', unsafe_allow_html=True)
        
        score_summary = calculate_aggregate_scores_per_cashier(filtered_df)
        if not score_summary.empty and len(score_summary) >= 3:
            top3_performers = score_summary.head(3)
            medal_icons = ["gold", "silver", "bronze"]
            medal_colors = ["#FFD700", "#C0C0C0", "#CD7F32"]
            
            col1, col2, col3 = st.columns(3, gap="medium")
            
            for i, (col, performer, medal, color) in enumerate(zip([col1, col2, col3], top3_performers.iterrows(), medal_icons, medal_colors)):
                idx, row = performer
                consistency_score = 100 - (row.get('CONSISTENCY', 0) * 2)  # Convert std to consistency score
                
                with col:
                    st.markdown(f"""
                    <div class="top-performer-card" style="border-top: 4px solid {color};">
                        <div class="top-performer-icon">{get_svg_icon(medal, size=80)}</div>
                        <div class="top-performer-name">{row['NAMA KASIR']}</div>
                        <div class="top-performer-score">{row['TOTAL SCORE PPSA']:.1f}</div>
                        <div style="font-size: 0.85rem; color: #64748b; margin-top: 0.5rem;">
                            Consistency: {max(0, consistency_score):.0f}%
                        </div>
                        <div style="font-size: 0.8rem; color: #64748b;">
                            Records: {row.get('RECORD_COUNT', 'N/A')}
                        </div>
                    </div>
                    """, unsafe_allow_html=True)
        
        st.markdown('</div>', unsafe_allow_html=True)

        # Performance Analytics Charts
        st.markdown('<div class="content-container">', unsafe_allow_html=True)
        st.markdown('<h2 class="section-header">📊 Performance Analytics</h2>', unsafe_allow_html=True)
        
        col_chart1, col_chart2 = st.columns(2, gap="large")
        
        with col_chart1:
            st.subheader("🎯 Component vs Target Analysis")
            chart_data = pd.DataFrame({
                'Komponen': ['PSM', 'PWP', 'SG', 'APC'],
                'Actual': [overall_scores['psm'], overall_scores['pwp'], overall_scores['sg'], overall_scores['apc']],
                'Target': [20, 25, 30, 25]
            })
            
            fig_vs_target = go.Figure()
            fig_vs_target.add_trace(go.Bar(
                name='Actual Score',
                x=chart_data['Komponen'],
                y=chart_data['Actual'],
                marker_color=['#667eea', '#764ba2', '#f093fb', '#4facfe'],
                text=[f"{val:.1f}" for val in chart_data['Actual']],
                textposition='outside'
            ))
            fig_vs_target.add_trace(go.Scatter(
                name='Target',
                x=chart_data['Komponen'],
                y=chart_data['Target'],
                mode='markers+lines',
                marker=dict(size=15, color='#ef4444', symbol='diamond'),
                line=dict(color='#ef4444', width=3, dash='dash')
            ))
            fig_vs_target.update_layout(
                template='plotly_white',
                height=350,
                showlegend=True,
                yaxis_title='Score',
                title_x=0.5
            )
            st.plotly_chart(fig_vs_target, use_container_width=True)
        
        with col_chart2:
            st.subheader("📈 Performance Distribution")
            if not score_summary.empty:
                fig_dist = go.Figure()
                fig_dist.add_trace(go.Histogram(
                    x=score_summary['TOTAL SCORE PPSA'],
                    nbinsx=15,
                    marker_color='rgba(102, 126, 234, 0.7)',
                    name='Distribution'
                ))
                fig_dist.add_vline(
                    x=100, 
                    line_dash="dash", 
                    line_color="red",
                    annotation_text="Target (100)"
                )
                fig_dist.update_layout(
                    template='plotly_white',
                    height=350,
                    xaxis_title='Total PPSA Score',
                    yaxis_title='Frequency',
                    showlegend=False
                )
                st.plotly_chart(fig_dist, use_container_width=True)
        
        st.markdown('</div>', unsafe_allow_html=True)

        # Detailed Performance Table
        st.markdown('<div class="content-container">', unsafe_allow_html=True)
        st.markdown('<h2 class="section-header">📋 Detailed Performance Analysis</h2>', unsafe_allow_html=True)
        
        if not score_summary.empty:
            # Add performance categories
            score_summary['Performance Category'] = score_summary['TOTAL SCORE PPSA'].apply(
                lambda x: "🏆 Excellent" if x >= 120 else
                         "⭐ Good" if x >= 100 else
                         "⚠️ Needs Improvement" if x >= 80 else
                         "🚨 Critical"
            )
            
            # Format the dataframe for display
            display_df = score_summary[['NAMA KASIR', 'TOTAL SCORE PPSA', 'Performance Category', 
                                       'SCORE PSM', 'SCORE PWP', 'SCORE SG', 'SCORE APC', 'CONSISTENCY']].copy()
            
            st.dataframe(
                display_df,
                use_container_width=True,
                column_config={
                    'NAMA KASIR': st.column_config.TextColumn("Nama Kasir", width="medium"),
                    'TOTAL SCORE PPSA': st.column_config.NumberColumn("Total Score", format="%.1f", width="small"),
                    'Performance Category': st.column_config.TextColumn("Category", width="medium"),
                    'SCORE PSM': st.column_config.NumberColumn("PSM", format="%.1f", width="small"),
                    'SCORE PWP': st.column_config.NumberColumn("PWP", format="%.1f", width="small"),
                    'SCORE SG': st.column_config.NumberColumn("SG", format="%.1f", width="small"),
                    'SCORE APC': st.column_config.NumberColumn("APC", format="%.1f", width="small"),
                    'CONSISTENCY': st.column_config.NumberColumn("Consistency", format="%.1f", width="small"),
                },
                hide_index=True
            )
        
        st.markdown('</div>', unsafe_allow_html=True)

    with tab2:
        # Tebus Analytics
        st.markdown('<div class="content-container">', unsafe_allow_html=True)
        st.markdown('<h2 class="section-header">🛒 Tebus (Suuegerr) Performance Analytics</h2>', unsafe_allow_html=True)
        
        if not filtered_df.empty and 'TARGET TEBUS 2500' in filtered_df.columns:
            # Calculate tebus summary
            tebus_summary = filtered_df.groupby('NAMA KASIR').agg({
                'TARGET TEBUS 2500': 'sum',
                'ACTUAL TEBUS 2500': 'sum'
            }).reset_index()
            
            tebus_summary['ACV TEBUS (%)'] = (tebus_summary['ACTUAL TEBUS 2500'] / tebus_summary['TARGET TEBUS 2500'] * 100).fillna(0)
            tebus_summary = tebus_summary.sort_values('ACV TEBUS (%)', ascending=False).reset_index(drop=True)
            
            # Overall Tebus Performance
            overall_tebus_target = filtered_df['TARGET TEBUS 2500'].sum()
            overall_tebus_actual = filtered_df['ACTUAL TEBUS 2500'].sum()
            overall_tebus_acv = (overall_tebus_actual / overall_tebus_target * 100) if overall_tebus_target > 0 else 0
            
            col1, col2, col3 = st.columns([1, 2, 1])
            with col2:
                st.markdown(f"""
                <div class="total-ppsa-card" style="background: linear-gradient(135deg, #10b981 0%, #059669 100%);">
                    <div class="total-ppsa-label">
                        {get_svg_icon("tebus", size=40, color="white")} 
                        TOTAL ACV TEBUS
                    </div>
                    <div class="total-ppsa-value">{overall_tebus_acv:.1f}%</div>
                    <div style="font-size: 1rem; margin-top: 1rem; opacity: 0.9;">
                        {overall_tebus_actual:,} / {overall_tebus_target:,}
                    </div>
                </div>
                """, unsafe_allow_html=True)
            
            # Tebus Performance by Shift
            st.subheader("🕐 Tebus Performance by Shift")
            if 'SHIFT' in filtered_df.columns:
                shift_tebus = filtered_df.groupby('SHIFT').agg({
                    'TARGET TEBUS 2500': 'sum',
                    'ACTUAL TEBUS 2500': 'sum'
                }).reset_index()
                
                shift_tebus['ACV TEBUS (%)'] = (shift_tebus['ACTUAL TEBUS 2500'] / shift_tebus['TARGET TEBUS 2500'] * 100).fillna(0)
                shift_tebus = shift_tebus.sort_values('ACV TEBUS (%)', ascending=False)
                
                fig_shift_tebus = go.Figure()
                colors = ['#10b981' if acv >= 100 else '#f59e0b' if acv >= 80 else '#ef4444' 
                         for acv in shift_tebus['ACV TEBUS (%)']]
                
                fig_shift_tebus.add_trace(go.Bar(
                    x=shift_tebus['SHIFT'],
                    y=shift_tebus['ACV TEBUS (%)'],
                    marker_color=colors,
                    text=[f"{acv:.1f}%" for acv in shift_tebus['ACV TEBUS (%)']],
                    textposition='outside'
                ))
                
                fig_shift_tebus.add_hline(
                    y=100, 
                    line_dash="dash", 
                    line_color="red",
                    annotation_text="Target (100%)"
                )
                
                fig_shift_tebus.update_layout(
                    template='plotly_white',
                    height=350,
                    showlegend=False,
                    yaxis_title='ACV Tebus (%)',
                    xaxis_title='Shift',
                    title="Tebus Achievement by Shift"
                )
                
                st.plotly_chart(fig_shift_tebus, use_container_width=True)
            
            # Tebus Performance by Day of Week
            st.subheader("📅 Tebus Performance by Day of Week")
            if 'HARI' in filtered_df.columns:
                day_tebus = filtered_df.groupby('HARI').agg({
                    'TARGET TEBUS 2500': 'sum',
                    'ACTUAL TEBUS 2500': 'sum'
                }).reset_index()
                
                day_tebus['ACV TEBUS (%)'] = (day_tebus['ACTUAL TEBUS 2500'] / day_tebus['TARGET TEBUS 2500'] * 100).fillna(0)
                
                # Define order for days
                day_order = ['Senin', 'Selasa', 'Rabu', 'Kamis', 'Jumat', 'Sabtu', 'Minggu']
                day_tebus['HARI'] = pd.Categorical(day_tebus['HARI'], categories=day_order, ordered=True)
                day_tebus = day_tebus.sort_values('HARI')
                
                fig_day_tebus = go.Figure()
                colors = ['#10b981' if acv >= 100 else '#f59e0b' if acv >= 80 else '#ef4444' 
                         for acv in day_tebus['ACV TEBUS (%)']]
                
                fig_day_tebus.add_trace(go.Bar(
                    x=day_tebus['HARI'],
                    y=day_tebus['ACV TEBUS (%)'],
                    marker_color=colors,
                    text=[f"{acv:.1f}%" for acv in day_tebus['ACV TEBUS (%)']],
                    textposition='outside'
                ))
                
                fig_day_tebus.add_hline(
                    y=100, 
                    line_dash="dash", 
                    line_color="red",
                    annotation_text="Target (100%)"
                )
                
                fig_day_tebus.update_layout(
                    template='plotly_white',
                    height=350,
                    showlegend=False,
                    yaxis_title='ACV Tebus (%)',
                    xaxis_title='Day of Week',
                    title="Tebus Achievement by Day of Week"
                )
                
                st.plotly_chart(fig_day_tebus, use_container_width=True)
            
            # Tebus Performance Trend
            st.subheader("📈 Tebus Performance Trend")
            if 'TANGGAL' in filtered_df.columns:
                daily_tebus = filtered_df.groupby('TANGGAL').agg({
                    'TARGET TEBUS 2500': 'sum',
                    'ACTUAL TEBUS 2500': 'sum'
                }).reset_index()
                
                daily_tebus['ACV TEBUS (%)'] = (daily_tebus['ACTUAL TEBUS 2500'] / daily_tebus['TARGET TEBUS 2500'] * 100).fillna(0)
                daily_tebus = daily_tebus.sort_values('TANGGAL')
                
                fig_tebus_trend = go.Figure()
                
                # Add line for ACV trend
                fig_tebus_trend.add_trace(go.Scatter(
                    x=daily_tebus['TANGGAL'],
                    y=daily_tebus['ACV TEBUS (%)'],
                    mode='lines+markers',
                    name='ACV Tebus (%)',
                    line=dict(color='#10b981', width=3),
                    marker=dict(size=8)
                ))
                
                # Add target line
                fig_tebus_trend.add_hline(
                    y=100, 
                    line_dash="dash", 
                    line_color="red",
                    annotation_text="Target (100%)"
                )
                
                # Add shaded area for variation
                fig_tebus_trend.add_trace(go.Scatter(
                    x=daily_tebus['TANGGAL'],
                    y=daily_tebus['ACV TEBUS (%)'],
                    mode='lines',
                    line=dict(width=0),
                    showlegend=False
                ))
                
                fig_tebus_trend.add_trace(go.Scatter(
                    x=daily_tebus['TANGGAL'],
                    y=daily_tebus['ACV TEBUS (%)'],
                    mode='lines',
                    line=dict(width=0),
                    fill='tonexty',
                    fillcolor='rgba(16, 185, 129, 0.2)',
                    name='Variation Range',
                    showlegend=True
                ))
                
                fig_tebus_trend.update_layout(
                    template='plotly_white',
                    height=400,
                    showlegend=True,
                    yaxis_title='ACV Tebus (%)',
                    xaxis_title='Date',
                    title="Tebus Performance Trend"
                )
                
                st.plotly_chart(fig_tebus_trend, use_container_width=True)
            
            # Tebus Performance Chart
            st.subheader("📊 Tebus Performance by Cashier")
            if not tebus_summary.empty:
                fig_tebus = go.Figure()
                colors = ['#10b981' if acv >= 100 else '#f59e0b' if acv >= 80 else '#ef4444' 
                         for acv in tebus_summary['ACV TEBUS (%)']]
                
                fig_tebus.add_trace(go.Bar(
                    y=tebus_summary['NAMA KASIR'],
                    x=tebus_summary['ACV TEBUS (%)'],
                    orientation='h',
                    marker_color=colors,
                    text=[f"{acv:.1f}%" for acv in tebus_summary['ACV TEBUS (%)']],
                    textposition='outside'
                ))
                
                fig_tebus.add_vline(x=100, line_dash="dash", line_color="red", annotation_text="Target 100%")
                
                fig_tebus.update_layout(
                    template='plotly_white',
                    height=max(400, len(tebus_summary) * 35),
                    showlegend=False,
                    xaxis_title='Achievement (%)',
                    yaxis={'categoryorder': 'total ascending'},
                    title="Tebus Performance by Cashier"
                )
                
                st.plotly_chart(fig_tebus, use_container_width=True)
            
            # Tebus Component Analysis
            st.subheader("🎯 Tebus Component Analysis")
            if 'NAMA KASIR' in filtered_df.columns:
                # Calculate tebus components by cashier
                tebus_components = filtered_df.groupby('NAMA KASIR').agg({
                    'TARGET TEBUS 2500': 'sum',
                    'ACTUAL TEBUS 2500': 'sum',
                    'TOTAL SCORE PPSA': 'mean'
                }).reset_index()
                
                tebus_components['ACV TEBUS (%)'] = (tebus_components['ACTUAL TEBUS 2500'] / tebus_components['TARGET TEBUS 2500'] * 100).fillna(0)
                
                # Create correlation scatter plot
                fig_correlation = go.Figure()
                
                fig_correlation.add_trace(go.Scatter(
                    x=tebus_components['TOTAL SCORE PPSA'],
                    y=tebus_components['ACV TEBUS (%)'],
                    mode='markers',
                    name='PPSA Score vs Tebus ACV',
                    marker=dict(
                        size=12,
                        color=tebus_components['ACV TEBUS (%)'],
                        colorscale='Viridis',
                        showscale=True,
                        colorbar=dict(title="ACV Tebus (%)")
                    ),
                    text=tebus_components['NAMA KASIR'],
                    textposition="top center"
                ))
                
                # Add trend line
                z = np.polyfit(tebus_components['TOTAL SCORE PPSA'], tebus_components['ACV TEBUS (%)'], 1)
                p = np.poly1d(z)
                x_trend = np.linspace(tebus_components['TOTAL SCORE PPSA'].min(), tebus_components['TOTAL SCORE PPSA'].max(), 100)
                y_trend = p(x_trend)
                
                fig_correlation.add_trace(go.Scatter(
                    x=x_trend,
                    y=y_trend,
                    mode='lines',
                    name='Trend Line',
                    line=dict(color='red', width=2, dash='dash')
                ))
                
                fig_correlation.update_layout(
                    template='plotly_white',
                    height=400,
                    xaxis_title='Total PPSA Score',
                    yaxis_title='ACV Tebus (%)',
                    title='Correlation: PPSA Score vs Tebus Performance'
                )
                
                st.plotly_chart(fig_correlation, use_container_width=True)
                
                # Display correlation coefficient
                correlation = tebus_components['TOTAL SCORE PPSA'].corr(tebus_components['ACV TEBUS (%)'])
                st.info(f"📊 **Korelasi PPSA vs Tebus:** {correlation:.3f} ({'Positif Kuat' if correlation > 0.5 else 'Moderat' if correlation > 0.3 else 'Lemah' if correlation > 0 else 'Sangat Lemah'})")
        
        st.markdown('</div>', unsafe_allow_html=True)

    with tab3:
        # Deep Insights Tab
        st.markdown('<div class="content-container">', unsafe_allow_html=True)
        st.markdown('<h2 class="section-header">🔍 Advanced Analytics & Deep Insights</h2>', unsafe_allow_html=True)
        
        # Correlation Analysis
        st.subheader("🔗 Component Correlation Analysis")
        corr_matrix = calculate_correlation_matrix(filtered_df)
        
        if not corr_matrix.empty:
            fig_corr = go.Figure(data=go.Heatmap(
                z=corr_matrix.values,
                x=corr_matrix.columns,
                y=corr_matrix.columns,
                colorscale='RdYlBu',
                zmid=0,
                text=corr_matrix.round(2).values,
                texttemplate="%{text}",
                textfont={"size": 12},
                hoverongaps=False
            ))
            
            fig_corr.update_layout(
                template='plotly_white',
                height=400,
                title="Correlation Matrix - PPSA Components"
            )
            
            st.plotly_chart(fig_corr, use_container_width=True)
            
            # Interpretation
            st.info("""
            **📊 Interpretasi Correlation Matrix:**
            - **Nilai mendekati +1**: Korelasi positif kuat (komponen bergerak searah)
            - **Nilai mendekati -1**: Korelasi negatif kuat (komponen bergerak berlawanan)
            - **Nilai mendekati 0**: Tidak ada korelasi linear
            """)
        
        # Outlier Detection
        st.subheader("🎯 Outlier Detection")
        outliers_df = detect_outliers(filtered_df)
        
        if not outliers_df.empty:
            col_outlier1, col_outlier2 = st.columns(2)
            
            with col_outlier1:
                exceptional_high = outliers_df[outliers_df['OUTLIER_TYPE'] == 'Exceptional High']
                if not exceptional_high.empty:
                    st.success(f"🌟 **Exceptional Performers** ({len(exceptional_high)} found)")
                    for _, row in exceptional_high.iterrows():
                        st.write(f"• {row['NAMA KASIR']}: {row['TOTAL SCORE PPSA']:.1f}")
            
            with col_outlier2:
                concerning_low = outliers_df[outliers_df['OUTLIER_TYPE'] == 'Concerning Low']
                if not concerning_low.empty:
                    st.error(f"⚠️ **Needs Attention** ({len(concerning_low)} found)")
                    for _, row in concerning_low.iterrows():
                        st.write(f"• {row['NAMA KASIR']}: {row['TOTAL SCORE PPSA']:.1f}")
        
        # Time Series Analysis
        if 'TANGGAL' in filtered_df.columns and not filtered_df.empty:
            st.subheader("📈 Time Series Analysis")
            
            daily_trend = filtered_df.groupby('TANGGAL').agg({
                'TOTAL SCORE PPSA': ['mean', 'std', 'count']
            }).reset_index()
            
            daily_trend.columns = ['TANGGAL', 'Mean_Score', 'Std_Score', 'Count']
            
            fig_timeseries = make_subplots(
                rows=2, cols=1,
                subplot_titles=('Daily Average Score Trend', 'Daily Performance Volatility'),
                vertical_spacing=0.15
            )
            
            # Mean trend
            fig_timeseries.add_trace(
                go.Scatter(
                    x=daily_trend['TANGGAL'],
                    y=daily_trend['Mean_Score'],
                    mode='lines+markers',
                    name='Average Score',
                    line=dict(color='#667eea', width=3)
                ),
                row=1, col=1
            )
            
            # Add target line
            fig_timeseries.add_hline(
                y=100, line_dash="dash", line_color="red",
                annotation_text="Target", row=1, col=1
            )
            
            # Volatility (std)
            fig_timeseries.add_trace(
                go.Scatter(
                    x=daily_trend['TANGGAL'],
                    y=daily_trend['Std_Score'],
                    mode='lines+markers',
                    name='Volatility (Std)',
                    line=dict(color='#f59e0b', width=2),
                    fill='tonexty'
                ),
                row=2, col=1
            )
            
            fig_timeseries.update_layout(
                template='plotly_white',
                height=600,
                showlegend=True
            )
            
            st.plotly_chart(fig_timeseries, use_container_width=True)
        
        st.markdown('</div>', unsafe_allow_html=True)

    with tab4:
        # Performance Alerts Tab
        st.markdown('<div class="content-container">', unsafe_allow_html=True)
        st.markdown('<h2 class="section-header">🚨 Performance Alerts & Action Items</h2>', unsafe_allow_html=True)
        
        # Generate alerts based on performance
        alerts = []
        
        if not filtered_df.empty:
            cashier_scores = calculate_aggregate_scores_per_cashier(filtered_df)
            
            # Critical performance alerts
            critical_performers = cashier_scores[cashier_scores['TOTAL SCORE PPSA'] < 80]
            if not critical_performers.empty:
                alerts.append({
                    'level': 'critical',
                    'title': f'🚨 Critical Performance Alert',
                    'message': f'{len(critical_performers)} kasir dengan performa < 80 poin',
                    'details': critical_performers[['NAMA KASIR', 'TOTAL SCORE PPSA']].to_dict('records'),
                    'action': 'Immediate coaching dan performance improvement plan diperlukan'
                })
            
            # Component-specific alerts
            overall_scores = calculate_overall_ppsa_breakdown(filtered_df)
            for comp, score in [('PSM', overall_scores['psm']), ('PWP', overall_scores['pwp']), 
                               ('SG', overall_scores['sg']), ('APC', overall_scores['apc'])]:
                target = {'PSM': 20, 'PWP': 25, 'SG': 30, 'APC': 25}[comp]
                if score < target * 0.8:  # Less than 80% of target
                    alerts.append({
                        'level': 'warning',
                        'title': f'⚠️ {comp} Component Alert',
                        'message': f'{comp} score ({score:.1f}) significantly below target ({target})',
                        'action': f'Focus training pada {comp} component untuk semua kasir'
                    })
            
            # Consistency alerts
            if 'CONSISTENCY' in cashier_scores.columns:
                inconsistent_performers = cashier_scores[cashier_scores['CONSISTENCY'] > 20]  # High std deviation
                if not inconsistent_performers.empty:
                    alerts.append({
                        'level': 'info',
                        'title': f'📊 Consistency Alert',
                        'message': f'{len(inconsistent_performers)} kasir dengan performa tidak konsisten',
                        'details': inconsistent_performers[['NAMA KASIR', 'CONSISTENCY']].to_dict('records'),
                        'action': 'Review work patterns dan provide stability coaching'
                    })
        
        # Display alerts
        if alerts:
            for alert in alerts:
                if alert['level'] == 'critical':
                    st.error(f"**{alert['title']}**\n\n{alert['message']}\n\n💡 **Action Required:** {alert['action']}")
                elif alert['level'] == 'warning':
                    st.warning(f"**{alert['title']}**\n\n{alert['message']}\n\n💡 **Recommendation:** {alert['action']}")
                else:
                    st.info(f"**{alert['title']}**\n\n{alert['message']}\n\n💡 **Suggestion:** {alert['action']}")
                
                if 'details' in alert:
                    with st.expander("View Details"):
                        st.json(alert['details'])
        else:
            st.success("✅ No critical performance alerts. All systems operating within normal parameters!")
        
        # Action Plan Generator
        st.subheader("🎯 Automated Action Plan")
        
        if st.button("Generate Action Plan", type="primary"):
            action_plan = []
            
            overall_scores = calculate_overall_ppsa_breakdown(filtered_df)
            
            # Overall performance actions
            if overall_scores['total'] < 100:
                gap = 100 - overall_scores['total']
                action_plan.append(f"1. **Close Performance Gap**: Focus on improving total score by {gap:.1f} points")
            
            # Component-specific actions
            targets = {'PSM': 20, 'PWP': 25, 'SG': 30, 'APC': 25}
            priorities = []
            for comp in ['PSM', 'PWP', 'SG', 'APC']:
                score = overall_scores[comp.lower()]
                target = targets[comp]
                if score < target:
                    gap_pct = ((target - score) / target) * 100
                    priorities.append((comp, gap_pct))
            
            priorities.sort(key=lambda x: x[1], reverse=True)
            
            for i, (comp, gap_pct) in enumerate(priorities[:2]):  # Top 2 priorities
                action_plan.append(f"{i+2}. **Improve {comp} Performance**: {gap_pct:.0f}% gap from target - implement targeted training")
            
            # Individual coaching
            if not filtered_df.empty:
                cashier_scores = calculate_aggregate_scores_per_cashier(filtered_df)
                bottom_performers = cashier_scores.tail(3)
                if not bottom_performers.empty:
                    names = ", ".join(bottom_performers['NAMA KASIR'].tolist())
                    action_plan.append(f"{len(action_plan)+1}. **Individual Coaching**: Provide additional support for {names}")
            
            # Display action plan
            st.success("🎯 **Action Plan Generated:**")
            for action in action_plan:
                st.write(action)
        
        st.markdown('</div>', unsafe_allow_html=True)

    with tab5:
        # Performance Shift Tab - PERBAIKAN LENGKAP
        st.markdown('<div class="content-container">', unsafe_allow_html=True)
        st.markdown('<h2 class="section-header">🕐 Performance Shift Analysis</h2>', unsafe_allow_html=True)
        
        if not filtered_df.empty and 'SHIFT' in filtered_df.columns:
            # Calculate shift performance
            shift_performance = calculate_shift_performance(filtered_df)
            
            if not shift_performance.empty:
                # Shift Performance Summary
                st.subheader("📊 Shift Performance Summary")
                
                col1, col2, col3 = st.columns(3)
                
                # Best performing shift - handle potential NaN values
                if not shift_performance['TOTAL SCORE PPSA'].isna().all():
                    best_shift = shift_performance.loc[shift_performance['TOTAL SCORE PPSA'].idxmax()]
                    best_shift_name = best_shift['SHIFT'] if pd.notna(best_shift['SHIFT']) else "Unknown"
                    best_shift_score = best_shift['TOTAL SCORE PPSA'] if pd.notna(best_shift['TOTAL SCORE PPSA']) else 0.0
                    
                    st.markdown(f"""
                    <div class="metric-card">
                        <div class="metric-label">
                            {get_svg_icon("trophy", size=20, color="#10b981")} 
                            Best Performing Shift
                        </div>
                        <div class="metric-value" style="color: #10b981;">
                            {best_shift_name}
                        </div>
                        <div style="font-size: 0.8rem; color: #64748b; margin-top: 0.5rem;">
                            Total Score: {best_shift_score:.1f}
                        </div>
                    </div>
                    """, unsafe_allow_html=True)
                else:
                    st.markdown(f"""
                    <div class="metric-card">
                        <div class="metric-label">
                            {get_svg_icon("trophy", size=20, color="#10b981")} 
                            Best Performing Shift
                        </div>
                        <div class="metric-value" style="color: #10b981;">
                            No Data
                        </div>
                        <div style="font-size: 0.8rem; color: #64748b; margin-top: 0.5rem;">
                            Total Score: N/A
                        </div>
                    </div>
                    """, unsafe_allow_html=True)
                
                # Worst performing shift - handle potential NaN values
                if not shift_performance['TOTAL SCORE PPSA'].isna().all():
                    worst_shift = shift_performance.loc[shift_performance['TOTAL SCORE PPSA'].idxmin()]
                    worst_shift_name = worst_shift['SHIFT'] if pd.notna(worst_shift['SHIFT']) else "Unknown"
                    worst_shift_score = worst_shift['TOTAL SCORE PPSA'] if pd.notna(worst_shift['TOTAL SCORE PPSA']) else 0.0
                    
                    st.markdown(f"""
                    <div class="metric-card">
                        <div class="metric-label">
                            {get_svg_icon("alert", size=20, color="#ef4444")} 
                            Needs Improvement
                        </div>
                        <div class="metric-value" style="color: #ef4444;">
                            {worst_shift_name}
                        </div>
                        <div style="font-size: 0.8rem; color: #64748b; margin-top: 0.5rem;">
                            Total Score: {worst_shift_score:.1f}
                        </div>
                    </div>
                    """, unsafe_allow_html=True)
                else:
                    st.markdown(f"""
                    <div class="metric-card">
                        <div class="metric-label">
                            {get_svg_icon("alert", size=20, color="#ef4444")} 
                            Needs Improvement
                        </div>
                        <div class="metric-value" style="color: #ef4444;">
                            No Data
                        </div>
                        <div style="font-size: 0.8rem; color: #64748b; margin-top: 0.5rem;">
                            Total Score: N/A
                        </div>
                    </div>
                    """, unsafe_allow_html=True)
                
                # Most consistent shift - handle potential NaN values
                if not shift_performance['Score Std Dev'].isna().all():
                    most_consistent_shift = shift_performance.loc[shift_performance['Score Std Dev'].idxmin()]
                    most_consistent_name = most_consistent_shift['SHIFT'] if pd.notna(most_consistent_shift['SHIFT']) else "Unknown"
                    most_consistent_std = most_consistent_shift['Score Std Dev'] if pd.notna(most_consistent_shift['Score Std Dev']) else 0.0
                    
                    st.markdown(f"""
                    <div class="metric-card">
                        <div class="metric-label">
                            {get_svg_icon("insights", size=20, color="#667eea")} 
                            Most Consistent
                        </div>
                        <div class="metric-value" style="color: #667eea;">
                            {most_consistent_name}
                        </div>
                        <div style="font-size: 0.8rem; color: #64748b; margin-top: 0.5rem;">
                            Std Dev: {most_consistent_std:.1f}
                        </div>
                    </div>
                    """, unsafe_allow_html=True)
                else:
                    st.markdown(f"""
                    <div class="metric-card">
                        <div class="metric-label">
                            {get_svg_icon("insights", size=20, color="#667eea")} 
                            Most Consistent
                        </div>
                        <div class="metric-value" style="color: #667eea;">
                            No Data
                        </div>
                        <div style="font-size: 0.8rem; color: #64748b; margin-top: 0.5rem;">
                            Std Dev: N/A
                        </div>
                    </div>
                    """, unsafe_allow_html=True)
                
                # Shift Performance Comparison Chart
                st.subheader("📈 Shift Performance Comparison")
                
                # Filter out NaN values for chart
                chart_data = shift_performance.dropna(subset=['TOTAL SCORE PPSA', 'Median Score'])
                
                if not chart_data.empty:
                    fig_shift = go.Figure()
                    
                    # Add bars for total score
                    fig_shift.add_trace(go.Bar(
                        x=chart_data['SHIFT'],
                        y=chart_data['TOTAL SCORE PPSA'],
                        name='Total Score',
                        marker_color=['#667eea', '#764ba2', '#f093fb'][:len(chart_data)],
                        text=[f"{score:.1f}" for score in chart_data['TOTAL SCORE PPSA']],
                        textposition='outside'
                    ))
                    
                    # Add line for median score
                    fig_shift.add_trace(go.Scatter(
                        x=chart_data['SHIFT'],
                        y=chart_data['Median Score'],
                        mode='markers+lines',
                        name='Median Score',
                        marker=dict(size=10, color='#ef4444'),
                        line=dict(color='#ef4444', width=2)
                    ))
                    
                    # Add target line
                    fig_shift.add_hline(
                        y=100, 
                        line_dash="dash", 
                        line_color="red",
                        annotation_text="Target (100)"
                    )
                    
                    fig_shift.update_layout(
                        template='plotly_white',
                        height=400,
                        showlegend=True,
                        yaxis_title='Score',
                        xaxis_title='Shift',
                        title="Performance Comparison by Shift"
                    )
                    
                    st.plotly_chart(fig_shift, use_container_width=True)
                else:
                    st.warning("⚠️ Tidak ada data yang valid untuk ditampilkan dalam grafik.")
                
                # Component Performance by Shift
                st.subheader("🎯 Component Performance by Shift")
                
                # Filter out NaN values for component chart
                component_cols = ['SHIFT', 'SCORE PSM', 'SCORE PWP', 'SCORE SG', 'SCORE APC']
                component_data = shift_performance.dropna(subset=component_cols)
                
                if not component_data.empty:
                    # Create a dataframe for component comparison
                    component_df = component_data[component_cols].melt(
                        id_vars=['SHIFT'], 
                        var_name='Component', 
                        value_name='Score'
                    )
                    
                    # Clean component names
                    component_df['Component'] = component_df['Component'].str.replace('SCORE ', '')
                    
                    fig_component = px.bar(
                        component_df, 
                        x='Component', 
                        y='Score', 
                        color='SHIFT',
                        barmode='group',
                        color_discrete_map={
                            'Shift 1 (Pagi)': '#667eea', 
                            'Shift 2 (Siang)': '#764ba2', 
                            'Shift 3 (Malam)': '#f093fb'
                        },
                        title="Component Scores by Shift"
                    )
                    
                    fig_component.update_layout(
                        template='plotly_white',
                        height=400,
                        yaxis_title='Score',
                        xaxis_title='Component'
                    )
                    
                    st.plotly_chart(fig_component, use_container_width=True)
                else:
                    st.warning("⚠️ Tidak ada data komponen yang valid untuk ditampilkan dalam grafik.")
                
                # Tebus Performance by Shift
                if 'ACV TEBUS (%)' in shift_performance.columns:
                    st.subheader("🛒 Tebus Performance by Shift")
                    
                    # Filter out NaN values for tebus chart
                    tebus_data = shift_performance.dropna(subset=['ACV TEBUS (%)'])
                    
                    if not tebus_data.empty:
                        fig_tebus_shift = go.Figure()
                        
                        colors = ['#10b981' if acv >= 100 else '#f59e0b' if acv >= 80 else '#ef4444' 
                                 for acv in tebus_data['ACV TEBUS (%)']]
                        
                        fig_tebus_shift.add_trace(go.Bar(
                            x=tebus_data['SHIFT'],
                            y=tebus_data['ACV TEBUS (%)'],
                            marker_color=colors,
                            text=[f"{acv:.1f}%" for acv in tebus_data['ACV TEBUS (%)']],
                            textposition='outside'
                        ))
                        
                        fig_tebus_shift.add_hline(
                            y=100, 
                            line_dash="dash", 
                            line_color="red",
                            annotation_text="Target (100%)"
                        )
                        
                        fig_tebus_shift.update_layout(
                            template='plotly_white',
                            height=350,
                            showlegend=False,
                            yaxis_title='ACV Tebus (%)',
                            xaxis_title='Shift',
                            title="Tebus Achievement by Shift"
                        )
                        
                        st.plotly_chart(fig_tebus_shift, use_container_width=True)
                    else:
                        st.warning("⚠️ Tidak ada data Tebus yang valid untuk ditampilkan dalam grafik.")
                
                # Detailed Shift Performance Table
                st.subheader("📋 Detailed Shift Performance")
                
                # Format the dataframe for display
                display_shift_df = shift_performance.copy()
                
                # Add performance categories
                display_shift_df['Performance Category'] = display_shift_df['TOTAL SCORE PPSA'].apply(
                    lambda x: "🏆 Excellent" if pd.notna(x) and x >= 120 else
                             "⭐ Good" if pd.notna(x) and x >= 100 else
                             "⚠️ Needs Improvement" if pd.notna(x) and x >= 80 else
                             "🚨 Critical" if pd.notna(x) else "📊 No Data"
                )
                
                # PERBAIKAN: Buat kolom baru dengan format persentase yang benar
                if 'ACV TEBUS (%)' in display_shift_df.columns:
                    display_shift_df['ACV TEBUS FORMATTED'] = display_shift_df['ACV TEBUS (%)'].apply(lambda x: f"{x:.1f}%")
                
                # Select columns to display
                display_cols = [
                    'SHIFT', 'TOTAL SCORE PPSA', 'Median Score', 'Performance Category',
                    'SCORE PSM', 'SCORE PWP', 'SCORE SG', 'SCORE APC',
                    'ACV TEBUS FORMATTED', 'Record Count'
                ]
                
                # Filter to only available columns
                available_cols = [col for col in display_cols if col in display_shift_df.columns]
                
                st.dataframe(
                    display_shift_df[available_cols],
                    use_container_width=True,
                    column_config={
                        'SHIFT': st.column_config.TextColumn("Shift", width="small"),
                        'TOTAL SCORE PPSA': st.column_config.NumberColumn("Total Score", format="%.1f", width="small"),
                        'Median Score': st.column_config.NumberColumn("Median Score", format="%.1f", width="small"),
                        'Performance Category': st.column_config.TextColumn("Category", width="medium"),
                        'SCORE PSM': st.column_config.NumberColumn("PSM", format="%.1f", width="small"),
                        'SCORE PWP': st.column_config.NumberColumn("PWP", format="%.1f", width="small"),
                        'SCORE SG': st.column_config.NumberColumn("SG", format="%.1f", width="small"),
                        'SCORE APC': st.column_config.NumberColumn("APC", format="%.1f", width="small"),
                        'ACV TEBUS FORMATTED': st.column_config.TextColumn("Tebus ACV", width="small"),  # PERBAIKAN: Gunakan TextColumn
                        'Record Count': st.column_config.NumberColumn("Records", width="small"),
                    },
                    hide_index=True
                )
                
                # Shift Performance Insights
                st.subheader("🤖 Shift Performance Insights")
                
                # Generate insights
                shift_insights = []
                
                # Best performing shift - handle potential NaN values
                if not shift_performance['TOTAL SCORE PPSA'].isna().all():
                    best_shift = shift_performance.loc[shift_performance['TOTAL SCORE PPSA'].idxmax()]
                    best_shift_name = best_shift['SHIFT'] if pd.notna(best_shift['SHIFT']) else "Unknown"
                    best_shift_score = best_shift['TOTAL SCORE PPSA'] if pd.notna(best_shift['TOTAL SCORE PPSA']) else 0.0
                    best_shift_median = best_shift['Median Score'] if pd.notna(best_shift['Median Score']) else 0.0
                    
                    shift_insights.append({
                        'type': 'success',
                        'title': f'🏆 Best Performing Shift: {best_shift_name}',
                        'text': f"Dengan total score {best_shift_score:.1f} dan median {best_shift_median:.1f}"
                    })
                else:
                    shift_insights.append({
                        'type': 'warning',
                        'title': '📊 No Shift Data Available',
                        'text': "Tidak ada data shift yang valid untuk dianalisis"
                    })
                
                # Most consistent shift - handle potential NaN values
                if not shift_performance['Score Std Dev'].isna().all():
                    most_consistent = shift_performance.loc[shift_performance['Score Std Dev'].idxmin()]
                    most_consistent_name = most_consistent['SHIFT'] if pd.notna(most_consistent['SHIFT']) else "Unknown"
                    most_consistent_std = most_consistent['Score Std Dev'] if pd.notna(most_consistent['Score Std Dev']) else 0.0
                    
                    shift_insights.append({
                        'type': 'info',
                        'title': f'🎯 Most Consistent Shift: {most_consistent_name}',
                        'text': f"Dengan standar deviasi terendah ({most_consistent_std:.1f})"
                    })
                
                # Tebus performance - handle potential NaN values
                if 'ACV TEBUS (%)' in shift_performance.columns and not shift_performance['ACV TEBUS (%)'].isna().all():
                    best_tebus = shift_performance.loc[shift_performance['ACV TEBUS (%)'].idxmax()]
                    best_tebus_name = best_tebus['SHIFT'] if pd.notna(best_tebus['SHIFT']) else "Unknown"
                    best_tebus_acv = best_tebus['ACV TEBUS (%)'] if pd.notna(best_tebus['ACV TEBUS (%)']) else 0.0
                    
                    if best_tebus_acv >= 100:
                        shift_insights.append({
                            'type': 'success',
                            'title': f'🛒 Best Tebus Performance: {best_tebus_name}',
                            'text': f"Mencapai {best_tebus_acv:.1f}% dari target"
                        })
                    else:
                        worst_tebus = shift_performance.loc[shift_performance['ACV TEBUS (%)'].idxmin()]
                        worst_tebus_name = worst_tebus['SHIFT'] if pd.notna(worst_tebus['SHIFT']) else "Unknown"
                        worst_tebus_acv = worst_tebus['ACV TEBUS (%)'] if pd.notna(worst_tebus['ACV TEBUS (%)']) else 0.0
                        
                        shift_insights.append({
                            'type': 'warning',
                            'title': f'⚠️ Tebus Performance Needs Improvement: {worst_tebus_name}',
                            'text': f"Hanya mencapai {worst_tebus_acv:.1f}% dari target"
                        })
                
                # Display insights
                for insight in shift_insights:
                    card_class = "insight-card" if insight['type'] in ['success', 'info'] else "alert-card"
                    st.markdown(f"""
                    <div class="{card_class}">
                        <div class="{'insight-title' if insight['type'] in ['success', 'info'] else 'alert-title'}">
                            {insight['title']}
                        </div>
                        <div class="{'insight-text' if insight['type'] in ['success', 'info'] else 'insight-text'}">
                            {insight['text']}
                        </div>
                    </div>
                    """, unsafe_allow_html=True)
            else:
                st.warning("⚠️ Tidak ada data shift yang tersedia untuk dianalisis.")
        else:
            st.warning("⚠️ Data shift tidak tersedia. Pastikan data memiliki kolom SHIFT.")
        
        st.markdown('</div>', unsafe_allow_html=True)

    with tab6:
        # Performance Per Hari Tab
        st.markdown('<div class="content-container">', unsafe_allow_html=True)
        st.markdown('<h2 class="section-header">📅 Performance Per Hari Analysis</h2>', unsafe_allow_html=True)
        
        if not filtered_df.empty and 'TANGGAL' in filtered_df.columns:
            # Calculate daily performance
            daily_performance = calculate_daily_performance(filtered_df)
            
            if not daily_performance.empty:
                # Daily Performance Summary
                st.subheader("📊 Daily Performance Summary")
                
                col1, col2, col3 = st.columns(3)
                
                with col1:
                    best_day = daily_performance.loc[daily_performance['TOTAL SCORE PPSA'].idxmax()]
                    st.markdown(f"""
                    <div class="metric-card">
                        <div class="metric-label">
                            {get_svg_icon("trophy", size=20, color="#10b981")} 
                            Best Performing Day
                        </div>
                        <div class="metric-value" style="color: #10b981; font-size: 1.5rem;">
                            {best_day['TANGGAL'].strftime('%d %b %Y')}
                        </div>
                        <div style="font-size: 0.8rem; color: #64748b; margin-top: 0.5rem;">
                            Score: {best_day['TOTAL SCORE PPSA']:.1f}
                        </div>
                    </div>
                    """, unsafe_allow_html=True)
                
                with col2:
                    worst_day = daily_performance.loc[daily_performance['TOTAL SCORE PPSA'].idxmin()]
                    st.markdown(f"""
                    <div class="metric-card">
                        <div class="metric-label">
                            {get_svg_icon("alert", size=20, color="#ef4444")} 
                            Needs Improvement
                        </div>
                        <div class="metric-value" style="color: #ef4444; font-size: 1.5rem;">
                            {worst_day['TANGGAL'].strftime('%d %b %Y')}
                        </div>
                        <div style="font-size: 0.8rem; color: #64748b; margin-top: 0.5rem;">
                            Score: {worst_day['TOTAL SCORE PPSA']:.1f}
                        </div>
                    </div>
                    """, unsafe_allow_html=True)
                
                with col3:
                    most_consistent_day = daily_performance.loc[daily_performance['Score Std Dev'].idxmin()]
                    st.markdown(f"""
                    <div class="metric-card">
                        <div class="metric-label">
                            {get_svg_icon("insights", size=20, color="#667eea")} 
                            Most Consistent
                        </div>
                        <div class="metric-value" style="color: #667eea; font-size: 1.5rem;">
                            {most_consistent_day['TANGGAL'].strftime('%d %b %Y')}
                        </div>
                        <div style="font-size: 0.8rem; color: #64748b; margin-top: 0.5rem;">
                            Std Dev: {most_consistent_day['Score Std Dev']:.1f}
                        </div>
                    </div>
                    """, unsafe_allow_html=True)
                
                # Daily Performance Trend Chart
                st.subheader("📈 Daily Performance Trend")
                
                fig_daily = go.Figure()
                
                # Add line for total score
                fig_daily.add_trace(go.Scatter(
                    x=daily_performance['TANGGAL'],
                    y=daily_performance['TOTAL SCORE PPSA'],
                    mode='lines+markers',
                    name='Total Score',
                    line=dict(color='#667eea', width=3),
                    marker=dict(size=8)
                ))
                
                # Add line for median score
                fig_daily.add_trace(go.Scatter(
                    x=daily_performance['TANGGAL'],
                    y=daily_performance['Median Score'],
                    mode='lines+markers',
                    name='Median Score',
                    line=dict(color='#764ba2', width=2),
                    marker=dict(size=6)
                ))
                
                # Add target line
                fig_daily.add_hline(
                    y=100, 
                    line_dash="dash", 
                    line_color="red",
                    annotation_text="Target (100)"
                )
                
                # Add shaded area for standard deviation
                fig_daily.add_trace(go.Scatter(
                    x=daily_performance['TANGGAL'],
                    y=daily_performance['TOTAL SCORE PPSA'] + daily_performance['Score Std Dev'],
                    mode='lines',
                    line=dict(width=0),
                    showlegend=False
                ))
                
                fig_daily.add_trace(go.Scatter(
                    x=daily_performance['TANGGAL'],
                    y=daily_performance['TOTAL SCORE PPSA'] - daily_performance['Score Std Dev'],
                    mode='lines',
                    line=dict(width=0),
                    fill='tonexty',
                    fillcolor='rgba(102, 126, 234, 0.2)',
                    name='Standard Deviation',
                    showlegend=True
                ))
                
                fig_daily.update_layout(
                    template='plotly_white',
                    height=400,
                    showlegend=True,
                    yaxis_title='Score',
                    xaxis_title='Date',
                    title="Daily Performance Trend with Standard Deviation"
                )
                
                st.plotly_chart(fig_daily, use_container_width=True)
                
                # Day of Week Performance
                day_performance = calculate_day_of_week_performance(filtered_df)
                
                if not day_performance.empty:
                    st.subheader("📅 Performance by Day of Week")
                    
                    fig_day_week = go.Figure()
                    
                    # Add bars for average score
                    fig_day_week.add_trace(go.Bar(
                        x=day_performance['Day'],
                        y=day_performance['Avg Score'],
                        name='Average Score',
                        marker_color=['#667eea', '#764ba2', '#f093fb', '#4facfe', '#00f2fe', '#fa709a', '#fee140'],
                        text=[f"{score:.1f}" for score in day_performance['Avg Score']],
                        textposition='outside'
                    ))
                    
                    # Add target line
                    fig_day_week.add_hline(
                        y=100, 
                        line_dash="dash", 
                        line_color="red",
                        annotation_text="Target (100)"
                    )
                    
                    fig_day_week.update_layout(
                        template='plotly_white',
                        height=400,
                        showlegend=False,
                        yaxis_title='Score',
                        xaxis_title='Day of Week',
                        title="Performance by Day of Week"
                    )
                    
                    st.plotly_chart(fig_day_week, use_container_width=True)
                    
                    # Component Performance by Day of Week
                    st.subheader("🎯 Component Performance by Day of Week")
                    
                    # Create a dataframe for component comparison
                    component_cols = ['Day', 'Avg PSM Score', 'Avg PWP Score', 'Avg SG Score', 'Avg APC Score']
                    component_df = day_performance[component_cols].melt(
                        id_vars=['Day'], 
                        var_name='Component', 
                        value_name='Score'
                    )
                    
                    # Clean component names
                    component_df['Component'] = component_df['Component'].str.replace('Avg ', '').str.replace(' Score', '')
                    
                    fig_component_day = px.bar(
                        component_df, 
                        x='Day', 
                        y='Score', 
                        color='Component',
                        barmode='group',
                        color_discrete_map={
                            'PSM': '#667eea', 
                            'PWP': '#764ba2', 
                            'SG': '#f093fb',
                            'APC': '#4facfe'
                        },
                        title="Component Scores by Day of Week"
                    )
                    
                    fig_component_day.update_layout(
                        template='plotly_white',
                        height=400,
                        yaxis_title='Score',
                        xaxis_title='Day of Week'
                    )
                    
                    st.plotly_chart(fig_component_day, use_container_width=True)
                
                # Tebus Performance by Day
                if 'ACV TEBUS (%)' in daily_performance.columns:
                    st.subheader("🛒 Tebus Performance by Day")
                    
                    fig_tebus_daily = go.Figure()
                    
                    colors = ['#10b981' if acv >= 100 else '#f59e0b' if acv >= 80 else '#ef4444' 
                             for acv in daily_performance['ACV TEBUS (%)']]
                    
                    fig_tebus_daily.add_trace(go.Bar(
                        x=daily_performance['TANGGAL'],
                        y=daily_performance['ACV TEBUS (%)'],
                        marker_color=colors,
                        text=[f"{acv:.1f}%" for acv in daily_performance['ACV TEBUS (%)']],
                        textposition='outside'
                    ))
                    
                    fig_tebus_daily.add_hline(
                        y=100, 
                        line_dash="dash", 
                        line_color="red",
                        annotation_text="Target (100%)"
                    )
                    
                    fig_tebus_daily.update_layout(
                        template='plotly_white',
                        height=350,
                        showlegend=False,
                        yaxis_title='ACV Tebus (%)',
                        xaxis_title='Date',
                        title="Tebus Achievement by Day"
                    )
                    
                    st.plotly_chart(fig_tebus_daily, use_container_width=True)
                
                # Detailed Daily Performance Table
                st.subheader("📋 Detailed Daily Performance")
                
                # Format the dataframe for display
                display_daily_df = daily_performance.copy()
                
                # Add performance categories
                display_daily_df['Performance Category'] = display_daily_df['TOTAL SCORE PPSA'].apply(
                    lambda x: "🏆 Excellent" if x >= 120 else
                             "⭐ Good" if x >= 100 else
                             "⚠️ Needs Improvement" if x >= 80 else
                             "🚨 Critical"
                )
                
                # Format date for display
                display_daily_df['Date'] = display_daily_df['TANGGAL'].dt.strftime('%d %b %Y')
                
                # PERBAIKAN: Buat kolom baru dengan format persentase yang benar
                if 'ACV TEBUS (%)' in display_daily_df.columns:
                    display_daily_df['ACV TEBUS FORMATTED'] = display_daily_df['ACV TEBUS (%)'].apply(lambda x: f"{x:.1f}%")
                
                # Select columns to display
                display_cols = [
                    'Date', 'Day of Week', 'TOTAL SCORE PPSA', 'Median Score', 'Performance Category',
                    'SCORE PSM', 'SCORE PWP', 'SCORE SG', 'SCORE APC',
                    'ACV TEBUS FORMATTED', 'Record Count'
                ]
                
                # Filter to only available columns
                available_cols = [col for col in display_cols if col in display_daily_df.columns]
                
                st.dataframe(
                    display_daily_df[available_cols],
                    use_container_width=True,
                    column_config={
                        'Date': st.column_config.TextColumn("Date", width="small"),
                        'Day of Week': st.column_config.TextColumn("Day", width="small"),
                        'TOTAL SCORE PPSA': st.column_config.NumberColumn("Total Score", format="%.1f", width="small"),
                        'Median Score': st.column_config.NumberColumn("Median Score", format="%.1f", width="small"),
                        'Performance Category': st.column_config.TextColumn("Category", width="medium"),
                        'SCORE PSM': st.column_config.NumberColumn("PSM", format="%.1f", width="small"),
                        'SCORE PWP': st.column_config.NumberColumn("PWP", format="%.1f", width="small"),
                        'SCORE SG': st.column_config.NumberColumn("SG", format="%.1f", width="small"),
                        'SCORE APC': st.column_config.NumberColumn("APC", format="%.1f", width="small"),
                        'ACV TEBUS FORMATTED': st.column_config.TextColumn("Tebus ACV", width="small"),  # PERBAIKAN: Gunakan TextColumn
                        'Record Count': st.column_config.NumberColumn("Records", width="small"),
                    },
                    hide_index=True
                )
                
                # Daily Performance Insights
                st.subheader("🤖 Daily Performance Insights")
                
                # Generate insights
                daily_insights = []
                
                # Best performing day
                best_day = daily_performance.loc[daily_performance['TOTAL SCORE PPSA'].idxmax()]
                daily_insights.append({
                    'type': 'success',
                    'title': f'🏆 Best Performing Day: {best_day["TANGGAL"].strftime("%d %b %Y")} ({best_day["Day of Week"]})',
                    'text': f"Dengan total score {best_day['TOTAL SCORE PPSA']:.1f} dan median {best_day['Median Score']:.1f}"
                })
                
                # Most consistent day
                most_consistent = daily_performance.loc[daily_performance['Score Std Dev'].idxmin()]
                daily_insights.append({
                    'type': 'info',
                    'title': f'🎯 Most Consistent Day: {most_consistent["TANGGAL"].strftime("%d %b %Y")} ({most_consistent["Day of Week"]})',
                    'text': f"Dengan standar deviasi terendah ({most_consistent['Score Std Dev']:.1f})"
                })
                
                # Best day of week
                if not day_performance.empty:
                    best_day_week = day_performance.loc[day_performance['Avg Score'].idxmax()]
                    daily_insights.append({
                        'type': 'success',
                        'title': f'📅 Best Day of Week: {best_day_week["Day"]}',
                        'text': f"Dengan rata-rata score {best_day_week['Avg Score']:.1f}"
                    })
                    
                    worst_day_week = day_performance.loc[day_performance['Avg Score'].idxmin()]
                    daily_insights.append({
                        'type': 'warning',
                        'title': f'📅 Worst Day of Week: {worst_day_week["Day"]}',
                        'text': f"Dengan rata-rata score {worst_day_week['Avg Score']:.1f}"
                    })
                
                # Tebus performance
                if 'ACV TEBUS (%)' in daily_performance.columns:
                    best_tebus = daily_performance.loc[daily_performance['ACV TEBUS (%)'].idxmax()]
                    if best_tebus['ACV TEBUS (%)'] >= 100:
                        daily_insights.append({
                            'type': 'success',
                            'title': f'🛒 Best Tebus Performance: {best_tebus["TANGGAL"].strftime("%d %b %Y")}',
                            'text': f"Mencapai {best_tebus['ACV TEBUS (%)']:.1f}% dari target"
                        })
                    else:
                        worst_tebus = daily_performance.loc[daily_performance['ACV TEBUS (%)'].idxmin()]
                        daily_insights.append({
                            'type': 'warning',
                            'title': f'⚠️ Tebus Performance Needs Improvement: {worst_tebus["TANGGAL"].strftime("%d %b %Y")}',
                            'text': f"Hanya mencapai {worst_tebus['ACV TEBUS (%)']:.1f}% dari target"
                        })
                
                # Display insights
                for insight in daily_insights:
                    card_class = "insight-card" if insight['type'] in ['success', 'info'] else "alert-card"
                    st.markdown(f"""
                    <div class="{card_class}">
                        <div class="{'insight-title' if insight['type'] in ['success', 'info'] else 'alert-title'}">
                            {insight['title']}
                        </div>
                        <div class="{'insight-text' if insight['type'] in ['success', 'info'] else 'insight-text'}">
                            {insight['text']}
                        </div>
                    </div>
                    """, unsafe_allow_html=True)
            else:
                st.warning("⚠️ Tidak ada data harian yang tersedia untuk dianalisis.")
        else:
            st.warning("⚠️ Data harian tidak tersedia. Pastikan data memiliki kolom TANGGAL.")
        
        st.markdown('</div>', unsafe_allow_html=True)

    # Footer
    st.markdown("<br><br>", unsafe_allow_html=True)
    st.markdown(f"""
    <div style='text-align: center; color: rgba(255,255,255,0.8); padding: 2rem; font-size: 0.9rem; 
                background: linear-gradient(135deg, rgba(255,255,255,0.1) 0%, rgba(248,249,255,0.1) 100%);
                border-radius: 15px; margin-top: 2rem;'>
        <strong>🚀 PPSA Analytics Dashboard v2.0</strong> • 
        {get_svg_icon("dashboard", size=16, color="rgba(255,255,255,0.8)")} 
        Powered by Streamlit & AI • © 2025<br>
        <small style="opacity: 0.7;">Advanced Analytics • Real-time Monitoring • Performance Optimization</small>
    </div>
    """, unsafe_allow_html=True)

if __name__ == "__main__":
    main()
