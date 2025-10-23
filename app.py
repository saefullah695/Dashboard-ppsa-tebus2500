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
    border-left: 5px solid #3A3B47;
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
.metric-psm { border-left-color: #1f77b4; }
.metric-pwp { border-left-color: #2ca02c; }
.metric-sg { border-left-color: #ff7f0e; }
.metric-apc { border-left-color: #d62728; }
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
@st.cache_data(ttl=600)
def load_data(sheet_name, worksheet_name, debug_mode=False):
    """Memuat dan memproses data, termasuk menghitung skor PPSA."""
    if debug_mode:
        st.info("🔍 **DEBUG MODE AKTIF**")
        st.write("1. Mencoba menghubungkan ke Google Sheets...")
    
    try:
        scope = ["https://www.googleapis.com/auth/spreadsheets", "https://www.googleapis.com/auth/drive"]
        creds = Credentials.from_service_account_info(st.secrets["gcp_service_account"], scopes=scope)
        client = gspread.authorize(creds)
        
        if debug_mode:
            st.success("   ✅ Koneksi ke Google Cloud berhasil.")
            st.write(f"2. Mencoba membuka spreadsheet: '{sheet_name}'...")

        spreadsheet = client.open(sheet_name)
        worksheet = spreadsheet.worksheet(worksheet_name)
        data = worksheet.get_all_records()
        df = pd.DataFrame(data)

        if debug_mode:
            st.success(f"   ✅ Spreadsheet dan worksheet '{worksheet_name}' ditemukan.")
            st.write("3. Memproses data...")

        # --- Validasi Kolom Wajib ---
        required_cols = ['TANGGAL', 'SHIFT', 'PSM Target', 'PSM Actual', 'PWP Target', 'PWP Actual', 'SG Target', 'SG Actual', 'APC Target', 'APC Actual']
        if not all(col in df.columns for col in required_cols):
            missing_cols = [col for col in required_cols if col not in df.columns]
            st.error(f"❌ **Error Validasi Kolom:** Kolom berikut tidak ditemukan: {', '.join(missing_cols)}. Periksa ejaan header di Google Sheet Anda.")
            return pd.DataFrame()

        # --- Preprocessing Data ---
        df['TANGGAL'] = pd.to_datetime(df['TANGGAL'], format='%d/%m/%Y', errors='coerce').dt.date
        df.dropna(subset=['TANGGAL'], inplace=True)

        numeric_cols = [
            'PSM Target', 'PSM Actual', 'PWP Target', 'PWP Actual', 'SG Target', 'SG Actual',
            'APC Target', 'APC Actual', 'TARGET TEBUS 2500', 'ACTUAL TEBUS 2500'
        ]
        for col in numeric_cols:
            if col in df.columns:
                df[col] = df[col].astype(str).str.replace('.', '', regex=False).str.replace(',', '', regex=False)
                df[col] = pd.to_numeric(df[col], errors='coerce').fillna(0)
        
        # --- Perhitungan Skor PPSA Berdasarkan Bobot ---
        # Definisi Bobot
        bobot_psm = 0.20
        bobot_pwp = 0.25
        bobot_sg = 0.30
        bobot_apc = 0.25

        # Fungsi helper untuk menghitung achievement (ACV)
        def hitung_acv(actual, target):
            if target == 0:
                return 0
            acv = (actual / target) * 100
            # PERBAIKAN: Menggunakan min() sebagai pengganti .clip()
            return min(acv, 100)

        # Hitung ACV untuk setiap metrik
        df['PSM ACV'] = df.apply(lambda row: hitung_acv(row['PSM Actual'], row['PSM Target']), axis=1)
        df['PWP ACV'] = df.apply(lambda row: hitung_acv(row['PWP Actual'], row['PWP Target']), axis=1)
        df['SG ACV'] = df.apply(lambda row: hitung_acv(row['SG Actual'], row['SG Target']), axis=1)
        df['APC ACV'] = df.apply(lambda row: hitung_acv(row['APC Actual'], row['APC Target']), axis=1)

        # Hitung skor per komponen
        df['SCORE PSM'] = df['PSM ACV'] * bobot_psm
        df['SCORE PWP'] = df['PWP ACV'] * bobot_pwp
        df['SCORE SG'] = df['SG ACV'] * bobot_sg
        df['SCORE APC'] = df['APC ACV'] * bobot_apc

        # Hitung Total Skor PPSA
        df['TOTAL SCORE PPSA'] = df['SCORE PSM'] + df['SCORE PWP'] + df['SCORE SG'] + df['SCORE APC']

        if debug_mode:
            st.success("   ✅ Data berhasil diproses dan skor PPSA dihitung.")
            st.write("   - 5 baris pertama data setelah perhitungan:")
            st.dataframe(df.head())
        
        return df

    except Exception as e:
        st.error(f"❌ **Error Tak Terduga:** {e}")
        return pd.DataFrame()

# --- Fungsi untuk Mendapatkan Insight dari Gemini AI ---
def get_gemini_insight(data_summary, debug_mode=False):
    """Menghasilkan insight dari Gemini AI."""
    if debug_mode:
        st.write("4. Meminta insight ke Gemini AI...")
    try:
        genai.configure(api_key=st.secrets["gemini_api"]["api_key"])
        model = genai.GenerativeModel('gemini-1.5-flash')
        prompt = f"Anda adalah analis data bisnis. Berdasarkan ringkasan berikut, berikan insight singkat (maks 3 kalimat) dalam bahasa Indonesia. Fokus pada pencapaian target. Ringkasan: {data_summary}"
        response = model.generate_content(prompt)
        if debug_mode:
            st.success("   ✅ Berhasil mendapat insight dari AI.")
        return response.text
    except Exception as e:
        st.error(f"❌ **Error AI:** Tidak dapat mengambil insight. Periksa API Key Gemini. Detail: {e}")
        return f"Tidak dapat mengambil insight dari AI."

# --- Sidebar untuk Filter ---
st.sidebar.title("⚙️ Filter Data")
debug_mode = st.sidebar.checkbox("🔍 Aktifkan Debug Mode", help="Tampilkan log detail untuk mencari error")

SHEET_NAME = "PesanOtomatis" 
WORKSHEET_NAME = "Data"

df = load_data(SHEET_NAME, WORKSHEET_NAME, debug_mode)

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

    # --- Bagian 1: Metrik Utama ---
    st.subheader("📈 Metrik Utama")
    total_psm_actual = filtered_df['PSM Actual'].sum()
    total_pwp_actual = filtered_df['PWP Actual'].sum()
    total_sg_actual = filtered_df['SG Actual'].sum()
    avg_apc_actual = filtered_df['APC Actual'].mean()

    # Fungsi helper untuk memformat angka
    def format_number(num):
        return f"{num:,.0f}".replace(",", ".")

    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.markdown(f'<div class="metric-card metric-psm"><div class="metric-label">PSM</div><div class="metric-value">{format_number(total_psm_actual)}</div></div>', unsafe_allow_html=True)
    with col2:
        st.markdown(f'<div class="metric-card metric-pwp"><div class="metric-label">PWP</div><div class="metric-value">{format_number(total_pwp_actual)}</div></div>', unsafe_allow_html=True)
    with col3:
        st.markdown(f'<div class="metric-card metric-sg"><div class="metric-label">SG</div><div class="metric-value">{format_number(total_sg_actual)}</div></div>', unsafe_allow_html=True)
    with col4:
        st.markdown(f'<div class="metric-card metric-apc"><div class="metric-label">APC (Rata-rata)</div><div class="metric-value">{format_number(avg_apc_actual)}</div></div>', unsafe_allow_html=True)

    st.markdown("---")
    
    # --- Bagian 2: Grafik ---
    st.subheader("📉 Visualisasi Data")
    col_g1, col_g2 = st.columns(2)
    with col_g1:
        st.markdown("**Tren Total Score PPSA per Hari**")
        trend_data = filtered_df.groupby('TANGGAL')['TOTAL SCORE PPSA'].sum().reset_index()
        fig_line = px.line(trend_data, x='TANGGAL', y='TOTAL SCORE PPSA', markers=True, template='plotly_dark')
        st.plotly_chart(fig_line, use_container_width=True)
    with col_g2:
        st.markdown("**Distribusi Skor per Shift**")
        pie_data = filtered_df.groupby('SHIFT')['TOTAL SCORE PPSA'].sum().reset_index()
        fig_pie = px.pie(pie_data, values='TOTAL SCORE PPSA', names='SHIFT', hole=0.4, template='plotly_dark')
        st.plotly_chart(fig_pie, use_container_width=True)
    
    st.markdown("---")
    
    # --- Bagian 3: Tabel Detail ---
    st.subheader("📋 Tabel Detail")
    col_t1, col_t2 = st.columns(2)
    with col_t1:
        st.markdown("**PPSA per Shift**")
        table_shift = filtered_df.groupby('SHIFT').agg(
            PSM_Actual=('PSM Actual', 'sum'),
            PWP_Actual=('PWP Actual', 'sum'),
            SG_Actual=('SG Actual', 'sum'),
            APC_Actual=('APC Actual', 'mean'),
            Total_Score_PPSA=('TOTAL SCORE PPSA', 'sum')
        ).reset_index()
        st.dataframe(table_shift, use_container_width=True, hide_index=True)
    with col_t2:
        st.markdown("**PPSA & Tebus 2500**")
        table_tebus = filtered_df.groupby('SHIFT')[['TARGET TEBUS 2500', 'ACTUAL TEBUS 2500', 'TOTAL SCORE PPSA']].sum().reset_index()
        st.dataframe(table_tebus, use_container_width=True, hide_index=True)

    st.markdown("---")

    # --- Tambahkan Tabel Detail Skor ---
    with st.expander("🔢 Lihat Detail Perhitungan Skor"):
        st.markdown("**Tabel Detail Skor per Komponen**")
        detail_cols = ['SHIFT', 'PSM ACV', 'SCORE PSM', 'PWP ACV', 'SCORE PWP', 'SG ACV', 'SCORE SG', 'APC ACV', 'SCORE APC', 'TOTAL SCORE PPSA']
        st.dataframe(filtered_df[detail_cols], use_container_width=True, hide_index=True)

    # --- Bagian 4: Insight dari AI ---
    st.subheader("🤖 Insight dari Gemini AI")
    summary = f"Periode: {start_date} hingga {end_date}, Shift: {selected_shift}. PSM Total: {total_psm_actual}, PWP Total: {total_pwp_actual}, SG Total: {total_sg_actual}, APC Rata-rata: {avg_apc_actual}."
    with st.spinner("Sedang menganalisis data..."):
        insight = get_gemini_insight(summary, debug_mode)
    st.info(insight)

else:
    st.warning("Dashboard tidak dapat menampilkan data. Silakan aktifkan 'Debug Mode' di sidebar untuk melihat detail error.")
