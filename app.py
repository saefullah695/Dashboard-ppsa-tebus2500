import streamlit as st
import pandas as pd
import gspread
from oauth2client.service_account import ServiceAccountCredentials

# --- Konfigurasi koneksi ke Google Spreadsheet ---
scope = ["https://spreadsheets.google.com/feeds",
         "https://www.googleapis.com/auth/drive"]
creds = ServiceAccountCredentials.from_json_keyfile_name("credentials.json", scope)
client = gspread.authorize(creds)

# --- Ambil data dari Sheet ---
sheet = client.open("PesanOtomatis").worksheet("Data")
data = sheet.get_all_records()
df = pd.DataFrame(data)

# --- Hitung skor otomatis berdasarkan ACV dan Bobot ---
def hitung_score(acv, bobot):
    try:
        return (float(acv) * float(bobot)) / 100
    except:
        return 0

# --- Hitung kolom skor dan total ---
df["SCORE PSM"] = df.apply(lambda x: hitung_score(x["ACV. 	BOBOT PSM"], 20), axis=1)
df["SCORE PWP"] = df.apply(lambda x: hitung_score(x["ACV, 	BOBOT PWP"], 25), axis=1)
df["SCORE SG"] = df.apply(lambda x: hitung_score(x["ACV, 	BOBOT SG"], 30), axis=1)
df["SCORE APC"] = df.apply(lambda x: hitung_score(x["ACV, 	BOBOT APC"], 25), axis=1)
df["TOTAL SCORE PPSA"] = df["SCORE PSM"] + df["SCORE PWP"] + df["SCORE SG"] + df["SCORE APC"]

# --- Tampilan Streamlit ---
st.set_page_config(page_title="Dashboard PPSA", layout="wide")
st.title("📊 Dashboard PPSA")

# Filter by tanggal / kasir
col1, col2 = st.columns(2)
tanggal = col1.selectbox("Pilih Tanggal", sorted(df["TANGGAL"].unique()))
kasir = col2.selectbox("Pilih Nama Kasir", ["Semua"] + sorted(df["NAMA KASIR"].unique()))

filtered_df = df[df["TANGGAL"] == tanggal]
if kasir != "Semua":
    filtered_df = filtered_df[filtered_df["NAMA KASIR"] == kasir]

st.dataframe(filtered_df, use_container_width=True)

# --- Statistik Ringkas ---
avg_score = filtered_df["TOTAL SCORE PPSA"].mean()
st.metric("Rata-rata Total Score PPSA", f"{avg_score:.2f}")

# --- Grafik Sederhana ---
st.bar_chart(filtered_df.set_index("NAMA KASIR")["TOTAL SCORE PPSA"])
