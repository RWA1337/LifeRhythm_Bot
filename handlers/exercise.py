from telegram import Update
from telegram.ext import ContextTypes
from data.exercises import exercises

async def exercise(update: Update, context: ContextTypes.DEFAULT_TYPE):
    goal = context.args[0] if context.args else "зарядка"
    if goal not in exercises:
        await update.message.reply_text("Цель не найдена. Доступно: " + ', '.join(exercises.keys()))
        return
    text = f"🏃 Комплекс — {goal}:\n"
    for i, ex in enumerate(exercises[goal], 1):
        text += f"{i}. {ex}\n"
    await update.message.reply_text(text)
