# 📊 Dashboard Realisasi Pengadaan Pemerintah — INAPROC

**Telkomsel Enterprise | Bid Management — Data Science**

Dashboard interaktif untuk analisis data realisasi pengadaan pemerintah Indonesia dari INAPROC (LKPP).

## ✨ Fitur

- **Overview**: KPI cards, Grand Top 20 Pemenang, ICT vs Non-ICT per Wilayah, Heatmap
- **Per K/L (7 Tema)**: Ketahanan Pangan, MBG, Pendidikan, Desa/Koperasi/UMKM, Kesehatan, Pertahanan, KOMDIGI
- **Per Wilayah & Dinas**: 6 Wilayah, DISKOMINFO se-Indonesia, Dinas Strategis per Wilayah
- **Detail Explorer**: Search & filter data mentah dengan visualisasi
- **Fuzzy Name Uncensoring**: Nama pemenang tersensor (contoh: `P* W******`) otomatis di-match ke nama asli
- **Excel Export**: Download dengan styling Telkomsel branding
- **Parquet Cache**: Load data < 1 detik setelah run pertama

## 🚀 Quick Start

```bash
# 1. Clone repository
git clone https://github.com/jidiyosua/Potensial-segmen-Inaproc-2025.git
cd Potensial-segmen-Inaproc-2025

# 2. Install dependencies
pip install -r requirements.txt

# 3. Letakkan database di root folder
# File: Datamart_Final_Report.db (atau Datamart_Lite.db)

# 4. (Opsional) Generate vendor mapping untuk uncensor nama tersensor
python generate_vendor_mapping.py

# 5. (Opsional) Buat database ringan
python create_lite_db.py

# 6. Jalankan dashboard
streamlit run app.py
```

## 📁 Struktur File

| File | Deskripsi |
|------|-----------|
| `app.py` | Dashboard utama (Streamlit) |
| `create_lite_db.py` | Script buat database ringan dari database utama |
| `generate_vendor_mapping.py` | Script fuzzy matching nama vendor tersensor |
| `requirements.txt` | Python dependencies |
| `.gitignore` | Files yang di-exclude dari Git |

## ⚙️ Konfigurasi

### Database
Dashboard akan mencari `Datamart_Final_Report.db` di root folder. Jika tidak ada, akan attempt download dari Google Drive.

### Password
Default: `TelkomselEnterprise2025ebpm`

Untuk custom password, buat `.streamlit/secrets.toml`:
```toml
[auth]
password_hash = "sha256_hash_password_anda"
```

## 🛠️ Tech Stack

- **Frontend**: Streamlit
- **Data**: Pandas, SQLite, Parquet (PyArrow)
- **Visualisasi**: Matplotlib, Seaborn
- **Export**: OpenPyXL

---

*Bid Management — Data Science | Telkomsel Enterprise © 2026*
