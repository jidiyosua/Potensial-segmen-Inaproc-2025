"""
=============================================================================
GENERATE TOP 20 PENYEDIA — DETAIL PAKET (1 Excel, Multi-Sheet)
=============================================================================
Membuat 1 file Excel dengan sheet terpisah untuk setiap zona/bidang.
Setiap sheet berisi detail paket dari Top 20 penyedia ICT dan Non-ICT.

Sheet structure:
  DAERAH:
    ICT_Sumatera, NonICT_Sumatera, ICT_Kalimantan, ...
  BIDANG (K/L):
    ICT_Bid_Pendidikan, NonICT_Bid_Pertahanan, ...

Kolom tambahan:
  - Prediksi_Nama_Asli: prediksi nama vendor yang tidak tersensor

Cara pakai:
  python generate_top20_detail.py

Output:
  output_si_channel/Top20_Detail_Paket.xlsx
=============================================================================
"""

import pandas as pd
import sqlite3
import os
import re
import glob
from difflib import SequenceMatcher

# ── Konfigurasi ──
DB_PATH = "Datamart_Final_Report.db"
OUTPUT_DIR = "output_si_channel"
OUTPUT_FILE = os.path.join(OUTPUT_DIR, "Top20_Detail_Paket.xlsx")

# Regex untuk illegal Excel characters
_ILLEGAL_CHARS_RE = re.compile(r"[\x00-\x08\x0b\x0c\x0e-\x1f\x7f-\x9f]")


def sanitize_str(val):
    """Strip illegal Excel chars from a single value."""
    if pd.isna(val):
        return val
    return _ILLEGAL_CHARS_RE.sub("", str(val))


# =====================================================================
# UNCENSORED NAME MATCHING
# =====================================================================

def extract_first_letters(name: str) -> list:
    """Extract visible chars per word from censored name."""
    words = str(name).split()
    result = []
    for w in words:
        visible = ""
        for c in w:
            if c == "*":
                break
            visible += c
        has_star = "*" in w
        result.append((visible, has_star))
    return result


def build_like_pattern(name: str) -> str:
    """Build SQL LIKE pattern: 'C*. S*******' -> 'C%. S%'"""
    parts = extract_first_letters(name)
    like_words = []
    for visible, is_censored in parts:
        if is_censored and visible:
            like_words.append(visible + "%")
        elif visible:
            like_words.append(visible)
        else:
            like_words.append("%")
    return " ".join(like_words)


def score_candidate(censored: str, candidate: str) -> float:
    """Score 0-100 how well candidate matches the censored name."""
    cens_words = str(censored).split()
    cand_words = str(candidate).split()
    score = 0.0

    # Word count match (max 30)
    if len(cens_words) == len(cand_words):
        score += 30.0
    else:
        score += max(0, 30.0 - abs(len(cens_words) - len(cand_words)) * 10)

    # First-letter per word (max 40)
    parts = extract_first_letters(censored)
    match_count = 0
    total = min(len(parts), len(cand_words))
    for i in range(total):
        vis, is_cens = parts[i]
        if not vis:
            continue
        cw = cand_words[i]
        if is_cens:
            if cw.upper().startswith(vis.rstrip(".,;:()").upper()):
                match_count += 1
        else:
            if vis.upper() == cw.upper():
                match_count += 1
    if total > 0:
        score += 40.0 * (match_count / total)

    # Length ratio (max 15)
    cand_len = len(candidate)
    if cand_len > 0:
        score += 15.0 * min(len(censored), cand_len) / max(len(censored), cand_len)

    # Sequence similarity (max 15)
    clean = censored.replace("*", "")
    score += 15.0 * SequenceMatcher(None, clean.upper(), candidate.upper()).ratio()

    return round(score, 2)


def predict_uncensored(conn, censored_name: str) -> str:
    """Predict the uncensored name using SQL LIKE + scoring."""
    like_pattern = build_like_pattern(censored_name).replace("'", "''")
    q = f"""
    SELECT DISTINCT Nama_Pemenang
    FROM datamart
    WHERE Nama_Pemenang NOT LIKE '%*%'
      AND Nama_Pemenang IS NOT NULL
      AND TRIM(Nama_Pemenang) != ''
      AND UPPER(Nama_Pemenang) LIKE UPPER('{like_pattern}')
    LIMIT 30
    """
    try:
        candidates = pd.read_sql(q, conn)["Nama_Pemenang"].tolist()
    except Exception:
        return ""

    if not candidates:
        return ""

    scored = [(c, score_candidate(censored_name, c)) for c in candidates]
    scored.sort(key=lambda x: -x[1])
    return scored[0][0]


def resolve_censored_names(conn, names: set) -> dict:
    """Resolve all censored names to best uncensored match. Returns dict."""
    cache = {}
    total = len(names)
    for i, nm in enumerate(sorted(names), 1):
        if i % 100 == 0 or i == total:
            print(f"       Resolving {i}/{total}...", flush=True)
        cache[nm] = predict_uncensored(conn, nm)
    return cache


# =====================================================================
# MAIN
# =====================================================================

def get_top20_names(si_csv_path: str) -> list:
    """Read SI CSV and return list of Nama_Pemenang."""
    if not os.path.exists(si_csv_path):
        return []
    df = pd.read_csv(si_csv_path)
    if "Nama_Pemenang" in df.columns:
        return df["Nama_Pemenang"].tolist()
    return []


def filter_detail(raw_df: pd.DataFrame, top_names: list, is_ict: bool) -> pd.DataFrame:
    """Filter raw data for Top 20 names and ICT/NonICT sector. Returns ALL columns."""
    if len(raw_df) == 0 or not top_names:
        return pd.DataFrame()

    mask_names = raw_df["Nama_Pemenang"].isin(top_names)
    mask_sector = raw_df["Is_ICT"] == is_ict
    df = raw_df[mask_names & mask_sector].copy()

    # Semua kolom asli dipertahankan, urutkan agar Nama_Pemenang di depan
    priority_cols = [
        "ID_RUP", "Nama_Pemenang", "Nama_Paket", "Kategori_Paket",
        "Pagu_Rp", "Jenis_Usaha", "Metode_Pemilihan", "Jenis_Pengadaan",
        "Tanggal_Pemilihan", "Instansi_Pembeli", "Satuan_Kerja", "Lokasi",
        "Nama_Produk", "Kategori_Produk", "Kuantitas_Produk",
        "Nama_Manufaktur", "Total_Pelaksanaan_Rp", "Sumber_Data", "Updated_At",
    ]
    # Pakai kolom prioritas yang ada, lalu tambah sisanya
    ordered = [c for c in priority_cols if c in df.columns]
    remaining = [c for c in df.columns if c not in ordered]
    df = df[ordered + remaining]

    df = df.sort_values(["Nama_Pemenang", "Pagu_Rp"], ascending=[True, False])
    df = df.reset_index(drop=True)
    return df


# Mapping: file identifiers
ZONA_MAP = {
    "Sumatera":       {"raw": "RAW_Sumatera_filtered.csv",
                       "si_ict": "SI_ICT_Sumatera.csv",
                       "si_non": "SI_NonICT_Sumatera.csv",
                       "sheet_ict": "ICT_Sumatera",
                       "sheet_non": "NonICT_Sumatera"},
    "Kalimantan":     {"raw": "RAW_Kalimantan_filtered.csv",
                       "si_ict": "SI_ICT_Kalimantan.csv",
                       "si_non": "SI_NonICT_Kalimantan.csv",
                       "sheet_ict": "ICT_Kalimantan",
                       "sheet_non": "NonICT_Kalimantan"},
    "Jawa":           {"raw": "RAW_Jawa_filtered.csv",
                       "si_ict": "SI_ICT_Jawa.csv",
                       "si_non": "SI_NonICT_Jawa.csv",
                       "sheet_ict": "ICT_Jawa",
                       "sheet_non": "NonICT_Jawa"},
    "Bali - NusRa":   {"raw": "RAW_Bali_-_NusRa_filtered.csv",
                       "si_ict": "SI_ICT_Bali_-_NusRa.csv",
                       "si_non": "SI_NonICT_Bali_-_NusRa.csv",
                       "sheet_ict": "ICT_Bali_NusRa",
                       "sheet_non": "NonICT_Bali_NusRa"},
    "Sulawesi":       {"raw": "RAW_Sulawesi_filtered.csv",
                       "si_ict": "SI_ICT_Sulawesi.csv",
                       "si_non": "SI_NonICT_Sulawesi.csv",
                       "sheet_ict": "ICT_Sulawesi",
                       "sheet_non": "NonICT_Sulawesi"},
    "Papua - Maluku": {"raw": "RAW_Papua_-_Maluku_filtered.csv",
                       "si_ict": "SI_ICT_Papua_-_Maluku.csv",
                       "si_non": "SI_NonICT_Papua_-_Maluku.csv",
                       "sheet_ict": "ICT_Papua_Maluku",
                       "sheet_non": "NonICT_Papua_Maluku"},
}

BIDANG_MAP = {
    "Pendidikan":         {"raw": "RAW_Bidang_Pendidikan_filtered.csv",
                           "si_ict": "SI_ICT_Bidang_Pendidikan.csv",
                           "si_non": "SI_NonICT_Bidang_Pendidikan.csv",
                           "sheet_ict": "ICT_Bid_Pendidikan",
                           "sheet_non": "NonICT_Bid_Pendidikan"},
    "Pertahanan":         {"raw": "RAW_Bidang_Pertahanan_filtered.csv",
                           "si_ict": "SI_ICT_Bidang_Pertahanan.csv",
                           "si_non": "SI_NonICT_Bidang_Pertahanan.csv",
                           "sheet_ict": "ICT_Bid_Pertahanan",
                           "sheet_non": "NonICT_Bid_Pertahanan"},
    "Kesehatan":          {"raw": "RAW_Bidang_Kesehatan_dan_Perlindungan_Sosial_filtered.csv",
                           "si_ict": "SI_ICT_Bidang_Kesehatan_dan_Perlindungan_Sosial.csv",
                           "si_non": "SI_NonICT_Bidang_Kesehatan_dan_Perlindungan_Sosial.csv",
                           "sheet_ict": "ICT_Bid_Kesehatan",
                           "sheet_non": "NonICT_Bid_Kesehatan"},
    "Subsidi Energi":     {"raw": "RAW_Bidang_Subsidi_Energi_dan_Non-Energi_filtered.csv",
                           "si_ict": "SI_ICT_Bidang_Subsidi_Energi_dan_Non-Energi.csv",
                           "si_non": "SI_NonICT_Bidang_Subsidi_Energi_dan_Non-Energi.csv",
                           "sheet_ict": "ICT_Bid_Energi",
                           "sheet_non": "NonICT_Bid_Energi"},
    "Ekonomi Infra":      {"raw": "RAW_Bidang_Pembangunan_Ekonomi_dan_Infrastruktur_filtered.csv",
                           "si_ict": "SI_ICT_Bidang_Pembangunan_Ekonomi_dan_Infrastruktur.csv",
                           "si_non": "SI_NonICT_Bidang_Pembangunan_Ekonomi_dan_Infrastruktur.csv",
                           "sheet_ict": "ICT_Bid_EkoInfra",
                           "sheet_non": "NonICT_Bid_EkoInfra"},
}


def main():
    print("=" * 70)
    print("  GENERATE TOP 20 PENYEDIA — DETAIL PAKET")
    print("  1 Excel, Multi-Sheet + Prediksi Uncensored")
    print("=" * 70)

    if not os.path.exists(OUTPUT_DIR):
        print(f"\n[ERROR] Folder '{OUTPUT_DIR}' tidak ditemukan.")
        return

    conn = sqlite3.connect(DB_PATH) if os.path.exists(DB_PATH) else None
    if conn:
        print(f"\n[INFO] Database {DB_PATH} terhubung untuk prediksi uncensored.")
    else:
        print(f"\n[WARN] {DB_PATH} tidak ditemukan. Kolom prediksi akan kosong.")

    # ── Phase 1: Collect all data + censored names ──
    print(f"\n[1/3] Collecting data & nama tersensor...")
    all_censored = set()
    sheets_data = {}  # {sheet_name: DataFrame}

    for section_name, mapping in [("DAERAH", ZONA_MAP), ("BIDANG", BIDANG_MAP)]:
        for label, info in mapping.items():
            raw_path = os.path.join(OUTPUT_DIR, info["raw"])
            if not os.path.exists(raw_path):
                print(f"  [SKIP] {info['raw']} tidak ditemukan")
                continue

            raw_df = pd.read_csv(raw_path, low_memory=False)
            raw_df["Pagu_Rp"] = pd.to_numeric(raw_df["Pagu_Rp"], errors="coerce").fillna(0)

            # ICT
            ict_names = get_top20_names(os.path.join(OUTPUT_DIR, info["si_ict"]))
            if ict_names:
                df_ict = filter_detail(raw_df, ict_names, is_ict=True)
                if len(df_ict) > 0:
                    sheets_data[info["sheet_ict"]] = df_ict
                    cens = df_ict["Nama_Pemenang"][
                        df_ict["Nama_Pemenang"].astype(str).str.contains(r"\*", na=False)
                    ].unique()
                    all_censored.update(cens)
                    print(f"  [OK] {info['sheet_ict']}: {len(df_ict):,} paket "
                          f"({len(ict_names)} penyedia)")

            # Non-ICT
            non_names = get_top20_names(os.path.join(OUTPUT_DIR, info["si_non"]))
            if non_names:
                df_non = filter_detail(raw_df, non_names, is_ict=False)
                if len(df_non) > 0:
                    sheets_data[info["sheet_non"]] = df_non
                    cens = df_non["Nama_Pemenang"][
                        df_non["Nama_Pemenang"].astype(str).str.contains(r"\*", na=False)
                    ].unique()
                    all_censored.update(cens)
                    print(f"  [OK] {info['sheet_non']}: {len(df_non):,} paket "
                          f"({len(non_names)} penyedia)")

    print(f"\n  Total sheets: {len(sheets_data)}")
    print(f"  Total nama tersensor unik: {len(all_censored)}")

    # ── Phase 2: Resolve censored names ──
    uncensored_cache = {}
    if conn and all_censored:
        print(f"\n[2/3] Prediksi uncensored untuk {len(all_censored)} nama...")
        uncensored_cache = resolve_censored_names(conn, all_censored)
        n_ok = sum(1 for v in uncensored_cache.values() if v)
        print(f"       Resolved: {n_ok}/{len(all_censored)}")
        conn.close()
    else:
        print(f"\n[2/3] Skip prediksi uncensored (tidak ada nama tersensor / DB).")

    # ── Phase 3: Write Excel ──
    print(f"\n[3/3] Writing Excel ke {OUTPUT_FILE}...")

    with pd.ExcelWriter(OUTPUT_FILE, engine="openpyxl") as writer:
        for sheet_name, df in sheets_data.items():
            # Add Prediksi_Nama_Asli column
            def predict(nm):
                nm_str = str(nm)
                if "*" not in nm_str:
                    return nm_str
                return uncensored_cache.get(nm_str, "") or ""

            df = df.copy()
            df.insert(1, "Prediksi_Nama_Asli",
                      df["Nama_Pemenang"].apply(predict))

            # Sanitize all string columns
            for col in df.select_dtypes(include=["object"]).columns:
                df[col] = df[col].apply(sanitize_str)

            # Truncate sheet name to 31 chars (Excel limit)
            sname = sheet_name[:31]
            df.to_excel(writer, sheet_name=sname, index=False)

            # Auto-adjust column widths
            ws = writer.sheets[sname]
            for col_cells in ws.columns:
                col_letter = col_cells[0].column_letter
                max_len = 0
                for cell in col_cells:
                    try:
                        val = str(cell.value) if cell.value else ""
                        max_len = max(max_len, len(val))
                    except Exception:
                        pass
                ws.column_dimensions[col_letter].width = min(max_len + 2, 55)

            print(f"  [OK] Sheet '{sname}': {len(df):,} rows")

    size_mb = os.path.getsize(OUTPUT_FILE) / (1024 * 1024)
    print(f"\n{'=' * 70}")
    print(f"RINGKASAN")
    print(f"   File output : {OUTPUT_FILE}")
    print(f"   Ukuran      : {size_mb:.1f} MB")
    print(f"   Jumlah sheet: {len(sheets_data)}")
    print(f"{'=' * 70}")
    print(f"\n[DONE] Selesai.")


if __name__ == "__main__":
    main()
