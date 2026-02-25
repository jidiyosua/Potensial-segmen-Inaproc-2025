"""
=============================================================================
GENERATE SI DETAIL EXCEL
=============================================================================
Script lanjutan dari SI_Channel_Potensial_INAPROC_2025.ipynb
Membaca RAW CSV per zona/bidang, lalu membuat Excel detail per SI Pemenang.

Output per file (ICT dan Non-ICT terpisah):
  - Nama_Pemenang
  - Jumlah_Kontrak
  - Top_Selling_Product   (Nama_Paket paling sering)
  - Klien                 (Daftar Satuan Kerja unik)
  - Total_Dealing_Rp      (Total Pagu)
  - Top_Product_Value_Rp  (Nilai kontrak tertinggi)

Tersimpan di: output_si_channel/detail_excel/
=============================================================================
"""

import pandas as pd
import os
import glob
import re

# Regex to match illegal Excel characters (control chars except tab/newline/carriage return)
_ILLEGAL_CHARS_RE = re.compile(
    r"[\x00-\x08\x0b\x0c\x0e-\x1f\x7f-\x9f]"
)


def sanitize_for_excel(df: pd.DataFrame) -> pd.DataFrame:
    """Strip illegal characters from all string columns."""
    df = df.copy()
    for col in df.select_dtypes(include=["object"]).columns:
        df[col] = df[col].apply(
            lambda x: _ILLEGAL_CHARS_RE.sub("", str(x)) if pd.notna(x) else x
        )
    return df

# ── Konfigurasi ──
OUTPUT_DIR = "output_si_channel"
DETAIL_DIR = os.path.join(OUTPUT_DIR, "detail_excel")


def fmt_rp(v):
    """Format angka ke Rupiah readable."""
    if pd.isna(v) or v == 0:
        return "Rp 0"
    a = abs(v)
    if a >= 1e12:
        return f"Rp {v/1e12:,.2f} T"
    if a >= 1e9:
        return f"Rp {v/1e9:,.2f} M"
    if a >= 1e6:
        return f"Rp {v/1e6:,.1f} Jt"
    return f"Rp {v:,.0f}"


def build_si_detail(df_raw: pd.DataFrame, min_satker: int = 5) -> pd.DataFrame:
    """
    Aggregate data per Nama_Pemenang.
    
    Returns DataFrame with columns:
    - Nama_Pemenang
    - Jumlah_Kontrak
    - Top_Selling_Product
    - Klien (Satuan Kerja)
    - Total_Dealing_Rp
    - Top_Product_Value_Rp
    """
    if len(df_raw) == 0:
        return pd.DataFrame()

    # Group by Nama_Pemenang
    groups = df_raw.groupby("Nama_Pemenang")

    records = []
    for pemenang, grp in groups:
        jumlah_kontrak = len(grp)
        jumlah_satker = grp["Satuan_Kerja"].nunique()

        # filter min satker
        if jumlah_satker < min_satker:
            continue

        # Top Selling Product: Nama_Paket paling sering muncul
        top_product = grp["Nama_Paket"].value_counts().index[0] if len(grp) > 0 else ""

        # Klien: Daftar Satuan_Kerja unik, semicolon-separated
        klien_list = sorted(grp["Satuan_Kerja"].dropna().unique().tolist())
        klien_str = "; ".join(klien_list)

        # Total Dealing
        total_dealing = grp["Pagu_Rp"].sum()

        # Top Product Value: nilai kontrak tertinggi (max Pagu_Rp single row)
        top_product_value = grp["Pagu_Rp"].max()

        # Nama paket dari kontrak tertinggi
        idx_max = grp["Pagu_Rp"].idxmax()
        top_value_product = grp.loc[idx_max, "Nama_Paket"] if pd.notna(idx_max) else ""

        records.append({
            "Nama_Pemenang": pemenang,
            "Jumlah_Kontrak": jumlah_kontrak,
            "Jumlah_Klien": jumlah_satker,
            "Top_Selling_Product": top_product,
            "Klien": klien_str,
            "Total_Dealing_Rp": total_dealing,
            "Top_Product_Value_Rp": top_product_value,
            "Top_Value_Product_Name": top_value_product,
        })

    if not records:
        return pd.DataFrame()

    result = pd.DataFrame(records)
    result = result.sort_values("Total_Dealing_Rp", ascending=False).reset_index(drop=True)
    result.index = result.index + 1
    result.index.name = "Rank"
    return result


def process_raw_file(filepath: str) -> dict:
    """
    Process satu RAW CSV: buat detail Excel untuk ICT dan Non-ICT.
    Returns stats dict.
    """
    fname = os.path.basename(filepath)
    df = pd.read_csv(filepath)

    # Check required columns
    required = ["Nama_Pemenang", "Nama_Paket", "Satuan_Kerja", "Pagu_Rp", "Is_ICT"]
    missing = [c for c in required if c not in df.columns]
    if missing:
        print(f"  [WARN] {fname}: kolom {missing} tidak ditemukan, skip.")
        return {"file": fname, "ict": 0, "non_ict": 0}

    # Ensure Pagu_Rp is numeric
    df["Pagu_Rp"] = pd.to_numeric(df["Pagu_Rp"], errors="coerce").fillna(0)

    # Derive label from filename
    # RAW_Jawa_filtered.csv -> Jawa
    # RAW_Bidang_Pendidikan_filtered.csv -> Bidang_Pendidikan
    label = fname.replace("RAW_", "").replace("_filtered.csv", "")

    stats = {"file": fname, "ict": 0, "non_ict": 0}

    for sektor, sektor_label in [("ICT", "ICT"), ("Non-ICT", "NonICT")]:
        if "Is_ICT" in df.columns:
            if sektor == "ICT":
                df_sector = df[df["Is_ICT"] == True].copy()
            else:
                df_sector = df[df["Is_ICT"] == False].copy()
        elif "Sektor" in df.columns:
            df_sector = df[df["Sektor"] == sektor].copy()
        else:
            continue

        detail = build_si_detail(df_sector, min_satker=5)

        if len(detail) == 0:
            continue

        # Save as Excel
        out_name = f"Detail_{sektor_label}_{label}.xlsx"
        out_path = os.path.join(DETAIL_DIR, out_name)

        with pd.ExcelWriter(out_path, engine="openpyxl") as writer:
            sanitize_for_excel(detail).to_excel(writer, sheet_name="SI Detail")

            # Auto-adjust column widths
            ws = writer.sheets["SI Detail"]
            for col_cells in ws.columns:
                max_len = 0
                col_letter = col_cells[0].column_letter
                for cell in col_cells:
                    try:
                        val = str(cell.value) if cell.value else ""
                        max_len = max(max_len, len(val))
                    except Exception:
                        pass
                # Cap column width
                adjusted = min(max_len + 2, 60)
                ws.column_dimensions[col_letter].width = adjusted

        if sektor == "ICT":
            stats["ict"] = len(detail)
        else:
            stats["non_ict"] = len(detail)

        print(f"  [OK] {out_name}: {len(detail)} pemenang")

    return stats


def main():
    print("=" * 70)
    print("  GENERATE SI DETAIL EXCEL")
    print("  Membuat Excel detail per SI Pemenang (ICT & Non-ICT)")
    print("=" * 70)

    if not os.path.exists(OUTPUT_DIR):
        print(f"\n[ERROR] Folder '{OUTPUT_DIR}' tidak ditemukan.")
        return

    os.makedirs(DETAIL_DIR, exist_ok=True)

    # Collect RAW files
    raw_files = sorted(glob.glob(os.path.join(OUTPUT_DIR, "RAW_*.csv")))
    if not raw_files:
        print(f"\n[ERROR] Tidak ada file RAW_*.csv di '{OUTPUT_DIR}'.")
        return

    # Separate zona vs bidang
    zona_files = [f for f in raw_files if "Bidang_" not in os.path.basename(f)]
    bidang_files = [f for f in raw_files if "Bidang_" in os.path.basename(f)]

    all_stats = []

    # Zona (Daerah)
    print(f"\n{'-' * 70}")
    print(f"[ZONA / DAERAH]")
    print(f"{'-' * 70}")
    for f in zona_files:
        stats = process_raw_file(f)
        all_stats.append(stats)

    # Bidang (K/L)
    print(f"\n{'-' * 70}")
    print(f"[BIDANG / K-L]")
    print(f"{'-' * 70}")
    for f in bidang_files:
        stats = process_raw_file(f)
        all_stats.append(stats)

    # Summary
    total_ict = sum(s["ict"] for s in all_stats)
    total_noict = sum(s["non_ict"] for s in all_stats)
    n_files = len([s for s in all_stats if s["ict"] > 0 or s["non_ict"] > 0])

    print(f"\n{'=' * 70}")
    print(f"RINGKASAN")
    print(f"   File Excel dibuat   : {n_files * 2} (ICT + Non-ICT)")
    print(f"   Total SI ICT        : {total_ict}")
    print(f"   Total SI Non-ICT    : {total_noict}")
    print(f"   Output folder       : {DETAIL_DIR}/")
    print(f"{'=' * 70}")

    # List generated files
    generated = sorted(os.listdir(DETAIL_DIR))
    print(f"\nFile yang dihasilkan:")
    for g in generated:
        size = os.path.getsize(os.path.join(DETAIL_DIR, g))
        print(f"  {g} ({size:,} bytes)")

    print(f"\n[DONE] Selesai.")


if __name__ == "__main__":
    main()
