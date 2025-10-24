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

# --- CSS KUSTOM UNTUK TAMPILAN MODERN ---
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap');

/* Reset dan Font Global */
* {
    font-family: 'Inter', -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif;
}

.stApp {
    background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
    background-attachment: fixed;
}

/* Container Utama */
.main .block-container {
    padding-top: 2rem;
    padding-bottom: 2rem;
    max-width: 1400px;
}

/* Header Dashboard */
.dashboard-header {
    background: linear-gradient(135deg, #ffffff 0%, #f8f9ff 100%);
    padding: 2.5rem;
    border-radius: 20px;
    box-shadow: 0 10px 40px rgba(0, 0, 0, 0.1);
    margin-bottom: 2rem;
    border: 1px solid rgba(255, 255, 255, 0.3);
}

.main-title {
    font-size: 3rem;
    background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
    background-clip: text;
    font-weight: 800;
    text-align: center;
    margin-bottom: 0.5rem;
    letter-spacing: -0.5px;
}

.subtitle {
    text-align: center;
    color: #64748b;
    font-size: 1.1rem;
    font-weight: 400;
    line-height: 1.6;
    max-width: 800px;
    margin: 0 auto;
}

/* Metric Cards */
.metric-card {
    background: linear-gradient(135deg, #ffffff 0%, #f8f9ff 100%);
    border-radius: 16px;
    padding: 1.5rem;
    box-shadow: 0 4px 20px rgba(0, 0, 0, 0.08);
    border: 1px solid rgba(102, 126, 234, 0.1);
    transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
    position: relative;
    overflow: hidden;
}

.metric-card::before {
    content: '';
    position: absolute;
    top: 0;
    left: 0;
    width: 4px;
    height: 100%;
    background: linear-gradient(180deg, #667eea 0%, #764ba2 100%);
}

.metric-card:hover {
    transform: translateY(-8px);
    box-shadow: 0 12px 40px rgba(102, 126, 234, 0.25);
}

.metric-label {
    font-size: 0.875rem;
    color: #64748b;
    font-weight: 600;
    text-transform: uppercase;
    letter-spacing: 0.5px;
    margin-bottom: 0.5rem;
}

.metric-value {
    font-size: 2.5rem;
    font-weight: 700;
    background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
    background-clip: text;
    line-height: 1.2;
}

/* Total PPSA Card - Special */
.total-ppsa-card {
    background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
    border-radius: 20px;
    padding: 3rem 2rem;
    box-shadow: 0 20px 60px rgba(102, 126, 234, 0.4);
    text-align: center;
    position: relative;
    overflow: hidden;
}

.total-ppsa-card::before {
    content: '';
    position: absolute;
    top: -50%;
    right: -50%;
    width: 200%;
    height: 200%;
    background: radial-gradient(circle, rgba(255,255,255,0.1) 0%, transparent 70%);
    animation: pulse 3s ease-in-out infinite;
}

@keyframes pulse {
    0%, 100% { transform: scale(1); opacity: 0.5; }
    50% { transform: scale(1.1); opacity: 0.8; }
}

.total-ppsa-label {
    font-size: 1rem;
    color: rgba(255, 255, 255, 0.9);
    font-weight: 600;
    text-transform: uppercase;
    letter-spacing: 2px;
    margin-bottom: 1rem;
}

.total-ppsa-value {
    font-size: 4rem;
    font-weight: 800;
    color: #ffffff;
    text-shadow: 0 4px 20px rgba(0, 0, 0, 0.2);
    position: relative;
    z-index: 1;
}

/* Content Container */
.content-container {
    background: linear-gradient(135deg, #ffffff 0%, #f8f9ff 100%);
    padding: 2rem;
    border-radius: 20px;
    box-shadow: 0 8px 32px rgba(0, 0, 0, 0.08);
    margin-bottom: 2rem;
    border: 1px solid rgba(255, 255, 255, 0.3);
}

/* Section Headers */
.section-header {
    font-size: 1.75rem;
    font-weight: 700;
    color: #1e293b;
    margin-bottom: 1.5rem;
    padding-bottom: 0.75rem;
    border-bottom: 3px solid #667eea;
    position: relative;
}

.section-header::before {
    content: '';
    position: absolute;
    bottom: -3px;
    left: 0;
    width: 60px;
    height: 3px;
    background: #764ba2;
}

/* Sidebar Styling */
.css-1d391kg, [data-testid="stSidebar"] {
    background: linear-gradient(180deg, #ffffff 0%, #f8f9ff 100%);
    border-right: 1px solid rgba(102, 126, 234, 0.1);
}

[data-testid="stSidebar"] .element-container {
    padding: 0.5rem 0;
}

/* Buttons & Inputs */
.stButton > button {
    background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
    color: white;
    border: none;
    border-radius: 12px;
    padding: 0.75rem 2rem;
    font-weight: 600;
    transition: all 0.3s ease;
    box-shadow: 0 4px 15px rgba(102, 126, 234, 0.3);
}

.stButton > button:hover {
    transform: translateY(-2px);
    box-shadow: 0 6px 20px rgba(102, 126, 234, 0.4);
}

/* Dataframe Styling */
.stDataFrame {
    border-radius: 16px;
    overflow: hidden;
    box-shadow: 0 4px 20px rgba(0, 0, 0, 0.06);
    border: 1px solid rgba(102, 126, 234, 0.1);
}

/* Plotly Charts */
.js-plotly-plot {
    border-radius: 12px;
    overflow: hidden;
}

/* Scrollbar */
::-webkit-scrollbar {
    width: 8px;
    height: 8px;
}

::-webkit-scrollbar-track {
    background: #f1f5f9;
    border-radius: 10px;
}

::-webkit-scrollbar-thumb {
    background: linear-gradient(180deg, #667eea 0%, #764ba2 100%);
    border-radius: 10px;
}

::-webkit-scrollbar-thumb:hover {
    background: linear-gradient(180deg, #764ba2 0%, #667eea 100%);
}

/* Animations */
@keyframes fadeIn {
    from {
        opacity: 0;
        transform: translateY(20px);
    }
    to {
        opacity: 1;
        transform: translateY(0);
    }
}

.content-container {
    animation: fadeIn 0.6s ease-out;
}

/* Badge */
.status-badge {
    display: inline-block;
    padding: 0.25rem 0.75rem;
    border-radius: 12px;
    font-size: 0.75rem;
    font-weight: 600;
    text-transform: uppercase;
    letter-spacing: 0.5px;
}

.badge-success {
    background: linear-gradient(135deg, #10b981 0%, #059669 100%);
    color: white;
}

.badge-warning {
    background: linear-gradient(135deg, #f59e0b 0%, #d97706 100%);
    color: white;
}

.badge-danger {
    background: linear-gradient(135deg, #ef4444 0%, #dc2626 100%);
    color: white;
}

/* Hide Streamlit Branding */
#MainMenu {visibility: hidden;}
footer {visibility: hidden;}
header {visibility: hidden;}
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
        st.error(f"❌ Gagal mengambil data dari Google Sheets: {e}")
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
# Header Dashboard
st.markdown("""
<div class="dashboard-header">
    <h1 class="main-title">📊 Dashboard PPSA Analytics</h1>
    <p class="subtitle">
        Platform pemantauan performa komprehensif untuk indikator <strong>PPSA</strong> yang mencakup 
        <strong>PSM</strong> (Produk Spesial Mingguan), <strong>PWP</strong> (Purchase With Purchase), 
        <strong>SG</strong> (Serba Gratis), dan <strong>APC</strong> (Average Purchase Customer)
    </p>
</div>
""", unsafe_allow_html=True)

# Load dan Process Data
raw_df = load_data_from_gsheet()

if not raw_df.empty:
    processed_df = process_data(raw_df.copy())
    
    # --- SIDEBAR FILTERS ---
    with st.sidebar:
        st.markdown("### ⚙️ Pengaturan Filter")
        st.markdown("---")
        
        # Filter Kasir
        if 'NAMA KASIR' in processed_df.columns:
            st.markdown("**👤 Pilih Kasir**")
            selected_names = st.multiselect(
                "Nama Kasir:",
                options=sorted(processed_df['NAMA KASIR'].unique()),
                default=processed_df['NAMA KASIR'].unique(),
                label_visibility="collapsed"
            )
            filtered_df = processed_df[processed_df['NAMA KASIR'].isin(selected_names)]
        else:
            filtered_df = processed_df

        st.markdown("---")
        
        # Filter Tanggal
        if 'TANGGAL' in filtered_df.columns:
            filtered_df = filtered_df.dropna(subset=['TANGGAL'])
            if not filtered_df.empty:
                st.markdown("**📅 Rentang Tanggal**")
                min_date = filtered_df['TANGGAL'].min().to_pydatetime()
                max_date = filtered_df['TANGGAL'].max().to_pydatetime()
                selected_date_range = st.date_input(
                    "Pilih periode:",
                    value=[min_date, max_date],
                    min_value=min_date,
                    max_value=max_date,
                    label_visibility="collapsed"
                )
                if len(selected_date_range) == 2:
                    start_date = pd.to_datetime(selected_date_range[0])
                    end_date = pd.to_datetime(selected_date_range[1])
                    mask = (filtered_df['TANGGAL'] >= start_date) & (filtered_df['TANGGAL'] <= end_date)
                    filtered_df = filtered_df.loc[mask]
        
        st.markdown("---")
        
        # Info Summary
        st.markdown("**📊 Ringkasan Data**")
        st.info(f"**Total Record:** {len(filtered_df)}\n\n**Kasir Terpilih:** {len(selected_names) if 'selected_names' in locals() else 0}")

    # --- RINGKASAN PERFORMA KESELURUHAN ---
    st.markdown('<div class="content-container">', unsafe_allow_html=True)
    st.markdown('<h2 class="section-header">🏆 Ringkasan Performa Keseluruhan</h2>', unsafe_allow_html=True)
    
    overall_scores = calculate_overall_ppsa_breakdown(filtered_df)
    
    # Metric Cards
    col1, col2, col3, col4 = st.columns(4, gap="medium")
    
    metrics = [
        {"label": "PSM Score", "value": overall_scores['psm'], "icon": "📦", "col": col1},
        {"label": "PWP Score", "value": overall_scores['pwp'], "icon": "🛍️", "col": col2},
        {"label": "SG Score", "value": overall_scores['sg'], "icon": "🎁", "col": col3},
        {"label": "APC Score", "value": overall_scores['apc'], "icon": "💳", "col": col4}
    ]
    
    for metric in metrics:
        with metric["col"]:
            st.markdown(f"""
            <div class="metric-card">
                <div class="metric-label">{metric['icon']} {metric['label']}</div>
                <div class="metric-value">{metric['value']:.2f}</div>
            </div>
            """, unsafe_allow_html=True)
    
    st.markdown("<br>", unsafe_allow_html=True)
    
    # Total PPSA dengan Chart
    col_total, col_chart = st.columns([1, 2], gap="large")
    
    with col_total:
        st.markdown(f"""
        <div class="total-ppsa-card">
            <div class="total-ppsa-label">💰 Total PPSA Score</div>
            <div class="total-ppsa-value">{overall_scores['total']:.2f}</div>
        </div>
        """, unsafe_allow_html=True)
    
    with col_chart:
        chart_data = pd.DataFrame({
            'Komponen': ['PSM', 'PWP', 'SG', 'APC'],
            'Skor': [overall_scores['psm'], overall_scores['pwp'], overall_scores['sg'], overall_scores['apc']],
            'Target': [20, 25, 30, 25]
        })
        
        fig_overall = go.Figure()
        
        fig_overall.add_trace(go.Bar(
            name='Score Aktual',
            x=chart_data['Komponen'],
            y=chart_data['Skor'],
            marker=dict(
                color=['#667eea', '#764ba2', '#f093fb', '#4facfe'],
                line=dict(color='rgba(255, 255, 255, 0.5)', width=2)
            ),
            text=chart_data['Skor'].round(2),
            textposition='outside',
            textfont=dict(size=12, color='#1e293b', weight='bold')
        ))
        
        fig_overall.add_trace(go.Scatter(
            name='Target',
            x=chart_data['Komponen'],
            y=chart_data['Target'],
            mode='markers+lines',
            marker=dict(size=12, color='#ef4444', symbol='diamond'),
            line=dict(color='#ef4444', width=2, dash='dash')
        ))
        
        fig_overall.update_layout(
            template='plotly_white',
            height=300,
            margin=dict(l=20, r=20, t=40, b=20),
            plot_bgcolor='rgba(0,0,0,0)',
            paper_bgcolor='rgba(0,0,0,0)',
            showlegend=True,
            legend=dict(
                orientation="h",
                yanchor="bottom",
                y=1.02,
                xanchor="right",
                x=1,
                font=dict(size=11)
            ),
            xaxis=dict(
                showgrid=False,
                showline=True,
                linecolor='rgba(0,0,0,0.1)',
                title=None
            ),
            yaxis=dict(
                showgrid=True,
                gridcolor='rgba(0,0,0,0.05)',
                showline=False,
                title='Skor'
            )
        )
        
        st.plotly_chart(fig_overall, use_container_width=True)
    
    st.markdown('</div>', unsafe_allow_html=True)

    # --- DATA PERFORMA KASIR ---
    st.markdown('<div class="content-container">', unsafe_allow_html=True)
    # --- PERBAIKAN: UBAH JUDUL MENJADI RATA-RATA ---
    st.markdown('<h2 class="section-header">📈 Rata-Rata Performa Kasir</h2>', unsafe_allow_html=True)
    
    if not filtered_df.empty and 'NAMA KASIR' in filtered_df.columns:
        # --- PERBAIKAN UTAMA: UBAH .sum() MENJADI .mean() ---
        score_summary = filtered_df.groupby('NAMA KASIR')['TOTAL SCORE PPSA'].mean().sort_values(ascending=False).reset_index()
        
        # Tambah ranking
        score_summary['Ranking'] = range(1, len(score_summary) + 1)
        
        fig_kasir = go.Figure()
        
        # Warna gradient berdasarkan ranking
        colors = ['#667eea' if i < 3 else '#764ba2' if i < 5 else '#a8a8a8' 
                  for i in range(len(score_summary))]
        
        fig_kasir.add_trace(go.Bar(
            y=score_summary['NAMA KASIR'],
            x=score_summary['TOTAL SCORE PPSA'],
            orientation='h',
            marker=dict(
                color=colors,
                line=dict(color='rgba(255, 255, 255, 0.5)', width=1.5)
            ),
            text=[f"#{rank} - {score:.2f}" for rank, score in 
                  zip(score_summary['Ranking'], score_summary['TOTAL SCORE PPSA'])],
            textposition='outside',
            textfont=dict(size=11, color='#1e293b', weight='bold')
        ))
        
        fig_kasir.update_layout(
            template='plotly_white',
            height=max(400, len(score_summary) * 40),
            margin=dict(l=20, r=80, t=20, b=20),
            plot_bgcolor='rgba(0,0,0,0)',
            paper_bgcolor='rgba(0,0,0,0)',
            showlegend=False,
            # --- PERBAIKAN: UBAH JUDUL SUMBU X ---
            xaxis=dict(
                showgrid=True,
                gridcolor='rgba(0,0,0,0.05)',
                showline=False,
                title='Rata-Rata Score PPSA'
            ),
            yaxis=dict(
                showgrid=False,
                showline=False,
                categoryorder='total ascending',
                title=None
            )
        )
        
        st.plotly_chart(fig_kasir, use_container_width=True)
        
        # Top 3 Performers
        st.markdown("#### 🏅 Top 3 Performers (Berdasarkan Rata-Rata)")
        cols = st.columns(3)
        medals = ["🥇", "🥈", "🥉"]
        
        for idx, (col, medal) in enumerate(zip(cols, medals)):
            if idx < len(score_summary):
                with col:
                    st.markdown(f"""
                    <div class="metric-card" style="text-align: center;">
                        <div style="font-size: 2.5rem; margin-bottom: 0.5rem;">{medal}</div>
                        <div style="font-size: 1.1rem; font-weight: 600; color: #1e293b; margin-bottom: 0.25rem;">
                            {score_summary.iloc[idx]['NAMA KASIR']}
                        </div>
                        <div style="font-size: 1.5rem; font-weight: 700; color: #667eea;">
                            {score_summary.iloc[idx]['TOTAL SCORE PPSA']:.2f}
                        </div>
                    </div>
                    """, unsafe_allow_html=True)
    else:
        st.warning("⚠️ Tidak ada data untuk ditampilkan setelah difilter.")
    
    st.markdown('</div>', unsafe_allow_html=True)

    # --- TABEL DETAIL ---
    st.markdown('<div class="content-container">', unsafe_allow_html=True)
    st.markdown('<h2 class="section-header">📋 Data Detail & Perhitungan</h2>', unsafe_allow_html=True)
    
    column_configuration = {
        'NAMA KASIR': st.column_config.TextColumn("👤 Nama Kasir", width="medium"),
        'TANGGAL': st.column_config.DateColumn("📅 Tanggal", format="DD/MM/YYYY", width="medium"),
        'SHIFT': st.column_config.TextColumn("⏰ Shift", width="small"),
        'PSM Target': st.column_config.NumberColumn("🎯 PSM Target", format="%.0f"),
        'PSM Actual': st.column_config.NumberColumn("✅ PSM Actual", format="%.0f"),
        'PWP Target': st.column_config.NumberColumn("🎯 PWP Target", format="%.0f"),
        'PWP Actual': st.column_config.NumberColumn("✅ PWP Actual", format="%.0f"),
        'SG Target': st.column_config.NumberColumn("🎯 SG Target", format="%.0f"),
        'SG Actual': st.column_config.NumberColumn("✅ SG Actual", format="%.0f"),
        'APC Target': st.column_config.NumberColumn("🎯 APC Target", format="%.0f"),
        'APC Actual': st.column_config.NumberColumn("✅ APC Actual", format="%.0f"),
        'TARGET TEBUS 2500': st.column_config.NumberColumn("🎯 Target Tebus", format="%.0f"),
        'ACTUAL TEBUS 2500': st.column_config.NumberColumn("✅ Actual Tebus", format="%.0f"),
        '(%) PSM ACV': st.column_config.NumberColumn("📊 ACV PSM", format="%.2f%%"),
        '(%) PWP ACV': st.column_config.NumberColumn("📊 ACV PWP", format="%.2f%%"),
        '(%) SG ACV': st.column_config.NumberColumn("📊 ACV SG", format="%.2f%%"),
        '(%) APC ACV': st.column_config.NumberColumn("📊 ACV APC", format="%.2f%%"),
        '(%) ACV TEBUS 2500': st.column_config.NumberColumn("📊 ACV Tebus", format="%.2f%%"),
        'BOBOT PSM': st.column_config.NumberColumn("⚖️ Bobot PSM", format="%.0f"),
        'BOBOT PWP': st.column_config.NumberColumn("⚖️ Bobot PWP", format="%.0f"),
        'BOBOT SG': st.column_config.NumberColumn("⚖️ Bobot SG", format="%.0f"),
        'BOBOT APC': st.column_config.NumberColumn("⚖️ Bobot APC", format="%.0f"),
        'SCORE PSM': st.column_config.NumberColumn("💯 Score PSM", format="%.2f"),
        'SCORE PWP': st.column_config.NumberColumn("💯 Score PWP", format="%.2f"),
        'SCORE SG': st.column_config.NumberColumn("💯 Score SG", format="%.2f"),
        'SCORE APC': st.column_config.NumberColumn("💯 Score APC", format="%.2f"),
        'TOTAL SCORE PPSA': st.column_config.NumberColumn("🏆 TOTAL SCORE", format="%.2f"),
    }
    
    final_column_config = {col: config for col, config in column_configuration.items() if col in filtered_df.columns}
    
    st.dataframe(
        filtered_df,
        use_container_width=True,
        column_config=final_column_config,
        hide_index=True,
        height=500
    )
    
    # Download Button
    csv = filtered_df.to_csv(index=False).encode('utf-8')
    st.download_button(
        label="📥 Download Data (CSV)",
        data=csv,
        file_name=f"ppsa_data_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
        mime="text/csv",
    )
    
    st.markdown('</div>', unsafe_allow_html=True)

else:
    st.error("❌ Tidak dapat memuat data. Silakan periksa koneksi Google Sheets Anda.")

# Footer
st.markdown("<br><br>", unsafe_allow_html=True)
st.markdown("""
<div style='text-align: center; color: rgba(255,255,255,0.7); padding: 2rem; font-size: 0.9rem;'>
    <strong>Dashboard PPSA Analytics</strong> • Powered by Streamlit • © 2025
</div>
""", unsafe_allow_html=True)
