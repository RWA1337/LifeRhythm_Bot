from telegram import Update
from telegram.ext import ContextTypes

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    text = (
        f"👋 Привет, {user.first_name or ''}! Я LifeRhythm — твой помощник по здоровью.\n\n"
        "Команды:\n"
        "/help — весь список команд\n"
        "/profile — профиль\n"
        "/biorhythm — биоритм\n"
        "/nutrition — рецепты\n"
        "/exercise — упражнения\n"
        "/yoga — йога\n"
        "/meditation — дыхание\n"
        "/analysis — расшифровка анализов\n"
        "/water — трекер воды\n"
        "/daily — мотивация дня"
    )
    await update.message.reply_text(text)
