import os
import json
import re
from datetime import datetime
from groq import AsyncGroq

GROQ_API_KEY = os.environ.get("GROQ_API_KEY")
client = AsyncGroq(api_key=GROQ_API_KEY)

KATEGORI_LIST = [
    "Makanan",
    "Minuman",
    "Transport",
    "Kuota/Internet",
    "Kesehatan",
    "Belanja",
    "Hiburan",
    "Tagihan",
    "Lainnya"
]

SYSTEM_PROMPT = f"""Kamu adalah asisten pencatat pengeluaran. 
Tugasmu adalah mengekstrak informasi pengeluaran dari teks bahasa Indonesia yang informal.

Kamu HARUS merespons HANYA dengan JSON valid, tanpa penjelasan apapun.

Format JSON yang harus kamu kembalikan:
{{
  "nama": "nama item yang dibeli (kapital di awal)",
  "harga": angka integer (dalam rupiah, tanpa titik/koma),
  "kategori": "salah satu dari kategori berikut"
}}

Daftar kategori yang tersedia:
{json.dumps(KATEGORI_LIST, ensure_ascii=False)}

Aturan konversi harga:
- "15k" atau "15rb" atau "15ribu" = 15000
- "50rb" atau "50k" = 50000
- "1.5k" = 1500
- "2.5jt" atau "2.5 juta" = 2500000
- Angka tanpa satuan = rupiah langsung

Contoh input → output:
- "mie ayam 15k" → {{"nama": "Mie Ayam", "harga": 15000, "kategori": "Makanan"}}
- "bensin 50rb" → {{"nama": "Bensin", "harga": 50000, "kategori": "Transport"}}
- "kopi susu 18000" → {{"nama": "Kopi Susu", "harga": 18000, "kategori": "Minuman"}}
- "paket data 3 hari 10k" → {{"nama": "Paket Data 3 Hari", "harga": 10000, "kategori": "Kuota/Internet"}}
- "obat batuk 25rb" → {{"nama": "Obat Batuk", "harga": 25000, "kategori": "Kesehatan"}}

Jika tidak bisa dikenali sebagai pengeluaran, kembalikan: {{"error": "tidak dikenali"}}
"""


def parse_harga_manual(teks: str) -> int | None:
    """Fallback parser harga jika AI gagal"""
    teks = teks.lower().replace('.', '').replace(',', '')
    
    patterns = [
        (r'(\d+(?:\.\d+)?)\s*jt', lambda m: int(float(m.group(1)) * 1_000_000)),
        (r'(\d+(?:\.\d+)?)\s*(?:rb|ribu|k)', lambda m: int(float(m.group(1)) * 1_000)),
        (r'(\d+)', lambda m: int(m.group(1))),
    ]
    
    for pattern, converter in patterns:
        match = re.search(pattern, teks)
        if match:
            return converter(match)
    return None


async def parse_pengeluaran(teks: str) -> dict | None:
    """Parse teks pengeluaran menggunakan Groq AI"""
    try:
        response = await client.chat.completions.create(
            model="llama-3.1-8b-instant",
            messages=[
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": teks}
            ],
            temperature=0.1,
            max_tokens=200,
        )

        raw = response.choices[0].message.content.strip()
        
        # Bersihkan jika ada markdown code block
        raw = re.sub(r'```(?:json)?', '', raw).strip()
        
        hasil = json.loads(raw)
        
        if "error" in hasil:
            return None
        
        # Validasi field
        if not all(k in hasil for k in ["nama", "harga", "kategori"]):
            return None
        
        # Pastikan kategori valid
        if hasil["kategori"] not in KATEGORI_LIST:
            hasil["kategori"] = "Lainnya"
        
        # Tambah tanggal & waktu sekarang
        now = datetime.now()
        hasil["tanggal"] = now.strftime("%Y-%m-%d")
        hasil["jam"] = now.strftime("%H:%M")
        hasil["teks_asli"] = teks
        
        return hasil

    except (json.JSONDecodeError, KeyError, Exception) as e:
        # Fallback: coba parse manual
        harga = parse_harga_manual(teks)
        if harga:
            return {
                "nama": teks.title(),
                "harga": harga,
                "kategori": "Lainnya",
                "tanggal": datetime.now().strftime("%Y-%m-%d"),
                "jam": datetime.now().strftime("%H:%M"),
                "teks_asli": teks
            }
        return None
