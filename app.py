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
        "correlation": f'<svg width="{size}" height="{size}" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg"><path d="M19 3H5c-1.1 0-2 .9-2 2v14c0 1.1.9 2 2 2h14c1.1 0 2-.9 2-2V5c0-1.1-.9-2-2-2zM9 17H7v-7h2v7zm4 0h-2V7h2v10zm4 0h-2v-4h2v4z" fill="{color}"/></svg>'
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
    
    return df

def calculate_overall_ppsa_breakdown(df):
    """Calculate overall PPSA breakdown dengan weights standar"""
    if df.empty:
        return {'total': 0.0, 'psm': 0.0, 'pwp': 0.0, 'sg': 0.0, 'apc': 0.0}
    
    weights = {'PSM': 20, 'PWP': 25, 'SG': 30, 'APC': 25}
    scores = {'psm': 0.0, 'pwp': 0.0, 'sg': 0.0, 'apc': 0.0}
    
    # For PSM, PWP, SG - use sum aggregation
    for comp in ['PSM', 'PWP', 'SG']:
        total_target = df[f'{comp} Target'].sum()
        total_actual = df[f'{comp} Actual'].sum()
        if total_target > 0:
            acv = (total_actual / total_target) * 100
            scores[comp.lower()] = (acv * weights[comp]) / 100
    
    # For APC - use average
    avg_target_apc = df['APC Target'].mean()
    avg_actual_apc = df['APC Actual'].mean()
    if avg_target_apc > 0:
        acv_apc = (avg_actual_apc / avg_target_apc) * 100
        scores['apc'] = (acv_apc * weights['APC']) / 100
    
    scores['total'] = sum(scores.values())
    return scores

def calculate_aggregate_scores_per_cashier(df):
    """Calculate aggregate scores per cashier"""
    if df.empty or 'NAMA KASIR' not in df.columns:
        return pd.DataFrame()
    
    weights = {'PSM': 20, 'PWP': 25, 'SG': 30, 'APC': 25}
    
    agg_cols = {
        'PSM Target': 'sum', 'PSM Actual': 'sum',
        'PWP Target': 'sum', 'PWP Actual': 'sum',
        'SG Target': 'sum', 'SG Actual': 'sum',
        'APC Target': 'mean', 'APC Actual': 'mean'
    }
    
    valid_agg_cols = {col: func for col, func in agg_cols.items() if col in df.columns}
    aggregated_df = df.groupby('NAMA KASIR')[list(valid_agg_cols.keys())].agg(valid_agg_cols).reset_index()

    def calculate_score_from_agg(row, comp):
        total_target = row[f'{comp} Target']
        total_actual = row[f'{comp} Actual']
        if total_target == 0:
            return 0.0
        acv = (total_actual / total_target) * 100
        return (acv * weights[comp]) / 100

    for comp in ['PSM', 'PWP', 'SG', 'APC']:
        aggregated_df[f'SCORE {comp}'] = aggregated_df.apply(
            lambda row: calculate_score_from_agg(row, comp), axis=1
        )
    
    score_cols = [f'SCORE {comp}' for comp in ['PSM', 'PWP', 'SG', 'APC']]
    aggregated_df['TOTAL SCORE PPSA'] = aggregated_df[score_cols].sum(axis=1)
    
    # Add performance consistency metrics
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
    tab1, tab2, tab3, tab4 = st.tabs([
        "📈 PPSA Analytics", 
        "🛒 Tebus Analytics", 
        "🔍 Deep Insights",
        "🎯 Performance Alerts"
    ])

    with tab1:
        # Overall Performance Summary
        overall_scores = calculate_overall_ppsa_breakdown(filtered_df)
        
        st.markdown('<div class="content-container">', unsafe_allow_html=True)
        st.markdown('<h2 class="section-header">🏆 Executive Summary</h2>', unsafe_allow_html=True)
        
        # KPI Metrics
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
        
        st.markdown('</div>', unsafe_allow_html=True)

        # Total PPSA Card and Insights
        col_total, col_insights = st.columns([1, 2], gap="large")
        
        with col_total:
            gap_value = overall_scores['total'] - 100
            gap_color = '#10b981' if gap_value >= 0 else '#ef4444'
            
            st.markdown(f"""
            <div class="total-ppsa-card">
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
        
        with col_insights:
            st.markdown('<div class="content-container" style="height: 280px; overflow-y: auto;">', unsafe_allow_html=True)
            st.markdown('<h3 class="section-header" style="font-size: 1.5rem; margin-bottom: 1rem;">🤖 AI Insights</h3>', unsafe_allow_html=True)
            
            insights = calculate_performance_insights(filtered_df)
            for insight in insights[:4]:  # Show top 4 insights
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
            
            # Tebus Performance Chart
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
