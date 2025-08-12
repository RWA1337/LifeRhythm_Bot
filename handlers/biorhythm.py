from telegram import Update
from telegram.ext import ContextTypes
import math
from datetime import datetime

async def biorhythm(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not context.args:
        await update.message.reply_text("Укажите дату: /biorhythm YYYY-MM-DD")
        return
    try:
        birth = datetime.strptime(context.args[0], "%Y-%m-%d")
    except:
        await update.message.reply_text("Неверный формат даты. Используй YYYY-MM-DD")
        return
    days = (datetime.now() - birth).days
    physical = round(100 * math.sin(2 * math.pi * days / 23), 2)
    emotional = round(100 * math.sin(2 * math.pi * days / 28), 2)
    intellectual = round(100 * math.sin(2 * math.pi * days / 33), 2)
    await update.message.reply_text(
        f"📊 Биоритм:\nФизический: {physical}%\nЭмоциональный: {emotional}%\nИнтеллект: {intellectual}%"
    )
