import os
import random
import threading
from flask import Flask
from telegram.ext import ApplicationBuilder, CommandHandler
from telegram import Update
from telegram.ext import ContextTypes

BOT_TOKEN = os.getenv("BOT_TOKEN")

# ======== Команды ========

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "👋 Привет! Я бот LifeRhythm.\n"
        "Доступные команды:\n"
        "/nutrition — советы по питанию\n"
        "/exercise — упражнения\n"
        "/meditation — медитации и дыхательные практики\n"
        "/yoga — позы йоги\n"
        "/analysis <анализ> — расшифровка анализов\n"
        "/water — отметка воды\n"
        "/help — помощь\n"
        "/about — обо мне"
    )

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "ℹ Помощь:\n"
        "Используй команды, чтобы получить советы по здоровью и образу жизни.\n"
        "Например:\n"
        "/nutrition\n"
        "/exercise\n"
        "/meditation\n"
        "/yoga\n"
        "/analysis hemoglobin"
    )

async def about(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "🤖 LifeRhythm Bot — помощник для здоровья.\n"
        "Даю советы по питанию, упражнениям, медитации и водному балансу."
    )

async def nutrition(update: Update, context: ContextTypes.DEFAULT_TYPE):
    tips = [
        "🥗 Ешь больше овощей и фруктов — минимум 400 г в день.",
        "💧 Пей достаточно воды — около 2 л в день.",
        "🍳 Завтракай в течение часа после пробуждения.",
        "🥜 Добавляй в рацион орехи и бобовые.",
        "🍋 Начни утро со стакана воды с лимоном."
    ]
    await update.message.reply_text(random.choice(tips))

async def exercise(update: Update, context: ContextTypes.DEFAULT_TYPE):
    workouts = [
        "🏃 Комплекс — зарядка:\n1. Прыжки 30 сек\n2. Приседания 15 раз\n3. Отжимания от стены 10\n4. Планка 30 сек",
        "💪 Короткая тренировка:\n1. Приседания 20 раз\n2. Выпады 10 на каждую ногу\n3. Отжимания 10 раз\n4. Планка 40 сек",
        "🤸 Лёгкая разминка:\n1. Круговые вращения головой\n2. Растяжка рук и ног\n3. Наклоны вперёд 10 раз"
    ]
    await update.message.reply_text(random.choice(workouts))

async def meditation(update: Update, context: ContextTypes.DEFAULT_TYPE):
    practices = [
        "💨 Дыхание 4-4-4:\nВдох 4 сек — Задержка 4 сек — Выдох 4 сек. Повтори 6–8 циклов.",
        "🧘 Медитация на дыхании:\nСфокусируйся на вдохах и выдохах в течение 5 минут.",
        "🌊 Визуализация:\nПредставь море и звук волн, расслабляясь 3–5 минут."
    ]
    await update.message.reply_text(random.choice(practices))

async def yoga(update: Update, context: ContextTypes.DEFAULT_TYPE):
    poses = [
        "🧘‍♂️ Поза горы (Тадасана) — выпрямься, ноги вместе, руки вверх.",
        "🦋 Поза бабочки — сядь, соединяя стопы, колени в стороны.",
        "🌿 Поза дерева — встань на одну ногу, вторую упри в бедро, руки вверх.",
        "🐍 Поза кобры — лёжа на животе, подними грудь, руки под плечами."
    ]
    await update.message.reply_text(random.choice(poses))

# Храним воду в памяти
user_water = {}

async def water(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.message.from_user.id
    amount = 250  # мл
    user_water[user_id] = user_water.get(user_id, 0) + amount
    await update.message.reply_text(
        f"💧 Отмечено {amount} мл. Всего сегодня: {user_water[user_id]} мл (цель ~2000 мл)."
    )

async def analysis(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not context.args:
        await update.message.reply_text("Использование: /analysis <показатель>")
        return
    param = context.args[0].lower()
    if param == "hemoglobin":
        await update.message.reply_text("📊 Гемоглобин: норма 120–160 г/л для женщин, 130–170 г/л для мужчин.")
    elif param == "glucose":
        await update.message.reply_text("📊 Глюкоза: норма 3.5–5.5 ммоль/л натощак.")
    else:
        await update.message.reply_text("❓ Неизвестный показатель.")

# ======== Flask сервер ========

app_web = Flask(__name__)

@app_web.route("/")
def home():
    return "Bot is alive!"

def run_flask():
    port = int(os.getenv("PORT", 5000))
    app_web.run(host="0.0.0.0", port=port)

# ======== Запуск Telegram ========

if __name__ == "__main__":
    app_telegram = ApplicationBuilder().token(BOT_TOKEN).build()

    app_telegram.add_handler(CommandHandler("start", start))
    app_telegram.add_handler(CommandHandler("help", help_command))
    app_telegram.add_handler(CommandHandler("about", about))
    app_telegram.add_handler(CommandHandler("nutrition", nutrition))
    app_telegram.add_handler(CommandHandler("exercise", exercise))
    app_telegram.add_handler(CommandHandler("meditation", meditation))
    app_telegram.add_handler(CommandHandler("yoga", yoga))
    app_telegram.add_handler(CommandHandler("water", water))
    app_telegram.add_handler(CommandHandler("analysis", analysis))

    threading.Thread(target=run_flask).start()
    app_telegram.run_polling()
