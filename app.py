import streamlit as st
import pandas as pd
import gspread
from google.oauth2.service_account import Credentials
import plotly.express as px
import google.generativeai as genai
from datetime import date

# --- Konfigurasi Halaman Streamlit ---
st.set_page_config(
    page_title="PPSA Dashboard",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded"
)

# --- CSS Kustom untuk Tampilan Mirip Screenshot ---
st.markdown("""
<style>
/* Latar Belakang dan Font Utama */
.stApp {
    background-color: #0E1117;
    color: #FAFAFA;
}

/* Container Utama */
.main .block-container {
    padding-top: 1.5rem;
    padding-bottom: 1.5rem;
    max-width: 1300px;
}

/* Styling untuk Metric Card */
.metric-card {
    background-color: #262730;
    border-left: 5px solid #3A3B47; /* Warna default */
    padding: 1rem;
    border-radius: 10px;
    box-shadow: 0 4px 12px rgba(0,0,0,0.2);
    margin-bottom: 1rem;
    text-align: center;
}
.metric-card .metric-label {
    color: #B0B3B8;
    font-size: 14px;
    font-weight: 500;
}
.metric-card .metric-value {
    color: #FFFFFF;
    font-size: 32px;
    font-weight: bold;
    margin-top: 0.5rem;
}

/* Warna Spesifik untuk Setiap Metrik */
.metric-psm { border-left-color: #1f77b4; } /* Biru */
.metric-pwp { border-left-color: #2ca02c; } /* Hijau */
.metric-sg { border-left-color: #ff7f0e; }  /* Oranye */
.metric-apc { border-left-color: #d62728; } /* Merah */

/* Sidebar */
.css-1d391kg, .e8zbici2 {
    background-color: #262730;
}

/* Tabel Data */
.stDataFrame {
    background-color: #262730;
    border-radius: 10px;
    padding: 10px;
}
.stDataFrame table {
    color: #FAFAFA;
}
</style>
""", unsafe_allow_html=True)


# --- Fungsi untuk Memuat Data dari Google Sheets ---
@st.cache_data(ttl=600) # Cache selama 10 menit untuk performa
def load_data(sheet_name, worksheet_name):
    """Memuat data dari Google Sheets dengan penanganan error yang baik."""
    try:
        scope = ["https://www.googleapis.com/auth/spreadsheets", "https://www.googleapis.com/auth/drive"]
        creds = Credentials.from_service_account_info(st.secrets["gcp_service_account"], scopes=scope)
        client = gspread.authorize(creds)

        spreadsheet = client.open(sheet_name)
        worksheet = spreadsheet.worksheet(worksheet_name)
        data = worksheet.get_all_records()
        df = pd.DataFrame(data)

        # --- Validasi Kolom Wajib ---
        required_cols = ['TANGGAL', 'SHIFT', 'PSM Actual', 'PWP Actual', 'SG Actual', 'APC Actual', 'TOTAL SCORE PPSA']
        if not all(col in df.columns for col in required_cols):
            missing_cols = [col for col in required_cols if col not in df.columns]
            st.error(f"Error: Kolom berikut tidak ditemukan di worksheet: {', '.join(missing_cols)}. Periksa header di Google Sheet.")
            return pd.DataFrame()

        # --- Preprocessing Data ---
        # Konversi Tanggal
        df['TANGGAL'] = pd.to_datetime(df['TANGGAL'], format='%d/%m/%Y', errors='coerce').dt.date
        df.dropna(subset=['TANGGAL'], inplace=True) # Hapus baris dengan tanggal tidak valid

        # Konversi Kolom Numerik
        numeric_cols = [
            'PSM Target', 'PSM Actual', 'PWP Target', 'PWP Actual', 'SG Target', 'SG Actual',
            'APC Target', 'APC Actual', 'TARGET TEBUS 2500', 'ACTUAL TEBUS 2500', 'TOTAL SCORE PPSA'
        ]
        for col in numeric_cols:
            if col in df.columns:
                # Ganti koma dan titik yang bukan desimal, lalu konversi
                df[col] = df[col].astype(str).str.replace('.', '', regex=False).str.replace(',', '', regex=False)
                df[col] = pd.to_numeric(df[col], errors='coerce').fillna(0)
        
        return df

    except gspread.exceptions.SpreadsheetNotFound:
        st.error(f"Error: Spreadsheet dengan nama '{sheet_name}' tidak ditemukan. Periksa nama dan pastikan Service Account sudah di-share.")
        return pd.DataFrame()
    except gspread.exceptions.WorksheetNotFound:
        st.error(f"Error: Worksheet dengan nama '{worksheet_name}' tidak ditemukan.")
        return pd.DataFrame()
    except Exception as e:
        st.error(f"Terjadi error tak terduga saat memuat data: {e}")
        return pd.DataFrame()

# --- Fungsi untuk Mendapatkan Insight dari Gemini AI ---
def get_gemini_insight(data_summary):
    """Menghasilkan insight dari Gemini AI berdasarkan ringkasan data."""
    try:
        genai.configure(api_key=st.secrets["gemini_api"]["api_key"])
        model = genai.GenerativeModel('gemini-1.5-flash')
        
        prompt = f"""
        Anda adalah analis data bisnis untuk sebuah retail. Berdasarkan ringkasan kinerja berikut, berikan insight singkat (maksimal 3 kalimat) dalam bahasa Indonesia.
        Fokus pada pencapaian terhadap target. Jika ada yang di bawah target, sebutkan metriknya. Jika semua di atas target, berikan apresiasi.
        
        Ringkasan Data:
        {data_summary}
        """
        response = model.generate_content(prompt)
        return response.text
    except Exception as e:
        return f"Error: Tidak dapat mengambil insight dari AI. Periksa API Key Gemini. Detail: {e}"

# --- Sidebar untuk Filter ---
st.sidebar.title("⚙️ Filter Data")
# Nama spreadsheet dan worksheet sudah diperbarui
SHEET_NAME = "PesanOtomatis" 
WORKSHEET_NAME = "Data"

df = load_data(SHEET_NAME, WORKSHEET_NAME)

if not df.empty:
    # Filter Tanggal
    min_date = df['TANGGAL'].min()
    max_date = df['TANGGAL'].max()
    selected_dates = st.sidebar.date_input("Pilih Rentang Tanggal", [min_date, max_date], min_value=min_date, max_value=max_date)

    # Filter Shift
    all_shifts = ['Semua'] + sorted(df['SHIFT'].unique().tolist())
    selected_shift = st.sidebar.selectbox("Pilih Shift", all_shifts)

    # Terapkan Filter
    if len(selected_dates) == 2:
        start_date, end_date = selected_dates
        filtered_df = df[(df['TANGGAL'] >= start_date) & (df['TANGGAL'] <= end_date)]
    else:
        filtered_df = df[df['TANGGAL'] == selected_dates[0]]

    if selected_shift != 'Semua':
        filtered_df = filtered_df[filtered_df['SHIFT'] == selected_shift]

    # --- Header Dashboard ---
    st.title("PPSA 2GC6 BAROS PANDEGLANG")
    st.markdown("---")

    # --- Bagian 1: Metrik Utama dengan Warna ---
    st.subheader("📈 Metrik Utama")
    # Hitung total actual dan target
    total_psm_actual = filtered_df['PSM Actual'].sum()
    total_psm_target = filtered_df['PSM Target'].sum()
    total_pwp_actual = filtered_df['PWP Actual'].sum()
    total_pwp_target = filtered_df['PWP Target'].sum()
    total_sg_actual = filtered_df['SG Actual'].sum()
    total_sg_target = filtered_df['SG Target'].sum()
    total_apc_actual = filtered_df['APC Actual'].sum()
    total_apc_target = filtered_df['APC Target'].sum()

    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.markdown(f"""
        <div class="metric-card metric-psm">
            <div class="metric-label">PSM</div>
            <div class="metric-value">{total_psm_actual:,.0f}".replace(",", ".")</div>
        </div>
        """, unsafe_allow_html=True)
    with col2:
        st.markdown(f"""
        <div class="metric-card metric-pwp">
            <div class="metric-label">PWP</div>
            <div class="metric-value">{total_pwp_actual:,.0f}".replace(",", ".")</div>
        </div>
        """, unsafe_allow_html=True)
    with col3:
        st.markdown(f"""
        <div class="metric-card metric-sg">
            <div class="metric-label">SG</div>
            <div class="metric-value">{total_sg_actual:,.0f}".replace(",", ".")</div>
        </div>
        """, unsafe_allow_html=True)
    with col4:
        st.markdown(f"""
        <div class="metric-card metric-apc">
            <div class="metric-label">APC</div>
            <div class="metric-value">{total_apc_actual:,.0f}".replace(",", ".")</div>
        </div>
        """, unsafe_allow_html=True)

    st.markdown("---")

    # --- Bagian 2: Grafik ---
    st.subheader("📉 Visualisasi Data")
    col_g1, col_g2 = st.columns(2)

    with col_g1:
        st.markdown("**Tren Total Score PPSA per Hari**")
        trend_data = filtered_df.groupby('TANGGAL')['TOTAL SCORE PPSA'].sum().reset_index()
        fig_line = px.line(trend_data, x='TANGGAL', y='TOTAL SCORE PPSA', markers=True, template='plotly_dark')
        fig_line.update_layout(legend_title_text='', xaxis_title='Tanggal', yaxis_title='Total Skor')
        st.plotly_chart(fig_line, use_container_width=True)

    with col_g2:
        st.markdown("**Distribusi Skor per Shift**")
        pie_data = filtered_df.groupby('SHIFT')['TOTAL SCORE PPSA'].sum().reset_index()
        fig_pie = px.pie(pie_data, values='TOTAL SCORE PPSA', names='SHIFT', hole=0.4, template='plotly_dark')
        fig_pie.update_layout(legend_title_text='Shift')
        st.plotly_chart(fig_pie, use_container_width=True)

    st.markdown("---")

    # --- Bagian 3: Tabel Detail ---
    st.subheader("📋 Tabel Detail")
    col_t1, col_t2 = st.columns(2)
    with col_t1:
        st.markdown("**PPSA per Shift**")
        table_shift = filtered_df.groupby('SHIFT')[['PSM Actual', 'PWP Actual', 'SG Actual', 'APC Actual', 'TOTAL SCORE PPSA']].sum().reset_index()
        st.dataframe(table_shift, use_container_width=True, hide_index=True)
    with col_t2:
        st.markdown("**PPSA & Tebus 2500**")
        table_tebus = filtered_df.groupby('SHIFT')[['TARGET TEBUS 2500', 'ACTUAL TEBUS 2500', 'TOTAL SCORE PPSA']].sum().reset_index()
        st.dataframe(table_tebus, use_container_width=True, hide_index=True)

    st.markdown("---")

    # --- Bagian 4: Insight dari AI ---
    st.subheader("🤖 Insight dari Gemini AI")
    summary = f"""
    - Periode: {start_date} hingga {end_date}
    - Shift: {selected_shift}
    - PSM: Actual {total_psm_actual} dari Target {total_psm_target}
    - PWP: Actual {total_pwp_actual} dari Target {total_pwp_target}
    - SG: Actual {total_sg_actual} dari Target {total_sg_target}
    - APC: Actual {total_apc_actual} dari Target {total_apc_target}
    """
    
    with st.spinner("Sedang menganalisis data..."):
        insight = get_gemini_insight(summary)
    
    st.info(insight)

else:
    st.warning("Dashboard tidak dapat menampilkan data. Silakan periksa konfigurasi di sidebar dan file `secrets.toml`.")
