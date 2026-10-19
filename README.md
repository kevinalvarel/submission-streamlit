# 🌫️ Proyek Analisis Data: Kualitas Udara Stasiun Dongsi

Dashboard interaktif yang menampilkan hasil analisis kualitas udara di stasiun pemantauan **Dongsi**, Beijing (periode Maret 2013 – Februari 2017).

🔗 **Live Dashboard URL**: [https://submission-app-dicoding.streamlit.app/](https://submission-app-dicoding.streamlit.app/)

## 📂 Struktur Proyek

```
Proyek Akhir Analisis Data/
├── dashboard/
│   ├── dashboard.py          # Streamlit dashboard
│   └── main_data.csv         # Dataset utama
├── data/
│   └── PRSA_Data_Dongsi_20130301-20170228.csv
├── Air_Quality_Proyek_Analisis_Data.ipynb   # Notebook analisis
├── README.md
├── requirements.txt
└── url.txt
```

## 🚀 Cara Menjalankan Dashboard

### 1. Setup Environment - Shell/Terminal
```bash
mkdir proyek_analisis_data
cd proyek_analisis_data
pipenv install
pipenv shell
pip install -r requirements.txt
```

### 2. Setup Environment - Anaconda (Alternatif)
```bash
conda create --name main-ds python=3.9
conda activate main-ds
pip install -r requirements.txt
```

### 3. Jalankan Aplikasi Streamlit
Masuk ke direktori `dashboard` lalu jalankan Streamlit:
```bash
cd dashboard
streamlit run dashboard.py
```
atau dapat dijalankan langsung dari direktori root proyek:
```bash
streamlit run dashboard/dashboard.py
```

Setelah dijalankan, buka browser di `http://localhost:8501`.

## 📊 Pertanyaan Analisis

1. **Bagaimana pengaruh kecepatan angin (WSPM) dan curah hujan (RAIN) terhadap konsentrasi PM2.5 selama musim dingin (Desember–Februari)?**
2. **Berapa rata-rata kenaikan konsentrasi NO₂ dan CO pada jam sibuk pagi (07.00–09.00) dibandingkan jam normal?**

## 📝 Kesimpulan Utama

- Kecepatan angin berkorelasi negatif terhadap PM2.5 (−0,304). Angin kencang menyapu polutan hingga PM2.5 turun drastis.
- Curah hujan di musim dingin sangat jarang, dan PM2.5 saat hujan justru lebih tinggi karena angin melemah.
- NO₂ dan CO meningkat pada jam sibuk pagi (07–09), dengan akumulasi tertinggi terjadi malam hari (21–23).
- Lebih dari 50% waktu pemantauan berada di kategori **Tidak Sehat** berdasarkan standar AQI.
