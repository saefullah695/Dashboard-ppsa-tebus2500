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
    """Memuat dan membersihkan data mentah dari Google Sheets."""
    if debug_mode:
        st.info("🔍 **DEBUG MODE AKTIF**")
        st.write("1. Mencoba menghubungkan ke Google Sheets...")
    
    try:
        scope = ["https://www.googleapis.com/auth/spreadsheets", "https://www.googleapis.com/auth/drive"]
        creds = Credentials.from_service_account_info(st.secrets["gcp_service_account"], scopes=scope)
        client = gspread.authorize(creds)
        
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
            st.error(f"❌ **Error Validasi Kolom:** Kolom berikut tidak ditemukan: {', '.join(missing_cols)}.")
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
        
        if debug_mode:
            st.success("   ✅ Data mentah berhasil dimuat dan dibersihkan.")
        
        return df

    except Exception as e:
        st.error(f"❌ **Error Tak Terduga:** {e}")
        return pd.DataFrame()

# --- FUNGSI BARU: Perhitungan Skor Berdasarkan Agregasi ---
def calculate_aggregated_scores(df, group_by_col='SHIFT'):
    """
    Menghitung skor PPSA berdasarkan agregasi data terlebih dahulu.
    """
    # --- Langkah 1: Agregasi Data ---
    agg_rules = {
        'PSM Target': 'sum',
        'PSM Actual': 'sum',
        'PWP Target': 'sum',
        'PWP Actual': 'sum',
        'SG Target': 'sum',
        'SG Actual': 'sum',
        'APC Target': 'mean', # Rata-rata untuk APC
        'APC Actual': 'mean', # Rata-rata untuk APC
        'TARGET TEBUS 2500': 'sum',
        'ACTUAL TEBUS 2500': 'sum'
    }
    aggregated_df = df.groupby(group_by_col).agg(agg_rules).reset_index()

    # --- Langkah 2: Hitung ACV dan Skor Akhir ---
    # Definisi Bobot
    bobot = {'PSM': 0.20, 'PWP': 0.25, 'SG': 0.30, 'APC': 0.25}

    for metric in ['PSM', 'PWP', 'SG', 'APC']:
        target_col = f'{metric} Target'
        actual_col = f'{metric} Actual'
        acv_col = f'{metric} ACV'
        score_col = f'SCORE {metric}'

        # Hitung ACV, hindari pembagian dengan nol
        aggregated_df[acv_col] = aggregated_df.apply(
            lambda row: (row[actual_col] / row[target_col] * 100) if row[target_col] > 0 else 0, axis=1
        )
        # Batasi ACV maksimal 100
        aggregated_df[acv_col] = aggregated_df[acv_col].apply(lambda x: min(x, 100))
        # Hitung skor berdasarkan bobot
        aggregated_df[score_col] = aggregated_df[acv_col] * bobot[metric]

    # --- Langkah 3: Hitung Total Skor PPSA ---
    score_cols = [f'SCORE {m}' for m in bobot.keys()]
    aggregated_df['TOTAL SCORE PPSA'] = aggregated_df[score_cols].sum(axis=1)

    return aggregated_df


# --- Fungsi untuk Mendapatkan Insight dari Gemini AI ---
def get_gemini_insight(data_summary, debug_mode=False):
    """Menghasilkan insight dari Gemini AI."""
    if debug_mode:
        st.write("Meminta insight ke Gemini AI...")
    try:
        genai.configure(api_key=st.secrets["gemini_api"]["api_key"])
        model = genai.GenerativeModel('gemini-1.5-flash')
        prompt = f"Anda adalah analis data bisnis. Berdasarkan ringkasan berikut, berikan insight singkat (maks 3 kalimat) dalam bahasa Indonesia. Fokus pada pencapaian target. Ringkasan: {data_summary}"
        response = model.generate_content(prompt)
        return response.text
    except Exception as e:
        st.error(f"❌ **Error AI:** Tidak dapat mengambil insight. Detail: {e}")
        return f"Tidak dapat mengambil insight dari AI."

# --- Sidebar untuk Filter ---
st.sidebar.title("⚙️ Filter Data")
debug_mode = st.sidebar.checkbox("🔍 Aktifkan Debug Mode", help="Tampilkan log detail untuk mencari error")

SHEET_NAME = "PesanOtomatis" 
WORKSHEET_NAME = "Data"

# --- Load Data Mentah ---
raw_df = load_data(SHEET_NAME, WORKSHEET_NAME, debug_mode)

if not raw_df.empty:
    # --- Filter Data Mentah ---
    min_date = raw_df['TANGGAL'].min()
    max_date = raw_df['TANGGAL'].max()
    selected_dates = st.sidebar.date_input("Pilih Rentang Tanggal", [min_date, max_date], min_value=min_date, max_value=max_date)
    all_shifts = ['Semua'] + sorted(raw_df['SHIFT'].unique().tolist())
    selected_shift = st.sidebar.selectbox("Pilih Shift", all_shifts)

    if len(selected_dates) == 2:
        start_date, end_date = selected_dates
        filtered_df = raw_df[(raw_df['TANGGAL'] >= start_date) & (raw_df['TANGGAL'] <= end_date)]
    else:
        filtered_df = raw_df[raw_df['TANGGAL'] == selected_dates[0]]

    if selected_shift != 'Semua':
        filtered_df = filtered_df[filtered_df['SHIFT'] == selected_shift]
    
    # --- Hitung Skor Berdasarkan Data yang Sudah Difilter ---
    # Jika "Semua" shift dipilih, kita hitung per shift. Jika satu shift dipilih, kita hitung total untuk shift tersebut.
    if selected_shift == 'Semua':
        scores_df = calculate_aggregated_scores(filtered_df, group_by_col='SHIFT')
    else:
        # Jika hanya satu shift, kita perlakukan seluruh data sebagai satu grup untuk mendapatkan total skor
        scores_df = calculate_aggregated_scores(filtered_df, group_by_col='SHIFT')


    # --- Header Dashboard ---
    st.title("PPSA 2GC6 BAROS PANDEGLANG")
    st.markdown("---")

    # --- Bagian 1: Metrik Utama (dari total data yang difilter) ---
    st.subheader("📈 Metrik Utama (Total)")
    total_psm_actual = filtered_df['PSM Actual'].sum()
    total_pwp_actual = filtered_df['PWP Actual'].sum()
    total_sg_actual = filtered_df['SG Actual'].sum()
    avg_apc_actual = filtered_df['APC Actual'].mean()

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
    
    # --- Bagian 2: Tabel Skor PPSA (Ini adalah bagian terpenting) ---
    st.subheader("📊 Tabel Skor PPSA per Shift")
    # Pilih kolom yang ingin ditampilkan
    display_cols = [
        'SHIFT', 'PSM ACV', 'SCORE PSM', 'PWP ACV', 'SCORE PWP', 
        'SG ACV', 'SCORE SG', 'APC ACV', 'SCORE APC', 'TOTAL SCORE PPSA'
    ]
    st.dataframe(scores_df[display_cols], use_container_width=True, hide_index=True)

    st.markdown("---")

    # --- Bagian 3: Grafik ---
    st.subheader("📉 Visualisasi Data")
    col_g1, col_g2 = st.columns(2)
    with col_g1:
        st.markdown("**Perbandingan Total Skor per Shift**")
        fig_bar = px.bar(scores_df, x='SHIFT', y='TOTAL SCORE PPSA', template='plotly_dark', title='Total Skor PPSA')
        st.plotly_chart(fig_bar, use_container_width=True)
    with col_g2:
        st.markdown("**Kontribusi Skor per Shift**")
        fig_pie = px.pie(scores_df, values='TOTAL SCORE PPSA', names='SHIFT', hole=0.4, template='plotly_dark', title='Total Skor PPSA')
        st.plotly_chart(fig_pie, use_container_width=True)
    
    st.markdown("---")
    
    # --- Bagian 4: Insight dari AI ---
    st.subheader("🤖 Insight dari Gemini AI")
    # Gunakan total skor dari keseluruhan data yang difilter untuk insight
    total_score_for_insight = scores_df['TOTAL SCORE PPSA'].sum()
    summary = f"Periode: {start_date} hingga {end_date}. Total PSM: {total_psm_actual}, Total PWP: {total_pwp_actual}, Total SG: {total_sg_actual}, Rata-rata APC: {avg_apc_actual}. Total Skor PPSA keseluruhan adalah {total_score_for_insight:.2f}."
    with st.spinner("Sedang menganalisis data..."):
        insight = get_gemini_insight(summary, debug_mode)
    st.info(insight)

else:
    st.warning("Dashboard tidak dapat menampilkan data. Silakan aktifkan 'Debug Mode' di sidebar untuk melihat detail error.")
