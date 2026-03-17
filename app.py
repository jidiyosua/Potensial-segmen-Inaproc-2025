"""
═══════════════════════════════════════════════════════════════════════════
  DASHBOARD REALISASI PENGADAAN PEMERINTAH — INAPROC
  Telkomsel Enterprise | Bid Management — Data Science
  Database: Datamart_Final_Report.db (SQLite)
  ───────────────────────────────────────────────────────────────────────
  streamlit run app.py
  
  OPTIMIZED v2 — Mega-regex, Parquet cache, Chart fuzzy uncensoring
═══════════════════════════════════════════════════════════════════════════
"""

import streamlit as st
import pandas as pd
import numpy as np
import sqlite3
import seaborn as sns
import matplotlib.pyplot as plt
import matplotlib.ticker as mticker
import textwrap, os, io, hashlib, re, json, gdown
from datetime import datetime
from difflib import SequenceMatcher
from openpyxl.styles import Font, PatternFill, Alignment, Border, Side
from openpyxl.utils import get_column_letter

# ═══════════════════════════════════════════════════════════════════════════
# PAGE CONFIG
# ═══════════════════════════════════════════════════════════════════════════
st.set_page_config(
    page_title="Realisasi Pengadaan INAPROC — Telkomsel Enterprise",
    page_icon="📊", layout="wide", initial_sidebar_state="expanded")

# ═══════════════════════════════════════════════════════════════════════════
# PASSWORD AUTHENTICATION
# ═══════════════════════════════════════════════════════════════════════════
def _hash(pw):
    return hashlib.sha256(pw.encode()).hexdigest()

def _get_valid_hash():
    try:
        return st.secrets["auth"]["password_hash"]
    except (KeyError, FileNotFoundError):
        return hashlib.sha256("TelkomselEnterprise2025ebpm".encode()).hexdigest()

def check_password():
    if st.session_state.get("authenticated"):
        return True
    st.markdown("""
    <style>
        .login-box{max-width:440px;margin:80px auto;background:#FFF;border-radius:20px;
            padding:48px 40px;text-align:center;box-shadow:0 8px 40px rgba(0,0,0,0.08);
            border-top:5px solid #ED1C24;}
        .login-box h2{color:#111!important;font-size:22px!important;font-weight:800!important;margin:16px 0 4px!important;}
        .login-box p{color:#888!important;font-size:13px!important;margin:0 0 24px!important;}
    </style>
    <div class="login-box">
        <div style="font-size:48px">🔒</div>
        <h2>Telkomsel Enterprise</h2>
        <p>Dashboard Realisasi Pengadaan INAPROC<br>Masukkan password untuk melanjutkan</p>
    </div>""", unsafe_allow_html=True)
    _,col_m,_ = st.columns([1,2,1])
    with col_m:
        password = st.text_input("Password", type="password", key="login_pw", placeholder="Masukkan password...")
        if st.button("🔐 Masuk", use_container_width=True, type="primary"):
            if _hash(password) == _get_valid_hash():
                st.session_state["authenticated"] = True
                st.rerun()
            else:
                st.error("❌ Password salah.")
        st.markdown("<div style='text-align:center;margin-top:20px'><span style='color:#BBB;font-size:11px'>Bid Management — Data Science | 2026</span></div>", unsafe_allow_html=True)
    return False

if not check_password():
    st.stop()

# ═══════════════════════════════════════════════════════════════════════════
# CSS — TELKOMSEL ENTERPRISE BRANDING
# ═══════════════════════════════════════════════════════════════════════════
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght@400;600;700;800&display=swap');
.stApp{background-color:#FAFAFA;font-family:'Plus Jakarta Sans',sans-serif;}
.stApp,.stApp p,.stApp span,.stApp div,.stApp label,.stApp li,
.stApp h1,.stApp h2,.stApp h3,.stApp h4,.stApp h5{color:#111!important;}
section[data-testid="stSidebar"]{background:linear-gradient(180deg,#1A1A2E 0%,#16213E 100%);}
section[data-testid="stSidebar"] *{color:#E0E0E0!important;}
section[data-testid="stSidebar"] .stRadio label span{color:#FFF!important;}
.block-container{padding-top:1rem;max-width:1400px;}

.hero{background:linear-gradient(135deg,#ED1C24 0%,#9B1B1F 60%,#1A1A2E 100%);
    padding:32px 40px;border-radius:20px;margin-bottom:28px;
    box-shadow:0 8px 32px rgba(237,28,36,0.25);position:relative;overflow:hidden;}
.hero::after{content:'';position:absolute;top:-50%;right:-10%;width:300px;height:300px;
    background:rgba(255,255,255,0.04);border-radius:50%;}
.hero h1{color:#FFF!important;font-size:30px!important;font-weight:800!important;margin:0!important;letter-spacing:-0.5px;}
.hero p{color:rgba(255,255,255,0.7)!important;font-size:14px!important;margin:6px 0 0!important;}

.kpi{background:#FFF;border:1px solid #E8E8E8;border-radius:16px;padding:20px 16px;
    text-align:center;box-shadow:0 2px 12px rgba(0,0,0,0.04);transition:transform 0.2s;margin-bottom:10px;}
.kpi:hover{transform:translateY(-2px);box-shadow:0 4px 20px rgba(0,0,0,0.08);}
.kpi .num{color:#111!important;font-size:22px;font-weight:800;line-height:1.1;}
.kpi .lab{color:#888!important;font-size:10px;font-weight:700;text-transform:uppercase;letter-spacing:1.2px;margin-bottom:8px;}
.kpi .sub{color:#AAA!important;font-size:10px;margin-top:6px;}

.sec{background:#FFF;border-left:5px solid #ED1C24;padding:14px 24px;margin:32px 0 18px;
    border-radius:0 12px 12px 0;box-shadow:0 1px 8px rgba(0,0,0,0.04);}
.sec h2{color:#111!important;font-size:20px!important;font-weight:800!important;margin:0!important;}
.sec p{color:#666!important;font-size:13px!important;margin:4px 0 0!important;}
.sec-b{background:#F5F8FF;border-left:5px solid #1565C0;padding:14px 24px;margin:32px 0 18px;
    border-radius:0 12px 12px 0;box-shadow:0 1px 8px rgba(0,0,0,0.04);}
.sec-b h2{color:#111!important;font-size:20px!important;font-weight:800!important;margin:0!important;}
.sec-b p{color:#666!important;font-size:13px!important;margin:4px 0 0!important;}

.rcard{border-radius:16px;padding:22px 26px;margin:10px 0;border:2px solid;box-shadow:0 2px 12px rgba(0,0,0,0.04);}
.rcard h3{font-size:20px;font-weight:800;margin:0 0 4px;}
.rcard p{font-size:12px;margin:2px 0;}

.streamlit-expanderHeader{font-size:14px!important;font-weight:700!important;}
.stTabs [data-baseweb="tab"]{font-weight:700;font-size:13px;padding:10px 20px;}
.stDownloadButton>button{background:linear-gradient(135deg,#1A1A2E,#16213E)!important;
    color:#FFF!important;font-weight:700!important;border-radius:10px!important;
    border:none!important;padding:8px 20px!important;}
.stDownloadButton>button:hover{background:linear-gradient(135deg,#ED1C24,#C41920)!important;}
#MainMenu{visibility:hidden;} footer{visibility:hidden;}
</style>""", unsafe_allow_html=True)

# ═══════════════════════════════════════════════════════════════════════════
# CONSTANTS
# ═══════════════════════════════════════════════════════════════════════════
DB_NAME = "Datamart_Final_Report.db"
GDRIVE_FILE_ID = "1vo4oi_v8ePU6WAPeRmsUG_-bbTsjMmqD"
PARQUET_CACHE = "datamart_cache.parquet"  # ← NEW: Parquet cache

WILAYAH_MAP = {
    "Aceh":"Sumatera","Sumatera Utara":"Sumatera","Sumatera Barat":"Sumatera",
    "Riau":"Sumatera","Kepulauan Riau":"Sumatera","Jambi":"Sumatera",
    "Sumatera Selatan":"Sumatera","Bangka Belitung":"Sumatera",
    "Bengkulu":"Sumatera","Lampung":"Sumatera",
    "DKI Jakarta":"Jawa","Jawa Barat":"Jawa","Jawa Tengah":"Jawa",
    "DI Yogyakarta":"Jawa","Jawa Timur":"Jawa","Banten":"Jawa",
    "Kalimantan Barat":"Kalimantan","Kalimantan Tengah":"Kalimantan",
    "Kalimantan Selatan":"Kalimantan","Kalimantan Timur":"Kalimantan",
    "Kalimantan Utara":"Kalimantan",
    "Sulawesi Utara":"Sulawesi","Gorontalo":"Sulawesi","Sulawesi Tengah":"Sulawesi",
    "Sulawesi Selatan":"Sulawesi","Sulawesi Barat":"Sulawesi","Sulawesi Tenggara":"Sulawesi",
    "Bali":"Bali NusRa","Nusa Tenggara Barat":"Bali NusRa","Nusa Tenggara Timur":"Bali NusRa",
    "Papua":"Papua Maluku","Papua Barat":"Papua Maluku","Papua Selatan":"Papua Maluku",
    "Papua Tengah":"Papua Maluku","Papua Pegunungan":"Papua Maluku",
    "Papua Barat Daya":"Papua Maluku","Maluku":"Papua Maluku","Maluku Utara":"Papua Maluku",
}

WILAYAH_LIST = ["Sumatera","Jawa","Kalimantan","Sulawesi","Bali NusRa","Papua Maluku"]

W_CFG = {
    "Sumatera":     {"c":"#ED1C24","bg":"#FFF3F3","i":"🔴"},
    "Jawa":         {"c":"#1565C0","bg":"#E8F0FE","i":"🔵"},
    "Kalimantan":   {"c":"#E6A817","bg":"#FFF8E1","i":"🟡"},
    "Sulawesi":     {"c":"#2E7D32","bg":"#E8F5E9","i":"🟢"},
    "Bali NusRa":   {"c":"#E65100","bg":"#FFF3ED","i":"🟠"},
    "Papua Maluku": {"c":"#6C5CE7","bg":"#F3F0FF","i":"🟣"},
}

WILAYAH_STRATEGY = {
    "Sumatera":{"tkd":"TKD diarahkan ke revitalisasi sekolah, irigasi, dan koperasi lokal.",
        "dinas":["Dinas Pendidikan","Dinas PUPR","Dinas Pertanian","Dinas Koperasi"],
        "produk":"IoT Smart Farming, Fleet Management, Telkomsel Learning Platform"},
    "Jawa":{"tkd":"Didorong menjadi megalopolis nasional — pusat industri teknologi dan ekonomi kreatif.",
        "dinas":["Diskominfo","Dinas Perindustrian","Dinas Perdagangan","Bappenda"],
        "produk":"Omnichannel, Msight, Tsurvey, IoT Monitoring Management"},
    "Kalimantan":{"tkd":"TKD diarahkan untuk infrastruktur dasar, energi, dan transportasi pendukung IKN.",
        "dinas":["Dinas PUPR","Dinas Perhubungan","Dinas ESDM"],
        "produk":"IoT Smart City, Industrial IoT, IoT Smart Energy Meter"},
    "Sulawesi":{"tkd":"TKD diarahkan untuk sekolah rakyat, irigasi pertanian, dan smart tourism infrastructure.",
        "dinas":["Dinas Pendidikan","Dinas PUPR","Dinas Pariwisata"],
        "produk":"IoT FleetSight, IoT Smart Connectivity, Msight/TSurvey"},
    "Bali NusRa":{"tkd":"TKD diarahkan untuk peningkatan kualitas pendidikan, gizi dan koperasi pariwisata lokal.",
        "dinas":["Dinas Pendidikan","Dinas Kesehatan","Dinas Pariwisata","Dinas Koperasi"],
        "produk":"DigiAds, Msight, Tsurvey, IoT Smart Connectivity"},
    "Papua Maluku":{"tkd":"TKD diarahkan ke pendidikan & kesehatan dasar, pengembangan perikanan & energi terbarukan.",
        "dinas":["Dinas Pendidikan","Dinas Kesehatan","Dinas Perikanan","Dinas ESDM"],
        "produk":"Basic Connectivity, IoT Smart Connectivity, OmniChannel"},
}

DINAS_PATTERNS = {
    "Dinas Pendidikan":  r'(?i)(dinas\s*pendidikan|disdik)',
    "Dinas PUPR":        r'(?i)(dinas\s*(pupr|pekerjaan\s*umum|pu\b|cipta\s*karya))',
    "Dinas Pertanian":   r'(?i)(dinas\s*pertanian|distan|ketahanan\s*pangan)',
    "Dinas Koperasi":    r'(?i)(dinas\s*koperasi|dinkop)',
    "Dinas Kesehatan":   r'(?i)(dinas\s*kesehatan|dinkes)',
    "Dinas Pariwisata":  r'(?i)(dinas\s*pariwisata|dispar)',
    "Dinas Perhubungan": r'(?i)(dinas\s*perhubungan|dishub)',
    "Dinas ESDM":        r'(?i)(dinas\s*(esdm|energi))',
    "Dinas Perindustrian":r'(?i)(dinas\s*perindustrian|disperindag)',
    "Dinas Perdagangan": r'(?i)(dinas\s*perdagangan)',
    "Bappenda":          r'(?i)(bappenda|pendapatan\s*daerah)',
    "Diskominfo":        r'(?i)(diskominfo|dinas\s*komunikasi|kominfo|informatika)',
    "Dinas Perikanan":   r'(?i)(dinas\s*(perikanan|kelautan))',
}

# Pre-compile dinas patterns (avoid recompilation per call)
DINAS_COMPILED = {k: re.compile(v) for k, v in DINAS_PATTERNS.items()}

TEMA_KL = {
    "🌾 Ketahanan Pangan": {
        "kw_inst":[r"(?i)(kementerian\s*pertanian|kementan)",r"(?i)(kementerian\s*kelautan|kemen.?kkp)",
                   r"(?i)(badan\s*riset\s*dan\s*inovasi|brin\b)",r"(?i)(kemendagri|kementerian\s*dalam\s*negeri)",
                   r"(?i)(bappenas)",r"(?i)(kemenko\s*pmk)"],
        "kw_satker":[r"(?i)(pertanian|ketahanan\s*pangan|perikanan|kelautan|peternakan|perkebunan|tanaman\s*pangan)"],
        "color":"#2E7D32","icon":"🌾","desc":"Ketahanan pangan nasional, pertanian, perikanan"
    },
    "🍽️ Program MBG": {
        "kw_inst":[r"(?i)(kementerian\s*kesehatan|kemenkes)",r"(?i)(kementerian\s*sosial|kemensos)",
                   r"(?i)(bkkbn)",r"(?i)(kemenko\s*pmk)",r"(?i)(badan\s*gizi\s*nasional|bgn\b)"],
        "kw_satker":[r"(?i)(gizi|kesehatan\s*masyarakat|perlindungan\s*sosial|keluarga\s*berencana)"],
        "color":"#E65100","icon":"🍽️","desc":"Program makan bergizi, gizi masyarakat"
    },
    "🎓 Penguatan Pendidikan": {
        "kw_inst":[r"(?i)(kementerian\s*pendidikan|kemendik)",r"(?i)(kemen\s*pan|pendayagunaan\s*aparatur)",
                   r"(?i)(lembaga\s*administrasi\s*negara)",r"(?i)(kementerian\s*agama|kemenag)",r"(?i)(bappenas)"],
        "kw_satker":[r"(?i)(pendidikan|universitas|politeknik|sekolah|pelatihan|diklat|perguruan\s*tinggi)"],
        "color":"#1565C0","icon":"🎓","desc":"Pendidikan tinggi, dasar-menengah, keagamaan"
    },
    "🏘️ Desa, Koperasi, UMKM": {
        "kw_inst":[r"(?i)(kemendagri|kementerian\s*dalam\s*negeri)",r"(?i)(kemenkop|kementerian\s*koperasi)",
                   r"(?i)(kemendes|kementerian\s*desa)",r"(?i)(kemenkeu|kementerian\s*keuangan)",r"(?i)(bappenas)"],
        "kw_satker":[r"(?i)(desa\b|koperasi|umkm|usaha\s*kecil|usaha\s*mikro|pemberdayaan\s*masyarakat)"],
        "color":"#6D4C41","icon":"🏘️","desc":"Pembangunan desa, koperasi, UMKM"
    },
    "🏥 Sektor Kesehatan": {
        "kw_inst":[r"(?i)(kementerian\s*kesehatan|kemenkes)",r"(?i)(bpjs|jaminan\s*sosial)",
                   r"(?i)(badan\s*riset\s*dan\s*inovasi|brin\b)",r"(?i)(kemensos)",r"(?i)(kemenko\s*pmk)"],
        "kw_satker":[r"(?i)(kesehatan|rumah\s*sakit|rsud|puskesmas|farmasi|alat\s*kesehatan)"],
        "color":"#AD1457","icon":"🏥","desc":"Kesehatan masyarakat, BPJS, riset kesehatan"
    },
    "🛡️ Pertahanan Semesta": {
        "kw_inst":[r"(?i)(kementerian\s*pertahanan|kemenhan)",r"(?i)(tentara\s*nasional|tni\b)",
                   r"(?i)(kepolisian|polri|polda|polres)",r"(?i)(bnpt)",r"(?i)(bssn|badan\s*siber)",
                   r"(?i)(bakamla)",r"(?i)(kemenkumham|kementerian\s*hukum)"],
        "kw_satker":[r"(?i)(pertahanan|militer|keamanan|intelijen|siber|imigrasi|pemasyarakatan)"],
        "color":"#37474F","icon":"🛡️","desc":"Pertahanan, keamanan, siber, kepolisian"
    },
    "📡 KOMDIGI": {
        "kw_inst":[r"(?i)(kementerian\s*komunikasi|komdigi|kominfo)",r"(?i)(bakti\b)"],
        "kw_satker":[r"(?i)(komunikasi|informatika|digital\b|telekomunikasi|penyiaran)"],
        "color":"#7B1FA2","icon":"📡","desc":"Komunikasi digital, infrastruktur telekomunikasi"
    },
}

# Pre-compile tema patterns
for _t in TEMA_KL.values():
    _t["_re_inst"] = [re.compile(p) for p in _t["kw_inst"]]
    _t["_re_satker"] = [re.compile(p) for p in _t["kw_satker"]]

# ═══════════════════════════════════════════════════════════════════════════
# ICT CLASSIFICATION — MEGA-REGEX (COMPILED ONCE)
# ═══════════════════════════════════════════════════════════════════════════
# OLD: 50+ individual .str.contains() calls → ~100 passes over 4M rows
# NEW: 1 compiled mega-regex → 2 passes total (whitelist + blacklist)

ICT_WHITELIST = [
    r'\binternet\b',r'\bbandwidth\b',r'\bfiber\s*optik?\b',r'\bjaringan\b',
    r'\bwifi\b',r'\bwi-fi\b',r'\bhotspot\b',r'\bmpls\b',r'\bvpn\b',r'\bsd-wan\b',
    r'\bbroadband\b',r'\btelekomunikasi\b',r'\bfttx?\b',r'\bdata\s*center\b',
    r'\bserver\b(?!.*makanan)',r'\bkomputer\b',r'\blaptop\b',r'\bnotebook\b',
    r'\bprinter\b',r'\bscanner\b',r'\bups\b',
    r'\bswitch\b(?!.*listrik)',r'\brouter\b',r'\bfirewall\b',r'\baccess\s*point\b',
    r'\bstorage\b',r'\brack\b(?!.*sepeda)',r'\bcctv\b',r'\bip\s*camera\b',
    r'\bnetwork\b',r'\binfrastruktur\s*(it|ti|ict|teknologi)\b',
    r'\baplikasi\b',r'\bsoftware\b',r'\bperangkat\s*lunak\b',r'\blisens[i]\b',
    r'\bsistem\s*informasi\b',r'\be-gov\w*\b',r'\bwebsite\b',r'\bportal\b',
    r'\bcloud\b',r'\bsaas\b',r'\berp\b',r'\bdatabase\b',r'\bbig\s*data\b',
    r'\bmachine\s*learning\b',r'\bcyber\s*security\b',r'\bkeamanan\s*siber\b',
    r'\biot\b',r'\bsmart\s*(city|village|building|farming|meter)\b',
    r'\bsensor\b(?!.*gas\s*lpg)',r'\btelemetri\b',r'\bsurveillance\b',
    r'\bsim\s*card\b',r'\bpulsa\b',r'\bpaket\s*data\b',r'\bsms\s*(gateway|blast)\b',
    r'\bvoip\b',r'\bip\s*phone\b',r'\bpabx\b',r'\bvideo\s*conference\b',
    r'\bdigital\s*(signage|marketing|transform)\b',r'\bomnichannel\b',
    r'\bpc\b(?!.*pcs)',r'\blan\b(?!.*lain)',r'\bwan\b(?!.*wan)',
]

ICT_BLACKLIST = [
    r'\bgaji\b',r'\bhonor\w*\b',r'\btunjangan\b',r'\bmakanan\b',r'\bminuman\b',
    r'\bjas\s*hujan\b',r'\bseragam\b',r'\bbaju\b',r'\bsepatu\b',
    r'\bkonstruksi\b(?!.*(smart|iot|sensor))',r'\bjalan\b(?!.*(smart|monitoring))',
    r'\bjembatan\b',r'\birigasi\b(?!.*(smart|iot))',
    r'\bpengolah\w*\s*sampah\b',r'\bpetugas\b',r'\bcaraka\b',r'\bnormalisasi\b',
    r'\brestorasi\b',r'\bperawat\s*taman\b',
    r'\bpemeliharaan\b(?!.*(server|jaringan|it|network))',
]

# ★ MEGA-REGEX: Compile all patterns into ONE regex each
# Patterns with negative lookahead can't be simply ORed, so we handle them specially
_ICT_WL_SIMPLE = []
_ICT_WL_LOOKAHEAD = []
for p in ICT_WHITELIST:
    if '(?!' in p:
        _ICT_WL_LOOKAHEAD.append(re.compile(p, re.IGNORECASE))
    else:
        _ICT_WL_SIMPLE.append(p)

_ICT_BL_SIMPLE = []
_ICT_BL_LOOKAHEAD = []
for p in ICT_BLACKLIST:
    if '(?!' in p:
        _ICT_BL_LOOKAHEAD.append(re.compile(p, re.IGNORECASE))
    else:
        _ICT_BL_SIMPLE.append(p)

# Compile the simple patterns into mega-regex
_ICT_WL_MEGA = re.compile('|'.join(_ICT_WL_SIMPLE), re.IGNORECASE) if _ICT_WL_SIMPLE else None
_ICT_BL_MEGA = re.compile('|'.join(_ICT_BL_SIMPLE), re.IGNORECASE) if _ICT_BL_SIMPLE else None


# ═══════════════════════════════════════════════════════════════════════════
# FORMAT HELPERS
# ═══════════════════════════════════════════════════════════════════════════
def fmt_rp(v):
    if pd.isna(v) or v == 0: return "Rp 0"
    a = abs(v)
    if a >= 1e12: return f"Rp {v/1e12:,.2f} T"
    if a >= 1e9:  return f"Rp {v/1e9:,.2f} M"
    if a >= 1e6:  return f"Rp {v/1e6:,.1f} Jt"
    return f"Rp {v:,.0f}"

def fmt_s(v):
    if pd.isna(v) or v == 0: return "0"
    a = abs(v)
    if a >= 1e12: return f"{v/1e12:.1f}T"
    if a >= 1e9:  return f"{v/1e9:.1f}M"
    if a >= 1e6:  return f"{v/1e6:.0f}Jt"
    return f"{v:,.0f}"

def fmt_n(v):
    if pd.isna(v): return "0"
    return f"{int(v):,}".replace(",", ".")

def kpi(lb, vl, sb=""):
    s = f'<div class="sub">{sb}</div>' if sb else ""
    return f'<div class="kpi"><div class="lab">{lb}</div><div class="num">{vl}</div>{s}</div>'

# ═══════════════════════════════════════════════════════════════════════════
# EXCEL EXPORT
# ═══════════════════════════════════════════════════════════════════════════
def _safe_sheet(name):
    return re.sub(r'[\*\?/\\\[\]:]', '', str(name))[:31].strip() or "Data"

def to_excel_styled(df, sheet_name="Data"):
    sheet_name = _safe_sheet(sheet_name)
    buf = io.BytesIO()
    with pd.ExcelWriter(buf, engine="openpyxl") as w:
        df.to_excel(w, index=False, sheet_name=sheet_name)
        ws = w.sheets[sheet_name]
        hf = Font(name="Calibri", bold=True, color="FFFFFF", size=11)
        hfl = PatternFill(start_color="C41920", end_color="C41920", fill_type="solid")
        ha = Alignment(horizontal="center", vertical="center", wrap_text=True)
        thin = Side(style="thin", color="DDDDDD")
        brd = Border(top=thin, left=thin, right=thin, bottom=thin)
        bf = Font(name="Calibri", size=10)
        af = PatternFill(start_color="FFF5F5", end_color="FFF5F5", fill_type="solid")
        for ci in range(1, len(df.columns)+1):
            c = ws.cell(row=1, column=ci); c.font=hf; c.fill=hfl; c.alignment=ha; c.border=brd
            ws.column_dimensions[get_column_letter(ci)].width = max(15, min(45, len(str(c.value or ""))+4))
        for ri in range(2, len(df)+2):
            for ci in range(1, len(df.columns)+1):
                c = ws.cell(row=ri, column=ci); c.font=bf; c.border=brd
                c.alignment = Alignment(vertical="center", wrap_text=True)
                if ri % 2 == 0: c.fill = af
        ws.auto_filter.ref = ws.dimensions; ws.freeze_panes = "A2"
    return buf.getvalue()

# ═══════════════════════════════════════════════════════════════════════════
# ★ FUZZY UNCENSORING — pre-computed at load time
# ═══════════════════════════════════════════════════════════════════════════
def _build_clean_names_index(all_names):
    """Build lookup structures from uncensored vendor names."""
    clean = [n for n in all_names if '*' not in n and len(n) > 2]
    index = {}
    for n in clean:
        key = (n[0].upper(), len(n))
        index.setdefault(key, []).append(n)
    return clean, index


def _uncensor_name(censored, clean_index):
    """Match a single censored name like 'P* W******' to best uncensored name."""
    try:
        pat_str = ""
        for ch in censored:
            if ch == '*':
                pat_str += '.'
            elif ch in r'\.[](){}+?^$|':
                pat_str += '\\' + ch
            else:
                pat_str += ch
        pat_re = re.compile(f'^{pat_str}$', re.IGNORECASE)
        first_char = censored[0].upper() if censored[0] != '*' else None
        candidates = []
        if first_char:
            bucket = clean_index.get((first_char, len(censored)), [])
            candidates = [n for n in bucket if pat_re.match(n)]
        if not candidates and first_char:
            for delta in [-1, 1]:
                bucket = clean_index.get((first_char, len(censored) + delta), [])
                candidates.extend(n for n in bucket if pat_re.match(n))
        if candidates:
            return candidates[0]
    except re.error:
        pass
    first_char = censored[0].upper() if censored[0] != '*' else None
    best_score, best_match = 0.0, None
    if first_char:
        for delta in range(-2, 3):
            bucket = clean_index.get((first_char, len(censored) + delta), [])
            for cn in bucket:
                score = SequenceMatcher(None, censored.upper(), cn.upper()).ratio()
                if score > best_score:
                    best_score = score
                    best_match = cn
    if best_score >= 0.6:
        return best_match
    return censored


def _build_uncensor_mapping(all_names):
    """Pre-compute a dict mapping censored→uncensored for ALL starred names.
    Called once at load time. Names without '*' are skipped."""
    censored_names = [n for n in all_names if '*' in n]
    if not censored_names:
        return {}
    _, clean_index = _build_clean_names_index(all_names)
    mapping = {}
    for cn in censored_names:
        result = _uncensor_name(cn, clean_index)
        if result != cn:
            mapping[cn] = result
    return mapping


def uncensor_for_chart(agg_df, uncensor_map, name_col="Nama_Pemenang"):
    """Uncensor starred names using pre-computed dict lookup.
    Names without '*' are untouched."""
    if len(agg_df) == 0 or not uncensor_map:
        return agg_df
    mask = agg_df[name_col].str.contains(r'\*', na=False)
    if not mask.any():
        return agg_df
    result = agg_df.copy()
    for idx in result[mask].index:
        old_name = result.at[idx, name_col]
        new_name = uncensor_map.get(old_name, old_name)
        if new_name != old_name:
            result.at[idx, name_col] = new_name
    return result


# ═══════════════════════════════════════════════════════════════════════════
# DATA LOADING & PREPROCESSING
# ═══════════════════════════════════════════════════════════════════════════
def _find_db():
    sd = os.path.dirname(os.path.abspath(__file__))
    db_path = os.path.join(sd, DB_NAME)
    if os.path.exists(db_path):
        return db_path
    try:
        url = f"https://drive.google.com/uc?id={GDRIVE_FILE_ID}"
        gdown.download(url, db_path, quiet=False)
        if os.path.exists(db_path):
            return db_path
    except Exception as e:
        st.error(f"❌ Gagal download database dari Google Drive: {e}")
    return None

VENDOR_MAPPING_FILE = "vendor_mapping.json"

def _load_vendor_mapping():
    sd = os.path.dirname(os.path.abspath(__file__))
    for base in [sd, ".", os.getcwd()]:
        p = os.path.join(base, VENDOR_MAPPING_FILE)
        if os.path.exists(p):
            with open(p, "r", encoding="utf-8") as f:
                return json.load(f)
    return {}


def _vectorized_ict_fast(nama_paket_series):
    """★ OPTIMIZED: Mega-regex ICT classification.
    OLD: ~100 .str.contains() calls (50 whitelist + 17 blacklist patterns)
    NEW: 2 mega-regex calls + a few lookahead patterns = ~50x faster
    """
    text = nama_paket_series.fillna("").str.lower()
    result = pd.Series("Non-ICT", index=text.index, dtype="object")

    # ── Blacklist: mega-regex (1 call) + lookahead patterns ──
    blacklist_mask = pd.Series(False, index=text.index)
    if _ICT_BL_MEGA:
        blacklist_mask |= text.str.contains(_ICT_BL_MEGA, na=False)
    for pat in _ICT_BL_LOOKAHEAD:
        blacklist_mask |= text.str.contains(pat, na=False)

    # ── Whitelist: mega-regex (1 call) + lookahead patterns ──
    ict_mask = pd.Series(False, index=text.index)
    if _ICT_WL_MEGA:
        ict_mask |= text.str.contains(_ICT_WL_MEGA, na=False)
    for pat in _ICT_WL_LOOKAHEAD:
        ict_mask |= text.str.contains(pat, na=False)

    result[ict_mask & ~blacklist_mask] = "ICT"
    return result


def _get_parquet_path():
    sd = os.path.dirname(os.path.abspath(__file__))
    return os.path.join(sd, PARQUET_CACHE)


@st.cache_data(show_spinner="🔄 Memuat database…")
def load_and_process():
    parquet_path = _get_parquet_path()

    # ═══ FAST PATH: Load from Parquet cache ═══
    if os.path.exists(parquet_path):
        try:
            df = pd.read_parquet(parquet_path)
            if all(c in df.columns for c in ["Nama_Pemenang","Pagu_Rp","Sektor","Wilayah","Provinsi","is_pemda"]):
                total_rows = len(df)
                n_matched = 0
                # ★ Pre-compute uncensor mapping (uses cached index)
                uncensor_map = _build_uncensor_mapping(df["Nama_Pemenang"].unique())
                return df, total_rows, n_matched, None, uncensor_map
        except Exception:
            pass

    # ═══ SLOW PATH: Load from SQLite → process → save Parquet ═══
    db_path = _find_db()
    if not db_path:
        return None, 0, 0, f"Database {DB_NAME} tidak ditemukan.", {}

    conn = sqlite3.connect(db_path)
    tables = pd.read_sql("SELECT name FROM sqlite_master WHERE type='table'", conn)
    if len(tables) == 0:
        conn.close()
        return None, 0, 0, "Database kosong.", {}
    tbl = tables['name'].iloc[0]

    pragma = conn.execute(f'PRAGMA table_info([{tbl}])').fetchall()
    db_columns = [row[1] for row in pragma]

    ESSENTIAL = ["Nama_Paket","Pagu_Rp","Instansi_Pembeli","Satuan_Kerja",
                 "Lokasi","Nama_Pemenang"]
    OPTIONAL  = ["ID_RUP","Kategori_Paket","Metode_Pemilihan","Jenis_Pengadaan",
                 "Total_Pelaksanaan_Rp","Sumber_Data"]

    missing_essential = [c for c in ESSENTIAL if c not in db_columns]
    if missing_essential:
        conn.close()
        return None, 0, 0, (f"Kolom essential tidak ditemukan: {missing_essential}\n"
                            f"Kolom di DB: {db_columns}"), {}

    select_cols = []
    for c in ESSENTIAL + OPTIONAL:
        if c in db_columns and c not in select_cols:
            select_cols.append(c)

    cols_sql = ", ".join([f'[{c}]' for c in select_cols])
    pagu_cast = "CAST([Pagu_Rp] AS REAL)" if "Pagu_Rp" in db_columns else "0"
    sql = (f"SELECT {cols_sql} FROM [{tbl}] "
           f"WHERE [Nama_Pemenang] IS NOT NULL AND TRIM([Nama_Pemenang]) != '' "
           f"AND {pagu_cast} > 0")

    total_rows = pd.read_sql(f"SELECT COUNT(*) as n FROM [{tbl}]", conn).iloc[0, 0]
    df = pd.read_sql(sql, conn)
    conn.close()

    for c in ESSENTIAL + OPTIONAL:
        if c not in df.columns:
            df[c] = ""

    df["Pagu_Rp"] = pd.to_numeric(df["Pagu_Rp"], errors="coerce").fillna(0)
    df["Total_Pelaksanaan_Rp"] = pd.to_numeric(df.get("Total_Pelaksanaan_Rp", 0), errors="coerce").fillna(0)
    df = df[df["Pagu_Rp"] > 0].reset_index(drop=True)

    # Vendor mapping
    n_matched = 0
    mapping = _load_vendor_mapping()
    if mapping:
        mask = df["Nama_Pemenang"].isin(mapping.keys())
        n_matched = mask.sum()
        if n_matched > 0:
            df.loc[mask, "Nama_Pemenang"] = df.loc[mask, "Nama_Pemenang"].map(mapping)

    # ★ ICT Classification — MEGA-REGEX
    df["Sektor"] = _vectorized_ict_fast(df["Nama_Paket"])

    # Wilayah
    df["Provinsi"] = df["Lokasi"].str.split(",").str[0].str.strip().fillna("Lainnya")
    df["Wilayah"] = df["Provinsi"].map(WILAYAH_MAP).fillna("Lainnya")

    # ★ Pre-compute is_pemda column (vectorized, avoids .apply() later)
    inst = df["Instansi_Pembeli"].fillna("").str.strip()
    df["is_pemda"] = (inst.str.startswith("Kab.") |
                      inst.str.startswith("Kota ") |
                      inst.str.startswith("Provinsi "))

    # ★ Convert object columns to category for memory savings
    for col in ["Sektor", "Wilayah", "Provinsi", "Metode_Pemilihan", "Jenis_Pengadaan"]:
        if col in df.columns:
            df[col] = df[col].astype("category")

    # ★ Pre-compute uncensor mapping (one-time fuzzy match)
    uncensor_map = _build_uncensor_mapping(df["Nama_Pemenang"].unique())

    # ★ Save Parquet cache for next reload (<1 sec load)
    try:
        df.to_parquet(parquet_path, index=False, compression="snappy")
    except Exception:
        pass

    return df, total_rows, n_matched, None, uncensor_map


# ═══════════════════════════════════════════════════════════════════════════
# CHART FUNCTIONS
# ═══════════════════════════════════════════════════════════════════════════
def chart_top20(df_agg, title, subtitle, accent_color, semesta=None, figsize=(16, 9),
                val_col="Total_Pagu", name_col="Nama_Pemenang",
                extra_cols=None):
    """Horizontal bar chart Top 20 with rich annotations."""
    sns.set_theme(style="white")
    d = df_agg.head(20).copy().reset_index(drop=True)
    n = len(d)
    if n == 0:
        fig, ax = plt.subplots(figsize=(8, 3))
        ax.text(0.5, 0.5, "Tidak ada data", ha="center", va="center", fontsize=16, color="#999")
        ax.axis("off"); return fig

    fig, ax = plt.subplots(figsize=figsize)
    fig.patch.set_facecolor("#FAFAFA")
    ax.set_facecolor("#FAFAFA")

    base = accent_color.lstrip('#')
    r0, g0, b0 = int(base[:2],16), int(base[2:4],16), int(base[4:6],16)
    palette = []
    for i in range(n):
        f = 1.0 - (i * 0.03)
        palette.append(f"#{max(0,min(255,int(r0*f))):02x}{max(0,min(255,int(g0*f))):02x}{max(0,min(255,int(b0*f))):02x}")

    y_pos = list(range(n-1, -1, -1))
    ax.barh(y_pos, d[val_col], color=palette, height=0.62, edgecolor="white", linewidth=1.2, zorder=3)
    mx = d[val_col].max()

    for i, (_, row) in enumerate(d.iterrows()):
        y = n - 1 - i
        val = row[val_col]
        pct = f"  ({val/semesta*100:.1f}%)" if semesta and semesta > 0 else ""
        line1 = f"{fmt_rp(val)}{pct}"
        parts = []
        if "Jumlah_Paket" in row.index and row["Jumlah_Paket"] > 0:
            parts.append(f"{int(row['Jumlah_Paket'])} paket")
        if "Instansi_Unik" in row.index and row["Instansi_Unik"] > 0:
            parts.append(f"{int(row['Instansi_Unik'])} instansi")
        if "Satker_Unik" in row.index and row["Satker_Unik"] > 0:
            parts.append(f"{int(row['Satker_Unik'])} satker")
        line2 = "  •  ".join(parts)

        ax.text(val + mx*0.008, y + 0.12, line1,
                va="center", ha="left", fontsize=10, fontweight="bold", color="#111")
        if line2:
            ax.text(val + mx*0.008, y - 0.18, line2,
                    va="center", ha="left", fontsize=8.5, fontweight="600", color="#666")

    ax.set_yticks(y_pos)
    ax.set_yticklabels(
        ["\n".join(textwrap.wrap(str(nm), 30)) for nm in d[name_col]],
        fontsize=10.5, fontweight="bold", color="#222")

    ax.set_title(title, fontsize=18, fontweight="bold", color="#111", loc="left", pad=24)
    if subtitle:
        ax.text(0, 1.035, subtitle, transform=ax.transAxes, fontsize=12, color="#777", ha="left")

    if semesta:
        ax.text(1.0, -0.06, f"SEMESTA: {fmt_rp(semesta)}",
                transform=ax.transAxes, fontsize=11, fontweight="bold",
                color="#ED1C24", ha="right", va="top",
                bbox=dict(boxstyle="round,pad=0.3", facecolor="#FFF3F3", edgecolor="#ED1C24", alpha=0.9))

    ax.set_xlabel(""); ax.set_ylabel("")
    ax.tick_params(axis="x", labelsize=9, labelcolor="#AAA")
    ax.xaxis.set_major_formatter(mticker.FuncFormatter(lambda x, _: fmt_s(x)))
    ax.set_xlim(0, mx * 1.58)
    ax.grid(axis="x", alpha=0.08, linestyle="-", zorder=0)
    for sp in ["top","right","left"]: ax.spines[sp].set_visible(False)
    ax.spines["bottom"].set_color("#E0E0E0")
    plt.tight_layout()
    return fig


def chart_donut(val_ict, val_non, cnt_ict, cnt_non, label=""):
    total = val_ict + val_non
    fig, ax = plt.subplots(figsize=(5, 5))
    fig.patch.set_facecolor("#FAFAFA"); ax.set_facecolor("#FAFAFA")
    if total == 0:
        ax.text(0.5, 0.5, "Tidak ada data", ha="center", va="center", fontsize=13, color="#999", transform=ax.transAxes)
        ax.axis("off"); return fig
    pct_ict = val_ict/total*100 if total > 0 else 0
    sizes, colors, labels = [], [], []
    if val_ict > 0:
        sizes.append(val_ict); colors.append("#1B4F72")
        labels.append(f"ICT — {fmt_rp(val_ict)} ({pct_ict:.1f}%) • {fmt_n(cnt_ict)} pemenang")
    if val_non > 0:
        sizes.append(val_non); colors.append("#1E6F3E")
        labels.append(f"Non-ICT — {fmt_rp(val_non)} ({100-pct_ict:.1f}%) • {fmt_n(cnt_non)} pemenang")

    wedges, _, autotexts = ax.pie(
        sizes, colors=colors, autopct=lambda p: f"{p:.1f}%", startangle=90, pctdistance=0.78,
        wedgeprops=dict(width=0.38, edgecolor="white", linewidth=3),
        textprops=dict(color="white", fontsize=12, fontweight="bold"))
    for at in autotexts: at.set_fontsize(13); at.set_fontweight("bold")
    ax.text(0, 0.06, fmt_rp(total), ha="center", va="center", fontsize=14, fontweight="bold", color="#111")
    ax.text(0, -0.10, label, ha="center", va="center", fontsize=9.5, fontweight="bold", color="#444")
    lg = ax.legend(wedges, labels, loc="lower center", bbox_to_anchor=(0.5, -0.10), fontsize=8.5, frameon=False, ncol=1)
    for t in lg.get_texts(): t.set_color("#333")
    ax.set_aspect("equal"); ax.axis("off")
    plt.subplots_adjust(bottom=0.12, top=0.95)
    return fig


def chart_heatmap(df_agg, si_col, seg_col, val_col, title, cmap="Reds"):
    top = df_agg.groupby(si_col)[val_col].sum().sort_values(ascending=False).head(15).index
    h = df_agg[df_agg[si_col].isin(top)].groupby([si_col, seg_col])[val_col].sum().unstack(fill_value=0)
    h["_t"] = h.sum(axis=1)
    h = h.sort_values("_t", ascending=False).drop("_t", axis=1)
    if h.empty: return None
    fig, ax = plt.subplots(figsize=(15, max(7, len(h)*0.48)))
    fig.patch.set_facecolor("#FAFAFA"); ax.set_facecolor("#FAFAFA")
    annot = h.map(lambda x: fmt_s(x) if x > 0 else "")
    sns.heatmap(h, ax=ax, annot=annot, fmt="", cmap=cmap, linewidths=2, linecolor="white",
                cbar_kws={"label":"Nilai (Rp)","shrink":0.5}, annot_kws={"fontsize":9,"fontweight":"bold"})
    ax.set_title(title, fontsize=16, fontweight="bold", color="#111", pad=16)
    ax.set_xlabel(""); ax.set_ylabel("")
    ax.set_yticklabels(["\n".join(textwrap.wrap(t.get_text(), 25)) for t in ax.get_yticklabels()],
                       fontsize=10, fontweight="bold", rotation=0)
    ax.set_xticklabels(ax.get_xticklabels(), fontsize=11, fontweight="bold", rotation=25, ha="right")
    plt.tight_layout()
    return fig


# ═══════════════════════════════════════════════════════════════════════════
# AGGREGATION HELPERS
# ═══════════════════════════════════════════════════════════════════════════
def agg_top_pemenang(df, sektor=None, n=20):
    """Aggregate top N pemenang by total Pagu_Rp."""
    d = df.copy()
    if sektor:
        d = d[d["Sektor"] == sektor]
    if len(d) == 0:
        return pd.DataFrame()
    agg = (d.groupby("Nama_Pemenang")
           .agg(Total_Pagu=("Pagu_Rp", "sum"),
                Jumlah_Paket=("Pagu_Rp", "count"),
                Instansi_Unik=("Instansi_Pembeli", "nunique"),
                Satker_Unik=("Satuan_Kerja", "nunique"))
           .sort_values("Total_Pagu", ascending=False)
           .head(n)
           .reset_index())
    return agg


def agg_top_instansi(df, n=15):
    if len(df) == 0: return pd.DataFrame()
    agg = (df.groupby("Instansi_Pembeli")
           .agg(Total_Pagu=("Pagu_Rp", "sum"),
                Jumlah_Paket=("Pagu_Rp", "count"),
                Pemenang_Unik=("Nama_Pemenang", "nunique"),
                Satker_Unik=("Satuan_Kerja", "nunique"))
           .sort_values("Total_Pagu", ascending=False)
           .head(n)
           .reset_index())
    return agg


def filter_by_tema(df, tema_cfg):
    """Filter by K/L tema keywords — uses pre-compiled patterns + vectorized is_pemda."""
    mask = pd.Series(False, index=df.index)
    for pat in tema_cfg["_re_inst"]:
        mask |= df["Instansi_Pembeli"].str.contains(pat, na=False)
    for pat in tema_cfg["_re_satker"]:
        mask |= df["Satuan_Kerja"].str.contains(pat, na=False)
    return df[mask & ~df["is_pemda"]]


def filter_pemda_wilayah(df, wilayah):
    return df[df["is_pemda"] & (df["Wilayah"] == wilayah)]


def filter_by_dinas(df, dinas_name):
    """Filter by dinas — uses pre-compiled patterns."""
    pat = DINAS_COMPILED.get(dinas_name)
    if not pat: return pd.DataFrame()
    return df[df["Satuan_Kerja"].str.contains(pat, na=False)]


# ═══════════════════════════════════════════════════════════════════════════
# RENDER HELPERS
# ═══════════════════════════════════════════════════════════════════════════
def render_top20_section(df_section, section_name, color, key_prefix, semesta=None,
                         uncensor_map=None):
    """Render Top 20 ICT + Non-ICT + detail cards for a section.
    uncensor_map: dict mapping censored→uncensored names."""
    kp = re.sub(r'[^a-zA-Z0-9]', '', key_prefix)[:20]

    total_pagu = df_section["Pagu_Rp"].sum()
    n_paket = len(df_section)
    n_pemenang = df_section["Nama_Pemenang"].nunique()
    n_inst = df_section["Instansi_Pembeli"].nunique()
    n_satker = df_section["Satuan_Kerja"].nunique()

    ict_df = df_section[df_section["Sektor"]=="ICT"]
    non_df = df_section[df_section["Sektor"]=="Non-ICT"]

    c1,c2,c3,c4,c5 = st.columns(5)
    c1.markdown(kpi("Total Paket", fmt_n(n_paket)), unsafe_allow_html=True)
    c2.markdown(kpi("Total Pagu", fmt_rp(total_pagu)), unsafe_allow_html=True)
    c3.markdown(kpi("Pemenang Unik", fmt_n(n_pemenang), f"ICT: {ict_df['Nama_Pemenang'].nunique()} | Non: {non_df['Nama_Pemenang'].nunique()}"), unsafe_allow_html=True)
    c4.markdown(kpi("Instansi", fmt_n(n_inst)), unsafe_allow_html=True)
    c5.markdown(kpi("Satuan Kerja", fmt_n(n_satker)), unsafe_allow_html=True)

    st.markdown("<div style='height:12px'></div>", unsafe_allow_html=True)

    t_ict, t_non, t_inst, t_detail = st.tabs(
        ["💻 Top 20 ICT", "📦 Top 20 Non-ICT", "🏛️ Top Instansi", "📋 Detail Paket"])

    with t_ict:
        agg_ict = agg_top_pemenang(df_section, "ICT")
        if len(agg_ict) > 0:
            # ★ Fuzzy uncensor for chart display (dict lookup)
            if uncensor_map:
                agg_ict = uncensor_for_chart(agg_ict, uncensor_map)
            sem_ict = ict_df["Pagu_Rp"].sum()
            fig = chart_top20(agg_ict,
                              f"Top {min(20,len(agg_ict))} Pemenang ICT — {section_name}",
                              f"N={fmt_n(len(ict_df))} paket ICT | Total: {fmt_rp(sem_ict)} | Semesta: {fmt_rp(semesta or total_pagu)}",
                              "#1565C0", semesta or total_pagu)
            st.pyplot(fig, use_container_width=True); plt.close(fig)
            st.download_button(f"📥 Excel Top 20 ICT — {section_name}",
                               to_excel_styled(agg_ict, f"ICT_{section_name[:15]}"),
                               f"Top20_ICT_{kp}_{datetime.now():%Y%m%d}.xlsx",
                               "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                               key=f"dlict_{kp}")
            _render_pemenang_expanders(agg_ict, ict_df, f"ict{kp}")
        else:
            st.info("Tidak ada data ICT di segmen ini.")

    with t_non:
        agg_non = agg_top_pemenang(df_section, "Non-ICT")
        if len(agg_non) > 0:
            # ★ Fuzzy uncensor for chart display (dict lookup)
            if uncensor_map:
                agg_non = uncensor_for_chart(agg_non, uncensor_map)
            sem_non = non_df["Pagu_Rp"].sum()
            fig = chart_top20(agg_non,
                              f"Top {min(20,len(agg_non))} Pemenang Non-ICT — {section_name}",
                              f"N={fmt_n(len(non_df))} paket Non-ICT | Total: {fmt_rp(sem_non)} | Semesta: {fmt_rp(semesta or total_pagu)}",
                              "#2E7D32", semesta or total_pagu)
            st.pyplot(fig, use_container_width=True); plt.close(fig)
            st.download_button(f"📥 Excel Top 20 Non-ICT — {section_name}",
                               to_excel_styled(agg_non, f"NonICT_{section_name[:15]}"),
                               f"Top20_NonICT_{kp}_{datetime.now():%Y%m%d}.xlsx",
                               "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                               key=f"dlnon_{kp}")
            _render_pemenang_expanders(agg_non, non_df, f"non{kp}")
        else:
            st.info("Tidak ada data Non-ICT di segmen ini.")

    with t_inst:
        agg_inst = agg_top_instansi(df_section)
        if len(agg_inst) > 0:
            agg_inst_chart = agg_inst.rename(columns={
                "Instansi_Pembeli":"Nama_Pemenang","Pemenang_Unik":"Instansi_Unik"})
            fig = chart_top20(agg_inst_chart,
                              f"Top {min(15,len(agg_inst))} Instansi Pembeli — {section_name}",
                              f"{fmt_n(n_inst)} instansi total",
                              "#E65100", total_pagu, figsize=(15, 7))
            st.pyplot(fig, use_container_width=True); plt.close(fig)
        else:
            st.info("Tidak ada data instansi.")

    with t_detail:
        cols_show = ["Nama_Pemenang","Pagu_Rp","Instansi_Pembeli","Satuan_Kerja",
                     "Lokasi","Metode_Pemilihan","Sektor","Nama_Paket"]
        cols_avail = [c for c in cols_show if c in df_section.columns]
        df_show = df_section[cols_avail].sort_values("Pagu_Rp", ascending=False).head(500)
        df_disp = df_show.copy()
        if "Pagu_Rp" in df_disp.columns:
            df_disp["Pagu_Rp"] = df_disp["Pagu_Rp"].apply(fmt_rp)
        st.dataframe(df_disp, use_container_width=True, hide_index=True, height=400)
        st.download_button(f"📥 Excel Detail — {section_name}",
                           to_excel_styled(df_show.head(2000), f"Detail_{section_name[:15]}"),
                           f"Detail_{kp}_{datetime.now():%Y%m%d}.xlsx",
                           "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                           key=f"dldet_{kp}")


def _render_pemenang_expanders(agg_df, detail_df, key_prefix):
    for idx, (_, row) in enumerate(agg_df.head(20).iterrows()):
        si = row["Nama_Pemenang"]
        dsi = detail_df[detail_df["Nama_Pemenang"] == si]
        n_inst = int(row.get("Instansi_Unik", 0))
        n_satk = int(row.get("Satker_Unik", 0))
        val = row["Total_Pagu"]

        header = f"**#{idx+1} {si}** — {fmt_rp(val)} | {n_inst} instansi • {n_satk} satker • {int(row['Jumlah_Paket'])} paket"
        with st.expander(header, expanded=False):
            if len(dsi) == 0:
                st.caption("Detail tidak tersedia."); continue

            k1, k2, k3, k4 = st.columns(4)
            k1.markdown(kpi("Total Pagu", fmt_rp(dsi["Pagu_Rp"].sum())), unsafe_allow_html=True)
            k2.markdown(kpi("Jumlah Paket", fmt_n(len(dsi))), unsafe_allow_html=True)
            k3.markdown(kpi("Instansi Unik", fmt_n(dsi["Instansi_Pembeli"].nunique())), unsafe_allow_html=True)
            k4.markdown(kpi("Satker Unik", fmt_n(dsi["Satuan_Kerja"].nunique())), unsafe_allow_html=True)

            col_a, col_b = st.columns(2)
            with col_a:
                st.markdown("**🏛️ Instansi Pembeli:**")
                ia = (dsi.groupby("Instansi_Pembeli").agg(Pagu=("Pagu_Rp","sum"), Paket=("Pagu_Rp","count"))
                      .sort_values("Pagu", ascending=False).reset_index())
                ia["Pagu"] = ia["Pagu"].apply(fmt_rp)
                ia.columns = ["Instansi", "Total Pagu", "Paket"]
                st.dataframe(ia, use_container_width=True, hide_index=True, height=200)
            with col_b:
                st.markdown("**🏢 Satuan Kerja (Top 15):**")
                sa = (dsi.groupby("Satuan_Kerja").agg(Pagu=("Pagu_Rp","sum"), Paket=("Pagu_Rp","count"))
                      .sort_values("Pagu", ascending=False).head(15).reset_index())
                sa["Pagu"] = sa["Pagu"].apply(fmt_rp)
                sa.columns = ["Satuan Kerja", "Total Pagu", "Paket"]
                st.dataframe(sa, use_container_width=True, hide_index=True, height=200)

            st.markdown("**📋 Daftar Paket:**")
            cs = ["Nama_Paket","Pagu_Rp","Instansi_Pembeli","Satuan_Kerja","Lokasi"]
            cs = [c for c in cs if c in dsi.columns]
            dp = dsi[cs].sort_values("Pagu_Rp", ascending=False).head(100).copy()
            dp["Pagu_Rp"] = dp["Pagu_Rp"].apply(fmt_rp)
            st.dataframe(dp, use_container_width=True, hide_index=True, height=220)


def render_drilldown_table(df_sub, label, key_prefix):
    kp = re.sub(r'[^a-zA-Z0-9]', '', key_prefix)[:25]
    cols_show = ["Nama_Pemenang","Pagu_Rp","Instansi_Pembeli","Satuan_Kerja",
                 "Lokasi","Metode_Pemilihan","Sektor","Nama_Paket"]
    cols_avail = [c for c in cols_show if c in df_sub.columns]
    df_raw = df_sub[cols_avail].sort_values("Pagu_Rp", ascending=False)

    ci, cn = st.columns(2)
    with ci:
        st.markdown("**💻 Top 20 ICT:**")
        ai = agg_top_pemenang(df_sub, "ICT", 20)
        if len(ai) > 0:
            ai_d = ai.copy(); ai_d["Total_Pagu"] = ai_d["Total_Pagu"].apply(fmt_rp)
            st.dataframe(ai_d, use_container_width=True, hide_index=True)
        else:
            st.caption("Tidak ada pemenang ICT.")
    with cn:
        st.markdown("**📦 Top 20 Non-ICT:**")
        an = agg_top_pemenang(df_sub, "Non-ICT", 20)
        if len(an) > 0:
            an_d = an.copy(); an_d["Total_Pagu"] = an_d["Total_Pagu"].apply(fmt_rp)
            st.dataframe(an_d, use_container_width=True, hide_index=True)
        else:
            st.caption("Tidak ada pemenang Non-ICT.")

    st.markdown(f"**📋 Tabel Lengkap — {label}** ({fmt_n(len(df_raw))} baris)")
    df_disp = df_raw.head(1000).copy()
    df_disp["Pagu_Rp"] = df_disp["Pagu_Rp"].apply(fmt_rp)
    st.dataframe(df_disp, use_container_width=True, hide_index=True, height=350)

    csv_data = df_raw.head(5000).to_csv(index=False).encode("utf-8")
    st.download_button(f"📥 Download CSV — {label}",
                       csv_data,
                       f"{kp}_{datetime.now():%Y%m%d}.csv",
                       "text/csv",
                       key=f"dlcsv_{kp}")
    st.download_button(f"📥 Download Excel — {label}",
                       to_excel_styled(df_raw.head(5000), label[:25]),
                       f"{kp}_{datetime.now():%Y%m%d}.xlsx",
                       "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                       key=f"dlxls_{kp}")


# ═══════════════════════════════════════════════════════════════════════════
# MAIN — LOAD DATA
# ═══════════════════════════════════════════════════════════════════════════
st.markdown("""
<div class="hero">
    <h1>📊 Dashboard Realisasi Pengadaan Pemerintah — INAPROC</h1>
    <p>Data Realisasi KLPD &nbsp;|&nbsp; Telkomsel Enterprise — Bid Management Intelligence</p>
</div>""", unsafe_allow_html=True)

df, total_rows, n_matched, err, UNCENSOR_MAP = load_and_process()
if err:
    st.error(f"⚠️ {err}\n\nLetakkan `{DB_NAME}` di folder yang sama dengan `app.py`.")
    st.stop()

# ═══════════════════════════════════════════════════════════════════════════
# SIDEBAR
# ═══════════════════════════════════════════════════════════════════════════
with st.sidebar:
    st.markdown("<div style='text-align:center;padding:8px 0'>"
                "<span style='font-size:24px'>📊</span><br>"
                "<span style='font-size:16px;font-weight:800;color:#FFF!important'>INAPROC INTELLIGENCE</span><br>"
                "<span style='font-size:10px;color:#AAA!important'>Telkomsel Enterprise</span></div>",
                unsafe_allow_html=True)
    st.markdown("---")
    st.success(f"✅ {fmt_n(len(df))} paket loaded (dari {fmt_n(total_rows)})")
    st.info(f"🔓 {fmt_n(n_matched)} vendor-mapping | {fmt_n(len(UNCENSOR_MAP))} chart-uncensor")

    # ★ Show parquet cache status
    pq = _get_parquet_path()
    if os.path.exists(pq):
        pq_mb = os.path.getsize(pq) / 1e6
        st.caption(f"⚡ Cache aktif ({pq_mb:.0f} MB)")
    
    st.markdown("---")
    view = st.radio("📌 Tampilan",
                    ["🏠 Overview",
                     "🏛️ Per K/L (7 Tema)",
                     "🗺️ Per Wilayah & Dinas",
                     "📋 Detail Explorer"], index=0)
    st.markdown("---")
    sektor_filter = st.radio("🔍 Sektor", ["Semua","ICT","Non-ICT"], index=0)
    st.markdown("---")

    # ★ Cache management
    if os.path.exists(pq):
        if st.button("🗑️ Hapus Cache", use_container_width=True, help="Rebuild dari SQLite"):
            os.remove(pq)
            st.cache_data.clear()
            st.rerun()

    if st.button("🚪 Logout", use_container_width=True):
        st.session_state["authenticated"] = False
        st.rerun()
    st.caption(f"Telkomsel Enterprise\n{datetime.now():%d %B %Y}")

# Apply sektor filter (no full .copy() — use view when possible)
if sektor_filter != "Semua":
    dff = df[df["Sektor"] == sektor_filter]
else:
    dff = df


# ═══════════════════════════════════════════════════════════════════════════
# VIEW: OVERVIEW
# ═══════════════════════════════════════════════════════════════════════════
if "Overview" in view:
    st.markdown('<div class="sec"><h2>📌 Ringkasan Eksekutif</h2>'
                '<p>Seluruh data realisasi pengadaan pemerintah — pemenang, instansi, dan wilayah</p></div>',
                unsafe_allow_html=True)

    total_pagu = dff["Pagu_Rp"].sum()
    total_realisasi = dff["Total_Pelaksanaan_Rp"].sum()
    n_paket = len(dff)
    n_pemenang = dff["Nama_Pemenang"].nunique()
    n_inst = dff["Instansi_Pembeli"].nunique()
    n_satker = dff["Satuan_Kerja"].nunique()
    n_ict = len(dff[dff["Sektor"]=="ICT"])
    n_non = len(dff[dff["Sektor"]=="Non-ICT"])

    c1,c2,c3,c4,c5,c6 = st.columns(6)
    c1.markdown(kpi("Total Paket", fmt_n(n_paket), f"ICT: {fmt_n(n_ict)} | Non: {fmt_n(n_non)}"), unsafe_allow_html=True)
    c2.markdown(kpi("Total Pagu", fmt_rp(total_pagu)), unsafe_allow_html=True)
    c3.markdown(kpi("Total Realisasi", fmt_rp(total_realisasi)), unsafe_allow_html=True)
    c4.markdown(kpi("Pemenang Unik", fmt_n(n_pemenang)), unsafe_allow_html=True)
    c5.markdown(kpi("Instansi Pembeli", fmt_n(n_inst)), unsafe_allow_html=True)
    c6.markdown(kpi("Satuan Kerja", fmt_n(n_satker)), unsafe_allow_html=True)

    st.markdown("<div style='height:16px'></div>", unsafe_allow_html=True)

    # Grand Top 20
    st.markdown('<div class="sec"><h2>🏆 Grand Top 20 Pemenang</h2>'
                '<p>Berdasarkan total Pagu Rp — dengan info instansi & satuan kerja</p></div>',
                unsafe_allow_html=True)
    grand = agg_top_pemenang(dff)
    if len(grand) > 0:
        # ★ Fuzzy uncensor for chart (dict lookup)
        grand = uncensor_for_chart(grand, UNCENSOR_MAP)
        fig = chart_top20(grand, "Grand Top 20 Pemenang — Semua Segmen",
                          f"{fmt_n(n_pemenang)} pemenang unik • {fmt_n(n_inst)} instansi • {fmt_n(n_satker)} satker",
                          "#ED1C24", total_pagu)
        st.pyplot(fig, use_container_width=True); plt.close(fig)
        st.download_button("📥 Download Excel — Grand Top 20",
                           to_excel_styled(grand, "Grand_Top20"),
                           f"Grand_Top20_{datetime.now():%Y%m%d}.xlsx",
                           "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                           key="dl_grand")
        _render_pemenang_expanders(grand, dff, "grand")

    # ICT vs Non-ICT per Wilayah
    st.markdown("<div style='height:20px'></div>", unsafe_allow_html=True)
    st.markdown('<div class="sec"><h2>🗺️ ICT vs Non-ICT per Wilayah</h2></div>', unsafe_allow_html=True)
    cols = st.columns(3)
    for i, w in enumerate(WILAYAH_LIST):
        cf = W_CFG[w]
        dw = dff[dff["Wilayah"] == w]
        with cols[i % 3]:
            rv = dw["Pagu_Rp"].sum()
            ni = dw["Instansi_Pembeli"].nunique()
            ns = dw["Satuan_Kerja"].nunique()
            np_ = dw["Nama_Pemenang"].nunique()
            st.markdown(f"""
            <div class="rcard" style="background:{cf['bg']};border-color:{cf['c']}">
                <h3 style="color:{cf['c']}!important">{cf['i']} {w}</h3>
                <p><strong>{fmt_rp(rv)}</strong> | {fmt_n(len(dw))} paket | {fmt_n(np_)} pemenang | {fmt_n(ni)} instansi</p>
            </div>""", unsafe_allow_html=True)

            dw_ict = dw[dw["Sektor"]=="ICT"]
            dw_non = dw[dw["Sektor"]=="Non-ICT"]
            fig = chart_donut(dw_ict["Pagu_Rp"].sum(), dw_non["Pagu_Rp"].sum(),
                              dw_ict["Nama_Pemenang"].nunique(), dw_non["Nama_Pemenang"].nunique(), w)
            st.pyplot(fig, use_container_width=True); plt.close(fig)

    # Heatmap
    st.markdown("<div style='height:20px'></div>", unsafe_allow_html=True)
    st.markdown('<div class="sec"><h2>🔥 Heatmap: Top Pemenang × Wilayah</h2></div>', unsafe_allow_html=True)
    df_wil = dff[dff["Wilayah"].isin(WILAYAH_LIST)]
    if len(df_wil) > 0:
        hm_agg = df_wil.groupby(["Nama_Pemenang","Wilayah"])["Pagu_Rp"].sum().reset_index()
        fig = chart_heatmap(hm_agg, "Nama_Pemenang", "Wilayah", "Pagu_Rp",
                            "Top 15 Pemenang × Wilayah — Nilai Pagu", "Reds")
        if fig: st.pyplot(fig, use_container_width=True); plt.close(fig)


# ═══════════════════════════════════════════════════════════════════════════
# VIEW: PER K/L (7 TEMA)
# ═══════════════════════════════════════════════════════════════════════════
elif "K/L" in view:
    st.markdown('<div class="sec-b"><h2>🏛️ Top 20 Pemenang per Kementerian/Lembaga</h2>'
                '<p>7 Tema Strategis — hanya Kementerian & Lembaga (exclude Pemda)</p></div>',
                unsafe_allow_html=True)

    tema_names = list(TEMA_KL.keys())
    tabs = st.tabs(tema_names)

    for tab, tema_name in zip(tabs, tema_names):
        with tab:
            cfg = TEMA_KL[tema_name]
            df_tema = filter_by_tema(dff, cfg)
            n_t = len(df_tema)

            st.markdown(f"""
            <div class="rcard" style="background:#FAFAFA;border-color:{cfg['color']}">
                <h3 style="color:{cfg['color']}!important">{cfg['icon']} {tema_name}</h3>
                <p>{cfg['desc']} | <strong>{fmt_n(n_t)} paket</strong> | <strong>{fmt_rp(df_tema['Pagu_Rp'].sum())}</strong></p>
            </div>""", unsafe_allow_html=True)

            if n_t == 0:
                st.warning("Tidak ada data matching untuk tema ini.")
                continue

            tema_kp = re.sub(r'[^a-zA-Z0-9]', '', tema_name)[:10]
            render_top20_section(df_tema, tema_name, cfg["color"], f"kl{tema_kp}",
                                semesta=dff["Pagu_Rp"].sum(),
                                uncensor_map=UNCENSOR_MAP)

            st.markdown(f"<div style='height:16px'></div>", unsafe_allow_html=True)
            st.markdown(f"**🔎 Drill-down per Instansi Pembeli — {tema_name}**")
            inst_list = df_tema["Instansi_Pembeli"].value_counts().head(20).index.tolist()
            if inst_list:
                sel_inst = st.selectbox(f"Pilih Instansi ({tema_name})", inst_list,
                                        key=f"selinst_{tema_kp}")
                if sel_inst:
                    df_inst = df_tema[df_tema["Instansi_Pembeli"] == sel_inst]
                    st.markdown(f"**{sel_inst}** — {fmt_n(len(df_inst))} paket | {fmt_rp(df_inst['Pagu_Rp'].sum())}")
                    inst_kp = re.sub(r'[^a-zA-Z0-9]', '', sel_inst)[:10]
                    render_drilldown_table(df_inst, sel_inst, f"kldrill{tema_kp}{inst_kp}")


# ═══════════════════════════════════════════════════════════════════════════
# VIEW: PER WILAYAH & DINAS
# ═══════════════════════════════════════════════════════════════════════════
elif "Wilayah" in view:
    st.markdown('<div class="sec"><h2>🗺️ Top 20 Pemenang per Wilayah & Dinas Strategis</h2>'
                '<p>Hanya Pemda (Kab/Kota/Provinsi) — filter berdasarkan Instansi Pembeli</p></div>',
                unsafe_allow_html=True)

    sub_view = st.radio("Pilih tampilan:", ["📍 Per Wilayah","📡 DISKOMINFO se-Indonesia","🏢 Per Dinas Strategis"],
                        horizontal=True, key="wil_subview")

    if sub_view == "📍 Per Wilayah":
        # ★ Pre-compute pemda data per wilayah (avoid repeated filtering)
        pemda_by_wil = {w: filter_pemda_wilayah(dff, w) for w in WILAYAH_LIST}
        wdata = [w for w in WILAYAH_LIST if len(pemda_by_wil[w]) > 0]
        # ★ Compute semesta once outside the loop
        sem_all = sum(pemda_by_wil[w]["Pagu_Rp"].sum() for w in WILAYAH_LIST)
        if not wdata:
            st.warning("Tidak ada data Pemda.")
        else:
            tabs = st.tabs([f"{W_CFG[w]['i']} {w}" for w in wdata])
            for tab, w in zip(tabs, wdata):
                with tab:
                    cf = W_CFG[w]
                    dw = pemda_by_wil[w]
                    w_kp = re.sub(r'[^a-zA-Z0-9]', '', w)[:8]
                    st.markdown(f"""
                    <div class="rcard" style="background:{cf['bg']};border-color:{cf['c']}">
                        <h3 style="color:{cf['c']}!important">{cf['i']} Wilayah {w}</h3>
                        <p>{fmt_n(len(dw))} paket | {fmt_rp(dw['Pagu_Rp'].sum())} |
                        {fmt_n(dw['Nama_Pemenang'].nunique())} pemenang | {fmt_n(dw['Instansi_Pembeli'].nunique())} instansi Pemda</p>
                    </div>""", unsafe_allow_html=True)
                    render_top20_section(dw, f"Wilayah {w}", cf["c"], f"wil{w_kp}", semesta=sem_all,
                                        uncensor_map=UNCENSOR_MAP)

                    st.markdown(f"**🔎 Drill-down per Instansi Pembeli — {w}:**")
                    inst_list = dw["Instansi_Pembeli"].value_counts().head(25).index.tolist()
                    if inst_list:
                        sel = st.selectbox("Pilih Instansi Pemda", inst_list, key=f"selwil{w_kp}")
                        if sel:
                            df_sel = dw[dw["Instansi_Pembeli"] == sel]
                            st.markdown(f"**{sel}** — {fmt_n(len(df_sel))} paket | {fmt_rp(df_sel['Pagu_Rp'].sum())}")
                            sel_kp = re.sub(r'[^a-zA-Z0-9]', '', sel)[:10]
                            render_drilldown_table(df_sel, sel, f"wildrill{w_kp}{sel_kp}")

    elif sub_view == "📡 DISKOMINFO se-Indonesia":
        st.markdown('<div class="sec-b"><h2>📡 DISKOMINFO se-Indonesia</h2>'
                    '<p>Satuan kerja Diskominfo/Komunikasi — hanya Pemda (Kab/Kota/Provinsi)</p></div>',
                    unsafe_allow_html=True)

        df_dkom = filter_by_dinas(dff, "Diskominfo")
        df_dkom = df_dkom[df_dkom["is_pemda"]]

        if len(df_dkom) == 0:
            st.warning("Tidak ada data DISKOMINFO Pemda.")
        else:
            c1,c2,c3,c4 = st.columns(4)
            c1.markdown(kpi("Paket", fmt_n(len(df_dkom))), unsafe_allow_html=True)
            c2.markdown(kpi("Total Pagu", fmt_rp(df_dkom["Pagu_Rp"].sum())), unsafe_allow_html=True)
            c3.markdown(kpi("Instansi Pemda", fmt_n(df_dkom["Instansi_Pembeli"].nunique())), unsafe_allow_html=True)
            c4.markdown(kpi("Pemenang", fmt_n(df_dkom["Nama_Pemenang"].nunique())), unsafe_allow_html=True)

            render_top20_section(df_dkom, "DISKOMINFO se-Indonesia", "#7B1FA2", "dkom",
                                semesta=dff["Pagu_Rp"].sum(),
                                uncensor_map=UNCENSOR_MAP)

            st.markdown("<div style='height:16px'></div>", unsafe_allow_html=True)
            st.markdown("**🔎 Drill-down per Instansi Pembeli (Diskominfo):**")
            dkom_inst = df_dkom["Instansi_Pembeli"].value_counts().head(30)
            sel_dkom = st.selectbox("Pilih Instansi Pemda", dkom_inst.index.tolist(), key="seldkominst")
            if sel_dkom:
                df_sel = df_dkom[df_dkom["Instansi_Pembeli"] == sel_dkom]
                st.markdown(f"**{sel_dkom}** — {fmt_n(len(df_sel))} paket | {fmt_rp(df_sel['Pagu_Rp'].sum())}")
                dkom_kp = re.sub(r'[^a-zA-Z0-9]', '', sel_dkom)[:12]
                render_drilldown_table(df_sel, sel_dkom, f"dkomdrill{dkom_kp}")

    elif sub_view == "🏢 Per Dinas Strategis":
        st.markdown('<div class="sec"><h2>🏢 Per Dinas Strategis per Wilayah</h2>'
                    '<p>Pilih wilayah → pilih dinas → lihat pemenang per instansi Pemda</p></div>',
                    unsafe_allow_html=True)

        sel_w = st.selectbox("Pilih Wilayah:", WILAYAH_LIST, key="seldinaswil")
        cf = W_CFG[sel_w]
        ws = WILAYAH_STRATEGY[sel_w]
        dw = filter_pemda_wilayah(dff, sel_w)
        w_kp = re.sub(r'[^a-zA-Z0-9]', '', sel_w)[:8]

        if len(dw) == 0:
            st.warning(f"Tidak ada data Pemda di {sel_w}.")
        else:
            dinas_tabs = st.tabs([f"🏢 {d}" for d in ws["dinas"]])
            for d_idx, (dtab, dinas_name) in enumerate(zip(dinas_tabs, ws["dinas"])):
                with dtab:
                    df_dinas = filter_by_dinas(dw, dinas_name)
                    d_kp = re.sub(r'[^a-zA-Z0-9]', '', dinas_name)[:8]
                    unique_kp = f"ds{d_idx}{d_kp}{w_kp}"

                    if len(df_dinas) == 0:
                        st.info(f"Tidak ada data {dinas_name} di {sel_w}.")
                        continue

                    st.markdown(f"""
                    <div class="rcard" style="background:{cf['bg']};border-color:{cf['c']}">
                        <h3 style="color:{cf['c']}!important">{dinas_name} — {sel_w}</h3>
                        <p>{fmt_n(len(df_dinas))} paket | {fmt_rp(df_dinas['Pagu_Rp'].sum())} |
                        {fmt_n(df_dinas['Nama_Pemenang'].nunique())} pemenang | {fmt_n(df_dinas['Instansi_Pembeli'].nunique())} instansi</p>
                    </div>""", unsafe_allow_html=True)

                    render_top20_section(df_dinas, f"{dinas_name} {sel_w}", cf["c"],
                                        unique_kp, semesta=dw["Pagu_Rp"].sum(),
                                        uncensor_map=UNCENSOR_MAP)

                    st.markdown(f"**🔎 Per Instansi Pembeli ({dinas_name} — {sel_w}):**")
                    inst_list = df_dinas["Instansi_Pembeli"].value_counts().head(20).index.tolist()
                    if inst_list:
                        sel = st.selectbox("Pilih Instansi", inst_list, key=f"sel{unique_kp}")
                        if sel:
                            df_si = df_dinas[df_dinas["Instansi_Pembeli"] == sel]
                            st.markdown(f"**{sel}** — {fmt_n(len(df_si))} paket | {fmt_rp(df_si['Pagu_Rp'].sum())}")
                            si_kp = re.sub(r'[^a-zA-Z0-9]', '', sel)[:10]
                            render_drilldown_table(df_si, sel, f"dsdrill{unique_kp}{si_kp}")


# ═══════════════════════════════════════════════════════════════════════════
# VIEW: DETAIL EXPLORER
# ═══════════════════════════════════════════════════════════════════════════
elif "Detail" in view:
    st.markdown('<div class="sec"><h2>📋 Detail Explorer</h2>'
                '<p>Cari & filter data mentah — pemenang, instansi, wilayah, sektor</p></div>',
                unsafe_allow_html=True)

    c1, c2, c3, c4 = st.columns(4)
    with c1:
        search_pem = st.text_input("🔍 Nama Pemenang", key="search_pem", placeholder="Ketik nama vendor...")
    with c2:
        search_inst = st.text_input("🏛️ Instansi", key="search_inst", placeholder="Ketik instansi...")
    with c3:
        sel_wil = st.selectbox("🗺️ Wilayah", ["Semua"] + WILAYAH_LIST, key="exp_wil")
    with c4:
        sel_sek = st.selectbox("🔍 Sektor", ["Semua","ICT","Non-ICT"], key="exp_sek")

    df_exp = dff.copy()
    if search_pem:
        df_exp = df_exp[df_exp["Nama_Pemenang"].str.contains(search_pem, case=False, na=False)]
    if search_inst:
        df_exp = df_exp[df_exp["Instansi_Pembeli"].str.contains(search_inst, case=False, na=False)]
    if sel_wil != "Semua":
        df_exp = df_exp[df_exp["Wilayah"] == sel_wil]
    if sel_sek != "Semua":
        df_exp = df_exp[df_exp["Sektor"] == sel_sek]

    st.markdown(f"**Hasil:** {fmt_n(len(df_exp))} paket | {fmt_rp(df_exp['Pagu_Rp'].sum())} | "
                f"{fmt_n(df_exp['Nama_Pemenang'].nunique())} pemenang unik")

    if len(df_exp) > 0:
        agg_exp = agg_top_pemenang(df_exp, n=20)
        if len(agg_exp) > 0:
            # ★ Fuzzy uncensor (dict lookup)
            agg_exp = uncensor_for_chart(agg_exp, UNCENSOR_MAP)
            fig = chart_top20(agg_exp,
                              f"Top 20 Pemenang — Hasil Filter",
                              f"N={fmt_n(len(df_exp))} paket | Total: {fmt_rp(df_exp['Pagu_Rp'].sum())}",
                              "#ED1C24", df_exp["Pagu_Rp"].sum())
            st.pyplot(fig, use_container_width=True); plt.close(fig)

        st.markdown("**📊 Data Mentah (max 1.000 baris):**")
        cols_show = ["Nama_Pemenang","Pagu_Rp","Instansi_Pembeli","Satuan_Kerja",
                     "Lokasi","Wilayah","Sektor","Metode_Pemilihan","Jenis_Pengadaan","Nama_Paket"]
        cols_avail = [c for c in cols_show if c in df_exp.columns]
        df_disp = df_exp[cols_avail].sort_values("Pagu_Rp", ascending=False).head(1000).copy()
        df_disp_fmt = df_disp.copy()
        df_disp_fmt["Pagu_Rp"] = df_disp_fmt["Pagu_Rp"].apply(fmt_rp)
        st.dataframe(df_disp_fmt, use_container_width=True, hide_index=True, height=500)

        st.download_button("📥 Download Excel — Hasil Filter (max 5.000)",
                           to_excel_styled(df_exp[cols_avail].sort_values("Pagu_Rp", ascending=False).head(5000),
                                           "Explorer"),
                           f"Explorer_{datetime.now():%Y%m%d}.xlsx",
                           "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                           key="dl_explorer")
    else:
        st.info("Tidak ada data yang cocok dengan filter.")


# ═══════════════════════════════════════════════════════════════════════════
# FOOTER
# ═══════════════════════════════════════════════════════════════════════════
st.markdown("---")
st.markdown(f"""
<div style="text-align:center;padding:24px 0;color:#BBB!important;font-size:11px;">
    Dashboard Realisasi Pengadaan Pemerintah — INAPROC<br>
    Telkomsel Enterprise | Bid Management — Data Science | {datetime.now():%Y}<br>
    <span style="font-size:10px;">🔓 {fmt_n(n_matched)} vendor-mapping | {fmt_n(len(UNCENSOR_MAP))} chart fuzzy-uncensor<br>
    📊 {fmt_n(len(df))} paket dari {fmt_n(total_rows)} total records | Database: {DB_NAME}</span>
</div>""", unsafe_allow_html=True)