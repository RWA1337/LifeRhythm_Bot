import os
import math
import random
import asyncio
from datetime import datetime, date
from typing import List, Dict

from flask import Flask, request, jsonify

from telegram import Update, Bot
from telegram.constants import ParseMode
from telegram.ext import (
    Application, ApplicationBuilder, CommandHandler, CallbackContext
)

# ================================
# --------- КОНФИГ --------------
# ================================
BOT_TOKEN = os.environ.get("BOT_TOKEN")
PUBLIC_URL = os.environ.get("PUBLIC_URL", "").rstrip("/")

if not BOT_TOKEN:
    raise RuntimeError("Не установлен BOT_TOKEN в переменных окружения Render.")
if not PUBLIC_URL:
    raise RuntimeError("Не установлен PUBLIC_URL (например, https://liferhythm-bot.onrender.com).")

TELEGRAM_WEBHOOK_PATH = "/webhook"
TELEGRAM_WEBHOOK_URL = f"{PUBLIC_URL}{TELEGRAM_WEBHOOK_PATH}"

PORT = int(os.environ.get("PORT", "10000"))

# ================================
# --------- ДАННЫЕ --------------
# ================================

# Хранилища в памяти (для Free-инстансов этого достаточно; при слипе Render это сбрасывается)
WATER_STATE: Dict[int, Dict[str, int]] = {}   # user_id -> { 'YYYY-MM-DD': ml_int }
DOB_STATE: Dict[int, str] = {}                 # user_id -> 'YYYY-MM-DD'

# Утилита безопасного парсинга числа из аргументов
def parse_n(args: List[str], default: int, min_v: int, max_v: int) -> int:
    if not args:
        return default
    try:
        n = int(args[0])
        return max(min_v, min(max_v, n))
    except Exception:
        return default

def chunk_text(text: str, limit: int = 3900) -> List[str]:
    # Делит длинные сообщения на части, чтобы не упереться в лимит Telegram
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

# -------------------------------
# БОЛЬШИЕ НАБОРЫ КОНТЕНТА
# -------------------------------

EXERCISES = [
    # 24 коротких комплексов (домашняя зарядка/функционал)
    {"title": "Разминка-5", "steps": [
        "Круговые движения плеч: 30 сек",
        "Повороты корпуса: 30 сек",
        "Приседания: 15 раз",
        "Планка: 30 сек",
        "Лёгкий бег на месте: 60 сек",
    ]},
    {"title": "Функциональный-7", "steps": [
        "Прыжки на месте: 30 сек",
        "Приседания: 20 раз",
        "Отжимания от стены: 12 раз",
        "Скручивания лёжа: 20 раз",
        "Планка боковая (каждая сторона): 20 сек",
        "Выпады на месте: 10/10",
        "Ходьба высоко поднимая колени: 60 сек",
    ]},
    {"title": "Быстрый тонус", "steps": [
        "Джампинг-джек: 30 сек",
        "Присед + подъём рук: 12 раз",
        "Отжимания коленях: 10 раз",
        "Гиперэкстензия лёжа: 15 раз",
        "Планка: 40 сек",
    ]},
    {"title": "Круг-10 минут", "steps": [
        "Круг из 5 упражнений по 40 сек/20 сек отдых: присед, отжим, планка, выпады, скручивания. Повторить 2 круга",
    ]},
    {"title": "Кардио-легко", "steps": [
        "Бег на месте: 60 сек",
        "Прыжки: 30 сек",
        "Шаги в стороны с хлопком: 60 сек",
        "Ходьба восстанавливающая: 60 сек",
        "Повторить весь блок 2 раза",
    ]},
    {"title": "Сила базовая", "steps": [
        "Приседания: 3×12",
        "Отжимания от стула: 3×8",
        "Ягодичный мост: 3×15",
        "Планка: 3×30 сек",
    ]},
    {"title": "Спина и пресс", "steps": [
        "Лодочка: 3×20 сек",
        "Супермен: 3×12",
        "Скручивания: 3×15",
        "Планка: 3×30 сек",
    ]},
    {"title": "Ноги и равновесие", "steps": [
        "Выпады: 3×10/10",
        "Ягодичный мост: 3×15",
        "Присед узкий/широкий: 10+10",
        "Баланс на одной ноге: 2×30 сек/нога",
    ]},
    {"title": "Мобилити-колени/таз", "steps": [
        "Круги тазом: 30 сек",
        "Растяжка квадрицепса: 30 сек/нога",
        "Растяжка задней поверхности бедра: 30 сек/нога",
        "Присед с удержанием: 20 сек",
    ]},
    {"title": "Офис-5 минут", "steps": [
        "Круги шеей: 20 сек",
        "Сведение/разведение лопаток: 30 сек",
        "Наклоны вперёд: 10 раз",
        "Растяжка запястий: 30 сек",
        "Ходьба: 60 сек",
    ]},
    {"title": "Утро-энергия", "steps": [
        "Потягивания стоя: 30 сек",
        "Присед + подъём на носки: 12 раз",
        "Планка: 30 сек",
        "Дыхание 4-2-6: 1 мин",
    ]},
    {"title": "Вечер-расслабление", "steps": [
        "Мягкие наклоны: 10 раз",
        "Кошка-корова: 8 раз",
        "Поза ребёнка: 60 сек",
        "Лёгкая планка: 20 сек",
    ]},
    {"title": "HIIT-лайт", "steps": [
        "30 сек работа / 30 сек отдых × 10: бег на месте, присед-прыжок (если можно), отжимания, альпинист, джампинг-джек",
    ]},
    {"title": "Кор-центр", "steps": [
        "Планка локти: 3×30 сек",
        "Велосипед: 3×20",
        "Ножницы: 3×20",
        "Боковая планка: 2×20 сек/сторона",
    ]},
    {"title": "Грудь/трицепс", "steps": [
        "Отжимания от стены/колен: 3×10",
        "Отжимания узкие: 2×8",
        "Задние отжимания от стула: 3×8",
        "Растяжка груди: 30 сек",
    ]},
    {"title": "Спина/бицепс без инвентаря", "steps": [
        "Тяга полотенца (изометрия): 3×20 сек",
        "Сведение лопаток лёжа: 3×12",
        "Супермен: 3×12",
        "Растяжка спины: 30 сек",
    ]},
    {"title": "Плечи/стабилизация", "steps": [
        "Круги руками: 30 сек",
        "Y-T-W изометрия: 3×8",
        "Планка с касанием плеч: 3×12",
    ]},
    {"title": "Ноги—быстрый тонус", "steps": [
        "Присед: 3×15",
        "Выпады назад: 3×10/10",
        "Подъёмы на носки: 3×20",
        "Изометрия — стенка: 2×30 сек",
    ]},
    {"title": "Кардио-лестница", "steps": [
        "40 сек бег — 20 сек отдых",
        "50 сек бег — 25 сек отдых",
        "60 сек бег — 30 сек отдых",
        "Повторить цикл 2 раза",
    ]},
    {"title": "Растяжка после дня", "steps": [
        "Икры у стены: 30 сек/нога",
        "Квадрицепс стоя: 30 сек/нога",
        "Бёдра и ягодицы: 30 сек/нога",
        "Поясница лёжа повороты: 30 сек/сторона",
    ]},
    {"title": "Колени—бережно", "steps": [
        "Мобилити голеностоп: 30 сек/нога",
        "Полуприсед со стулом: 3×10",
        "Шаг в сторону с резинкой/без: 3×12/12",
        "Растяжка квадрицепса: 30 сек/нога",
    ]},
    {"title": "Шея/осанка", "steps": [
        "Подбородок к горлу (чайн-тук): 3×10",
        "Потягивание макушкой: 3×20 сек",
        "Сведение лопаток: 3×12",
        "Растяжка трапеций: 30 сек/сторона",
    ]},
    {"title": "5х5 минут (на день)", "steps": [
        "Каждые 2–3 часа: 5 минут — 1 мин ходьба, 1 мин присед, 1 мин планка, 1 мин дыхание, 1 мин растяжка",
    ]},
    {"title": "Лимфа/разогрев", "steps": [
        "Потряхивание кистями/стопами: 60 сек",
        "Похлопывания по телу: 60 сек",
        "Прыжки лёгкие: 30 сек",
        "Дыхание 4-4-4: 1 мин",
    ]},
]

MEDITATIONS = [
    {"title": "Дыхание 4–4–4 (бокc-бриз)", "how": [
        "Вдох на 4 счета", "Задержка на 4", "Выдох на 4", "Задержка на 4", "5–8 циклов"
    ]},
    {"title": "4–7–8", "how": [
        "Вдох 4", "Задержка 7", "Выдох 8", "4–6 циклов"
    ]},
    {"title": "Удлинённый выдох (2×)", "how": [
        "Вдох 4", "Выдох 8", "3–5 минут"
    ]},
    {"title": "Когерентное дыхание 5/5", "how": [
        "Вдох 5 сек", "Выдох 5 сек", "5–10 минут"
    ]},
    {"title": "Насос (sigh breathing)", "how": [
        "Два быстрых вдоха через нос", "Длинный выдох ртом", "1–3 минуты"
    ]},
    {"title": "Квадранты тела", "how": [
        "Внимание по зонам: стопы, таз, грудь, лицо", "По 30–60 сек на зону", "3 круга"
    ]},
    {"title": "Сканирование тела", "how": [
        "Медленно от макушки к пальцам", "Замечай напряжение, отпускай", "5–10 минут"
    ]},
    {"title": "Метта (доброжелательность)", "how": [
        "Мысленно: «Пусть я буду спокоен…»", "Расширяй на близких и нейтральных", "5 минут"
    ]},
    {"title": "Заземление 5-4-3-2-1", "how": [
        "5 вижу, 4 слышу, 3 ощущаю, 2 обоняю, 1 вкушаю", "2–3 минуты"
    ]},
    {"title": "Квадрат внимания", "how": [
        "Ведёшь взгляд по воображаемому квадрату синхронно с 4–4–4–4", "3 минуты"
    ]},
    {"title": "Через шаг", "how": [
        "Вдох — шаг, выдох — два шага", "5–10 минут прогулки"
    ]},
    {"title": "Дыхание животом", "how": [
        "Ладонь на живот", "На вдохе живот под ладонь, на выдохе — назад", "5 минут"
    ]},
    {"title": "Ритм 6/4", "how": [
        "Вдох 6, выдох 4", "3–5 минут"
    ]},
    {"title": "Простое присутствие", "how": [
        "Сидишь удобно", "Отмечаешь вдох/выдох", "Когда уносит — мягко возвращаешь", "5–10 минут"
    ]},
    {"title": "Три глубоких выдоха", "how": [
        "3 медленных глубоких выдоха с расслаблением плеч и челюсти"
    ]},
    {"title": "Клиновое (на сон)", "how": [
        "Вдох 4, выдох 6–8", "В кровати 5 минут"
    ]},
    {"title": "Ритм 3-3-6", "how": [
        "Вдох 3, удержание 3, выдох 6", "3–5 минут"
    ]},
    {"title": "Шум моря (уджайи-лайт)", "how": [
        "Лёгкое сужение горла, ровный шум на выдохе", "2–3 минуты"
    ]},
    {"title": "Микропаузa", "how": [
        "1 минута: 6 медленных циклов 5/5 с расслаблением плеч"
    ]},
    {"title": "Когерентность с шагами", "how": [
        "Вдох 4 шага, выдох 6 шагов", "5–10 минут"
    ]},
]

YOGA = [
    {"title": "Гора (Тадасана)", "how": [
        "Стопы вместе/на ширине таза", "Макушка вверх, плечи вниз", "Дыхание ровное 5–10 циклов"
    ]},
    {"title": "Дерево (Врикшасана)", "how": [
        "Стой на одной ноге", "Стопа ко внутреннему бедру/голени", "Ладони вместе", "30–60 сек/нога"
    ]},
    {"title": "Собака мордой вниз", "how": [
        "Ладони широко, таз вверх", "Пятки к полу, спина вытянута", "5–8 дыханий"
    ]},
    {"title": "Кошка–корова", "how": [
        "На вдох — прогиб, на выдох — округление", "8–10 циклов"
    ]},
    {"title": "Поза ребёнка", "how": [
        "Сядь на пятки, лоб к коврику", "Дыхание спиной", "1–2 минуты"
    ]},
    {"title": "Воин II", "how": [
        "Широкая стойка, колено над пяткой", "Руки в стороны", "5–8 дыханий/сторона"
    ]},
    {"title": "Треугольник", "how": [
        "Нога впереди прямая", "Рука к голени/блоку", "Грудь раскрыта", "5 дыханий/сторона"
    ]},
    {"title": "Поза стула", "how": [
        "Колени назад, таз назад", "Руки вверх", "5–8 дыханий"
    ]},
    {"title": "Полумост", "how": [
        "Лёжа, стопы к тазу", "Таз вверх", "5 дыханий"
    ]},
    {"title": "Сфинкс", "how": [
        "Лёжа на животе, предплечья под плечами", "Мягкий прогиб", "1–2 минуты"
    ]},
    {"title": "Голубь (лайт)", "how": [
        "Из собаки вниз — колено вперёд", "Таз ровный, корпус вниз", "1 мин/сторона"
    ]},
    {"title": "Повороты лёжа", "how": [
        "Колени согнуты, падение в сторону", "Плечи прижаты", "1 мин/сторона"
    ]},
    {"title": "Скрутка сидя", "how": [
        "Спина ровная", "Поворот от таза", "5 дыханий/сторона"
    ]},
    {"title": "Наклон сидя", "how": [
        "Спина длинная", "Складка от тазобедренных", "8 дыханий"
    ]},
    {"title": "Поза лодки (лайт)", "how": [
        "Сидя, корпус назад, ноги согнуты", "Держи центр", "20–30 сек"
    ]},
    {"title": "Планка", "how": [
        "Ладони под плечами", "Кор крепкий, тело прямое", "20–40 сек"
    ]},
    {"title": "Боковая планка (колено в пол)", "how": [
        "Предплечье/ладонь, нижнее колено в пол", "Таз вверх", "20–30 сек/сторона"
    ]},
    {"title": "Орел (руки)", "how": [
        "Руки переплести, плечи вниз", "5–8 дыханий"
    ]},
    {"title": "Верблюд (лайт)", "how": [
        "Колени под тазом, ладони на крестец", "Мягкий прогиб", "5 дыханий"
    ]},
    {"title": "Поза угла у стены", "how": [
        "Ноги на ширине, наклон с опорой", "Руки на стене", "8 дыханий"
    ]},
    {"title": "Счастливый ребёнок", "how": [
        "Лёжа, колени к подмышкам, стопы в руки", "Поясница в пол", "1 мин"
    ]},
    {"title": "Бабочка", "how": [
        "Стопы вместе, колени врозь", "Наклон вперёд легко", "1–2 минуты"
    ]},
    {"title": "Шавасана", "how": [
        "Лёжа, тело расслаблено", "3–5 минут покоя"
    ]},
    {"title": "Полумесяц у стены", "how": [
        "Боком к стене, рука вверх, наклон в сторону", "5–8 дыханий/сторона"
    ]},
]

NUTRITION_TIPS = [
    # 50 кратких и конкретных рекомендаций
    "Старт дня со стакана воды (250–300 мл).",
    "Добавляй белок в каждый приём пищи (яйца/рыба/творог/бобовые).",
    "Овощи — не меньше 400 г в день (2–3 порции).",
    "Фрукты — 1–2 порции ежедневно.",
    "Сложные углеводы: крупы, цельнозерновой хлеб, картофель в мундире.",
    "Полезные жиры: оливковое, орехи, семена, авокадо.",
    "Сократи сахар и сладкие напитки.",
    "Минимизируй ультрапереработанные продукты.",
    "Ешь по расписанию, выдерживай интервалы 3–5 часов.",
    "Следи за размером порций — тарелка: 1/2 овощи, 1/4 белок, 1/4 гарнир.",
    "Пей 30–35 мл воды на кг массы (ориентир, не догма).",
    "Соль до 5 г/сутки, больше специй и трав.",
    "На перекус лучше орехи/йогурт/фрукты, а не печенье.",
    "Кофе до 2–3 чашек, не поздно вечером.",
    "Ужин за 2–3 часа до сна.",
    "Перед тренировкой — углеводы + немного белка (банан + йогурт).",
    "После тренировки — белок 20–30 г и вода.",
    "Следи за реакцией на молочку/глютен — индивидуально.",
    "Алкоголь минимизировать/исключить.",
    "Планируй меню на 2–3 дня — меньше срывов.",
    "Хранение: готовь крупы/белок заранее, держи овощи нарезанными.",
    "Соусы делай сам: йогурт + горчица/травы.",
    "Завтрак с белком (омлет/творог) улучшает сытость.",
    "Добавляй бобовые 3–4 раза/нед — источник клетчатки и белка.",
    "Цельнозерновые макароны вместо обычных.",
    "Приготовление — больше запекания и тушения, меньше жарки.",
    "Сладости — по правилу 1 порция/день после основной еды.",
    "Взвешивайся 1–2 раза в неделю утром — для контроля тренда.",
    "Веди фото-дневник еды — дисциплина.",
    "Если тянет на сладкое — сначала вода и прогулка 10 мин.",
    "Ешь осознанно: без экрана, медленно, отмечай вкус.",
    "Клетчатка 25–30 г/день (овощи, бобовые, цельные злаки).",
    "Рыба 2 раза/нед., в т. ч. жирная.",
    "Красное мясо ≤ 1–2 раза/нед.",
    "Яйца: от 4 до 7 шт/нед. — по самочувствию.",
    "Проверяй витамин D по анализу и корректируй с врачом.",
    "Раз в 3–4 часа — стакан воды.",
    "Снэки упакуй заранее (контейнеры).",
    "Экономия: крупы/бобовые — база бюджета.",
    "Сезонные овощи/фрукты — дешевле и вкуснее.",
    "Уменьшай жидкие калории (соки/латте).",
    "Йогурт — без сахара, добавь ягоды сам.",
    "Сыры — небольшие порции, как деликатес.",
    "Чай без сахара, попробуй травяные.",
    "Завтраки ротируй (3–4 варианта) — меньше скуки.",
    "Порционная посуда помогает не переедать.",
    "Оцени сытость по шкале 1–10 и останавливайся на 7–8.",
    "Ешь больше дома, чем вне дома.",
    "Список покупок — всегда, без него не заходи.",
    "Помни про орехи: 20–30 г — порция.",
]

ANALYSIS_DB = {
    # 35 справок по анализам (кратко, понятно, НЕ медсовет, а ориентиры)
    "hemoglobin": "Гемоглобин — перенос кислорода. Низкий: усталость, бледность. Высокий: обезвоживание/курение/горы. Оценивать с эритроцитами/ферритином.",
    "ferritin": "Ферритин — запас железа. Низкий — частая причина усталости/выпадения волос. Высокий — воспаление/перегрузка железом. Смотри CRP, гемоглобин.",
    "vitamin_d": "Витамин D — кости/иммунитет. Низкий част — у сидящих в помещении. Коррекция только после анализа и по схеме врача.",
    "b12": "В12 — нервная система/кроветворение. Дефицит: покалывания, слабость. Возможен при веганстве/гастритах.",
    "glucose": "Глюкоза натощак. Высокая — риск преддиабета/диабета. Следить с HbA1c и глюкозотолерантным тестом.",
    "hba1c": "HbA1c — средняя глюкоза за 3 мес. Удобен для скрининга преддиабета/диабета.",
    "alt_ast": "АЛТ/АСТ — ферменты печени. Рост: алкоголь, ожирение печени, лекарства. Сопоставить с УЗИ и образом жизни.",
    "ggt": "ГГТ — чувствителен к алкоголю/желчи. Часто растёт при злоупотреблении алкоголем/застое желчи.",
    "bilirubin": "Билирубин — печень/желчь. Рост: проблемы оттока желчи, гемолиз. Бывает доброкачественная гипербилирубинемия (Гильберт).",
    "chol_total": "Общий холестерин — общий индикатор. Важнее смотреть ЛПНП, ЛПВП, ТГ.",
    "ldl": "ЛПНП («плохой»). Высокий — фактор риска ССЗ. Коррекция: питание, активность, иногда препараты по назначению врача.",
    "hdl": "ЛПВП («хороший»). Выше — лучше. Растёт от активности, омега-3.",
    "tg": "Триглицериды — жиры крови. Высокие: избыток сахара/алкоголя/калорий.",
    "creatinine": "Креатинин — почки. Оценивают вместе с СКФ.",
    "egfr": "СКФ — расчётная фильтрация почек. Важно с креатинином/давлением.",
    "uric_acid": "Мочевая кислота. Высокая: подагра/метаболические риски. Коррекция диетой и массой.",
    "crp": "СРБ — маркёр воспаления. Высокий: острое/хроническое воспаление.",
    "wbc": "Лейкоциты — иммунитет. Высокие: воспаление; низкие: дефициты/супрессия.",
    "rbc": "Эритроциты — кислород/перенос. См. вместе с Hb, Hct.",
    "platelets": "Тромбоциты — свёртывание. Оценивать с коагулограммой.",
    "iron": "Железо сывороточное — колеблется, лучше ферритин/ОЖСС.",
    "tsh": "ТТГ — щитовидка. Отклонения требуют T3/T4 и консультации эндокринолога.",
    "ft4": "Свободный T4 — функция щитовидки. Смотреть с ТТГ/Т3.",
    "ft3": "Свободный T3 — активная форма. В комплексе с ТТГ/T4.",
    "magnesium": "Магний — мышцы/нервы. Дефицит: судороги, утомляемость.",
    "calcium": "Кальций — кости/нервы. Смотри общий/ионизированный и PTH.",
    "potassium": "Калий — сердце/нервы. Отклонения опасны — не самолечиться!",
    "sodium": "Натрий — водный баланс. Сдвиги при обезвоживании/патологиях.",
    "vitamin_b9": "Фолат — кровь/нервы/беременность. Дефицит част у скудного рациона.",
    "coagulation": "Коагулограмма — свёртывание. Важно перед операциями/при проблемах с кровоточивостью.",
    "alp": "ЩФ — желчь/кости. Рост при холестазе/росте костей/беременности.",
    "amylase": "Амилаза — поджелудочная. Рост при панкреатите/слюнных железах.",
    "lipase": "Липаза — поджелудочная. Более специфична для панкреатита.",
    "vitamin_b6": "B6 — метаболизм, нервы. Избыток добавок тоже вреден.",
    "omega3_index": "Индекс омега-3 — маркёр потребления омега-3 жиров.",
    "insulin": "Инсулин натощак — оценка ИР с HOMA-IR, обсуждать с врачом.",
    "homocysteine": "Гомоцистеин — сосудистые риски, зависит от B12/B9/B6.",
}

# ================================
# --------- ПРИЛОЖЕНИЕ PTB -------
# ================================
application: Application = ApplicationBuilder().token(BOT_TOKEN).build()


# ================================
# --------- ОБРАБОТЧИКИ ----------
# ================================

async def cmd_start(update: Update, context: CallbackContext):
    text = (
        "👋 Привет! Я Life Rhythm.\n\n"
        "Доступные команды:\n"
        "/help — справка\n"
        "/exercise [N] — тренировки (по умолчанию 3, максимум 10)\n"
        "/meditation [N] — дыхательные практики (3..10)\n"
        "/yoga [N] — йога-позы с описанием (3..10)\n"
        "/nutrition [N] — советы по питанию (5..20)\n"
        "/analysis <ключ> — краткая справка по анализу (см. /analysis list)\n"
        "/water [мл] — учёт воды (по умолчанию 250 мл)\n"
        "/stats — сколько воды выпито сегодня\n"
        "/setdob YYYY-MM-DD — дата рождения для /biorhythm\n"
        "/biorhythm — био-ритмы на сегодня\n"
    )
    await update.effective_message.reply_text(text)

async def cmd_help(update: Update, context: CallbackContext):
    await cmd_start(update, context)

def format_block(title: str, lines: List[str]) -> str:
    out = f"• <b>{title}</b>\n"
    for i, l in enumerate(lines, 1):
        out += f"  {i}. {l}\n"
    return out

async def cmd_exercise(update: Update, context: CallbackContext):
    n = parse_n(context.args, default=3, min_v=1, max_v=10)
    items = random.sample(EXERCISES, k=min(n, len(EXERCISES)))
    text = "🏃 <b>Тренировки</b> — делай разминку и прислушивайся к самочувствию.\n\n"
    for it in items:
        text += format_block(it["title"], it["steps"]) + "\n"
    for part in chunk_text(text):
        await update.effective_message.reply_text(part, parse_mode=ParseMode.HTML)

async def cmd_meditation(update: Update, context: CallbackContext):
    n = parse_n(context.args, default=3, min_v=1, max_v=10)
    items = random.sample(MEDITATIONS, k=min(n, len(MEDITATIONS)))
    text = "🧘 <b>Дыхательные практики</b> — мягко, без напряжения.\n\n"
    for it in items:
        text += format_block(it["title"], it["how"]) + "\n"
    for part in chunk_text(text):
        await update.effective_message.reply_text(part, parse_mode=ParseMode.HTML)

async def cmd_yoga(update: Update, context: CallbackContext):
    n = parse_n(context.args, default=3, min_v=1, max_v=10)
    items = random.sample(YOGA, k=min(n, len(YOGA)))
    text = "🌿 <b>Йога-позы</b> — без боли, в своём диапазоне.\n\n"
    for it in items:
        text += format_block(it["title"], it["how"]) + "\n"
    for part in chunk_text(text):
        await update.effective_message.reply_text(part, parse_mode=ParseMode.HTML)

async def cmd_nutrition(update: Update, context: CallbackContext):
    n = parse_n(context.args, default=10, min_v=5, max_v=20)
    items = random.sample(NUTRITION_TIPS, k=min(n, len(NUTRITION_TIPS)))
    text = "🥗 <b>Питание</b> — простые рабочие советы:\n\n"
    for i, tip in enumerate(items, 1):
        text += f"{i}. {tip}\n"
    for part in chunk_text(text):
        await update.effective_message.reply_text(part, parse_mode=ParseMode.HTML)

async def cmd_analysis(update: Update, context: CallbackContext):
    if not context.args:
        keys = ", ".join(sorted(ANALYSIS_DB.keys()))
        await update.effective_message.reply_text(
            "Использование: <code>/analysis ключ</code>\n"
            "Например: <code>/analysis ferritin</code>\n\n"
            "Доступные ключи:\n" + keys,
            parse_mode=ParseMode.HTML
        )
        return
    key = context.args[0].lower()
    if key == "list":
        keys = ", ".join(sorted(ANALYSIS_DB.keys()))
        await update.effective_message.reply_text("Ключи: " + keys)
        return
    info = ANALYSIS_DB.get(key)
    if not info:
        await update.effective_message.reply_text("Не знаю такой ключ. Напиши /analysis list")
        return
    text = f"🧪 <b>{key}</b>\n{info}\n\n<b>Важно:</b> это не медсовет. Интерпретацию делает врач."
    await update.effective_message.reply_text(text, parse_mode=ParseMode.HTML)

def today_str() -> str:
    return date.today().isoformat()

async def cmd_water(update: Update, context: CallbackContext):
    ml = 250
    if context.args:
        try:
            ml = max(50, min(2000, int(context.args[0])))
        except Exception:
            pass
    uid = update.effective_user.id
    day = today_str()
    user = WATER_STATE.setdefault(uid, {})
    user[day] = user.get(day, 0) + ml
    total = user[day]
    goal = 2000
    await update.effective_message.reply_text(f"💧 +{ml} мл. Всего сегодня: {total} мл (цель ~{goal} мл).")

async def cmd_stats(update: Update, context: CallbackContext):
    uid = update.effective_user.id
    day = today_str()
    total = WATER_STATE.get(uid, {}).get(day, 0)
    await update.effective_message.reply_text(f"📊 Вода сегодня: {total} мл.")

def parse_date(s: str) -> date:
    y, m, d = s.split("-")
    return date(int(y), int(m), int(d))

def biorhythm_percent(days: int, period: float) -> int:
    # классическая синусоида 0..100
    val = (math.sin(2 * math.pi * days / period) + 1) / 2
    return int(round(val * 100))

async def cmd_setdob(update: Update, context: CallbackContext):
    if not context.args:
        await update.effective_message.reply_text("Использование: /setdob YYYY-MM-DD")
        return
    try:
        dt = parse_date(context.args[0])
        DOB_STATE[update.effective_user.id] = dt.isoformat()
        await update.effective_message.reply_text(f"✅ Дата сохранена: {dt.isoformat()}")
    except Exception:
        await update.effective_message.reply_text("Неверный формат. Пример: /setdob 1990-08-20")

async def cmd_biorhythm(update: Update, context: CallbackContext):
    uid = update.effective_user.id
    dob_s = DOB_STATE.get(uid)
    if not dob_s:
        await update.effective_message.reply_text("Сначала /setdob YYYY-MM-DD")
        return
    dob = parse_date(dob_s)
    days = (date.today() - dob).days
    physical = biorhythm_percent(days, 23.0)
    emotional = biorhythm_percent(days, 28.0)
    intellectual = biorhythm_percent(days, 33.0)
    text = (
        "📈 <b>Биоритмы на сегодня</b>\n"
        f"Физический: {physical}%\n"
        f"Эмоциональный: {emotional}%\n"
        f"Интеллектуальный: {intellectual}%\n\n"
        "Это развлекательная метрика. Слушай самочувствие и ориентируйся на факты."
    )
    await update.effective_message.reply_text(text, parse_mode=ParseMode.HTML)

# Регистрируем команды
application.add_handler(CommandHandler("start", cmd_start))
application.add_handler(CommandHandler("help", cmd_help))
application.add_handler(CommandHandler("exercise", cmd_exercise))
application.add_handler(CommandHandler("meditation", cmd_meditation))
application.add_handler(CommandHandler("yoga", cmd_yoga))
application.add_handler(CommandHandler("nutrition", cmd_nutrition))
application.add_handler(CommandHandler("analysis", cmd_analysis))
application.add_handler(CommandHandler("water", cmd_water))
application.add_handler(CommandHandler("stats", cmd_stats))
application.add_handler(CommandHandler("setdob", cmd_setdob))
application.add_handler(CommandHandler("biorhythm", cmd_biorhythm))

# ================================
# --------- FLASK (WEB) ----------
# ================================
app = Flask(__name__)

@app.get("/")
def index():
    return "LifeRhythm Bot is running. Use /healthz for health."

@app.get("/healthz")
def healthz():
    # Render health-check
    return jsonify(ok=True, time=datetime.utcnow().isoformat())

# ВНИМАНИЕ: async-view требует Flask[async] (мы добавили в requirements).
@app.post(TELEGRAM_WEBHOOK_PATH)
async def telegram_webhook():
    # Инициализируем и запускаем PTB-приложение один раз (лениво, при первом апдейте)
    if not application.running:
        await application.initialize()
        await application.start()
    # Читаем апдейт и отдаём PTB
    data = request.get_json(silent=True, force=True)
    if not data:
        return jsonify(ok=False, error="no json"), 400
    update = Update.de_json(data, application.bot)
    await application.process_update(update)
    return jsonify(ok=True)

async def setup_webhook_once(bot: Bot):
    # Ставим вебхук при старте контейнера и чистим хвосты
    await bot.set_webhook(
        url=TELEGRAM_WEBHOOK_URL,
        allowed_updates=Update.ALL_TYPES,
        drop_pending_updates=True,
    )
    print(f"[OK] Webhook set to {TELEGRAM_WEBHOOK_URL}")

if __name__ == "__main__":
    # 1) Ставим вебхук (без запуска polling)
    asyncio.run(setup_webhook_once(Bot(token=BOT_TOKEN)))
    # 2) Стартуем Flask-сервер для Render
    app.run(host="0.0.0.0", port=PORT)
