import os
import random
import threading
import math
import datetime
from flask import Flask
from telegram.ext import ApplicationBuilder, CommandHandler
from telegram import Update
from telegram.ext import ContextTypes
from config import BOT_TOKEN, PORT

# --- Данные ---
exercises = [
    "🏃 Комплекс — зарядка:\n1. Прыжки 30 сек\n2. Приседания 15 раз\n3. Отжимания от стены 10\n4. Планка 30 сек",
    "💪 Утренняя разминка:\n1. Махи руками 20 раз\n2. Наклоны 15 раз\n3. Приседания 10 раз\n4. Лёгкая растяжка 2 мин"
]

breathing = [
    "💨 Дыхание 4-4-4:\nВдох 4 сек — Задержка 4 сек — Выдох 4 сек. Повтори 6–8 циклов.",
    "🌬️ Дыхание 4-7-8:\nВдох 4 сек — Задержка 7 сек — Выдох 8 сек. 3–4 повтора для расслабления."
]

yoga_poses = [
    "🧘 Поза горы (Тадасана) — 1 мин, затем наклон вперёд.",
    "🧘 Поза ребёнка (Баласана) — 2–3 мин для расслабления спины."
]

nutrition_tips = [
    "🥗 Съешь сегодня тарелку овощей и белок (курица, рыба или бобовые).",
    "🍎 Перекус — яблоко и горсть орехов вместо сладкого."
]

# --- Состояние ---
water_intake = {}

# --- Команды ---
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "Привет! Я LifeRhythm Bot 🚀\n"
        "Команды:\n"
        "/exercise — упражнения\n"
        "/meditation — дыхание и медитация\n"
        "/yoga — йога\n"
        "/nutrition — советы по питанию\n"
        "/water — учёт воды\n"
        "/analysis <анализ> — справка по анализу\n"
        "/biorhythm <ДД.ММ.ГГГГ> — биоритмы"
    )

async def exercise(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(random.choice(exercises))

async def meditation(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(random.choice(breathing))

async def yoga(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(random.choice(yoga_poses))

async def nutrition(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(random.choice(nutrition_tips))

async def water(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    water_intake[user_id] = water_intake.get(user_id, 0) + 250
    await update.message.reply_text(f"💧 Отмечено 250 мл. Всего сегодня: {water_intake[user_id]} мл (цель ~2000 мл).")

async def analysis(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not context.args:
        await update.message.reply_text("Использование: /analysis hemoglobin")
        return
    param = context.args[0].lower()
    reference = {
        "hemoglobin": "Гемоглобин: норма 120-160 г/л у женщин, 130-170 г/л у мужчин.",
        "glucose": "Глюкоза: норма 3.9-5.5 ммоль/л натощак."
    }
    await update.message.reply_text(reference.get(param, "Нет информации по этому параметру."))

async def biorhythm(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not context.args:
        await update.message.reply_text("Использование: /biorhythm ДД.ММ.ГГГГ")
        return
    try:
        birth_date = datetime.datetime.strptime(context.args[0], "%d.%m.%Y")
        today = datetime.datetime.now()
        days_alive = (today - birth_date).days
        physical = math.sin(2 * math.pi * days_alive / 23) * 100
        emotional = math.sin(2 * math.pi * days_alive / 28) * 100
        intellectual = math.sin(2 * math.pi * days_alive / 33) * 100
        await update.message.reply_text(
            f"📊 Биоритмы на сегодня:\n"
            f"Физический: {physical:.1f}%\n"
            f"Эмоциональный: {emotional:.1f}%\n"
            f"Интеллектуальный: {intellectual:.1f}%"
        )
    except ValueError:
        await update.message.reply_text("Неверный формат даты. Используй ДД.ММ.ГГГГ.")

# --- Flask ---
app_web = Flask(__name__)

@app_web.route("/")
def home():
    return "Bot is alive!"

def run_flask():
    app_web.run(host="0.0.0.0", port=PORT)

# --- Запуск ---
def run_bot():
    app_telegram = ApplicationBuilder().token(BOT_TOKEN).build()
    app_telegram.add_handler(CommandHandler("start", start))
    app_telegram.add_handler(CommandHandler("exercise", exercise))
    app_telegram.add_handler(CommandHandler("meditation", meditation))
    app_telegram.add_handler(CommandHandler("yoga", yoga))
    app_telegram.add_handler(CommandHandler("nutrition", nutrition))
    app_telegram.add_handler(CommandHandler("water", water))
    app_telegram.add_handler(CommandHandler("analysis", analysis))
    app_telegram.add_handler(CommandHandler("biorhythm", biorhythm))
    app_telegram.run_polling()

if __name__ == "__main__":
    threading.Thread(target=run_flask).start()
    run_bot()

    threading.Thread(target=run_flask).start()
    app_telegram.run_polling()

