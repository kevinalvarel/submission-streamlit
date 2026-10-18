import streamlit as st
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
import os

# ---------------------------------------------------------------------------
# Konfigurasi Halaman
# ---------------------------------------------------------------------------
st.set_page_config(
    page_title="Dashboard Kualitas Udara – Stasiun Dongsi",
    page_icon="🌫️",
    layout="wide",
)

# ---------------------------------------------------------------------------
# Helper: Load & Clean Data
# ---------------------------------------------------------------------------

@st.cache_data
def load_data():
    """Muat data CSV utama dan lakukan pembersihan dasar."""
    csv_path = os.path.join(os.path.dirname(__file__), "main_data.csv")
    df = pd.read_csv(csv_path)

    # Hapus baris yang memiliki missing values & reset index
    df.dropna(inplace=True)
    df.reset_index(drop=True, inplace=True)

    # Buat kolom datetime untuk kemudahan filter
    df["datetime"] = pd.to_datetime(
        df[["year", "month", "day", "hour"]].astype(str).agg("-".join, axis=1),
        format="%Y-%m-%d-%H",
    )

    # Kolom kategori jam
    df["kategori_jam"] = df["hour"].apply(
        lambda h: "Jam Sibuk Pagi (07‑09)" if 7 <= h <= 9 else "Jam Normal/Lainnya"
    )

    # Kolom kategori kualitas udara (binning PM2.5 berdasarkan standar AQI US EPA)
    bins = [-1, 12.0, 35.4, 55.4, 150.4, 250.4, 1000.0]
    labels = [
        "1. Baik",
        "2. Sedang",
        "3. Tidak Sehat (Sensitif)",
        "4. Tidak Sehat",
        "5. Sangat Tidak Sehat",
        "6. Berbahaya",
    ]
    df["kategori_udara"] = pd.cut(df["PM2.5"], bins=bins, labels=labels)

    return df


df = load_data()

# ---------------------------------------------------------------------------
# Sidebar – Filter
# ---------------------------------------------------------------------------
st.sidebar.title("🔧 Filter Data")

# Rentang tahun
years = sorted(df["year"].unique())
selected_years = st.sidebar.multiselect(
    "Pilih Tahun", years, default=years
)

# Rentang bulan
months = list(range(1, 13))
selected_months = st.sidebar.multiselect(
    "Pilih Bulan", months, default=months,
    format_func=lambda m: [
        "Jan", "Feb", "Mar", "Apr", "Mei", "Jun",
        "Jul", "Agu", "Sep", "Okt", "Nov", "Des",
    ][m - 1],
)

# Terapkan filter
mask = df["year"].isin(selected_years) & df["month"].isin(selected_months)
df_filtered = df[mask].copy()

st.sidebar.markdown("---")
st.sidebar.caption(
    f"**Data terfilter:** {len(df_filtered):,} baris dari {len(df):,} total"
)

# ---------------------------------------------------------------------------
# Header
# ---------------------------------------------------------------------------
st.title("🌫️ Dashboard Analisis Kualitas Udara – Stasiun Dongsi")
st.markdown(
    """
    Dashboard ini menyajikan hasil analisis kualitas udara di stasiun pemantauan **Dongsi**
    (periode Maret 2013 – Februari 2017). Analisis berfokus pada dua pertanyaan bisnis utama:

    1. **Bagaimana pengaruh kecepatan angin (WSPM) dan curah hujan (RAIN) terhadap PM2.5
       selama musim dingin (Desember–Februari)?**
    2. **Berapa rata‑rata kenaikan konsentrasi NO₂ dan CO pada jam sibuk pagi (07.00–09.00)
       dibandingkan jam normal?**

    Serta analisis lanjutan distribusi **Indeks Kualitas Udara (AQI)** berdasarkan PM2.5.
    """
)

# ---------------------------------------------------------------------------
# KPI Ringkasan
# ---------------------------------------------------------------------------
st.subheader("📊 Ringkasan Statistik Utama")

col1, col2, col3, col4, col5 = st.columns(5)

with col1:
    st.metric("Rata-rata PM2.5", f"{df_filtered['PM2.5'].mean():.1f} µg/m³")

with col2:
    st.metric("Rata-rata NO₂", f"{df_filtered['NO2'].mean():.1f} µg/m³")

with col3:
    st.metric("Rata-rata CO", f"{df_filtered['CO'].mean():.0f} µg/m³")

with col4:
    st.metric("Rata-rata Suhu", f"{df_filtered['TEMP'].mean():.1f} °C")

with col5:
    st.metric("Rata-rata Kec. Angin", f"{df_filtered['WSPM'].mean():.2f} m/s")

st.markdown("---")

# =====================================================================
# BAGIAN 1 – Pengaruh Cuaca terhadap PM2.5
# =====================================================================
st.header("1️⃣ Pengaruh Kecepatan Angin & Curah Hujan terhadap PM2.5")

# ---------- Korelasi Cuaca vs Polutan ----------
st.subheader("🔗 Matriks Korelasi Cuaca vs Polutan")

weather_pollutant_cols = ["PM2.5", "PM10", "RAIN", "WSPM", "TEMP", "DEWP", "PRES"]
corr_matrix = df_filtered[weather_pollutant_cols].corr()[["PM2.5", "PM10"]].round(3)

fig_corr, ax_corr = plt.subplots(figsize=(6, 5))
sns.heatmap(
    corr_matrix,
    annot=True,
    cmap="RdBu_r",
    center=0,
    vmin=-1,
    vmax=1,
    linewidths=0.5,
    ax=ax_corr,
)
ax_corr.set_title("Korelasi Variabel Cuaca terhadap PM2.5 & PM10", fontsize=12, fontweight="bold")
st.pyplot(fig_corr)

st.caption(
    "Kecepatan angin (WSPM) memiliki korelasi negatif terkuat terhadap PM2.5, "
    "menunjukkan bahwa semakin kencang angin → polutan tertiup/tersebar."
)

# ---------- Analisis Musim Dingin ----------
st.subheader("❄️ Analisis PM2.5 saat Musim Dingin (Desember – Februari)")

winter_mask = df_filtered["month"].isin([12, 1, 2])
winter_df = df_filtered[winter_mask].copy()

if winter_df.empty:
    st.warning("Tidak ada data musim dingin pada filter yang dipilih.")
else:
    winter_df["kondisi_hujan"] = winter_df["RAIN"].apply(
        lambda x: "Hujan (> 0 mm)" if x > 0 else "Tidak Hujan (0 mm)"
    )

    # Tabel ringkasan
    summary_winter = (
        winter_df.groupby("kondisi_hujan")[["PM2.5", "WSPM"]]
        .agg(["count", "mean", "median"])
        .round(2)
    )
    st.dataframe(summary_winter, use_container_width=True)

    # --- Scatter: WSPM vs PM2.5 musim dingin ---
    fig_scatter, ax_scatter = plt.subplots(figsize=(9, 5))
    scatter = ax_scatter.scatter(
        winter_df["WSPM"],
        winter_df["PM2.5"],
        c=winter_df["RAIN"].apply(lambda x: 1 if x > 0 else 0),
        cmap="coolwarm",
        alpha=0.35,
        s=15,
        edgecolors="none",
    )
    ax_scatter.set_xlabel("Kecepatan Angin / WSPM (m/s)", fontsize=11)
    ax_scatter.set_ylabel("PM2.5 (µg/m³)", fontsize=11)
    ax_scatter.set_title(
        "Hubungan Kecepatan Angin dengan PM2.5 saat Musim Dingin",
        fontsize=12,
        fontweight="bold",
    )
    legend_labels = ["Tidak Hujan", "Hujan"]
    handles = [
        plt.Line2D([0], [0], marker="o", color="w", markerfacecolor=c, markersize=8)
        for c in ["#3b4cc0", "#b40426"]
    ]
    ax_scatter.legend(handles, legend_labels, title="Kondisi", loc="upper right")
    st.pyplot(fig_scatter)

    st.caption(
        "Saat kecepatan angin rendah (≤ 1 m/s), PM2.5 menumpuk sangat tinggi. "
        "Sebaliknya, angin kencang (> 3.5 m/s) menyapu polutan hingga PM2.5 turun drastis."
    )

    # --- Bar: Rata-rata PM2.5 berdasarkan kategori kecepatan angin ---
    bins_wind = [0, 1, 2, 3.5, 15]
    labels_wind = ["≤ 1 m/s", "1‑2 m/s", "2‑3.5 m/s", "> 3.5 m/s"]
    winter_df["kat_angin"] = pd.cut(winter_df["WSPM"], bins=bins_wind, labels=labels_wind)

    wind_pm = winter_df.groupby("kat_angin", observed=False)["PM2.5"].mean().round(1)

    fig_bar_wind, ax_bw = plt.subplots(figsize=(8, 4))
    colors_wind = ["#e74c3c", "#e67e22", "#f1c40f", "#2ecc71"]
    bars = ax_bw.bar(wind_pm.index.astype(str), wind_pm.values, color=colors_wind)
    for b in bars:
        ax_bw.text(
            b.get_x() + b.get_width() / 2,
            b.get_height() + 2,
            f"{b.get_height():.1f}",
            ha="center",
            fontweight="bold",
        )
    ax_bw.set_xlabel("Kategori Kecepatan Angin", fontsize=11)
    ax_bw.set_ylabel("Rata‑rata PM2.5 (µg/m³)", fontsize=11)
    ax_bw.set_title(
        "Rata‑rata PM2.5 per Kategori Kecepatan Angin (Musim Dingin)",
        fontsize=12,
        fontweight="bold",
    )
    st.pyplot(fig_bar_wind)

st.markdown("---")

# =====================================================================
# BAGIAN 2 – Emisi Kendaraan pada Jam Sibuk Pagi
# =====================================================================
st.header("2️⃣ Konsentrasi NO₂ & CO: Jam Sibuk Pagi vs Jam Normal")

# Tabel Perbandingan
rush_summary = (
    df_filtered.groupby("kategori_jam")[["NO2", "CO", "PM2.5"]]
    .agg(["mean", "median", "max"])
    .round(2)
)
st.dataframe(rush_summary, use_container_width=True)

# --- Grouped Bar Chart ---
rush_means = df_filtered.groupby("kategori_jam")[["NO2", "CO"]].mean().round(2)

fig_rush, axes_rush = plt.subplots(1, 2, figsize=(12, 5))

for idx, col in enumerate(["NO2", "CO"]):
    ax = axes_rush[idx]
    vals = rush_means[col]
    colors_rush = ["#3498db", "#e74c3c"]
    b = ax.bar(vals.index.astype(str), vals.values, color=colors_rush)
    for bar in b:
        ax.text(
            bar.get_x() + bar.get_width() / 2,
            bar.get_height() + 1,
            f"{bar.get_height():.1f}",
            ha="center",
            fontweight="bold",
            fontsize=10,
        )
    ax.set_title(f"Rata‑rata {col}", fontsize=12, fontweight="bold")
    ax.set_ylabel(f"{col} (µg/m³)", fontsize=10)

fig_rush.suptitle(
    "Perbandingan Rata‑rata Polutan: Jam Sibuk Pagi vs Jam Normal",
    fontsize=13,
    fontweight="bold",
    y=1.02,
)
fig_rush.tight_layout()
st.pyplot(fig_rush)

# --- Tren Harian (24 jam) ---
st.subheader("⏰ Tren Konsentrasi Polutan per Jam (0–23)")

hourly_trend = df_filtered.groupby("hour")[["NO2", "CO", "PM2.5", "O3"]].mean().round(2)

pollutant_choice = st.multiselect(
    "Pilih polutan yang ingin ditampilkan:",
    options=["NO2", "CO", "PM2.5", "O3"],
    default=["NO2", "CO"],
)

if pollutant_choice:
    fig_hourly, ax_hourly = plt.subplots(figsize=(11, 5))
    palette = {"NO2": "#e74c3c", "CO": "#3498db", "PM2.5": "#e67e22", "O3": "#2ecc71"}
    for p in pollutant_choice:
        ax_hourly.plot(
            hourly_trend.index,
            hourly_trend[p],
            marker="o",
            markersize=5,
            label=p,
            color=palette.get(p, None),
            linewidth=2,
        )
    ax_hourly.set_xlabel("Jam (0–23)", fontsize=11)
    ax_hourly.set_ylabel("Konsentrasi Rata‑rata", fontsize=11)
    ax_hourly.set_title("Tren Rata‑rata Polutan per Jam dalam Sehari", fontsize=13, fontweight="bold")
    ax_hourly.legend()
    ax_hourly.set_xticks(range(0, 24))
    ax_hourly.axvspan(7, 9, alpha=0.12, color="red", label="Jam Sibuk Pagi")
    st.pyplot(fig_hourly)

    st.caption(
        "Area merah muda menandakan jam sibuk pagi (07–09). "
        "Puncak akumulasi polutan tertinggi justru terjadi pada malam hari (21–23), "
        "akibat aktivitas logistik dan fenomena inversi suhu."
    )
else:
    st.info("Silakan pilih minimal satu polutan untuk menampilkan grafik.")

# Tabel: 5 jam dengan NO2 tertinggi
st.subheader("🏆 Top‑5 Jam dengan Konsentrasi NO₂ Tertinggi")
top5_no2 = hourly_trend.sort_values(by="NO2", ascending=False).head(5)
st.dataframe(top5_no2, use_container_width=True)

st.markdown("---")

# =====================================================================
# BAGIAN 3 – Distribusi Kategori Kualitas Udara (AQI)
# =====================================================================
st.header("3️⃣ Distribusi Kategori Kualitas Udara (Standar AQI)")

aqi_dist = (
    df_filtered["kategori_udara"]
    .value_counts()
    .sort_index()
    .reset_index()
)
aqi_dist.columns = ["Kategori Kualitas Udara", "Jumlah Jam Observasi"]
aqi_dist["Persentase (%)"] = (
    aqi_dist["Jumlah Jam Observasi"] / len(df_filtered) * 100
).round(2)

st.dataframe(aqi_dist, use_container_width=True)

fig_aqi, ax_aqi = plt.subplots(figsize=(11, 6))
aqi_colors = ["#2ecc71", "#f1c40f", "#e67e22", "#e74c3c", "#8e44ad", "#7f1d1d"]
bars_aqi = ax_aqi.barh(
    aqi_dist["Kategori Kualitas Udara"],
    aqi_dist["Persentase (%)"],
    color=aqi_colors,
)
for bar in bars_aqi:
    ax_aqi.text(
        bar.get_width() + 0.5,
        bar.get_y() + bar.get_height() / 2,
        f"{bar.get_width():.2f}%",
        va="center",
        fontweight="bold",
    )
ax_aqi.set_xlabel("Persentase Waktu Observasi (%)", fontsize=11)
ax_aqi.set_ylabel("Kategori Kualitas Udara (Standar AQI)", fontsize=11)
ax_aqi.set_title(
    "Proporsi Waktu Kualitas Udara Berdasarkan Standar Ambang Batas PM2.5",
    fontsize=13,
    fontweight="bold",
)
ax_aqi.set_xlim(0, aqi_dist["Persentase (%)"].max() + 8)
fig_aqi.tight_layout()
st.pyplot(fig_aqi)

st.caption(
    "Lebih dari 50% waktu pemantauan berada pada kategori **Tidak Sehat** atau di atasnya, "
    "menunjukkan risiko tinggi terhadap kesehatan pernapasan masyarakat."
)

st.markdown("---")

# =====================================================================
# Kesimpulan & Rekomendasi
# =====================================================================
st.header("📝 Kesimpulan & Rekomendasi")

st.markdown(
    """
    #### Kesimpulan

    1. **Pengaruh Kecepatan Angin & Hujan terhadap PM2.5 (Musim Dingin)**
       - Kecepatan angin (WSPM) memiliki korelasi negatif signifikan terhadap PM2.5 (−0,304).
         Saat angin ≤ 1 m/s, PM2.5 rata‑rata mencapai ~159 µg/m³; saat angin > 3,5 m/s,
         PM2.5 turun drastis hingga ~17 µg/m³.
       - Curah hujan di musim dingin sangat jarang (61 observasi) dan PM2.5 saat hujan
         justru lebih tinggi (132 µg/m³) karena angin melemah & kelembapan menahan polutan.

    2. **Lonjakan NO₂ & CO pada Jam Sibuk Pagi**
       - NO₂ dan CO meningkat pada jam 07–09 (rata‑rata NO₂ ≈ 57,8 µg/m³; CO ≈ 1.412,8 µg/m³)
         dibandingkan jam normal.
       - Puncak akumulasi tertinggi terjadi malam hari (21–23) akibat aktivitas logistik
         dan inversi suhu.

    3. **Distribusi Kualitas Udara (AQI)**
       - Lebih dari separuh waktu pemantauan berada di kategori **Tidak Sehat** ke atas,
         menegaskan perlunya kebijakan pengendalian emisi dan peringatan publik.

    ---

    #### Rekomendasi

    - **Sistem Peringatan Dini berbasis Prakiraan Angin**: Integrasikan data kecepatan angin
      ke dalam sistem alert otomatis. Saat angin ≤ 1 m/s di musim dingin, kirim notifikasi
      publik agar warga menggunakan masker N95/KN95 & menyalakan *air purifier*.
    - **Rekayasa Lalu Lintas & Regulasi Emisi Malam**: Terapkan pembatasan kendaraan pada
      jam sibuk pagi (ganjil‑genap / *Low Emission Zone*) serta batasi operasional truk
      logistik diesel pada pukul 21–23 di area pemukiman.
    - **Jadwal Aktivitas Luar Ruangan yang Aman**: Prioritaskan olahraga & kegiatan outdoor
      pada pukul 14–17 (terutama 15–16) saat sirkulasi atmosfer optimal dan polutan
      pada titik terendah harian.
    """
)

# Footer
st.markdown("---")
st.caption("© 2026 – Dashboard Analisis Kualitas Udara | Data: PRSA Dongsi (2013–2017)")
