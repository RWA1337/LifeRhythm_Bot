from telegram import Update
from telegram.ext import ContextTypes
from config import ADMIN_IDS
from db import get_conn

async def admin_stats(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id not in ADMIN_IDS:
        await update.message.reply_text("Доступ запрещён.")
        return
    conn = get_conn()
    cur = conn.cursor()
    cur.execute("SELECT COUNT(*) FROM users")
    total = cur.fetchone()[0]
    conn.close()
    await update.message.reply_text(f"Пользователей в БД: {total}")
