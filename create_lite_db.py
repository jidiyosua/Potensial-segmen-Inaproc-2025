"""
═══════════════════════════════════════════════════════════════════════════
  SCRIPT: Buat Database Clone Ringan
  Input:  Datamart_Final_Report.db
  Output: Datamart_Lite.db

  Jalankan 1x sebelum deploy dashboard:
    python create_lite_db.py
═══════════════════════════════════════════════════════════════════════════
"""

import sqlite3
import pandas as pd
import re
import os
import sys

# ─── CONFIG ───
INPUT_DB  = "Datamart_Final_Report.db"
OUTPUT_DB = "Datamart_Lite.db"

# Kolom yang DIPERTAHANKAN (11 dari 19)
KEEP_COLUMNS = [
    "ID_RUP",
    "Nama_Paket",
    "Pagu_Rp",
    "Metode_Pemilihan",
    "Jenis_Pengadaan",
    "Instansi_Pembeli",
    "Satuan_Kerja",
    "Lokasi",
    "Nama_Pemenang",
    "Total_Pelaksanaan_Rp",
    "Sumber_Data",
]

# Kolom yang DIHAPUS (8 kolom):
# - Kategori_Paket (mayoritas kosong/"Others")
# - Jenis_Usaha (selalu "Kecil")
# - Tanggal_Pemilihan (format text tidak standar)
# - Nama_Produk (mayoritas kosong)
# - Kategori_Produk (mayoritas kosong)
# - Kuantitas_Produk (mayoritas kosong)
# - Nama_Manufaktur (mayoritas kosong)
# - Updated_At (metadata internal)

# ═══════════════════════════════════════════════════════════════════════════
# INSTANSI BLACKLIST — K/L tidak relevan untuk B2G Telkomsel
# ═══════════════════════════════════════════════════════════════════════════
INSTANSI_BLACKLIST = [
    # Kebudayaan, Olahraga
    r"(?i)kementerian\s*kebudayaan",
    r"(?i)kementerian\s*pemuda\s*dan\s*olahraga",
    r"(?i)kemenpora",
    r"(?i)kementerian\s*pariwisata\s*dan\s*ekonomi\s*kreatif",
    r"(?i)kemenparekraf",
    r"(?i)badan\s*otorita\s*(borobudur|danau\s*toba|labuan\s*bajo)",

    # Yudikatif & Legislatif
    r"(?i)mahkamah\s*(agung|konstitusi)",
    r"(?i)komisi\s*yudisial",
    r"(?i)dewan\s*perwakilan\s*(rakyat|daerah)",
    r"(?i)majelis\s*permusyawaratan",
    r"(?i)sekretariat\s*jenderal\s*(dpr|dpd|mpr)",

    # Audit & Pengawas
    r"(?i)badan\s*pemeriksa\s*keuangan",
    r"(?i)badan\s*pengawasan\s*keuangan",
    r"(?i)ombudsman",
    r"(?i)komisi\s*pemberantasan\s*korupsi",
    r"(?i)pusat\s*pelaporan.*transaksi\s*keuangan",

    # Lembaga kecil / niche
    r"(?i)komisi\s*pemilihan\s*umum",
    r"(?i)badan\s*pengawas\s*pemilu",
    r"(?i)komisi\s*aparatur\s*sipil",
    r"(?i)komisi\s*informasi\b",
    r"(?i)dewan\s*ketahanan\s*nasional",
    r"(?i)dewan\s*pertimbangan\s*presiden",
    r"(?i)badan\s*pembinaan\s*ideologi\s*pancasila",
    r"(?i)badan\s*nasional\s*pengelola\s*perbatasan",
    r"(?i)lembaga\s*kebijakan\s*pengadaan",
    r"(?i)komisi\s*pengawas\s*persaingan",
    r"(?i)komisi\s*nasional\s*hak\s*asasi",
    r"(?i)komisi\s*perlindungan\s*anak",
    r"(?i)lembaga\s*perlindungan\s*saksi",

    # Infrastruktur fisik murni (PUPR pusat, bukan Dinas PUPR daerah)
    r"(?i)kementerian\s*pekerjaan\s*umum",
    r"(?i)kementerian\s*perumahan",
    r"(?i)kementerian\s*perhubungan",

    # SDA
    r"(?i)kementerian\s*lingkungan\s*hidup",
    r"(?i)kementerian\s*kehutanan",
    r"(?i)kementerian\s*energi\s*dan\s*sumber\s*daya\s*mineral",

    # Ketenagakerjaan
    r"(?i)kementerian\s*ketenagakerjaan",
    r"(?i)kementerian\s*transmigrasi",

    # Lembaga sektoral kecil
    r"(?i)badan\s*meteorologi",
    r"(?i)badan\s*informasi\s*geospasial",
    r"(?i)badan\s*tenaga\s*nuklir",
    r"(?i)badan\s*pengawas\s*tenaga\s*nuklir",
    r"(?i)badan\s*standardisasi",
    r"(?i)badan\s*pengawas\s*obat",
    r"(?i)perpustakaan\s*nasional",
    r"(?i)arsip\s*nasional",
    r"(?i)lembaga\s*penerbangan\s*dan\s*antariksa",
    r"(?i)lembaga\s*ilmu\s*pengetahuan",
    r"(?i)badan\s*pengkajian.*penerapan\s*teknologi",
]

# WHITELIST — JANGAN PERNAH HAPUS
INSTANSI_WHITELIST = [
    # Semua Pemda
    r"(?i)^kab\.",
    r"(?i)^kota\s",
    r"(?i)^provinsi\s",
    r"(?i)^pemerintah\s*(kab|kota|provinsi|daerah)",

    # 7 Tema K/L Strategis
    r"(?i)kementerian\s*pertanian",
    r"(?i)kementerian\s*kelautan",
    r"(?i)badan\s*riset\s*dan\s*inovasi",
    r"(?i)kementerian\s*kesehatan",
    r"(?i)kementerian\s*sosial",
    r"(?i)bkkbn",
    r"(?i)badan\s*gizi\s*nasional",
    r"(?i)kementerian\s*pendidikan",
    r"(?i)kementerian\s*agama",
    r"(?i)lembaga\s*administrasi\s*negara",
    r"(?i)kementerian\s*dalam\s*negeri",
    r"(?i)kementerian\s*koperasi",
    r"(?i)kementerian\s*desa",
    r"(?i)kementerian\s*keuangan",
    r"(?i)bappenas",
    r"(?i)bpjs",
    r"(?i)kementerian\s*pertahanan",
    r"(?i)tentara\s*nasional",
    r"(?i)tni\b",
    r"(?i)kepolisian",
    r"(?i)polri",
    r"(?i)bnpt",
    r"(?i)bssn",
    r"(?i)bakamla",
    r"(?i)kementerian\s*hukum",
    r"(?i)kementerian\s*komunikasi",
    r"(?i)komdigi",
    r"(?i)kominfo",
    r"(?i)kemenko",
]

def should_keep(instansi):
    """Whitelist ALWAYS wins over blacklist."""
    if pd.isna(instansi):
        return False
    s = str(instansi).strip()
    if not s:
        return False

    # Whitelist check first
    for pat in INSTANSI_WHITELIST:
        if re.search(pat, s):
            return True

    # Blacklist check
    for pat in INSTANSI_BLACKLIST:
        if re.search(pat, s):
            return False

    # Default: keep (safety net)
    return True


def create_lite_db():
    if not os.path.exists(INPUT_DB):
        print(f"❌ File {INPUT_DB} tidak ditemukan!")
        sys.exit(1)

    original_size = os.path.getsize(INPUT_DB)
    print(f"📂 Input: {INPUT_DB} ({original_size/1024/1024:.1f} MB)")

    # ─── 1. Load ───
    conn = sqlite3.connect(INPUT_DB)
    tables = pd.read_sql("SELECT name FROM sqlite_master WHERE type='table'", conn)
    print(f"📋 Tabel: {tables['name'].tolist()}")
    tbl = tables['name'].iloc[0]

    total_count = pd.read_sql(f"SELECT COUNT(*) as n FROM [{tbl}]", conn).iloc[0,0]
    print(f"📊 Total rows: {total_count:,}")

    # Check available columns
    sample = pd.read_sql(f"SELECT * FROM [{tbl}] LIMIT 1", conn)
    all_cols = sample.columns.tolist()
    print(f"📋 Kolom ({len(all_cols)}): {all_cols}")

    # ─── 2. Select only needed columns ───
    available = [c for c in KEEP_COLUMNS if c in all_cols]
    dropped = [c for c in all_cols if c not in available]
    print(f"\n✅ Kolom dipertahankan ({len(available)}): {available}")
    print(f"🗑️  Kolom dihapus ({len(dropped)}): {dropped}")

    cols_sql = ", ".join([f'[{c}]' for c in available])
    df = pd.read_sql(f"SELECT {cols_sql} FROM [{tbl}]", conn)
    conn.close()

    print(f"\n📊 Loaded: {len(df):,} rows")

    # ─── 3. Drop rows without pemenang or pagu ───
    before = len(df)
    df = df[df["Nama_Pemenang"].notna() & (df["Nama_Pemenang"].str.strip() != "")]
    df["Pagu_Rp"] = pd.to_numeric(df["Pagu_Rp"], errors="coerce").fillna(0)
    df = df[df["Pagu_Rp"] > 0]
    print(f"🧹 Hapus tanpa pemenang/pagu: {before - len(df):,} rows")

    # ─── 4. Filter instansi ───
    before = len(df)
    mask = df["Instansi_Pembeli"].apply(should_keep)

    removed = df[~mask]
    removed_inst = removed["Instansi_Pembeli"].value_counts()
    print(f"\n🗑️  Instansi dihapus ({len(removed_inst)} unique, {len(removed):,} rows):")
    for inst, cnt in removed_inst.head(25).items():
        pagu = removed[removed["Instansi_Pembeli"]==inst]["Pagu_Rp"].sum()
        print(f"   • {inst}: {cnt:,} paket ({pagu/1e9:.1f} M)")

    df = df[mask].reset_index(drop=True)
    print(f"\n📉 Filter instansi: {before:,} → {len(df):,} (-{before-len(df):,})")

    # ─── 5. Strip whitespace ───
    for col in df.select_dtypes(include='object').columns:
        df[col] = df[col].str.strip()

    # ─── 6. Write output ───
    if os.path.exists(OUTPUT_DB):
        os.remove(OUTPUT_DB)

    conn_out = sqlite3.connect(OUTPUT_DB)
    df.to_sql("datamart", conn_out, index=False, if_exists="replace")

    # Indexes
    conn_out.execute("CREATE INDEX idx_pemenang ON datamart(Nama_Pemenang)")
    conn_out.execute("CREATE INDEX idx_instansi ON datamart(Instansi_Pembeli)")
    conn_out.execute("CREATE INDEX idx_satker ON datamart(Satuan_Kerja)")
    conn_out.execute("CREATE INDEX idx_lokasi ON datamart(Lokasi)")

    conn_out.execute("VACUUM")
    conn_out.close()

    # ─── 7. Report ───
    new_size = os.path.getsize(OUTPUT_DB)
    reduction = (1 - new_size / original_size) * 100

    print(f"\n{'='*60}")
    print(f"✅ DATABASE CLONE BERHASIL")
    print(f"{'='*60}")
    print(f"📂 Output: {OUTPUT_DB}")
    print(f"📊 Rows: {total_count:,} → {len(df):,}")
    print(f"📋 Kolom: {len(all_cols)} → {len(available)}")
    print(f"💾 Size: {original_size/1024/1024:.1f} MB → {new_size/1024/1024:.1f} MB")
    print(f"📉 Reduksi: {reduction:.1f}%")
    print(f"{'='*60}")

    # Validate
    print(f"\n🔍 Validasi...")
    conn_v = sqlite3.connect(OUTPUT_DB)

    # Pemda check
    pemda = pd.read_sql("""
        SELECT COUNT(DISTINCT Instansi_Pembeli) as n FROM datamart
        WHERE Instansi_Pembeli LIKE 'Kab.%'
           OR Instansi_Pembeli LIKE 'Kota %'
           OR Instansi_Pembeli LIKE 'Provinsi %'
    """, conn_v).iloc[0,0]
    print(f"   ✅ Pemda unik: {pemda}")

    # Top instansi
    top = pd.read_sql("""
        SELECT Instansi_Pembeli, COUNT(*) as cnt, SUM(CAST(Pagu_Rp AS REAL)) as pagu
        FROM datamart GROUP BY Instansi_Pembeli ORDER BY pagu DESC LIMIT 10
    """, conn_v)
    print(f"   🏛️ Top 10 Instansi:")
    for _, r in top.iterrows():
        print(f"      {r['Instansi_Pembeli']}: {r['cnt']:,} paket, {r['pagu']/1e9:.1f} M")

    conn_v.close()
    print(f"\n🎉 Selesai! Gunakan '{OUTPUT_DB}' di app.py (ganti DB_NAME)")


if __name__ == "__main__":
    create_lite_db()
