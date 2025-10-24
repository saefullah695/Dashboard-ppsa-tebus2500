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
    page_title="Dashboard PPSA & Tebus Murah 2025",
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

/* Modern Header */
.hero-section {
    background: linear-gradient(135deg, 
        rgba(99, 102, 241, 0.2) 0%, 
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
    background: radial-gradient(circle, var(--secondary), transparent);
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
    background: linear-gradient(135deg, var(--primary), var(--secondary));
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

def convert_percentage_to_decimal(value) -> float:
    """
    Konversi berbagai format persentase ke desimal (0-1)
    Menangani format: '85%', '85.5%', '0.85', 0.85, 85, '85,5%'
    """
    if pd.isna(value):
        return 0.0
    
    # Konversi ke string dulu untuk handling yang konsisten
    value_str = str(value)
    
    # Hapus karakter non-numerik kecuali titik dan koma
    value_str = re.sub(r'[^\d.,-]', '', value_str)
    
    # Ganti koma dengan titik untuk desimal
    value_str = value_str.replace(',', '.')
    
    # Konversi ke numeric
    try:
        numeric_value = float(value_str)
    except (ValueError, TypeError):
        return 0.0
    
    # Jika nilai adalah desimal (misal 0.85 dari Google Sheets format), kembalikan sebagai desimal
    # Kondisi: nilai > 0 dan nilai < 1
    if 0 < numeric_value < 1:
        return numeric_value
    
    # Jika nilai adalah persentase (85, 85.5), konversi ke desimal
    return numeric_value / 100

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
    """Load dan proses data dari Google Sheets dengan caching"""
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
        
        status_text.text("🔄 Memproses data...")
        progress_bar.progress(75)
        
        # Bersihkan data
        df.dropna(axis=0, how="all", inplace=True)
        df.columns = df.columns.str.strip()
        
        # Konversi kolom tanggal
        if 'TANGGAL' in df.columns:
            df['TANGGAL'] = pd.to_datetime(df['TANGGAL'], errors='coerce', dayfirst=True)
        
        # Daftar semua kolom ACV yang harus dikonversi sebagai persentase
        acv_columns = [
            'PSM ACV', 'PWP ACV', 'SG ACV', 'APC ACV', 'ACV TEBUS 2500'
        ]
        
        # Daftar kolom numerik lainnya
        numeric_cols = [
            'BOBOT PSM', 'SCORE PSM', 'BOBOT PWP', 'SCORE PWP',
            'BOBOT SG', 'SCORE SG', 'BOBOT APC', 'SCORE APC',
            'TOTAL SCORE PPSA', 'TARGET TEBUS 2500', 'ACTUAL TEBUS 2500', 'JHK'
        ]
        
        # --- PERBAIKAN UTAMA: PENANGANAN DATA PERSENTASE ---
        # Fungsi untuk membersihkan dan mengkonversi kolom persentase
        def convert_percentage_column(series: pd.Series) -> pd.Series:
            """Konversi kolom persentase dari berbagai format ke angka float 0-100"""
            # Konversi ke string dulu untuk handling yang konsisten
            series = series.astype(str)
            
            # Hapus karakter non-numerik kecuali titik dan koma
            series = series.str.replace('%', '', regex=False)
            series = series.str.replace('[^\d.,-]', '', regex=True)
            
            # Ganti koma dengan titik untuk desimal
            series = series.str.replace(',', '.', regex=False)
            
            # Konversi ke numeric
            numeric_series = pd.to_numeric(series, errors='coerce')
            
            # Jika nilai adalah desimal (misal 0.85 dari Google Sheets format), kalikan dengan 100
            # Kondisi: nilai > 0 dan nilai < 1
            numeric_series = numeric_series.apply(lambda x: x * 100 if 0 < x < 1 else x)
            
            # --- PERBAIKAN: Batasi nilai maksimal menjadi 100% ---
            numeric_series = numeric_series.apply(lambda x: min(x, 100) if not pd.isna(x) and x > 100 else x)
            
            return numeric_series
        
        # Konversi kolom ACV dengan fungsi baru
        for col in acv_columns:
            if col in df.columns:
                df[col] = convert_percentage_column(df[col])
        
        # Konversi kolom numerik lainnya (tanpa logika persentase)
        for col in numeric_cols:
            if col in df.columns:
                df[col] = df[col].astype(str).str.replace('%', '').str.replace(',', '.')
                df[col] = pd.to_numeric(df[col], errors='coerce')
        
        # Perbaiki perhitungan total score PPSA jika belum benar
        if all(col in df.columns for col in ['SCORE PSM', 'SCORE PWP', 'SCORE SG', 'SCORE APC']):
            df['TOTAL SCORE PPSA (CORRECTED)'] = (
                df['SCORE PSM'].fillna(0) + 
                df['SCORE PWP'].fillna(0) + 
                df['SCORE SG'].fillna(0) + 
                df['SCORE APC'].fillna(0)
            )
        elif all(col in df.columns for col in ['PSM ACV', 'BOBOT PSM', 'PWP ACV', 'BOBOT PWP', 'SG ACV', 'BOBOT SG', 'APC ACV', 'BOBOT APC']):
            df['TOTAL SCORE PPSA (CORRECTED)'] = (
                (df['PSM ACV'].fillna(0) * df['BOBOT PSM'].fillna(0)) + 
                (df['PWP ACV'].fillna(0) * df['BOBOT PWP'].fillna(0)) + 
                (df['SG ACV'].fillna(0) * df['BOBOT SG'].fillna(0)) + 
                (df['APC ACV'].fillna(0) * df['BOBOT APC'].fillna(0))
            )
        else:
            df['TOTAL SCORE PPSA (CORRECTED)'] = df['TOTAL SCORE PPSA'].fillna(0)
        
        status_text.text("✅ Data berhasil dimuat!")
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
    Menghitung Global PPSA Score dari semua kasir
    Rumus: Score per Indikator = (ACV / 100) × Bobot
    Total Global Score = Σ(Score PSM + PWP + SG + APC)
    """
    if df.empty:
        return {
            'global_score': 0.0,
            'details': {
                'PSM': {'acv': 0.0, 'bobot': 0.0, 'kontribusi': 0.0},
                'PWP': {'acv': 0.0, 'bobot': 0.0, 'kontribusi': 0.0},
                'SG': {'acv': 0.0, 'bobot': 0.0, 'kontribusi': 0.0},
                'APC': {'acv': 0.0, 'bobot': 0.0, 'kontribusi': 0.0}
            }
        }
    
    # Hitung rata-rata ACV dan bobot untuk setiap indikator
    indicators = ['PSM', 'PWP', 'SG', 'APC']
    details = {}
    total_score = 0.0
    
    for indicator in indicators:
        acv_col = f'{indicator} ACV'
        bobot_col = f'BOBOT {indicator}'
        
        if acv_col in df.columns and bobot_col in df.columns:
            avg_acv = df[acv_col].mean()
            avg_bobot = df[bobot_col].mean()
            
            # Kontribusi = (Avg ACV / 100) × Avg Bobot
            kontribusi = (avg_acv / 100) * avg_bobot
            
            details[indicator] = {
                'acv': avg_acv,
                'bobot': avg_bobot,
                'kontribusi': kontribusi
            }
            
            total_score += kontribusi
        else:
            details[indicator] = {
                'acv': 0.0,
                'bobot': 0.0,
                'kontribusi': 0.0
            }
    
    return {
        'global_score': total_score,
        'details': details
    }

# =========================================================
# ------------------- VISUALISASI CHARTS -----------------
# =========================================================
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
    avg_values = []
    labels = []
    
    for indicator in indicators:
        acv_col = f'{indicator} ACV'
        if acv_col in df.columns:
            avg_acv = df[acv_col].mean()
            
            if not pd.isna(avg_acv):
                avg_values.append(avg_acv)
                labels.append(indicator)
    
    if not avg_values:
        return go.Figure().add_annotation(
            text="Data ACV tidak tersedia",
            xref="paper", yref="paper", x=0.5, y=0.5,
            showarrow=False, font=dict(size=16, color="#64748B")
        )
    
    # Buat radar chart
    fig = go.Figure()
    
    # Data aktual
    fig.add_trace(go.Scatterpolar(
        r=avg_values,
        theta=labels,
        fill='toself',
        name='Rata-rata ACV (%)',
        line_color=COLOR_SCHEME['primary'],
        fillcolor=f"rgba(99, 102, 241, 0.3)",
        hovertemplate="<b>%{theta}</b><br>" +
                     "ACV: %{r:.2f}%<br>" +
                     "<extra></extra>"
    ))
    
    # Target line (100%)
    target_values = [100] * len(labels)
    fig.add_trace(go.Scatterpolar(
        r=target_values,
        theta=labels,
        mode='lines',
        name='Target (100%)',
        line_color=COLOR_SCHEME['success'],
        line_dash='dash',
        hovertemplate="<b>%{theta}</b><br>" +
                     "Target: 100%<br>" +
                     "<extra></extra>"
    ))
    
    fig.update_layout(
        polar=dict(
            radialaxis=dict(
                visible=True,
                range=[0, 100],
                ticksuffix="%"
            )
        ),
        title="<b>📊 Radar Performa PPSA (ACV %)</b>",
        height=500,
        hovermode="closest"
    )
    
    return fig

def create_cashier_performance_chart(df: pd.DataFrame) -> go.Figure:
    """Chart performa kasir berdasarkan total score PPSA"""
    if df.empty or 'TOTAL SCORE PPSA (CORRECTED)' not in df.columns:
        return go.Figure().add_annotation(
            text="Data performa kasir tidak tersedia",
            xref="paper", yref="paper", x=0.5, y=0.5,
            showarrow=False, font=dict(size=16, color="#64748B")
        )
    
    # Group by kasir
    cashier_performance = df.groupby('NAMA KASIR')['TOTAL SCORE PPSA (CORRECTED)'].agg([
        'mean', 'count'
    ]).reset_index()
    
    cashier_performance.columns = ['NAMA KASIR', 'Rata_rata_Score', 'Jumlah_Laporan']
    cashier_performance = cashier_performance.sort_values('Rata_rata_Score', ascending=True)
    
    # Tentukan warna berdasarkan performa
    colors = []
    for score in cashier_performance['Rata_rata_Score']:
        if score >= 80:
            colors.append(COLOR_SCHEME['success'])
        elif score >= 60:
            colors.append(COLOR_SCHEME['warning'])
        else:
            colors.append(COLOR_SCHEME['danger'])
    
    fig = go.Figure(go.Bar(
        x=cashier_performance['Rata_rata_Score'],
        y=cashier_performance['NAMA KASIR'],
        orientation='h',
        marker_color=colors,
        text=[f"{score:.2f}" for score in cashier_performance['Rata_rata_Score']],
        textposition='auto',
        hovertemplate="<b>%{y}</b><br>" +
                     "Score: %{x:.2f}<br>" +
                     "Jumlah Laporan: %{customdata}<br>" +
                     "<extra></extra>",
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
    fig.add_vline(x=100, line_dash="dash", line_color=COLOR_SCHEME['success'], 
                  annotation_text="Target Excellent (100)")
    fig.add_vline(x=80, line_dash="dash", line_color=COLOR_SCHEME['warning'], 
                  annotation_text="Target Good (80)")
    
    return fig

def create_tebus_murah_chart(df: pd.DataFrame) -> go.Figure:
    """Chart analisis tebus murah"""
    if df.empty:
        return go.Figure().add_annotation(
            text="Data tebus murah tidak tersedia",
            xref="paper", yref="paper", x=0.5, y=0.5,
            showarrow=False, font=dict(size=16, color="#64748B")
        )
    
    # Cek ketersediaan kolom
    required_cols = ['TARGET TEBUS 2500', 'ACTUAL TEBUS 2500', 'ACV TEBUS 2500']
    available_cols = [col for col in required_cols if col in df.columns]
    
    if not available_cols:
        return go.Figure().add_annotation(
            text="Kolom data tebus murah tidak ditemukan",
            xref="paper", yref="paper", x=0.5, y=0.5,
            showarrow=False, font=dict(size=16, color="#64748B")
        )
    
    # Group by kasir
    tebus_data = df.groupby('NAMA KASIR').agg({
        col: 'sum' if 'TARGET' in col or 'ACTUAL' in col else 'mean' 
        for col in available_cols
    }).reset_index()
    
    tebus_data = tebus_data.sort_values('ACV TEBUS 2500', ascending=False)
    
    # Buat subplots
    fig = make_subplots(
        specs=[[{"secondary_y": True}]],
        subplot_titles=["💰 Performa Tebus Murah Rp 2.500"]
    )
    
    # Bar chart untuk target vs actual
    if 'TARGET TEBUS 2500' in available_cols:
        fig.add_trace(
            go.Bar(
                x=tebus_data['NAMA KASIR'],
                y=tebus_data['TARGET TEBUS 2500'],
                name='Target',
                marker_color=COLOR_SCHEME['info'],
                opacity=0.7,
                hovertemplate="<b>%{x}</b><br>" +
                             "Target: %{y:,.0f} items<br>" +
                             "<extra></extra>"
            ),
            secondary_y=False
        )
    
    if 'ACTUAL TEBUS 2500' in available_cols:
        fig.add_trace(
            go.Bar(
                x=tebus_data['NAMA KASIR'],
                y=tebus_data['ACTUAL TEBUS 2500'],
                name='Actual',
                marker_color=COLOR_SCHEME['success'],
                opacity=0.8,
                hovertemplate="<b>%{x}</b><br>" +
                             "Actual: %{y:,.0f} items<br>" +
                             "<extra></extra>"
            ),
            secondary_y=False
        )
    
    # Line chart untuk ACV
    if 'ACV TEBUS 2500' in available_cols:
        fig.add_trace(
            go.Scatter(
                x=tebus_data['NAMA KASIR'],
                y=tebus_data['ACV TEBUS 2500'],
                mode='lines+markers',
                name='ACV (%)',
                line=dict(color=COLOR_SCHEME['accent'], width=3),
                marker=dict(size=8),
                hovertemplate="<b>%{x}</b><br>" +
                             "ACV: %{y:.2f}%<br>" +
                             "<extra></extra>"
            ),
            secondary_y=True
        )
    
    fig.update_xaxes(title_text="Nama Kasir")
    fig.update_yaxes(title_text="Jumlah Item", secondary_y=False)
    fig.update_yaxes(title_text="ACV (%)", ticksuffix="%", secondary_y=True)
    
    fig.update_layout(
        height=500,
        showlegend=True,
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1)
    )
    
    return fig

def create_trend_analysis_chart(df: pd.DataFrame) -> go.Figure:
    """Chart analisis tren performance"""
    if df.empty or 'TANGGAL' not in df.columns:
        return go.Figure().add_annotation(
            text="Data tanggal tidak tersedia untuk analisis tren",
            xref="paper", yref="paper", x=0.5, y=0.5,
            showarrow=False, font=dict(size=16, color="#64748B")
        )
    
    # Group by tanggal
    daily_performance = df.groupby(df['TANGGAL'].dt.date).agg({
        'TOTAL SCORE PPSA (CORRECTED)': ['mean', 'count'],
        'NAMA KASIR': 'nunique'
    }).reset_index()
    
    daily_performance.columns = ['Tanggal', 'Avg_Score', 'Total_Laporan', 'Jumlah_Kasir']
    
    # Hitung moving average
    daily_performance['MA_3'] = daily_performance['Avg_Score'].rolling(3, min_periods=1).mean()
    daily_performance['MA_7'] = daily_performance['Avg_Score'].rolling(7, min_periods=1).mean()
    
    fig = go.Figure()
    
    # Area chart untuk score harian
    fig.add_trace(go.Scatter(
        x=daily_performance['Tanggal'],
        y=daily_performance['Avg_Score'],
        mode='lines+markers',
        name='Score Harian',
        line=dict(color=COLOR_SCHEME['primary'], width=2),
        marker=dict(size=6),
        fill='tonexty',
        fillcolor=f"rgba(99, 102, 241, 0.1)",
        hovertemplate="<b>%{x}</b><br>" +
                     "Score: %{y:.2f}<br>" +
                     "<extra></extra>"
    ))
    
    # Moving averages
    fig.add_trace(go.Scatter(
        x=daily_performance['Tanggal'],
        y=daily_performance['MA_3'],
        mode='lines',
        name='MA 3 Hari',
        line=dict(color=COLOR_SCHEME['secondary'], width=2, dash='dot'),
        hovertemplate="<b>%{x}</b><br>" +
                     "MA 3 Hari: %{y:.2f}<br>" +
                     "<extra></extra>"
    ))
    
    fig.add_trace(go.Scatter(
        x=daily_performance['Tanggal'],
        y=daily_performance['MA_7'],
        mode='lines',
        name='MA 7 Hari',
        line=dict(color=COLOR_SCHEME['success'], width=3, dash='dash'),
        hovertemplate="<b>%{x}</b><br>" +
                     "MA 7 Hari: %{y:.2f}<br>" +
                     "<extra></extra>"
    ))
    
    fig.update_layout(
        title="<b>📈 Tren Performa Harian PPSA</b>",
        xaxis_title="Tanggal",
        yaxis_title="Rata-rata Score PPSA",
        height=500,
        hovermode='x unified'
    )
    
    return fig

def create_acv_comparison_chart(df: pd.DataFrame) -> go.Figure:
    """Chart perbandingan ACV semua indikator"""
    if df.empty:
        return go.Figure().add_annotation(
            text="Tidak ada data untuk ditampilkan",
            xref="paper", yref="paper", x=0.5, y=0.5,
            showarrow=False, font=dict(size=16, color="#64748B")
        )
    
    # Daftar semua kolom ACV
    acv_columns = []
    for col in df.columns:
        if 'ACV' in col and df[col].dtype in ['float64', 'int64']:
            acv_columns.append(col)
    
    if not acv_columns:
        return go.Figure().add_annotation(
            text="Data ACV tidak tersedia",
            xref="paper", yref="paper", x=0.5, y=0.5,
            showarrow=False, font=dict(size=16, color="#64748B")
        )
    
    # Hitung rata-rata untuk setiap ACV
    acv_averages = []
    for col in acv_columns:
        avg_val = df[col].mean()
        if not pd.isna(avg_val):
            acv_averages.append(avg_val)
        else:
            acv_averages.append(0)
    
    # Buat bar chart
    colors = [COLOR_SCHEME['primary'], COLOR_SCHEME['secondary'], COLOR_SCHEME['success'], 
              COLOR_SCHEME['warning'], COLOR_SCHEME['info']][:len(acv_columns)]
    
    fig = go.Figure(data=[
        go.Bar(
            x=acv_columns,
            y=acv_averages,
            marker_color=colors,
            text=[f"{val:.2f}%" for val in acv_averages],
            textposition='auto',
            hovertemplate="<b>%{x}</b><br>" +
                         "Rata-rata ACV: %{y:.2f}%<br>" +
                         "<extra></extra>"
        )
    ])
    
    fig.update_layout(
        title="<b>📊 Perbandingan Rata-rata ACV Semua Indikator</b>",
        xaxis_title="Indikator ACV",
        yaxis_title="Rata-rata ACV (%)",
        yaxis_ticksuffix="%",
        height=500
    )
    
    # Tambahkan garis target 100%
    fig.add_hline(y=100, line_dash="dash", line_color=COLOR_SCHEME['danger'], 
                  annotation_text="Target (100%)")
    
    return fig

# =========================================================
# -------------------- GEMINI AI INTEGRATION -------------
# =========================================================
def setup_gemini():
    """Setup Gemini AI"""
    try:
        api_key = st.secrets["gemini"]["api_key"]
        genai.configure(api_key=api_key)
        return genai.GenerativeModel('gemini-2.0-flash')
    except Exception as e:
        st.error(f"❌ Gagal setup Gemini AI: {e}")
        return None

def generate_advanced_insights(df: pd.DataFrame, model) -> str:
    """Generate advanced AI insights dari data"""
    if df.empty or model is None:
        return "Tidak dapat menghasilkan insight karena data kosong atau model tidak tersedia."
    
    # Siapkan data summary untuk AI
    total_records = len(df)
    unique_cashiers = df['NAMA KASIR'].nunique() if 'NAMA KASIR' in df.columns else 0
    total_hari_kerja = df['JHK'].sum() if 'JHK' in df.columns else 0
    
    # Analisis PPSA
    ppsa_summary = {}
    if 'TOTAL SCORE PPSA (CORRECTED)' in df.columns:
        scores = df['TOTAL SCORE PPSA (CORRECTED)']
        ppsa_summary = {
            'avg_score': scores.mean(),
            'max_score': scores.max(),
            'min_score': scores.min(),
            'std_score': scores.std()
        }
    
    # Analisis per indikator
    indicators_analysis = {}
    for indicator in ['PSM', 'PWP', 'SG', 'APC']:
        acv_col = f'{indicator} ACV'
        score_col = f'SCORE {indicator}'
        if acv_col in df.columns:
            indicators_analysis[indicator] = {
                'avg_acv': df[acv_col].mean(),
                'avg_score': df[score_col].mean() if score_col in df.columns else None
            }
    
    # Analisis ACV Tebus Murah
    tebus_murah_acv = df['ACV TEBUS 2500'].mean() if 'ACV TEBUS 2500' in df.columns else 0
    
    # Best and worst performers
    if 'NAMA KASIR' in df.columns and 'TOTAL SCORE PPSA (CORRECTED)' in df.columns:
        cashier_performance = df.groupby('NAMA KASIR')['TOTAL SCORE PPSA (CORRECTED)'].mean()
        best_performer = cashier_performance.idxmax()
        worst_performer = cashier_performance.idxmin()
        best_score = cashier_performance.max()
        worst_score = cashier_performance.min()
    else:
        best_performer = worst_performer = "N/A"
        best_score = worst_score = 0
    
    # Buat prompt untuk Gemini
    prompt = f"""
    Sebagai seorang Business Intelligence Analyst expert, analisis data performa kasir PPSA berikut:

    📊 RINGKASAN DATA:
    - Total Laporan/Entri: {total_records:,}
    - Jumlah Kasir Aktif: {unique_cashiers}
    - Total Hari Kerja (JHK): {total_hari_kerja:,.0f}
    - Period: {df['TANGGAL'].min().strftime('%d/%m/%Y') if 'TANGGAL' in df.columns else 'N/A'} - {df['TANGGAL'].max().strftime('%d/%m/%Y') if 'TANGGAL' in df.columns else 'N/A'}

    🎯 PERFORMA PPSA:
    - Rata-rata Total Score: {ppsa_summary.get('avg_score', 0):.2f}
    - Score Tertinggi: {ppsa_summary.get('max_score', 0):.2f}
    - Score Terendah: {ppsa_summary.get('min_score', 0):.2f}
    - Standar Deviasi: {ppsa_summary.get('std_score', 0):.2f}

    📈 ANALISIS PER INDIKATOR (SEMUA DALAM %):
    """ + "\n".join([f"- {indicator}: ACV {data['avg_acv']:.2f}%, Score {data['avg_score']:.2f}" if data['avg_score'] else f"- {indicator}: ACV {data['avg_acv']:.2f}%"
                     for indicator, data in indicators_analysis.items()]) + f"""
    
    💰 TEBUS MURAH:
    - ACV Tebus Murah: {tebus_murah_acv:.2f}%

    🏆 PERFORMA KASIR:
    - Terbaik: {best_performer} ({best_score:.2f} poin)
    - Terburuk: {worst_performer} ({worst_score:.2f} poin)
    - Gap Performa: {best_score - worst_score:.2f} poin

    Berikan analisis mendalam yang mencakup:

    1. 🔍 ANALISIS PERFORMA KESELURUHAN
    - Bagaimana performa PPSA secara umum?
    - Indikator mana yang paling berkontribusi/menghambat?
    - Apakah ada pola atau tren yang menarik?

    2. ⚠️ AREA CRITICAL & OPPORTUNITY
    - Indikator mana yang butuh perhatian khusus?
    - Kasir mana yang perlu coaching intensif?
    - Potensi peningkatan score jika fokus pada area tertentu?

    3. 🚀 REKOMENDASI STRATEGIS
    - Action plan konkret untuk meningkatkan performa
    - Prioritas improvement berdasarkan bobot indikator
    - Target realistis untuk periode berikutnya (dengan target sempurna 100)

    4. 💡 INSIGHTS BISNIS
    - Correlation antara performa kasir dengan faktor lain
    - Benchmark industry jika applicable
    - Prediksi dampak jika rekomendasi dijalankan

    **CATATAN PENTING:**
    - Data ini adalah data teragregasi per periode (harian/mingguan/bulanan).
    - Total Records adalah jumlah laporan, bukan jumlah transaksi individual.
    - JHK adalah Jumlah Hari Kerja.
    - Semua nilai ACV adalah persentase (%).
    - PSM = Promo Spesial Mingguan
    - PWP = Purchase With Purchase
    - SG = Serba Gratis
    - APC = Average Purchase Customer

    Format response dalam bahasa Indonesia yang profesional namun engaging, gunakan emoji untuk memperjelas poin-poin penting.
    """
    
    try:
        response = model.generate_content(prompt)
        return response.text
    except Exception as e:
        return f"❌ Terjadi kesalahan saat menghasilkan insight: {e}"

# =========================================================
# -------------------- SIDEBAR CONTROLS ------------------
# =========================================================
def render_sidebar(df: pd.DataFrame) -> Dict:
    """Render sidebar dengan controls modern"""
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
        
        # Shift filter
        if 'SHIFT' in df.columns and not df.empty:
            shifts = ['Semua'] + sorted(df['SHIFT'].unique().tolist())
            filters['shifts'] = st.multiselect(
                "⏰ Pilih Shift",
                options=shifts,
                default=['Semua']
            )
        
        st.markdown("---")
        
        # Refresh button
        if st.button("🔄 Refresh Data", use_container_width=True):
            st.cache_data.clear()
            st.rerun()
        
        # Data info
        if not df.empty:
            # Hitung nilai-nilai terlebih dahulu sebelum memasukkannya ke f-string
            total_records_count = f"{len(df):,}"
            kasir_aktif_count = f"{df['NAMA KASIR'].nunique()}" if 'NAMA KASIR' in df.columns else 'N/A'
            total_hari_kerja_str = f"{df['JHK'].sum():,.0f}" if 'JHK' in df.columns else 'N/A'
            
            periode_start = df['TANGGAL'].min().strftime('%d/%m/%Y') if 'TANGGAL' in df.columns else 'N/A'
            periode_end = df['TANGGAL'].max().strftime('%d/%m/%Y') if 'TANGGAL' in df.columns else 'N/A'
            
            st.markdown("### 📋 Data Info")
            st.info(f"""
            **Total Records:** {total_records_count}  
            **Kasir Aktif:** {kasir_aktif_count}  
            **Total Hari Kerja:** {total_hari_kerja_str}  
            **Periode:** {periode_start} - {periode_end}
            """)
        
        return {'spreadsheet_url': spreadsheet_url, 'sheet_name': sheet_name, **filters}

# =========================================================
# ----------------------- MAIN APP -----------------------
# =========================================================
def main():
    """Main application function"""
    
    # Hero Section
    st.markdown("""
    <div class="hero-section">
        <h1 class="hero-title">🚀 Dashboard PPSA & Tebus Murah 2025</h1>
        <p class="hero-subtitle">
            Advanced Analytics Dashboard dengan AI-powered insights untuk monitoring performa kasir secara real-time.
            <br><strong>🏪 Toko:</strong> 2GC6 BAROS PANDEGLANG
        </p>
    </div>
    """, unsafe_allow_html=True)
    
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
    avg_ppsa_score = filtered_df['TOTAL SCORE PPSA (CORRECTED)'].mean() if 'TOTAL SCORE PPSA (CORRECTED)' in filtered_df.columns else 0
    
    # Calculate Total Hari Kerja (JHK)
    if 'JHK' in filtered_df.columns:
        total_hari_kerja = filtered_df['JHK'].sum()
    else:
        total_hari_kerja = 0
    
    # Tebus Murah metrics
    if 'ACTUAL TEBUS 2500' in filtered_df.columns:
        total_tebus_actual = filtered_df['ACTUAL TEBUS 2500'].sum()
    else:
        total_tebus_actual = 0
    
    if 'ACV TEBUS 2500' in filtered_df.columns:
        avg_tebus_acv = filtered_df['ACV TEBUS 2500'].mean()
    else:
        avg_tebus_acv = 0
    
    # Render metrics grid
    st.markdown('<div class="metrics-grid">', unsafe_allow_html=True)
    
    col1, col2, col3, col4, col5 = st.columns(5)
    
    with col1:
        st.markdown(create_metric_card(
            "Total Hari Kerja (JHK)",
            format_number(total_hari_kerja),
            icon="📅"
        ), unsafe_allow_html=True)
    
    with col2:
        # Global PPSA Score
        delta_type = "positive" if global_ppsa['global_score'] >= 80 else "warning" if global_ppsa['global_score'] >= 60 else "negative"
        st.markdown(create_metric_card(
            "Global PPSA Score",
            format_score(global_ppsa['global_score']),
            delta=f"Target: 100.00",
            delta_type=delta_type,
            icon="🌍"
        ), unsafe_allow_html=True)
    
    with col3:
        delta_type = "positive" if avg_ppsa_score >= 80 else "warning" if avg_ppsa_score >= 60 else "negative"
        st.markdown(create_metric_card(
            "Rata-rata Score PPSA",
            format_score(avg_ppsa_score),
            delta=f"Target: 100.00",
            delta_type=delta_type,
            icon="🎯"
        ), unsafe_allow_html=True)
    
    with col4:
        st.markdown(create_metric_card(
            "Total Tebus Murah",
            format_number(total_tebus_actual),
            icon="💰"
        ), unsafe_allow_html=True)
    
    with col5:
        delta_type = "positive" if avg_tebus_acv >= 80 else "warning" if avg_tebus_acv >= 60 else "negative"
        st.markdown(create_metric_card(
            "ACV Tebus Murah",
            format_percentage(avg_tebus_acv),
            delta="Target: 100.00%",
            delta_type=delta_type,
            icon="📈"
        ), unsafe_allow_html=True)
    
    st.markdown('</div>', unsafe_allow_html=True)
    
    # Global PPSA Score Details
    with st.expander("🌍 Detail Global PPSA Score", expanded=False):
        st.markdown("### Kontribusi Setiap Indikator terhadap Global Score")
        
        details_data = []
        for indicator, data in global_ppsa['details'].items():
            details_data.append({
                'Indikator': indicator,
                'ACV': format_percentage(data['acv']),
                'Bobot': format_score(data['bobot']),
                'Kontribusi': format_score(data['kontribusi'])
            })
        
        details_df = pd.DataFrame(details_data)
        st.dataframe(details_df, use_container_width=True)
        
        st.markdown(f"""
        **Total Global PPSA Score:** {format_score(global_ppsa['global_score'])}
        
        **Cara Perhitungan:**
        - Score per Indikator = (ACV / 100) × Bobot
        - Total Global Score = Σ(Score PSM + PWP + SG + APC)
        """)
    
    # Main Content Tabs
    tab1, tab2, tab3, tab4, tab5 = st.tabs([
        "📊 Analisis PPSA",
        "💰 Tebus Murah",
        "📈 Tren & Performa",
        "🤖 AI Insights",
        "📄 Raw Data"
    ])
    
    with tab1:
        st.markdown("### 📊 Analisis PPSA Comprehensive")
        
        # Informasi PPSA
        with st.expander("ℹ️ Informasi Tentang Indikator PPSA", expanded=False):
            st.markdown("""
            **PPSA (Program Penjualan Sales Assistant)** adalah kumpulan indikator performa penjualan yang terdiri dari:
            
            - **PSM (Promo Spesial Mingguan)**: Program promosi yang dijalankan mingguan
            - **PWP (Purchase With Purchase)**: Program beli gratis/beli dapat bonus  
            - **SG (Serba Gratis)**: Program produk gratis
            - **APC (Average Purchase Customer)**: Rata-rata nilai pembelian per pelanggan
            
            **ACV (Actual vs Target)** adalah persentase pencapaian terhadap target yang ditetapkan.
            Semua kolom ACV adalah nilai persentase (%).
            
            **Catatan Penting:** Data ini adalah data teragregasi per periode. Jumlah baris data mewakili jumlah laporan, bukan jumlah transaksi individual.
            """)
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.markdown('<div class="chart-container">', unsafe_allow_html=True)
            st.plotly_chart(create_ppsa_radar_chart(filtered_df), use_container_width=True)
            st.markdown('</div>', unsafe_allow_html=True)
        
        with col2:
            # PPSA Score Distribution
            if 'TOTAL SCORE PPSA (CORRECTED)' in filtered_df.columns:
                scores = filtered_df['TOTAL SCORE PPSA (CORRECTED)']
                
                fig = go.Figure(data=[go.Histogram(
                    x=scores,
                    nbinsx=20,
                    marker_color=COLOR_SCHEME['primary'],
                    opacity=0.7,
                    hovertemplate="<b>Score PPSA</b><br>" +
                                 "Range: %{x:.2f}<br>" +
                                 "Frekuensi: %{y}<br>" +
                                 "<extra></extra>"
                )])
                
                fig.update_layout(
                    title="<b>🔔 Distribusi Score PPSA</b>",
                    xaxis_title="Score PPSA",
                    yaxis_title="Frekuensi",
                    height=500
                )
                
                st.markdown('<div class="chart-container">', unsafe_allow_html=True)
                st.plotly_chart(fig, use_container_width=True)
                st.markdown('</div>', unsafe_allow_html=True)
        
        # Cashier Performance Chart
        st.markdown('<div class="chart-container">', unsafe_allow_html=True)
        st.plotly_chart(create_cashier_performance_chart(filtered_df), use_container_width=True)
        st.markdown('</div>', unsafe_allow_html=True)
        
        # Detail Score per Indicator
        st.markdown("#### 📋 Detail Score per Indikator")
        
        score_cols = []
        for indicator in ['PSM', 'PWP', 'SG', 'APC']:
            score_col = f'SCORE {indicator}'
            if score_col in filtered_df.columns:
                score_cols.append(score_col)
        
        if score_cols and 'NAMA KASIR' in filtered_df.columns:
            score_detail = filtered_df.groupby('NAMA KASIR')[score_cols].mean().reset_index()
            score_detail['TOTAL SCORE'] = score_detail[score_cols].sum(axis=1)
            score_detail = score_detail.sort_values('TOTAL SCORE', ascending=False)
            
            # Format the dataframe with 2 decimal places
            formatted_score_detail = score_detail.copy()
            for col in score_cols + ['TOTAL SCORE']:
                formatted_score_detail[col] = formatted_score_detail[col].apply(lambda x: format_score(x))
            
            st.dataframe(formatted_score_detail, use_container_width=True)
        
        # ACV Comparison Chart
        st.markdown('<div class="chart-container">', unsafe_allow_html=True)
        st.plotly_chart(create_acv_comparison_chart(filtered_df), use_container_width=True)
        st.markdown('</div>', unsafe_allow_html=True)
    
    with tab2:
        st.markdown("### 💰 Analisis Tebus Murah")
        
        st.markdown('<div class="chart-container">', unsafe_allow_html=True)
        st.plotly_chart(create_tebus_murah_chart(filtered_df), use_container_width=True)
        st.markdown('</div>', unsafe_allow_html=True)
        
        # Detail table
        if all(col in filtered_df.columns for col in ['TARGET TEBUS 2500', 'ACTUAL TEBUS 2500']):
            st.markdown("#### 📋 Detail Performa Tebus Murah")
            
            tebus_detail = filtered_df.groupby('NAMA KASIR').agg({
                'TARGET TEBUS 2500': 'sum',
                'ACTUAL TEBUS 2500': 'sum'
            }).reset_index()
            
            tebus_detail['ACV (%)'] = (tebus_detail['ACTUAL TEBUS 2500'] / tebus_detail['TARGET TEBUS 2500'] * 100).round(2)
            tebus_detail['Gap'] = tebus_detail['TARGET TEBUS 2500'] - tebus_detail['ACTUAL TEBUS 2500']
            
            # Format the dataframe
            formatted_tebus_detail = tebus_detail.copy()
            formatted_tebus_detail['TARGET TEBUS 2500'] = formatted_tebus_detail['TARGET TEBUS 2500'].apply(lambda x: format_number(x))
            formatted_tebus_detail['ACTUAL TEBUS 2500'] = formatted_tebus_detail['ACTUAL TEBUS 2500'].apply(lambda x: format_number(x))
            formatted_tebus_detail['ACV (%)'] = formatted_tebus_detail['ACV (%)'].apply(lambda x: format_percentage(x))
            formatted_tebus_detail['Gap'] = formatted_tebus_detail['Gap'].apply(lambda x: format_number(x))
            
            # Color coding for performance
            def color_performance(val):
                if val >= 100:
                    return f'background-color: {COLOR_SCHEME["success"]}33'
                elif val >= 80:
                    return f'background-color: {COLOR_SCHEME["warning"]}33'
                else:
                    return f'background-color: {COLOR_SCHEME["danger"]}33'
            
            styled_df = tebus_detail.style.applymap(color_performance, subset=['ACV (%)'])
            st.dataframe(styled_df, use_container_width=True)
    
    with tab3:
        st.markdown("### 📈 Tren & Analisis Performa")
        
        st.markdown('<div class="chart-container">', unsafe_allow_html=True)
        st.plotly_chart(create_trend_analysis_chart(filtered_df), use_container_width=True)
        st.markdown('</div>', unsafe_allow_html=True)
        
        # Performance correlation matrix
        if len(filtered_df) > 1:
            st.markdown("#### 🔗 Korelasi Antar Indikator ACV")
            
            corr_cols = []
            for indicator in ['PSM', 'PWP', 'SG', 'APC']:
                acv_col = f'{indicator} ACV'
                if acv_col in filtered_df.columns:
                    corr_cols.append(acv_col)
            
            # Tambahkan ACV TEBUS 2500 jika ada
            if 'ACV TEBUS 2500' in filtered_df.columns:
                corr_cols.append('ACV TEBUS 2500')
            
            if len(corr_cols) > 1:
                correlation_matrix = filtered_df[corr_cols].corr()
                
                fig = px.imshow(
                    correlation_matrix,
                    color_continuous_scale='RdBu',
                    aspect='auto',
                    labels=dict(color="Korelasi"),
                    title="<b>🔗 Heatmap Korelasi Semua Indikator ACV (%)</b>",
                    text_auto=True,
                    color_continuous_midpoint=0
                )
                
                st.markdown('<div class="chart-container">', unsafe_allow_html=True)
                st.plotly_chart(fig, use_container_width=True)
                st.markdown('</div>', unsafe_allow_html=True)
    
    with tab4:
        st.markdown("### 🤖 AI-Powered Business Insights")
        
        gemini_model = setup_gemini()
        
        if gemini_model is None:
            st.error("❌ Gemini AI tidak tersedia. Pastikan API key sudah dikonfigurasi.")
        else:
            col1, col2 = st.columns([3, 1])
            
            with col2:
                if st.button("🔮 Generate AI Insights", type="primary", use_container_width=True):
                    with st.spinner("🧠 AI sedang menganalisis data..."):
                        insights = generate_advanced_insights(filtered_df, gemini_model)
                        st.session_state['ai_insights'] = insights
            
            with col1:
                st.markdown("Klik tombol untuk mendapatkan analisis mendalam dari AI mengenai performa kasir.")
            
            # Display insights if available
            if 'ai_insights' in st.session_state:
                st.markdown('<div class="ai-response">', unsafe_allow_html=True)
                st.markdown(st.session_state['ai_insights'])
                st.markdown('</div>', unsafe_allow_html=True)
    
    with tab5:
        st.markdown("### 📄 Raw Data & Export")
        
        # Export functionality
        col1, col2, col3 = st.columns([1, 1, 2])
        
        with col1:
            # Export to CSV
            csv = filtered_df.to_csv(index=False)
            st.download_button(
                label="📥 Download CSV",
                data=csv,
                file_name=f"ppsa_data_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
                mime="text/csv",
                use_container_width=True
            )
        
        with col2:
            # Export to Excel
            buffer = BytesIO()
            with pd.ExcelWriter(buffer, engine='openpyxl') as writer:
                filtered_df.to_excel(writer, sheet_name='PPSA Data', index=False)
            
            st.download_button(
                label="📊 Download Excel",
                data=buffer.getvalue(),
                file_name=f"ppsa_data_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                use_container_width=True
            )
        
        # Data preview
        st.markdown("#### 👁️ Preview Data")
        
        # Show column info
        st.markdown("**📋 Informasi Kolom:**")
        col_info = pd.DataFrame({
            'Kolom': filtered_df.columns,
            'Tipe Data': filtered_df.dtypes.astype(str),
            'Non-Null Count': filtered_df.count(),
            'Null Count': filtered_df.isnull().sum()
        })
        st.dataframe(col_info, use_container_width=True)
        
        # Show actual data
        st.markdown("**📊 Data Sample:**")
        st.dataframe(filtered_df.head(100), use_container_width=True)
    
    # Footer
    st.markdown("---")
    st.markdown("""
    <div style="text-align: center; color: #64748B; font-size: 0.9rem;">
        <p>🚀 <strong>Dashboard PPSA & Tebus Murah 2025</strong> | 
        Powered by <strong>Streamlit</strong> + <strong>Plotly</strong> + <strong>Gemini AI</strong><br>
        © 2025 Advanced Business Analytics | Designed with ❤️ for better insights</p>
    </div>
    """, unsafe_allow_html=True)

if __name__ == "__main__":
    main()
