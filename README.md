# 📊 Dashboard Realisasi Pengadaan INAPROC

**Telkomsel Enterprise | Bid Management — Data Science**

Dashboard analisis realisasi pengadaan pemerintah dari data INAPROC, dengan fitur:
- Klasifikasi ICT vs Non-ICT
- Analisis per Wilayah (6 region) & Tema K/L (7 tema)
- Top 20 Pemenang, Top Instansi, Heatmap
- Fuzzy matching nama vendor tersensor
- Export Excel dengan styling Telkomsel branding

## 🚀 Quick Start

```bash
# 1. Install dependencies
pip install -r requirements.txt

# 2. Siapkan database
#    Letakkan Datamart_Final_Report.db di folder ini

# 3. (Opsional) Generate vendor mapping
python generate_vendor_mapping.py

# 4. (Opsional) Buat database ringan
python create_lite_db.py

# 5. Jalankan dashboard
streamlit run app.py
```

## 📁 Struktur File

| File | Deskripsi |
|------|-----------|
| `app.py` | Dashboard utama (Streamlit) |
| `create_lite_db.py` | Script buat database ringan dari Datamart_Final_Report.db |
| `generate_vendor_mapping.py` | Script fuzzy matching nama vendor tersensor |
| `vendor_mapping.json` | Hasil mapping vendor (di-generate offline) |
| `requirements.txt` | Daftar dependensi Python |

## ⚠️ Catatan

- File `.db` **tidak di-push** ke GitHub karena ukurannya besar (>2 GB)
- Siapkan database secara terpisah di server/lokal
