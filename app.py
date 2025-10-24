import streamlit as st
import pandas as pd
import gspread
from google.oauth2.service_account import Credentials

# --- KONFIGURASI HALAMAN ---
st.set_page_config(
    page_title="Dashboard PPSA",
    page_icon="📊",
    layout="wide"
)

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

# --- FUNGSI YANG DIPERBAIKI: MENGEMBALIKAN DETAIL SKOR SETIAP KOMPONEN ---
def calculate_overall_ppsa_breakdown(df):
    """
    Menghitung total PPSA keseluruhan dan mengembalikan skor per komponen.
    Logika: PSM/PWP/SG (dari total), APC (dari rata-rata).
    """
    if df.empty:
        return {
            'total': 0.0, 'psm': 0.0, 'pwp': 0.0, 'sg': 0.0, 'apc': 0.0
        }

    weights = {'PSM': 20, 'PWP': 25, 'SG': 30, 'APC': 25}
    scores = {'psm': 0.0, 'pwp': 0.0, 'sg': 0.0, 'apc': 0.0}

    # Komponen PSM, PWP, SG (berdasarkan JUMLAH/SUM)
    sum_components = ['PSM', 'PWP', 'SG']
    for comp in sum_components:
        target_col = f'{comp} Target'
        actual_col = f'{comp} Actual'
        total_target = df[target_col].sum()
        total_actual = df[actual_col].sum()
        
        if total_target > 0:
            acv = (total_actual / total_target) * 100
            scores[comp.lower()] = (acv * weights[comp]) / 100

    # Komponen APC (berdasarkan RATA-RATA/MEAN)
    avg_target_apc = df['APC Target'].mean()
    avg_actual_apc = df['APC Actual'].mean()
    
    if avg_target_apc > 0:
        acv_apc = (avg_actual_apc / avg_target_apc) * 100
        scores['apc'] = (acv_apc * weights['APC']) / 100
        
    scores['total'] = sum(scores.values())
    return scores

# --- UI DASHBOARD ---
st.title("📊 Dashboard Performa PPSA")
st.markdown("Dashboard untuk memantau performa **Penjualan Prestasi Sales Assistant (PPSA)** yang terdiri dari komponen **PSM, PWP, SG, dan APC**.")

raw_df = load_data_from_gsheet()

if not raw_df.empty:
    processed_df = process_data(raw_df.copy())
    
    st.sidebar.header("Filter Data")
    
    if 'NAMA KASIR' in processed_df.columns:
        selected_names = st.sidebar.multiselect(
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
            
            selected_date_range = st.sidebar.date_input(
                "Pilih Rentang Tanggal:",
                value=[min_date, max_date],
                min_value=min_date,
                max_value=max_date
            )
            
            if len(selected_date_range) == 2:
                start_date, end_date = pd.to_datetime(selected_date_range[0]), pd.to_datetime(selected_date_range[1])
                mask = (filtered_df['TANGGAL'] >= start_date) & (filtered_df['TANGGAL'] <= end_date)
                filtered_df = filtered_df.loc[mask]

    # --- PENINGKATAN: TAMPILKAN RINGKASAN DENGAN METRIK TERPERINCI ---
    st.header("🏆 Ringkasan Performa Keseluruhan")
    overall_scores = calculate_overall_ppsa_breakdown(filtered_df)
    
    # Tampilkan skor per komponen
    col_psm, col_pwp, col_sg, col_apc = st.columns(4)
    with col_psm:
        st.metric("Skor PSM", f"{overall_scores['psm']:.2f}", help="Skor dari total PSM")
    with col_pwp:
        st.metric("Skor PWP", f"{overall_scores['pwp']:.2f}", help="Skor dari total PWP")
    with col_sg:
        st.metric("Skor SG", f"{overall_scores['sg']:.2f}", help="Skor dari total SG")
    with col_apc:
        st.metric("Skor APC", f"{overall_scores['apc']:.2f}", help="Skor dari rata-rata APC")
    
    st.markdown("---") # Garis pemisah
    
    # Tampilkan total skor dan grafik kontribusi
    col_total, col_chart = st.columns([1, 2])
    with col_total:
        st.metric(
            label="💰 **TOTAL PPSA**",
            value=f"{overall_scores['total']:.2f}",
            help="Total skor adalah jumlah dari Skor PSM, PWP, SG, dan APC."
        )
    with col_chart:
        # Data untuk grafik
        chart_data = {
            'Komponen': ['PSM', 'PWP', 'SG', 'APC'],
            'Skor': [overall_scores['psm'], overall_scores['pwp'], overall_scores['sg'], overall_scores['apc']]
        }
        chart_df = pd.DataFrame(chart_data).set_index('Komponen')
        st.bar_chart(chart_df)

    st.divider()

    st.header("Data Performa Kasir")
    
    st.subheader("Rata-rata Score PPSA per Kasir")
    if not filtered_df.empty and 'NAMA KASIR' in filtered_df.columns:
        score_summary = filtered_df.groupby('NAMA KASIR')['TOTAL SCORE PPSA'].mean().sort_values(ascending=False)
        st.bar_chart(score_summary)
    else:
        st.warning("Tidak ada data untuk ditampilkan setelah difilter.")

    st.subheader("Tabel Detail Perhitungan")
    
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
    
    st.dataframe(
        filtered_df,
        use_container_width=True,
        column_config=final_column_config,
        hide_index=True
    )
