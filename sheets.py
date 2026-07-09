import os
import json
import gspread
from datetime import datetime
from google.oauth2.service_account import Credentials

SPREADSHEET_ID = os.environ.get("SPREADSHEET_ID")
GOOGLE_CREDENTIALS_JSON = os.environ.get("GOOGLE_CREDENTIALS_JSON")  # isi JSON service account sebagai string

SCOPES = [
    "https://www.googleapis.com/auth/spreadsheets",
    "https://www.googleapis.com/auth/drive"
]

HEADER = ["Tanggal", "Jam", "Nama Item", "Harga", "Kategori", "Teks Asli"]


def get_client():
    creds_dict = json.loads(GOOGLE_CREDENTIALS_JSON)
    creds = Credentials.from_service_account_info(creds_dict, scopes=SCOPES)
    return gspread.authorize(creds)


def get_or_create_sheet(gc, nama_sheet: str):
    """Ambil sheet berdasarkan nama, buat baru jika belum ada"""
    try:
        spreadsheet = gc.open_by_key(SPREADSHEET_ID)
    except Exception:
        raise Exception("Spreadsheet tidak ditemukan. Cek SPREADSHEET_ID kamu.")

    try:
        sheet = spreadsheet.worksheet(nama_sheet)
    except gspread.WorksheetNotFound:
        sheet = spreadsheet.add_worksheet(title=nama_sheet, rows=1000, cols=10)
        sheet.append_row(HEADER)
    
    # Pastikan header ada
    existing = sheet.row_values(1)
    if existing != HEADER:
        sheet.insert_row(HEADER, 1)
    
    return sheet


async def simpan_pengeluaran(data: dict):
    """Simpan satu baris pengeluaran ke Google Sheets"""
    gc = get_client()
    
    # Sheet per bulan: format "2025-01", "2025-02", dst
    bulan = datetime.now().strftime("%Y-%m")
    sheet = get_or_create_sheet(gc, bulan)
    
    row = [
        data["tanggal"],
        data["jam"],
        data["nama"],
        data["harga"],
        data["kategori"],
        data.get("teks_asli", "")
    ]
    sheet.append_row(row)


async def get_rekap_hari_ini() -> str:
    """Ambil semua pengeluaran hari ini dan format jadi pesan"""
    gc = get_client()
    bulan = datetime.now().strftime("%Y-%m")
    hari_ini = datetime.now().strftime("%Y-%m-%d")

    try:
        sheet = get_or_create_sheet(gc, bulan)
        semua = sheet.get_all_records()
    except Exception:
        return "❌ Gagal mengambil data dari Google Sheets."

    hari_data = [r for r in semua if r.get("Tanggal") == hari_ini]

    if not hari_data:
        return f"📭 Belum ada pengeluaran hari ini ({hari_ini})."

    total = sum(r["Harga"] for r in hari_data)
    
    # Kelompokkan per kategori
    per_kategori = {}
    for r in hari_data:
        kat = r["Kategori"]
        if kat not in per_kategori:
            per_kategori[kat] = []
        per_kategori[kat].append(r)

    lines = [f"📋 *Rekap Pengeluaran {hari_ini}*\n"]
    
    for kat, items in per_kategori.items():
        subtotal = sum(i["Harga"] for i in items)
        lines.append(f"\n*{kat}* (Rp {subtotal:,})")
        for item in items:
            lines.append(f"  • {item['Jam']} — {item['Nama Item']} : Rp {item['Harga']:,}")
    
    lines.append(f"\n{'─'*30}")
    lines.append(f"💰 *Total Hari Ini: Rp {total:,}*")

    return "\n".join(lines)


async def get_rekap_bulan() -> str:
    """Ambil rekap seluruh bulan ini per kategori"""
    gc = get_client()
    bulan = datetime.now().strftime("%Y-%m")
    nama_bulan = datetime.now().strftime("%B %Y")

    try:
        sheet = get_or_create_sheet(gc, bulan)
        semua = sheet.get_all_records()
    except Exception:
        return "❌ Gagal mengambil data dari Google Sheets."

    if not semua:
        return f"📭 Belum ada pengeluaran bulan {nama_bulan}."

    total = sum(r["Harga"] for r in semua)
    
    # Kelompokkan per kategori
    per_kategori = {}
    for r in semua:
        kat = r["Kategori"]
        if kat not in per_kategori:
            per_kategori[kat] = {"total": 0, "count": 0}
        per_kategori[kat]["total"] += r["Harga"]
        per_kategori[kat]["count"] += 1

    # Urutkan dari terbesar
    per_kategori = dict(sorted(per_kategori.items(), key=lambda x: x[1]["total"], reverse=True))

    lines = [f"📊 *Rekap Bulan {nama_bulan}*\n"]
    for kat, info in per_kategori.items():
        persen = (info["total"] / total * 100) if total > 0 else 0
        lines.append(f"*{kat}*: Rp {info['total']:,} ({persen:.1f}%) — {info['count']} transaksi")
    
    lines.append(f"\n{'─'*30}")
    lines.append(f"💰 *Total Bulan Ini: Rp {total:,}*")
    lines.append(f"📝 *Total Transaksi: {len(semua)}*")

    return "\n".join(lines)


async def get_semua_data_bulan() -> list:
    """Ambil semua data bulan ini (untuk export Excel)"""
    gc = get_client()
    bulan = datetime.now().strftime("%Y-%m")

    try:
        sheet = get_or_create_sheet(gc, bulan)
        return sheet.get_all_records()
    except Exception:
        return []
