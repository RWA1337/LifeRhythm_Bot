# main.py
import os
import json
import random
import datetime
from typing import List, Dict

from flask import Flask, request, jsonify
import telebot
from telebot import types

# ---------- КОНФИГ ----------
BOT_TOKEN = os.environ.get("BOT_TOKEN")
PUBLIC_URL = os.environ.get("PUBLIC_URL", "").rstrip("/")
PORT = int(os.environ.get("PORT", 10000))

if not BOT_TOKEN:
    raise RuntimeError("Установи BOT_TOKEN в переменных окружения.")
if not PUBLIC_URL:
    raise RuntimeError("Установи PUBLIC_URL в переменных окружения, например https://liferhythm-bot.onrender.com")

WEBHOOK_PATH = "/webhook"
WEBHOOK_URL = f"{PUBLIC_URL}{WEBHOOK_PATH}"

DATA_FILE = "liferhythm_data.json"  # локальное хранилище (json)

bot = telebot.TeleBot(BOT_TOKEN)
app = Flask(__name__)

# ---------- УТИЛИТЫ ----------
def load_data() -> dict:
    try:
        with open(DATA_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return {"users": {}}  # users: {chat_id: { "water": {date: ml}, "dob": "YYYY-MM-DD" } }

def save_data(data: dict):
    try:
        with open(DATA_FILE, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
    except Exception as e:
        print("SAVE ERROR:", e)

def today_str() -> str:
    return datetime.date.today().isoformat()

def parse_n_from_text(text: str, default: int, min_v: int, max_v: int) -> int:
    # Попытка найти число в сообщении, иначе default
    parts = text.strip().split()
    for p in parts:
        if p.isdigit():
            n = int(p)
            return max(min_v, min(max_v, n))
    return default

# ---------- КОНТЕНТ (много вариантов) ----------
# Упражнения (20 вариантов)
EXERCISES = [
    {"title": "Утренний тонус (10 минут)", "steps": ["Потягивания 30 с", "Приседания 15", "Отжимания от стены 10", "Планка 40 с", "Ходьба на месте 60 с"]},
    {"title": "Кардио-быстро (8 мин)", "steps": ["Джампинг джек 40 с", "Бег на месте 40 с", "Прыжки с подъемом колен 30 с", "Отдых 30 с", "Повтор 2 круга"]},
    {"title": "Сила корпуса", "steps": ["Планка 3×30 с", "Боковая планка 2×20 с", "Скручивания 3×20", "Ножницы 3×30"]},
    {"title": "Ноги и ягодицы", "steps": ["Присед 3×15", "Выпады 3×10/нога", "Мост ягодичный 3×15", "Подъём на носки 3×20"]},
    {"title": "Спина и осанка", "steps": ["Супермен 3×12", "Ягодичный мост 3×15", "Растяжка поясницы 60 с"]},
    {"title": "Офис-микро (5 мин)", "steps": ["Круги плечами 30 с", "Растяжка шеи 30 с", "Наклоны 10 раз", "Сведение лопаток 20 раз"]},
    {"title": "HIIT-6", "steps": ["30 с ходьба/30 с прыжки ×6", "Отдых 60 с", "Повторить при силе"]},
    {"title": "Укрепление рук", "steps": ["Отжимания от стула 3×10", "Обратные отжимания 3×8", "Изометрия 30 с"]},
    {"title": "Баланс и ноги", "steps": ["Баланс на одной ноге 2×30 с", "Боковые выпады 3×12", "Растяжка 60 с"]},
    {"title": "Лёгкое кардио (20 мин)", "steps": ["Ходьба / степ 20 минут, пульс комфортный"]},
    {"title": "Кор-стабильность", "steps": ["Планка на локтях 3×40 с", "Русские скручивания 3×20", "Планка с подъемом ноги 2×10/нога"]},
    {"title": "Интервальная лестница", "steps": ["40 с работа / 20 с отдых х8: бег, прыжки, присед"]},
    {"title": "Полный круг 12 мин", "steps": ["Присед 40 с", "Отжим 30 с", "Планка 30 с", "Скручивания 40 с"]},
    {"title": "Растяжка после работы", "steps": ["Растяжка задней поверхности бедра 30 с", "Квадрицепс 30 с", "Поясница 30 с", "Поза ребёнка 60 с"]},
    {"title": "Функционал—дом", "steps": ["Подъёмы со стула 3×12", "Перенос веса 2×20", "Баланс 2×30 с"]},
    {"title": "Динамическая разминка", "steps": ["Круги тазом 30 с", "Колени вверх 30 с", "Наклоны в стороны 20 раз"]},
    {"title": "Силовой мини", "steps": ["Присед 4×12", "Выпады 3×10", "Отжим 3×8", "Планка 3×30"]},
    {"title": "Тонус плеч/спины", "steps": ["Круги руками 30 с", "Y-T-W 2×8", "Растяжка грудных 30 с"]},
    {"title": "Кардио-энергия", "steps": ["Бёрпи (легко) 3×10", "Скакалка 2×60 с", "Быстрая ходьба 5 мин"]},
    {"title": "Вечерняя релаксация", "steps": ["Медленные наклоны 10 раз", "Кошка-корова 8 циклов", "Шавасана 3–5 мин"]},
]

# Дыхательные техники / медитации (20)
MEDITATIONS = [
    {"title": "4-4-4-4 (квадрат)", "how": ["Вдох 4", "Задержка 4", "Выдох 4", "Задержка 4", "Повтори 6-10 циклов"]},
    {"title": "4-7-8", "how": ["Вдох 4", "Задержка 7", "Выдох 8", "3–6 циклов"]},
    {"title": "Когерентное 5/5", "how": ["Вдох 5", "Выдох 5", "5–10 минут"]},
    {"title": "Продлённый выдох 1:2", "how": ["Вдох 4", "Выдох 8", "3–5 минут"]},
    {"title": "Диафрагмальное дыхание", "how": ["Рука на живот, дыхание носом, живот под ладонь", "5–7 минут"]},
    {"title": "Дыхание йоги (уджайи)", "how": ["Мягкий шум в горле на выдохе", "3–5 минут"]},
    {"title": "Прогрессивная релаксация", "how": ["Напряги и отпусти группы мышц, сверху вниз", "10 минут"]},
    {"title": "Сканирование тела", "how": ["Внимание по зонам от головы к стопам", "5–12 минут"]},
    {"title": "Ритм шагов 4/6", "how": ["Во время прогулки: вдох 4 шага, выдох 6 шагов", "10–20 мин"]},
    {"title": "3 глубоких выдоха", "how": ["3 медленных глубоких выдоха, расслабляя плечи"]},
    {"title": "Заземление 5-4-3-2-1", "how": ["Отмечай объекты: 5 вижу, 4 слышу, 3 чувствую ...", "2–3 мин"]},
    {"title": "Метта (доброжелательность)", "how": ["Посылай добрые пожелания сначала себе, потом другим", "5 мин"]},
    {"title": "Визуализация дыхания", "how": ["Воображай, как воздух смягчает тело", "5–8 минут"]},
    {"title": "Дыхание «насос»", "how": ["Два коротких вдоха + длинный выдох", "1–2 минуты"]},
    {"title": "Расслабляющий счет", "how": ["Считай тихо вдох/выдох до 10, затем назад", "5 минут"]},
    {"title": "Бодрость 3/3", "how": ["Короткий ритм 3/3 при усталости", "2–4 минуты"]},
    {"title": "Дыхание животом сидя", "how": ["Ладонь на живот, дыхание мягко в живот", "5 минут"]},
    {"title": "Микро-медитация 1 мин", "how": ["1 мин: медленное дыхание и внимание к телу"]},
    {"title": "День-ночь (для сна)", "how": ["Выдох длиннее вдоха 1.5–2×", "5–10 минут перед сном"]},
    {"title": "Дыхание и осознанность", "how": ["Сосредоточься на точке у ноздрей", "5–10 минут"]},
]

# Йога (20)
YOGA = [
    {"title": "Тадасана (Гора)", "how": ["Стой прямо, стопы вместе/на ширине таза", "Вытяни макушку вверх", "Дыши ровно 6–10 циклов"]},
    {"title": "Врикшасана (Дерево)", "how": ["Опора на одной ноге", "Стопа ко внутренней бедренной поверхности", "30–60 с/нога"]},
    {"title": "Адхо Мукха Шванасана (Собака вниз)", "how": ["Расположи ладони, таз вверх", "Дыхание ровное 6–8 циклов"]},
    {"title": "Бхуджангасана (Кобра)", "how": ["Лежа, руки под плечи, мягкий прогиб", "5–8 дыханий"]},
    {"title": "Баласана (Поза ребёнка)", "how": ["Сядь на пятки, лоб к полу", "Дыши спиной 1–2 минуты"]},
    {"title": "Вирасана (воин II)", "how": ["Широкая стойка, взгляд вперед", "5–8 дыханий/сторона"]},
    {"title": "Поза дерева", "how": ["Стабильный баланс, дыхание ровное"]},
    {"title": "Поза лодки", "how": ["Сидя, корпус назад, держи центр 20–40 с"]},
    {"title": "Поза стула", "how": ["Колени назад, руки вверх, 5–8 дыханий"]},
    {"title": "Поза треугольника", "how": ["Тянемся одной рукой к ноге, раскрываем грудь", "5 дыханий/сторона"]},
    {"title": "Полумост", "how": ["Лежа, поднимаем таз, 5–8 дыханий"]},
    {"title": "Поза младенца счастья", "how": ["Лёжа, стопы в руки, мягкая растяжка"]},
    {"title": "Поза голубя (лайт)", "how": ["Колено вперед, таз ровно, 1 мин/сторона"]},
    {"title": "Кошка-корова", "how": ["На вдох — прогиб, на выдох — округление", "8–12 циклов"]},
    {"title": "Шавасана", "how": ["Полный релакс лёжа, 3–7 минут"]},
    {"title": "Поза скрутки лёжа", "how": ["Колени в сторону, плечи прижаты", "1–2 минуты/сторона"]},
    {"title": "Поза моста на одном плече (лайт)", "how": ["Таз вверх, удержание 20–30 с"]},
    {"title": "Планка", "how": ["Кор в напряжении, 20–60 с"]},
    {"title": "Боковая планка (колено в пол)", "how": ["Поддержка, 20–40 с/сторона"]},
    {"title": "Наклон сидя", "how": ["Длинная спина, наклон от таза, 8 дыханий"]},
]

# Питание (50 коротких советов)
NUTRITION = [
    "Старт дня со стакана воды (250–300 мл).",
    "Добавляй белок в каждый приём пищи.",
    "Цель: 400 г овощей в день.",
    "Фрукты 1–2 порции в день.",
    "Цельнозерновые вместо рафинированных.",
    "Орехи — порция 20–30 г.",
    "Уменьши сладкие напитки.",
    "Ешь медленнее — насыщение приходит позже.",
    "Завтрак с белком улучшит сытость.",
    "Ужин за 2–3 часа до сна.",
    "Планируй меню на 2–3 дня.",
    "Готовь комбинированные блюда: белок + овощи.",
    "Сокращай перекусы из упаковки.",
    "Пей воду до еды — иногда это помогает.",
    "Соль умеренно, используй травы и специи.",
    "Проверяй порции — тарелка 1/2 овощи, 1/4 белок, 1/4 углеводы.",
    "Ограничь фастфуд, он высококалориен и беден нутриентами.",
    "После тренировки белок + углеводы (йогурт + банан).",
    "Включай рыбу 1–2 раза в неделю.",
    "Бобовые — источник белка и клетчатки.",
    "Ешь сезонно — вкуснее и экономнее.",
    "Избегай поздних перекусов.",
    "Снэки: фрукты, йогурт, орехи.",
    "Читай составы — меньше E-аддитивов.",
    "Домашние соусы лучше магазинных.",
    "Контроль порций помогает снижать вес.",
    "Не пропускай завтрак регулярно.",
    "Интервально-голодание — опция, но не для всех.",
    "Умеренность важнее крайностей.",
    "Сладости лучше после основного приёма пищи.",
    "Планируй покупки списком.",
    "Готовь и замораживай порции для занятых дней.",
    "Пей чай/воду без сахара.",
    "Если нужен подсчёт калорий — используй приложение.",
    "Следи за признаками пищевой непереносимости.",
    "Холодная вода после тренировки — ок.",
    "Поддерживай разнообразие — так легче соблюдать.",
    "Оценка сытости 1–10: стоп на 7–8.",
    "Отдавай предпочтение цельным продуктам.",
    "Быстрые перекусы: творог, яйца, банан.",
    "Готовь несколько овощных гарниров заранее.",
    "Добавляй зелень — витамины и вкус.",
    "Регулярный сон помогает питанию и весу.",
    "Алкоголь повышает калорийность и снижает самоконтроль.",
    "Питайся в компании — это уменьшает стресс.",
    "Измеряй прогресс по трендам, а не по весу каждый день.",
    "Если есть хронические болезни — консультируйся с врачом."
]

# Анализ (40 справок) — краткие ориентиры (не медсовет)
ANALYSIS = {
    "hemoglobin": "Гемоглобин — перенос кислорода. Низкий: усталость, бледность. Проверять с ферритином.",
    "ferritin": "Ферритин — запасы железа. Низкий часто вызывает усталость/выпадение волос.",
    "vitamin_d": "Витамин D — кости и иммунитет. Дефицит распространен, корректировать по анализу.",
    "b12": "B12 — нервная система. Дефицит: покалывания, слабость. Веганы рискуют больше.",
    "glucose": "Глюкоза натощак — маркер сахара крови. Высокие значения требуют контроля.",
    "hba1c": "HbA1c — средняя глюкоза за 3 мес, важный скрининг.",
    "alt": "АЛТ — фермент печени. Повышение: алкоголь, лекарства, ЖЖП (ожирение печени).",
    "ast": "АСТ — фермент печени/мышц. Оценивать вместе с АЛТ.",
    "ggt": "ГГТ — чувствителен к алкоголю/желчи.",
    "cholesterol": "Холестерин — важны фракции ЛПНП/ЛПВП/ТГ.",
    "ldl": "ЛПНП — «плохой» холестерин. Высокие уровни повышают риск ССЗ.",
    "hdl": "ЛПВП — «хороший» холестерин. Чем выше — лучше.",
    "triglycerides": "Триглицериды — повышаются при избытке сахара/алкоголя.",
    "creatinine": "Креатинин — почки. Оценивать вместе с eGFR.",
    "egfr": "СКФ — функция почек.",
    "uric_acid": "Мочевая кислота — риск подагры при высоких уровнях.",
    "crp": "СРБ — маркер воспаления. Высокие значения указывают на воспаление.",
    "wbc": "Лейкоциты — инфекция/воспаление при повышении.",
    "rbc": "Эритроциты — оцениваются с гемоглобином и Hct.",
    "platelets": "Тромбоциты — свёртывание крови.",
    "iron": "Сывороточное железо — плавает; смотрите ферритин для запасов.",
    "tsh": "ТТГ — скрининг щитовидной железы.",
    "ft4": "Свободный T4 — функция щитовидки.",
    "ft3": "Свободный T3 — активная форма гормонов.",
    "magnesium": "Магний — мышцы и нервная система. Дефицит: судороги.",
    "calcium": "Кальций — кости/нервы. Оценивать с PTH при проблемах.",
    "potassium": "Калий — сердце. Отклонения опасны.",
    "sodium": "Натрий — баланс жидкости.",
    "vitamin_b9": "Фолат — важен при беременности и кроветворении.",
    "coag": "Коагулограмма — свёртывание крови.",
    "alp": "ЩФ — желчные пути и кости.",
    "amylase": "Амилаза — панкреатическая активность.",
    "lipase": "Липаза — панкреатит (более специфична).",
    "omega3": "Индекс омега-3 — маркер насыщенности полезными жирами.",
    "insulin": "Инсулин натощак — оценка инсулинрезистентности.",
    "homocysteine": "Гомоцистеин — сосудистые риски при повышении.",
    "vitamin_b6": "B6 — метаболизм/нервы.",
    "hct": "Гематокрит — % кровяных клеток."
}

# ---------- МЕНЮ ----------
MAIN_KEYBOARD = types.ReplyKeyboardMarkup(resize_keyboard=True, row_width=2)
MAIN_KEYBOARD.add(
    "🏋️ Упражнения",
    "🧘 Медитации",
    "🌀 Йога",
    "🥗 Питание",
    "📊 Анализы",
    "💧 Вода",
    "📈 Биоритмы",
    "ℹ️ Помощь"
)

# Подменю с вариантами количества (быстрое)
DEF_COUNTS_KB = types.ReplyKeyboardMarkup(resize_keyboard=True, row_width=4)
DEF_COUNTS_KB.add("3", "5", "7", "10", "Назад")

# ---------- ХЕПЛЕРЫ (команды) ----------
@bot.message_handler(commands=["start", "help"])
def cmd_start(message):
    text = (
        "Привет! 👋 Я LifeRhythm — твой помощник по здоровью.\n\n"
        "Нажми кнопку раздела или напиши команду:\n"
        "/exercise [N] — тренировки (например /exercise 5)\n"
        "/meditation [N] — дыхание и медитации\n"
        "/yoga [N] — позы йоги\n"
        "/nutrition [N] — советы по питанию\n"
        "/analysis <ключ> — краткая справка по анализу (напр. /analysis ferritin)\n"
        "/water [мл] — отметка воды (по умолчанию 250)\n"
        "/stats — сколько воды сегодня\n"
        "/setdob YYYY-MM-DD — установить дату рождения\n        /biorhythm — показать биоритмы\n"
    )
    bot.send_message(message.chat.id, text, reply_markup=MAIN_KEYBOARD)

@bot.message_handler(commands=["exercise"])
def cmd_exercise(message):
    n = 3
    parts = message.text.split()
    if len(parts) > 1 and parts[1].isdigit():
        n = max(1, min(10, int(parts[1])))
    send_exercises(message.chat.id, n)

@bot.message_handler(commands=["meditation"])
def cmd_meditation(message):
    n = 3
    parts = message.text.split()
    if len(parts) > 1 and parts[1].isdigit():
        n = max(1, min(10, int(parts[1])))
    send_meditations(message.chat.id, n)

@bot.message_handler(commands=["yoga"])
def cmd_yoga(message):
    n = 3
    parts = message.text.split()
    if len(parts) > 1 and parts[1].isdigit():
        n = max(1, min(10, int(parts[1])))
    send_yoga(message.chat.id, n)

@bot.message_handler(commands=["nutrition"])
def cmd_nutrition(message):
    n = 10
    parts = message.text.split()
    if len(parts) > 1 and parts[1].isdigit():
        n = max(5, min(20, int(parts[1])))
    send_nutrition(message.chat.id, n)

@bot.message_handler(commands=["analysis"])
def cmd_analysis(message):
    parts = message.text.split()
    if len(parts) == 1:
        keys = ", ".join(sorted(list(ANALYSIS.keys())))
        bot.send_message(message.chat.id, "Использование: /analysis <ключ>\nНапример: /analysis ferritin\n\nДоступные ключи: " + keys)
        return
    key = parts[1].lower()
    info = ANALYSIS.get(key)
    if not info:
        bot.send_message(message.chat.id, "Не найден ключ. Напиши /analysis list чтобы посмотреть доступные ключи.")
        return
    bot.send_message(message.chat.id, f"🧪 <b>{key}</b>\n{info}\n\n<b>Важно:</b> это ориентиры, не замена врачу.", parse_mode="HTML")

@bot.message_handler(commands=["water"])
def cmd_water(message):
    args = message.text.split()
    ml = 250
    if len(args) > 1 and args[1].isdigit():
        ml = max(50, min(2000, int(args[1])))
    data = load_data()
    uid = str(message.chat.id)
    user = data["users"].setdefault(uid, {})
    water = user.setdefault("water", {})
    day = today_str()
    water[day] = water.get(day, 0) + ml
    save_data(data)
    bot.send_message(message.chat.id, f"💧 Отмечено +{ml} мл. Всего сегодня: {water[day]} мл.")

@bot.message_handler(commands=["stats"])
def cmd_stats(message):
    data = load_data()
    uid = str(message.chat.id)
    water = data["users"].get(uid, {}).get("water", {})
    total = water.get(today_str(), 0)
    bot.send_message(message.chat.id, f"📊 Вода сегодня: {total} мл.")

@bot.message_handler(commands=["setdob"])
def cmd_setdob(message):
    parts = message.text.split()
    if len(parts) < 2:
        bot.send_message(message.chat.id, "Использование: /setdob YYYY-MM-DD")
        return
    val = parts[1]
    try:
        datetime.datetime.strptime(val, "%Y-%m-%d")
    except Exception:
        bot.send_message(message.chat.id, "Неверный формат. Пример: /setdob 1990-08-20")
        return
    data = load_data()
    uid = str(message.chat.id)
    user = data["users"].setdefault(uid, {})
    user["dob"] = val
    save_data(data)
    bot.send_message(message.chat.id, f"✅ Дата рождения сохранена: {val}")

@bot.message_handler(commands=["biorhythm"])
def cmd_biorhythm(message):
    data = load_data()
    uid = str(message.chat.id)
    user = data["users"].get(uid, {})
    dob = user.get("dob")
    if not dob:
        bot.send_message(message.chat.id, "Сначала установи дату рождения: /setdob YYYY-MM-DD")
        return
    dob_date = datetime.datetime.strptime(dob, "%Y-%m-%d").date()
    days = (datetime.date.today() - dob_date).days
    def br(days, period):
        import math
        return int(round((math.sin(2*math.pi*days/period)+1)/2*100))
    physical = br(days, 23)
    emotional = br(days, 28)
    intellectual = br(days, 33)
    txt = f"📈 Биоритмы на {today_str()}:\nФизический: {physical}%\nЭмоциональный: {emotional}%\nИнтеллектуальный: {intellectual}%\n\nЭто развлекательная метрика — ориентируйся на самочувствие."
    bot.send_message(message.chat.id, txt)

# ---------- ФУНКЦИИ ОТПРАВКИ (форматированные) ----------
def format_block(title: str, lines: List[str]) -> str:
    out = f"• {title}\n"
    for i, l in enumerate(lines, 1):
        out += f"  {i}. {l}\n"
    return out

def send_exercises(chat_id: int, n: int):
    items = random.sample(EXERCISES, k=min(n, len(EXERCISES)))
    text = "🏃 Тренировки — выбери комфортный темп и слушай тело.\n\n"
    for it in items:
        text += format_block(it["title"], it["steps"]) + "\n"
    for chunk in split_message(text):
        bot.send_message(chat_id, chunk)

def send_meditations(chat_id: int, n: int):
    items = random.sample(MEDITATIONS, k=min(n, len(MEDITATIONS)))
    text = "🧘 Дыхательные практики и медитации — выполняй в спокойной обстановке.\n\n"
    for it in items:
        text += format_block(it["title"], it["how"]) + "\n"
    for chunk in split_message(text):
        bot.send_message(chat_id, chunk)

def send_yoga(chat_id: int, n: int):
    items = random.sample(YOGA, k=min(n, len(YOGA)))
    text = "🌿 Йога — аккуратно, не форсируй амплитуду.\n\n"
    for it in items:
        text += format_block(it["title"], it["how"]) + "\n"
    for chunk in split_message(text):
        bot.send_message(chat_id, chunk)

def send_nutrition(chat_id: int, n: int):
    items = random.sample(NUTRITION, k=min(n, len(NUTRITION)))
    text = "🥗 Советы по питанию — простые и рабочие.\n\n"
    for i, tip in enumerate(items, 1):
        text += f"{i}. {tip}\n"
    for chunk in split_message(text):
        bot.send_message(chat_id, chunk)

def split_message(text: str, limit: int = 3800) -> List[str]:
    if len(text) <= limit:
        return [text]
    parts = []
    while len(text) > limit:
        cut = text.rfind("\n", 0, limit)
        if cut == -1:
            cut = limit
        parts.append(text[:cut])
        text = text[cut:]
    if text:
        parts.append(text)
    return parts

# ---------- ОБРАБОТЧИК ТЕКСТА (кнопки меню и ответы) ----------
@bot.message_handler(func=lambda m: True)
def all_text_handler(message):
    txt = message.text.strip()
    # Быстрые кнопки: если пользователь нажал кнопку раздела
    if txt == "🏋️ Упражнения":
        # предложим выбрать количество
        kb = types.ReplyKeyboardMarkup(resize_keyboard=True, row_width=4)
        kb.add("3", "5", "7", "10", "Назад")
        bot.send_message(message.chat.id, "Сколько вариантов показать? Нажми число или напиши /exercise N", reply_markup=kb)
        return
    if txt == "🧘 Медитации":
        kb = types.ReplyKeyboardMarkup(resize_keyboard=True, row_width=4)
        kb.add("3", "5", "7", "10", "Назад")
        bot.send_message(message.chat.id, "Сколько практик показать? Нажми число или напиши /meditation N", reply_markup=kb)
        return
    if txt == "🌀 Йога":
        kb = types.ReplyKeyboardMarkup(resize_keyboard=True, row_width=4)
        kb.add("3", "5", "7", "10", "Назад")
        bot.send_message(message.chat.id, "Сколько поз показать? Нажми число или напиши /yoga N", reply_markup=kb)
        return
    if txt == "🥗 Питание":
        kb = types.ReplyKeyboardMarkup(resize_keyboard=True, row_width=4)
        kb.add("5", "10", "15", "20", "Назад")
        bot.send_message(message.chat.id, "Сколько советов показать? Нажми число или напиши /nutrition N", reply_markup=kb)
        return
    if txt == "📊 Анализы":
        bot.send_message(message.chat.id, "Напиши /analysis list для списка ключей или /analysis <ключ> (например /analysis ferritin)")
        return
    if txt == "💧 Вода":
        bot.send_message(message.chat.id, "Отметь воду командой /water [мл], по умолчанию 250 мл. Пример: /water 300")
        return
    if txt == "📈 Биоритмы":
        bot.send_message(message.chat.id, "Установи дату рождения: /setdob YYYY-MM-DD, затем /biorhythm")
        return
    if txt == "ℹ️ Помощь":
        cmd_start(message)
        return
    if txt == "Назад":
        bot.send_message(message.chat.id, "Возврат в меню", reply_markup=MAIN_KEYBOARD)
        return
    # если нажата цифра после запроса
    if txt.isdigit():
        n = int(txt)
        # попробуем угадать что запросили недавно — простая логика: если пользователь просил медитации/упражнения перед этим,
        # но у нас нет состояния диалога — просто спросим, какой раздел. Упростим: покажем все списки с выбранным n — предложим кнопки
        # Реализуем: спросим, что показать (предложим клавиатуру)
        kb = types.ReplyKeyboardMarkup(resize_keyboard=True, row_width=2)
        kb.add(f"Упражнения ×{n}", f"Медитации ×{n}")
        kb.add(f"Йога ×{n}", f"Питание ×{n}")
        kb.add("Назад")
        bot.send_message(message.chat.id, f"Что показать по {n} вариантов?", reply_markup=kb)
        return
    # если пользователь выбрал "Упражнения ×N"
    if txt.startswith("Упражнения ×"):
        try:
            n = int(txt.split("×")[1])
        except:
            n = 3
        send_exercises(message.chat.id, n)
        bot.send_message(message.chat.id, "Возврат в меню", reply_markup=MAIN_KEYBOARD)
        return
    if txt.startswith("Медитации ×"):
        try:
            n = int(txt.split("×")[1])
        except:
            n = 3
        send_meditations(message.chat.id, n)
        bot.send_message(message.chat.id, "Возврат в меню", reply_markup=MAIN_KEYBOARD)
        return
    if txt.startswith("Йога ×"):
        try:
            n = int(txt.split("×")[1])
        except:
            n = 3
        send_yoga(message.chat.id, n)
        bot.send_message(message.chat.id, "Возврат в меню", reply_markup=MAIN_KEYBOARD)
        return
    if txt.startswith("Питание ×"):
        try:
            n = int(txt.split("×")[1])
        except:
            n = 10
        send_nutrition(message.chat.id, n)
        bot.send_message(message.chat.id, "Возврат в меню", reply_markup=MAIN_KEYBOARD)
        return

    # fallback: если введено что-то вроде "/exercise 7" без обработчика выше
    if txt.startswith("/exercise"):
        cmd_exercise(message); return
    if txt.startswith("/meditation"):
        cmd_meditation(message); return
    if txt.startswith("/yoga"):
        cmd_yoga(message); return
    if txt.startswith("/nutrition"):
        cmd_nutrition(message); return
    if txt.startswith("/analysis"):
        cmd_analysis(message); return
    if txt.startswith("/water"):
        cmd_water(message); return
    if txt.startswith("/setdob"):
        cmd_setdob(message); return
    if txt.startswith("/biorhythm"):
        cmd_biorhythm(message); return

    # Если не узнали — подсказка
    bot.send_message(message.chat.id, "Не распознал. Используй меню или команду /help", reply_markup=MAIN_KEYBOARD)

# ---------- FLASK WEBHOOK ----------
@app.route("/")
def index():
    return "LifeRhythm Bot — running", 200

@app.route(WEBHOOK_PATH, methods=["POST"])
def webhook():
    data = request.get_json(force=True, silent=True)
    if not data:
        return jsonify({"ok": False, "error": "no json"}), 400
    update = telebot.types.Update.de_json(data)
    bot.process_new_updates([update])
    return jsonify({"ok": True})

# ---------- СТАРТ (устанавливаем webhook при запуске) ----------
def set_webhook():
    try:
        bot.remove_webhook()
    except Exception:
        pass
    res = bot.set_webhook(url=WEBHOOK_URL)
    print("Webhook set:", res, WEBHOOK_URL)

if __name__ == "__main__":
    print("Setting webhook:", WEBHOOK_URL)
    set_webhook()
    # Flask встроенный сервер — в Render мы запускаем через gunicorn (Procfile или Start Command),
    # но для локального теста можно использовать app.run:
    app.run(host="0.0.0.0", port=PORT)
