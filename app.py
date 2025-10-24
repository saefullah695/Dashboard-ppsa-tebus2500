import streamlit as st
import pandas as pd
import plotly.express as px
import gspread
from google.oauth2.service_account import Credentials

# --- Konfigurasi koneksi ke Google Sheet (PAKAI cara kamu yang sudah jalan) ---
scope = ["https://spreadsheets.google.com/feeds",
         "https://www.googleapis.com/auth/drive"]

# Gunakan secrets (AMAN di Streamlit Cloud)
creds_dict = st.secrets["gcp_service_account"]
creds = Credentials.from_service_account_info(creds_dict, scopes=scope)
client = gspread.authorize(creds)

# --- Ambil data dari sheet ---
sheet = client.open("PesanOtomatis").worksheet("Data")
data = sheet.get_all_records()
df = pd.DataFrame(data)

# --- Pastikan nama kolom konsisten (hapus spasi aneh) ---
df.columns = [c.strip().upper().replace(" ", "_") for c in df.columns]

# --- Hitung skor otomatis ---
def hitung_score(acv, bobot):
    try:
        return (float(acv) * float(bobot)) / 100
    except:
        return 0

# Bobot default PPSA
bobot = {"PSM": 20, "PWP": 25, "SG": 30, "APC": 25}

# Hitung score tiap kategori
for k, v in bobot.items():
    if f"ACV_{k}" in df.columns:
        df[f"SCORE_{k}"] = df[f"ACV_{k}"].apply(lambda x: hitung_score(x, v))

# Total Score PPSA
score_cols = [f"SCORE_{k}" for k in bobot.keys() if f"SCORE_{k}" in df.columns]
df["TOTAL_SCORE_PPSA"] = df[score_cols].sum(axis=1)

# --- TAMPILAN STREAMLIT ---
st.set_page_config(page_title="Dashboard PPSA", layout="wide")
st.title("📊 Dashboard PPSA - Perhitungan Otomatis")

col1, col2 = st.columns(2)
tanggal_list = sorted(df["TANGGAL"].unique())
kasir_list = ["Semua"] + sorted(df["NAMA_KASIR"].unique())

tgl = col1.selectbox("Pilih Tanggal", tanggal_list)
kasir = col2.selectbox("Pilih Nama Kasir", kasir_list)

filtered = df[df["TANGGAL"] == tgl]
if kasir != "Semua":
    filtered = filtered[filtered["NAMA_KASIR"] == kasir]

# --- Ringkasan Skor ---
avg_total = filtered["TOTAL_SCORE_PPSA"].mean() if not filtered.empty else 0
st.metric("📈 Rata-rata Total Score PPSA", f"{avg_total:.2f}")

# --- Tabel hasil ---
st.dataframe(filtered, use_container_width=True)

# --- Grafik performa ---
if not filtered.empty:
    fig = px.bar(
        filtered,
        x="NAMA_KASIR",
        y="TOTAL_SCORE_PPSA",
        color="TOTAL_SCORE_PPSA",
        title="Performa Total Score PPSA per Kasir",
        text_auto=".2f",
    )
    st.plotly_chart(fig, use_container_width=True)
else:
    st.warning("⚠️ Tidak ada data untuk filter yang dipilih.")
