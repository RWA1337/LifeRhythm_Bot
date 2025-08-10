import os
from telegram.ext import ApplicationBuilder, CommandHandler

BOT_TOKEN = os.getenv("BOT_TOKEN")  # токен берём из Render

async def start(update, context):
    await update.message.reply_text("👋 Привет! Я LifeRhythmBot — твой помощник по здоровью!")

async def help_command(update, context):
    await update.message.reply_text("📋 Доступные команды:\n/start — начать\n/help — помощь")

if __name__ == "__main__":
    app = ApplicationBuilder().token(BOT_TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("help", help_command))
    print("✅ Бот запущен!")
    app.run_polling()

