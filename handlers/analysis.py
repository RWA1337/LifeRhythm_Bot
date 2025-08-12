from telegram import Update
from telegram.ext import ContextTypes
from data.analysis_ref import analysis_ref

async def analysis(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not context.args:
        await update.message.reply_text("Использование: /analysis hemoglobin")
        return
    key = context.args[0].lower()
    info = analysis_ref.get(key) or analysis_ref.get(key.upper())
    if not info:
        await update.message.reply_text("Параметр не найден.")
        return
    text = f"🩺 {info.get('name', key)}\nНорма: {info.get('norm','-')}\n{info.get('what','')}\n\nСовет: {info.get('advice','Обратитесь к врачу при сомнениях')}"
    await update.message.reply_text(text)
