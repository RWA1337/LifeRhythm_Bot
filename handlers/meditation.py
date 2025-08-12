from telegram import Update
from telegram.ext import ContextTypes

async def meditation(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = (
        "💨 Дыхание 4-4-4:\n"
        "Вдох 4 сек — Задержка 4 сек — Выдох 4 сек. Повтори 6–8 циклов.\n"
        "Также можно 4-6 минут медитации лежа."
    )
    await update.message.reply_text(text)
