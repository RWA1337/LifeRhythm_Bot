from telegram import Update
from telegram.ext import ContextTypes

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "📌 Список команд:\n"
        "/start — приветствие\n"
        "/help — справка\n"
        "/profile — показать/задать профиль\n"
        "/biorhythm YYYY-MM-DD — расчёт биоритма\n"
        "/nutrition — рецепты\n"
        "/exercise [цель] — упражнения\n"
        "/yoga — йога/растяжка\n"
        "/meditation — дыхание\n"
        "/analysis [param] — расшифровка анализов\n"
        "/water [ml] — отметить воду (например /water 250)\n"
        "/daily — мотивация дня"
    )
