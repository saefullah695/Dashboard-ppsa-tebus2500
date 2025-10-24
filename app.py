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
        if not data:
            st.warning("Spreadsheet kosong atau tidak ada data yang ditemukan.")
            return pd.DataFrame()
        df = pd.DataFrame(data[1:], columns=data[0])
        return df
    except Exception as e:
        st.error(f"Gagal mengambil data dari Google Sheets: {e}")
        return pd.DataFrame()

# --- FUNGSI UNTUK MEMPROSES DATA DAN MENGHITUNG SCORE ---
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

# --- UI DASHBOARD ---
st.title("📊 Dashboard PPSA")
st.markdown("Dashboard untuk memantau performa Penjualan Prestasi Sales Assistant (PPSA)")

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

    st.header("Data Performa Kasir")
    
    st.subheader("Total Score PPSA per Kasir")
    if not filtered_df.empty and 'NAMA KASIR' in filtered_df.columns:
        score_summary = filtered_df.groupby('NAMA KASIR')['TOTAL SCORE PPSA'].mean().sort_values(ascending=False)
        st.bar_chart(score_summary)
    else:
        st.warning("Tidak ada data untuk ditampilkan setelah difilter.")

    st.subheader("Tabel Detail Perhitungan")
    
    # --- PERBAIKAN: MENGGUNAKAN column_config (METODE BARU) ---
    # Definisikan konfigurasi untuk setiap kolom yang perlu diformat
    # Format "%.2f %%" berarti: angka dengan 2 desimal, diikuti spasi dan simbol %
    column_configuration = {
        'NAMA KASIR': st.column_config.TextColumn("Nama Kasir", width="large", help="Nama dari kasir"),
        'TANGGAL': st.column_config.DateColumn("Tanggal", format="DD.MM.YYYY", width="medium"),
        'SHIFT': st.column_config.TextColumn("Shift", width="small"),
        
        # Kolom Target & Actual
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

        # Kolom Persentase ACV
        '(%) PSM ACV': st.column_config.NumberColumn("ACV PSM (%)", format="%.2f %%", help="Persentase Pencapaian PSM"),
        '(%) PWP ACV': st.column_config.NumberColumn("ACV PWP (%)", format="%.2f %%", help="Persentase Pencapaian PWP"),
        '(%) SG ACV': st.column_config.NumberColumn("ACV SG (%)", format="%.2f %%", help="Persentase Pencapaian SG"),
        '(%) APC ACV': st.column_config.NumberColumn("ACV APC (%)", format="%.2f %%", help="Persentase Pencapaian APC"),
        '(%) ACV TEBUS 2500': st.column_config.NumberColumn("ACV Tebus 2500 (%)", format="%.2f %%", help="Persentase Pencapaian Tebus 2500"),

        # Kolom Bobot
        'BOBOT PSM': st.column_config.NumberColumn(format="%.0f"),
        'BOBOT PWP': st.column_config.NumberColumn(format="%.0f"),
        'BOBOT SG': st.column_config.NumberColumn(format="%.0f"),
        'BOBOT APC': st.column_config.NumberColumn(format="%.0f"),
        
        # Kolom Score
        'SCORE PSM': st.column_config.NumberColumn("Score PSM", format="%.2f"),
        'SCORE PWP': st.column_config.NumberColumn("Score PWP", format="%.2f"),
        'SCORE SG': st.column_config.NumberColumn("Score SG", format="%.2f"),
        'SCORE APC': st.column_config.NumberColumn("Score APC", format="%.2f"),
        'TOTAL SCORE PPSA': st.column_config.NumberColumn("TOTAL SCORE PPSA", format="%.2f", help="Total akhir score PPSA"),
    }
    
    # Buat dictionary konfigurasi final hanya untuk kolom yang ada di dataframe
    final_column_config = {col: config for col, config in column_configuration.items() if col in filtered_df.columns}
    
    # Tampilkan dataframe dengan konfigurasi baru
    st.dataframe(
        filtered_df,
        use_container_width=True,
        column_config=final_column_config,
        hide_index=True # Sembunyikan index pandas
    )
