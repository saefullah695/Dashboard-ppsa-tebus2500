import streamlit as st
import pandas as pd
import gspread
from google.oauth2.service_account import Credentials
import plotly.express as px
import google.generativeai as genai
from datetime import datetime

# --- Konfigurasi Halaman ---
st.set_page_config(
    page_title="PPSA 2GC6 BAROS PANDEGLANG",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded"
)

# --- Fungsi untuk Memuat Data dari Google Sheets ---
@st.cache_data(ttl=600) # Cache data selama 10 menit
def load_data_from_gsheet():
    try:
        # Menggunakan kredensial dari secrets.toml
        scope = ["https://www.googleapis.com/auth/spreadsheets", "https://www.googleapis.com/auth/drive"]
        creds = Credentials.from_service_account_info(
            st.secrets["gcp_service_account"],
            scopes=scope
        )
        client = gspread.authorize(creds)

        # Buka spreadsheet dan worksheet
        spreadsheet = client.open("NAMA_SPREADSHEET_ANDA") # <-- GANTI dengan nama Google Sheet Anda
        worksheet = spreadsheet.worksheet("Data")
        
        # Ambil semua data dan konversi ke DataFrame
        data = worksheet.get_all_records()
        df = pd.DataFrame(data)
        
        # --- Preprocessing Data ---
        # Konversi kolom tanggal ke datetime
        df['TANGGAL'] = pd.to_datetime(df['TANGGAL'], format='%d/%m/%Y').dt.date
        
        # Konversi kolom numerik, ganti koma jika ada dan handle error
        numeric_cols = [
            'PSM Target', 'PSM Actual', 'PSM ACV', 'BOBOT PSM', 'SCORE PSM',
            'PWP Target', 'PWP Actual', 'PWP ACV', 'BOBOT PWP', 'SCORE PWP',
            'SG Target', 'SG Actual', 'SG ACV', 'BOBOT SG', 'SCORE SG',
            'APC Target', 'APC Actual', 'APC ACV', 'BOBOT APC', 'SCORE APC',
            'TARGET TEBUS 2500', 'ACTUAL TEBUS 2500', 'ACV TEBUS 2500',
            'TOTAL SCORE PPSA', 'JHK'
        ]
        for col in numeric_cols:
            if col in df.columns:
                df[col] = df[col].astype(str).str.replace(',', '').str.replace('.', '', regex=False) # Hapus koma/titik
                df[col] = pd.to_numeric(df[col], errors='coerce').fillna(0)

        return df
    except Exception as e:
        st.error(f"Gagal memuat data dari Google Sheets: {e}")
        return pd.DataFrame()

# --- Fungsi untuk Mendapatkan Insight dari Gemini AI ---
def get_gemini_insight(summary_data):
    try:
        genai.configure(api_key=st.secrets["gemini_api"]["api_key"])
        model = genai.GenerativeModel('gemini-1.5-flash')
        
        prompt = f"""
        Anda adalah analis data bisnis yang ahli. Berdasarkan ringkasan data berikut, berikan insight atau analisis singkat (maksimal 3 kalimat) dalam bahasa Indonesia.
        Fokus pada pencapaian, tantangan, atau area yang perlu diperhatikan.
        
        Ringkasan Data:
        {summary_data}
        """
        response = model.generate_content(prompt)
        return response.text
    except Exception as e:
        return f"Tidak dapat mengambil insight dari AI: {e}"

# --- CSS untuk Styling Mirip Screenshot ---
def local_css(file_name):
    with open(file_name) as f:
        st.markdown(f'<style>{f.read()}</style>', unsafe_allow_html=True)

# Kita akan masukkan CSS langsung ke dalam string untuk kemudahan
st.markdown("""
<style>
/* Warna Latar dan Font */
.stApp {
    background-color: #0E1117;
    color: white;
}
/* Header */
.main .block-container {
    padding-top: 2rem;
    padding-bottom: 2rem;
    max-width: 1200px;
}
/* Metric Card */
div[data-testid="metric-container"] {
    background-color: #262730;
    border: 1px solid #3A3B47;
    padding: 15px;
    border-radius: 10px;
    box-shadow: 0 4px 6px rgba(0,0,0,0.1);
}
div[data-testid="metric-container"] > label {
    color: #B0B3B8;
    font-size: 14px;
}
div[data-testid="metric-container"] > div[data-testid="stMetricValue"] {
    color: #FFFFFF;
    font-size: 28px;
    font-weight: bold;
}
/* Sidebar */
.css-1d391kg {
    background-color: #262730;
}
/* Table */
.stDataFrame {
    background-color: #262730;
    border-radius: 10px;
}
</style>
""", unsafe_allow_html=True)


# --- Sidebar untuk Filter ---
st.sidebar.title("📊 Filter Data")
df = load_data_from_gsheet()

if not df.empty:
    # Filter Tanggal
    min_date = df['TANGGAL'].min()
    max_date = df['TANGGAL'].max()
    selected_dates = st.sidebar.date_input(
        "Pilih Rentang Tanggal",
        value=[min_date, max_date],
        min_value=min_date,
        max_value=max_date
    )

    # Filter Shift
    all_shifts = ['Semua'] + sorted(df['SHIFT'].unique().tolist())
    selected_shift = st.sidebar.selectbox("Pilih Shift", all_shifts)

    # Terapkan Filter
    start_date, end_date = selected_dates
    filtered_df = df[(df['TANGGAL'] >= start_date) & (df['TANGGAL'] <= end_date)]

    if selected_shift != 'Semua':
        filtered_df = filtered_df[filtered_df['SHIFT'] == selected_shift]

    # --- Header Dashboard ---
    st.title("PPSA 2GC6 BAROS PANDEGLANG")
    st.markdown("---")

    # --- Bagian 1: Metrik Utama ---
    st.subheader("📈 Metrik Utama")
    col1, col2, col3, col4 = st.columns(4)
    
    # Hitung total actual untuk setiap metrik
    total_psm = filtered_df['PSM Actual'].sum()
    total_pwp = filtered_df['PWP Actual'].sum()
    total_sg = filtered_df['SG Actual'].sum()
    total_apc = filtered_df['APC Actual'].sum()

    with col1:
        st.metric("PSM Actual", f"{total_psm:,.0f}".replace(',', '.'))
    with col2:
        st.metric("PWP Actual", f"{total_pwp:,.0f}".replace(',', '.'))
    with col3:
        st.metric("SG Actual", f"{total_sg:,.0f}".replace(',', '.'))
    with col4:
        st.metric("APC Actual", f"{total_apc:,.0f}".replace(',', '.'))

    st.markdown("---")

    # --- Bagian 2: Grafik ---
    st.subheader("📉 Visualisasi Data")
    col_g1, col_g2 = st.columns(2)

    with col_g1:
        st.markdown("**Tren Total Score PPSA per Hari**")
        # Siapkan data untuk grafik garis
        trend_data = filtered_df.groupby('TANGGAL')['TOTAL SCORE PPSA'].sum().reset_index()
        fig_line = px.line(
            trend_data, 
            x='TANGGAL', 
            y='TOTAL SCORE PPSA', 
            title='Tren Skor PPSA',
            labels={'TANGGAL': 'Tanggal', 'TOTAL SCORE PPSA': 'Total Skor'},
            markers=True
        )
        fig_line.update_layout(template='plotly_dark')
        st.plotly_chart(fig_line, use_container_width=True)

    with col_g2:
        st.markdown("**Distribusi Total Score per Shift**")
        # Siapkan data untuk grafik pie
        pie_data = filtered_df.groupby('SHIFT')['TOTAL SCORE PPSA'].sum().reset_index()
        fig_pie = px.pie(
            pie_data, 
            values='TOTAL SCORE PPSA', 
            names='SHIFT', 
            title='Kontribusi Skor per Shift',
            hole=0.3
        )
        fig_pie.update_layout(template='plotly_dark')
        st.plotly_chart(fig_pie, use_container_width=True)

    st.markdown("---")

    # --- Bagian 3: Tabel Detail ---
    st.subheader("📋 Tabel Detail")
    col_t1, col_t2 = st.columns(2)

    with col_t1:
        st.markdown("**PPSA per Shift**")
        # Tabel PPSA per shift
        table_shift = filtered_df.groupby('SHIFT').agg(
            {
                'PSM Actual': 'sum',
                'PWP Actual': 'sum',
                'SG Actual': 'sum',
                'APC Actual': 'sum',
                'TOTAL SCORE PPSA': 'sum'
            }
        ).reset_index()
        st.dataframe(table_shift, use_container_width=True)

    with col_t2:
        st.markdown("**PPSA & Tebus 2500**")
        # Tabel PPSA & Tebus
        table_tebus = filtered_df[['SHIFT', 'TARGET TEBUS 2500', 'ACTUAL TEBUS 2500', 'TOTAL SCORE PPSA']].groupby('SHIFT').sum().reset_index()
        st.dataframe(table_tebus, use_container_width=True)

    st.markdown("---")

    # --- Bagian 4: Insight dari AI ---
    st.subheader("🤖 Insight dari Gemini AI")
    
    # Buat ringkasan data untuk dikirim ke AI
    summary = f"""
    Periode: {start_date} hingga {end_date}
    Shift: {selected_shift}
    Total PSM Actual: {total_psm}
    Total PWP Actual: {total_pwp}
    Total SG Actual: {total_sg}
    Total APC Actual: {total_apc}
    Total Skor PPSA: {filtered_df['TOTAL SCORE PPSA'].sum()}
    """
    
    with st.spinner("Sedang menghasilkan insight..."):
        insight = get_gemini_insight(summary)
    
    st.info(insight)

else:
    st.warning("Tidak dapat memuat data. Silakan periksa koneksi dan konfigurasi Google Sheets Anda.")
