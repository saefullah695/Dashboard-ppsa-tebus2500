import streamlit as st
import pandas as pd
import gspread
from gspread_dataframe import get_as_dataframe
from oauth2client.service_account import ServiceAccountCredentials
import plotly.express as px
import plotly.graph_objects as go
import re
from datetime import datetime
import logging

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Konfigurasi halaman
st.set_page_config(
    page_title="Dashboard PPSA Sederhana",
    page_icon="📊",
    layout="wide"
)

# CSS sederhana
st.markdown("""
<style>
.metric-card {
    background-color: #f0f2f6;
    border-radius: 10px;
    padding: 20px;
    margin-bottom: 20px;
    box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
}
.metric-value {
    font-size: 2rem;
    font-weight: bold;
    color: #1f77b4;
}
.metric-label {
    font-size: 1rem;
    color: #555;
}
</style>
""", unsafe_allow_html=True)

# Fungsi untuk format angka
def format_number(value):
    try:
        return f"{value:,.2f}"
    except (TypeError, ValueError):
        return "0.00"

def format_percentage(value):
    try:
        return f"{value:.2f}%"
    except (TypeError, ValueError):
        return "0.00%"

# Fungsi untuk mendeteksi dan mengkonversi persentase
def detect_and_convert_percentage(value):
    """
    Deteksi dan konversi berbagai format persentase ke nilai float 0-100
    Menangani format: '85%', '85.5%', '0.85', 0.85, 85, '85,5%'
    """
    if pd.isna(value):
        return 0.0
    
    # Konversi ke string dulu untuk handling yang konsisten
    value_str = str(value).strip()
    
    # Jika string kosong, kembalikan 0
    if not value_str:
        return 0.0
    
    # Deteksi format persentase
    is_percentage_format = '%' in value_str
    
    # Hapus karakter non-numerik kecuali titik dan koma
    value_str = re.sub(r'[^\d.,-]', '', value_str)
    
    # Ganti koma dengan titik untuk desimal
    value_str = value_str.replace(',', '.')
    
    # Konversi ke numeric
    try:
        numeric_value = float(value_str)
    except (ValueError, TypeError):
        logger.warning(f"Tidak dapat mengkonversi nilai '{value}' ke numerik")
        return 0.0
    
    # Jika format asli adalah persentase (%), gunakan nilai langsung
    if is_percentage_format:
        return numeric_value
    
    # Jika nilai adalah desimal (0 < nilai < 1), konversi ke persentase
    if 0 < numeric_value < 1:
        return numeric_value * 100
    
    # Jika nilai > 1, anggap sudah dalam format persentase
    return numeric_value

# Fungsi untuk memuat dan memproses data
@st.cache_data(ttl=300)
def load_and_process_data(spreadsheet_url, sheet_name):
    """
    Load dan proses data dari Google Sheets dengan pembacaan data yang benar
    """
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
        
        # Ambil data mentah tanpa evaluasi formula
        df = get_as_dataframe(worksheet, evaluate_formulas=False)
        
        # Bersihkan data
        df.dropna(axis=0, how="all", inplace=True)
        df.columns = df.columns.str.strip()
        
        # Konversi kolom tanggal
        if 'TANGGAL' in df.columns:
            df['TANGGAL'] = pd.to_datetime(df['TANGGAL'], errors='coerce', dayfirst=True)
        
        # Daftar kolom ACV yang harus dikonversi sebagai persentase
        acv_columns = [
            'PSM ACV', 'PWP ACV', 'SG ACV', 'APC ACV'
        ]
        
        # Konversi kolom ACV dengan fungsi deteksi format
        for col in acv_columns:
            if col in df.columns:
                df[col] = df[col].apply(detect_and_convert_percentage)
        
        # Konversi kolom numerik lainnya
        numeric_cols = [
            'BOBOT PSM', 'BOBOT PWP', 'BOBOT SG', 'BOBOT APC',
            'TARGET TEBUS 2500', 'ACTUAL TEBUS 2500', 'JHK'
        ]
        
        for col in numeric_cols:
            if col in df.columns:
                df[col] = df[col].astype(str).str.replace('%', '').str.replace(',', '.')
                df[col] = pd.to_numeric(df[col], errors='coerce')
        
        # Set bobot indikator sesuai yang ditentukan
        indicator_weights = {
            'PSM': 20,
            'PWP': 25,
            'SG': 30,
            'APC': 25
        }
        
        # Update bobot di dataframe
        for indicator, weight in indicator_weights.items():
            bobot_col = f'BOBOT {indicator}'
            if bobot_col in df.columns:
                df[bobot_col] = weight
        
        # Hitung score untuk setiap indikator dengan formula yang benar
        # Score = (ACV × Bobot) / 100
        for indicator in indicator_weights.keys():
            acv_col = f'{indicator} ACV'
            bobot_col = f'BOBOT {indicator}'
            score_col = f'SCORE {indicator}'
            
            if acv_col in df.columns and bobot_col in df.columns:
                # Gunakan formula yang benar
                df[score_col] = (df[acv_col] * df[bobot_col]) / 100
        
        # Hitung total score PPSA
        if all(col in df.columns for col in ['SCORE PSM', 'SCORE PWP', 'SCORE SG', 'SCORE APC']):
            df['TOTAL SCORE PPSA'] = (
                df['SCORE PSM'].fillna(0) + 
                df['SCORE PWP'].fillna(0) + 
                df['SCORE SG'].fillna(0) + 
                df['SCORE APC'].fillna(0)
            )
        
        return df
        
    except Exception as e:
        st.error(f"❌ Gagal memuat data: {str(e)}")
        logger.error(f"Error loading data: {str(e)}")
        return None

# Fungsi untuk filter data
def filter_data(df, start_date=None, end_date=None, selected_cashiers=None):
    filtered_df = df.copy()
    
    # Filter tanggal
    if start_date and end_date and 'TANGGAL' in df.columns:
        start_ts = pd.to_datetime(start_date)
        end_ts = pd.to_datetime(end_date) + pd.Timedelta(days=1)
        filtered_df = filtered_df[
            (filtered_df['TANGGAL'] >= start_ts) & 
            (filtered_df['TANGGAL'] < end_ts)
        ]
    
    # Filter kasir
    if selected_cashiers and 'NAMA KASIR' in df.columns and 'Semua' not in selected_cashiers:
        filtered_df = filtered_df[filtered_df['NAMA KASIR'].isin(selected_cashiers)]
    
    return filtered_df

# Fungsi untuk menghitung global score
def calculate_global_score(df):
    if df.empty or 'TOTAL SCORE PPSA' not in df.columns:
        return 0.0
    
    # Global score adalah rata-rata dari total score PPSA
    return df['TOTAL SCORE PPSA'].mean()

# Fungsi untuk membuat chart performa kasir
def create_cashier_performance_chart(df):
    if df.empty or 'TOTAL SCORE PPSA' not in df.columns or 'NAMA KASIR' not in df.columns:
        return go.Figure()
    
    # Group by kasir
    cashier_performance = df.groupby('NAMA KASIR')['TOTAL SCORE PPSA'].mean().reset_index()
    cashier_performance = cashier_performance.sort_values('TOTAL SCORE PPSA', ascending=True)
    
    # Buat bar chart
    fig = go.Figure(go.Bar(
        x=cashier_performance['TOTAL SCORE PPSA'],
        y=cashier_performance['NAMA KASIR'],
        orientation='h',
        marker_color='lightblue',
        text=[f"{score:.2f}" for score in cashier_performance['TOTAL SCORE PPSA']],
        textposition='auto'
    ))
    
    fig.update_layout(
        title="Performa Kasir (Total Score PPSA)",
        xaxis_title="Total Score PPSA",
        yaxis_title="Nama Kasir",
        height=max(400, len(cashier_performance) * 40)
    )
    
    return fig

# Fungsi untuk membuat chart radar PPSA
def create_ppsa_radar_chart(df):
    if df.empty:
        return go.Figure()
    
    # Hitung rata-rata ACV per indikator
    indicators = ['PSM', 'PWP', 'SG', 'APC']
    avg_values = []
    labels = []
    
    for indicator in indicators:
        acv_col = f'{indicator} ACV'
        if acv_col in df.columns:
            avg_acv = df[acv_col].mean()
            
            if not pd.isna(avg_acv):
                avg_values.append(avg_acv)
                labels.append(indicator)
    
    if not avg_values:
        return go.Figure()
    
    # Buat radar chart
    fig = go.Figure()
    
    # Data aktual
    fig.add_trace(go.Scatterpolar(
        r=avg_values,
        theta=labels,
        fill='toself',
        name='Rata-rata ACV (%)'
    ))
    
    # Target line (100%)
    target_values = [100] * len(labels)
    fig.add_trace(go.Scatterpolar(
        r=target_values,
        theta=labels,
        mode='lines',
        name='Target (100%)',
        line=dict(dash='dash')
    ))
    
    fig.update_layout(
        polar=dict(
            radialaxis=dict(
                visible=True,
                range=[0, 100]
            )
        ),
        title="Radar Performa PPSA (ACV %)"
    )
    
    return fig

# Main app
def main():
    st.title("📊 Dashboard PPSA Sederhana")
    st.markdown("Dashboard untuk monitoring performa PPSA dengan perhitungan yang benar")
    
    # Sidebar untuk input
    st.sidebar.title("Konfigurasi")
    
    # Input URL Google Sheets
    spreadsheet_url = st.sidebar.text_input(
        "Google Spreadsheet URL",
        placeholder="https://docs.google.com/spreadsheets/d/...",
        help="Masukkan URL Google Sheets"
    )
    
    # Input nama sheet
    sheet_name = st.sidebar.text_input(
        "Nama Sheet",
        value="Data",
        help="Nama sheet dalam Google Sheets"
    )
    
    # Load data
    df = None
    if spreadsheet_url and sheet_name:
        df = load_and_process_data(spreadsheet_url, sheet_name)
    
    if df is None or df.empty:
        st.warning("⚠️ Tidak dapat memuat data. Periksa URL dan nama sheet.")
        return
    
    # Filter
    st.sidebar.markdown("### Filter")
    
    # Filter tanggal
    if 'TANGGAL' in df.columns:
        min_date = df['TANGGAL'].min().date()
        max_date = df['TANGGAL'].max().date()
        
        start_date = st.sidebar.date_input("Tanggal Mulai", value=min_date, min_value=min_date, max_value=max_date)
        end_date = st.sidebar.date_input("Tanggal Akhir", value=max_date, min_value=min_date, max_value=max_date)
    else:
        start_date = None
        end_date = None
    
    # Filter kasir
    if 'NAMA KASIR' in df.columns:
        cashiers = ['Semua'] + sorted(df['NAMA KASIR'].unique().tolist())
        selected_cashiers = st.sidebar.multiselect("Pilih Kasir", options=cashiers, default=['Semua'])
    else:
        selected_cashiers = None
    
    # Apply filter
    filtered_df = filter_data(df, start_date, end_date, selected_cashiers)
    
    if filtered_df.empty:
        st.warning("⚠️ Filter yang dipilih tidak menghasilkan data")
        return
    
    # Tampilkan informasi perhitungan
    st.markdown("### 🧮 Cara Perhitungan Score (SKALA 0-100)")
    st.markdown("""
    **RUMUS:** Score = (ACV × Bobot) / 100
    
    **Contoh Perhitungan:**
    - SG ACV = 85%, Bobot SG = 30
    - Score SG = (85 × 30) / 100 = 25.5
    
    **Bobot Default:**
    - PSM: 20
    - PWP: 25
    - SG: 30
    - APC: 25
    - Total Bobot: 100
    
    **Total Score PPSA** = Score PSM + Score PWP + Score SG + Score APC
    """)
    
    # Hitung global score
    global_score = calculate_global_score(filtered_df)
    
    # Tampilkan metrik
    st.markdown("### 📊 Metrik Utama")
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.markdown("""
        <div class="metric-card">
            <div class="metric-value">{}</div>
            <div class="metric-label">Global Score PPSA</div>
        </div>
        """.format(format_number(global_score)), unsafe_allow_html=True)
    
    with col2:
        total_records = len(filtered_df)
        st.markdown("""
        <div class="metric-card">
            <div class="metric-value">{}</div>
            <div class="metric-label">Total Data</div>
        </div>
        """.format(total_records), unsafe_allow_html=True)
    
    with col3:
        if 'NAMA KASIR' in filtered_df.columns:
            unique_cashiers = filtered_df['NAMA KASIR'].nunique()
            st.markdown("""
            <div class="metric-card">
                <div class="metric-value">{}</div>
                <div class="metric-label">Jumlah Kasir</div>
            </div>
            """.format(unique_cashiers), unsafe_allow_html=True)
    
    # Tampilkan detail perhitungan
    st.markdown("### 📋 Detail Perhitungan Score")
    
    # Tampilkan 5 data teratas
    display_cols = []
    if 'NAMA KASIR' in filtered_df.columns:
        display_cols.append('NAMA KASIR')
    if 'TANGGAL' in filtered_df.columns:
        display_cols.append('TANGGAL')
    
    # Tambahkan kolom ACV
    for indicator in ['PSM', 'PWP', 'SG', 'APC']:
        acv_col = f'{indicator} ACV'
        if acv_col in filtered_df.columns:
            display_cols.append(acv_col)
    
    # Tambahkan kolom Bobot
    for indicator in ['PSM', 'PWP', 'SG', 'APC']:
        bobot_col = f'BOBOT {indicator}'
        if bobot_col in filtered_df.columns:
            display_cols.append(bobot_col)
    
    # Tambahkan kolom Score
    for indicator in ['PSM', 'PWP', 'SG', 'APC']:
        score_col = f'SCORE {indicator}'
        if score_col in filtered_df.columns:
            display_cols.append(score_col)
    
    # Tambahkan kolom Total Score
    if 'TOTAL SCORE PPSA' in filtered_df.columns:
        display_cols.append('TOTAL SCORE PPSA')
    
    if display_cols:
        # Format dataframe untuk tampilan
        display_df = filtered_df[display_cols].copy()
        
        # Format kolom tanggal
        if 'TANGGAL' in display_df.columns:
            display_df['TANGGAL'] = display_df['TANGGAL'].dt.strftime('%d/%m/%Y')
        
        # Format kolom ACV
        for indicator in ['PSM', 'PWP', 'SG', 'APC']:
            acv_col = f'{indicator} ACV'
            if acv_col in display_df.columns:
                display_df[acv_col] = display_df[acv_col].apply(lambda x: format_percentage(x))
        
        # Format kolom Score
        for indicator in ['PSM', 'PWP', 'SG', 'APC']:
            score_col = f'SCORE {indicator}'
            if score_col in display_df.columns:
                display_df[score_col] = display_df[score_col].apply(lambda x: format_number(x))
        
        # Format kolom Total Score
        if 'TOTAL SCORE PPSA' in display_df.columns:
            display_df['TOTAL SCORE PPSA'] = display_df['TOTAL SCORE PPSA'].apply(lambda x: format_number(x))
        
        st.dataframe(display_df.head(10), use_container_width=True)
    
    # Tampilkan chart
    st.markdown("### 📈 Visualisasi Data")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.plotly_chart(create_cashier_performance_chart(filtered_df), use_container_width=True)
    
    with col2:
        st.plotly_chart(create_ppsa_radar_chart(filtered_df), use_container_width=True)
    
    # Tampilkan formula perhitungan
    st.markdown("### 🧮 Detail Formula Perhitungan")
    
    # Tampilkan contoh perhitungan untuk 5 data teratas
    if not filtered_df.empty:
        example_data = filtered_df.head(5).copy()
        
        # Buat dataframe untuk menampilkan perhitungan
        calc_df = pd.DataFrame()
        
        if 'NAMA KASIR' in example_data.columns:
            calc_df['Nama Kasir'] = example_data['NAMA KASIR']
        
        for indicator in ['PSM', 'PWP', 'SG', 'APC']:
            acv_col = f'{indicator} ACV'
            bobot_col = f'BOBOT {indicator}'
            score_col = f'SCORE {indicator}'
            
            if acv_col in example_data.columns and bobot_col in example_data.columns:
                calc_df[f'{indicator} ACV'] = example_data[acv_col].apply(lambda x: f"{x:.2f}%")
                calc_df[f'{indicator} Bobot'] = example_data[bobot_col]
                
                # Tampilkan formula perhitungan
                if score_col in example_data.columns:
                    calc_df[f'{indicator} Score'] = example_data.apply(
                        lambda row: f"({row[acv_col]:.2f} × {row[bobot_col]}) / 100 = {row[score_col]:.2f}", 
                        axis=1
                    )
        
        if 'TOTAL SCORE PPSA' in example_data.columns:
            calc_df['Total Score PPSA'] = example_data['TOTAL SCORE PPSA'].apply(lambda x: f"{x:.2f}")
        
        st.dataframe(calc_df, use_container_width=True)

if __name__ == "__main__":
    main()
