"""
=============================================================================
CLEANUP OUTPUT CSV — Post-Processing
=============================================================================
Script ini TIDAK memodifikasi notebook.
Dijalankan SETELAH notebook selesai export ke folder output_si_channel/.

Logika:
  1. File ZONA (daerah):  RAW_<Zona>_filtered.csv
     → Drop baris yang Instansi_Pembeli TIDAK mengandung "Provinsi", "Kab.", "Kota "
       (karena itu K/L, bukan daerah)

  2. File BIDANG (K/L):   RAW_Bidang_<Bidang>_filtered.csv
     → Drop baris yang Instansi_Pembeli MENGANDUNG "Provinsi", "Kab.", "Kota "
       (karena itu daerah, bukan K/L)

Output: file CSV yang sama di-overwrite (backup otomatis di subfolder _backup/)
=============================================================================
"""

import pandas as pd
import os
import re
import shutil
from datetime import datetime

# ── Konfigurasi ──
OUTPUT_DIR = "output_si_channel"
BACKUP_DIR = os.path.join(OUTPUT_DIR, "_backup")

# Pattern untuk mendeteksi instansi daerah
DAERAH_PATTERNS = ["Provinsi ", "Kab. ", "Kota "]


def is_daerah(instansi: str) -> bool:
    """Return True jika Instansi_Pembeli mengandung unsur daerah."""
    if pd.isna(instansi):
        return False
    s = str(instansi)
    return any(pat in s for pat in DAERAH_PATTERNS)


def cleanup_csv(filepath: str, mode: str) -> dict:
    """
    Cleanup satu file CSV.
    mode: 'zona' atau 'bidang'
    Returns dict dengan statistik.
    """
    df = pd.read_csv(filepath)
    n_before = len(df)

    if "Instansi_Pembeli" not in df.columns:
        print(f"   [WARN] Kolom 'Instansi_Pembeli' tidak ditemukan, skip.")
        return {"file": filepath, "before": n_before, "after": n_before, "dropped": 0}

    if mode == "zona":
        # ZONA (daerah): KEEP hanya yang mengandung Provinsi/Kab./Kota
        #                DROP yang TIDAK mengandung (= K/L)
        mask_keep = df["Instansi_Pembeli"].apply(is_daerah)
        df_clean = df[mask_keep].copy()
    elif mode == "bidang":
        # BIDANG (K/L): DROP yang mengandung Provinsi/Kab./Kota (= daerah)
        mask_drop = df["Instansi_Pembeli"].apply(is_daerah)
        df_clean = df[~mask_drop].copy()
    else:
        raise ValueError(f"Mode tidak dikenal: {mode}")

    n_after = len(df_clean)
    n_dropped = n_before - n_after

    # Backup file asli
    os.makedirs(BACKUP_DIR, exist_ok=True)
    backup_name = os.path.basename(filepath)
    shutil.copy2(filepath, os.path.join(BACKUP_DIR, backup_name))

    # Overwrite file dengan data yang sudah dibersihkan
    df_clean.to_csv(filepath, index=False)

    return {"file": filepath, "before": n_before, "after": n_after, "dropped": n_dropped}


def main():
    print("=" * 70)
    print("  CLEANUP OUTPUT CSV — Post-Processing")
    print(f"  {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 70)

    if not os.path.exists(OUTPUT_DIR):
        print(f"\n[ERROR] Folder '{OUTPUT_DIR}' tidak ditemukan. Jalankan notebook dulu.")
        return

    # Kumpulkan semua file RAW
    all_files = sorted(os.listdir(OUTPUT_DIR))
    raw_files = [f for f in all_files if f.startswith("RAW_") and f.endswith(".csv")]

    if not raw_files:
        print(f"\n[ERROR] Tidak ada file RAW_*.csv di '{OUTPUT_DIR}'.")
        return

    # Kategorikan: zona vs bidang
    zona_files = [f for f in raw_files if not f.startswith("RAW_Bidang_")]
    bidang_files = [f for f in raw_files if f.startswith("RAW_Bidang_")]

    results = []

    # ── Zona (Daerah) ──
    print(f"\n{'-' * 70}")
    print(f"[ZONA / DAERAH] -- Drop instansi yang BUKAN daerah")
    print(f"{'-' * 70}")
    for f in zona_files:
        fp = os.path.join(OUTPUT_DIR, f)
        r = cleanup_csv(fp, mode="zona")
        results.append(r)
        status = "[OK]" if r["dropped"] > 0 else "[--]"
        print(f"   {status} {f}: {r['before']:,} -> {r['after']:,} ({r['dropped']:,} dropped)")

    # ── Bidang (K/L) ──
    print(f"\n{'-' * 70}")
    print(f"[BIDANG / K/L] -- Drop instansi yang BUKAN K/L (= daerah)")
    print(f"{'-' * 70}")
    for f in bidang_files:
        fp = os.path.join(OUTPUT_DIR, f)
        r = cleanup_csv(fp, mode="bidang")
        results.append(r)
        status = "[OK]" if r["dropped"] > 0 else "[--]"
        print(f"   {status} {f}: {r['before']:,} -> {r['after']:,} ({r['dropped']:,} dropped)")

    # ── Ringkasan ──
    total_dropped = sum(r["dropped"] for r in results)
    total_before = sum(r["before"] for r in results)
    total_after = sum(r["after"] for r in results)

    print(f"\n{'=' * 70}")
    print(f"RINGKASAN CLEANUP")
    print(f"   Total file diproses : {len(results)}")
    print(f"   Total baris sebelum : {total_before:,}")
    print(f"   Total baris sesudah : {total_after:,}")
    print(f"   Total baris dropped : {total_dropped:,}")
    print(f"   Backup tersimpan di : {BACKUP_DIR}/")
    print(f"{'=' * 70}")
    print(f"\n[DONE] Selesai. File asli sudah di-backup, file output sudah dibersihkan.")


if __name__ == "__main__":
    main()
