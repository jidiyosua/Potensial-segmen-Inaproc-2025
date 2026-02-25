"""
=============================================================================
UNMASK NAMA PEMENANG — Mengganti nama tersensor dengan nama asli
=============================================================================
Script ini membaca CSV output dari notebook SI_Channel dan mencocokkan
Nama_Pemenang yang tersensor (mengandung *) dengan nama asli dari database
SQLite Datamart_Final_Report.db.

Strategi matching:
  1. Kumpulkan SEMUA nama tersensor unik dari seluruh CSV
  2. Untuk setiap nama, build SQL LIKE pattern dari huruf pertama tiap kata
  3. Cari kandidat nama asli di DB, score berdasarkan kesamaan struktur
  4. Build lookup dict: censored -> best_match
  5. Apply ke semua CSV secara vectorized (cepat)

Output: subfolder output_si_channel/unmasked/
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
UNMASKED_DIR = os.path.join(OUTPUT_DIR, "unmasked")


# =====================================================================
# MATCHING FUNCTIONS
# =====================================================================

def extract_first_letters(censored_name: str) -> list:
    """
    Extract huruf-huruf yang terlihat dari setiap kata.
    'C*. S******* S*******' -> [('C.', True), ('S', True), ('S', True)]
    Returns list of (visible_prefix, is_censored) tuples per word.
    """
    words = str(censored_name).split()
    result = []
    for w in words:
        visible = ""
        has_star = False
        for c in w:
            if c == "*":
                has_star = True
            else:
                visible += c
        result.append((visible, has_star or ("*" in w)))
    return result


def build_like_pattern(censored_name: str) -> str:
    """
    Build SQL LIKE pattern dari nama tersensor.
    'C*. S******* S*******' -> 'C%. S% S%'
    """
    parts = extract_first_letters(censored_name)
    like_words = []
    for visible, is_censored in parts:
        if is_censored and visible:
            like_words.append(visible + "%")
        elif visible:
            like_words.append(visible)
        else:
            like_words.append("%")
    return " ".join(like_words)


def score_candidate(censored_name: str, candidate: str) -> float:
    """
    Score seberapa mirip kandidat dengan nama tersensor.
    Returns score 0-100.
    """
    cens_words = str(censored_name).split()
    cand_words = str(candidate).split()

    score = 0.0

    # Factor 1: Jumlah kata (max 30)
    if len(cens_words) == len(cand_words):
        score += 30.0
    else:
        diff = abs(len(cens_words) - len(cand_words))
        score += max(0, 30.0 - diff * 10)

    # Factor 2: Huruf pertama per kata cocok (max 40)
    cens_parts = extract_first_letters(censored_name)
    match_count = 0
    total_compare = min(len(cens_parts), len(cand_words))

    for i in range(total_compare):
        visible, is_censored = cens_parts[i]
        cand_word = cand_words[i]
        if not visible:
            continue
        if is_censored:
            vis_clean = visible.rstrip(".,;:()")
            cand_clean = cand_word.rstrip(".,;:()")
            if cand_clean.upper().startswith(vis_clean.upper()):
                match_count += 1
        else:
            if visible.upper() == cand_word.upper():
                match_count += 1

    if total_compare > 0:
        score += 40.0 * (match_count / total_compare)

    # Factor 3: Panjang total (max 15)
    cens_len = len(censored_name)
    cand_len = len(candidate)
    if cand_len > 0:
        ratio = min(cens_len, cand_len) / max(cens_len, cand_len)
        score += 15.0 * ratio

    # Factor 4: Sequence similarity (max 15)
    cens_clean = censored_name.replace("*", "")
    sim = SequenceMatcher(None, cens_clean.upper(), candidate.upper()).ratio()
    score += 15.0 * sim

    return round(score, 2)


def find_candidates_sql(conn, censored_name: str, limit: int = 5) -> list:
    """
    Cari kandidat nama asli dari DB menggunakan SQL LIKE pattern.
    Returns list of (candidate_name, score) sorted by score desc.
    """
    like_pattern = build_like_pattern(censored_name)
    like_safe = like_pattern.replace("'", "''")

    q = f"""
    SELECT DISTINCT Nama_Pemenang
    FROM datamart
    WHERE Nama_Pemenang NOT LIKE '%*%'
      AND Nama_Pemenang IS NOT NULL
      AND TRIM(Nama_Pemenang) != ''
      AND UPPER(Nama_Pemenang) LIKE UPPER('{like_safe}')
    LIMIT 50
    """
    try:
        df = pd.read_sql(q, conn)
        candidates = df["Nama_Pemenang"].tolist()
    except Exception:
        candidates = []

    scored = [(cand, score_candidate(censored_name, cand)) for cand in candidates]
    scored.sort(key=lambda x: -x[1])
    return scored[:limit]


# =====================================================================
# MAIN LOGIC
# =====================================================================

def collect_all_censored_names(csv_files: list) -> set:
    """Scan all CSVs and collect unique censored Nama_Pemenang."""
    censored = set()
    for fp in csv_files:
        try:
            df = pd.read_csv(fp, usecols=["Nama_Pemenang"], low_memory=False)
            mask = df["Nama_Pemenang"].astype(str).str.contains(r"\*", na=False)
            names = df.loc[mask, "Nama_Pemenang"].unique()
            censored.update(names)
        except Exception:
            pass
    return censored


def resolve_all_censored(conn, censored_names: set) -> dict:
    """
    Resolve all censored names to their best match.
    Returns dict: {censored_name: {best_match, best_score, candidates, method}}
    """
    results = {}
    total = len(censored_names)

    for i, nm in enumerate(sorted(censored_names), 1):
        if i % 50 == 0 or i == total:
            print(f"       Resolving {i}/{total}...", flush=True)

        candidates = find_candidates_sql(conn, nm, limit=5)

        if candidates:
            results[nm] = {
                "best_match": candidates[0][0],
                "best_score": candidates[0][1],
                "candidates": candidates,
                "method": "sql",
            }
        else:
            results[nm] = {
                "best_match": None,
                "best_score": 0,
                "candidates": [],
                "method": "none",
            }

    return results


def apply_unmask_to_csv(filepath: str, lookup: dict) -> dict:
    """
    Apply unmasking to one CSV file using pre-built lookup dict.
    Uses vectorized .map() for speed.
    Returns stats dict.
    """
    fname = os.path.basename(filepath)
    df = pd.read_csv(filepath, low_memory=False)

    if "Nama_Pemenang" not in df.columns:
        return {"file": fname, "total": len(df), "censored": 0, "matched": 0}

    names = df["Nama_Pemenang"].astype(str)
    is_censored = names.str.contains(r"\*", na=False)
    n_censored = is_censored.sum()

    # Build mapping columns via vectorized map
    def get_best_match(nm):
        if nm in lookup and lookup[nm]["best_match"]:
            return lookup[nm]["best_match"]
        return nm  # return original if no match

    def get_score(nm):
        if nm in lookup and lookup[nm]["best_match"]:
            return lookup[nm]["best_score"]
        return 100.0 if "*" not in nm else 0.0

    def get_method(nm):
        if "*" not in nm:
            return "original"
        if nm in lookup and lookup[nm]["best_match"]:
            return lookup[nm]["method"]
        return "none"

    def get_others(nm):
        if nm in lookup and lookup[nm]["candidates"]:
            others = [f"{c[0]} ({c[1]})" for c in lookup[nm]["candidates"][1:4]]
            return " | ".join(others)
        return ""

    df["Nama_Pemenang_Asli"] = names.map(get_best_match)
    df["Match_Score"] = names.map(get_score)
    df["Match_Method"] = names.map(get_method)
    df["Kandidat_Lain"] = names.map(get_others)

    # Mark unmatched censored names
    still_censored = df["Nama_Pemenang_Asli"].str.contains(r"\*", na=False)
    df.loc[still_censored, "Nama_Pemenang_Asli"] = (
        "[TIDAK DITEMUKAN] " + df.loc[still_censored, "Nama_Pemenang_Asli"]
    )

    n_matched = n_censored - still_censored.sum()

    # Save
    out_path = os.path.join(UNMASKED_DIR, fname)
    df.to_csv(out_path, index=False)

    return {"file": fname, "total": len(df), "censored": n_censored, "matched": n_matched}


def main():
    print("=" * 70)
    print("  UNMASK NAMA PEMENANG")
    print("  Mencocokkan nama tersensor dengan data asli dari DB")
    print("=" * 70)

    if not os.path.exists(DB_PATH):
        print(f"\n[ERROR] {DB_PATH} tidak ditemukan.")
        return

    if not os.path.exists(OUTPUT_DIR):
        print(f"\n[ERROR] Folder {OUTPUT_DIR} tidak ditemukan.")
        return

    os.makedirs(UNMASKED_DIR, exist_ok=True)

    # Collect all CSV files
    si_csvs = sorted(glob.glob(os.path.join(OUTPUT_DIR, "SI_*.csv")))
    raw_csvs = sorted(glob.glob(os.path.join(OUTPUT_DIR, "RAW_*.csv")))
    all_csvs = si_csvs + raw_csvs

    print(f"\n[1/4] Scanning {len(all_csvs)} CSV files untuk nama tersensor...")
    censored_names = collect_all_censored_names(all_csvs)
    print(f"       Ditemukan {len(censored_names):,} nama tersensor unik.")

    if not censored_names:
        print("\n[INFO] Tidak ada nama tersensor. Semua sudah bersih.")
        return

    # Resolve all at once
    print(f"\n[2/4] Mencocokkan {len(censored_names):,} nama dengan database...")
    conn = sqlite3.connect(DB_PATH)
    lookup = resolve_all_censored(conn, censored_names)
    conn.close()

    n_resolved = sum(1 for v in lookup.values() if v["best_match"])
    n_unresolved = len(lookup) - n_resolved
    print(f"       Resolved: {n_resolved:,} | Unresolved: {n_unresolved:,}")

    # Apply to SI files
    print(f"\n[3/4] Applying unmask ke SI files...")
    print(f"{'-' * 70}")
    all_stats = []
    for fp in si_csvs:
        result = apply_unmask_to_csv(fp, lookup)
        all_stats.append(result)
        if result["censored"] > 0:
            print(f"  [OK] {result['file']}: "
                  f"{result['censored']} tersensor, {result['matched']} matched")
        else:
            print(f"  [--] {result['file']}: tidak ada nama tersensor")

    # Apply to RAW files
    print(f"\n[4/4] Applying unmask ke RAW files...")
    print(f"{'-' * 70}")
    for fp in raw_csvs:
        fname = os.path.basename(fp)
        print(f"  Processing {fname}...", end=" ", flush=True)
        result = apply_unmask_to_csv(fp, lookup)
        all_stats.append(result)
        if result["censored"] > 0:
            print(f"{result['censored']:,} tersensor, {result['matched']:,} matched")
        else:
            print("tidak ada nama tersensor")

    # Summary
    total_censored = sum(r["censored"] for r in all_stats)
    total_matched = sum(r["matched"] for r in all_stats)

    print(f"\n{'=' * 70}")
    print(f"RINGKASAN UNMASK")
    print(f"   File diproses       : {len(all_stats)}")
    print(f"   Nama tersensor total: {total_censored:,}")
    print(f"   Berhasil dicocokkan : {total_matched:,}")
    if total_censored > 0:
        pct = total_matched / total_censored * 100
        print(f"   Match rate          : {pct:.1f}%")
    print(f"   Nama unik resolved : {n_resolved:,}/{len(lookup):,}")
    print(f"   Output folder       : {UNMASKED_DIR}/")
    print(f"{'=' * 70}")

    # Detail matching report
    print(f"\nDETAIL PENCOCOKAN ({len(lookup)} nama unik tersensor)")
    print(f"{'-' * 70}")
    for censored in sorted(lookup.keys()):
        r = lookup[censored]
        if r["candidates"]:
            best = r["candidates"][0]
            print(f"\n  {censored}")
            for i, (name, score) in enumerate(r["candidates"], 1):
                marker = " <<< BEST" if i == 1 else ""
                print(f"    [{i}] {name}  (score: {score}){marker}")
        else:
            print(f"\n  {censored}")
            print(f"    [!] Tidak ada kandidat ditemukan")

    print(f"\n[DONE] Output di: {UNMASKED_DIR}/")
    print("Kolom tambahan: Nama_Pemenang_Asli, Match_Score, Match_Method, Kandidat_Lain")


if __name__ == "__main__":
    main()
