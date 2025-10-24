import streamlit as st
import pandas as pd
import gspread
from google.oauth2.service_account import Credentials
import plotly.express as px

# --- KONFIGURASI HALAMAN ---
st.set_page_config(
    page_title="Dashboard PPSA",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded"
)

# --- CSS KUSTOM UNTUK TAMPILAN MODERN ---
st.markdown("""
<style>
/* Font dan Latar Belakang Utama */
.stApp {
    background-color: #F0F2F6;
    font-family: 'Segoe UI', 'Roboto', sans-serif;
}

/* Judul Utama */
.main-title {
    font-size: 2.5rem;
    color: #1f77b4;
    font-weight: 700;
    text-align: center;
    padding-bottom: 1rem;
    border-bottom: 2px solid #E0E0E0;
    margin-bottom: 2rem;
}

/* Header */
h2, h3 {
    color: #1f77b4;
    font-weight: 600;
}

/* Kartu Metrik */
.metric-card {
    background-color: #FFFFFF;
    border-left: 5px solid #1f77b4;
    padding: 1rem;
    border-radius: 8px;
    box-shadow: 0 4px 6px rgba(0,0,0,0.05);
    transition: transform 0.2s;
}
.metric-card:hover {
    transform: translateY(-5px);
}

/* Sidebar */
.css-1d391kg, .css-1lcbmhc {
    background-color: #FFFFFF;
    border-right: 1px solid #E0E0E0;
}

/* Tabel Dataframe */
.stDataFrame {
    border-radius: 10px;
    overflow: hidden;
    box-shadow: 0 4px 6px rgba(0,0,0,0.05);
}

/* Container untuk konten utama */
.content-container {
    background-color: #FFFFFF;
    padding: 1.5rem;
    border-radius: 10px;
    box-shadow: 0 4px 6px rgba(0,0,0,0.05);
    margin-bottom: 1.5rem;
}

/* Footer */
footer {
    visibility: hidden;
}
</style>
""", unsafe_allow_html=True)


# --- FUNGSI UNTUK MENGAMBIL DATA DARI GOOGLE SHEETS ---
@st.cache_data(ttl=600)
def load_data_from_gsheet():
    try:
        scopes = [
            'https://www.googleapis.com/auth/spreadsheets',
            'https://www.googleapis.com/auth/drive'
        ]
        creds = Credentials.from_service_account_info(
            st.secrets["gcp_service_account"],
            scopes=scopes
        )
        client = gspread.authorize(creds)
        
        spreadsheet = client.open("Dashboard")
        worksheet = spreadsheet.get_worksheet(0)
        
        data = worksheet.get_all_values()
        if not data:
            st.warning("Spreadsheet kosong atau tidak ada data yang ditemukan.")
            return pd.DataFrame()
        df = pd.DataFrame(data[1:], columns=data[0])
        return df
    except Exception as e:
        st.error(f"Gagal mengambil data dari Google Sheets: {e}")
        return pd.DataFrame()

# --- FUNGSI UNTUK MEMPROSES DATA PER KASIR ---
def process_data(df):
    if df.empty:
        return df

    if 'TANGGAL' in df.columns:
        df['TANGGAL'] = pd.to_datetime(df['TANGGAL'], format='%d/%m/%Y', errors='coerce')

    numeric_cols = [
        'PSM Target', 'PSM Actual', 'BOBOT PSM', 'PWP Target', 'PWP Actual', 'BOBOT PWP',
        'SG Target', 'SG Actual', 'BOBOT SG', 'APC Target', 'APC Actual', 'BOBOT APC',
        'TARGET TEBUS 2500', 'ACTUAL TEBUS 2500'
    ]
    
    for col in numeric_cols:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors='coerce').fillna(0)

    def calculate_acv(actual, target):
        if target == 0:
            return 0.0
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

# --- FUNGSI UNTUK MENGHITUNG TOTAL PPSA KESELURUHAN ---
def calculate_overall_ppsa_breakdown(df):
    if df.empty:
        return {'total': 0.0, 'psm': 0.0, 'pwp': 0.0, 'sg': 0.0, 'apc': 0.0}
    weights = {'PSM': 20, 'PWP': 25, 'SG': 30, 'APC': 25}
    scores = {'psm': 0.0, 'pwp': 0.0, 'sg': 0.0, 'apc': 0.0}
    sum_components = ['PSM', 'PWP', 'SG']
    for comp in sum_components:
        target_col = f'{comp} Target'
        actual_col = f'{comp} Actual'
        total_target = df[target_col].sum()
        total_actual = df[actual_col].sum()
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

# --- UI DASHBOARD ---
st.markdown('<h1 class="main-title">📊 Dashboard PPSA</h1>', unsafe_allow_html=True)
st.markdown("""
<div style='text-align: center; color: #6B7280; margin-bottom: 2rem;'>
Memantau performa indikator <strong>PPSA</strong> yang terdiri dari <strong>PSM</strong> (Produk Spesial Mingguan), <strong>PWP</strong> (Purchase With Purchase), <strong>SG</strong> (Serba Gratis), dan <strong>APC</strong> (Average Purchase Customer).
</div>
""", unsafe_allow_html=True)

raw_df = load_data_from_gsheet()

if not raw_df.empty:
    processed_df = process_data(raw_df.copy())
    
    with st.sidebar:
        st.header("⚙️ Filter Data")
        if 'NAMA KASIR' in processed_df.columns:
            selected_names = st.multiselect(
                "Pilih Nama Kasir:",
                options=processed_df['NAMA KASIR'].unique(),
                default=processed_df['NAMA KASIR'].unique()
            )
            filtered_df = processed_df[processed_df['NAMA KASIR'].isin(selected_names)]
        else:
            filtered_df = processed_df

        if 'TANGGAL' in filtered_df.columns:
            filtered_df = filtered_df.dropna(subset=['TANGGAL'])
            if not filtered_df.empty:
                min_date = filtered_df['TANGGAL'].min().to_pydatetime()
                max_date = filtered_df['TANGGAL'].max().to_pydatetime()
                selected_date_range = st.date_input(
                    "Pilih Rentang Tanggal:",
                    value=[min_date, max_date],
                    min_value=min_date,
                    max_value=max_date
                )
                if len(selected_date_range) == 2:
                    start_date, end_date = pd.to_datetime(selected_date_range[0]), pd.to_datetime(selected_date_range[1])
                    mask = (filtered_df['TANGGAL'] >= start_date) & (filtered_df['TANGGAL'] <= end_date)
                    filtered_df = filtered_df.loc[mask]

    # --- RINGKASAN PERFORMA KESELURUHAN ---
    st.markdown('<div class="content-container">', unsafe_allow_html=True)
    st.header("🏆 Ringkasan Performa Keseluruhan")
    overall_scores = calculate_overall_ppsa_breakdown(filtered_df)
    
    col_psm, col_pwp, col_sg, col_apc = st.columns(4, gap="medium")
    with col_psm:
        st.markdown(f"""
        <div class="metric-card">
            <div style="font-size: 0.9rem; color: #6B7280;">Skor PSM</div>
            <div style="font-size: 1.8rem; font-weight: 700; color: #1f77b4;">{overall_scores['psm']:.2f}</div>
        </div>
        """, unsafe_allow_html=True)
    with col_pwp:
        st.markdown(f"""
        <div class="metric-card">
            <div style="font-size: 0.9rem; color: #6B7280;">Skor PWP</div>
            <div style="font-size: 1.8rem; font-weight: 700; color: #1f77b4;">{overall_scores['pwp']:.2f}</div>
        </div>
        """, unsafe_allow_html=True)
    with col_sg:
        st.markdown(f"""
        <div class="metric-card">
            <div style="font-size: 0.9rem; color: #6B7280;">Skor SG</div>
            <div style="font-size: 1.8rem; font-weight: 700; color: #1f77b4;">{overall_scores['sg']:.2f}</div>
        </div>
        """, unsafe_allow_html=True)
    with col_apc:
        st.markdown(f"""
        <div class="metric-card">
            <div style="font-size: 0.9rem; color: #6B7280;">Skor APC</div>
            <div style="font-size: 1.8rem; font-weight: 700; color: #1f77b4;">{overall_scores['apc']:.2f}</div>
        </div>
        """, unsafe_allow_html=True)
    
    st.markdown("---")
    
    col_total, col_chart = st.columns([1, 2], gap="large")
    with col_total:
        st.markdown(f"""
        <div class="metric-card" style="border-left-color: #2E8B57; text-align: center; padding: 2rem 1rem;">
            <div style="font-size: 1.2rem; color: #6B7280; margin-bottom: 0.5rem;">💰 TOTAL PPSA</div>
            <div style="font-size: 3rem; font-weight: 700; color: #2E8B57;">{overall_scores['total']:.2f}</div>
        </div>
        """, unsafe_allow_html=True)
    with col_chart:
        chart_data = {
            'Komponen': ['PSM', 'PWP', 'SG', 'APC'],
            'Skor': [overall_scores['psm'], overall_scores['pwp'], overall_scores['sg'], overall_scores['apc']]
        }
        chart_df = pd.DataFrame(chart_data)
        fig_overall = px.bar(
            chart_df, 
            x='Komponen', 
            y='Skor', 
            color='Skor',
            color_continuous_scale=px.colors.sequential.Blues,
            template='plotly_white'
        )
        fig_overall.update_layout(showlegend=False, height=250, margin=dict(l=20, r=20, t=20, b=20))
        st.plotly_chart(fig_overall, use_container_width=True)
    st.markdown('</div>', unsafe_allow_html=True) # Tutup container

    # --- DATA PERFORMA KASIR ---
    st.markdown('<div class="content-container">', unsafe_allow_html=True)
    st.header("📈 Data Performa Kasir")
    
    st.subheader("Total Score PPSA per Kasir")
    if not filtered_df.empty and 'NAMA KASIR' in filtered_df.columns:
        score_summary = filtered_df.groupby('NAMA KASIR')['TOTAL SCORE PPSA'].sum().sort_values(ascending=False).reset_index()
        fig_kasir = px.bar(
            score_summary, 
            x='TOTAL SCORE PPSA', 
            y='NAMA KASIR', 
            orientation='h',
            color='TOTAL SCORE PPSA',
            color_continuous_scale=px.colors.sequential.Viridis,
            template='plotly_white'
        )
        fig_kasir.update_layout(showlegend=False, height=400, yaxis={'categoryorder':'total ascending'})
        st.plotly_chart(fig_kasir, use_container_width=True)
    else:
        st.warning("Tidak ada data untuk ditampilkan setelah difilter.")

    st.subheader("📋 Tabel Detail Perhitungan")
    column_configuration = {
        'NAMA KASIR': st.column_config.TextColumn("Nama Kasir", width="large"),
        'TANGGAL': st.column_config.DateColumn("Tanggal", format="DD.MM.YYYY", width="medium"),
        'SHIFT': st.column_config.TextColumn("Shift", width="small"),
        'PSM Target': st.column_config.NumberColumn(format="%.0f"),
        'PSM Actual': st.column_config.NumberColumn(format="%.0f"),
        'PWP Target': st.column_config.NumberColumn(format="%.0f"),
        'PWP Actual': st.column_config.NumberColumn(format="%.0f"),
        'SG Target': st.column_config.NumberColumn(format="%.0f"),
        'SG Actual': st.column_config.NumberColumn(format="%.0f"),
        'APC Target': st.column_config.NumberColumn(format="%.0f"),
        'APC Actual': st.column_config.NumberColumn(format="%.0f"),
        'TARGET TEBUS 2500': st.column_config.NumberColumn(format="%.0f"),
        'ACTUAL TEBUS 2500': st.column_config.NumberColumn(format="%.0f"),
        '(%) PSM ACV': st.column_config.NumberColumn("ACV PSM (%)", format="%.2f %%"),
        '(%) PWP ACV': st.column_config.NumberColumn("ACV PWP (%)", format="%.2f %%"),
        '(%) SG ACV': st.column_config.NumberColumn("ACV SG (%)", format="%.2f %%"),
        '(%) APC ACV': st.column_config.NumberColumn("ACV APC (%)", format="%.2f %%"),
        '(%) ACV TEBUS 2500': st.column_config.NumberColumn("ACV Tebus 2500 (%)", format="%.2f %%"),
        'BOBOT PSM': st.column_config.NumberColumn(format="%.0f"),
        'BOBOT PWP': st.column_config.NumberColumn(format="%.0f"),
        'BOBOT SG': st.column_config.NumberColumn(format="%.0f"),
        'BOBOT APC': st.column_config.NumberColumn(format="%.0f"),
        'SCORE PSM': st.column_config.NumberColumn("Score PSM", format="%.2f"),
        'SCORE PWP': st.column_config.NumberColumn("Score PWP", format="%.2f"),
        'SCORE SG': st.column_config.NumberColumn("Score SG", format="%.2f"),
        'SCORE APC': st.column_config.NumberColumn("Score APC", format="%.2f"),
        'TOTAL SCORE PPSA': st.column_config.NumberColumn("TOTAL SCORE PPSA", format="%.2f"),
    }
    final_column_config = {col: config for col, config in column_configuration.items() if col in filtered_df.columns}
    st.dataframe(filtered_df, use_container_width=True, column_config=final_column_config, hide_index=True)
    st.markdown('</div>', unsafe_allow_html=True) # Tutup container
