import os
import json
import logging
from datetime import datetime
from telegram import Update, ReplyKeyboardMarkup
from telegram.ext import (
    Application, CommandHandler, MessageHandler,
    filters, ContextTypes, ConversationHandler
)
from groq_parser import parse_pengeluaran
from sheets import simpan_pengeluaran, get_rekap_hari_ini, get_rekap_bulan
from scheduler import setup_scheduler
from export import buat_excel_rekap

logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

TELEGRAM_TOKEN = os.environ.get("TELEGRAM_TOKEN")
ALLOWED_USER_ID = int(os.environ.get("ALLOWED_USER_ID", "0"))  # ID Telegram kamu

KONFIRMASI = 1
pending_data = {}  # simpan sementara data yang menunggu konfirmasi


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != ALLOWED_USER_ID:
        await update.message.reply_text("❌ Maaf, bot ini private.")
        return

    await update.message.reply_text(
        "👋 Halo! Aku siap mencatat pengeluaran kamu.\n\n"
        "Cukup ketik apa yang kamu beli dan harganya, contoh:\n"
        "• `mie ayam 15k`\n"
        "• `bensin 50000`\n"
        "• `kopi 8rb`\n\n"
        "Perintah lain:\n"
        "/hari - Rekap hari ini\n"
        "/bulan - Rekap bulan ini\n"
        "/export - Download Excel rekap bulan ini",
        parse_mode='Markdown'
    )


async def catat_pengeluaran(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != ALLOWED_USER_ID:
        return

    teks = update.message.text.strip()
    chat_id = update.effective_chat.id

    await update.message.reply_text("⏳ Sedang memproses...")

    hasil = await parse_pengeluaran(teks)

    if not hasil:
        await update.message.reply_text(
            "❓ Aku tidak bisa mengenali pengeluaran dari teks itu.\n"
            "Coba format seperti: `mie ayam 15k` atau `bensin 50000`",
            parse_mode='Markdown'
        )
        return

    pending_data[chat_id] = hasil

    keyboard = [["✅ Ya, benar", "✏️ Koreksi", "❌ Batal"]]
    reply_markup = ReplyKeyboardMarkup(keyboard, one_time_keyboard=True, resize_keyboard=True)

    await update.message.reply_text(
        f"📝 Aku catat ini ya:\n\n"
        f"🛒 Item    : *{hasil['nama']}*\n"
        f"💰 Harga   : *Rp {hasil['harga']:,}*\n"
        f"📂 Kategori: *{hasil['kategori']}*\n"
        f"📅 Tanggal : *{hasil['tanggal']}*\n\n"
        f"Sudah benar?",
        reply_markup=reply_markup,
        parse_mode='Markdown'
    )
    return KONFIRMASI


async def handle_konfirmasi(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != ALLOWED_USER_ID:
        return

    chat_id = update.effective_chat.id
    jawaban = update.message.text

    if jawaban == "✅ Ya, benar":
        data = pending_data.pop(chat_id, None)
        if data:
            await simpan_pengeluaran(data)
            await update.message.reply_text(
                f"✅ Tercatat!\n*{data['nama']}* — Rp {data['harga']:,} [{data['kategori']}]",
                parse_mode='Markdown'
            )
        return ConversationHandler.END

    elif jawaban == "✏️ Koreksi":
        await update.message.reply_text(
            "Ketik ulang pengeluarannya dengan format yang lebih jelas, contoh:\n"
            "`nasi goreng ayam 20000`",
            parse_mode='Markdown'
        )
        pending_data.pop(chat_id, None)
        return ConversationHandler.END

    elif jawaban == "❌ Batal":
        pending_data.pop(chat_id, None)
        await update.message.reply_text("❌ Dibatalkan, tidak ada yang dicatat.")
        return ConversationHandler.END


async def rekap_hari(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != ALLOWED_USER_ID:
        return

    await update.message.reply_text("⏳ Mengambil data hari ini...")
    pesan = await get_rekap_hari_ini()
    await update.message.reply_text(pesan, parse_mode='Markdown')


async def rekap_bulan(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != ALLOWED_USER_ID:
        return

    await update.message.reply_text("⏳ Mengambil data bulan ini...")
    pesan = await get_rekap_bulan()
    await update.message.reply_text(pesan, parse_mode='Markdown')


async def export_excel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != ALLOWED_USER_ID:
        return

    await update.message.reply_text("⏳ Membuat file Excel...")
    filepath = await buat_excel_rekap()

    if filepath:
        with open(filepath, 'rb') as f:
            await update.message.reply_document(
                document=f,
                filename=os.path.basename(filepath),
                caption="📊 Rekap pengeluaran bulan ini"
            )
    else:
        await update.message.reply_text("❌ Gagal membuat Excel, tidak ada data bulan ini.")


def main():
    app = Application.builder().token(TELEGRAM_TOKEN).build()

    conv_handler = ConversationHandler(
        entry_points=[MessageHandler(filters.TEXT & ~filters.COMMAND, catat_pengeluaran)],
        states={
            KONFIRMASI: [MessageHandler(filters.TEXT & ~filters.COMMAND, handle_konfirmasi)],
        },
        fallbacks=[]
    )

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("hari", rekap_hari))
    app.add_handler(CommandHandler("bulan", rekap_bulan))
    app.add_handler(CommandHandler("export", export_excel))
    app.add_handler(conv_handler)

    # Setup scheduler (kirim rekap jam 9 malam & akhir bulan)
    setup_scheduler(app)

    logger.info("Bot berjalan...")
    app.run_polling()


if __name__ == "__main__":
    main()
