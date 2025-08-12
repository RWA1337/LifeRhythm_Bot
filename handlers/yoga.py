from telegram import Update
from telegram.ext import ContextTypes

async def yoga(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = "🧘 Утренняя растяжка:\n1) Наклоны головы 30 сек\n2) Кошка-корова 1 мин\n3) Наклон вперед 1 мин\n4) Савасана 1 мин"
    await update.message.reply_text(text)
