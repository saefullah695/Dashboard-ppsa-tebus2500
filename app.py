import streamlit as st
import pandas as pd
import gspread
from google.oauth2.service_account import Credentials
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime

# --- KONFIGURASI HALAMAN ---
st.set_page_config(
    page_title="Dashboard PPSA Analytics",
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
        "trophy": f'<svg width="{size}" height="{size}" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg"><path d="M19 5h-2V3H7v2H5c-1.1 0-2 .9-2 2v1c0 2.55 1.92 4.63 4.39 4.94A5.01 5.01 0 0 0 11 15.9V19H7v2h10v-2h-4v-3.1a5.01 5.01 0 0 0 3.61-2.96C19.08 12.63 21 10.55 21 8V7c0-1.1-.9-2-2-2zM5 8V7h2v3.82C5.84 10.4 5 9.3 5 8zm14 0c0 1.3-.84 2.4-2 2.82V7h2v1z" fill="{color}"/></svg>'
    }
    return icons.get(icon_name, "")

# --- CSS KUSTOM UNTUK TAMPILAN MODERN ---
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap');
* { font-family: 'Inter', sans-serif; }
.stApp { background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); background-attachment: fixed; }
.main .block-container { padding-top: 2rem; padding-bottom: 2rem; max-width: 1400px; }
.dashboard-header { background: linear-gradient(135deg, #ffffff 0%, #f8f9ff 100%); padding: 2.5rem; border-radius: 20px; box-shadow: 0 10px 40px rgba(0, 0, 0, 0.1); margin-bottom: 2rem; border: 1px solid rgba(255, 255, 255, 0.3); text-align: center; }
.main-title { font-size: 3rem; background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); -webkit-background-clip: text; -webkit-text-fill-color: transparent; background-clip: text; font-weight: 800; margin-bottom: 0.5rem; letter-spacing: -0.5px; display: flex; align-items: center; justify-content: center; gap: 1rem; }
.subtitle { text-align: center; color: #64748b; font-size: 1.1rem; font-weight: 400; line-height: 1.6; max-width: 800px; margin: 0 auto; }
.metric-card { background: linear-gradient(135deg, #ffffff 0%, #f8f9ff 100%); border-radius: 16px; padding: 1.5rem; box-shadow: 0 4px 20px rgba(0, 0, 0, 0.08); border: 1px solid rgba(102, 126, 234, 0.1); transition: all 0.3s ease; position: relative; overflow: hidden; height: 100%; }
.metric-card::before { content: ''; position: absolute; top: 0; left: 0; width: 4px; height: 100%; background: linear-gradient(180deg, #667eea 0%, #764ba2 100%); }
.metric-card:hover { transform: translateY(-8px); box-shadow: 0 12px 40px rgba(102, 126, 234, 0.25); }
.metric-label { font-size: 0.875rem; color: #64748b; font-weight: 600; text-transform: uppercase; letter-spacing: 0.5px; margin-bottom: 0.5rem; display: flex; align-items: center; gap: 0.5rem; }
.metric-value { font-size: 2.5rem; font-weight: 700; background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); -webkit-background-clip: text; -webkit-text-fill-color: transparent; background-clip: text; line-height: 1.2; }
.total-ppsa-card { background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); border-radius: 20px; padding: 3rem 2rem; box-shadow: 0 20px 60px rgba(102, 126, 234, 0.4); text-align: center; position: relative; overflow: hidden; }
.total-ppsa-card::before { content: ''; position: absolute; top: -50%; right: -50%; width: 200%; height: 200%; background: radial-gradient(circle, rgba(255,255,255,0.1) 0%, transparent 70%); animation: pulse 3s ease-in-out infinite; }
@keyframes pulse { 0%, 100% { transform: scale(1); opacity: 0.5; } 50% { transform: scale(1.1); opacity: 0.8; } }
.total-ppsa-label { font-size: 1rem; color: rgba(255, 255, 255, 0.9); font-weight: 600; text-transform: uppercase; letter-spacing: 2px; margin-bottom: 1rem; }
.total-ppsa-value { font-size: 4rem; font-weight: 800; color: #ffffff; text-shadow: 0 4px 20px rgba(0, 0, 0, 0.2); position: relative; z-index: 1; }
.content-container { background: linear-gradient(135deg, #ffffff 0%, #f8f9ff 100%); padding: 2rem; border-radius: 20px; box-shadow: 0 8px 32px rgba(0, 0, 0, 0.08); margin-bottom: 2rem; border: 1px solid rgba(255, 255, 255, 0.3); }
.section-header { font-size: 1.75rem; font-weight: 700; color: #1e293b; margin-bottom: 1.5rem; padding-bottom: 0.75rem; border-bottom: 3px solid #667eea; position: relative; }
.section-header::before { content: ''; position: absolute; bottom: -3px; left: 0; width: 60px; height: 3px; background: #764ba2; }
.css-1d391kg, [data-testid="stSidebar"] { background: linear-gradient(180deg, #ffffff 0%, #f8f9ff 100%); border-right: 1px solid rgba(102, 126, 234, 0.1); }
[data-testid="stSidebar"] .element-container { padding: 0.5rem 0; }
.stButton > button { background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); color: white; border: none; border-radius: 12px; padding: 0.75rem 2rem; font-weight: 600; transition: all 0.3s ease; box-shadow: 0 4px 15px rgba(102, 126, 234, 0.3); }
.stButton > button:hover { transform: translateY(-2px); box-shadow: 0 6px 20px rgba(102, 126, 234, 0.4); }
.stDataFrame { border-radius: 16px; overflow: hidden; box-shadow: 0 4px 20px rgba(0, 0, 0, 0.06); border: 1px solid rgba(102, 126, 234, 0.1); }
.js-plotly-plot { border-radius: 12px; overflow: hidden; }
::-webkit-scrollbar { width: 8px; height: 8px; }
::-webkit-scrollbar-track { background: #f1f5f9; border-radius: 10px; }
::-webkit-scrollbar-thumb { background: linear-gradient(180deg, #667eea 0%, #764ba2 100%); border-radius: 10px; }
::-webkit-scrollbar-thumb:hover { background: linear-gradient(180deg, #764ba2 0%, #667eea 100%); }
@keyframes fadeIn { from { opacity: 0; transform: translateY(20px); } to { opacity: 1; transform: translateY(0); } }
.content-container { animation: fadeIn 0.6s ease-out; }
#MainMenu, footer, header { visibility: hidden; }
</style>
""", unsafe_allow_html=True)

# --- FUNGSI DATA ---
@st.cache_data(ttl=600)
def load_data_from_gsheet():
    try:
        scopes = ['https://www.googleapis.com/auth/spreadsheets', 'https://www.googleapis.com/auth/drive']
        creds = Credentials.from_service_account_info(st.secrets["gcp_service_account"], scopes=scopes)
        client = gspread.authorize(creds)
        spreadsheet = client.open("Dashboard")
        worksheet = spreadsheet.get_worksheet(0)
        data = worksheet.get_all_values()
        if not data: return pd.DataFrame()
        df = pd.DataFrame(data[1:], columns=data[0])
        return df
    except Exception as e:
        st.error(f"❌ Gagal mengambil data: {e}")
        return pd.DataFrame()

def process_data(df):
    if df.empty: return df
    if 'TANGGAL' in df.columns:
        df['TANGGAL'] = pd.to_datetime(df['TANGGAL'], format='%d/%m/%Y', errors='coerce')
        df['HARI'] = df['TANGGAL'].dt.day_name()
        hari_map = {'Monday': 'Senin', 'Tuesday': 'Selasa', 'Wednesday': 'Rabu', 'Thursday': 'Kamis', 'Friday': 'Jumat', 'Saturday': 'Sabtu', 'Sunday': 'Minggu'}
        df['HARI'] = df['HARI'].map(hari_map)

    numeric_cols = ['PSM Target', 'PSM Actual', 'BOBOT PSM', 'PWP Target', 'PWP Actual', 'BOBOT PWP', 'SG Target', 'SG Actual', 'BOBOT SG', 'APC Target', 'APC Actual', 'BOBOT APC', 'TARGET TEBUS 2500', 'ACTUAL TEBUS 2500']
    for col in numeric_cols:
        if col in df.columns: df[col] = pd.to_numeric(df[col], errors='coerce').fillna(0)

    def calculate_acv(actual, target):
        if target == 0: return 0.0
        return (actual / target) * 100

    df['(%) PSM ACV'] = df.apply(lambda row: calculate_acv(row['PSM Actual'], row['PSM Target']), axis=1)
    df['(%) PWP ACV'] = df.apply(lambda row: calculate_acv(row['PWP Actual'], row['PWP Target']), axis=1)
    df['(%) SG ACV'] = df.apply(lambda row: calculate_acv(row['SG Actual'], row['SG Target']), axis=1)
    df['(%) APC ACV'] = df.apply(lambda row: calculate_acv(row['APC Actual'], row['APC Target']), axis=1)
    df['(%) ACV TEBUS 2500'] = df.apply(lambda row: calculate_acv(row['ACTUAL TEBUS 2500'], row['TARGET TEBUS 2500']), axis=1)

    df['SCORE PSM'] = (df['(%) PSM ACV'] * df['BOBOT PSM']) / 100
    df['SCORE PWP'] = (df['(%) PWP ACV'] * df['BOBOT PWP']) / 100
    df['SCORE SG'] = (df['(%) SG ACV'] * df['BOBOT SG']) / 100
    df['SCORE APC'] = (df['(%) APC ACV'] * df['BOBOT APC']) / 100
    
    score_cols = ['SCORE PSM', 'SCORE PWP', 'SCORE SG', 'SCORE APC']
    df['TOTAL SCORE PPSA'] = df[score_cols].sum(axis=1)
    return df

def calculate_overall_ppsa_breakdown(df):
    if df.empty: return {'total': 0.0, 'psm': 0.0, 'pwp': 0.0, 'sg': 0.0, 'apc': 0.0}
    weights = {'PSM': 20, 'PWP': 25, 'SG': 30, 'APC': 25}
    scores = {'psm': 0.0, 'pwp': 0.0, 'sg': 0.0, 'apc': 0.0}
    sum_components = ['PSM', 'PWP', 'SG']
    for comp in sum_components:
        total_target = df[f'{comp} Target'].sum()
        total_actual = df[f'{comp} Actual'].sum()
        if total_target > 0:
            acv = (total_actual / total_target) * 100
            scores[comp.lower()] = (acv * weights[comp]) / 100
    avg_target_apc = df['APC Target'].mean()
    avg_actual_apc = df['APC Actual'].mean()
    if avg_target_apc > 0:
        acv_apc = (avg_actual_apc / avg_target_apc) * 100
        scores['apc'] = (acv_apc * weights['APC']) / 100
    scores['total'] = sum(scores.values())
    return scores

# --- PERBAIKAN: INDENTASI FUNGSI AGREGASI ---
def calculate_aggregate_scores_per_cashier(df):
    if df.empty or 'NAMA KASIR' not in df.columns:
        return pd.DataFrame()
    
    weights = {'PSM': 20, 'PWP': 25, 'SG': 30, 'APC': 25}
    agg_cols = {
        'PSM Target': 'sum', 'PSM Actual': 'sum', 'PWP Target': 'sum', 'PWP Actual': 'sum',
        'SG Target': 'sum', 'SG Actual': 'sum', 'APC Target': 'mean', 'APC Actual': 'mean'
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
        aggregated_df[f'SCORE {comp}'] = aggregated_df.apply(lambda row: calculate_score_from_agg(row, comp), axis=1)
    
    score_cols = [f'SCORE {comp}' for comp in ['PSM', 'PWP', 'SG', 'APC']]
    aggregated_df['TOTAL SCORE PPSA'] = aggregated_df[score_cols].sum(axis=1)
    
    return aggregated_df.sort_values(by='TOTAL SCORE PPSA', ascending=False).reset_index(drop=True)

# --- PERBAIKAN: INDENTASI FUNGSI AGREGASI SHIFT ---
def calculate_aggregate_scores_per_shift(df):
    if df.empty or 'SHIFT' not in df.columns:
        return pd.DataFrame()
    
    weights = {'PSM': 20, 'PWP': 25, 'SG': 30, 'APC': 25}
    agg_cols = {
        'PSM Target': 'sum', 'PSM Actual': 'sum', 'PWP Target': 'sum', 'PWP Actual': 'sum',
        'SG Target': 'sum', 'SG Actual': 'sum', 'APC Target': 'mean', 'APC Actual': 'mean'
    }
    
    valid_agg_cols = {col: func for col, func in agg_cols.items() if col in df.columns}
    aggregated_df = df.groupby('SHIFT')[list(valid_agg_cols.keys())].agg(valid_agg_cols).reset_index()

    def calculate_score_from_agg(row, comp):
        total_target = row[f'{comp} Target']
        total_actual = row[f'{comp} Actual']
        if total_target == 0:
            return 0.0
        acv = (total_actual / total_target) * 100
        return (acv * weights[comp]) / 100

    for comp in ['PSM', 'PWP', 'SG', 'APC']:
        aggregated_df[f'SCORE {comp}'] = aggregated_df.apply(lambda row: calculate_score_from_agg(row, comp), axis=1)
    
    score_cols = [f'SCORE {comp}' for comp in ['PSM', 'PWP', 'SG', 'APC']]
    aggregated_df['TOTAL SCORE PPSA'] = aggregated_df[score_cols].sum(axis=1)
    
    return aggregated_df.sort_values(by='TOTAL SCORE PPSA', ascending=False).reset_index(drop=True)

def calculate_tebus_summary_per_cashier(df):
    if df.empty or 'NAMA KASIR' not in df.columns:
        return pd.DataFrame()
    
    agg_cols = {
        'TARGET TEBUS 2500': 'sum',
        'ACTUAL TEBUS 2500': 'sum'
    }
    
    valid_agg_cols = {col: func for col, func in agg_cols.items() if col in df.columns}
    aggregated_df = df.groupby('NAMA KASIR')[list(valid_agg_cols.keys())].agg(valid_agg_cols).reset_index()

    def calculate_acv_tebus(row):
        if row['TARGET TEBUS 2500'] == 0:
            return 0.0
        return (row['ACTUAL TEBUS 2500'] / row['TARGET TEBUS 2500']) * 100
        
    aggregated_df['(%) ACV TEBUS 2500'] = aggregated_df.apply(calculate_acv_tebus, axis=1)
    
    return aggregated_df.sort_values(by='(%) ACV TEBUS 2500', ascending=False).reset_index(drop=True)

def calculate_gap_analysis(df):
    if df.empty: return pd.DataFrame()
    
    overall_acv = {}
    components = ['PSM', 'PWP', 'SG', 'APC']
    for comp in components:
        target_col = f'{comp} Target'
        actual_col = f'{comp} Actual'
        total_target = df[target_col].sum()
        total_actual = df[actual_col].sum()
        if total_target > 0:
            acv = (total_actual / total_target) * 100
        else:
            acv = 0.0
        overall_acv[comp] = acv

    gap_df = pd.DataFrame(list(overall_acv.items()), columns=['Komponen', 'ACV'])
    gap_df['Target'] = 100.0
    gap_df['Gap'] = gap_df['ACV'] - gap_df['Target']
    gap_df['Warna'] = gap_df['Gap'].apply(lambda x: '#10b981' if x >= 0 else '#ef4444')
    
    return gap_df

def calculate_gap_per_cashier(df):
    if df.empty or 'NAMA KASIR' not in df.columns:
        return pd.DataFrame()
    
    # Gunakan fungsi yang sudah ada untuk menghitung skor
    score_summary = calculate_aggregate_scores_per_cashier(df)
    
    if score_summary.empty:
        return pd.DataFrame()
        
    score_summary['Gap Skor'] = score_summary['TOTAL SCORE PPSA'] - 100.0
    score_summary['Warna'] = score_summary['Gap Skor'].apply(lambda x: '#10b981' if x >= 0 else '#ef4444')
    
    return score_summary.sort_values(by='Gap Skor', ascending=False).reset_index(drop=True)


# --- UI DASHBOARD ---
st.markdown(f"""
<div class="dashboard-header">
    <h1 class="main-title">{get_svg_icon("dashboard", size=48, color="#667eea")} Dashboard PPSA Analytics</h1>
    <p class="subtitle">Platform pemantauan performa komprehensif untuk indikator <strong>PPSA</strong> (PSM, PWP, SG, APC) dan <strong>Tebus (Suuegerr)</strong>.</p>
</div>
""", unsafe_allow_html=True)

raw_df = load_data_from_gsheet()

if not raw_df.empty:
    processed_df = process_data(raw_df.copy())
    
    with st.sidebar:
        st.markdown("### ⚙️ Pengaturan Filter")
        if 'NAMA KASIR' in processed_df.columns:
            selected_names = st.multiselect("Pilih Kasir:", options=sorted(processed_df['NAMA KASIR'].unique()), default=processed_df['NAMA KASIR'].unique())
            filtered_df = processed_df[processed_df['NAMA KASIR'].isin(selected_names)]
        else:
            filtered_df = processed_df
        if 'TANGGAL' in filtered_df.columns:
            filtered_df = filtered_df.dropna(subset=['TANGGAL'])
            if not filtered_df.empty:
                min_date = filtered_df['TANGGAL'].min().to_pydatetime()
                max_date = filtered_df['TANGGAL'].max().to_pydatetime()
                selected_date_range = st.date_input("Pilih Rentang Tanggal:", value=[min_date, max_date], min_value=min_date, max_value=max_date)
                if len(selected_date_range) == 2:
                    start_date, end_date = pd.to_datetime(selected_date_range[0]), pd.to_datetime(selected_date_range[1])
                    mask = (filtered_df['TANGGAL'] >= start_date) & (filtered_df['TANGGAL'] <= end_date)
                    filtered_df = filtered_df.loc[mask]
        st.info(f"**Total Record:** {len(filtered_df)}\n\n**Kasir Terpilih:** {len(selected_names) if 'selected_names' in locals() else 0}")

    tab1, tab2 = st.tabs(["📈 PPSA Analytics", "🛒 Tebus (Suuegerr) Analytics"])

    with tab1:
        overall_scores = calculate_overall_ppsa_breakdown(filtered_df)
        
        st.markdown('<div class="content-container">', unsafe_allow_html=True)
        st.markdown('<h2 class="section-header">🏆 Ringkasan Performa Keseluruhan</h2>', unsafe_allow_html=True)
        
        col1, col2, col3, col4 = st.columns(4, gap="small")
        metrics = [
            {"label": "PSM Score", "value": overall_scores['psm'], "icon": "psm", "col": col1},
            {"label": "PWP Score", "value": overall_scores['pwp'], "icon": "pwp", "col": col2},
            {"label": "SG Score", "value": overall_scores['sg'], "icon": "sg", "col": col3},
            {"label": "APC Score", "value": overall_scores['apc'], "icon": "apc", "col": col4}
        ]
        for metric in metrics:
            with metric["col"]:
                st.markdown(f"""
                <div class="metric-card">
                    <div class="metric-label">{get_svg_icon(metric['icon'], size=20)} {metric['label']}</div>
                    <div class="metric-value">{metric['value']:.2f}</div>
                </div>
                """, unsafe_allow_html=True)
        
        st.markdown("<br>", unsafe_allow_html=True)
        
        col_actual, col_gap, col_chart = st.columns([1, 1, 2], gap="medium")
        with col_actual:
            st.markdown(f"""
            <div class="total-ppsa-card">
                <div class="total-ppsa-label">{get_svg_icon("trophy", size=32, color="white")} TOTAL PPSA SCORE</div>
                <div class="total-ppsa-value">{overall_scores['total']:.2f}</div>
            </div>
            """, unsafe_allow_html=True)
        
        with col_gap:
            gap_value = overall_scores['total'] - 100
            gap_color = '#10b981' if gap_value >= 0 else '#ef4444'
            st.markdown(f"""
            <div class="metric-card" style="border-left-color: {gap_color}; background: linear-gradient(135deg, #ffffff 0%, #f8f9ff 100%);">
                <div class="metric-label">{get_svg_icon("tebus", size=20, color=gap_color)} GAP TO TARGET</div>
                <div class="metric-value" style="color: {gap_color};">{gap_value:+.2f}</div>
            </div>
            """, unsafe_allow_html=True)

        with col_chart:
            chart_data = pd.DataFrame({'Komponen': ['PSM', 'PWP', 'SG', 'APC'], 'Skor': [overall_scores['psm'], overall_scores['pwp'], overall_scores['sg'], overall_scores['apc']], 'Target': [20, 25, 30, 25]})
            fig_overall = go.Figure()
            fig_overall.add_trace(go.Bar(name='Score Aktual', x=chart_data['Komponen'], y=chart_data['Skor'], marker=dict(color=['#667eea', '#764ba2', '#f093fb', '#4facfe']), text=chart_data['Skor'].round(2), textposition='outside'))
            fig_overall.add_trace(go.Scatter(name='Target', x=chart_data['Komponen'], y=chart_data['Target'], mode='markers+lines', marker=dict(size=12, color='#ef4444', symbol='diamond'), line=dict(color='#ef4444', width=2, dash='dash')))
            fig_overall.update_layout(template='plotly_white', height=300, margin=dict(l=20, r=20, t=40, b=20), showlegend=True, legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1), yaxis_title='Skor')
            st.plotly_chart(fig_overall, use_container_width=True)
        st.markdown('</div>', unsafe_allow_html=True)

        st.markdown('<div class="content-container">', unsafe_allow_html=True)
        st.markdown('<h2 class="section-header">📉 Gap Analysis (Target 100%)</h2>', unsafe_allow_html=True)
        
        st.subheader("Gap Indikator Keseluruhan")
        gap_df = calculate_gap_analysis(filtered_df)
        if not gap_df.empty:
            fig_gap_overall = go.Figure()
            fig_gap_overall.add_trace(go.Bar(x=gap_df['Komponen'], y=gap_df['Gap'], marker_color=gap_df['Warna'], text=gap_df['Gap'].round(2), textposition='outside', textfont=dict(color='#1e293b', weight='bold')))
            fig_gap_overall.update_layout(template='plotly_white', height=300, yaxis_title='Gap (ACV - 100%)', xaxis_title='Komponen')
            st.plotly_chart(fig_gap_overall, use_container_width=True)
        
        st.subheader("Gap Skor PPSA per Kasir")
        gap_cashier_df = calculate_gap_per_cashier(filtered_df)
        if not gap_cashier_df.empty:
            fig_gap_cashier = go.Figure()
            fig_gap_cashier.add_trace(go.Bar(y=gap_cashier_df['NAMA KASIR'], x=gap_cashier_df['Gap Skor'], orientation='h', marker_color=gap_cashier_df['Warna'], text=[f"{score:.2f}" for score in gap_cashier_df['Gap Skor']], textposition='outside', textfont=dict(size=11, color='#1e293b', weight='bold')))
            fig_gap_cashier.update_layout(template='plotly_white', height=max(400, len(gap_cashier_df) * 40), showlegend=False, xaxis_title='Gap Skor (Skor - 100)', yaxis={'categoryorder': 'total ascending'})
            st.plotly_chart(fig_gap_cashier, use_container_width=True)
        st.markdown('</div>', unsafe_allow_html=True)

        st.markdown('<div class="content-container">', unsafe_allow_html=True)
        st.markdown('<h2 class="section-header">🔍 Analisa Mendalam PPSA</h2>', unsafe_allow_html=True)
        score_summary = calculate_aggregate_scores_per_cashier(filtered_df)
        if not score_summary.empty:
            top_cashiers = score_summary.head(5)
            fig_breakdown = go.Figure()
            components = ['SCORE PSM', 'SCORE PWP', 'SCORE SG', 'SCORE APC']
            for comp in components:
                fig_breakdown.add_trace(go.Bar(name=comp.replace('SCORE ', ''), y=top_cashiers['NAMA KASIR'], x=top_cashiers[comp], orientation='h'))
            fig_breakdown.update_layout(barmode='stack', template='plotly_white', height=300, yaxis={'categoryorder': 'total ascending'}, xaxis_title='Skor Kontribusi')
            st.plotly_chart(fig_breakdown, use_container_width=True)
        st.markdown('</div>', unsafe_allow_html=True)

        st.markdown('<div class="content-container">', unsafe_allow_html=True)
        st.markdown('<h2 class="section-header">📊 Tren & Pola Performa</h2>', unsafe_allow_html=True)
        
        st.subheader("📅 Total Skor PPSA per Tanggal")
        if not filtered_df.empty and 'TANGGAL' in filtered_df.columns:
            daily_score = filtered_df.groupby('TANGGAL')['TOTAL SCORE PPSA'].sum().reset_index()
            fig_date = px.line(daily_score, x='TANGGAL', y='TOTAL SCORE PPSA', title='Tren Skor PPSA Keseluruhan', template='plotly_white', markers=True)
            fig_date.update_layout(yaxis_title='Total Skor PPSA', xaxis_title='Tanggal')
            st.plotly_chart(fig_date, use_container_width=True)
        
        st.subheader("📆 Rata-rata Skor PPSA per Hari")
        if not filtered_df.empty and 'HARI' in filtered_df.columns:
            daily_avg = filtered_df.groupby('HARI')['TOTAL SCORE PPSA'].mean().reindex(['Senin', 'Selasa', 'Rabu', 'Kamis', 'Jumat', 'Sabtu', 'Minggu']).reset_index()
            fig_day_avg = px.bar(daily_avg, x='TOTAL SCORE PPSA', y='HARI', orientation='h', title='Rata-rata Skor Berdasarkan Hari', template='plotly_white', labels={'TOTAL SCORE PPSA': 'Rata-rata Skor PPSA', 'HARI': 'Hari'})
            fig_day_avg.update_layout(yaxis={'categoryorder': 'array', 'categoryarray': ['Minggu', 'Sabtu', 'Jumat', 'Kamis', 'Rabu', 'Selasa', 'Senin']})
            st.plotly_chart(fig_day_avg, use_container_width=True)
        st.markdown('</div>', unsafe_allow_html=True)

        st.markdown('<div class="content-container">', unsafe_allow_html=True)
        st.markdown('<h2 class="section-header">👥 Performa Kasir & Shift</h2>', unsafe_allow_html=True)
        
        st.subheader("Total Performa Kasir (Agregat)")
        if not score_summary.empty:
            score_summary['Ranking'] = range(1, len(score_summary) + 1)
            fig_kasir = go.Figure()
            colors = ['#667eea' if i < 3 else '#764ba2' if i < 5 else '#a8a8a8' for i in range(len(score_summary))]
            fig_kasir.add_trace(go.Bar(y=score_summary['NAMA KASIR'], x=score_summary['TOTAL SCORE PPSA'], orientation='h', marker=dict(color=colors), text=[f"#{rank} - {score:.2f}" for rank, score in zip(score_summary['Ranking'], score_summary['TOTAL SCORE PPSA'])], textposition='outside'))
            fig_kasir.update_layout(template='plotly_white', height=max(400, len(score_summary) * 40), showlegend=False, xaxis_title='Total Score PPSA (Agregat)', yaxis={'categoryorder': 'total ascending'})
            st.plotly_chart(fig_kasir, use_container_width=True)
        
        st.subheader("Performa per Shift")
        shift_summary = calculate_aggregate_scores_per_shift(filtered_df)
        if not shift_summary.empty:
            fig_shift = px.bar(shift_summary, x='TOTAL SCORE PPSA', y='SHIFT', orientation='h', color='TOTAL SCORE PPSA', color_continuous_scale=px.colors.sequential.Blues, template='plotly_white')
            fig_shift.update_layout(height=300, showlegend=False, yaxis={'categoryorder': 'total ascending'})
            st.plotly_chart(fig_shift, use_container_width=True)
        st.markdown('</div>', unsafe_allow_html=True)

    with tab2:
        st.markdown('<div class="content-container">', unsafe_allow_html=True)
        st.markdown('<h2 class="section-header">🛒 Performa Tebus (Suuegerr)</h2>', unsafe_allow_html=True)
        
        if not filtered_df.empty and 'NAMA KASIR' in filtered_df.columns:
            tebus_summary = calculate_tebus_summary_per_cashier(filtered_df)
            
            if not tebus_summary.empty:
                overall_tebus_acv = (filtered_df['ACTUAL TEBUS 2500'].sum() / filtered_df['TARGET TEBUS 2500'].sum()) * 100 if filtered_df['TARGET TEBUS 2500'].sum() > 0 else 0
                col1, col2, col3 = st.columns([1, 2, 1])
                with col2:
                    st.markdown(f"""
                    <div class="total-ppsa-card" style="background: linear-gradient(135deg, #10b981 0%, #059669 100%);">
                        <div class="total-ppsa-label">{get_svg_icon("tebus", size=32, color="white")} TOTAL ACV TEBUS (SUUEGERR)</div>
                        <div class="total-ppsa-value">{overall_tebus_acv:.2f}%</div>
                    </div>
                    """, unsafe_allow_html=True)
                st.markdown("---")
                
                fig_tebus = go.Figure()
                colors = ['#10b981' if i < 3 else '#34d399' if i < 5 else '#a8a8a8' for i in range(len(tebus_summary))]
                tebus_summary['Ranking'] = range(1, len(tebus_summary) + 1)
                fig_tebus.add_trace(go.Bar(y=tebus_summary['NAMA KASIR'], x=tebus_summary['(%) ACV TEBUS 2500'], orientation='h', marker=dict(color=colors), text=[f"#{rank} - {score:.2f}%" for rank, score in zip(tebus_summary['Ranking'], tebus_summary['(%) ACV TEBUS 2500'])], textposition='outside'))
                fig_tebus.update_layout(template='plotly_white', height=max(400, len(tebus_summary) * 40), showlegend=False, xaxis_title='ACV Tebus (Suuegerr) (%)', yaxis={'categoryorder': 'total ascending'})
                st.plotly_chart(fig_tebus, use_container_width=True)

                st.markdown("#### 🛒 Top 3 Performers (Tebus Suuegerr)")
                cols = st.columns(3)
                medals = ["🥇", "🥈", "🥉"]
                for idx, (col, medal) in enumerate(zip(cols, medals)):
                    if idx < len(tebus_summary):
                        with col:
                            st.markdown(f"""
                            <div class="metric-card" style="text-align: center;">
                                <div style="font-size: 2.5rem; margin-bottom: 0.5rem;">{medal}</div>
                                <div style="font-size: 1.1rem; font-weight: 600; color: #1e293b; margin-bottom: 0.25rem;">{tebus_summary.iloc[idx]['NAMA KASIR']}</div>
                                <div style="font-size: 1.5rem; font-weight: 700; color: #10b981;">{tebus_summary.iloc[idx]['(%) ACV TEBUS 2500']:.2f}%</div>
                            </div>
                            """, unsafe_allow_html=True)
                
                st.markdown("---")
                st.subheader("📉 Gap Analysis Tebus (Target 100%)")
                tebus_summary['Gap'] = tebus_summary['(%) ACV TEBUS 2500'] - 100.0
                tebus_summary['Warna'] = tebus_summary['Gap'].apply(lambda x: '#10b981' if x >= 0 else '#ef4444')
                
                fig_gap_tebus = go.Figure()
                fig_gap_tebus.add_trace(go.Bar(y=tebus_summary['NAMA KASIR'], x=tebus_summary['Gap'], orientation='h', marker_color=tebus_summary['Warna'], text=[f"{gap:.2f}%" for gap in tebus_summary['Gap']], textposition='outside', textfont=dict(size=11, color='#1e293b', weight='bold')))
                fig_gap_tebus.update_layout(template='plotly_white', height=max(400, len(tebus_summary) * 40), showlegend=False, xaxis_title='Gap (ACV - 100%)', yaxis={'categoryorder': 'total ascending'})
                st.plotly_chart(fig_gap_tebus, use_container_width=True)

            else:
                st.warning("Tidak ada data Tebus (Suuegerr) untuk ditampilkan.")
        st.markdown('</div>', unsafe_allow_html=True)

else:
    st.error("❌ Tidak dapat memuat data. Silakan periksa koneksi Google Sheets Anda.")

st.markdown("<br><br>", unsafe_allow_html=True)
st.markdown(f"""
<div style='text-align: center; color: rgba(255,255,255,0.7); padding: 2rem; font-size: 0.9rem;'>
    <strong>Dashboard PPSA Analytics</strong> • {get_svg_icon("dashboard", size=16, color="rgba(255,255,255,0.7)")} Powered by Streamlit • © 2025
</div>
""", unsafe_allow_html=True)
