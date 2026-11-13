import sqlite3
from datetime import datetime
DB_NAME = "crypto_system.db"
def init_db():
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    c.execute("CREATE TABLE IF NOT EXISTS alerts (id INTEGER PRIMARY KEY AUTOINCREMENT, event_hash TEXT UNIQUE, bot_name TEXT, symbol TEXT, message TEXT, created_at TEXT)")
    c.execute("CREATE TABLE IF NOT EXISTS wallet (id INTEGER PRIMARY KEY, balance REAL)")
    c.execute("INSERT OR IGNORE INTO wallet (id, balance) VALUES (1, 1000.0)")
    c.execute("CREATE TABLE IF NOT EXISTS trades (id INTEGER PRIMARY KEY AUTOINCREMENT, symbol TEXT, side TEXT, entry_price REAL, amount_usd REAL, status TEXT, pnl REAL DEFAULT 0.0, timestamp TEXT)")
    conn.commit()
    conn.close()
def is_duplicate_alert(h):
    conn = sqlite3.connect(DB_NAME); c = conn.cursor(); c.execute("SELECT 1 FROM alerts WHERE event_hash=?", (h,))
    ok = c.fetchone() is not None; conn.close(); return ok
def save_alert(h, b, s, m):
    conn = sqlite3.connect(DB_NAME); c = conn.cursor(); c.execute("INSERT OR IGNORE INTO alerts VALUES (NULL,?,?,?,?,?)", (h, b, s, m, datetime.now().strftime("%Y-%m-%d %H:%M:%S"))); conn.commit(); conn.close()
