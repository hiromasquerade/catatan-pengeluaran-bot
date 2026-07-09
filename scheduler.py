import os
import logging
from datetime import datetime
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger
import pytz

logger = logging.getLogger(__name__)

ALLOWED_USER_ID = int(os.environ.get("ALLOWED_USER_ID", "0"))
TIMEZONE = pytz.timezone("Asia/Jakarta")  # WIB


def setup_scheduler(app):
    scheduler = AsyncIOScheduler(timezone=TIMEZONE)

    # Kirim rekap harian setiap jam 21:00 WIB
    scheduler.add_job(
        kirim_rekap_harian,
        CronTrigger(hour=21, minute=0, timezone=TIMEZONE),
        args=[app],
        id="rekap_harian",
        name="Rekap Harian Jam 9 Malam"
    )

    # Kirim rekap bulanan setiap tanggal 1 jam 07:00 WIB (rekap bulan kemarin)
    scheduler.add_job(
        kirim_rekap_bulanan,
        CronTrigger(day=1, hour=7, minute=0, timezone=TIMEZONE),
        args=[app],
        id="rekap_bulanan",
        name="Rekap Bulanan Awal Bulan"
    )

    scheduler.start()
    logger.info("Scheduler aktif: rekap harian jam 21:00 WIB, rekap bulanan tanggal 1")


async def kirim_rekap_harian(app):
    """Kirim ringkasan pengeluaran hari ini ke Telegram jam 9 malam"""
    from sheets import get_rekap_hari_ini
    from export import buat_excel_rekap
    
    try:
        pesan = await get_rekap_hari_ini()
        await app.bot.send_message(
            chat_id=ALLOWED_USER_ID,
            text=pesan,
            parse_mode='Markdown'
        )
        logger.info("Rekap harian terkirim")
    except Exception as e:
        logger.error(f"Gagal kirim rekap harian: {e}")


async def kirim_rekap_bulanan(app):
    """Kirim rekap bulan lalu di tanggal 1 setiap bulan"""
    from sheets import get_rekap_bulan
    from export import buat_excel_rekap_bulan_lalu
    import calendar
    
    # Ambil bulan lalu
    now = datetime.now(TIMEZONE)
    bulan_lalu = now.month - 1 if now.month > 1 else 12
    tahun_lalu = now.year if now.month > 1 else now.year - 1
    nama_bulan = datetime(tahun_lalu, bulan_lalu, 1).strftime("%B %Y")

    try:
        # Kirim pesan rekap
        pesan = f"📅 *Rekap Bulan {nama_bulan} Selesai!*\n\nBerikut rekap pengeluaran kamu bulan lalu:"
        await app.bot.send_message(
            chat_id=ALLOWED_USER_ID,
            text=pesan,
            parse_mode='Markdown'
        )

        # Kirim file Excel
        filepath = await buat_excel_rekap_bulan_lalu(bulan_lalu, tahun_lalu)
        if filepath:
            import os
            with open(filepath, 'rb') as f:
                await app.bot.send_document(
                    chat_id=ALLOWED_USER_ID,
                    document=f,
                    filename=os.path.basename(filepath),
                    caption=f"📊 File Excel rekap {nama_bulan}"
                )
        
        logger.info(f"Rekap bulanan {nama_bulan} terkirim")
    except Exception as e:
        logger.error(f"Gagal kirim rekap bulanan: {e}")
