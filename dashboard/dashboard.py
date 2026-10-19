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

# Gaya visualisasi global (mengikuti notebook)
sns.set_theme(style="whitegrid")

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

    winter_df["kategori_angin"] = pd.cut(
        winter_df["WSPM"],
        bins=[-1, 1.0, 2.0, 3.5, 15.0],
        labels=[
            "Sangat Lemah (≤1 m/s)",
            "Lemah (1-2 m/s)",
            "Sedang (2-3.5 m/s)",
            "Kencang (>3.5 m/s)",
        ],
    )

    fig, axes = plt.subplots(1, 2, figsize=(15, 6))

    # Subplot 1: Dampak kecepatan angin terhadap PM2.5
    sns.barplot(
        data=winter_df,
        x="kategori_angin",
        y="PM2.5",
        palette="Blues_r",
        errorbar=None,
        ax=axes[0],
    )
    axes[0].set_title(
        "Rata-rata PM2.5 Berdasarkan Kecepatan Angin\n(Musim Dingin)",
        fontsize=13,
        fontweight="bold",
    )
    axes[0].set_xlabel("Kategori Kecepatan Angin (WSPM)", fontsize=11)
    axes[0].set_ylabel("Rata-rata Konsentrasi PM2.5 (µg/m³)", fontsize=11)
    axes[0].tick_params(axis="x", rotation=15)

    for container in axes[0].containers:
        axes[0].bar_label(container, fmt="%.1f", padding=3, fontweight="bold")

    # Subplot 2: Perbandingan PM2.5 saat Hujan vs Tidak Hujan
    rain_summary = winter_df.groupby("kondisi_hujan")[["PM2.5"]].mean().reset_index()
    sns.barplot(
        data=rain_summary,
        x="kondisi_hujan",
        y="PM2.5",
        palette=["#e74c3c", "#3498db"],
        ax=axes[1],
    )
    axes[1].set_title(
        "Perbandingan Rata-rata PM2.5: Hujan vs Tidak Hujan\n(Musim Dingin)",
        fontsize=13,
        fontweight="bold",
    )
    axes[1].set_xlabel("Kondisi Presipitasi (RAIN)", fontsize=11)
    axes[1].set_ylabel("Rata-rata Konsentrasi PM2.5 (µg/m³)", fontsize=11)

    for container in axes[1].containers:
        axes[1].bar_label(container, fmt="%.2f", padding=3, fontweight="bold")

    fig.tight_layout()
    st.pyplot(fig)

    # Insight (angka dihitung langsung dari data agar tetap sesuai filter)
    wind_means = winter_df.groupby("kategori_angin", observed=False)["PM2.5"].mean()
    caption_wind = (
        "Rata-rata PM2.5 turun drastis seiring menguatnya kecepatan angin: "
        f"{wind_means.iloc[0]:.1f} µg/m³ saat sangat lemah (≤1 m/s) → "
        f"{wind_means.iloc[1]:.1f} µg/m³ (1-2 m/s) → "
        f"{wind_means.iloc[2]:.1f} µg/m³ (2-3.5 m/s) → "
        f"{wind_means.iloc[3]:.1f} µg/m³ saat kencang (>3.5 m/s). "
    )

    rain_means = winter_df.groupby("kondisi_hujan")[["PM2.5", "WSPM"]].mean()
    if {"Hujan (> 0 mm)", "Tidak Hujan (0 mm)"}.issubset(rain_means.index):
        caption_rain = (
            "Sebaliknya, saat turun hujan (RAIN > 0 mm) rata-rata PM2.5 justru lebih tinggi "
            f"({rain_means.loc['Hujan (> 0 mm)', 'PM2.5']:.2f} µg/m³) dibandingkan saat tidak hujan "
            f"({rain_means.loc['Tidak Hujan (0 mm)', 'PM2.5']:.2f} µg/m³), karena kecepatan angin "
            f"cenderung melemah ({rain_means.loc['Hujan (> 0 mm)', 'WSPM']:.2f} m/s) dan kelembapan udara "
            "yang tinggi menahan partikel polutan di permukaan."
        )
    else:
        caption_rain = "Tidak ada observasi hujan pada filter yang dipilih."

    st.caption(caption_wind + caption_rain)

st.markdown("---")

# =====================================================================
# BAGIAN 2 – Emisi Kendaraan pada Jam Sibuk Pagi
# =====================================================================
st.header("2️⃣ Konsentrasi NO₂ & CO: Jam Sibuk Pagi vs Jam Normal")

# ---------- Tren Harian (Siklus 24 Jam) ----------
st.subheader("⏰ Tren Rata-rata NO₂ & CO per Jam (Siklus 24 Jam)")

hourly_emissions = df_filtered.groupby("hour")[["NO2", "CO"]].mean().reset_index()

fig_hourly, axes_hourly = plt.subplots(2, 1, figsize=(14, 9), sharex=True)

# Subplot 1: Tren harian NO2
sns.lineplot(
    data=hourly_emissions,
    x="hour",
    y="NO2",
    marker="o",
    color="#d35400",
    linewidth=2.5,
    ax=axes_hourly[0],
    label="Rata-rata NO2",
)
axes_hourly[0].axvspan(7, 9, color="#f39c12", alpha=0.3, label="Jam Sibuk Pagi (07:00 - 09:00)")
axes_hourly[0].axvspan(21, 23, color="#8e44ad", alpha=0.2, label="Puncak Akumulasi Malam (21:00 - 23:00)")
axes_hourly[0].set_title(
    "Tren Rata-rata Konsentrasi NO2 per Jam (Siklus 24 Jam)",
    fontsize=13,
    fontweight="bold",
)
axes_hourly[0].set_ylabel("Konsentrasi NO2 (µg/m³)", fontsize=11)
axes_hourly[0].legend(loc="upper left")

# Subplot 2: Tren harian CO
sns.lineplot(
    data=hourly_emissions,
    x="hour",
    y="CO",
    marker="s",
    color="#2c3e50",
    linewidth=2.5,
    ax=axes_hourly[1],
    label="Rata-rata CO",
)
axes_hourly[1].axvspan(7, 9, color="#f39c12", alpha=0.3, label="Jam Sibuk Pagi (07:00 - 09:00)")
axes_hourly[1].axvspan(21, 23, color="#8e44ad", alpha=0.2, label="Puncak Akumulasi Malam (21:00 - 23:00)")
axes_hourly[1].set_title(
    "Tren Rata-rata Konsentrasi CO per Jam (Siklus 24 Jam)",
    fontsize=13,
    fontweight="bold",
)
axes_hourly[1].set_xlabel("Jam (00:00 - 23:00)", fontsize=11)
axes_hourly[1].set_ylabel("Konsentrasi CO (µg/m³)", fontsize=11)
axes_hourly[1].set_xticks(range(0, 24))
axes_hourly[1].legend(loc="upper left")

fig_hourly.tight_layout()
st.pyplot(fig_hourly)

# Insight (angka dihitung langsung dari data agar tetap sesuai filter)
if hourly_emissions.empty:
    st.warning("Tidak ada data pada filter yang dipilih.")
else:
    rush_hours = hourly_emissions[hourly_emissions["hour"].between(7, 9)]
    night_hours = hourly_emissions[hourly_emissions["hour"].between(21, 23)]
    peak_hour = int(rush_hours.loc[rush_hours["NO2"].idxmax(), "hour"])
    low_hour = int(hourly_emissions.loc[hourly_emissions["NO2"].idxmin(), "hour"])

    st.caption(
        "Terlihat pola dua puncak (bimodal): konsentrasi menurun pada dini hari, lalu kembali "
        f"menanjak pada jam sibuk pagi (07.00–09.00) dengan puncak pukul {peak_hour:02d}.00 "
        f"(rata-rata jam sibuk NO₂ ≈ {rush_hours['NO2'].mean():.2f} µg/m³; "
        f"CO ≈ {rush_hours['CO'].mean():.2f} µg/m³). Memasuki siang hingga sore hari, kedua gas "
        f"turun tajam dan mencapai titik terendah pada pukul {low_hour:02d}.00, sebelum kembali "
        f"merangkak naik hingga mencapai puncak tertinggi pada malam hari pukul 21.00–23.00 "
        f"(NO₂ ≈ {night_hours['NO2'].mean():.2f} µg/m³; CO ≈ {night_hours['CO'].mean():.2f} µg/m³) "
        "akibat akumulasi emisi dan fenomena inversi suhu malam hari."
    )

# Tabel: 5 jam dengan NO2 tertinggi
st.subheader("🏆 Top‑5 Jam dengan Konsentrasi NO₂ Tertinggi")
hourly_trend = df_filtered.groupby("hour")[["NO2", "CO", "PM2.5", "O3"]].mean().round(2)
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
ax_aqi.invert_yaxis()
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
