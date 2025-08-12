from telegram import Update
from telegram.ext import ContextTypes
from db import get_conn

def parse_pairs(text):
    pairs = {}
    for part in text.split():
        if '=' in part:
            k,v = part.split('=',1)
            pairs[k.strip()] = v.strip()
    return pairs

async def profile(update: Update, context: ContextTypes.DEFAULT_TYPE):
    tg = update.effective_user
    conn = get_conn()
    cur = conn.cursor()
    cur.execute("SELECT sex, age, height_cm, weight_kg, goal FROM users WHERE tg_id=?", (tg.id,))
    r = cur.fetchone()
    if not r:
        await update.message.reply_text("Профиль пуст. Установите /setprofile sex=male age=30 height=180 weight=80 goal=loss")
    else:
        sex,age,height,weight,goal = r
        await update.message.reply_text(f"👤 Профиль:\nПол: {sex}\nВозраст: {age}\nРост: {height} см\nВес: {weight} кг\nЦель: {goal}")
    conn.close()

async def setprofile(update: Update, context: ContextTypes.DEFAULT_TYPE):
    tg = update.effective_user
    text = ' '.join(context.args)
    if not text:
        await update.message.reply_text("Пример: /setprofile sex=male age=30 height=180 weight=80 goal=loss")
        return
    pairs = parse_pairs(text)
    conn = get_conn()
    cur = conn.cursor()
    # ensure user row exists
    cur.execute("INSERT OR IGNORE INTO users (tg_id, first_name, last_name, username) VALUES (?, ?, ?, ?)",
                (tg.id, tg.first_name or "", tg.last_name or "", tg.username or ""))
    fields = []
    params = []
    mapping = {'sex':'sex','age':'age','height':'height_cm','weight':'weight_kg','goal':'goal'}
    for k,v in pairs.items():
        if k in mapping:
            fields.append(f"{mapping[k]}=?")
            if k in ('age','height','weight'):
                params.append(float(v) if '.' in v else int(v))
            else:
                params.append(v)
    if fields:
        params.append(tg.id)
        cur.execute(f"UPDATE users SET {', '.join(fields)} WHERE tg_id=?", params)
        conn.commit()
        await update.message.reply_text("Профиль обновлён.")
    else:
        await update.message.reply_text("Не распознал поля. Пример: sex=male age=30 height=180 weight=80 goal=loss")
    conn.close()
