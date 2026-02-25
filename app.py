"""
═══════════════════════════════════════════════════════════════════════════
  DASHBOARD TOP 20 SI CHANNEL POTENSIAL
  Telkomsel Enterprise | Bid Management — Data Science
  Data Realisasi INAPROC 2025
  ───────────────────────────────────────────────────────────────────────
  streamlit run dashboard_top20_si.py
═══════════════════════════════════════════════════════════════════════════
"""

import streamlit as st
import pandas as pd
import numpy as np
import seaborn as sns
import matplotlib.pyplot as plt
import matplotlib.ticker as mticker
import textwrap, os, io
from datetime import datetime
from openpyxl.styles import Font, PatternFill, Alignment, Border, Side
from openpyxl.utils import get_column_letter

# ═══════════════════════════════════════════════════════════════════════════
st.set_page_config(page_title="Top 20 SI Channel — Telkomsel Enterprise",
                   page_icon="📊", layout="wide", initial_sidebar_state="expanded")

# ═══════════════════════════════════════════════════════════════════════════
# CSS
# ═══════════════════════════════════════════════════════════════════════════
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght@400;600;700;800&display=swap');
    .stApp { background-color:#FAFAFA; font-family:'Plus Jakarta Sans',sans-serif; }
    .stApp,.stApp p,.stApp span,.stApp div,.stApp label,.stApp li,
    .stApp h1,.stApp h2,.stApp h3,.stApp h4,.stApp h5 { color:#111!important; }
    section[data-testid="stSidebar"] { background:linear-gradient(180deg,#1A1A2E 0%,#16213E 100%); }
    section[data-testid="stSidebar"] * { color:#E0E0E0!important; }
    section[data-testid="stSidebar"] .stRadio label span { color:#FFF!important; }
    .block-container { padding-top:1rem; max-width:1400px; }

    .hero { background:linear-gradient(135deg,#ED1C24 0%,#9B1B1F 60%,#1A1A2E 100%);
            padding:32px 40px; border-radius:20px; margin-bottom:28px;
            box-shadow:0 8px 32px rgba(237,28,36,0.25); position:relative; overflow:hidden; }
    .hero::after { content:''; position:absolute; top:-50%; right:-10%; width:300px; height:300px;
                   background:rgba(255,255,255,0.04); border-radius:50%; }
    .hero h1 { color:#FFF!important; font-size:32px!important; font-weight:800!important;
               margin:0!important; letter-spacing:-0.5px; }
    .hero p  { color:rgba(255,255,255,0.7)!important; font-size:14px!important; margin:6px 0 0!important; }

    .kpi { background:#FFF; border:1px solid #E8E8E8; border-radius:16px; padding:20px 16px;
           text-align:center; box-shadow:0 2px 12px rgba(0,0,0,0.04); transition:transform 0.2s;
           margin-bottom:10px; }
    .kpi:hover { transform:translateY(-2px); box-shadow:0 4px 20px rgba(0,0,0,0.08); }
    .kpi .num { color:#111!important; font-size:24px; font-weight:800; line-height:1.1; }
    .kpi .lab { color:#888!important; font-size:10px; font-weight:700; text-transform:uppercase;
                letter-spacing:1.2px; margin-bottom:8px; }
    .kpi .sub { color:#AAA!important; font-size:10px; margin-top:6px; }

    .sec { background:#FFF; border-left:5px solid #ED1C24; padding:14px 24px;
           margin:32px 0 18px; border-radius:0 12px 12px 0;
           box-shadow:0 1px 8px rgba(0,0,0,0.04); }
    .sec h2 { color:#111!important; font-size:20px!important; font-weight:800!important; margin:0!important; }
    .sec p  { color:#666!important; font-size:13px!important; margin:4px 0 0!important; }
    .sec-b  { background:#F5F8FF; border-left:5px solid #1565C0; padding:14px 24px;
              margin:32px 0 18px; border-radius:0 12px 12px 0;
              box-shadow:0 1px 8px rgba(0,0,0,0.04); }
    .sec-b h2 { color:#111!important; font-size:20px!important; font-weight:800!important; margin:0!important; }
    .sec-b p  { color:#666!important; font-size:13px!important; margin:4px 0 0!important; }

    .rcard { border-radius:16px; padding:22px 26px; margin:10px 0; border:2px solid;
             box-shadow:0 2px 12px rgba(0,0,0,0.04); }
    .rcard h3 { font-size:20px; font-weight:800; margin:0 0 4px; }
    .rcard p  { font-size:12px; margin:2px 0; }

    .si-card { background:#FFF; border:1px solid #E8E8E8; border-radius:14px; padding:18px 20px;
               margin:8px 0; box-shadow:0 1px 8px rgba(0,0,0,0.03); }
    .si-card h4 { font-size:15px; font-weight:800; margin:0 0 8px; color:#111!important; }
    .si-tag { display:inline-block; background:#F0F0F0; border-radius:6px; padding:3px 10px;
              font-size:11px; font-weight:600; margin:2px 3px 2px 0; color:#444!important; }
    .si-tag-red { background:#FFEBEE; color:#C62828!important; }
    .si-tag-blue { background:#E3F2FD; color:#1565C0!important; }

    .streamlit-expanderHeader { font-size:14px!important; font-weight:700!important; }
    .stTabs [data-baseweb="tab"] { font-weight:700; font-size:13px; padding:10px 20px; }
    .stDownloadButton>button { background:linear-gradient(135deg,#1A1A2E,#16213E)!important;
        color:#FFF!important; font-weight:700!important; border-radius:10px!important;
        border:none!important; padding:8px 20px!important; }
    .stDownloadButton>button:hover { background:linear-gradient(135deg,#ED1C24,#C41920)!important; }
    #MainMenu{visibility:hidden;} footer{visibility:hidden;}
</style>
""", unsafe_allow_html=True)

# ═══════════════════════════════════════════════════════════════════════════
# KONSTANTA
# ═══════════════════════════════════════════════════════════════════════════
WILAYAH = ["Sumatera","Jawa","Kalimantan","Sulawesi","Bali Nusra","Papua Maluku"]
BIDANG  = ["Kesehatan","Ekoinfra","Pendidikan","Pertahanan","Energi"]
BIDANG_L = {"Kesehatan":"Kesehatan & Perlindungan Sosial",
            "Ekoinfra":"Pembangunan Ekonomi & Infrastruktur",
            "Pendidikan":"Pendidikan","Pertahanan":"Pertahanan",
            "Energi":"Subsidi Energi & Non-Energi"}

W_CFG = {"Sumatera":    {"c":"#ED1C24","bg":"#FFF3F3","i":"🔴"},
         "Jawa":        {"c":"#1565C0","bg":"#E8F0FE","i":"🔵"},
         "Kalimantan":  {"c":"#E6A817","bg":"#FFF8E1","i":"🟡"},
         "Sulawesi":    {"c":"#2E7D32","bg":"#E8F5E9","i":"🟢"},
         "Bali Nusra":  {"c":"#E65100","bg":"#FFF3ED","i":"🟠"},
         "Papua Maluku":{"c":"#6C5CE7","bg":"#F3F0FF","i":"🟣"}}

B_CFG = {"Kesehatan": {"c":"#AD1457","bg":"#FCE4EC","i":"🏥"},
         "Ekoinfra":  {"c":"#E65100","bg":"#FFF3E0","i":"🏗️"},
         "Pendidikan":{"c":"#1565C0","bg":"#E3F2FD","i":"🎓"},
         "Pertahanan":{"c":"#37474F","bg":"#ECEFF1","i":"🛡️"},
         "Energi":    {"c":"#F9A825","bg":"#FFFDE7","i":"⚡"}}

# ═══════════════════════════════════════════════════════════════════════════
# FORMAT HELPERS
# ═══════════════════════════════════════════════════════════════════════════
def fmt_rp(v):
    if pd.isna(v) or v==0: return "Rp 0"
    a=abs(v)
    if a>=1e12: return f"Rp {v/1e12:,.2f} T"
    if a>=1e9:  return f"Rp {v/1e9:,.2f} M"
    if a>=1e6:  return f"Rp {v/1e6:,.1f} Jt"
    return f"Rp {v:,.0f}"

def fmt_s(v):
    if pd.isna(v) or v==0: return "0"
    a=abs(v)
    if a>=1e12: return f"{v/1e12:.1f}T"
    if a>=1e9:  return f"{v/1e9:.1f}M"
    if a>=1e6:  return f"{v/1e6:.0f}Jt"
    return f"{v:,.0f}"

def fmt_n(v):
    if pd.isna(v): return "0"
    return f"{int(v):,}".replace(",",".")

def kpi(lb,vl,sb=""):
    s=f'<div class="sub">{sb}</div>' if sb else ""
    return f'<div class="kpi"><div class="lab">{lb}</div><div class="num">{vl}</div>{s}</div>'

# ═══════════════════════════════════════════════════════════════════════════
# EXCEL EXPORT HELPER
# ═══════════════════════════════════════════════════════════════════════════
import re

def _safe_sheet_name(name):
    """Sanitize string agar bisa dipakai sebagai Excel sheet title."""
    # Hapus karakter ilegal:  * ? / \ [ ] :
    name = re.sub(r'[\*\?/\\\[\]:]', '', name)
    # Sheet name max 31 karakter
    return name[:31].strip() or "Data"

def to_excel_styled(df, sheet_name="Data"):
    """Export DataFrame ke Excel dengan styling profesional."""
    sheet_name = _safe_sheet_name(sheet_name)
    buf = io.BytesIO()
    with pd.ExcelWriter(buf, engine="openpyxl") as writer:
        df.to_excel(writer, index=False, sheet_name=sheet_name)
        ws = writer.sheets[sheet_name]

        hdr_font = Font(name="Calibri", bold=True, color="FFFFFF", size=11)
        hdr_fill = PatternFill(start_color="C41920", end_color="C41920", fill_type="solid")
        hdr_align = Alignment(horizontal="center", vertical="center", wrap_text=True)
        thin = Side(style="thin", color="DDDDDD")
        border = Border(top=thin, left=thin, right=thin, bottom=thin)
        body_font = Font(name="Calibri", size=10)
        alt_fill = PatternFill(start_color="FFF5F5", end_color="FFF5F5", fill_type="solid")

        for col_idx in range(1, len(df.columns)+1):
            cell = ws.cell(row=1, column=col_idx)
            cell.font = hdr_font
            cell.fill = hdr_fill
            cell.alignment = hdr_align
            cell.border = border
            ws.column_dimensions[get_column_letter(col_idx)].width = max(
                15, min(45, len(str(cell.value or ""))+4))

        for row_idx in range(2, len(df)+2):
            for col_idx in range(1, len(df.columns)+1):
                cell = ws.cell(row=row_idx, column=col_idx)
                cell.font = body_font
                cell.border = border
                cell.alignment = Alignment(vertical="center", wrap_text=True)
                if row_idx % 2 == 0:
                    cell.fill = alt_fill

        ws.auto_filter.ref = ws.dimensions
        ws.freeze_panes = "A2"

    return buf.getvalue()


# ═══════════════════════════════════════════════════════════════════════════
# BUILD SI SUMMARY (merge prioritas + detail for instansi/satker info)
# ═══════════════════════════════════════════════════════════════════════════
def build_si_summary(df_pri_seg, df_det_seg):
    """Build enriched SI summary with instansi & satker info from detail."""
    # Aggregate from prioritas
    agg_pri = (df_pri_seg.groupby("Nama_Pemenang")
               .agg(Total_Dealing=("Total_Dealing_Rp","sum"),
                    Jumlah_Kontrak=("Jumlah_Kontrak","sum"),
                    Max_Klien=("Jumlah_Klien","max"),
                    Sektor_List=("Sektor", lambda x: ", ".join(sorted(x.unique()))))
               .reset_index())

    # Aggregate from detail
    if len(df_det_seg) > 0:
        agg_det = (df_det_seg.groupby("Nama_Pemenang")
                   .agg(Jml_Paket_Detail=("Pagu_Rp","count"),
                        Total_Pagu=("Pagu_Rp","sum"),
                        Jml_Instansi=("Instansi_Pembeli","nunique"),
                        Jml_Satker=("Satuan_Kerja","nunique"),
                        Top_Instansi=("Instansi_Pembeli",
                                      lambda x: "; ".join(x.value_counts().head(5).index.tolist())),
                        Top_Satker=("Satuan_Kerja",
                                    lambda x: "; ".join(x.value_counts().head(5).index.tolist())),
                        Lokasi_List=("Lokasi",
                                     lambda x: "; ".join(x.dropna().unique()[:5])))
                   .reset_index())
        merged = agg_pri.merge(agg_det, on="Nama_Pemenang", how="left")
    else:
        merged = agg_pri.copy()
        for c in ["Jml_Paket_Detail","Total_Pagu","Jml_Instansi","Jml_Satker",
                   "Top_Instansi","Top_Satker","Lokasi_List"]:
            merged[c] = 0 if "Jml" in c or "Total" in c else ""

    merged = merged.sort_values("Total_Dealing", ascending=False)
    # Fill NaN
    for c in ["Jml_Instansi","Jml_Satker","Jml_Paket_Detail","Total_Pagu"]:
        if c in merged.columns:
            merged[c] = merged[c].fillna(0).astype(int)
    for c in ["Top_Instansi","Top_Satker","Lokasi_List"]:
        if c in merged.columns:
            merged[c] = merged[c].fillna("")

    return merged


# ═══════════════════════════════════════════════════════════════════════════
# CHART: TOP 20 HORIZONTAL BAR (with instansi/satker annotations)
# ═══════════════════════════════════════════════════════════════════════════
def chart_top20(df_summary, title, subtitle, accent_color, semesta=None, figsize=(16,9)):
    """Top 20 bar chart with rich annotations: value, %, kontrak, instansi, satker."""
    sns.set_theme(style="white")
    d = df_summary.head(20).copy().reset_index(drop=True)
    n = len(d)
    if n == 0:
        fig, ax = plt.subplots(figsize=(8,3))
        ax.text(0.5,0.5,"Tidak ada data",ha="center",va="center",fontsize=16,color="#999")
        ax.axis("off"); return fig

    fig, ax = plt.subplots(figsize=figsize)
    fig.patch.set_facecolor("#FAFAFA")
    ax.set_facecolor("#FAFAFA")

    # Gradient palette
    base = accent_color.lstrip('#')
    r0,g0,b0 = int(base[:2],16), int(base[2:4],16), int(base[4:6],16)
    palette = []
    for i in range(n):
        f = 1.0 - (i * 0.03)
        palette.append(f"#{max(0,min(255,int(r0*f))):02x}{max(0,min(255,int(g0*f))):02x}{max(0,min(255,int(b0*f))):02x}")

    y_pos = list(range(n-1, -1, -1))
    bars = ax.barh(y_pos, d["Total_Dealing"], color=palette, height=0.62,
                   edgecolor="white", linewidth=1.2, zorder=3)

    mx = d["Total_Dealing"].max()

    for i, (_, row) in enumerate(d.iterrows()):
        y = n - 1 - i
        val = row["Total_Dealing"]
        # Line 1: Value + %
        pct = f"  ({val/semesta*100:.1f}%)" if semesta and semesta > 0 else ""
        line1 = f"{fmt_rp(val)}{pct}"
        # Line 2: Kontrak | Instansi | Satker
        parts = []
        if "Jumlah_Kontrak" in row.index and row["Jumlah_Kontrak"] > 0:
            parts.append(f"{int(row['Jumlah_Kontrak'])} kontrak")
        if "Jml_Instansi" in row.index and row["Jml_Instansi"] > 0:
            parts.append(f"{int(row['Jml_Instansi'])} instansi")
        if "Jml_Satker" in row.index and row["Jml_Satker"] > 0:
            parts.append(f"{int(row['Jml_Satker'])} satker")
        line2 = "  •  ".join(parts) if parts else ""

        ax.text(val + mx*0.008, y + 0.12, line1,
                va="center", ha="left", fontsize=10, fontweight="bold", color="#111")
        if line2:
            ax.text(val + mx*0.008, y - 0.18, line2,
                    va="center", ha="left", fontsize=8.5, fontweight="600", color="#666")

    ax.set_yticks(y_pos)
    ax.set_yticklabels(
        ["\n".join(textwrap.wrap(str(nm), 30)) for nm in d["Nama_Pemenang"]],
        fontsize=10.5, fontweight="bold", color="#222")

    ax.set_title(title, fontsize=18, fontweight="bold", color="#111", loc="left", pad=24)
    if subtitle:
        ax.text(0, 1.035, subtitle, transform=ax.transAxes,
                fontsize=12, color="#777", ha="left")

    if semesta:
        ax.text(1.0, -0.06, f"SEMESTA: {fmt_rp(semesta)}",
                transform=ax.transAxes, fontsize=11, fontweight="bold",
                color="#ED1C24", ha="right", va="top",
                bbox=dict(boxstyle="round,pad=0.3", facecolor="#FFF3F3",
                          edgecolor="#ED1C24", alpha=0.9))

    ax.set_xlabel("")
    ax.set_ylabel("")
    ax.tick_params(axis="x", labelsize=9, labelcolor="#AAA")
    ax.xaxis.set_major_formatter(mticker.FuncFormatter(lambda x,_: fmt_s(x)))
    ax.set_xlim(0, mx * 1.58)
    ax.grid(axis="x", alpha=0.08, linestyle="-", zorder=0)
    for sp in ["top","right","left"]: ax.spines[sp].set_visible(False)
    ax.spines["bottom"].set_color("#E0E0E0")
    plt.tight_layout()
    return fig


# ═══════════════════════════════════════════════════════════════════════════
# CHART: DONUT PIE (ICT vs Non-ICT)
# ═══════════════════════════════════════════════════════════════════════════
def chart_pie(df_seg, seg_name):
    total_val = df_seg["Total_Dealing_Rp"].sum()
    ict = df_seg[df_seg["Sektor"]=="ICT"]
    non = df_seg[df_seg["Sektor"]=="Non-ICT"]
    val_ict, val_non = ict["Total_Dealing_Rp"].sum(), non["Total_Dealing_Rp"].sum()
    cnt_ict, cnt_non = len(ict), len(non)
    pct_ict = val_ict/total_val*100 if total_val>0 else 0

    fig, ax = plt.subplots(figsize=(5,5))
    fig.patch.set_facecolor("#FAFAFA")
    ax.set_facecolor("#FAFAFA")
    if total_val == 0:
        ax.text(0.5,0.5,"Tidak ada data",ha="center",va="center",fontsize=13,color="#999",
                transform=ax.transAxes)
        ax.axis("off"); return fig

    sizes,colors,labels = [],[],[]
    if val_ict>0:
        sizes.append(val_ict); colors.append("#1B4F72")
        labels.append(f"ICT — {fmt_rp(val_ict)} ({pct_ict:.1f}%) • {cnt_ict} SI")
    if val_non>0:
        sizes.append(val_non); colors.append("#1E6F3E")
        labels.append(f"Non-ICT — {fmt_rp(val_non)} ({100-pct_ict:.1f}%) • {cnt_non} SI")

    wedges,_,autotexts = ax.pie(
        sizes, colors=colors, autopct=lambda p: f"{p:.1f}%", startangle=90, pctdistance=0.78,
        wedgeprops=dict(width=0.38, edgecolor="white", linewidth=3),
        textprops=dict(color="white", fontsize=12, fontweight="bold"))
    for at in autotexts: at.set_fontsize(13); at.set_fontweight("bold")

    ax.text(0,0.06,fmt_rp(total_val),ha="center",va="center",fontsize=14,fontweight="bold",color="#111")
    ax.text(0,-0.10,seg_name,ha="center",va="center",fontsize=9.5,fontweight="bold",color="#444")
    ax.text(0,-0.22,f"{cnt_ict+cnt_non} SI Channel",ha="center",va="center",fontsize=8.5,color="#888")

    lg = ax.legend(wedges, labels, loc="lower center", bbox_to_anchor=(0.5,-0.10),
                   fontsize=8.5, frameon=False, ncol=1)
    for t in lg.get_texts(): t.set_color("#333")
    ax.set_aspect("equal"); ax.axis("off")
    plt.subplots_adjust(bottom=0.12, top=0.95)
    return fig


# ═══════════════════════════════════════════════════════════════════════════
# RENDER SI DETAIL CARDS (Instansi + Satker breakdown)
# ═══════════════════════════════════════════════════════════════════════════
def render_si_cards(df_summary, df_det_seg, seg_name, key_prefix):
    """Render expandable detail cards per SI showing instansi & satker."""

    top20 = df_summary.head(20)

    for idx, (_, row) in enumerate(top20.iterrows()):
        si = row["Nama_Pemenang"]
        dsi = df_det_seg[df_det_seg["Nama_Pemenang"] == si] if len(df_det_seg)>0 else pd.DataFrame()

        n_inst = int(row.get("Jml_Instansi", 0))
        n_satk = int(row.get("Jml_Satker", 0))
        n_pkt  = int(row.get("Jml_Paket_Detail", 0))
        val    = row["Total_Dealing"]

        # Header line
        header = (f"**#{idx+1} {si}** — {fmt_rp(val)} | "
                  f"{n_inst} instansi • {n_satk} satker • {n_pkt} paket")

        with st.expander(header, expanded=False):
            if len(dsi) == 0:
                st.caption("Detail paket tidak tersedia untuk SI ini.")
                continue

            # ── Mini KPI row ──
            k1,k2,k3,k4 = st.columns(4)
            k1.markdown(kpi("Total Pagu", fmt_rp(dsi["Pagu_Rp"].sum())), unsafe_allow_html=True)
            k2.markdown(kpi("Jumlah Paket", fmt_n(len(dsi))), unsafe_allow_html=True)
            k3.markdown(kpi("Instansi Unik", fmt_n(dsi["Instansi_Pembeli"].nunique())),
                        unsafe_allow_html=True)
            k4.markdown(kpi("Satuan Kerja Unik", fmt_n(dsi["Satuan_Kerja"].nunique())),
                        unsafe_allow_html=True)

            st.markdown("<div style='height:8px'></div>", unsafe_allow_html=True)

            # ── Instansi breakdown ──
            col_a, col_b = st.columns(2)
            with col_a:
                st.markdown("**🏛️ Instansi Pembeli yang Dilayani:**")
                inst_agg = (dsi.groupby("Instansi_Pembeli")
                            .agg(Pagu=("Pagu_Rp","sum"), Paket=("Pagu_Rp","count"))
                            .sort_values("Pagu", ascending=False).reset_index())
                inst_agg["Pagu"] = inst_agg["Pagu"].apply(fmt_rp)
                inst_agg.columns = ["Instansi Pembeli", "Total Pagu", "Jml Paket"]
                st.dataframe(inst_agg, use_container_width=True, hide_index=True, height=220)

            with col_b:
                st.markdown("**🏢 Satuan Kerja yang Dilayani (Top 15):**")
                satk_agg = (dsi.groupby("Satuan_Kerja")
                            .agg(Pagu=("Pagu_Rp","sum"), Paket=("Pagu_Rp","count"))
                            .sort_values("Pagu", ascending=False).head(15).reset_index())
                satk_agg["Pagu"] = satk_agg["Pagu"].apply(fmt_rp)
                satk_agg.columns = ["Satuan Kerja", "Total Pagu", "Jml Paket"]
                st.dataframe(satk_agg, use_container_width=True, hide_index=True, height=220)

            # ── Semua paket ──
            st.markdown("**📋 Daftar Paket:**")
            cols_show = ["Nama_Paket","Pagu_Rp","Instansi_Pembeli","Satuan_Kerja",
                         "Lokasi","Metode_Pemilihan","Sektor","Kategori_ICT"]
            cols_avail = [c for c in cols_show if c in dsi.columns]
            df_paket = dsi[cols_avail].copy()
            if "Pagu_Rp" in df_paket.columns:
                df_paket = df_paket.sort_values("Pagu_Rp", ascending=False)
                df_paket["Pagu_Rp"] = df_paket["Pagu_Rp"].apply(fmt_rp)
            st.dataframe(df_paket, use_container_width=True, hide_index=True, height=250)

            # ── Download per SI ──
            excel_si = to_excel_styled(dsi[cols_avail] if cols_avail else dsi, f"Paket_{si[:20]}")
            _fn_si = re.sub(r'[^\w\s-]', '', si[:25]).replace(' ', '_')
            st.download_button(
                f"📥 Download Excel — {si[:30]}",
                excel_si,
                f"Paket_{_fn_si}_{datetime.now():%Y%m%d}.xlsx",
                "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                key=f"dlsi_{key_prefix}_{idx}",
            )


# ═══════════════════════════════════════════════════════════════════════════
# RENDER FULL SEGMENT (chart + cards + download)
# ═══════════════════════════════════════════════════════════════════════════
def render_segment(df_pri_seg, df_det_seg, seg_name, color, key_pf, semesta_pri=None):
    """Full render: KPIs + Top 20 chart + ICT/Non-ICT tabs + SI detail cards + download."""

    summary = build_si_summary(df_pri_seg, df_det_seg)
    n_si = len(summary)
    total_val = summary["Total_Dealing"].sum()
    total_kontrak = summary["Jumlah_Kontrak"].sum()
    total_inst = summary["Jml_Instansi"].sum()
    total_satker = summary["Jml_Satker"].sum()
    total_det = len(df_det_seg)
    total_pagu = df_det_seg["Pagu_Rp"].sum() if total_det > 0 else 0

    # ── KPIs ──
    c1,c2,c3,c4,c5,c6 = st.columns(6)
    c1.markdown(kpi("SI Channel", fmt_n(n_si)), unsafe_allow_html=True)
    c2.markdown(kpi("Total Dealing", fmt_rp(total_val)), unsafe_allow_html=True)
    c3.markdown(kpi("Total Kontrak", fmt_n(total_kontrak)), unsafe_allow_html=True)
    c4.markdown(kpi("Instansi Dilayani",
                    fmt_n(df_det_seg["Instansi_Pembeli"].nunique() if total_det>0 else 0)),
                unsafe_allow_html=True)
    c5.markdown(kpi("Satuan Kerja",
                    fmt_n(df_det_seg["Satuan_Kerja"].nunique() if total_det>0 else 0)),
                unsafe_allow_html=True)
    c6.markdown(kpi("Detail Paket", fmt_n(total_det), fmt_rp(total_pagu)),
                unsafe_allow_html=True)

    st.markdown("<div style='height:16px'></div>", unsafe_allow_html=True)

    # ── TOP 20 CHART (ALL) ──
    fig = chart_top20(summary, f"Top {min(20,n_si)} SI Channel — {seg_name}",
                      f"Nilai dealing + jumlah instansi & satuan kerja yang dilayani",
                      color, semesta_pri or total_val)
    st.pyplot(fig, use_container_width=True)
    plt.close(fig)

    # ── Download Excel Top 20 summary ──
    dl_summary = summary.head(20).copy()
    dl_cols = ["Nama_Pemenang","Total_Dealing","Jumlah_Kontrak","Max_Klien",
               "Jml_Instansi","Jml_Satker","Jml_Paket_Detail","Total_Pagu",
               "Top_Instansi","Top_Satker","Sektor_List"]
    dl_cols = [c for c in dl_cols if c in dl_summary.columns]
    st.download_button(
        f"📥 Download Excel — Top 20 SI {seg_name}",
        to_excel_styled(dl_summary[dl_cols], f"Top20_{seg_name[:20]}"),
        f"Top20_SI_{seg_name.replace(' ','_')}_{datetime.now():%Y%m%d}.xlsx",
        "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        key=f"dl_top20_{key_pf}",
    )

    st.markdown("<div style='height:12px'></div>", unsafe_allow_html=True)

    # ── TABS: ICT / Non-ICT / Detail Cards ──
    t_all, t_ict, t_non, t_inst = st.tabs(
        ["📊 Detail per SI", "💻 Top 20 ICT", "📦 Top 20 Non-ICT", "🏛️ Top Instansi & Satker"])

    with t_all:
        render_si_cards(summary, df_det_seg, seg_name, key_pf)

    with t_ict:
        df_ict = df_pri_seg[df_pri_seg["Sektor"]=="ICT"]
        if len(df_ict) > 0:
            df_det_ict = df_det_seg[df_det_seg["Sektor"]=="ICT"]
            sum_ict = build_si_summary(df_ict, df_det_ict)
            sem_ict = sum_ict["Total_Dealing"].sum()
            fig = chart_top20(sum_ict, f"Top {min(20,len(sum_ict))} SI ICT — {seg_name}",
                              f"{len(df_ict)} SI ICT | Total: {fmt_rp(sem_ict)}",
                              "#1565C0", sem_ict)
            st.pyplot(fig, use_container_width=True)
            plt.close(fig)
            st.download_button(
                f"📥 Download Excel — Top 20 ICT {seg_name}",
                to_excel_styled(sum_ict.head(20), f"ICT_{seg_name[:15]}"),
                f"Top20_ICT_{seg_name.replace(' ','_')}_{datetime.now():%Y%m%d}.xlsx",
                "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                key=f"dl_ict_{key_pf}",
            )
            render_si_cards(sum_ict, df_det_ict, f"{seg_name} ICT", f"ict_{key_pf}")
        else:
            st.info("Tidak ada SI ICT di segmen ini.")

    with t_non:
        df_non = df_pri_seg[df_pri_seg["Sektor"]=="Non-ICT"]
        if len(df_non) > 0:
            df_det_non = df_det_seg[df_det_seg["Sektor"]=="Non-ICT"]
            sum_non = build_si_summary(df_non, df_det_non)
            sem_non = sum_non["Total_Dealing"].sum()
            fig = chart_top20(sum_non, f"Top {min(20,len(sum_non))} SI Non-ICT — {seg_name}",
                              f"{len(df_non)} SI Non-ICT | Total: {fmt_rp(sem_non)}",
                              "#2E7D32", sem_non)
            st.pyplot(fig, use_container_width=True)
            plt.close(fig)
            st.download_button(
                f"📥 Download Excel — Top 20 Non-ICT {seg_name}",
                to_excel_styled(sum_non.head(20), f"NonICT_{seg_name[:15]}"),
                f"Top20_NonICT_{seg_name.replace(' ','_')}_{datetime.now():%Y%m%d}.xlsx",
                "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                key=f"dl_non_{key_pf}",
            )
            render_si_cards(sum_non, df_det_non, f"{seg_name} Non-ICT", f"non_{key_pf}")
        else:
            st.info("Tidak ada SI Non-ICT di segmen ini.")

    with t_inst:
        if len(df_det_seg) > 0:
            # Top 15 instansi
            st.markdown(f"**🏛️ Top 15 Instansi Pembeli — {seg_name}**")
            inst_top = (df_det_seg.groupby("Instansi_Pembeli")
                        .agg(Total=("Pagu_Rp","sum"), Paket=("Pagu_Rp","count"),
                             SI_Unik=("Nama_Pemenang","nunique"),
                             Satker_Unik=("Satuan_Kerja","nunique"))
                        .sort_values("Total", ascending=False).head(15).reset_index())
            fig = chart_top20(
                inst_top.rename(columns={"Instansi_Pembeli":"Nama_Pemenang","Total":"Total_Dealing",
                                         "Paket":"Jumlah_Kontrak","SI_Unik":"Jml_Instansi",
                                         "Satker_Unik":"Jml_Satker"}),
                f"Top 15 Instansi Pembeli — {seg_name}",
                f"{df_det_seg['Instansi_Pembeli'].nunique()} instansi total | "
                f"Angka: SI unik & satker unik per instansi",
                "#E65100", total_pagu, figsize=(15,7))
            st.pyplot(fig, use_container_width=True)
            plt.close(fig)

            st.download_button(
                f"📥 Download Excel — Top Instansi {seg_name}",
                to_excel_styled(inst_top, f"Instansi_{seg_name[:15]}"),
                f"Instansi_{seg_name.replace(' ','_')}_{datetime.now():%Y%m%d}.xlsx",
                "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                key=f"dl_inst_{key_pf}",
            )

            st.markdown(f"<div style='height:16px'></div>", unsafe_allow_html=True)

            # Top 15 satker
            st.markdown(f"**🏢 Top 15 Satuan Kerja — {seg_name}**")
            satk_top = (df_det_seg.groupby("Satuan_Kerja")
                        .agg(Total=("Pagu_Rp","sum"), Paket=("Pagu_Rp","count"),
                             SI_Unik=("Nama_Pemenang","nunique"),
                             Inst_Unik=("Instansi_Pembeli","nunique"))
                        .sort_values("Total", ascending=False).head(15).reset_index())
            fig = chart_top20(
                satk_top.rename(columns={"Satuan_Kerja":"Nama_Pemenang","Total":"Total_Dealing",
                                         "Paket":"Jumlah_Kontrak","SI_Unik":"Jml_Instansi",
                                         "Inst_Unik":"Jml_Satker"}),
                f"Top 15 Satuan Kerja — {seg_name}",
                f"{df_det_seg['Satuan_Kerja'].nunique()} satker total | "
                f"Angka: SI unik & instansi unik per satker",
                "#1565C0", total_pagu, figsize=(15,7))
            st.pyplot(fig, use_container_width=True)
            plt.close(fig)

            st.download_button(
                f"📥 Download Excel — Top Satker {seg_name}",
                to_excel_styled(satk_top, f"Satker_{seg_name[:15]}"),
                f"Satker_{seg_name.replace(' ','_')}_{datetime.now():%Y%m%d}.xlsx",
                "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                key=f"dl_satk_{key_pf}",
            )
        else:
            st.info("Tidak ada detail instansi/satker untuk segmen ini.")


# ═══════════════════════════════════════════════════════════════════════════
# HEATMAP
# ═══════════════════════════════════════════════════════════════════════════
def chart_heatmap(df, si_col, seg_col, val_col, title, cmap="Reds"):
    top = df.groupby(si_col)[val_col].sum().sort_values(ascending=False).head(15).index
    h = df[df[si_col].isin(top)].groupby([si_col,seg_col])[val_col].sum().unstack(fill_value=0)
    h["_t"] = h.sum(axis=1)
    h = h.sort_values("_t", ascending=False).drop("_t", axis=1)
    if h.empty: return None

    fig, ax = plt.subplots(figsize=(15, max(7, len(h)*0.48)))
    fig.patch.set_facecolor("#FAFAFA")
    ax.set_facecolor("#FAFAFA")
    annot = h.map(lambda x: fmt_s(x) if x>0 else "")
    sns.heatmap(h, ax=ax, annot=annot, fmt="", cmap=cmap, linewidths=2, linecolor="white",
                cbar_kws={"label":"Nilai (Rp)","shrink":0.5},
                annot_kws={"fontsize":9,"fontweight":"bold"})
    ax.set_title(title, fontsize=16, fontweight="bold", color="#111", pad=16)
    ax.set_xlabel(""); ax.set_ylabel("")
    ax.set_yticklabels(["\n".join(textwrap.wrap(t.get_text(),25))
                        for t in ax.get_yticklabels()], fontsize=10, fontweight="bold", rotation=0)
    ax.set_xticklabels(ax.get_xticklabels(), fontsize=11, fontweight="bold", rotation=25, ha="right")
    plt.tight_layout()
    return fig


# ═══════════════════════════════════════════════════════════════════════════
# LOAD DATA
# ═══════════════════════════════════════════════════════════════════════════
@st.cache_data
def load_all():
    sd = os.path.dirname(os.path.abspath(__file__))
    def find(nm, alts=None):
        for c in [nm]+(alts or []):
            for b in [sd,".",os.getcwd()]:
                p = os.path.join(b,c)
                if os.path.exists(p): return p
        return None
    f1 = find("TOP_20_SI_Prioritas__Data_Realisasi_2025_.xlsx")
    f2 = find("Top20_Detail_Paket.xlsx")
    f3 = find("prediksi_nama_vendor.csv")
    err = []
    if not f1: err.append("TOP_20_SI_Prioritas__Data_Realisasi_2025_.xlsx")
    if not f2: err.append("Top20_Detail_Paket.xlsx")
    if not f3: err.append("prediksi_nama_vendor.csv")
    if err: return None,None,0,err

    dp = pd.read_excel(f1)
    dd = pd.read_excel(f2)
    dc = pd.read_csv(f3)

    # Uncensor
    um = {}
    for _,r in dc.iterrows():
        n = str(r.get("Nama_Pemenang","")).strip()
        a = str(r.get("Nama_Pemenang_Asli","")).strip()
        if "*" in n and "[TIDAK DITEMUKAN]" not in a and a: um[n]=a
    if um:
        dp["Nama_Pemenang"] = dp["Nama_Pemenang"].replace(um)
        dd["Nama_Pemenang"] = dd["Nama_Pemenang"].replace(um)
        if "Prediksi_Nama_Asli" in dd.columns:
            dd["Prediksi_Nama_Asli"] = dd["Prediksi_Nama_Asli"].replace(um)

    snorm = {"Bali — NusRa":"Bali Nusra","Papua — Maluku":"Papua Maluku"}
    dp["Segmen"]=dp["Segmen"].replace(snorm)
    dd["Segmen"]=dd["Segmen"].replace(snorm)
    if "Zona" in dd.columns: dd["Zona"]=dd["Zona"].replace(snorm)

    return dp, dd, len(um), []


# ═══════════════════════════════════════════════════════════════════════════
# MAIN
# ═══════════════════════════════════════════════════════════════════════════

# HERO
st.markdown("""
<div class="hero">
    <h1>📊 Dashboard Top 20 SI Channel Potensial</h1>
    <p>Data Realisasi INAPROC 2025 &nbsp;|&nbsp; Telkomsel Enterprise — Bid Management Intelligence</p>
</div>""", unsafe_allow_html=True)

dp, dd, n_unc, err = load_all()
if err:
    st.error(f"⚠️ File tidak ditemukan: **{', '.join(err)}**\n\n"
             f"Letakkan 3 file di folder yang sama dengan script ini.")
    st.stop()

# SIDEBAR
with st.sidebar:
    st.markdown("<div style='text-align:center;padding:8px 0'>"
                "<span style='font-size:24px'>📊</span><br>"
                "<span style='font-size:16px;font-weight:800;color:#FFF!important'>SI CHANNEL</span><br>"
                "<span style='font-size:10px;color:#AAA!important'>Telkomsel Enterprise</span>"
                "</div>", unsafe_allow_html=True)
    st.markdown("---")
    st.success(f"✅ {fmt_n(len(dp))} SI  •  {fmt_n(len(dd))} paket")
    st.info(f"🔓 {n_unc} nama di-uncensor")
    st.markdown("---")
    view = st.radio("📌 Tampilan",
                    ["🏠 Overview","🗺️ Per Wilayah","🏛️ Per Bidang K/L"], index=0)
    st.markdown("---")
    sektor = st.radio("🔍 Sektor", ["Semua","ICT","Non-ICT"], index=0)
    st.markdown("---")
    st.caption(f"Telkomsel Enterprise\n{datetime.now():%d %B %Y}")

# FILTER
dpf = dp.copy()
ddf = dd.copy()
if sektor != "Semua":
    dpf = dpf[dpf["Sektor"]==sektor]
    ddf = ddf[ddf["Sektor"]==sektor]


# ═══════════════════════════════════════════════════════════════════════════
# VIEW: OVERVIEW
# ═══════════════════════════════════════════════════════════════════════════
if "Overview" in view:

    # KPIs
    st.markdown('<div class="sec"><h2>📌 Ringkasan Eksekutif</h2>'
                '<p>Gabungan semua wilayah dan bidang</p></div>', unsafe_allow_html=True)

    total_si = dpf["Nama_Pemenang"].nunique()
    total_val = dpf["Total_Dealing_Rp"].sum()
    total_det = len(ddf)
    total_pagu = ddf["Pagu_Rp"].sum()
    total_inst = ddf["Instansi_Pembeli"].nunique() if total_det>0 else 0
    total_satk = ddf["Satuan_Kerja"].nunique() if total_det>0 else 0

    c1,c2,c3,c4,c5,c6 = st.columns(6)
    c1.markdown(kpi("SI Channel Unik", fmt_n(total_si)), unsafe_allow_html=True)
    c2.markdown(kpi("Total Dealing", fmt_rp(total_val)), unsafe_allow_html=True)
    c3.markdown(kpi("Total Kontrak", fmt_n(dpf["Jumlah_Kontrak"].sum())), unsafe_allow_html=True)
    c4.markdown(kpi("Instansi Pembeli", fmt_n(total_inst)), unsafe_allow_html=True)
    c5.markdown(kpi("Satuan Kerja", fmt_n(total_satk)), unsafe_allow_html=True)
    c6.markdown(kpi("Detail Paket", fmt_n(total_det), fmt_rp(total_pagu)), unsafe_allow_html=True)

    st.markdown("<div style='height:16px'></div>", unsafe_allow_html=True)

    # Pie per Wilayah
    st.markdown('<div class="sec"><h2>🗺️ ICT vs Non-ICT per Wilayah</h2>'
                '<p>Klik "Per Wilayah" di sidebar untuk detail Top 20</p></div>', unsafe_allow_html=True)
    cols = st.columns(3)
    for i,w in enumerate(WILAYAH):
        cf = W_CFG[w]
        dw = dpf[dpf["Segmen"]==w]
        with cols[i%3]:
            rv = dw["Total_Dealing_Rp"].sum()
            # Count instansi/satker from detail
            dw_det = ddf[ddf["Segmen"]==w]
            ni = dw_det["Instansi_Pembeli"].nunique() if len(dw_det)>0 else 0
            ns = dw_det["Satuan_Kerja"].nunique() if len(dw_det)>0 else 0
            st.markdown(f"""
            <div class="rcard" style="background:{cf['bg']};border-color:{cf['c']}">
                <h3 style="color:{cf['c']}!important">{cf['i']} {w}</h3>
                <p><strong>{fmt_rp(rv)}</strong> &nbsp;|&nbsp; {len(dw)} SI &nbsp;|&nbsp;
                   {ni} instansi &nbsp;|&nbsp; {ns} satker</p>
            </div>""", unsafe_allow_html=True)
            fig = chart_pie(dw, w)
            st.pyplot(fig, use_container_width=True); plt.close(fig)

    st.markdown("<div style='height:20px'></div>", unsafe_allow_html=True)

    # Pie per Bidang
    st.markdown('<div class="sec-b"><h2>🏛️ ICT vs Non-ICT per Bidang K/L</h2>'
                '<p>Klik "Per Bidang K/L" di sidebar untuk detail Top 20</p></div>', unsafe_allow_html=True)
    cols_b = st.columns(3)
    for i,b in enumerate(BIDANG):
        cf = B_CFG[b]
        db = dpf[dpf["Segmen"]==b]
        if len(db)==0: continue
        with cols_b[i%3]:
            bv = db["Total_Dealing_Rp"].sum()
            db_det = ddf[ddf["Segmen"]==b]
            ni = db_det["Instansi_Pembeli"].nunique() if len(db_det)>0 else 0
            ns = db_det["Satuan_Kerja"].nunique() if len(db_det)>0 else 0
            st.markdown(f"""
            <div class="rcard" style="background:{cf['bg']};border-color:{cf['c']}">
                <h3 style="color:{cf['c']}!important">{cf['i']} {BIDANG_L.get(b,b)}</h3>
                <p><strong>{fmt_rp(bv)}</strong> &nbsp;|&nbsp; {len(db)} SI &nbsp;|&nbsp;
                   {ni} instansi &nbsp;|&nbsp; {ns} satker</p>
            </div>""", unsafe_allow_html=True)
            fig = chart_pie(db, BIDANG_L.get(b,b))
            st.pyplot(fig, use_container_width=True); plt.close(fig)

    st.markdown("<div style='height:20px'></div>", unsafe_allow_html=True)

    # Grand Top 20
    st.markdown('<div class="sec"><h2>🏆 Grand Top 20 SI Channel</h2>'
                '<p>Semua segmen — dengan info instansi & satuan kerja yang dilayani</p></div>',
                unsafe_allow_html=True)
    grand = build_si_summary(dpf, ddf)
    fig = chart_top20(grand, "Grand Top 20 SI Channel — Semua Segmen",
                      f"{fmt_n(total_si)} SI unik  •  {fmt_n(total_inst)} instansi  •  {fmt_n(total_satk)} satker",
                      "#ED1C24", total_val)
    st.pyplot(fig, use_container_width=True); plt.close(fig)

    st.download_button("📥 Download Excel — Grand Top 20",
                       to_excel_styled(grand.head(20), "Grand_Top20"),
                       f"Grand_Top20_{datetime.now():%Y%m%d}.xlsx",
                       "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                       key="dl_grand")

    st.markdown("<div style='height:8px'></div>", unsafe_allow_html=True)

    # Grand SI Detail Cards — langsung tanpa outer expander (nested expander tidak diperbolehkan)
    st.markdown("**📋 Detail per SI — Instansi & Satuan Kerja**")
    render_si_cards(grand, ddf, "Semua Segmen", "gd")

    st.markdown("<div style='height:20px'></div>", unsafe_allow_html=True)

    # Heatmaps
    st.markdown('<div class="sec"><h2>🔥 Heatmap: Top SI × Wilayah</h2></div>', unsafe_allow_html=True)
    dpw = dpf[dpf["Segmen"].isin(WILAYAH)]
    if len(dpw)>0:
        fig = chart_heatmap(dpw,"Nama_Pemenang","Segmen","Total_Dealing_Rp",
                            "Top 15 SI × Wilayah — Nilai Dealing","Reds")
        if fig: st.pyplot(fig, use_container_width=True); plt.close(fig)

    st.markdown('<div class="sec-b"><h2>🔥 Heatmap: Top SI × Bidang K/L</h2></div>', unsafe_allow_html=True)
    dpb = dpf[dpf["Segmen"].isin(BIDANG)]
    if len(dpb)>0:
        fig = chart_heatmap(dpb,"Nama_Pemenang","Segmen","Total_Dealing_Rp",
                            "Top 15 SI × Bidang K/L — Nilai Dealing","Blues")
        if fig: st.pyplot(fig, use_container_width=True); plt.close(fig)


# ═══════════════════════════════════════════════════════════════════════════
# VIEW: PER WILAYAH
# ═══════════════════════════════════════════════════════════════════════════
elif "Wilayah" in view:
    st.markdown('<div class="sec"><h2>🗺️ Top 20 SI Channel per Wilayah</h2>'
                '<p>Masing-masing wilayah terpisah dengan detail instansi & satuan kerja</p></div>',
                unsafe_allow_html=True)

    wdata = [w for w in WILAYAH if len(dpf[dpf["Segmen"]==w])>0]
    if not wdata: st.warning("Tidak ada data."); st.stop()

    tabs = st.tabs([f"{W_CFG[w]['i']} {w}" for w in wdata])
    for tab,w in zip(tabs,wdata):
        with tab:
            cf = W_CFG[w]
            dw_det = ddf[ddf["Segmen"]==w]
            ni = dw_det["Instansi_Pembeli"].nunique() if len(dw_det)>0 else 0
            ns = dw_det["Satuan_Kerja"].nunique() if len(dw_det)>0 else 0
            st.markdown(f"""
            <div class="rcard" style="background:{cf['bg']};border-color:{cf['c']}">
                <h3 style="color:{cf['c']}!important">{cf['i']} Wilayah {w}</h3>
                <p>Top 20 SI Channel &nbsp;|&nbsp; {ni} instansi &nbsp;|&nbsp; {ns} satker</p>
            </div>""", unsafe_allow_html=True)
            dpw = dpf[dpf["Segmen"]==w]
            sem = dpf[dpf["Segmen"].isin(WILAYAH)]["Total_Dealing_Rp"].sum()
            render_segment(dpw, dw_det, f"Wilayah {w}", cf["c"], f"w_{w}", sem)


# ═══════════════════════════════════════════════════════════════════════════
# VIEW: PER BIDANG
# ═══════════════════════════════════════════════════════════════════════════
elif "Bidang" in view:
    st.markdown('<div class="sec-b"><h2>🏛️ Top 20 SI Channel per Bidang K/L</h2>'
                '<p>Masing-masing bidang terpisah dengan detail instansi & satuan kerja</p></div>',
                unsafe_allow_html=True)

    bdata = [b for b in BIDANG if len(dpf[dpf["Segmen"]==b])>0]
    if not bdata: st.warning("Tidak ada data."); st.stop()

    tabs = st.tabs([f"{B_CFG[b]['i']} {BIDANG_L.get(b,b)}" for b in bdata])
    for tab,b in zip(tabs,bdata):
        with tab:
            cf = B_CFG[b]
            lb = BIDANG_L.get(b,b)
            db_det = ddf[ddf["Segmen"]==b]
            ni = db_det["Instansi_Pembeli"].nunique() if len(db_det)>0 else 0
            ns = db_det["Satuan_Kerja"].nunique() if len(db_det)>0 else 0
            st.markdown(f"""
            <div class="rcard" style="background:{cf['bg']};border-color:{cf['c']}">
                <h3 style="color:{cf['c']}!important">{cf['i']} {lb}</h3>
                <p>Top 20 SI Channel &nbsp;|&nbsp; {ni} instansi &nbsp;|&nbsp; {ns} satker</p>
            </div>""", unsafe_allow_html=True)
            dpb = dpf[dpf["Segmen"]==b]
            sem = dpf[dpf["Segmen"].isin(BIDANG)]["Total_Dealing_Rp"].sum()
            render_segment(dpb, db_det, lb, cf["c"], f"b_{b}", sem)


# ═══════════════════════════════════════════════════════════════════════════
# SOLUSI ICT + KENAIKAN ANGGARAN (selalu tampil)
# ═══════════════════════════════════════════════════════════════════════════
st.markdown("---")
st.markdown('<div class="sec"><h2>🚀 Solusi ICT Telkomsel Enterprise per Wilayah</h2></div>',
            unsafe_allow_html=True)

sol = {"Sumatera":("Revitalisasi sekolah, irigasi, koperasi",
                    "IoT Smart Farming • Fleet Management • Learning Platform • IoT Smart Water Meter"),
       "Kalimantan":("Infrastruktur, energi, transportasi IKN",
                      "IoT Smart City • Industrial IoT • IoT Smart Energy Meter"),
       "Jawa":("Megalopolis — industri teknologi & ekonomi kreatif",
                "Omnichannel • Msight/Tsurvey • IoT Monitoring Management"),
       "Bali Nusra":("Pendidikan, gizi, koperasi pariwisata",
                      "DigiAds • Msight/Tsurvey • IoT Smart Connectivity • Omnichannel"),
       "Sulawesi":("Sekolah rakyat, irigasi, smart tourism",
                    "IoT FleetSight • IoT Smart Connectivity • IoT Smart Water Meter"),
       "Papua Maluku":("Pendidikan & kesehatan dasar, perikanan",
                        "Basic Connectivity • IoT Smart Connectivity • OmniChannel")}

cs = st.columns(3)
for i,(w,(f,p)) in enumerate(sol.items()):
    cf = W_CFG.get(w, W_CFG["Sumatera"])
    with cs[i%3]:
        st.markdown(f"""
        <div style='background:{cf["bg"]};border:2px solid {cf["c"]};border-left:6px solid {cf["c"]};
                    border-radius:14px;padding:16px 18px;margin-bottom:12px;'>
            <h4 style='color:{cf["c"]}!important;margin:0 0 6px;font-size:15px;'>{cf["i"]} {w}</h4>
            <p style='color:#333!important;font-size:11px;margin:0 0 4px;'><strong>Fokus:</strong> {f}</p>
            <p style='color:{cf["c"]}!important;font-size:11px;font-weight:700;margin:0;'>💡 {p}</p>
        </div>""", unsafe_allow_html=True)

st.markdown("---")
st.markdown('<div class="sec"><h2>📈 Proyeksi Kenaikan Anggaran 2025 → 2026</h2></div>',
            unsafe_allow_html=True)

ang = pd.DataFrame({"Bidang":["Pemb. Ekonomi &\nInfrastruktur","Pertahanan","Pendidikan",
                               "Subsidi Energi &\nNon-Energi","Kesehatan &\nPerl. Sosial"],
                     "2025":[324,479,520,288,552],"2026":[488,706,580,318,599],
                     "Pct":[50.4,47.5,11.6,10.7,8.6]})

fig,(ax1,ax2) = plt.subplots(1,2,figsize=(17,5.5),gridspec_kw={"width_ratios":[1.3,1]})
fig.patch.set_facecolor("#FAFAFA")
ax1.set_facecolor("#FAFAFA"); ax2.set_facecolor("#FAFAFA")
x = np.arange(len(ang)); w = 0.32
ax1.bar(x-w/2,ang["2025"],w,label="2025",color="#666",edgecolor="white",linewidth=1.5)
ax1.bar(x+w/2,ang["2026"],w,label="2026",color="#ED1C24",edgecolor="white",linewidth=1.5)
for j in range(len(ang)):
    ax1.text(x[j]-w/2,ang.iloc[j]["2025"]+8,f'Rp {ang.iloc[j]["2025"]:.0f}T',
             ha="center",fontsize=9,fontweight="bold",color="#666")
    ax1.text(x[j]+w/2,ang.iloc[j]["2026"]+8,f'Rp {ang.iloc[j]["2026"]:.0f}T',
             ha="center",fontsize=9,fontweight="bold",color="#ED1C24")
ax1.set_xticks(x); ax1.set_xticklabels(ang["Bidang"],fontsize=9,fontweight="bold")
ax1.set_title("Anggaran 2025 vs 2026 (Triliun Rp)",fontsize=14,fontweight="bold",pad=12)
ax1.legend(fontsize=11); ax1.set_ylim(0,780)
for s in ["top","right"]: ax1.spines[s].set_visible(False)

cpct = ["#ED1C24" if p>30 else "#1565C0" if p>10 else "#E6A817" for p in ang["Pct"]]
ax2.barh(range(len(ang)-1,-1,-1),ang["Pct"],color=cpct,height=0.5,edgecolor="white",linewidth=1.5)
for j in range(len(ang)):
    ax2.text(ang.iloc[j]["Pct"]+1,len(ang)-1-j,f'  +{ang.iloc[j]["Pct"]}%',
             va="center",fontsize=13,fontweight="bold",color="#111")
ax2.set_yticks(range(len(ang)-1,-1,-1))
ax2.set_yticklabels(ang["Bidang"],fontsize=9,fontweight="bold")
ax2.set_title("Kenaikan (%)",fontsize=14,fontweight="bold",pad=12); ax2.set_xlim(0,63)
for s in ["top","right"]: ax2.spines[s].set_visible(False)
plt.tight_layout()
st.pyplot(fig, use_container_width=True); plt.close(fig)

# FOOTER
st.markdown("---")
st.markdown(f"""
<div style="text-align:center;padding:24px 0;color:#BBB!important;font-size:11px;">
    Dashboard Top 20 SI Channel Potensial — Data Realisasi INAPROC 2025<br>
    Telkomsel Enterprise | Bid Management — Data Science | {datetime.now():%Y}<br>
    <span style="font-size:10px;">🔓 Nama vendor tersensor telah di-uncensor via fuzzy matching</span>
</div>""", unsafe_allow_html=True)