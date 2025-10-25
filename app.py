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
        "analytics": f'<svg width="{size}" height="{size}" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg"><path d="M19 3H5c-1.1 0-2 .9-2 2v14c0 1.1.9 2 2 2h14c1.1 0 2-.9 2-2V5c0-1.1-.9-2-2-2zM9 17H7v-7h2v7zm4 0h-2V7h2v10zm4 0h-2v-4h2v4z" fill="{color}"/></svg>',
        "store": f'<svg width="{size}" height="{size}" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg"><path d="M12 2L2 7v2c0 1.1.9 2 2 2h2v9h2v-9h4v9h2v-9h2c1.1 0 2-.9 2-2V7l-10-5z" fill="{color}"/></svg>',
        "medal": f'<svg width="{size}" height="{size}" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg"><path d="M12 2C6.48 2 2 6.48 2 12s4.48 10 10 10 10-4.48 10-10S17.52 2 12 2zm0 18c-4.41 0-8-3.59-8-8s3.59-8 8-8 8 3.59 8 8-3.59 8-8 8zm-2-8c0 1.1.9 2 2 2s2-.9 2-2-.9-2-2-2-2 .9-2 2z" fill="{color}"/></svg>',
        "refresh": f'<svg width="{size}" height="{size}" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg"><path d="M17.65 6.35C16.2 4.9 14.21 4 12 4c-4.42 0-7.99 3.58-7.99 8s3.57 8 7.99 8c3.73 0 6.84-2.55 7.73-6h-2.08c-.82 2.33-3.04 4-5.65 4-3.31 0-6-2.69-6-6s2.69-6 6-6c1.66 0 3.14.69 4.22 1.78L13 11h7V4l-2.35 2.35z" fill="{color}"/></svg>'
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
    margin-bottom: 0.5rem;
    letter-spacing: -1px;
    display: flex;
    align-items: center;
    justify-content: center;
    gap: 1rem;
    animation: slideInFromTop 0.8s ease-out;
}

.store-name {
    font-size: 1.8rem;
    color: #64748b;
    font-weight: 600;
    margin-bottom: 1rem;
    display: flex;
    align-items: center;
    justify-content: center;
    gap: 0.5rem;
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
    
    .store-name {
        font-size: 1.4rem;
    }
    
    .metric-card {
        padding: 1.5rem 1rem;
    }
    
    .content-container {
        padding: 1.5rem;
    }
}

/* REFRESH BUTTON STYLING */
.refresh-button-container {
    display: flex;
    justify-content: center;
    align-items: center;
    gap: 1rem;
    margin: 1rem 0;
}

.last-update-indicator {
    background: linear-gradient(135deg, rgba(255,255,255,0.95) 0%, rgba(248,249,255,0.95) 100%);
    backdrop-filter: blur(20px);
    border-radius: var(--border-radius-sm);
    padding: 1rem 1.5rem;
    box-shadow: var(--card-shadow);
    border: 1px solid rgba(102, 126, 234, 0.1);
    text-align: center;
    margin-bottom: 1rem;
}

.last-update-text {
    font-size: 0.9rem;
    color: #64748b;
    font-weight: 600;
    display: flex;
    align-items: center;
    justify-content: center;
    gap: 0.5rem;
}

.last-update-time {
    font-size: 1.1rem;
    font-weight: 800;
    background: var(--primary-gradient);
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
    background-clip: text;
    margin-top: 0.25rem;
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

# ... (semua fungsi lainnya tetap sama, tidak berubah)

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
    
    return insights

# --- MAIN DASHBOARD ---
def main():
    # Initialize session state for last update time
    if 'last_update_time' not in st.session_state:
        st.session_state.last_update_time = datetime.now()
    
    # Dashboard Header - PERBAIKAN: Tambahkan nama toko
    st.markdown(f"""
    <div class="dashboard-header">
        <h1 class="main-title">
            {get_svg_icon("dashboard", size=60, color="#667eea")}
            PPSA Analytics Dashboard
        </h1>
        <div class="store-name">
            {get_svg_icon("store", size=24, color="#764ba2")}
            2GC6 BAROS PANDEGLANG
        </div>
        <p class="subtitle">
            Platform <strong>analytics</strong> komprehensif untuk monitoring real-time 
            performa <strong>PPSA</strong> (PSM, PWP, SG, APC) dan <strong>Tebus Suuegerr</strong> 
            dengan insights AI-powered untuk optimasi performa tim.
        </p>
    </div>
    """, unsafe_allow_html=True)

    # Refresh Button and Last Update Indicator
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        st.markdown('<div class="refresh-button-container">', unsafe_allow_html=True)
        
        # Manual Refresh Button
        if st.button(
            "🔄 Refresh Data Sekarang", 
            type="primary",
            use_container_width=True,
            help="Klik untuk memperbarui data terbaru dari Google Sheets"
        ):
            # Clear cache to force reload
            st.cache_data.clear()
            st.session_state.last_update_time = datetime.now()
            st.rerun()
        
        st.markdown('</div>', unsafe_allow_html=True)
        
        # Last Update Indicator
        last_update_str = st.session_state.last_update_time.strftime("%d %B %Y %H:%M:%S")
        st.markdown(f"""
        <div class="last-update-indicator">
            <div class="last-update-text">
                {get_svg_icon("calendar", size=16, color="#667eea")}
                Data Terakhir Di-update:
            </div>
            <div class="last-update-time">{last_update_str}</div>
        </div>
        """, unsafe_allow_html=True)

    # Load and process data
    with st.spinner('🔄 Memuat data dari Google Sheets...'):
        raw_df = load_data_from_gsheet()
    
    if raw_df.empty:
        st.error("❌ Tidak dapat memuat data. Silakan periksa koneksi Google Sheets Anda.")
        return

    processed_df = process_data(raw_df.copy())
    
    # Sidebar filters
    with st.sidebar:
        st.markdown("### ⚙️ Filter & Pengaturan")
        
        # Tambahkan informasi last update di sidebar juga
        st.markdown(f"""
        <div style="background: linear-gradient(135deg, rgba(102,126,234,0.1) 0%, rgba(118,75,162,0.1) 100%); 
                    padding: 1rem; border-radius: 10px; margin-bottom: 1rem;">
            <div style="font-size: 0.8rem; color: #64748b; font-weight: 600;">
                {get_svg_icon("refresh", size=14, color="#667eea")}
                Terakhir Update:
            </div>
            <div style="font-size: 0.9rem; color: #1e293b; font-weight: 700;">
                {st.session_state.last_update_time.strftime("%d %b %Y %H:%M")}
            </div>
        </div>
        """, unsafe_allow_html=True)
        
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

    # ... (rest of the code for tabs and analytics remains exactly the same)

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

        # ... (rest of tab1 content remains exactly the same)

    # ... (other tabs remain exactly the same)

    # Footer dengan informasi last update
    st.markdown("<br><br>", unsafe_allow_html=True)
    st.markdown(f"""
    <div style='text-align: center; color: rgba(255,255,255,0.8); padding: 2rem; font-size: 0.9rem; 
                background: linear-gradient(135deg, rgba(255,255,255,0.1) 0%, rgba(248,249,255,0.1) 100%);
                border-radius: 15px; margin-top: 2rem;'>
        <strong>🚀 PPSA Analytics Dashboard v2.0</strong> • 
        {get_svg_icon("dashboard", size=16, color="rgba(255,255,255,0.8)")} 
        Powered by Streamlit & AI • © 2025<br>
        <small style="opacity: 0.7;">Data terakhir di-update: {st.session_state.last_update_time.strftime("%d %B %Y %H:%M:%S")}</small>
    </div>
    """, unsafe_allow_html=True)

if __name__ == "__main__":
    main()
