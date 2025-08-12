from telegram import Update
from telegram.ext import ContextTypes
from data.recipes import recipes

async def nutrition(update: Update, context: ContextTypes.DEFAULT_TYPE):
    # simple list
    text = "🍽 Рецепты (выберите ключ):\n"
    for r in recipes:
        text += f"- {r['key']}: {r['title']}\n"
    text += "\nЧтобы получить рецепт: /recipe key"
    await update.message.reply_text(text)

async def recipe(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not context.args:
        await update.message.reply_text("Укажи ключ рецепта: /recipe ovsyanka")
        return
    key = context.args[0]
    for r in recipes:
        if r['key'] == key:
            txt = f"🍽 {r['title']}\nИнгредиенты: {', '.join(r['ingredients'])}\n\nПриготовление:\n" + '\n'.join(r['steps'])
            txt += f"\n\nКалории: ~{r.get('calories','-')} ккал | Б:{r.get('prot','-')}г Ж:{r.get('fat','-')}г У:{r.get('carb','-')}г"
            await update.message.reply_text(txt)
            return
    await update.message.reply_text("Рецепт не найден.")
