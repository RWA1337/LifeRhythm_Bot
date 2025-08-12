import os
import threading
from datetime import datetime
from flask import Flask
from telegram import Update, InlineKeyboardMarkup, InlineKeyboardButton
from telegram.ext import (
    ApplicationBuilder, CommandHandler, ContextTypes,
    MessageHandler, filters, CallbackQueryHandler
)

BOT_TOKEN = os.getenv("BOT_TOKEN")

# ---- Telegram bot ----
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    keyboard = [
        [InlineKeyboardButton("📅 Биоритмы", callback_data="biorhythm")],
        [InlineKeyboardButton("ℹ️ О проекте", callback_data="about")],
        [InlineKeyboardButton("❓ Помощь", callback_data="help")]
    ]
    await update.message.reply_text(
        "Привет! Я бот для расчёта биоритмов и помощи в планировании дня 🚀\n"
        "Выберите раздел ниже:",
        reply_markup=InlineKeyboardMarkup(keyboard)
    )

async def button_click(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    if query.data == "biorhythm":
        await query.edit_message_text("📅 Введите дату рождения в формате ДД.ММ.ГГГГ")
    elif query.data == "about":
        await query.edit_message_text("ℹ️ Этот бот рассчитывает биоритмы по вашей дате рождения.\nАвтор: @ваш_ник")
    elif query.data == "help":
        await query.edit_message_text("❓ Просто введите дату рождения, и я скажу ваши текущие биоритмы!")

async def handle_date(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        bday = datetime.strptime(update.message.text.strip(), "%d.%m.%Y")
        days_lived = (datetime.now() - bday).days
        physical = round((days_lived % 23) / 23 * 100, 1)
        emotional = round((days_lived % 28) / 28 * 100, 1)
        intellectual = round((days_lived % 33) / 33 * 100, 1)
        await update.message.reply_text(
            f"📊 Ваши биоритмы сегодня:\n"
            f"💪 Физический: {physical}%\n"
            f"💖 Эмоциональный: {emotional}%\n"
            f"🧠 Интеллектуальный: {intellectual}%"
        )
    except ValueError:
        await update.message.reply_text("⚠️ Неверный формат даты! Используйте ДД.ММ.ГГГГ")

app_telegram = ApplicationBuilder().token(BOT_TOKEN).build()
app_telegram.add_handler(CommandHandler("start", start))
app_telegram.add_handler(CallbackQueryHandler(button_click))
app_telegram.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_date))

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

