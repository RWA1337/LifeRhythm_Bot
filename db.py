import sqlite3
from config import DB_PATH
from contextlib import closing

def init_db():
    with closing(sqlite3.connect(DB_PATH)) as conn:
        cur = conn.cursor()
        cur.executescript("""
        CREATE TABLE IF NOT EXISTS users (
            tg_id INTEGER PRIMARY KEY,
            first_name TEXT,
            last_name TEXT,
            username TEXT,
            sex TEXT,
            age INTEGER,
            height_cm REAL,
            weight_kg REAL,
            goal TEXT,
            created_at TEXT DEFAULT CURRENT_TIMESTAMP
        );
        CREATE TABLE IF NOT EXISTS water (
            tg_id INTEGER,
            day TEXT,
            amount_ml INTEGER,
            PRIMARY KEY (tg_id, day)
        );
        CREATE TABLE IF NOT EXISTS challenges (
            tg_id INTEGER,
            challenge TEXT,
            start_day TEXT,
            progress INTEGER,
            streak INTEGER,
            PRIMARY KEY (tg_id, challenge)
        );
        CREATE TABLE IF NOT EXISTS logs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            tg_id INTEGER,
            event TEXT,
            created_at TEXT DEFAULT CURRENT_TIMESTAMP
        );
        """)
        conn.commit()

def get_conn():
    return sqlite3.connect(DB_PATH)
