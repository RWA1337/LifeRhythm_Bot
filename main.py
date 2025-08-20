import os
import random
from datetime import datetime, date
from typing import List, Dict

from flask import Flask, request, jsonify, abort

from telegram import Update, ReplyKeyboardMarkup
from telegram.ext import (
    ApplicationBuilder,
    Application,
    CommandHandler,
    ContextTypes,
)

# ==============================
# Конфиг
# ==============================
TOKEN = os.getenv("BOT_TOKEN")
if not TOKEN:
    raise RuntimeError("Env var BOT_TOKEN is not set")

PORT = int(os.getenv("PORT", "10000"))  # Render обычно даёт 10000
BASE_URL = os.getenv("BASE_URL", "https://liferhythm-bot.onrender.com")
WEBHOOK_PATH = "/webhook"  # можешь поменять, например "/webhook-secret"
WEBHOOK_URL = f"{BASE_URL}{WEBHOOK_PATH}"

# ==============================
# Данные (наполненные разделы)
# ==============================

EXERCISE_SETS: List[Dict] = [
    {
        "title": "Быстрая утренняя зарядка (5–7 мин)",
        "steps": [
            "Прыжки на месте — 30 сек",
            "Круговые вращения руками — 20 сек",
            "Приседания — 12 раз",
            "Планка — 30 сек",
            "Наклоны к носкам — 10 раз"
        ],
        "note": "Лёгкая активация без инвентаря."
    },
    {
        "title": "Силовой комплекс без инвентаря (10 мин)",
        "steps": [
            "Приседания — 15",
            "Отжимания (от пола/стены) — 10",
            "Выпады — по 10 на ногу",
            "Планка — 40 сек",
            "Скручивания — 15"
        ],
        "note": "Дыши ровно, движение в среднем темпе."
    },
    {
        "title": "Кардио-дом (8–10 мин)",
        "steps": [
            "Бёрпи облегчённые — 8",
            "Бег на месте — 45 сек",
            "Прыжки «джампинг джек» — 30 сек",
            "Высокие колени — 30 сек",
            "Спокойная ходьба — 1 мин"
        ],
        "note": "Следи за пульсом, не перегревайся."
    },
    {
        "title": "Мобилити для спины и бёдер (7–9 мин)",
        "steps": [
            "Кошка-корова — 8–10 циклов",
            "Повороты корпуса стоя — 10",
            "Выпад с растяжкой сгибателей — по 30 сек",
            "Скрутка лёжа — по 30 сек",
            "Наклон из положения сидя — 40 сек"
        ],
        "note": "Работай мягко, без боли."
    },
    {
        "title": "Офис-микро-тренировка (4–6 мин)",
        "steps": [
            "Приседания у стула — 12",
            "Отжимания от стола — 10",
            "Подъём на носки — 20",
            "Разведение лопаток — 12",
            "Шея: наклоны — по 6 в стороны"
        ],
        "note": "Разомнёт, если сидишь долго."
    },
    {
        "title": "Кор (пресс/спина) (8–10 мин)",
        "steps": [
            "Планка — 30–45 сек",
            "Боковая планка — по 25–30 сек",
            "Скручивания — 15",
            "«Ножницы» — 20 сек",
            "Гиперэкстензия лёжа — 12–15"
        ],
        "note": "Контроль поясницы, не прогибайся чрезмерно."
    },
    {
        "title": "Ноги и ягодицы (10–12 мин)",
        "steps": [
            "Приседания — 15",
            "Ягодичный мост — 15–20",
            "Выпады назад — по 10",
            "Пульсирующие приседания — 12",
            "Растяжка квадрицепса — по 30 сек"
        ],
        "note": "Колени направляй в сторону носков."
    },
    {
        "title": "Грудь/плечи (10 мин)",
        "steps": [
            "Отжимания (вариант по уровню) — 10–12",
            "Отжимания узким хватом — 8–10",
            "Упор на предплечья — 40 сек",
            "Плие-приседания — 12",
            "Растяжка груди у стены — 30 сек"
        ],
        "note": "Следи за плечами — не задирай их к ушам."
    },
    {
        "title": "Кардио-интервалы (12 мин)",
        "steps": [
            "Бег на месте — 60 сек",
            "Прыжки — 30 сек",
            "Ходьба — 60 сек",
            "Высокие колени — 30 сек",
            "Повторить 2–3 круга"
        ],
        "note": "Пей воду маленькими глотками."
    },
    {
        "title": "Расслабляющий вечерний комплекс (6–8 мин)",
        "steps": [
            "Наклон стоя — 40 сек",
            "Скрутка лёжа — по 30 сек",
            "Поза ребёнка — 40 сек",
            "Диафрагмальное дыхание — 1–2 мин"
        ],
        "note": "Замедляйся к вечеру, готовься ко сну."
    },
    # Ещё 10 коротких вариантов:
    *[
        {
            "title": f"Мини-комплекс #{i}",
            "steps": [
                "20 приседаний",
                "10–15 отжиманий (от стены/колен)",
                "Планка 30–40 сек",
                "Скручивания 12–15",
            ],
            "note": "Быстрый полноценный круг."
        }
        for i in range(11, 21)
    ]
]

BREATHING_TECHNIQUES: List[Dict] = [
    {"title": "4-4-4", "how": "Вдох 4 сек — задержка 4 — выдох 4. Повтори 6–8 циклов."},
    {"title": "4-7-8", "how": "Вдох 4 — задержка 7 — выдох 8. 4–6 циклов, перед сном."},
    {"title": "Box breathing 4-4-4-4", "how": "Вдох — задержка — выдох — задержка по 4 сек. 5–10 циклов."},
    {"title": "Уддияна с мягким животом", "how": "Спокойный вдох/выдох через нос, живот мягкий. 2–3 мин."},
    {"title": "Дыхание по счёту", "how": "Вдох на 5, выдох на 7. 2–5 мин, удлиняй выдох."},
    {"title": "Через одну ноздрю", "how": "Зажимай по очереди ноздри: вдох левой — выдох правой и наоборот. 3–5 мин."},
    {"title": "Кохерентное 5-5", "how": "Вдох 5 сек — выдох 5 сек. 5–10 мин для стабилизации."},
    {"title": "«Шипящее» (уджайи)", "how": "Дыши через нос с лёгким «шипением» в горле. 2–5 мин."},
    {"title": "Дыхание животом", "how": "Лёжа, ладонь на животе. Вдох — поднимается, выдох — опускается. 3–6 мин."},
    {"title": "360° дыхание", "how": "Расширяй бока и спину на вдохе. 2–4 мин."},
    {"title": "6-сек вдох / 6-сек выдох", "how": "Ровный цикл 6/6. 5 мин для фокуса."},
    {"title": "Выдох длиннее", "how": "Вдох 3–4, выдох 6–8. Успокаивает. 3–5 мин."},
    {"title": "Шаговое дыхание", "how": "При ходьбе: вдох на 3 шага, выдох на 4–5. 5–10 мин."},
    {"title": "Дыхание с визуализацией", "how": "На вдохе — свет, на выдохе — напряжение уходит. 3–5 мин."},
    {"title": "«Пчела» (бхрамари)", "how": "Гудящий выдох как «м-м-м». 6–10 выдохов."},
    {"title": "Расслабляющий счёт 10→1", "how": "На каждом выдохе считай вниз. 2–3 мин."},
    {"title": "Метта-медитация", "how": "На выдохе: «Пусть я буду спокоен…» 3–5 мин."},
    {"title": "Сканирование тела", "how": "Проходи вниманием от макушки к стопам. 5–10 мин."},
    {"title": "Квадраты внимания", "how": "Взглядом веди воображаемый квадрат, синхронно с 4-4-4-4. 2–4 мин."},
    {"title": "Дыхание перед сном", "how": "Вдох 4 — выдох 8, лёжа в темноте. 5–8 мин."},
]

YOGA_POSES: List[Dict] = [
    {"title": "Тадасана (Гора)", "how": "Ноги вместе, макушка вверх, плечи вниз, дыхание ровное — 30–60 сек."},
    {"title": "Врикшасана (Дерево)", "how": "Стой на одной ноге, стопу другой на бедро, ладони к груди или вверх — 30–60 сек."},
    {"title": "Ардха уттанасана (Полункалон)", "how": "Наклон вперёд, спина длинная, руки на голенях — 30 сек."},
    {"title": "Ашва санчаласана (Выпад)", "how": "Длинный шаг назад, колено вниз/вверх, грудь вперёд — 30 сек/сторона."},
    {"title": "Адхо мукха шванасана (Собака мордой вниз)", "how": "Ладони жмут пол, таз вверх, шея длинная — 30–45 сек."},
    {"title": "Баласана (Ребёнок)", "how": "Сядь на пятки, лоб на коврик, руки вперёд — 40–60 сек."},
    {"title": "Бхуджангасана (Кобра)", "how": "Лёжа на животе, мягкий прогиб, локти близко — 20–30 сек."},
    {"title": "Апанаcана (Колени к груди)", "how": "Лёжа, обними колени, покачайся — 40 сек."},
    {"title": "Супта матсиендрасана (Скрутка лёжа)", "how": "Колени вбок, плечи на полу — 30–40 сек/сторона."},
    {"title": "Дандасана (Посох)", "how": "Сидя, ноги вперёд, спина ровная — 40 сек."},
    {"title": "Пашчимоттанасана (Наклон сидя)", "how": "Наклон к стопам, спина длинная — 40–60 сек."},
    {"title": "Сету бандха сарвангасана (Мост)", "how": "Лёжа, таз вверх, лопатки к центру — 20–30 сек."},
    {"title": "Шавасана", "how": "Полное расслабление лёжа — 2–5 мин."},
    {"title": "Уткатасана (Стул)", "how": "Полуприсед, руки вверх, живот в тонусе — 30–40 сек."},
    {"title": "Вирабхадрасана II (Воин II)", "how": "Широкая стойка, колено над пяткой — 30 сек/сторона."},
    {"title": "Триконасана (Треугольник)", "how": "Боковой наклон, бока длинные — 30 сек/сторона."},
    {"title": "Пурвоттанасана (Обратная планка)", "how": "Таз вверх, грудь раскрыта — 15–25 сек."},
    {"title": "Ардха хануманасана (Полушпагат)", "how": "Полувыпад, носок на себя — 30–40 сек/сторона."},
    {"title": "Гомукхасана руки", "how": "Одна рука сверху, другая снизу — 20–30 сек/сторона."},
    {"title": "Пранамаcана (Молитвенная поза)", "how": "Ладони у груди, дыхание ровное — 30–60 сек."},
]

NUTRITION_TIPS: List[str] = [
    "Питайся по режиму: 3 главных приёма пищи + 1–2 перекуса.",
    "Каждый приём включай белок (яйца, рыба, мясо, бобовые, творог).",
    "Добавляй клетчатку: овощи/зелень 300–500 г в день.",
    "Сложные углеводы: цельнозерновые крупы вместо сахара и белой муки.",
    "Пей воду 25–35 мл/кг массы в сутки (учитывай самочувствие).",
    "Сократи сахар и сладкие напитки — это быстрые калории.",
    "Полезные жиры: оливковое масло, орехи, семена, авокадо.",
    "Ограничь трансжиры (фастфуд, маргарины).",
    "Следи за тарелкой: половина овощи, четверть белок, четверть сложные угли.",
    "Пережёвывай медленно — сигнал сытости приходит с задержкой.",
    "Планируй меню на 2–3 дня вперёд — меньше срывов.",
    "Завтрак с белком (яйца/творог) — меньше тяги к сладкому.",
    "Контролируй соль до 5 г/сутки (если нет иных рекомендаций врача).",
    "Ферментированные продукты (кефир, йогурт без сахара) поддерживают микробиом.",
    "Добавляй бобовые 2–4 раза в неделю.",
    "Меньше алкоголя — пустые калории и аппетит растёт.",
    "Читай состав: чем короче список — тем лучше.",
    "Готовь дома чаще — контролируешь состав и порции.",
    "Десерты — после еды, а не вместо неё.",
    "Стабильный сон — меньше ночных перекусов.",
    "Перекусывай полезно: орехи 20–30 г, йогурт натуральный, фрукты.",
    "Сезонные овощи/фрукты вкуснее и дешевле.",
    "Держи на виду полезное, «мусор» — подальше.",
    "Если худеешь: дефицит 10–15% от поддержки, не жестко.",
    "Добавь белка при наборе мышц: ~1.6–2.0 г/кг/сутки.",
    "Омега-3 из рыбы 2–3 раза/нед или добавки (по согласованию с врачом).",
    "Жирная рыба, яйца, печень — источники витамина D (проверь анализ).",
    "Крупы промывай и вари «аль денте» — ниже гликемический индекс.",
    "Старайся есть за 2–3 часа до сна.",
    "Не «наказывай» себя голодом — выбирай устойчивые привычки.",
    "Пей воду перед кофе/чаем — меньше обезвоживания.",
    "Фрукты — целиком, а не сок.",
    "Сладкое — по плану, а не импульсивно.",
    "Ешь кефир/йогурт после антибиотиков (если назначались).",
    "Старайся разнообразить крупы: гречка, булгур, киноа, бурый рис.",
    "Салаты заправляй маслом, а не майонезом.",
    "Сократи полуфабрикаты — много соли и добавок.",
    "Отслеживай самочувствие после продуктов — личная непереносимость бывает.",
    "Готовь «на завтра» — контейнеры решают.",
    "Разгрузочные дни не обязаны быть голодными — делай их «чистыми».",
]

LABS: Dict[str, Dict] = {
    "hemoglobin": {
        "name": "Гемоглобин",
        "normal": "М: ~130–170 г/л, Ж: ~120–150 г/л (референсы лабораторий могут отличаться)",
        "more": "Низкий — возможна анемия (железо, B12, фолат). Высокий — обезвоживание, адаптация к высоте и др."
    },
    "ferritin": {
        "name": "Ферритин",
        "normal": "Обычно ~20–250 нг/мл (зависит от пола/лаб.)",
        "more": "Показывает запасы железа. Низкий — дефицит, высокий — воспаление/перегрузка железом."
    },
    "iron": {
        "name": "Железо сывороточное",
        "normal": "~9–30 мкмоль/л",
        "more": "Оценивают вместе с ферритином, ОЖСС, ТФС."
    },
    "vitamin_d": {
        "name": "Витамин D (25-OH)",
        "normal": "~30–100 нг/мл (спорный диапазон)",
        "more": "Низкий — часто в северных регионах. Коррекция добавками по назначению врача."
    },
    "b12": {
        "name": "B12",
        "normal": "~200–900 пг/мл",
        "more": "Низкий — слабость, анемия, неврол. симптомы."
    },
    "glucose": {
        "name": "Глюкоза",
        "normal": "Натощак ~3.9–5.5 ммоль/л",
        "more": "Постоянно повышена — проверь HbA1c, к врачу."
    },
    "hba1c": {
        "name": "Гликированный гемоглобин (HbA1c)",
        "normal": "~4.0–5.6%",
        "more": "5.7–6.4% — преддиабет, ≥6.5% — критерий диабета (подтверждает врач)."
    },
    "chol_total": {
        "name": "Холестерин общий",
        "normal": "Часто целевой <5.0 ммоль/л",
        "more": "Смотрят вместе с ЛПНП, ЛПВП, ТГ и риском ССЗ."
    },
    "ldl": {
        "name": "ЛПНП",
        "normal": "Целевой зависит от риска; часто <3.0, а при высоком риске — <1.4–1.8 ммоль/л",
        "more": "«Плохой» холестерин — основной таргет терапии."
    },
    "hdl": {
        "name": "ЛПВП",
        "normal": "Желательно >1.0–1.2 ммоль/л",
        "more": "«Хороший» холестерин."
    },
    "tg": {
        "name": "Триглицериды",
        "normal": "<1.7 ммоль/л",
        "more": "Высокие ТГ часто при избытке калорий/сахара/алкоголя."
    },
    "ast": {
        "name": "АСТ",
        "normal": "Обычно <40 Ед/л",
        "more": "Печёночные ферменты; оценивают вместе с АЛТ."
    },
    "alt": {
        "name": "АЛТ",
        "normal": "Обычно <40 Ед/л",
        "more": "Чувствителен к поражению печени."
    },
    "ggt": {
        "name": "ГГТ",
        "normal": "Обычно <60 Ед/л",
        "more": "Повышается при холестазе, алкоголе и др."
    },
    "bilirubin": {
        "name": "Билирубин общий",
        "normal": "~3–21 мкмоль/л",
        "more": "Смотрят также прямой/непрямой."
    },
    "creatinine": {
        "name": "Креатинин",
        "normal": "Зависит от пола/массы; нужен расчёт eGFR",
        "more": "Для оценки функции почек рассчитай eGFR (CKD-EPI)."
    },
    "urea": {
        "name": "Мочевина",
        "normal": "~2.5–8.3 ммоль/л",
        "more": "Растёт при обезвоживании/белковом избытке/нарушении почек."
    },
    "uric": {
        "name": "Мочевая кислота",
        "normal": "~200–420 мкмоль/л",
        "more": "Высокий уровень — риск подагры/камней."
    },
    "tsH": {
        "name": "ТТГ",
        "normal": "~0.4–4.0 мЕд/л",
        "more": "При отклонениях проверяют T4 свободный."
    },
    "t4free": {
        "name": "T4 свободный",
        "normal": "Лаб. референты",
        "more": "Оценивают при подозрении на дисфункцию щитовидки."
    },
    "crp": {
        "name": "СРБ (в/ч)",
        "normal": "<1 мг/л — низкий риск",
        "more": "Маркер воспаления/риска ССЗ."
    },
    "vitamin_b9": {
        "name": "Фолат (B9)",
        "normal": "Лаб. референты",
        "more": "Низкий — анемия, утомляемость."
    },
    "magnesium": {
        "name": "Магний",
        "normal": "~0.66–1.07 ммоль/л",
        "more": "Сывороточный Mg не всегда отражает запасы."
    },
    "calcium": {
        "name": "Кальций общий/ионизированный",
        "normal": "Лаб. референты",
        "more": "Смотреть совместно с альбумином/витамином D/ПТГ."
    },
    "potassium": {
        "name": "Калий",
        "normal": "~3.5–5.1 ммоль/л",
        "more": "Отклонения опасны для сердца — к врачу."
    },
    "sodium": {
        "name": "Натрий",
        "normal": "~135–145 ммоль/л",
        "more": "Сильно зависит от водного баланса/гормонов."
    },
    "platelets": {
        "name": "Тромбоциты",
        "normal": "~150–400 ×10⁹/л",
        "more": "Низкие — риск кровотечений, высокие — тромбозов (к врачу)."
    },
    "wbc": {
        "name": "Лейкоциты",
        "normal": "~4–9 ×10⁹/л",
        "more": "Повышение — воспаление/инфекция, снижение — др. причины."
    },
    "rbc": {
        "name": "Эритроциты",
        "normal": "~3.8–5.8 ×10¹²/л (пол/лаб.)",
        "more": "Оценивают вместе с Hb/MCV/MCH."
    },
    "vitamin_b6": {
        "name": "B6",
        "normal": "Лаб. референты",
        "more": "Дефицит — утомляемость, кожа, нервы."
    },
    "vitamin_b1": {
        "name": "B1 (Тиамин)",
        "normal": "Лаб. референты",
        "more": "Дефицит — неврол. симптомы, утомляемость."
    },
}

# Псевдонимы для /analysis
LABS_ALIASES = {
    "гемоглобин": "hemoglobin",
    "ферритин": "ferritin",
    "железо": "iron",
    "витамин d": "vitamin_d",
    "д3": "vitamin_d",
    "b12": "b12",
    "в12": "b12",
    "глюкоза": "glucose",
    "сахар": "glucose",
    "hba1c": "hba1c",
    "гликированный": "hba1c",
    "общий холестерин": "chol_total",
    "лпнп": "ldl",
    "лпвп": "hdl",
    "триглицериды": "tg",
    "аст": "ast",
    "алт": "alt",
    "ггт": "ggt",
    "билирубин": "bilirubin",
    "креатинин": "creatinine",
    "мочевина": "urea",
    "мочевая кислота": "uric",
    "ттг": "tsH",
    "t4": "t4free",
    "срб": "crp",
    "фолат": "vitamin_b9",
    "магний": "magnesium",
    "кальций": "calcium",
    "калий": "potassium",
    "натрий": "sodium",
    "тромбоциты": "platelets",
    "лейкоциты": "wbc",
    "эритроциты": "rbc",
}

# Вода — храним в памяти по user_id и дате (на free-инстансах данных хватит)
WATER: Dict[int, Dict[str, int]] = {}  # {user_id: {"YYYY-MM-DD": ml}}

# ==============================
# Вспомогательные функции
# ==============================

def pick_many(items: List, n: int) -> List:
    n = max(1, min(n, min(10, len(items))))  # ограничим до 10 за раз
    return random.sample(items, n)

def today_key() -> str:
    return date.today().isoformat()

def split_chunks(text: str, max_len: int = 3500) -> List[str]:
    # делим длинные ответы (лимит Telegram ~4096)
    parts = []
    while len(text) > max_len:
        cut = text.rfind("\n", 0, max_len)
        if cut == -1:
            cut = max_len
        parts.append(text[:cut])
        text = text[cut:]
    parts.append(text)
    return parts

def biorhythm_for(birth: date, on_date: date) -> Dict[str, float]:
    days = (on_date - birth).days
    import math
    return {
        "physical": math.sin(2 * math.pi * days / 23),
        "emotional": math.sin(2 * math.pi * days / 28),
        "intellectual": math.sin(2 * math.pi * days / 33),
    }

# ==============================
# Handlers
# ==============================

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    kb = [
        ["/exercise", "/meditation", "/yoga"],
        ["/nutrition", "/analysis", "/water"],
        ["/biorhythm", "/help"]
    ]
    await update.message.reply_text(
        "Привет! Я Life Rhythm. Доступные разделы — жми кнопки или пиши команды. "
        "Подсказки: `/exercise 3` — выдам 3 комплекса; `/meditation 5` — 5 техник и т.д.",
        reply_markup=ReplyKeyboardMarkup(kb, resize_keyboard=True),
    )

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = (
        "Доступные команды:\n"
        "• /exercise [n] — комплексы упражнений (укажи число для нескольких)\n"
        "• /meditation [n] — дыхательные техники (укажи число)\n"
        "• /yoga [n] — йога-позы (укажи число)\n"
        "• /nutrition [n] — советы по питанию (по умолчанию 5, можно число)\n"
        "• /analysis <название> — справка по анализу (например: /analysis гемоглобин)\n"
        "• /analysis list — список доступных анализов\n"
        "• /water [add/set/reset] [мл] — учёт воды. Примеры: `/water` (плюс 250 мл), "
        "`/water add 500`, `/water set 1500`, `/water reset`\n"
        "• /biorhythm DD.MM.YYYY — расчёт биоритмов на сегодня\n"
        "• /menu — клавиатура с разделами"
    )
    await update.message.reply_text(text)

async def menu_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    kb = [
        ["/exercise", "/meditation", "/yoga"],
        ["/nutrition", "/analysis", "/water"],
        ["/biorhythm", "/help"]
    ]
    await update.message.reply_text("Меню:", reply_markup=ReplyKeyboardMarkup(kb, resize_keyboard=True))

def _format_exercise(item: Dict) -> str:
    steps = "\n".join([f"{i+1}. {s}" for i, s in enumerate(item["steps"])])
    return f"🏃 {item['title']}\n{steps}\n💡 {item['note']}"

async def exercise(update: Update, context: ContextTypes.DEFAULT_TYPE):
    n = 1
    if context.args:
        try:
            n = int(context.args[0])
        except:
            n = 1
    chosen = pick_many(EXERCISE_SETS, n)
    text = "\n\n".join(_format_exercise(x) for x in chosen)
    for chunk in split_chunks(text):
        await update.message.reply_text(chunk)

async def meditation(update: Update, context: ContextTypes.DEFAULT_TYPE):
    n = 1
    if context.args:
        try:
            n = int(context.args[0])
        except:
            n = 1
    chosen = pick_many(BREATHING_TECHNIQUES, n)
    lines = []
    for x in chosen:
        lines.append(f"💨 {x['title']}\nКак делать: {x['how']}")
    text = "\n\n".join(lines)
    for chunk in split_chunks(text):
        await update.message.reply_text(chunk)

async def yoga(update: Update, context: ContextTypes.DEFAULT_TYPE):
    n = 1
    if context.args:
        try:
            n = int(context.args[0])
        except:
            n = 1
    chosen = pick_many(YOGA_POSES, n)
    lines = [f"🧘 {x['title']}\nКак делать: {x['how']}" for x in chosen]
    text = "\n\n".join(lines)
    for chunk in split_chunks(text):
        await update.message.reply_text(chunk)

async def nutrition(update: Update, context: ContextTypes.DEFAULT_TYPE):
    n = 5
    if context.args:
        try:
            n = int(context.args[0])
        except:
            n = 5
    chosen = pick_many(NUTRITION_TIPS, n)
    text = "🥗 Советы по питанию:\n" + "\n".join([f"• {t}" for t in chosen])
    for chunk in split_chunks(text):
        await update.message.reply_text(chunk)

async def analysis(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not context.args:
        await update.message.reply_text("Использование: /analysis <название> или /analysis list")
        return
    key = " ".join(context.args).strip().lower()
    if key == "list":
        keys = sorted({v["name"] for v in LABS.values()})
        rus = sorted(set(list(LABS_ALIASES.keys())))
        text = (
            "Доступные анализы (основные названия):\n- " + "\n- ".join(keys) +
            "\n\nМожно писать по-русски: " + ", ".join(rus)
        )
        for ch in split_chunks(text):
            await update.message.reply_text(ch)
        return

    # нормализуем на англ ключ
    if key in LABS:
        code = key
    else:
        code = LABS_ALIASES.get(key)

    if not code or code not in LABS:
        await update.message.reply_text("Не узнал анализ. Напиши /analysis list — покажу, что есть.")
        return

    info = LABS[code]
    text = f"🧪 {info['name']}\nНорма: {info['normal']}\nПояснение: {info['more']}\n\nВажно: ориентируйся на референты своей лаборатории и рекомендации врача."
    await update.message.reply_text(text)

async def water(update: Update, context: ContextTypes.DEFAULT_TYPE):
    uid = update.effective_user.id
    day = today_key()
    user = WATER.setdefault(uid, {})
    current = user.get(day, 0)

    action = None
    value = None
    if context.args:
        if context.args[0].lower() in ("add", "set", "reset"):
            action = context.args[0].lower()
            if action in ("add", "set") and len(context.args) >= 2:
                try:
                    value = int(context.args[1])
                except:
                    value = None

    if action is None:
        # просто добавляем 250 мл
        current += 250
        user[day] = current
        await update.message.reply_text(f"💧 Отмечено 250 мл. Всего сегодня: {current} мл (цель ~2000 мл).")
        return

    if action == "reset":
        user[day] = 0
        await update.message.reply_text("♻️ Сброс воды за сегодня. Текущий объём: 0 мл.")
        return

    if action == "add":
        if value is None or value <= 0:
            await update.message.reply_text("Использование: /water add 300")
            return
        current += value
        user[day] = current
        await update.message.reply_text(f"💧 Добавлено {value} мл. Всего сегодня: {current} мл.")
        return

    if action == "set":
        if value is None or value < 0:
            await update.message.reply_text("Использование: /water set 1200")
            return
        user[day] = value
        await update.message.reply_text(f"🔧 Установлено: {value} мл за сегодня.")
        return

async def biorhythm(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not context.args:
        await update.message.reply_text("Использование: /biorhythm DD.MM.YYYY (дата рождения)")
        return
    try:
        bdate = datetime.strptime(context.args[0], "%d.%m.%Y").date()
    except Exception:
        await update.message.reply_text("Неверный формат. Пример: /biorhythm 14.02.1990")
        return

    res = biorhythm_for(bdate, date.today())
    def emoji(v):
        return "⬆️" if v > 0.33 else "➡️" if v > -0.33 else "⬇️"
    msg = (
        f"📈 Биоритмы на сегодня:\n"
        f"Физический: {res['physical']:.2f} {emoji(res['physical'])}\n"
        f"Эмоциональный: {res['emotional']:.2f} {emoji(res['emotional'])}\n"
        f"Интеллектуальный: {res['intellectual']:.2f} {emoji(res['intellectual'])}\n"
        "Знак > 0 — фаза подъёма, < 0 — спада."
    )
    await update.message.reply_text(msg)

# ==============================
# Telegram Application (PTB 21.x)
# ==============================
application: Application = ApplicationBuilder().token(TOKEN).build()

# Регистрируем команды
application.add_handler(CommandHandler("start", start))
application.add_handler(CommandHandler("help", help_command))
application.add_handler(CommandHandler("menu", menu_command))
application.add_handler(CommandHandler("exercise", exercise))
application.add_handler(CommandHandler("meditation", meditation))
application.add_handler(CommandHandler("yoga", yoga))
application.add_handler(CommandHandler("nutrition", nutrition))
application.add_handler(CommandHandler("analysis", analysis))
application.add_handler(CommandHandler("water", water))
application.add_handler(CommandHandler("biorhythm", biorhythm))

# ==============================
# Flask (приём webhook + health)
# ==============================
app = Flask(__name__)

@app.get("/")
def home():
    return "OK"

@app.get("/healthz")
def healthz():
    # используем aware-время в UTC
    return jsonify(ok=True, time=datetime.now().astimezone().isoformat())

@app.post(WEBHOOK_PATH)
async def tg_webhook():
    if request.headers.get("content-type") != "application/json":
        return abort(403)
    data = request.get_json(silent=True, force=True)
    if not data:
        return "no json", 400
    update = Update.de_json(data=data, bot=application.bot)
    await application.process_update(update)
    return "ok", 200

# ==============================
# Старт: инициализация, сброс/установка webhook и запуск Flask
# ==============================
async def setup_webhook():
    # Готовим PTB к работе в webhook-режиме
    await application.initialize()
    # На всякий случай удаляем предыдущий вебхук и старые апдейты
    try:
        await application.bot.delete_webhook(drop_pending_updates=True)
    except Exception:
        pass
    # Ставим актуальный вебхук
    await application.bot.set_webhook(WEBHOOK_URL, allowed_updates=Update.ALL_TYPES)
    # Запускаем application (нужен для job-очереди и корректной обработки)
    await application.start()
    print(f"[OK] Webhook set to {WEBHOOK_URL}")

if __name__ == "__main__":
    # Однократная настройка webhook при запуске
    import asyncio
    asyncio.run(setup_webhook())
    # Запуск Flask-сервера (Render детектит порт)
    app.run(host="0.0.0.0", port=PORT)
