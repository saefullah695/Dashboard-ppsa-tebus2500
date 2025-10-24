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
@st.cache_data(ttl=600) # Cache data selama 10 menit untuk performa
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
        worksheet = spreadsheet.get_worksheet(0) # Mengambil sheet pertama
        
        data = worksheet.get_all_values()
        df = pd.DataFrame(data[1:], columns=data[0])
        return df
    except Exception as e:
        st.error(f"Gagal mengambil data dari Google Sheets: {e}")
        return None

# --- FUNGSI UNTUK MEMPROSES DATA DAN MENGHITUNG SCORE ---
def process_data(df):
    # --- PERBAIKAN 1: PEMBACAAN TANGGAL ---
    # Konversi kolom TANGGAL ke datetime dengan format DD/MM/YYYY
    if 'TANGGAL' in df.columns:
        df['TANGGAL'] = pd.to_datetime(df['TANGGAL'], format='%d/%m/%Y', errors='coerce')

    # Daftar kolom yang perlu dikonversi ke numerik
    numeric_cols = [
        'PSM Target', 'PSM Actual', 'BOBOT PSM', 'PWP Target', 'PWP Actual', 'BOBOT PWP',
        'SG Target', 'SG Actual', 'BOBOT SG', 'APC Target', 'APC Actual', 'BOBOT APC',
        'TARGET TEBUS 2500', 'ACTUAL TEBUS 2500'
    ]
    
    for col in numeric_cols:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors='coerce').fillna(0)

    # Fungsi helper untuk menghitung ACV (Actual vs Target)
    def calculate_acv(actual, target):
        if target == 0:
            return 0.0
        return (actual / target) * 100

    # Hitung kolom ACV
    df['(%) PSM ACV'] = df.apply(lambda row: calculate_acv(row['PSM Actual'], row['PSM Target']), axis=1)
    df['(%) PWP ACV'] = df.apply(lambda row: calculate_acv(row['PWP Actual'], row['PWP Target']), axis=1)
    df['(%) SG ACV'] = df.apply(lambda row: calculate_acv(row['SG Actual'], row['SG Target']), axis=1)
    df['(%) APC ACV'] = df.apply(lambda row: calculate_acv(row['APC Actual'], row['APC Target']), axis=1)
    df['(%) ACV TEBUS 2500'] = df.apply(lambda row: calculate_acv(row['ACTUAL TEBUS 2500'], row['TARGET TEBUS 2500']), axis=1)

    # Rumus: Score = (ACV × Bobot) / 100
    df['SCORE PSM'] = (df['(%) PSM ACV'] * df['BOBOT PSM']) / 100
    df['SCORE PWP'] = (df['(%) PWP ACV'] * df['BOBOT PWP']) / 100
    df['SCORE SG'] = (df['(%) SG ACV'] * df['BOBOT SG']) / 100
    df['SCORE APC'] = (df['(%) APC ACV'] * df['BOBOT APC']) / 100
    
    # Total Score PPSA
    score_cols = ['SCORE PSM', 'SCORE PWP', 'SCORE SG', 'SCORE APC']
    df['TOTAL SCORE PPSA'] = df[score_cols].sum(axis=1)
    
    return df

# --- UI DASHBOARD ---
st.title("📊 Dashboard PPSA")
st.markdown("Dashboard untuk memantau performa Penjualan Prestasi Sales Assistant (PPSA)")

# Muat data
raw_df = load_data_from_gsheet()

if raw_df is not None:
    # Proses data
    processed_df = process_data(raw_df.copy())
    
    # --- SIDEBAR UNTUK FILTER ---
    st.sidebar.header("Filter Data")
    
    # Filter berdasarkan Nama Kasir
    if 'NAMA KASIR' in processed_df.columns:
        selected_names = st.sidebar.multiselect(
            "Pilih Nama Kasir:",
            options=processed_df['NAMA KASIR'].unique(),
            default=processed_df['NAMA KASIR'].unique()
        )
        filtered_df = processed_df[processed_df['NAMA KASIR'].isin(selected_names)]
    else:
        filtered_df = processed_df

    # Filter berdasarkan Tanggal
    if 'TANGGAL' in filtered_df.columns and not filtered_df['TANGGAL'].isnull().all():
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

    # --- TAMPILKAN DATA ---
    st.header("Data Performa Kasir")
    
    # Tampilkan Total Score PPSA per Kasir
    st.subheader("Total Score PPSA per Kasir")
    if not filtered_df.empty and 'NAMA KASIR' in filtered_df.columns:
        score_summary = filtered_df.groupby('NAMA KASIR')['TOTAL SCORE PPSA'].mean().sort_values(ascending=False)
        st.bar_chart(score_summary)
    
    # Tampilkan Tabel Detail
    st.subheader("Tabel Detail Perhitungan")
    
    # --- PERBAIKAN 2: FORMAT TAMPILAN PERSEN ---
    # Buat dictionary untuk format kolom
    # Kolom persentase akan ditampilkan dengan 2 angka di belakang koma dan simbol %
    # Kolom score akan ditampilkan dengan 2 angka di belakang koma
    format_dict = {
        '(%) PSM ACV': "{:.2f}%",
        '(%) PWP ACV': "{:.2f}%",
        '(%) SG ACV': "{:.2f}%",
        '(%) APC ACV': "{:.2f}%",
        '(%) ACV TEBUS 2500': "{:.2f}%",
        'SCORE PSM': "{:.2f}",
        'SCORE PWP': "{:.2f}",
        'SCORE SG': "{:.2f}",
        'SCORE APC': "{:.2f}",
        'TOTAL SCORE PPSA': "{:.2f}"
    }
    
    st.dataframe(filtered_df, use_container_width=True, format=format_dict)
