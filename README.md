# LifeRhythm_Bot

Телеграм-бот с Flask-сервером для деплоя на Render.

## Как запустить на Render

1. Залей репозиторий на GitHub.
2. На сайте [Render](https://render.com) создай **Web Service**.
3. Укажи:
   - Build Command: `pip install -r requirements.txt`
   - Start Command: `python main.py`
4. В настройках Render добавь переменную окружения:
   - Key: `BOT_TOKEN`
   - Value: токен твоего бота из BotFather.
5. Запусти деплой.
