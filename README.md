# 🤖 Bot Catatan Pengeluaran Harian

Bot Telegram untuk mencatat pengeluaran harian dengan AI parser otomatis.

## Fitur
- ✅ Ketik bebas → AI parse otomatis (nama, harga, kategori)
- ✅ Konfirmasi sebelum disimpan
- ✅ Rekap harian otomatis jam 21:00 WIB
- ✅ Rekap bulanan + file Excel otomatis tiap tanggal 1
- ✅ Command `/hari`, `/bulan`, `/export`
- ✅ Data tersimpan di Google Sheets (bisa dibuka manual)

---

## SETUP LENGKAP

### 1. Buat Telegram Bot
1. Buka Telegram → cari `@BotFather`
2. Kirim `/newbot`
3. Isi nama & username bot
4. **Simpan TOKEN**

### 2. Cari ID Telegram kamu
1. Buka Telegram → cari `@userinfobot`
2. Kirim `/start`
3. **Simpan ID angka kamu** (misal: `123456789`)

### 3. Daftar Groq API (gratis)
1. Buka https://console.groq.com
2. Daftar dengan Google
3. Klik API Keys → Create API Key
4. **Simpan API Key**

### 4. Setup Google Sheets
1. Buka https://console.cloud.google.com
2. Buat project baru (nama bebas)
3. Cari & aktifkan **Google Sheets API**
4. Cari & aktifkan **Google Drive API**
5. Klik **IAM & Admin** → **Service Accounts** → **Create Service Account**
6. Isi nama (bebas) → Create → Done
7. Klik service account yang baru dibuat
8. Tab **Keys** → Add Key → Create New Key → **JSON** → Download
9. **Buka file JSON** → copy semua isinya
10. Buat Google Sheets baru di drive.google.com
11. **Share** spreadsheet ke email service account (ada di JSON, field `client_email`)
    - Beri akses **Editor**
12. **Salin Spreadsheet ID** dari URL:
    - `https://docs.google.com/spreadsheets/d/INI_SPREADSHEET_ID/edit`

### 5. Deploy ke Railway (gratis)

#### A. Siapkan GitHub
```bash
git init
git add .
git commit -m "first commit"
# Buat repo di github.com lalu:
git remote add origin https://github.com/USERNAME/nama-repo.git
git push -u origin main
```

#### B. Deploy di Railway
1. Buka https://railway.app → Login dengan GitHub
2. **New Project** → **Deploy from GitHub repo**
3. Pilih repo yang baru dibuat
4. Klik **Variables** → tambahkan semua env berikut:

| Variable | Value |
|---|---|
| `TELEGRAM_TOKEN` | Token dari BotFather |
| `ALLOWED_USER_ID` | ID Telegram kamu |
| `GROQ_API_KEY` | API Key dari Groq |
| `SPREADSHEET_ID` | ID Spreadsheet Google |
| `GOOGLE_CREDENTIALS_JSON` | Paste isi file JSON service account (satu baris) |

5. Railway otomatis deploy → bot langsung jalan!

---

## CARA PAKAI

### Catat Pengeluaran
Cukup ketik di chat bot:
```
mie ayam 15k
bensin 50rb
kopi susu 18000
paket data 3 hari 10k
obat batuk 25rb
```

Bot akan konfirmasi dulu sebelum menyimpan.

### Command
| Command | Fungsi |
|---|---|
| `/start` | Tampilkan panduan |
| `/hari` | Rekap pengeluaran hari ini |
| `/bulan` | Rekap pengeluaran bulan ini (per kategori) |
| `/export` | Download file Excel bulan ini |

### Notifikasi Otomatis
- **Jam 21:00 WIB** → Bot kirim ringkasan pengeluaran hari itu
- **Tanggal 1 tiap bulan jam 07:00** → Bot kirim file Excel rekap bulan lalu

---

## Kategori yang Tersedia
- 🍜 Makanan
- 🥤 Minuman
- 🚗 Transport
- 📱 Kuota/Internet
- 💊 Kesehatan
- 🛍️ Belanja
- 🎮 Hiburan
- 📄 Tagihan
- 📦 Lainnya

---

## Troubleshooting

**Bot tidak merespons?**
- Cek TELEGRAM_TOKEN sudah benar
- Cek log di Railway Dashboard

**Gagal simpan ke Sheets?**
- Pastikan spreadsheet sudah di-share ke email service account
- Cek GOOGLE_CREDENTIALS_JSON tidak ada baris baru (harus satu baris)

**AI salah parse?**
- Pilih "Koreksi" lalu ketik ulang lebih jelas
- Contoh: `nasi goreng ayam spesial 25000` lebih jelas dari `nasgor 25k`
