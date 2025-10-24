import streamlit as st
import pandas as pd
import gspread
from gspread_dataframe import get_as_dataframe
from oauth2client.service_account import ServiceAccountCredentials
import plotly.express as px

st.set_page_config(page_title="Dashboard PPSA", layout="wide")

st.title("📊 Dashboard PPSA (PSM, PWP, SG, APC)")
st.markdown("### Evaluasi performa kasir berdasarkan pencapaian dan bobot indikator")

# === KONEKSI GOOGLE SHEET ===
scope = ["https://spreadsheets.google.com/feeds",'https://www.googleapis.com/auth/drive']
creds = ServiceAccountCredentials.from_json_keyfile_name("credentials.json", scope)
client = gspread.authorize(creds)

sheet = client.open("PesanOtomatis").worksheet("Data")
df = get_as_dataframe(sheet, evaluate_formulas=True)

df = df.dropna(subset=["NAMA KASIR"])
df = df.fillna(0)

# === HITUNG SCORE PER SHIFT ===
def calculate_scores(row):
    def safe_divide(a, b):
        return (a / b) * 100 if b != 0 else 0

    # PSM
    acv_psm = safe_divide(row["PSM Actual"], row["PSM Target"])
    score_psm = (acv_psm / 100) * 20

    # PWP
    acv_pwp = safe_divide(row["PWP Actual"], row["PWP Target"])
    score_pwp = (acv_pwp / 100) * 25

    # SG
    acv_sg = safe_divide(row["SG Actual"], row["SG Target"])
    score_sg = (acv_sg / 100) * 30

    # APC (AVERAGE, bukan total)
    acv_apc = safe_divide(row["APC Actual"], row["APC Target"])
    score_apc = (acv_apc / 100) * 25

    total = score_psm + score_pwp + score_sg + score_apc

    return pd.Series({
        "PSM ACV": acv_psm,
        "SCORE PSM": score_psm,
        "PWP ACV": acv_pwp,
        "SCORE PWP": score_pwp,
        "SG ACV": acv_sg,
        "SCORE SG": score_sg,
        "APC ACV": acv_apc,
        "SCORE APC": score_apc,
        "TOTAL SCORE PPSA": total
    })

score_df = df.apply(calculate_scores, axis=1)
df = pd.concat([df, score_df], axis=1)

# === GABUNGKAN PER TANGGAL (AGAR APC DIRATAKAN) ===
df_grouped = df.groupby(["NAMA KASIR", "TANGGAL"]).agg({
    "PSM Target":"sum", "PSM Actual":"sum", "PSM ACV":"mean", "SCORE PSM":"mean",
    "PWP Target":"sum", "PWP Actual":"sum", "PWP ACV":"mean", "SCORE PWP":"mean",
    "SG Target":"sum", "SG Actual":"sum", "SG ACV":"mean", "SCORE SG":"mean",
    "APC Target":"mean", "APC Actual":"mean", "APC ACV":"mean", "SCORE APC":"mean",
    "TOTAL SCORE PPSA":"mean"
}).reset_index()

# === FILTER & TAMPILKAN ===
kasir_selected = st.selectbox("Pilih Nama Kasir:", df_grouped["NAMA KASIR"].unique())
df_filtered = df_grouped[df_grouped["NAMA KASIR"] == kasir_selected]

st.dataframe(df_filtered[[
    "TANGGAL",
    "PSM Target", "PSM Actual", "PSM ACV", "SCORE PSM",
    "PWP Target", "PWP Actual", "PWP ACV", "SCORE PWP",
    "SG Target", "SG Actual", "SG ACV", "SCORE SG",
    "APC Target", "APC Actual", "APC ACV", "SCORE APC",
    "TOTAL SCORE PPSA"
]])

# === GRAFIK ===
fig = px.line(df_filtered, x="TANGGAL", y="TOTAL SCORE PPSA",
              title=f"📈 Tren Total Score PPSA - {kasir_selected}", markers=True)
st.plotly_chart(fig, use_container_width=True)

# === RANKING ===
st.subheader("🏅 Ranking Kasir Berdasarkan Rata-rata Total Score PPSA")
ranking = df_grouped.groupby("NAMA KASIR")["TOTAL SCORE PPSA"].mean().reset_index()
ranking = ranking.sort_values(by="TOTAL SCORE PPSA", ascending=False)
st.dataframe(ranking)
fig_rank = px.bar(ranking, x="NAMA KASIR", y="TOTAL SCORE PPSA", title="Rata-rata Total Score PPSA per Kasir", color="TOTAL SCORE PPSA", color_continuous_scale="Blues")
st.plotly_chart(fig_rank, use_container_width=True)
