from telegram import Update
from telegram.ext import ContextTypes
from db import get_conn
from datetime import datetime

async def challenges(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = "🏆 Челленджи:\n1) Водный 7-дн (пей 2000 мл/день)\n\nОтметить стакан: /water 250\nПосмотреть: /water status"
    await update.message.reply_text(text)

async def water(update: Update, context: ContextTypes.DEFAULT_TYPE):
    conn = get_conn()
    cur = conn.cursor()
    tg = update.effective_user
    day = datetime.now().strftime("%Y-%m-%d")
    try:
        amount = int(context.args[0]) if context.args else 250
    except:
        await update.message.reply_text("Неверный формат. Пример: /water 250")
        conn.close()
        return
    cur.execute("SELECT amount_ml FROM water WHERE tg_id=? AND day=?", (tg.id, day))
    r = cur.fetchone()
    if r:
        total = r[0] + amount
        cur.execute("UPDATE water SET amount_ml=? WHERE tg_id=? AND day=?", (total, tg.id, day))
    else:
        total = amount
        cur.execute("INSERT INTO water (tg_id, day, amount_ml) VALUES (?, ?, ?)", (tg.id, day, amount))
    conn.commit()
    conn.close()
    await update.message.reply_text(f"💧 Отмечено {amount} мл. Всего сегодня: {total} мл (цель ~2000 мл).")

async def water_status(update: Update, context: ContextTypes.DEFAULT_TYPE):
    conn = get_conn()
    cur = conn.cursor()
    tg = update.effective_user
    day = datetime.now().strftime("%Y-%m-%d")
    cur.execute("SELECT amount_ml FROM water WHERE tg_id=? AND day=?", (tg.id, day))
    r = cur.fetchone()
    total = r[0] if r else 0
    conn.close()
    await update.message.reply_text(f"💧 Сегодня выпито: {total} мл (цель 2000 мл).")
