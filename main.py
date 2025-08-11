# main.py — webhook версия (Flask + ручная обработка апдейтов)
import os
import requests
from flask import Flask, request, jsonify

BOT_TOKEN = os.getenv("BOT_TOKEN")
if not BOT_TOKEN:
    raise SystemExit("BOT_TOKEN is not set")

# Адрес твоего сервиса на Render (пример): https://liferhythm-bot.onrender.com
# Лучше задать в Render переменную APP_URL, если хостнейм другой.
APP_URL = os.getenv("APP_URL", "").rstrip("/")

TELEGRAM_API = f"https://api.telegram.org/bot{BOT_TOKEN}"

app = Flask(__name__)

def send_message(chat_id: int, text: str):
    url = f"{TELEGRAM_API}/sendMessage"
    payload = {"chat_id": chat_id, "text": text}
    try:
        r = requests.post(url, json=payload, timeout=5)
        return r.ok, r.text
    except Exception as e:
        return False, str(e)

@app.route("/", methods=["GET"])
def index():
    return "Bot is alive!", 200

# Telegram will POST updates here. We set webhook to https://<your-domain>/<BOT_TOKEN>
@app.route(f"/{BOT_TOKEN}", methods=["POST"])
def telegram_webhook():
    data = request.get_json(force=True)
    # quickly respond 200 to Telegram
    # parse incoming message if present
    if not data:
        return jsonify({"ok": False, "reason": "no json"}), 400

    # Handle message updates
    msg = data.get("message") or data.get("edited_message")
    if msg:
        chat = msg.get("chat", {})
        chat_id = chat.get("id")
        text = msg.get("text", "")
        if text is None:
            # not text (sticker, photo...), ignore for now
            return jsonify({"ok": True}), 200

        text = text.strip()
        # Simple command handling
        if text.startswith("/start"):
            send_message(chat_id, "👋 Привет! Я LifeRhythm — твой помощник по здоровью. Напиши /help.")
        elif text.startswith("/help"):
            send_message(chat_id,
                "Доступные команды:\n"
                "/start — начать\n"
                "/help — помощь\n"
                "/ping — проверка бота")
        elif text.startswith("/ping"):
            send_message(chat_id, "pong")
        else:
            # default small reply — можно расширить
            send_message(chat_id, "Я получил сообщение: " + (text[:300] if text else "<пусто>"))

    # you can also handle callback_query etc. here later
    return jsonify({"ok": True}), 200

# helper endpoints
@app.route("/set_webhook", methods=["GET"])
def set_webhook():
    # must be called once after deploy OR Render will call it on startup below
    if not APP_URL:
        return "APP_URL not set", 400
    webhook_url = f"{APP_URL}/{BOT_TOKEN}"
    resp = requests.post(f"{TELEGRAM_API}/setWebhook", json={"url": webhook_url, "allowed_updates": ["message","edited_message"]}, timeout=10)
    return jsonify({"setWebhook_resp": resp.json()}), 200

@app.route("/get_webhook_info", methods=["GET"])
def get_webhook_info():
    resp = requests.get(f"{TELEGRAM_API}/getWebhookInfo", timeout=10)
    return jsonify(resp.json()), 200

if __name__ == "__main__":
    # Try to set webhook on start if APP_URL provided
    if APP_URL:
        try:
            webhook_url = f"{APP_URL}/{BOT_TOKEN}"
            print("Setting webhook to", webhook_url)
            r = requests.post(f"{TELEGRAM_API}/setWebhook", json={"url": webhook_url, "allowed_updates": ["message","edited_message"]}, timeout=10)
            print("setWebhook response:", r.status_code, r.text)
        except Exception as e:
            print("Failed to set webhook on startup:", e)

    port = int(os.getenv("PORT", 5000))
    # start Flask (Render detects the open port)
    app.run(host="0.0.0.0", port=port)

