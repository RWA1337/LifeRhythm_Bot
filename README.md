# LifeRhythm_Bot

MVP Telegram-бот с функциями: профиль, биоритмы, рецепты, упражнения, йога, дыхание, расшифровка анализов, трекер воды, челленджи.

## Как развернуть

1. Добавь файлы в репозиторий (корень + папки handlers, data).
2. На Render — создавай **Web Service (Free)**:
   - Build command: `pip install -r requirements.txt`
   - Start command: `python main.py`
3. В Environment добавь:
   - `BOT_TOKEN` = токен от BotFather
   - `APP_URL` = https://<твой-subdomain>.onrender.com
4. Deploy.
