import sqlite3
from datetime import datetime

DB_NAME = "crypto_system.db"

def init_db():
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    c.execute("CREATE TABLE IF NOT EXISTS alerts (hash TEXT PRIMARY KEY, bot TEXT, symbol TEXT, message TEXT, created_at TEXT)")
    c.execute("CREATE TABLE IF NOT EXISTS wallet (id INTEGER PRIMARY KEY, balance REAL)")
    try:
        c.execute("ALTER TABLE wallet ADD COLUMN balance REAL DEFAULT 1000.0")
    except Exception:
        pass
    c.execute("INSERT OR IGNORE INTO wallet (id, balance) VALUES (1, 1000.0)")
    c.execute("UPDATE wallet SET balance=1000.0 WHERE id=1 AND balance IS NULL")
    c.execute("CREATE TABLE IF NOT EXISTS trades (id INTEGER PRIMARY KEY AUTOINCREMENT, symbol TEXT, side TEXT, entry REAL, exit_price REAL, pnl REAL, status TEXT, created_at TEXT)")
    conn.commit()
    conn.close()

def is_duplicate_alert(h):
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    c.execute("SELECT 1 FROM alerts WHERE hash=?", (h,))
    ok = c.fetchone() is not None
    conn.close()
    return ok

def save_alert(h, b, s, m):
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    c.execute("INSERT OR IGNORE INTO alerts VALUES (?, ?, ?, ?, ?)", (h, b, s, m, str(datetime.now())))
    conn.commit()
    conn.close()
