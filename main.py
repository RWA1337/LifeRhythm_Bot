import os
import threading
from flask import Flask
from telegram.ext import Application, CommandHandler
from config import BOT_TOKEN, APP_URL
from db import init_db, get_conn

# handlers imports
from handlers.start import start as start_handler
from handlers.help import help_command
from handlers.profile import profile, setprofile
from handlers.biorhythm import biorhythm
from handlers.nutrition import nutrition, recipe
from handlers.exercise import exercise
from handlers.yoga import yoga
from handlers.meditation import meditation
from handlers.analysis import analysis
from handlers.challenges import challenges, water, water_status
from handlers.admin import admin_stats

# init DB
init_db()

# Telegram app
if not BOT_TOKEN:
    raise SystemExit("BOT_TOKEN is not set in environment")

app_telegram = Application.builder().token(BOT_TOKEN).build()

# register commands
app_telegram.add_handler(CommandHandler("start", start_handler))
app_telegram.add_handler(CommandHandler("help", help_command))
app_telegram.add_handler(CommandHandler("profile", profile))
app_telegram.add_handler(CommandHandler("setprofile", setprofile))
app_telegram.add_handler(CommandHandler("biorhythm", biorhythm))
app_telegram.add_handler(CommandHandler("nutrition", nutrition))
app_telegram.add_handler(CommandHandler("recipe", recipe))
app_telegram.add_handler(CommandHandler("exercise", exercise))
app_telegram.add_handler(CommandHandler("yoga", yoga))
app_telegram.add_handler(CommandHandler("meditation", meditation))
app_telegram.add_handler(CommandHandler("analysis", analysis))
app_telegram.add_handler(CommandHandler("challenges", challenges))
app_telegram.add_handler(CommandHandler("water", water))
app_telegram.add_handler(CommandHandler("water_status", water_status))
app_telegram.add_handler(CommandHandler("admin_stats", admin_stats))

# Flask for health (Render expects open port)
app_web = Flask(__name__)

@app_web.route("/")
def home():
    return "Bot is alive!"

@app_web.route("/get_webhook_info")
def get_webhook_info():
    # helper: not using webhook flow here, but keep endpoint
    return "OK"

def run_flask():
    port = int(os.getenv("PORT", 5000))
    app_web.run(host="0.0.0.0", port=port)

if __name__ == "__main__":
    t = threading.Thread(target=run_flask)
    t.start()
    # start polling (works with Render + Flask thread)
    app_telegram.run_polling()

    app.run(host="0.0.0.0", port=port)


