import streamlit as st
import pandas as pd
import gspread
from gspread_dataframe import get_as_dataframe
from oauth2client.service_account import ServiceAccountCredentials
import plotly.express as px
import plotly.graph_objects as go
import plotly.io as pio
from datetime import datetime, timedelta
from typing import Optional, Tuple, List, Dict
import numpy as np
from scipy import stats
from plotly.subplots import make_subplots
import google.generativeai as genai
import re
import json
from io import BytesIO
import base64

# =========================================================
# ------------------- KONFIGURASI AWAL --------------------
# =========================================================
st.set_page_config(
    page_title="Dashboard PPSA & Tebus Murah 2025 - FIXED CALCULATION",
    page_icon="🚀",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Palet warna modern 2025
COLOR_SCHEME = {
    'primary': '#6366F1',      # Indigo modern
    'secondary': '#06B6D4',    # Cyan vibrant
    'success': '#10B981',      # Emerald
    'warning': '#F59E0B',      # Amber
    'danger': '#EF4444',       # Red
    'info': '#8B5CF6',         # Violet
    'accent': '#EC4899',       # Pink
    'dark': '#0F172A',         # Slate 900
    'light': '#F8FAFC',        # Slate 50
    'muted': '#64748B'         # Slate 500
}

PLOTLY_COLORS = list(COLOR_SCHEME.values())

# CSS Modern dengan Advanced Animations
MODERN_CSS = """
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;800&display=swap');

:root {
    --primary: #6366F1;
    --secondary: #06B6D4;
    --success: #10B981;
    --warning: #F59E0B;
    --danger: #EF4444;
    --info: #8B5CF6;
    --accent: #EC4899;
    --dark: #0F172A;
    --light: #F8FAFC;
    --muted: #64748B;
    --glass-bg: rgba(15, 23, 42, 0.75);
    --glass-border: rgba(255, 255, 255, 0.1);
    --blur: 20px;
    --transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
    --shadow: 0 25px 50px -12px rgba(0, 0, 0, 0.25);
    --shadow-lg: 0 25px 50px -12px rgba(0, 0, 0, 0.35);
}

* {
    box-sizing: border-box;
}

body {
    font-family: 'Inter', -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif !important;
    background: linear-gradient(135deg, 
        rgba(99, 102, 241, 0.1) 0%, 
        rgba(6, 182, 212, 0.1) 25%,
        rgba(16, 185, 129, 0.1) 50%,
        rgba(236, 72, 153, 0.1) 75%,
        rgba(139, 92, 246, 0.1) 100%),
        var(--dark);
    color: var(--light);
    min-height: 100vh;
}

[data-testid="stAppViewContainer"] {
    background: transparent;
}

.main .block-container {
    padding-top: 2rem;
    padding-bottom: 2rem;
    max-width: 100%;
}

/* Modern Header dengan fokus SG */
.hero-section {
    background: linear-gradient(135deg, 
        rgba(16, 185, 129, 0.2) 0%, 
        rgba(6, 182, 212, 0.2) 100%);
    border-radius: 24px;
    padding: 3rem 2rem;
    margin-bottom: 2rem;
    border: 1px solid var(--glass-border);
    backdrop-filter: blur(var(--blur));
    position: relative;
    overflow: hidden;
}

.hero-section::before {
    content: '';
    position: absolute;
    top: -50%;
    right: -20%;
    width: 200px;
    height: 200px;
    background: radial-gradient(circle, var(--success), transparent);
    opacity: 0.3;
    animation: float 6s ease-in-out infinite;
}

@keyframes float {
    0%, 100% { transform: translateY(0px) rotate(0deg); }
    50% { transform: translateY(-20px) rotate(180deg); }
}

.hero-title {
    font-size: clamp(2rem, 4vw, 3.5rem);
    font-weight: 800;
    background: linear-gradient(135deg, var(--success), var(--secondary));
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
    background-clip: text;
    margin-bottom: 1rem;
}

.hero-subtitle {
    font-size: 1.25rem;
    color: var(--muted);
    font-weight: 400;
    line-height: 1.6;
}

/* Highlight untuk SG */
.sg-highlight {
    background: linear-gradient(135deg, 
        rgba(16, 185, 129, 0.2), 
        rgba(6, 182, 212, 0.2));
    border: 2px solid var(--success);
    border-radius: 16px;
    padding: 1.5rem;
    margin: 1rem 0;
    position: relative;
}

.sg-highlight::before {
    content: '🏆 SG TOP PERFORMER';
    position: absolute;
    top: -10px;
    left: 20px;
    background: var(--success);
    color: white;
    padding: 5px 15px;
    border-radius: 20px;
    font-size: 0.8rem;
    font-weight: 700;
}

/* Modern Metrics Grid */
.metrics-grid {
    display: grid;
    grid-template-columns: repeat(auto-fit, minmax(280px, 1fr));
    gap: 1.5rem;
    margin: 2rem 0;
}

.metric-card {
    background: var(--glass-bg);
    backdrop-filter: blur(var(--blur));
    border-radius: 20px;
    padding: 2rem;
    border: 1px solid var(--glass-border);
    position: relative;
    overflow: hidden;
    transition: var(--transition);
    cursor: pointer;
}

.metric-card:hover {
    transform: translateY(-8px) scale(1.02);
    box-shadow: var(--shadow-lg);
    border-color: var(--primary);
}

.metric-card::before {
    content: '';
    position: absolute;
    top: 0;
    left: 0;
    right: 0;
    height: 4px;
    background: linear-gradient(90deg, var(--primary), var(--secondary));
    border-radius: 20px 20px 0 0;
}

.metric-icon {
    font-size: 2.5rem;
    margin-bottom: 1rem;
    display: block;
}

.metric-label {
    font-size: 0.9rem;
    color: var(--muted);
    font-weight: 600;
    text-transform: uppercase;
    letter-spacing: 0.05em;
    margin-bottom: 0.5rem;
}

.metric-value {
    font-size: 2.5rem;
    font-weight: 800;
    color: var(--light);
    margin-bottom: 0.5rem;
    line-height: 1;
}

.metric-delta {
    font-size: 0.9rem;
    font-weight: 600;
    display: flex;
    align-items: center;
    gap: 0.5rem;
}

.delta-positive { color: var(--success); }
.delta-negative { color: var(--danger); }
.delta-neutral { color: var(--warning); }

/* Modern Tabs */
.stTabs [role="tablist"] {
    gap: 0.5rem;
    border-bottom: 2px solid var(--glass-border);
    padding-bottom: 0;
}

.stTabs [role="tab"] {
    background: transparent;
    border: none;
    border-radius: 12px 12px 0 0;
    padding: 1rem 2rem;
    font-weight: 600;
    color: var(--muted);
    transition: var(--transition);
    position: relative;
}

.stTabs [role="tab"]:hover {
    color: var(--primary);
    background: rgba(99, 102, 241, 0.1);
}

.stTabs [aria-selected="true"] {
    color: var(--light);
    background: linear-gradient(135deg, 
        rgba(99, 102, 241, 0.2), 
        rgba(6, 182, 212, 0.2));
    border-bottom: 2px solid var(--primary);
}

/* Modern Charts */
.chart-container {
    background: var(--glass-bg);
    backdrop-filter: blur(var(--blur));
    border-radius: 20px;
    border: 1px solid var(--glass-border);
    padding: 1.5rem;
    margin-bottom: 2rem;
    transition: var(--transition);
}

.chart-container:hover {
    box-shadow: var(--shadow);
    border-color: var(--primary);
}

/* Modern Sidebar */
[data-testid="stSidebar"] {
    background: var(--glass-bg);
    backdrop-filter: blur(var(--blur));
    border-right: 1px solid var(--glass-border);
}

[data-testid="stSidebar"] .stSelectbox > div > div,
[data-testid="stSidebar"] .stMultiSelect > div > div,
[data-testid="stSidebar"] .stDateInput > div > div {
    background: rgba(99, 102, 241, 0.1);
    border: 1px solid var(--glass-border);
    border-radius: 12px;
    backdrop-filter: blur(var(--blur));
}

/* Modern Buttons */
.stButton > button {
    background: linear-gradient(135deg, var(--primary), var(--secondary));
    border: none;
    border-radius: 12px;
    padding: 0.75rem 2rem;
    font-weight: 600;
    color: white;
    transition: var(--transition);
    box-shadow: 0 4px 15px rgba(99, 102, 241, 0.3);
}

.stButton > button:hover {
    transform: translateY(-2px);
    box-shadow: 0 8px 25px rgba(99, 102, 241, 0.5);
}

/* Modern Alerts */
.stAlert {
    border-radius: 16px;
    border: 1px solid var(--glass-border);
    background: var(--glass-bg);
    backdrop-filter: blur(var(--blur));
}

/* AI Response Styling */
.ai-response {
    background: linear-gradient(135deg, 
        rgba(139, 92, 246, 0.15), 
        rgba(236, 72, 153, 0.15));
    border-radius: 20px;
    border: 1px solid rgba(139, 92, 246, 0.3);
    padding: 2rem;
    margin: 1rem 0;
    backdrop-filter: blur(var(--blur));
    position: relative;
    overflow: hidden;
}

.ai-response::before {
    content: '🤖';
    position: absolute;
    top: 1rem;
    right: 1rem;
    font-size: 1.5rem;
    opacity: 0.5;
}

/* Loading States */
.stSpinner {
    border-color: var(--primary) !important;
}

/* Responsive Design */
@media (max-width: 768px) {
    .metrics-grid {
        grid-template-columns: 1fr;
    }
    
    .hero-section {
        padding: 2rem 1rem;
    }
    
    .metric-card {
        padding: 1.5rem;
    }
}

/* Scrollbar Styling */
::-webkit-scrollbar {
    width: 8px;
}

::-webkit-scrollbar-track {
    background: var(--dark);
}

::-webkit-scrollbar-thumb {
    background: linear-gradient(135deg, var(--primary), var(--secondary));
    border-radius: 4px;
}

::-webkit-scrollbar-thumb:hover {
    background: linear-gradient(135deg, var(--secondary), var(--primary));
}
</style>
"""

st.markdown(MODERN_CSS, unsafe_allow_html=True)

# =========================================================
# ------------------- KONFIGURASI PLOTLY -----------------
# =========================================================
def setup_plotly_theme():
    """Setup tema plotly modern"""
    theme = go.layout.Template(
        layout=go.Layout(
            font=dict(family="Inter, -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif", 
                     color="#F8FAFC", size=12),
            title=dict(font=dict(size=20, color="#F8FAFC"), x=0.5, xanchor='center'),
            paper_bgcolor="rgba(15, 23, 42, 0)",
            plot_bgcolor="rgba(15, 23, 42, 0.3)",
            colorway=PLOTLY_COLORS,
            legend=dict(
                bgcolor="rgba(15, 23, 42, 0.8)",
                bordercolor="rgba(255, 255, 255, 0.1)",
                borderwidth=1,
                font=dict(size=11)
            ),
            margin=dict(l=60, r=60, t=80, b=60),
            xaxis=dict(
                gridcolor="rgba(255, 255, 255, 0.1)",
                zerolinecolor="rgba(255, 255, 255, 0.2)",
                color="#F8FAFC"
            ),
            yaxis=dict(
                gridcolor="rgba(255, 255, 255, 0.1)",
                zerolinecolor="rgba(255, 255, 255, 0.2)",
                color="#F8FAFC"
            )
        )
    )
    pio.templates["modern_dark"] = theme
    px.defaults.template = "modern_dark"

setup_plotly_theme()

# =========================================================
# ------------------- FUNGSI UTILITAS --------------------
# =========================================================
def format_currency(value: float) -> str:
    """Format nilai ke rupiah"""
    try:
        return f"Rp {value:,.0f}".replace(",", ".")
    except (TypeError, ValueError):
        return "Rp 0"

def format_percentage(value: float) -> str:
    """Format nilai ke persentase dengan 2 desimal"""
    try:
        return f"{value:.2f}%"
    except (TypeError, ValueError):
        return "0.00%"

def format_score(value: float) -> str:
    """Format nilai score dengan 2 desimal"""
    try:
        return f"{value:.2f}"
    except (TypeError, ValueError):
        return "0.00"

def format_number(value: float) -> str:
    """Format nilai tanpa desimal"""
    try:
        return f"{value:,.0f}".replace(",", ".")
    except (TypeError, ValueError):
        return "0"

def create_metric_card(title: str, value: str, delta: str = None, 
                      delta_type: str = "neutral", icon: str = "📊") -> str:
    """Generate HTML untuk metric card modern"""
    delta_class = f"delta-{delta_type}"
    delta_html = f'<div class="metric-delta {delta_class}">{delta}</div>' if delta else ""
    
    return f"""
    <div class="metric-card">
        <div class="metric-icon">{icon}</div>
        <div class="metric-label">{title}</div>
        <div class="metric-value">{value}</div>
        {delta_html}
    </div>
    """

@st.cache_data(ttl=300, show_spinner=False)
def load_and_process_data(spreadsheet_url: str, sheet_name: str) -> Optional[pd.DataFrame]:
    """Load dan proses data dari Google Sheets dengan perhitungan yang benar"""
    scope = [
        "https://www.googleapis.com/auth/spreadsheets",
        "https://www.googleapis.com/auth/drive"
    ]
    
    try:
        creds_dict = st.secrets["gcp_service_account"]
        creds = ServiceAccountCredentials.from_json_keyfile_dict(creds_dict, scope)
        client = gspread.authorize(creds)
        
        # Progress indicator
        progress_bar = st.progress(0)
        status_text = st.empty()
        
        status_text.text("🔗 Menghubungkan ke Google Sheets...")
        progress_bar.progress(25)
        
        spreadsheet = client.open_by_url(spreadsheet_url)
        worksheet = spreadsheet.worksheet(sheet_name)
        
        status_text.text("📊 Mengunduh data...")
        progress_bar.progress(50)
        
        df = get_as_dataframe(worksheet, evaluate_formulas=True)
        
        status_text.text("🔄 Memproses data dan menghitung score...")
        progress_bar.progress(75)
        
        # Bersihkan data
        df.dropna(axis=0, how="all", inplace=True)
        df.columns = df.columns.str.strip()
        
        # Konversi kolom tanggal
        if 'TANGGAL' in df.columns:
            df['TANGGAL'] = pd.to_datetime(df['TANGGAL'], errors='coerce', dayfirst=True)
        
        # =========================================================
        # PERBAIKAN UTAMA: KONVERSI DAN PERHITUNGAN YANG BENAR
        # =========================================================
        
        # Daftar kolom ACV yang harus dikonversi
        acv_columns = ['PSM ACV', 'PWP ACV', 'SG ACV', 'APC ACV', 'ACV TEBUS 2500']
        
        # Daftar kolom bobot
        bobot_columns = ['BOBOT PSM', 'BOBOT PWP', 'BOBOT SG', 'BOBOT APC']
        
        # Daftar kolom numerik lainnya
        numeric_cols = ['TARGET TEBUS 2500', 'ACTUAL TEBUS 2500', 'JHK']
        
        # --- KONVERSI KOLOM ACV KE BENTUK PERSENTASE (0-100) ---
        def clean_and_convert_percentage(series):
            """Bersihkan dan konversi nilai persentase ke format 0-100"""
            # Convert to string first
            series = series.astype(str)
            
            # Remove percentage signs and spaces
            series = series.str.replace('%', '', regex=False)
            series = series.str.replace(' ', '', regex=False)
            
            # Replace comma with dot for decimal
            series = series.str.replace(',', '.', regex=False)
            
            # Convert to numeric
            numeric_series = pd.to_numeric(series, errors='coerce')
            
            # If values are between 0 and 1, multiply by 100
            if numeric_series.max() <= 1 and numeric_series.min() >= 0:
                numeric_series = numeric_series * 100
            
            # Cap at 100%
            numeric_series = numeric_series.clip(0, 100)
            
            return numeric_series
        
        # Apply conversion to ACV columns
        for col in acv_columns:
            if col in df.columns:
                df[col] = clean_and_convert_percentage(df[col])
        
        # --- KONVERSI KOLOM BOBOT ---
        for col in bobot_columns:
            if col in df.columns:
                df[col] = pd.to_numeric(df[col], errors='coerce')
        
        # --- KONVERSI KOLOM NUMERIK LAINNYA ---
        for col in numeric_cols:
            if col in df.columns:
                df[col] = pd.to_numeric(df[col], errors='coerce')
        
        # =========================================================
        # PERHITUNGAN SCORE YANG BENAR SESUAI RUMUS
        # Score = (ACV × Bobot) / 100
        # =========================================================
        
        # Definisikan mapping indikator dan bobot default jika tidak ada di data
        indicators_config = {
            'PSM': {'acv_col': 'PSM ACV', 'bobot_col': 'BOBOT PSM', 'default_bobot': 20},
            'PWP': {'acv_col': 'PWP ACV', 'bobot_col': 'BOBOT PWP', 'default_bobot': 25},
            'SG': {'acv_col': 'SG ACV', 'bobot_col': 'BOBOT SG', 'default_bobot': 30},
            'APC': {'acv_col': 'APC ACV', 'bobot_col': 'BOBOT APC', 'default_bobot': 25}
        }
        
        # Hitung score untuk setiap indikator
        for indicator, config in indicators_config.items():
            acv_col = config['acv_col']
            bobot_col = config['bobot_col']
            default_bobot = config['default_bobot']
            
            if acv_col in df.columns:
                # Gunakan bobot dari data jika ada,否则gunakan default
                if bobot_col in df.columns:
                    bobot_values = df[bobot_col].fillna(default_bobot)
                else:
                    bobot_values = default_bobot
                
                # Hitung score: (ACV × Bobot) / 100
                df[f'SCORE {indicator} (CALCULATED)'] = (df[acv_col].fillna(0) * bobot_values) / 100
                
                # Debug info
                st.sidebar.info(f"🔍 {indicator}: ACV×Bobot/100 = Score")
                st.sidebar.write(f"Sample: {df[acv_col].iloc[0]:.1f}% × {bobot_values.iloc[0]} / 100 = {df[f'SCORE {indicator} (CALCULATED)'].iloc[0]:.2f}")
        
        # Hitung TOTAL SCORE yang benar
        score_columns = [f'SCORE {indicator} (CALCULATED)' for indicator in indicators_config.keys()]
        if all(col in df.columns for col in score_columns):
            df['TOTAL SCORE PPSA (CALCULATED)'] = df[score_columns].sum(axis=1)
        
        # Simpan config bobot untuk digunakan di visualisasi
        st.session_state['indicators_config'] = indicators_config
        
        status_text.text("✅ Data berhasil dimuat dan dihitung!")
        progress_bar.progress(100)
        
        # Clear progress indicators
        progress_bar.empty()
        status_text.empty()
        
        return df
        
    except Exception as e:
        st.error(f"❌ Gagal memuat data: {str(e)}")
        return None

def filter_data(df: pd.DataFrame, filters: Dict) -> pd.DataFrame:
    """Apply filters ke dataframe"""
    filtered_df = df.copy()
    
    # Filter tanggal
    if filters.get('date_range') and len(filters['date_range']) == 2:
        start_date, end_date = filters['date_range']
        if 'TANGGAL' in df.columns:
            start_ts = pd.to_datetime(start_date)
            end_ts = pd.to_datetime(end_date) + pd.Timedelta(days=1)
            filtered_df = filtered_df[
                (filtered_df['TANGGAL'] >= start_ts) & 
                (filtered_df['TANGGAL'] < end_ts)
            ]
    
    # Filter kasir
    if filters.get('cashiers') and 'Semua' not in filters['cashiers']:
        if 'NAMA KASIR' in df.columns:
            filtered_df = filtered_df[filtered_df['NAMA KASIR'].isin(filters['cashiers'])]
    
    # Filter shift
    if filters.get('shifts') and 'Semua' not in filters['shifts']:
        if 'SHIFT' in df.columns:
            filtered_df = filtered_df[filtered_df['SHIFT'].isin(filters['shifts'])]
    
    return filtered_df

def calculate_global_ppsa_score(df: pd.DataFrame) -> Dict:
    """
    Menghitung Global PPSA Score dengan perhitungan yang benar
    """
    if df.empty:
        return {
            'global_score': 0.0,
            'details': {
                'PSM': {'acv': 0.0, 'bobot': 0.0, 'score': 0.0},
                'PWP': {'acv': 0.0, 'bobot': 0.0, 'score': 0.0},
                'SG': {'acv': 0.0, 'bobot': 0.0, 'score': 0.0},
                'APC': {'acv': 0.0, 'bobot': 0.0, 'score': 0.0}
            }
        }
    
    # Gunakan kolom yang sudah dihitung dengan benar
    total_score_col = 'TOTAL SCORE PPSA (CALCULATED)'
    if total_score_col in df.columns:
        global_score = df[total_score_col].mean()
    else:
        global_score = 0
    
    # Hitung detail untuk setiap indikator
    details = {}
    indicators_config = st.session_state.get('indicators_config', {})
    
    for indicator, config in indicators_config.items():
        acv_col = config['acv_col']
        bobot_col = config['bobot_col']
        score_col = f'SCORE {indicator} (CALCULATED)'
        default_bobot = config['default_bobot']
        
        if acv_col in df.columns:
            avg_acv = df[acv_col].mean()
            
            # Rata-rata bobot yang digunakan
            if bobot_col in df.columns:
                avg_bobot = df[bobot_col].mean()
            else:
                avg_bobot = default_bobot
            
            # Rata-rata score
            if score_col in df.columns:
                avg_score = df[score_col].mean()
            else:
                avg_score = (avg_acv * avg_bobot) / 100
            
            details[indicator] = {
                'acv': avg_acv,
                'bobot': avg_bobot,
                'score': avg_score,
                'performance': 'Excellent' if avg_acv >= 90 else 'Good' if avg_acv >= 80 else 'Need Improvement'
            }
        else:
            details[indicator] = {
                'acv': 0.0,
                'bobot': config['default_bobot'],
                'score': 0.0,
                'performance': 'No Data'
            }
    
    return {
        'global_score': global_score,
        'details': details
    }

# =========================================================
# ------------------- VISUALISASI CHARTS -----------------
# =========================================================
def create_score_calculation_explanation():
    """Panel penjelasan perhitungan score"""
    st.markdown("""
    ### 🧮 Cara Perhitungan Score
    
    **RUMUS:** `Score = (ACV × Bobot) / 100`
    
    **Contoh Perhitungan:**
    - SG ACV = 85%, Bobot SG = 30
    - Score SG = (85 × 30) / 100 = 25.5
    
    **Bobot Default:**
    - PSM: 20
    - PWP: 25  
    - SG: 30
    - APC: 25
    - **Total Bobot: 100**
    
    **Total Score PPSA** = Score PSM + Score PWP + Score SG + Score APC
    """)

def create_sg_focused_chart(df: pd.DataFrame) -> go.Figure:
    """Chart khusus untuk analisis SG ACV dan Score"""
    if df.empty or 'SG ACV' not in df.columns:
        return go.Figure().add_annotation(
            text="Data SG tidak tersedia",
            xref="paper", yref="paper", x=0.5, y=0.5,
            showarrow=False, font=dict(size=16, color="#64748B")
        )
    
    # Group by kasir untuk SG
    sg_performance = df.groupby('NAMA KASIR').agg({
        'SG ACV': ['mean', 'count', 'max'],
        'SCORE SG (CALCULATED)': 'mean'
    }).reset_index()
    
    sg_performance.columns = ['NAMA KASIR', 'Rata_rata_SG_ACV', 'Jumlah_Entri', 'Max_SG_ACV', 'Rata_rata_Score_SG']
    sg_performance = sg_performance.sort_values('Rata_rata_SG_ACV', ascending=True)
    
    # Buat subplot: ACV di kiri, Score di kanan
    fig = make_subplots(
        rows=1, cols=2,
        subplot_titles=("🏆 SG ACV (%) by Kasir", "📊 SG Score by Kasir"),
        horizontal_spacing=0.1
    )
    
    # Plot 1: SG ACV
    colors_acv = []
    for score in sg_performance['Rata_rata_SG_ACV']:
        if score >= 90: colors_acv.append(COLOR_SCHEME['success'])
        elif score >= 80: colors_acv.append(COLOR_SCHEME['warning'])
        else: colors_acv.append(COLOR_SCHEME['danger'])
    
    fig.add_trace(go.Bar(
        x=sg_performance['Rata_rata_SG_ACV'],
        y=sg_performance['NAMA KASIR'],
        orientation='h',
        marker_color=colors_acv,
        name='SG ACV',
        hovertemplate="<b>%{y}</b><br>SG ACV: %{x:.2f}%<br><extra></extra>"
    ), row=1, col=1)
    
    # Plot 2: SG Score
    colors_score = []
    for score in sg_performance['Rata_rata_Score_SG']:
        if score >= 27: colors_score.append(COLOR_SCHEME['success'])  # 90% of 30
        elif score >= 24: colors_score.append(COLOR_SCHEME['warning'])  # 80% of 30
        else: colors_score.append(COLOR_SCHEME['danger'])
    
    fig.add_trace(go.Bar(
        x=sg_performance['Rata_rata_Score_SG'],
        y=sg_performance['NAMA KASIR'],
        orientation='h',
        marker_color=colors_score,
        name='SG Score',
        hovertemplate="<b>%{y}</b><br>SG Score: %{x:.2f}<br><extra></extra>"
    ), row=1, col=2)
    
    fig.update_xaxes(title_text="SG ACV (%)", row=1, col=1)
    fig.update_xaxes(title_text="SG Score", row=1, col=2)
    fig.update_yaxes(title_text="", row=1, col=1)
    fig.update_yaxes(title_text="", row=1, col=2)
    
    fig.update_layout(
        height=max(400, len(sg_performance) * 30),
        showlegend=False,
        title_text="Performa SG by Kasir"
    )
    
    return fig

def create_ppsa_radar_chart(df: pd.DataFrame) -> go.Figure:
    """Buat radar chart untuk PPSA indicators"""
    if df.empty:
        return go.Figure().add_annotation(
            text="Tidak ada data untuk ditampilkan",
            xref="paper", yref="paper", x=0.5, y=0.5,
            showarrow=False, font=dict(size=16, color="#64748B")
        )
    
    # Hitung rata-rata ACV per indikator
    indicators = ['PSM', 'PWP', 'SG', 'APC']
    avg_acv_values = []
    avg_score_values = []
    labels = []
    
    for indicator in indicators:
        acv_col = f'{indicator} ACV'
        score_col = f'SCORE {indicator} (CALCULATED)'
        
        if acv_col in df.columns:
            avg_acv = df[acv_col].mean()
            avg_score = df[score_col].mean() if score_col in df.columns else 0
            
            if not pd.isna(avg_acv):
                avg_acv_values.append(avg_acv)
                avg_score_values.append(avg_score)
                labels.append(indicator)
    
    if not avg_acv_values:
        return go.Figure().add_annotation(
            text="Data ACV tidak tersedia",
            xref="paper", yref="paper", x=0.5, y=0.5,
            showarrow=False, font=dict(size=16, color="#64748B")
        )
    
    # Buat radar chart untuk ACV
    fig = go.Figure()
    
    # Data ACV aktual
    fig.add_trace(go.Scatterpolar(
        r=avg_acv_values,
        theta=labels,
        fill='toself',
        name='Rata-rata ACV (%)',
        line_color=COLOR_SCHEME['primary'],
        fillcolor=f"rgba(99, 102, 241, 0.3)",
        hovertemplate="<b>%{theta}</b><br>ACV: %{r:.2f}%<br><extra></extra>"
    ))
    
    # Data Score (skala berbeda)
    max_score = max(avg_score_values) if avg_score_values else 1
    scale_factor = 100 / max_score if max_score > 0 else 1
    scaled_scores = [score * scale_factor for score in avg_score_values]
    
    fig.add_trace(go.Scatterpolar(
        r=scaled_scores,
        theta=labels,
        fill='toself',
        name=f'Rata-rata Score (scaled)',
        line_color=COLOR_SCHEME['success'],
        fillcolor=f"rgba(16, 185, 129, 0.3)",
        hovertemplate="<b>%{theta}</b><br>Score: %{customdata:.2f}<br><extra></extra>",
        customdata=avg_score_values
    ))
    
    # Target line (100%)
    target_values = [100] * len(labels)
    fig.add_trace(go.Scatterpolar(
        r=target_values,
        theta=labels,
        mode='lines',
        name='Target ACV (100%)',
        line_color=COLOR_SCHEME['danger'],
        line_dash='dash',
        hovertemplate="<b>%{theta}</b><br>Target: 100%<br><extra></extra>"
    ))
    
    fig.update_layout(
        polar=dict(
            radialaxis=dict(
                visible=True,
                range=[0, 100]
            )
        ),
        title="<b>📊 Radar Performa PPSA: ACV vs Score</b>",
        height=500,
        hovermode="closest"
    )
    
    return fig

def create_cashier_performance_chart(df: pd.DataFrame) -> go.Figure:
    """Chart performa kasir berdasarkan total score PPSA"""
    if df.empty or 'TOTAL SCORE PPSA (CALCULATED)' not in df.columns:
        return go.Figure().add_annotation(
            text="Data performa kasir tidak tersedia",
            xref="paper", yref="paper", x=0.5, y=0.5,
            showarrow=False, font=dict(size=16, color="#64748B")
        )
    
    # Group by kasir
    cashier_performance = df.groupby('NAMA KASIR')['TOTAL SCORE PPSA (CALCULATED)'].agg([
        'mean', 'count', 'std'
    ]).reset_index()
    
    cashier_performance.columns = ['NAMA KASIR', 'Rata_rata_Score', 'Jumlah_Laporan', 'Std_Dev']
    cashier_performance = cashier_performance.sort_values('Rata_rata_Score', ascending=True)
    
    # Tentukan warna berdasarkan performa
    colors = []
    for score in cashier_performance['Rata_rata_Score']:
        if score >= 80: colors.append(COLOR_SCHEME['success'])
        elif score >= 60: colors.append(COLOR_SCHEME['warning'])
        else: colors.append(COLOR_SCHEME['danger'])
    
    fig = go.Figure(go.Bar(
        x=cashier_performance['Rata_rata_Score'],
        y=cashier_performance['NAMA KASIR'],
        orientation='h',
        marker_color=colors,
        text=[f"{score:.2f}" for score in cashier_performance['Rata_rata_Score']],
        textposition='auto',
        hovertemplate="<b>%{y}</b><br>Score: %{x:.2f}<br>Jumlah Laporan: %{customdata}<br><extra></extra>",
        customdata=cashier_performance['Jumlah_Laporan']
    ))
    
    fig.update_layout(
        title="<b>👥 Performa Kasir (Total Score PPSA)</b>",
        xaxis_title="Total Score PPSA",
        yaxis_title="Nama Kasir",
        height=max(400, len(cashier_performance) * 40),
        showlegend=False
    )
    
    # Garis referensi
    fig.add_vline(x=80, line_dash="dash", line_color=COLOR_SCHEME['success'], 
                  annotation_text="Target Excellent (80)")
    fig.add_vline(x=60, line_dash="dash", line_color=COLOR_SCHEME['warning'], 
                  annotation_text="Target Good (60)")
    
    return fig

def create_score_breakdown_chart(df: pd.DataFrame) -> go.Figure:
    """Chart breakdown score per indikator untuk kasir terbaik"""
    if df.empty:
        return go.Figure().add_annotation(
            text="Tidak ada data untuk ditampilkan",
            xref="paper", yref="paper", x=0.5, y=0.5,
            showarrow=False, font=dict(size=16, color="#64748B")
        )
    
    # Cari kasir dengan total score tertinggi
    if 'TOTAL SCORE PPSA (CALCULATED)' in df.columns and 'NAMA KASIR' in df.columns:
        top_performer = df.groupby('NAMA KASIR')['TOTAL SCORE PPSA (CALCULATED)'].mean().idxmax()
        top_data = df[df['NAMA KASIR'] == top_performer].iloc[0]
    else:
        return go.Figure().add_annotation(
            text="Data kasir tidak lengkap",
            xref="paper", yref="paper", x=0.5, y=0.5,
            showarrow=False, font=dict(size=16, color="#64748B")
        )
    
    # Data untuk breakdown
    indicators = ['PSM', 'PWP', 'SG', 'APC']
    acv_values = []
    score_values = []
    bobot_values = []
    
    for indicator in indicators:
        acv_col = f'{indicator} ACV'
        score_col = f'SCORE {indicator} (CALCULATED)'
        bobot_col = f'BOBOT {indicator}'
        
        if acv_col in df.columns:
            acv_values.append(top_data[acv_col] if acv_col in top_data else 0)
            score_values.append(top_data[score_col] if score_col in top_data else 0)
            bobot_values.append(top_data[bobot_col] if bobot_col in top_data else 
                               st.session_state.get('indicators_config', {}).get(indicator, {}).get('default_bobot', 0))
    
    # Buat grouped bar chart
    fig = go.Figure()
    
    # ACV bars
    fig.add_trace(go.Bar(
        name='ACV (%)',
        x=indicators,
        y=acv_values,
        marker_color=COLOR_SCHEME['primary'],
        text=[f"{v:.1f}%" for v in acv_values],
        textposition='auto',
    ))
    
    # Score bars
    fig.add_trace(go.Bar(
        name='Score',
        x=indicators,
        y=score_values,
        marker_color=COLOR_SCHEME['success'],
        text=[f"{v:.2f}" for v in score_values],
        textposition='auto',
    ))
    
    # Bobot line
    fig.add_trace(go.Scatter(
        name='Bobot',
        x=indicators,
        y=bobot_values,
        mode='lines+markers',
        line=dict(color=COLOR_SCHEME['warning'], width=3),
        marker=dict(size=8),
        yaxis='y2'
    ))
    
    fig.update_layout(
        title=f"<b>📊 Breakdown Score untuk {top_performer} (Top Performer)</b>",
        xaxis_title="Indikator",
        yaxis_title="ACV (%) & Score",
        yaxis2=dict(
            title="Bobot",
            overlaying='y',
            side='right',
            range=[0, 35]
        ),
        barmode='group',
        height=500
    )
    
    return fig

# =========================================================
# -------------------- SIDEBAR CONTROLS ------------------
# =========================================================
def render_sidebar(df: pd.DataFrame) -> Dict:
    """Render sidebar dengan controls"""
    with st.sidebar:
        st.markdown("## 🎛️ Control Center")
        st.markdown("---")
        
        # Connection status
        try:
            spreadsheet_url = st.secrets["spreadsheet"]["url"]
            st.success("🔗 Connected to Google Sheets")
        except:
            spreadsheet_url = st.text_input(
                "📊 Google Spreadsheet URL",
                placeholder="https://docs.google.com/spreadsheets/d/...",
                help="Masukkan URL Google Sheets"
            )
        
        sheet_name = st.text_input(
            "📄 Worksheet Name",
            value="Data",
            help="Nama sheet dalam Google Sheets"
        )
        
        st.markdown("---")
        
        # Info Bobot
        st.markdown("### ⚖️ Konfigurasi Bobot")
        st.info("""
        **Bobot Default:**
        - PSM: 20
        - PWP: 25  
        - SG: 30
        - APC: 25
        """)
        
        # Filters
        st.markdown("### 🔍 Filters")
        
        filters = {}
        
        # Date filter
        if 'TANGGAL' in df.columns and not df.empty:
            min_date = df['TANGGAL'].min().date()
            max_date = df['TANGGAL'].max().date()
            
            filters['date_range'] = st.date_input(
                "📅 Periode Tanggal",
                value=(min_date, max_date),
                min_value=min_date,
                max_value=max_date
            )
        
        # Cashier filter
        if 'NAMA KASIR' in df.columns and not df.empty:
            cashiers = ['Semua'] + sorted(df['NAMA KASIR'].unique().tolist())
            filters['cashiers'] = st.multiselect(
                "👥 Pilih Kasir",
                options=cashiers,
                default=['Semua']
            )
        
        st.markdown("---")
        
        # Refresh button
        if st.button("🔄 Refresh Data", use_container_width=True):
            st.cache_data.clear()
            st.rerun()
        
        # Data info
        if not df.empty:
            total_records = len(df)
            kasir_aktif = df['NAMA KASIR'].nunique() if 'NAMA KASIR' in df.columns else 0
            
            periode_start = df['TANGGAL'].min().strftime('%d/%m/%Y') if 'TANGGAL' in df.columns else 'N/A'
            periode_end = df['TANGGAL'].max().strftime('%d/%m/%Y') if 'TANGGAL' in df.columns else 'N/A'
            
            st.markdown("### 📋 Data Info")
            st.info(f"""
            **Total Records:** {total_records:,}  
            **Kasir Aktif:** {kasir_aktif}  
            **Periode:** {periode_start} - {periode_end}
            """)
        
        return {'spreadsheet_url': spreadsheet_url, 'sheet_name': sheet_name, **filters}

# =========================================================
# ----------------------- MAIN APP -----------------------
# =========================================================
def main():
    """Main application function dengan perhitungan yang benar"""
    
    # Hero Section
    st.markdown("""
    <div class="hero-section">
        <h1 class="hero-title">🚀 Dashboard PPSA - PERHITUNGAN DIPERBAIKI</h1>
        <p class="hero-subtitle">
            Dashboard dengan <strong>perhitungan score yang benar</strong>: Score = (ACV × Bobot) / 100
            <br><strong>🏪 Toko:</strong> 2GC6 BAROS PANDEGLANG
        </p>
    </div>
    """, unsafe_allow_html=True)
    
    # Panel penjelasan perhitungan
    with st.expander("🧮 PENJELASAN PERHITUNGAN SCORE", expanded=True):
        create_score_calculation_explanation()
    
    # Initialize empty dataframe
    df = pd.DataFrame()
    
    # Render sidebar and get config
    config = render_sidebar(df)
    
    if not config['spreadsheet_url']:
        st.warning("⚠️ Masukkan URL Google Spreadsheet untuk memulai")
        return
    
    # Load data
    df = load_and_process_data(config['spreadsheet_url'], config['sheet_name'])
    
    if df is None or df.empty:
        st.error("❌ Tidak dapat memuat data. Periksa URL dan nama sheet.")
        return
    
    # Apply filters
    filtered_df = filter_data(df, config)
    
    if filtered_df.empty:
        st.warning("⚠️ Filter yang dipilih tidak menghasilkan data")
        return
    
    # Calculate Global PPSA Score
    global_ppsa = calculate_global_ppsa_score(filtered_df)
    
    # Key Metrics Section
    st.markdown("## 📊 Key Performance Indicators")
    
    # Calculate metrics
    total_records = len(filtered_df)
    
    # Gunakan score yang sudah dihitung dengan benar
    avg_ppsa_score = filtered_df['TOTAL SCORE PPSA (CALCULATED)'].mean() if 'TOTAL SCORE PPSA (CALCULATED)' in filtered_df.columns else 0
    
    # SG Specific metrics
    if 'SG ACV' in filtered_df.columns:
        avg_sg_acv = filtered_df['SG ACV'].mean()
        avg_sg_score = filtered_df['SCORE SG (CALCULATED)'].mean() if 'SCORE SG (CALCULATED)' in filtered_df.columns else 0
    else:
        avg_sg_acv = 0
        avg_sg_score = 0
    
    # Tebus Murah metrics
    if 'ACV TEBUS 2500' in filtered_df.columns:
        avg_tebus_acv = filtered_df['ACV TEBUS 2500'].mean()
    else:
        avg_tebus_acv = 0
    
    # Render metrics grid
    st.markdown('<div class="metrics-grid">', unsafe_allow_html=True)
    
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.markdown(create_metric_card(
            "Global PPSA Score",
            format_score(global_ppsa['global_score']),
            delta=f"Target: 80.00",
            delta_type="positive" if global_ppsa['global_score'] >= 80 else "warning",
            icon="🌍"
        ), unsafe_allow_html=True)
    
    with col2:
        st.markdown(create_metric_card(
            "Rata-rata Total Score",
            format_score(avg_ppsa_score),
            delta=f"Target: 80.00", 
            delta_type="positive" if avg_ppsa_score >= 80 else "warning",
            icon="🎯"
        ), unsafe_allow_html=True)
    
    with col3:
        st.markdown(create_metric_card(
            "SG ACV Score",
            format_percentage(avg_sg_acv),
            delta=f"Score: {avg_sg_score:.2f}",
            delta_type="positive" if avg_sg_acv >= 80 else "warning",
            icon="🏆"
        ), unsafe_allow_html=True)
    
    with col4:
        st.markdown(create_metric_card(
            "ACV Tebus Murah", 
            format_percentage(avg_tebus_acv),
            delta="Target: 100%",
            delta_type="positive" if avg_tebus_acv >= 80 else "warning",
            icon="💰"
        ), unsafe_allow_html=True)
    
    st.markdown('</div>', unsafe_allow_html=True)
    
    # Detail Global Score
    with st.expander("📋 Detail Global Score per Indikator", expanded=False):
        details_data = []
        for indicator, data in global_ppsa['details'].items():
            details_data.append({
                'Indikator': indicator,
                'ACV Rata-rata': format_percentage(data['acv']),
                'Bobot Rata-rata': format_score(data['bobot']),
                'Score Rata-rata': format_score(data['score']),
                'Performa': data['performance']
            })
        
        details_df = pd.DataFrame(details_data)
        st.dataframe(details_df, use_container_width=True)
    
    # Main Content Tabs
    tab1, tab2, tab3, tab4, tab5 = st.tabs([
        "🏆 SG Analysis", 
        "📊 Score Breakdown",
        "📈 Trend Analysis", 
        "👥 Performa Kasir",
        "📄 Raw Data"
    ])
    
    with tab1:
        st.markdown("### 🏆 SG (Serba Gratis) Performance Analysis")
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.markdown('<div class="chart-container">', unsafe_allow_html=True)
            st.plotly_chart(create_sg_focused_chart(filtered_df), use_container_width=True)
            st.markdown('</div>', unsafe_allow_html=True)
        
        with col2:
            st.markdown('<div class="chart-container">', unsafe_allow_html=True)
            st.plotly_chart(create_ppsa_radar_chart(filtered_df), use_container_width=True)
            st.markdown('</div>', unsafe_allow_html=True)
    
    with tab2:
        st.markdown("### 📊 Score Breakdown Analysis")
        
        st.markdown('<div class="chart-container">', unsafe_allow_html=True)
        st.plotly_chart(create_score_breakdown_chart(filtered_df), use_container_width=True)
        st.markdown('</div>', unsafe_allow_html=True)
        
        # Tabel detail perhitungan
        st.markdown("#### 📋 Sample Perhitungan Score")
        sample_data = filtered_df.head(3).copy()
        
        display_columns = ['NAMA KASIR', 'TANGGAL']
        for indicator in ['PSM', 'PWP', 'SG', 'APC']:
            acv_col = f'{indicator} ACV'
            bobot_col = f'BOBOT {indicator}'
            score_col = f'SCORE {indicator} (CALCULATED)'
            
            if acv_col in sample_data.columns:
                display_columns.extend([acv_col, bobot_col, score_col])
        
        if 'TOTAL SCORE PPSA (CALCULATED)' in sample_data.columns:
            display_columns.append('TOTAL SCORE PPSA (CALCULATED)')
        
        st.dataframe(sample_data[display_columns], use_container_width=True)
    
    with tab3:
        st.markdown("### 📈 Trend Analysis")
        # (Anda bisa menambahkan chart tren di sini)
        st.info("Fitur trend analysis dalam pengembangan...")
    
    with tab4:
        st.markdown("### 👥 Performa Kasir")
        st.markdown('<div class="chart-container">', unsafe_allow_html=True)
        st.plotly_chart(create_cashier_performance_chart(filtered_df), use_container_width=True)
        st.markdown('</div>', unsafe_allow_html=True)
    
    with tab5:
        st.markdown("### 📄 Raw Data & Export")
        
        # Export functionality
        col1, col2 = st.columns(2)
        
        with col1:
            csv = filtered_df.to_csv(index=False)
            st.download_button(
                label="📥 Download CSV",
                data=csv,
                file_name=f"ppsa_calculated_data_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
                mime="text/csv",
                use_container_width=True
            )
        
        with col2:
            buffer = BytesIO()
            with pd.ExcelWriter(buffer, engine='openpyxl') as writer:
                filtered_df.to_excel(writer, sheet_name='PPSA Calculated Data', index=False)
            
            st.download_button(
                label="📊 Download Excel",
                data=buffer.getvalue(),
                file_name=f"ppsa_calculated_data_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                use_container_width=True
            )
        
        # Data preview
        st.markdown("#### 👁️ Preview Data")
        st.dataframe(filtered_df.head(50), use_container_width=True)
    
    # Footer
    st.markdown("---")
    st.markdown("""
    <div style="text-align: center; color: #64748B; font-size: 0.9rem;">
        <p>🚀 <strong>Dashboard PPSA - Perhitungan Diperbaiki</strong> | 
        Formula: Score = (ACV × Bobot) / 100<br>
        © 2025 Advanced Business Analytics | Calculation Verified</p>
    </div>
    """, unsafe_allow_html=True)

if __name__ == "__main__":
    main()
