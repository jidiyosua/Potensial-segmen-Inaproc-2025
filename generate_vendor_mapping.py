"""
═══════════════════════════════════════════════════════════════════════════
  SCRIPT: Generate Vendor Name Mapping (Offline Fuzzy Matching)
  Input:  Datamart_Final_Report.db (atau Datamart_Lite.db)
  Output: vendor_mapping.json
  
  Jalankan 1x di lokal sebelum deploy:
    python generate_vendor_mapping.py
  
  Hasil vendor_mapping.json di-commit ke GitHub bersama app.py
═══════════════════════════════════════════════════════════════════════════
"""

import sqlite3
import json
import os
import sys
import time
from difflib import SequenceMatcher

# ─── CONFIG ───
DB_CANDIDATES = ["Datamart_Lite.db", "Datamart_Final_Report.db"]
OUTPUT_FILE = "vendor_mapping.json"
THRESHOLD = 0.60  # minimum confidence score

def find_db():
    for db in DB_CANDIDATES:
        if os.path.exists(db):
            return db
    return None

def generate_mapping():
    db_path = find_db()
    if not db_path:
        print(f"❌ Database tidak ditemukan! Cari: {DB_CANDIDATES}")
        sys.exit(1)

    print(f"📂 Database: {db_path} ({os.path.getsize(db_path)/1024/1024:.1f} MB)")

    # ── 1. Load distinct nama pemenang ──
    conn = sqlite3.connect(db_path)
    tables = conn.execute("SELECT name FROM sqlite_master WHERE type='table'").fetchall()
    tbl = tables[0][0]
    
    # Check if Nama_Pemenang column exists
    pragma = conn.execute(f"PRAGMA table_info([{tbl}])").fetchall()
    col_names = [r[1] for r in pragma]
    if "Nama_Pemenang" not in col_names:
        print(f"❌ Kolom Nama_Pemenang tidak ada! Kolom: {col_names}")
        sys.exit(1)

    # Get DISTINCT names only — much faster than loading all rows
    names_df = conn.execute(f"SELECT DISTINCT [Nama_Pemenang] FROM [{tbl}] WHERE [Nama_Pemenang] IS NOT NULL AND [Nama_Pemenang] != ''").fetchall()
    conn.close()

    all_names = [r[0].strip() for r in names_df if r[0] and r[0].strip()]
    print(f"📊 Total nama unik: {len(all_names):,}")

    censored = [n for n in all_names if "*" in n]
    clean = [n for n in all_names if "*" not in n]
    print(f"   🔒 Tersensor: {len(censored):,}")
    print(f"   ✅ Bersih: {len(clean):,}")

    if not censored:
        print("ℹ️  Tidak ada nama tersensor. Buat mapping kosong.")
        with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
            json.dump({}, f)
        print(f"✅ {OUTPUT_FILE} created (empty)")
        return

    # ── 2. Build prefix index ──
    print(f"\n🔨 Building prefix index...")
    prefix_index = {}
    for cn in clean:
        # Index by 1-char and 2-char prefix
        if len(cn) >= 1:
            p1 = cn[0].upper()
            prefix_index.setdefault(p1, []).append(cn)
        if len(cn) >= 2:
            p2 = cn[:2].upper()
            prefix_index.setdefault(p2, []).append(cn)

    # Deduplicate
    for k in prefix_index:
        prefix_index[k] = list(set(prefix_index[k]))

    print(f"   Index size: {len(prefix_index)} prefixes")

    # ── 3. Fuzzy match ──
    print(f"\n🔍 Fuzzy matching {len(censored):,} nama tersensor...")
    mapping = {}
    matched = 0
    skipped = 0
    t0 = time.time()

    for idx, cname in enumerate(censored):
        # Progress
        if (idx + 1) % 5000 == 0 or idx == 0:
            elapsed = time.time() - t0
            pct = (idx + 1) / len(censored) * 100
            rate = (idx + 1) / elapsed if elapsed > 0 else 0
            eta = (len(censored) - idx - 1) / rate if rate > 0 else 0
            print(f"   [{pct:5.1f}%] {idx+1:,}/{len(censored):,} | "
                  f"matched: {matched:,} | {rate:.0f}/sec | ETA: {eta:.0f}s")

        # Extract prefix (chars before first *)
        prefix = ""
        for ch in cname:
            if ch != "*":
                prefix += ch
            else:
                break
        prefix = prefix.strip()

        if not prefix:
            skipped += 1
            continue

        # Get candidates — try 2-char first, fallback to 1-char
        pk2 = prefix[:2].upper() if len(prefix) >= 2 else None
        pk1 = prefix[0].upper()

        candidates = []
        if pk2 and pk2 in prefix_index:
            candidates = prefix_index[pk2]
        elif pk1 in prefix_index:
            candidates = prefix_index[pk1]

        if not candidates:
            skipped += 1
            continue

        # Limit candidates to prevent slowness (max 500)
        if len(candidates) > 500:
            # Pre-filter: only candidates starting with same prefix
            candidates = [c for c in candidates if c.upper().startswith(prefix.upper())]
            if not candidates:
                skipped += 1
                continue

        # Score each candidate
        visible = [(i, c) for i, c in enumerate(cname) if c != "*"]
        clean_chars = cname.replace("*", "").upper()

        best_match, best_score = None, 0
        for cand in candidates:
            score = 0.0
            cand_upper = cand.upper()

            # 1. Prefix match (0.45)
            if prefix and cand_upper.startswith(prefix.upper()):
                score += 0.45

            # 2. Character position match (0.25)
            if visible:
                char_m = sum(1 for pos, ch in visible
                             if pos < len(cand) and cand_upper[pos] == ch.upper())
                score += 0.25 * (char_m / len(visible))

            # 3. SequenceMatcher (0.30) — only if score already promising
            if score >= 0.30:
                ratio = SequenceMatcher(None, clean_chars, cand_upper).ratio()
                score += 0.30 * ratio

            if score > best_score:
                best_score = score
                best_match = cand

        if best_score >= THRESHOLD and best_match:
            mapping[cname] = best_match
            matched += 1

    elapsed = time.time() - t0

    # ── 4. Save ──
    with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
        json.dump(mapping, f, ensure_ascii=False, indent=2)

    file_size = os.path.getsize(OUTPUT_FILE)

    print(f"\n{'='*60}")
    print(f"✅ VENDOR MAPPING SELESAI")
    print(f"{'='*60}")
    print(f"📊 Tersensor: {len(censored):,}")
    print(f"✅ Matched:   {matched:,} ({matched/len(censored)*100:.1f}%)")
    print(f"❌ Skipped:   {skipped:,}")
    print(f"❓ No match:  {len(censored) - matched - skipped:,}")
    print(f"⏱️  Waktu:     {elapsed:.1f} detik")
    print(f"📂 Output:    {OUTPUT_FILE} ({file_size/1024:.1f} KB)")
    print(f"{'='*60}")

    # Show sample matches
    print(f"\n📋 Sample matches (10 pertama):")
    for i, (k, v) in enumerate(list(mapping.items())[:10]):
        print(f"   {k:40s} → {v}")

    print(f"\n🎉 Commit '{OUTPUT_FILE}' ke GitHub bersama app.py!")


if __name__ == "__main__":
    generate_mapping()
