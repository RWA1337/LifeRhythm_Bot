import os
import threading
import random
import math
from datetime import datetime, date
from typing import Dict, Any, List

from flask import Flask
from telegram import Update
from telegram.ext import Application, CommandHandler, ContextTypes

# ======== Настройки окружения ========
BOT_TOKEN = os.getenv("BOT_TOKEN")
if not BOT_TOKEN or not BOT_TOKEN.strip():
    raise RuntimeError("Переменная окружения BOT_TOKEN не задана. Укажи её в Render → Environment.")

# ======== Хранилище пользователей (память) ========
USERS: Dict[int, Dict[str, Any]] = {}

def u(user_id: int) -> Dict[str, Any]:
    """Ленивая инициализация пользовательского словаря."""
    if user_id not in USERS:
        USERS[user_id] = {
            "name": None,
            "sex": None,         # 'м' или 'ж'
            "height": None,      # см
            "weight": None,      # кг
            "dob": None,         # YYYY-MM-DD
            "goal": None,        # цель: похудение/здоровье/...
            "water_total": 0,    # мл за сегодня
            "water_day": date.today().isoformat(),
        }
    # сброс воды при смене дня
    if USERS[user_id]["water_day"] != date.today().isoformat():
        USERS[user_id]["water_day"] = date.today().isoformat()
        USERS[user_id]["water_total"] = 0
    return USERS[user_id]

# ======== Утилиты ========
TG_LIMIT = 4096
def chunk_text(s: str, limit: int = TG_LIMIT) -> List[str]:
    parts = []
    while len(s) > limit:
        cut = s.rfind("\n", 0, limit)
        if cut == -1:
            cut = limit
        parts.append(s[:cut])
        s = s[cut:]
    if s:
        parts.append(s)
    return parts

async def send_long(update: Update, text: str):
    for part in chunk_text(text):
        await update.message.reply_text(part)

def parse_kv(args: List[str]) -> Dict[str, str]:
    out = {}
    for token in args:
        if "=" in token:
            k, v = token.split("=", 1)
            out[k.strip().lower()] = v.strip()
    return out

def pick_many(pool: List[str], count: int) -> List[str]:
    count = max(1, min(count, len(pool)))
    return random.sample(pool, count)

# ======== ДАННЫЕ (сжатые, но дают сотни уникальных комбинаций) ========

EXERCISE_BLOCKS = {
    "зарядка": [
        "Прыжки на месте 30 сек",
        "Круговые махи руками 20 сек",
        "Приседания 15 раз",
        "Отжимания от стены 12 раз",
        "Планка 30 сек",
        "Выпады на месте 10/10",
        "Скручивания лёжа 15 раз",
        "Берпи без прыжка 8 раз",
        "Ягодичный мост 15 раз",
        "Подъём колен к груди стоя 20 сек",
        "Боковая планка 20/20 сек",
        "Растяжка шейного отдела 30 сек",
        "Кошка-корова 8 циклов",
        "Наклоны корпуса 12 раз",
        "Пружинистые выпады 8/8",
        "Прыжки «звезда» 20 сек",
        "Супермен 12 раз",
        "Диагональные скручивания 12/12",
        "Подъём на носки 20 раз",
        "Растяжка квадрицепса 20/20 сек",
    ],
    "похудение": [
        "Берпи 10 раз",
        "Прыжки с разведением рук 30 сек",
        "Скейт-перемахи 30 сек",
        "Горизонтальный бег (горка) 30 сек",
        "Присед + прыжок 12 раз",
        "Альпинист 30 сек",
        "Русские скручивания 20 раз",
        "Жим от пола на коленях 12 раз",
        "Выпады назад 12/12",
        "Планка + касание плеч 20 раз",
        "Сумо-присед 15 раз",
        "Джампинг-джек 30 сек",
        "Скакалка (без скакалки) 45 сек",
        "Сайд-шаги с приседом 30 сек",
        "Боковые выпады 12/12",
        "Супермен удержание 30 сек",
        "Косые скручивания 15/15",
        "Мёртвый жук 20 раз",
        "Планка 45 сек",
        "Прыжки вперёд-назад 30 сек",
    ],
    "выносливость": [
        "Интервальный бег на месте 40/20 сек × 4",
        "Сайд-шаги быстрые 45 сек",
        "Альпинист 40 сек",
        "Скейт-перемахи 40 сек",
        "Берпи 8–12 раз",
        "Высокие колени 40 сек",
        "Планка 60 сек",
        "Джампинг-джек 45 сек",
        "Бёрд-дог 20/20",
        "Подъём колен сидя 30 раз",
        "Лягушка 15 раз",
        "Прыжки в выпады 10/10",
        "Болгарские выпады (опора) 12/12",
        "Приседания 20 раз",
        "Отжимания 10–15",
        "Скручивания 25",
        "Сумо-пульс 20 раз",
        "Бег на месте 2 мин",
        "Прыжки на одной ноге 20/20",
        "Планка с шагами 40 сек",
    ],
    "спина": [
        "Супермен 15 раз",
        "Ягодичный мост 15–20",
        "Бёрд-дог 12/12",
        "Тяга полотенца (изометрика) 30 сек",
        "Разведение рук лёжа 15",
        "Планка на предплечьях 30–45 сек",
        "Кобра 20–30 сек",
        "Лодочка 20–30 сек",
        "Растяжка кошка-корова 10 циклов",
        "Подтягивание лопаток лёжа 12",
        "Верхняя планка 30 сек",
        "Отведение ног в упоре 12/12",
        "Развороты корпуса 12/12",
        "Махи назад стоя 15/15",
        "Боковая планка 20/20",
    ],
    "офис": [
        "Круги плечами 10/10",
        "Растяжка трапеций 20/20 сек",
        "Наклоны головы 5 направлений",
        "Сжатие лопаток 12 раз",
        "Скручивание сидя 20/20 сек",
        "Подъём колен к груди сидя 12/12",
        "Встать/сесть 15 раз",
        "Отжимания от стола 12",
        "Кистевой «намот» 12/12",
        "Растяжка сгибателей бедра 20/20 сек",
        "Стоя на носках 20",
        "Баланс на одной ноге 20/20 сек",
        "Планка у стола 30 сек",
        "Лопаточная тяга к столу (изо) 30 сек",
        "Мобилизация грудного отдела 10",
    ]
}

YOGA_POSES = [
    "Тадасана (Гора) — выпрямись, макушка вверх",
    "Врикшасана (Дерево) — баланс на одной ноге",
    "Адо Мукха Шванасана (Пёс мордой вниз) — вытяжение спины",
    "Баласана (Поза ребёнка) — расслабление",
    "Бхуджангасана (Кобра) — мягкий прогиб",
    "Уттанасана — наклон вперёд стоя",
    "Вирабхадрасана I — выпад, руки вверх",
    "Вирабхадрасана II — выпад, руки в стороны",
    "Триконасана — треугольник, вытяжение боков",
    "Паванмуктасана — колени к груди лёжа",
    "Сету Бандхасана — полумост",
    "Джатхара Паривартанасана — скрутка лёжа",
    "Марджариасана — кошка-корова (мягко)",
    "Паршвоттанасана — наклон к прямой ноге",
    "Супта Баддха Конасана — лёжа, стопы вместе",
    "Апанаcана — подтягивание коленей по одному",
    "Маласана — глубокий присед-растяжка",
    "Арда Матсиендрасана — скрутка сидя",
    "Прасарита Падоттанасана — наклон, ноги широко",
    "Гомукхасана руки — плечевой пояс",
    "Сфинкс — мягкий прогиб лёжа",
    "Ардха Хануманасана — полушпагат",
    "Ардха Чандрасана — полумесяц (со стеной)",
    "Випарита Карани — ноги на стену",
    "Супта Мацйендрасана — скрутка лёжа",
    "Ананд Баласана — счастливый ребёнок",
    "Пашчимоттанасана — наклон сидя",
    "Дандасана — посох (осанка)",
    "Урдхва Хастасана — вытяжение вверх",
    "Шавасана — расслабление 3–5 мин",
]

BREATH_MEDIT = {
    "дыхание": [
        "Коэрентное дыхание 5-5 (вдох 5с / выдох 5с) 5–10 мин",
        "Box 4-4-4-4 (вдох-задержка-выдох-задержка) по 4с, 3–5 мин",
        "4-7-8 (вдох 4с / задержка 7с / выдох 8с) 2–4 мин",
        "Диафрагмальное (животом) 6–10 мин",
        "Уджаи мягкое 3–7 мин",
        "Нади Шодхана (поочерёдные ноздри) 3–6 мин",
        "Дыхание по счёту 1→10 (цикл) 5 мин",
        "Удлинённый выдох 4/6 → 4/8, 5–7 мин",
        "Резонансное 6 дыханий/мин 5 мин",
        "Пейсинг с шагами (вдох 3 шага/выдох 4 шага) 5–10 мин",
        "Сканирование дыхания (mindful) 5 мин",
        "«Соломинка» — узкий выдох, 3–5 мин",
        "Через нос-рот (очищающее) 3–5 мин",
        "1:2 (вдох:выдох) 4→8, 5 мин",
        "С квадратом 5-5-5-5, 5–10 мин",
        "С удержанием низа живота 3–5 мин",
        "С мягкой капхалабхати (осторожно) 1–2 мин",
        "Дыхание с метрикой 3-3-6, 4–5 мин",
        "Дыхание перед сном 4-6, 5 мин",
        "Дыхание «волнa» (грудь-живот) 5 мин",
    ],
    "медитация": [
        "Сканирование тела 5–10 мин",
        "Осознанность на дыхании 5–10 мин",
        "Метта (доброта) 5 мин",
        "5 ощущений (слух/зрение/осязание/вкус/запах) 5 мин",
        "Отслеживание мыслей как облаков 5–10 мин",
        "Якорь на звуке/таймере 5–8 мин",
        "Медленная прогулка mindfulness 10 мин",
        "Короткая благодарность 3 мин",
        "Визуализация «спокойное место» 5–8 мин",
        "3-минутная пауза (STOP) 3 мин",
        "Медитация перед сном 6–10 мин",
        "Заземление через ощущения стоп 5 мин",
        "Созерцание пламени (тратак) 3–5 мин",
        "Мягкая мантра (мысленно) 5–8 мин",
        "Ненапряжное присутствие «просто быть» 5–10 мин",
    ]
}

NUTRITION_TIPS_BASE = [
    "Пей воду: цель 30–35 мл/кг/сутки.",
    "Каждый приём пищи — источник белка (рыба/яйца/птица/творог/бобовые).",
    "Овощи 400–600 г/день, добавляй к каждому приёму.",
    "Цельнозерновые лучше рафинированных.",
    "Сладкие напитки → исключить, десерты → по праздникам.",
    "Жиры: оливковое/льняное/орехи/авокадо; меньше транс-жиров.",
    "Завтрак с белком (20–30 г) — меньше перекусов днём.",
    "Планируй тарелку: ½ овощи, ¼ белок, ¼ сложные углеводы.",
    "Ферментированные продукты (кефир/йогурт без сахара, квашеные).",
    "Соль ≤5 г/сутки, при гипертонии — меньше.",
    "Алкоголь — лучше исключить.",
    "Порции измеряй руками: белок — ладонь, углеводы — кулак, жир — большой палец.",
    "Клетчатка 25–35 г/сутки (овощи, ягоды, отруби).",
    "Ешь не спеша: 15–20 минут на приём пищи.",
    "Последний приём за 2–3 часа до сна.",
    "Баланс по неделе важнее идеальности каждого дня.",
    "Контролируй добавленные сахара (<25–36 г/сутки).",
    "Неделя — меню, день — список покупок.",
    "Снэки: йогурт без сахара, творог, орехи 20–30 г, яйцо, яблоко.",
    "Следи за железом/витамином D у групп риска (по анализам и врачу).",
    "Белок 1.2–1.6 г/кг (при похудении) — ориентир.",
    "Поддерживай шаги/активность — это влияет на аппетит.",
    "Готовь большими партиями и замораживай.",
    "Контролируй кофеин после 15:00 при проблемах со сном.",
    "Добавляй специи: корица, куркума, чеснок — польза и вкус.",
    "Не ешь «из эмоций» — замени ритуалом (чай/прогулка).",
    "Углеводы ближе к тренировке/после неё — ок.",
    "При похудении: дефицит 10–20% от поддерживающих калорий.",
    "Старайся получать витамины из еды; добавки — по показаниям врача.",
    "Не наказывай себя — одна «ошибка» ничего не ломает.",
]

RECIPES = {
    "низкокал": [
        "Омлет из 2 яиц с шпинатом и томатами (~220 ккал, БЖУ≈20/12/6)",
        "Куриная грудка на гриле + салат (оливк. масло 1 ч.л.) (~300 ккал, 35/10/8)",
        "Творог 150 г + ягоды 100 г (~220 ккал, 20/5/20)",
        "Лосось в духовке 120 г + брокколи (~320 ккал, 30/18/8)",
        "Суп-пюре из тыквы с йогуртом (~250 ккал, 8/8/30)",
        "Греческий салат (без хлеба) (~280 ккал, 10/18/16)",
        "Тунец + огурец + йогурт со специями (~250 ккал, 30/6/10)",
        "Индейка тушёная + цветная капуста (~300 ккал, 32/12/10)",
        "Фриттата овощная (~260 ккал, 16/14/18)",
        "Запечённые овощи + фета 40 г (~280 ккал, 10/16/20)",
    ],
    "баланс": [
        "Гречка 60 г (сух.) + кур. бедро 120 г + салат (~520 ккал, 35/18/55)",
        "Рис басмати 60 г + лосось 120 г + овощи (~560 ккал, 32/22/55)",
        "Паста цельнозерн. 70 г + томатный соус + моцарелла 40 г (~550 ккал, 22/17/70)",
        "Лаваш цельнозерн. + хумус + овощи + курица (~500 ккал, 35/14/55)",
        "Чили с индейкой и фасолью (~540 ккал, 38/16/60)",
        "Плов «лайт»: рис+индейка+овощи (~560 ккал, 32/16/70)",
        "Буррито-боул: рис+чёрная фасоль+курица (~580 ккал, 35/14/75)",
        "Карри из нута с рисом (~520 ккал, 16/14/80)",
        "Соба + тофу + овощи (~520 ккал, 24/16/70)",
        "Поке-боул: рис+рыба+овощи (~560 ккал, 28/18/70)",
    ],
    "масса": [
        "Овсянка 80 г + молоко + банан + арах. паста (~650 ккал, 20/22/90)",
        "Паста + тунец + оливк. масло (~700 ккал, 28/26/90)",
        "Рис + говядина + авокадо (~720 ккал, 35/28/80)",
        "Тортилья с курицей, сыром и овощами (~680 ккал, 40/22/75)",
        "Смузи: молоко+банан+творог+овсянка+мёд (~650 ккал, 35/10/95)",
        "Булгур + лосось + тахини (~720 ккал, 35/30/75)",
        "Картофель печёный + творог + лосось (~680 ккал, 35/22/80)",
        "Омлет 3 яйца + сыр + тост цельнозерн. (~650 ккал, 35/38/30)",
        "Кускус + баранина + овощи (~700 ккал, 35/25/85)",
        "Чечевица + курица + оливк. масло (~680 ккал, 45/18/70)",
    ]
}

ANALYSIS_INFO = {
    "гемоглобин": "Норма ~130–170 г/л (м), 120–150 г/л (ж). Низкий — возможен дефицит железа/кровопотеря; высокий — обезвоживание/гипоксия. Обсуди с врачом.",
    "ферритин": "Склад железа. Ориентир ~30–300 нг/мл (разброс), ниже 30 — часто дефицит запасов. Интерпретация у врача.",
    "железо": "Сывороточное железо колеблется; оценивай вместе с ферритином/ОЖСС/ТЖСС.",
    "витамин_d": "25(OH)D: дефицит <20 нг/мл, недостаточность 20–30, цель 30–50. Дозировки — только по врачу.",
    "ттг": "Щитовидка: реф. ~0.4–4.0 мЕд/л. Повышен — часто гипофункция, снижен — гиперфункция. Нужна очная оценка.",
    "глюкоза": "Натощак ~3.9–5.5 ммоль/л. Выше — пересдать/консультация.",
    "hba1c": "Гликированный Hb: <5.7% норма, 5.7–6.4 преддиабет, ≥6.5 диабет (по критериям). Уточняй у врача.",
    "лдл": "«Плохой» холестерин; чем ниже, тем лучше при рисках. Целевые — индивидуальны.",
    "hdl": "«Хороший» холестерин; выше — лучше (в разумных пределах).",
    "триглицериды": "Высокие ТГ — риск метаболических нарушений; цель <1.7 ммоль/л.",
    "алт": "Печёночные ферменты: АЛТ/АСТ повышены — повод к оценке печени.",
    "аст": "Смотри комментарий к АЛТ; соотношение тоже важно.",
    "билирубин": "Высокий — возможны проблемы оттока/печени/гемолиз; интерпретация у врача.",
    "креатинин": "Оценка почек; с ростом креатинина падает СКФ.",
    "мочевина": "Обмен белка/почечная функция; смотри в комплексе.",
    "crp": "С-реактивный белок: маркёр воспаления/риска; оценка динамики у врача.",
    "соэ": "Неспецифично; повышено при воспалении/анемии и др.",
    "лейкоциты": "Иммунитет; высокие — инфекция/воспаление; низкие — разные причины.",
    "тромбоциты": "Свертывание; и высокие, и низкие требуют оценки.",
    "эритроциты": "Переносят кислород; смотри с Hb/гематокритом.",
    "гематокрит": "Доля форменных элементов; влияет гидратация.",
    "магний": "Дефицит — судороги/утомляемость; но интерпретация сложна.",
    "калий": "Сердце/мышцы; и низкий, и высокий опасны — срочно к врачу при симптомах.",
    "натрий": "Водный баланс; отклонения — к врачу.",
}

# ======== Команды ========

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = u(update.effective_user.id)
    name = user["name"] or update.effective_user.first_name
    text = (
        f"👋 Привет, {name}!\n"
        "Я LifeRhythm — твой ассистент по здоровью и энергии.\n\n"
        "Попробуй:\n"
        "• /set name=Иван height=180 weight=82 sex=м dob=1992-05-12 goal=похудение\n"
        "• /water 300 — отметить воду\n"
        "• /exercise goal=зарядка level=новичок count=8\n"
        "• /yoga level=новичок count=6\n"
        "• /meditation type=дыхание count=6\n"
        "• /nutrition goal=здоровье count=10\n"
        "• /recipes goal=низкокал count=6\n"
        "• /analysis витамин_d\n"
        "• /biorhythm — расчет по дате рождения\n"
        "• /idealweight — ИМТ и диапазоны\n"
        "• /status — сводка за сегодня"
    )
    await send_long(update, text)

async def help_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await start(update, context)

async def status(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = u(update.effective_user.id)
    text = (
        "📊 Статус:\n"
        f"Имя: {user['name']}\n"
        f"Пол: {user['sex']}\n"
        f"Рост: {user['height']} см\n"
        f"Вес: {user['weight']} кг\n"
        f"Цель: {user['goal']}\n"
        f"ДР: {user['dob']}\n"
        f"Вода сегодня: {user['water_total']} мл\n"
        "Команды: /set /water /exercise /yoga /meditation /nutrition /recipes /analysis /biorhythm /idealweight"
    )
    await update.message.reply_text(text)

async def set_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = u(update.effective_user.id)
    data = parse_kv(context.args)
    mapping = {
        "name": "name",
        "sex": "sex",
        "пол": "sex",
        "height": "height",
        "рост": "height",
        "weight": "weight",
        "вес": "weight",
        "dob": "dob",
        "др": "dob",
        "goal": "goal",
        "цель": "goal",
    }
    applied = []
    for k, v in data.items():
        key = mapping.get(k)
        if not key:
            continue
        if key in ("height", "weight"):
            try:
                user[key] = int(v)
            except:
                continue
        else:
            user[key] = v
        applied.append(f"{key}={user[key]}")
    if applied:
        await update.message.reply_text("✅ Обновлено: " + ", ".join(applied))
    else:
        await update.message.reply_text("Использование: /set name=Иван height=180 weight=82 sex=м dob=1992-05-12 goal=похудение")

async def water(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = u(update.effective_user.id)
    amount = 250
    if context.args:
        try:
            amount = int(context.args[0])
        except:
            pass
    user["water_total"] += max(0, amount)
    target = 2000
    await update.message.reply_text(f"💧 Отмечено {amount} мл. Всего сегодня: {user['water_total']} мл (цель ~{target} мл).")

def build_exercise_text(goal: str, level: str, count: int) -> str:
    goal = goal or "зарядка"
    pool = EXERCISE_BLOCKS.get(goal, [])
    if not pool:
        all_blocks = sum(EXERCISE_BLOCKS.values(), [])
        chosen = pick_many(all_blocks, count)
    else:
        chosen = pick_many(pool, min(count, len(pool)))
    title = f"🏃 Тренировка — {goal.capitalize()}, уровень: {level or 'любой'}"
    lines = [f"{i+1}. {ex}" for i, ex in enumerate(chosen)]
    lines.append("⏱ Отдых 30–45 сек между упражнениями. 2–3 круга.")
    return title + "\n" + "\n".join(lines)

async def exercise(update: Update, context: ContextTypes.DEFAULT_TYPE):
    # параметры: goal=..., level=..., count=...
    params = parse_kv(context.args)
    goal = params.get("goal")
    level = params.get("level", "новичок")
    try:
        count = int(params.get("count", "8"))
    except:
        count = 8
    text = build_exercise_text(goal, level, count)
    await send_long(update, text)

async def yoga(update: Update, context: ContextTypes.DEFAULT_TYPE):
    params = parse_kv(context.args)
    try:
        count = int(params.get("count", "6"))
    except:
        count = 6
    poses = pick_many(YOGA_POSES, min(count, len(YOGA_POSES)))
    title = f"🧘 Йога/растяжка — {params.get('level','новичок')}"
    text = title + "\n" + "\n".join(f"{i+1}. {p}" for i, p in enumerate(poses)) + "\n" + "Дыши спокойно, без боли."
    await send_long(update, text)

async def meditation(update: Update, context: ContextTypes.DEFAULT_TYPE):
    params = parse_kv(context.args)
    typ = params.get("type", "дыхание")
    try:
        count = int(params.get("count", "6"))
    except:
        count = 6
    pool = BREATH_MEDIT.get(typ, BREATH_MEDIT["дыхание"])
    chosen = pick_many(pool, min(count, len(pool)))
    title = f"🧠 {typ.capitalize()} — подборка"
    text = title + "\n" + "\n".join(f"{i+1}. {p}" for i, p in enumerate(chosen))
    await send_long(update, text)

async def nutrition(update: Update, context: ContextTypes.DEFAULT_TYPE):
    params = parse_kv(context.args)
    try:
        count = int(params.get("count", "12"))
    except:
        count = 12
    tips = pick_many(NUTRITION_TIPS_BASE, min(count, len(NUTRITION_TIPS_BASE)))
    head = f"🥗 Советы по питанию — {params.get('goal','общие')}"
    await send_long(update, head + "\n" + "\n".join(f"• {t}" for t in tips))

async def recipes(update: Update, context: ContextTypes.DEFAULT_TYPE):
    params = parse_kv(context.args)
    goal = params.get("goal", "низкокал")
    try:
        count = int(params.get("count", "6"))
    except:
        count = 6
    pool = RECIPES.get(goal, RECIPES["низкокал"])
    chosen = pick_many(pool, min(count, len(pool)))
    head = f"🍽 Рецепты ({goal})"
    await send_long(update, head + "\n" + "\n".join(f"{i+1}. {r}" for i, r in enumerate(chosen)))

async def analysis(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not context.args:
        keys = ", ".join(sorted(ANALYSIS_INFO.keys())[:12]) + ", ..."
        await update.message.reply_text(f"Использование: /analysis показатель\nНапр.: /analysis витамин_d\nДоступно: {keys}")
        return
    key = " ".join(context.args).strip().lower()
    key = key.replace(" ", "_")
    info = ANALYSIS_INFO.get(key)
    if info:
        await update.message.reply_text(f"🧪 {key.replace('_',' ').title()}:\n{info}\n\nЭто не диагноз — интерпретация с лечащим врачом.")
    else:
        await update.message.reply_text("Пока нет справки по этому показателю. Попробуй другой (vitamin_d → «витамин_d»).")

def calc_biorhythm(dob: str, on_date: date) -> str:
    try:
        bd = datetime.strptime(dob, "%Y-%m-%d").date()
    except:
        return "Укажи дату рождения через /set dob=YYYY-MM-DD"
    days = (on_date - bd).days
    def phase(period):
        return math.sin(2 * math.pi * days / period)
    def pct(x):  # -100..100
        return int(round(x * 100))
    phys = pct(phase(23))
    emot = pct(phase(28))
    intel = pct(phase(33))
    return (f"📈 Биоритмы на {on_date.isoformat()}:\n"
            f"Физический: {phys:+d}%\n"
            f"Эмоциональный: {emot:+d}%\n"
            f"Интеллектуальный: {intel:+d}%\n"
            "Это развлекательная метрика, используй с разумом 😉")

async def biorhythm(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = u(update.effective_user.id)
    if not user["dob"]:
        await update.message.reply_text("Сначала установи дату рождения: /set dob=YYYY-MM-DD")
        return
    today = date.today()
    await update.message.reply_text(calc_biorhythm(user["dob"], today))

async def idealweight(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = u(update.effective_user.id)
    h = user["height"]
    w = user["weight"]
    if not h or not w:
        await update.message.reply_text("Укажи рост и вес: /set height=180 weight=82")
        return
    h_m = h / 100.0
    bmi = w / (h_m ** 2)
    # Диапазоны ВОЗ
    cat = ("Недостаточный вес" if bmi < 18.5 else
           "Нормальный вес" if bmi < 25 else
           "Избыточный" if bmi < 30 else
           "Ожирение")
    # Простейшая «идеалка» Девина/Брока (условно)
    brock = (h - 100) * (0.9 if user["sex"] == "м" else 0.85)
    text = (
        f"📏 Рост: {h} см, Вес: {w} кг\n"
        f"ИМТ: {bmi:.1f} — {cat}\n"
        f"Ориентир «идеального» по Броку: ~{brock:.0f} кг (очень грубо)\n"
        "Это оценка для ориентира. Решения — с врачом/тренером."
    )
    await update.message.reply_text(text)

# ======== Flask keep-alive (для Render free) ========
app_web = Flask(__name__)

@app_web.route("/")
def root():
    return "LifeRhythm: OK"

@app_web.route("/healthz")
def healthz():
    return "ok"

def run_flask():
    port = int(os.getenv("PORT", "10000"))
    app_web.run(host="0.0.0.0", port=port)

# ======== Запуск PTB v21 ========
def run_bot():
    application = Application.builder().token(BOT_TOKEN).build()
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("help", help_cmd))
    application.add_handler(CommandHandler("status", status))
    application.add_handler(CommandHandler("set", set_cmd))
    application.add_handler(CommandHandler("water", water))
    application.add_handler(CommandHandler("exercise", exercise))
    application.add_handler(CommandHandler("yoga", yoga))
    application.add_handler(CommandHandler("meditation", meditation))
    application.add_handler(CommandHandler("nutrition", nutrition))
    application.add_handler(CommandHandler("recipes", recipes))
    application.add_handler(CommandHandler("analysis", analysis))
    application.add_handler(CommandHandler("biorhythm", biorhythm))
    application.add_handler(CommandHandler("idealweight", idealweight))
    application.run_polling(close_loop=False)

if __name__ == "__main__":
    threading.Thread(target=run_flask, daemon=True).start()
    run_bot()
