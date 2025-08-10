import os
import threading
from flask import Flask
from telegram.ext import ApplicationBuilder, CommandHandler
from telegram import Update
from telegram.ext import ContextTypes

BOT_TOKEN = os.getenv("BOT_TOKEN")

# ---- Telegram bot ----
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Привет! Бот запущен и работает на Render 🚀")

app_telegram = ApplicationBuilder().token(BOT_TOKEN).build()
app_telegram.add_handler(CommandHandler("start", start))

# ---- Flask server ----
app_web = Flask(__name__)

@app_web.route("/")
def home():
    return "Bot is alive!"

def run_flask():
    port = int(os.getenv("PORT", 5000))
    app_web.run(host="0.0.0.0", port=port)

# ---- Запуск ----
if __name__ == "__main__":
    threading.Thread(target=run_flask).start()
    app_telegram.run_polling()
