import streamlit as st
import pandas as pd
import gspread
from gspread_dataframe import get_as_dataframe
from oauth2client.service_account import ServiceAccountCredentials
import plotly.express as px
import plotly.graph_objects as go
import plotly.io as pio
from datetime import datetime, timedelta
from typing import Optional, Tuple, List
import numpy as np
from scipy import stats
from plotly.subplots import make_subplots
import google.generativeai as genai
import re

# =========================================================
# ------------------- KONFIGURASI AWAL --------------------
# =========================================================
st.set_page_config(
    page_title="Dashboard PPSA & Tebus Murah",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Palet warna kekinian
COLOR_PRIMARY = "#6366F1"     # Indigo neon
COLOR_ACCENT = "#22D3EE"      # Cyan terang
COLOR_SUCCESS = "#34D399"     # Hijau pastel
COLOR_WARNING = "#FACC15"     # Kuning keemasan
COLOR_DANGER = "#F97316"      # Oranye sunset
COLOR_NEGATIVE = "#FB7185"    # Merah salmon
COLOR_BG = "#0F172A"          # Biru gelap
COLOR_CARD = "rgba(15, 23, 42, 0.65)"
COLOR_BORDER = "rgba(148, 163, 184, 0.28)"

PLOTLY_COLORWAY = [
    "#6366F1", "#22D3EE", "#34D399", "#F97316",
    "#FACC15", "#A855F7", "#38BDF8", "#FB7185", "#F472B6"
]

CUSTOM_CSS = """
<style>
:root {
    --color-primary: #6366F1;
    --color-accent: #22D3EE;
    --color-success: #34D399;
    --color-warning: #FACC15;
    --color-danger: #F97316;
    --color-negative: #FB7185;
    --color-bg: #0F172A;
    --color-bg-secondary: rgba(15, 23, 42, 0.75);
    --color-card: rgba(15, 23, 42, 0.65);
    --color-border: rgba(148, 163, 184, 0.28);
    --color-text: #E2E8F0;
    --color-text-muted: #94A3B8;
    --color-highlight: rgba(99, 102, 241, 0.22);
    --radius: 20px;
    --blur: 22px;
    --transition: 0.25s ease;
}

body {
    font-family: 'Inter', 'Segoe UI', system-ui, -apple-system, BlinkMacSystemFont, sans-serif;
    color: var(--color-text);
    background: radial-gradient(circle at top left, rgba(99,102,241,0.18), transparent 55%),
                radial-gradient(circle at top right, rgba(34,211,238,0.18), transparent 55%),
                radial-gradient(circle at bottom, rgba(251,113,133,0.18), transparent 55%),
                var(--color-bg);
}

[data-testid="stAppViewContainer"] {
    background: transparent;
}

section.main > div {
    padding-top: 1.2rem;
}

h1, h2, h3, h4, h5, h6 {
    color: var(--color-text) !important;
    letter-spacing: 0.01em;
}

.stTabs [role="tablist"] {
    gap: 0.75rem;
}

.stTabs [role="tab"] {
    padding: 0.85rem 1.35rem;
    background: rgba(99, 102, 241, 0.08);
    border-radius: var(--radius);
    border: 1px solid transparent;
    transition: var(--transition);
    color: var(--color-text-muted);
    font-weight: 600;
}

.stTabs [role="tab"]:hover {
    border-color: rgba(34, 211, 238, 0.4);
    color: var(--color-accent);
}

.stTabs [aria-selected="true"] {
    background: var(--color-card);
    border-color: rgba(99, 102, 241, 0.55);
    color: var(--color-text);
    box-shadow: 0 12px 30px -12px rgba(99, 102, 241, 0.6);
}

[data-testid="stSidebar"] {
    background: rgba(15, 23, 42, 0.85);
    border-right: 1px solid var(--color-border);
    backdrop-filter: blur(var(--blur));
}

[data-testid="stSidebar"] * {
    color: var(--color-text);
}

.stButton button, .stDownloadButton button {
    border-radius: 999px !important;
    background: linear-gradient(135deg, rgba(99,102,241,0.15), rgba(34,211,238,0.15));
    color: var(--color-text);
    border: 1px solid rgba(99,102,241,0.35);
    transition: var(--transition);
    font-weight: 600;
    letter-spacing: 0.03em;
}

.stButton button:hover, .stDownloadButton button:hover {
    border-color: rgba(34,211,238,0.55);
    background: linear-gradient(135deg, rgba(99,102,241,0.25), rgba(34,211,238,0.25));
    box-shadow: 0 12px 30px -14px rgba(34, 211, 238, 0.65);
}

.metric-grid {
    display: grid;
    gap: 1.2rem;
    grid-template-columns: repeat(auto-fit, minmax(240px, 1fr));
}

.metric-card {
    background: linear-gradient(160deg, rgba(99,102,241,0.16), rgba(15,23,42,0.6));
    border-radius: var(--radius);
    padding: 1.4rem 1.6rem;
    border: 1px solid var(--color-border);
    backdrop-filter: blur(var(--blur));
    box-shadow: 0 20px 45px -25px rgba(15, 23, 42, 0.9);
    transition: var(--transition);
    position: relative;
    overflow: hidden;
}

.metric-card::after {
    content: "";
    position: absolute;
    inset: -40% 30% auto auto;
    width: 180px;
    height: 180px;
    background: radial-gradient(circle, rgba(34, 211, 238, 0.28) 0%, transparent 60%);
    transform: rotate(35deg);
    opacity: 0.9;
}

.metric-card:hover {
    transform: translateY(-6px);
    border-color: rgba(34, 211, 238, 0.55);
    box-shadow: 0 24px 55px -28px rgba(34, 211, 238, 0.55);
}

.metric-card .metric-icon {
    font-size: 1.8rem;
    margin-bottom: 0.35rem;
}

.metric-card .metric-label {
    font-size: 0.78rem;
    letter-spacing: 0.26em;
    text-transform: uppercase;
    color: var(--color-text-muted);
    margin-bottom: 0.25rem;
}

.metric-card .metric-value {
    font-size: clamp(1.75rem, 3vw, 2.45rem);
    font-weight: 700;
    color: var(--color-text);
    margin: 0.15rem 0 0.5rem;
}

.metric-card .metric-delta {
    display: inline-flex;
    gap: 0.4rem;
    align-items: center;
    font-size: 0.95rem;
    font-weight: 600;
}

.delta-positive { color: var(--color-success); }
.delta-negative { color: var(--color-negative); }
.delta-neutral { color: var(--color-warning); }

.hero-card {
    background: linear-gradient(135deg, rgba(99,102,241,0.32), rgba(37,99,235,0.18));
    border-radius: calc(var(--radius) * 1.1);
    border: 1px solid rgba(99, 102, 241, 0.38);
    padding: 1.6rem 1.8rem;
    margin-bottom: 1.8rem;
    position: relative;
    overflow: hidden;
    box-shadow: 0 28px 60px -32px rgba(99, 102, 241, 0.65);
}

.hero-card::before {
    content: "";
    position: absolute;
    inset: 12% -25% auto auto;
    width: 260px;
    height: 260px;
    border-radius: 50%;
    background: radial-gradient(circle, rgba(34,211,238,0.35), transparent 65%);
    filter: blur(2px);
    opacity: 0.65;
    animation: pulseGlow 6s ease-in-out infinite alternate;
}

@keyframes pulseGlow {
    from { transform: scale(0.95); opacity: 0.55; }
    to { transform: scale(1.08); opacity: 0.85; }
}

.hero-card h1 {
    font-size: clamp(2rem, 3.5vw, 2.8rem);
    margin-bottom: 0.6rem;
}

.hero-card p {
    color: var(--color-text-muted);
    font-size: 1.02rem;
    max-width: 62ch;
    line-height: 1.65;
}

.insight-card {
    background: var(--color-card);
    border-radius: var(--radius);
    border: 1px solid rgba(99,102,241,0.28);
    padding: 1.2rem 1.35rem;
    backdrop-filter: blur(var(--blur));
    position: relative;
    overflow: hidden;
    transition: var(--transition);
}

.insight-card::after {
    content: "";
    position: absolute;
    inset: 65% -30% auto auto;
    width: 160px;
    height: 160px;
    background: radial-gradient(circle, rgba(99,102,241,0.22), transparent 65%);
    opacity: 0.55;
}

.insight-card strong {
    color: var(--color-accent);
}

.stDataFrame {
    border-radius: calc(var(--radius) * 0.9);
    border: 1px solid rgba(99,102,241,0.18);
    overflow: hidden;
}

[data-testid="stDataFrame"] div[role="table"] {
    border-radius: 0;
}

.chart-container {
    background: var(--color-card);
    border-radius: var(--radius);
    border: 1px solid var(--color-border);
    padding: 1.2rem;
    margin-bottom: 1.5rem;
    backdrop-filter: blur(var(--blur));
    box-shadow: 0 20px 45px -25px rgba(15, 23, 42, 0.9);
}

.ai-response {
    background: linear-gradient(160deg, rgba(34,211,238,0.12), rgba(15,23,42,0.6));
    border-radius: var(--radius);
    border: 1px solid rgba(34,211,238,0.28);
    padding: 1.2rem;
    margin-bottom: 1rem;
    backdrop-filter: blur(var(--blur));
}

.ai-response h4 {
    color: var(--color-accent);
    margin-bottom: 0.5rem;
}

.ai-response p {
    color: var(--color-text);
    font-size: 0.95rem;
    line-height: 1.6;
    margin-bottom: 0;
}

</style>
"""

st.markdown(CUSTOM_CSS, unsafe_allow_html=True)

# =========================================================
# ----------------- KONFIGURASI PLOTLY --------------------
# =========================================================
def configure_plotly_theme() -> None:
    template = go.layout.Template(
        layout=go.Layout(
            font=dict(family="Inter, 'Segoe UI', sans-serif", color="#E2E8F0"),
            title=dict(font=dict(size=22, family="Inter, 'Segoe UI', sans-serif", color="#F8FAFC")),
            paper_bgcolor="rgba(15, 23, 42, 0)",
            plot_bgcolor="rgba(15, 23, 42, 0.35)",
            legend=dict(
                bgcolor="rgba(15, 23, 42, 0.6)",
                bordercolor="rgba(148, 163, 184, 0.25)",
                borderwidth=1,
                font=dict(size=13)
            ),
            margin=dict(l=60, r=40, t=80, b=60),
            xaxis=dict(gridcolor="rgba(148,163,184,0.22)", zerolinecolor="rgba(148,163,184,0.32)"),
            yaxis=dict(gridcolor="rgba(148,163,184,0.22)", zerolinecolor="rgba(148,163,184,0.32)"),
            colorway=PLOTLY_COLORWAY
        )
    )
    pio.templates["neon_glass"] = template
    px.defaults.template = "neon_glass"
    px.defaults.color_discrete_sequence = PLOTLY_COLORWAY

configure_plotly_theme()

# =========================================================
# ------------------- FUNGSI UTILITAS ---------------------
# =========================================================
def format_currency(value: float) -> str:
    try:
        return f"Rp {value:,.0f}".replace(",", "X").replace(".", ",").replace("X", ".")
    except (TypeError, ValueError):
        return "Rp 0"


def format_quantity(value: float) -> str:
    try:
        return f"{value:,.0f}".replace(",", ".")
    except (TypeError, ValueError):
        return "0"


def render_metric_card(
    title: str,
    value: str,
    delta_label: Optional[str] = None,
    delta_type: str = "neutral",
    icon: str = "📌"
) -> None:
    delta_class = {
        "positive": "delta-positive",
        "negative": "delta-negative",
        "neutral": "delta-neutral"
    }.get(delta_type, "delta-neutral")

    delta_markup = ""
    if delta_label:
        delta_markup = f'<div class="metric-delta {delta_class}">{delta_label}</div>'

    st.markdown(
        f"""
        <div class="metric-card">
            <div class="metric-icon">{icon}</div>
            <div class="metric-label">{title}</div>
            <div class="metric-value">{value}</div>
            {delta_markup}
        </div>
        """,
        unsafe_allow_html=True
    )


@st.cache_data(ttl=600, show_spinner=False)
def load_data(spreadsheet_url: str, sheet_name: str) -> Optional[pd.DataFrame]:
    scope = [
        "https://www.googleapis.com/auth/spreadsheets",
        "https://www.googleapis.com/auth/drive"
    ]
    try:
        creds_dict = st.secrets["gcp_service_account"]
        creds = ServiceAccountCredentials.from_json_keyfile_dict(creds_dict, scope)
        client = gspread.authorize(creds)
        spreadsheet = client.open_by_url(spreadsheet_url)
        worksheet = spreadsheet.worksheet(sheet_name)
        df = get_as_dataframe(worksheet, evaluate_formulas=True)
    except Exception as exc:
        st.error(f"Gagal memuat data: {exc}")
        return None

    df.dropna(axis=0, how="all", inplace=True)
    df.columns = df.columns.str.strip()
    
    return df


def filter_dataframe(
    df: pd.DataFrame,
    date_range: Tuple[datetime, datetime],
    selected_cashiers: List[str],
    selected_shifts: List[str]
) -> pd.DataFrame:
    filtered = df.copy()
    
    # Filter berdasarkan rentang tanggal
    if isinstance(date_range, tuple) and len(date_range) == 2:
        start_date, end_date = date_range
    else:
        start_date = end_date = date_range[0] if date_range else datetime.today()

    # Konversi kolom tanggal jika ada
    if 'TANGGAL' in df.columns:
        df['TANGGAL'] = pd.to_datetime(df['TANGGAL'], errors='coerce', dayfirst=True)
        start_ts = pd.to_datetime(start_date)
        end_ts = pd.to_datetime(end_date) + pd.Timedelta(days=1) - pd.Timedelta(seconds=1)
        filtered = filtered[
            (filtered["TANGGAL"] >= start_ts) &
            (filtered["TANGGAL"] <= end_ts)
        ]

    # Filter berdasarkan kasir
    if selected_cashiers and "Semua" not in selected_cashiers:
        if 'NAMA KASIR' in df.columns:
            filtered = filtered[filtered["NAMA KASIR"].isin(selected_cashiers)]

    # Filter berdasarkan shift
    if selected_shifts and "Semua" not in selected_shifts:
        if 'SHIFT' in df.columns:
            filtered = filtered[filtered["SHIFT"].isin(selected_shifts)]

    return filtered


def render_insight_card(title: str, value: str, description: str, icon: str = "✨") -> None:
    st.markdown(
        f"""
        <div class="insight-card">
            <h4>{icon} {title}</h4>
            <p><strong>{value}</strong></p>
            <p style="color: var(--color-text-muted); margin-bottom: 0;">{description}</p>
        </div>
        """,
        unsafe_allow_html=True
    )

# =========================================================
# ------------------- FUNGSI VISUALISASI -------------------
# =========================================================
def create_ppsa_radar_chart(df: pd.DataFrame) -> go.Figure:
    # Hitung rata-rata ACV per indikator
    indicators = ['PSM', 'PWP', 'SG', 'APC']
    avg_acv = {}
    
    for indicator in indicators:
        acv_col = f'{indicator} ACV'
        if acv_col in df.columns:
            # Konversi nilai ACV ke numerik
            df[acv_col] = df[acv_col].astype(str).str.replace('%', '').str.replace(',', '.')
            df[acv_col] = pd.to_numeric(df[acv_col], errors='coerce')
            avg_acv[indicator] = df[acv_col].mean()
    
    # Buat chart radar
    fig = go.Figure()
    
    fig.add_trace(go.Scatterpolar(
        r=list(avg_acv.values()),
        theta=list(avg_acv.keys()),
        fill='toself',
        name='Rata-rata ACV',
        line_color=COLOR_PRIMARY,
        fillcolor=f'rgba(99, 102, 241, 0.25)'
    ))
    
    # Tambahkan garis target (100%)
    fig.add_trace(go.Scatterpolar(
        r=[100, 100, 100, 100],
        theta=list(avg_acv.keys()),
        mode='lines',
        name='Target (100%)',
        line_color=COLOR_ACCENT,
        line_dash='dash'
    ))
    
    fig.update_layout(
        polar=dict(
            radialaxis=dict(
                visible=True,
                range=[0, 120]
            )
        ),
        title="<b>Radar Performa PPSA</b>",
        title_x=0.5
    )
    
    return fig


def create_cashier_performance_chart(df: pd.DataFrame) -> go.Figure:
    # Hitung total score per kasir
    if 'TOTAL SCORE PPSA' in df.columns:
        # Konversi ke numerik
        df['TOTAL SCORE PPSA'] = pd.to_numeric(df['TOTAL SCORE PPSA'], errors='coerce')
        
        cashier_scores = df.groupby('NAMA KASIR')['TOTAL SCORE PPSA'].mean().reset_index()
        cashier_scores = cashier_scores.sort_values('TOTAL SCORE PPSA', ascending=False)
        
        fig = px.bar(
            cashier_scores,
            x='TOTAL SCORE PPSA',
            y='NAMA KASIR',
            orientation='h',
            color='TOTAL SCORE PPSA',
            color_continuous_scale=[COLOR_NEGATIVE, COLOR_WARNING, COLOR_SUCCESS],
            labels={'TOTAL SCORE PPSA': 'Total Score', 'NAMA KASIR': 'Nama Kasir'},
            title="<b>Performa Kasir (Total Score PPSA)</b>",
            height=500
        )
        
        fig.update_layout(
            yaxis=dict(categoryorder='total ascending'),
            title_x=0.5,
            coloraxis_showscale=False
        )
        
        return fig
    
    # Fallback jika kolom tidak ada
    fig = go.Figure()
    fig.add_annotation(
        text="Kolom TOTAL SCORE PPSA tidak ditemukan",
        xref="paper", yref="paper",
        x=0.5, y=0.5,
        showarrow=False,
        font=dict(color="#CBD5F5", size=16)
    )
    fig.update_layout(title="<b>Performa Kasir</b>", title_x=0.5)
    return fig


def create_tebus_murah_chart(df: pd.DataFrame) -> go.Figure:
    # Konversi kolom yang relevan
    if 'ACV TEBUS 2500' in df.columns:
        df['ACV TEBUS 2500'] = df['ACV TEBUS 2500'].astype(str).str.replace('%', '').str.replace(',', '.')
        df['ACV TEBUS 2500'] = pd.to_numeric(df['ACV TEBUS 2500'], errors='coerce')
        
        if 'TARGET TEBUS 2500' in df.columns:
            df['TARGET TEBUS 2500'] = pd.to_numeric(df['TARGET TEBUS 2500'], errors='coerce')
        if 'ACTUAL TEBUS 2500' in df.columns:
            df['ACTUAL TEBUS 2500'] = pd.to_numeric(df['ACTUAL TEBUS 2500'], errors='coerce')
        
        # Group by kasir
        tebus_data = df.groupby('NAMA KASIR').agg({
            'TARGET TEBUS 2500': 'sum',
            'ACTUAL TEBUS 2500': 'sum',
            'ACV TEBUS 2500': 'mean'
        }).reset_index()
        
        # Hitung total
        tebus_data = tebus_data.sort_values('ACV TEBUS 2500', ascending=False)
        
        fig = go.Figure()
        
        # Tambahkan bar untuk actual vs target
        fig.add_trace(go.Bar(
            x=tebus_data['NAMA KASIR'],
            y=tebus_data['TARGET TEBUS 2500'],
            name='Target',
            marker_color=COLOR_ACCENT,
            opacity=0.7
        ))
        
        fig.add_trace(go.Bar(
            x=tebus_data['NAMA KASIR'],
            y=tebus_data['ACTUAL TEBUS 2500'],
            name='Actual',
            marker_color=COLOR_SUCCESS,
            opacity=0.7
        ))
        
        # Tambahkan line untuk ACV
        fig.add_trace(go.Scatter(
            x=tebus_data['NAMA KASIR'],
            y=tebus_data['ACV TEBUS 2500'],
            mode='markers+lines',
            name='ACV (%)',
            marker=dict(size=8, color=COLOR_PRIMARY),
            line=dict(width=2, color=COLOR_PRIMARY),
            yaxis='y2'
        ))
        
        fig.update_layout(
            title="<b>Performa Tebus Murah Rp 2.500</b>",
            xaxis_title="Nama Kasir",
            yaxis_title="Nilai",
            yaxis2=dict(
                title="ACV (%)",
                overlaying='y',
                side='right',
                range=[0, 120]
            ),
            title_x=0.5,
            legend=dict(
                orientation="h",
                yanchor="bottom",
                y=1.02,
                xanchor="right",
                x=1
            )
        )
        
        return fig
    
    # Fallback jika kolom tidak ada
    fig = go.Figure()
    fig.add_annotation(
        text="Kolom Tebus Murah tidak ditemukan",
        xref="paper", yref="paper",
        x=0.5, y=0.5,
        showarrow=False,
        font=dict(color="#CBD5F5", size=16)
    )
    fig.update_layout(title="<b>Performa Tebus Murah</b>", title_x=0.5)
    return fig


def create_trend_chart(df: pd.DataFrame) -> go.Figure:
    # Konversi kolom tanggal
    if 'TANGGAL' in df.columns:
        df['TANGGAL'] = pd.to_datetime(df['TANGGAL'], errors='coerce', dayfirst=True)
        
        # Konversi kolom score
        if 'TOTAL SCORE PPSA' in df.columns:
            df['TOTAL SCORE PPSA'] = pd.to_numeric(df['TOTAL SCORE PPSA'], errors='coerce')
        
        # Group by tanggal
        trend_data = df.groupby(df['TANGGAL'].dt.date)['TOTAL SCORE PPSA'].mean().reset_index()
        
        # Tambahkan moving average
        trend_data['MA_7'] = trend_data['TOTAL SCORE PPSA'].rolling(7, min_periods=1).mean()
        
        fig = go.Figure()
        
        fig.add_trace(go.Scatter(
            x=trend_data['TANGGAL'],
            y=trend_data['TOTAL SCORE PPSA'],
            mode='lines+markers',
            name='Rata-rata Score Harian',
            line=dict(color=COLOR_PRIMARY, width=3),
            marker=dict(size=6)
        ))
        
        fig.add_trace(go.Scatter(
            x=trend_data['TANGGAL'],
            y=trend_data['MA_7'],
            mode='lines',
            name='Moving Average (7 Hari)',
            line=dict(color=COLOR_ACCENT, width=3, dash="dot")
        ))
        
        fig.update_layout(
            title="<b>Tren Performa PPSA</b>",
            xaxis_title="Tanggal",
            yaxis_title="Rata-rata Score",
            title_x=0.5
        )
        
        return fig
    
    # Fallback jika kolom tidak ada
    fig = go.Figure()
    fig.add_annotation(
        text="Kolom TANGGAL atau TOTAL SCORE PPSA tidak ditemukan",
        xref="paper", yref="paper",
        x=0.5, y=0.5,
        showarrow=False,
        font=dict(color="#CBD5F5", size=16)
    )
    fig.update_layout(title="<b>Tren Performa</b>", title_x=0.5)
    return fig


def create_shift_comparison_chart(df: pd.DataFrame) -> go.Figure:
    if 'SHIFT' in df.columns and 'TOTAL SCORE PPSA' in df.columns:
        df['TOTAL SCORE PPSA'] = pd.to_numeric(df['TOTAL SCORE PPSA'], errors='coerce')
        
        shift_data = df.groupby('SHIFT')['TOTAL SCORE PPSA'].mean().reset_index()
        
        fig = px.bar(
            shift_data,
            x='SHIFT',
            y='TOTAL SCORE PPSA',
            color='TOTAL SCORE PPSA',
            color_continuous_scale=[COLOR_NEGATIVE, COLOR_WARNING, COLOR_SUCCESS],
            labels={'TOTAL SCORE PPSA': 'Rata-rata Score', 'SHIFT': 'Shift'},
            title="<b>Perbandingan Performa per Shift</b>",
            height=400
        )
        
        fig.update_layout(title_x=0.5, coloraxis_showscale=False)
        return fig
    
    # Fallback jika kolom tidak ada
    fig = go.Figure()
    fig.add_annotation(
        text="Kolom SHIFT atau TOTAL SCORE PPSA tidak ditemukan",
        xref="paper", yref="paper",
        x=0.5, y=0.5,
        showarrow=False,
        font=dict(color="#CBD5F5", size=16)
    )
    fig.update_layout(title="<b>Perbandingan Shift</b>", title_x=0.5)
    return fig


# =========================================================
# ------------------- FUNGSI GEMINI AI --------------------
# =========================================================
def configure_gemini():
    try:
        api_key = st.secrets["gemini"]["api_key"]
        genai.configure(api_key=api_key)
        model = genai.GenerativeModel('gemini-2.0-flash')
        return model
    except Exception as e:
        st.error(f"Gagal mengkonfigurasi Gemini API: {e}")
        return None


def generate_ai_insights(df: pd.DataFrame, model) -> str:
    if df.empty or model is None:
        return "Tidak ada data atau model tidak tersedia."
    
    # Siapkan ringkasan data
    total_records = len(df)
    if 'TANGGAL' in df.columns:
        df['TANGGAL'] = pd.to_datetime(df['TANGGAL'], errors='coerce', dayfirst=True)
        date_range = f"{df['TANGGAL'].min().date()} hingga {df['TANGGAL'].max().date()}"
    else:
        date_range = "Tidak tersedia"
    
    # Hitung metrik PPSA
    ppsa_metrics = {}
    indicators = ['PSM', 'PWP', 'SG', 'APC']
    
    for indicator in indicators:
        acv_col = f'{indicator} ACV'
        if acv_col in df.columns:
            df[acv_col] = df[acv_col].astype(str).str.replace('%', '').str.replace(',', '.')
            df[acv_col] = pd.to_numeric(df[acv_col], errors='coerce')
            ppsa_metrics[indicator] = df[acv_col].mean()
    
    # Hitung metrik Tebus Murah
    tebus_metrics = {}
    if 'ACV TEBUS 2500' in df.columns:
        df['ACV TEBUS 2500'] = df['ACV TEBUS 2500'].astype(str).str.replace('%', '').str.replace(',', '.')
        df['ACV TEBUS 2500'] = pd.to_numeric(df['ACV TEBUS 2500'], errors='coerce')
        tebus_metrics['acv'] = df['ACV TEBUS 2500'].mean()
    
    # Buat prompt untuk Gemini
    prompt = f"""
    Analisis data performa kasir berikut dan berikan insight yang berharga:
    
    Ringkasan Data:
    - Total Records: {total_records}
    - Periode Data: {date_range}
    
    Metrik PPSA (Rata-rata ACV):
    - PSM: {ppsa_metrics.get('PSM', 'N/A')}%
    - PWP: {ppsa_metrics.get('PWP', 'N/A')}%
    - SG: {ppsa_metrics.get('SG', 'N/A')}%
    - APC: {ppsa_metrics.get('APC', 'N/A')}%
    
    Metrik Tebus Murah:
    - ACV Rata-rata: {tebus_metrics.get('acv', 'N/A')}%
    
    Berikan analisis mendalam tentang:
    1. Performa keseluruhan PPSA dan Tebus Murah
    2. Indikator dengan performa terbaik dan terburuk
    3. Area yang perlu mendapat perhatian khusus
    4. Rekomendasi tindakan untuk meningkatkan performa
    5. Strategi untuk mengoptimalkan penjualan
    
    Jawab dalam bahasa Indonesia dengan gaya profesional namun mudah dipahami.
    """
    
    try:
        response = model.generate_content(prompt)
        return response.text
    except Exception as e:
        return f"Terjadi kesalahan saat menghasilkan insight: {e}"


# =========================================================
# ------------------- FUNGSI PERHITUNGAN SCORE PPSA --------------------
# =========================================================
def calculate_ppsa_score(df: pd.DataFrame) -> pd.DataFrame:
    """
    Menghitung PPSA score dengan bobot yang benar sesuai script asli:
    - PSM bobot 20%
    - PWP bobot 25%
    - SG bobot 30%
    - APC bobot 25%
    """
    # Buat copy dataframe untuk menghindari SettingWithCopyWarning
    df_calc = df.copy()
    
    # Konversi kolom ACV ke numerik
    indicators = ['PSM', 'PWP', 'SG', 'APC']
    
    for indicator in indicators:
        acv_col = f'{indicator} ACV'
        if acv_col in df_calc.columns:
            # Konversi nilai ACV ke numerik
            df_calc[acv_col] = df_calc[acv_col].astype(str).str.replace('%', '').str.replace(',', '.')
            df_calc[acv_col] = pd.to_numeric(df_calc[acv_col], errors='coerce')
            
            # Hitung score per indikator dengan bobot yang sesuai
            if indicator == 'PSM':
                df_calc[f'{indicator} SCORE'] = (df_calc[acv_col] * 20) / 100
            elif indicator == 'PWP':
                df_calc[f'{indicator} SCORE'] = (df_calc[acv_col] * 25) / 100
            elif indicator == 'SG':
                df_calc[f'{indicator} SCORE'] = (df_calc[acv_col] * 30) / 100
            elif indicator == 'APC':
                df_calc[f'{indicator} SCORE'] = (df_calc[acv_col] * 25) / 100
    
    # Hitung total score PPSA
    score_cols = [f'{indicator} SCORE' for indicator in indicators if f'{indicator} SCORE' in df_calc.columns]
    if score_cols:
        df_calc['TOTAL SCORE PPSA'] = df_calc[score_cols].sum(axis=1)
    
    return df_calc


# =========================================================
# ----------------------- SIDEBAR -------------------------
# =========================================================
with st.sidebar:
    st.header("🎛️ Kontrol Dashboard")
    st.caption("Atur parameter analitik secara real-time untuk melihat performa kasir.")
    
    st.divider()
    
    try:
        spreadsheet_url = st.secrets["spreadsheet"]["url"]
        st.success("✅ Terhubung ke Google Sheets via Secrets")
    except (KeyError, FileNotFoundError):
        spreadsheet_url = st.text_input(
            "URL Google Spreadsheet",
            placeholder="https://docs.google.com/spreadsheets/d/...",
            help="Masukkan URL jika tidak menggunakan st.secrets."
        )
        st.caption("Tip: Simpan kredensial pada `st.secrets` untuk koneksi otomatis.")
    
    sheet_name = st.text_input(
        "Nama Worksheet",
        value="Data",
        help="Pastikan nama worksheet sesuai dengan di Google Sheets."
    )
    
    st.markdown("---")
    
    st.subheader("🧮 Filter")
    
    # Filter akan ditambahkan setelah data dimuat
    st.info("Filter akan tersedia setelah data dimuat")
    
    st.markdown("---")
    
    if st.button("🔄 Refresh Data", use_container_width=True):
        st.experimental_rerun()

# =========================================================
# ---------------------- MAIN APP -------------------------
# =========================================================
st.markdown(
    """
    <div class="hero-card">
        <h1>📊 Dashboard PPSA & Tebus Murah</h1>
        <p>Menghadirkan visual interaktif dan insight instan untuk memantau performa kasir secara komprehensif.
        <br/><strong>📍 Toko:</strong> 2GC6 BAROS PANDEGLANG</p>
    </div>
    """,
    unsafe_allow_html=True
)

if not spreadsheet_url.strip():
    st.warning("Masukkan URL Google Spreadsheet terlebih dahulu untuk memulai.")
    st.stop()

with st.spinner("Memuat dan memproses data dari Google Sheets..."):
    dataframe = load_data(spreadsheet_url, sheet_name)

if dataframe is None or dataframe.empty:
    st.error("Tidak ada data yang dapat diproses. Periksa kembali sumber data Anda.")
    st.stop()

# Initialize Gemini model
gemini_model = configure_gemini()

# Hitung PPSA score dengan bobot yang benar
dataframe_with_scores = calculate_ppsa_score(dataframe)

# Tambahkan filter setelah data dimuat
with st.sidebar:
    st.subheader("🧮 Filter")
    
    # Filter berdasarkan rentang tanggal
    if 'TANGGAL' in dataframe.columns:
        dataframe['TANGGAL'] = pd.to_datetime(dataframe['TANGGAL'], errors='coerce', dayfirst=True)
        min_date = dataframe["TANGGAL"].min().to_pydatetime()
        max_date = dataframe["TANGGAL"].max().to_pydatetime()
        
        selected_date_range = st.date_input(
            "Rentang Tanggal",
            value=(min_date, max_date),
            min_value=min_date,
            max_value=max_date
        )
    else:
        selected_date_range = None
        st.warning("Kolom TANGGAL tidak ditemukan dalam data")
    
    # Filter berdasarkan kasir
    if 'NAMA KASIR' in dataframe.columns:
        available_cashiers = sorted(dataframe["NAMA KASIR"].unique().tolist())
        available_cashiers = ["Semua"] + available_cashiers
        selected_cashiers = st.multiselect(
            "Filter Kasir",
            options=available_cashiers,
            default=["Semua"]
        )
    else:
        selected_cashiers = ["Semua"]
        st.warning("Kolom NAMA KASIR tidak ditemukan dalam data")
    
    # Filter berdasarkan shift
    if 'SHIFT' in dataframe.columns:
        available_shifts = sorted(dataframe["SHIFT"].unique().tolist())
        available_shifts = ["Semua"] + available_shifts
        selected_shifts = st.multiselect(
            "Filter Shift",
            options=available_shifts,
            default=["Semua"]
        )
    else:
        selected_shifts = ["Semua"]
        st.warning("Kolom SHIFT tidak ditemukan dalam data")

# Filter data
filtered_df = filter_dataframe(
    dataframe_with_scores,
    date_range=selected_date_range,
    selected_cashiers=selected_cashiers,
    selected_shifts=selected_shifts
)

if filtered_df.empty:
    st.warning("Filter saat ini tidak menghasilkan data. Sesuaikan parameter filter.")
    st.stop()

# =========================================================
# --------------------- RINGKASAN KPI ---------------------
# =========================================================
st.subheader("🔑 Ringkasan Eksekutif")

# Hitung metrik PPSA dengan score yang benar
total_score = 0
avg_score = 0
if 'TOTAL SCORE PPSA' in filtered_df.columns:
    filtered_df['TOTAL SCORE PPSA'] = pd.to_numeric(filtered_df['TOTAL SCORE PPSA'], errors='coerce')
    total_score = filtered_df['TOTAL SCORE PPSA'].sum()
    avg_score = filtered_df['TOTAL SCORE PPSA'].mean()

# Hitung metrik Tebus Murah
total_target_tebus = 0
total_actual_tebus = 0
avg_acv_tebus = 0
if 'TARGET TEBUS 2500' in filtered_df.columns and 'ACTUAL TEBUS 2500' in filtered_df.columns:
    filtered_df['TARGET TEBUS 2500'] = pd.to_numeric(filtered_df['TARGET TEBUS 2500'], errors='coerce')
    filtered_df['ACTUAL TEBUS 2500'] = pd.to_numeric(filtered_df['ACTUAL TEBUS 2500'], errors='coerce')
    total_target_tebus = filtered_df['TARGET TEBUS 2500'].sum()
    total_actual_tebus = filtered_df['ACTUAL TEBUS 2500'].sum()
    
    if 'ACV TEBUS 2500' in filtered_df.columns:
        filtered_df['ACV TEBUS 2500'] = filtered_df['ACV TEBUS 2500'].astype(str).str.replace('%', '').str.replace(',', '.')
        filtered_df['ACV TEBUS 2500'] = pd.to_numeric(filtered_df['ACV TEBUS 2500'], errors='coerce')
        avg_acv_tebus = filtered_df['ACV TEBUS 2500'].mean()

# Hitung jumlah kasir dan shift
total_cashiers = filtered_df['NAMA KASIR'].nunique() if 'NAMA KASIR' in filtered_df.columns else 0
total_shifts = filtered_df['SHIFT'].nunique() if 'SHIFT' in filtered_df.columns else 0

metric_container = st.container()
with metric_container:
    st.markdown('<div class="metric-grid">', unsafe_allow_html=True)
    render_metric_card(
        "Total Score PPSA",
        f"{total_score:.2f}",
        icon="📊"
    )
    render_metric_card(
        "Rata-rata Score PPSA",
        f"{avg_score:.2f}",
        icon="📈"
    )
    render_metric_card(
        "Total Target Tebus",
        format_quantity(total_target_tebus),
        icon="🎯"
    )
    render_metric_card(
        "Total Actual Tebus",
        format_quantity(total_actual_tebus),
        icon="✅"
    )
    st.markdown('</div>', unsafe_allow_html=True)

st.divider()

# =========================================================
# -------------------- VISUALISASI ------------------------
# =========================================================
tabs = st.tabs([
    "📊 Analisis PPSA",
    "💰 Analisis Tebus Murah",
    "📈 Tren Performa",
    "🤖 Analisis AI"
])

with tabs[0]:
    st.subheader("📊 Analisis PPSA")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown('<div class="chart-container">', unsafe_allow_html=True)
        st.plotly_chart(create_ppsa_radar_chart(filtered_df), use_container_width=True)
        st.markdown('</div>', unsafe_allow_html=True)
    
    with col2:
        st.markdown('<div class="chart-container">', unsafe_allow_html=True)
        st.plotly_chart(create_shift_comparison_chart(filtered_df), use_container_width=True)
        st.markdown('</div>', unsafe_allow_html=True)
    
    st.markdown('<div class="chart-container">', unsafe_allow_html=True)
    st.plotly_chart(create_cashier_performance_chart(filtered_df), use_container_width=True)
        st.markdown('</div>', unsafe_allow_html=True)
    
    # Tambahkan detail perhitungan score
    with st.expander("📋 Detail Perhitungan Score PPSA", expanded=False):
        st.markdown("""
        ### 📋 Formula Perhitungan Score PPSA
        
        **Bobot Indikator:**
        - PSM: 20%
        - PWP: 25%
        - SG: 30%
        - APC: 25%
        
        **Formula:**
        - Score PSM = (%ACV PSM × 20) ÷ 100
        - Score PWP = (%ACV PWP × 25) ÷ 100
        - Score SG = (%ACV SG × 30) ÷ 100
        - Score APC = (%ACV APC × 25) ÷ 100
        - Total Score = Score PSM + Score PWP + Score SG + Score APC
        """)
        
        # Tampilkan detail score per indikator
        indicators = ['PSM', 'PWP', 'SG', 'APC']
        score_data = []
        
        for indicator in indicators:
            acv_col = f'{indicator} ACV'
            score_col = f'{indicator} SCORE'
            
            if acv_col in filtered_df.columns and score_col in filtered_df.columns:
                avg_acv = filtered_df[acv_col].mean()
                avg_score = filtered_df[score_col].mean()
                
                score_data.append({
                    'Indikator': indicator,
                    'Rata-rata ACV (%)': f"{avg_acv:.2f}",
                    'Rata-rata Score': f"{avg_score:.2f}",
                    'Bobot (%)': f"{20 if indicator == 'PSM' else 25 if indicator == 'PWP' else 30 if indicator == 'SG' else 25}%"
                })
        
        if score_data:
            score_detail_df = pd.DataFrame(score_data)
            st.dataframe(score_detail_df, use_container_width=True, hide_index=True)

with tabs[1]:
    st.subheader("💰 Analisis Tebus Murah")
    
    st.markdown('<div class="chart-container">', unsafe_allow_html=True)
    st.plotly_chart(create_tebus_murah_chart(filtered_df), use_container_width=True)
    st.markdown('</div>', unsafe_allow_html=True)
    
    # Tambahkan tabel detail performa tebus murah
    if 'TARGET TEBUS 2500' in filtered_df.columns and 'ACTUAL TEBUS 2500' in filtered_df.columns:
        tebus_detail = filtered_df.groupby('NAMA KASIR').agg({
            'TARGET TEBUS 2500': 'sum',
            'ACTUAL TEBUS 2500': 'sum'
        }).reset_index()
        
        # Hitung ACV
        tebus_detail['ACV'] = (tebus_detail['ACTUAL TEBUS 2500'] / tebus_detail['TARGET TEBUS 2500'] * 100).round(2)
        tebus_detail = tebus_detail.sort_values('ACV', ascending=False)
        
        st.subheader("Detail Performa Tebus Murah per Kasir")
        st.dataframe(tebus_detail, use_container_width=True)

with tabs[2]:
    st.subheader("📈 Tren Performa")
    
    st.markdown('<div class="chart-container">', unsafe_allow_html=True)
    st.plotly_chart(create_trend_chart(filtered_df), use_container_width=True)
    st.markdown('</div>', unsafe_allow_html=True)

with tabs[3]:
    st.subheader("🤖 Analisis AI dengan Gemini")
    
    if gemini_model is None:
        st.error("Model Gemini tidak tersedia. Pastikan API key sudah dikonfigurasi dengan benar.")
    else:
        # AI Insights Section
        st.markdown("### 🧠 Insight Cerdas dari Data")
        
        if st.button("🔍 Generate Insight", type="primary"):
            with st.spinner("Menganalisis data dengan AI..."):
                insights = generate_ai_insights(filtered_df, gemini_model)
                
                st.markdown('<div class="ai-response">', unsafe_allow_html=True)
                st.markdown(insights)
                st.markdown('</div>', unsafe_allow_html=True)

st.divider()

# =========================================================
# ------------------- TABEL DETAIL ------------------------
# =========================================================
with st.expander("📄 Lihat Data Detail", expanded=False):
    df_display = filtered_df.copy()
    
    # Format kolom tanggal
    if 'TANGGAL' in df_display.columns:
        df_display['TANGGAL'] = df_display['TANGGAL'].dt.strftime("%Y-%m-%d")
    
    # Format kolom numerik
    numeric_cols = ['TARGET TEBUS 2500', 'ACTUAL TEBUS 2500', 'TOTAL SCORE PPSA']
    for col in numeric_cols:
        if col in df_display.columns:
            df_display[col] = pd.to_numeric(df_display[col], errors='coerce')
    
    st.dataframe(df_display, use_container_width=True, hide_index=True)

st.caption("© 2025 – Dashboard PPSA & Tebus Murah • Dibangun dengan Streamlit + Plotly • Desain futuristic-glassmorphism")
