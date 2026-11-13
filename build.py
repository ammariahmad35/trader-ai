import os

S = chr(47)
H = "https:" + S * 2

with open(".env", "w") as f:
    f.write("TELEGRAM_TOKEN=8894693945:AAF8VGU0oSJnHYTVqdPPWP_Wfkc6yxPjf_g\n")
    f.write("TELEGRAM_CHAT_ID=5754171593\n")

db_code = """import sqlite3
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

def is_duplicate_alert(event_hash):
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    c.execute("SELECT 1 FROM alerts WHERE event_hash = ?", (event_hash,))
    exists = c.fetchone() is not None
    conn.close()
    return exists

def save_alert(event_hash, bot_name, symbol, message):
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    c.execute("INSERT OR IGNORE INTO alerts (event_hash, bot_name, symbol, message, created_at) VALUES (?, ?, ?, ?, ?)", (event_hash, bot_name, symbol, message, now))
    conn.commit()
    conn.close()
"""
open("database.py", "w").write(db_code)

notifier_code = f"""import os, hashlib, requests, sqlite3
from dotenv import load_dotenv
from database import is_duplicate_alert, save_alert, DB_NAME

load_dotenv()
TOKEN = os.getenv("TELEGRAM_TOKEN")
CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")
BASE_URL = "{H}api.telegram.org{S}bot" + str(TOKEN)

MSG_WELCOME = "\\u0623\\u0647\\u0644\\u0627\\u064b \\u0628\\u0643 \\u064a\\u0627 \\u0645\\u0644\\u0643! \\U0001f916\\n\\u062a\\u0645 \\u062a\\u0634\\u063a\\u064a\\u0644 \\u0627\\u0644\\u0645\\u0646\\u0638\\u0648\\u0645\\u0629 \\u0627\\u0644\\u0643\\u0627\\u0645\\u0644\\u0629 (5 \\u0628\\u0648\\u062a\\u0627\\u062a + \\u062a\\u062f\\u0627\\u0648\\u0644 \\u062a\\u062c\\u0631\\u064a\\u0628\\u064a 1000$).\\n\\u0627\\u0643\\u062a\\u0628: <b>\\u0627\\u0644\\u0631\\u0635\\u064a\\u062f</b> \\u0623\\u0648 <b>\\u0627\\u0644\\u062d\\u0627\\u0644\\u0629</b> \\u0623\\u0648 <b>\\u0627\\u0644\\u0635\\u0641\\u0642\\u0627\\u062a</b>"
MSG_STATUS = "\\u2705 \\u062c\\u0645\\u064a\\u0639 \\u0627\\u0644\\u0628\\u0648\\u062a\\u0627\\u062a \\u0627\\u0644\\u062e\\u0645\\u0633\\u0629 \\u062a\\u0639\\u0645\\u0644 \\u0628\\u0646\\u062c\\u0627\\u062d \\u0639\\u0644\\u0649 \\u0645\\u062f\\u0627\\u0631 \\u0627\\u0644\\u0633\\u0627\\u0639\\u0629!"

def send_telegram_alert(bot_name, symbol, unique_id, details_text):
    event_hash = hashlib.md5(f"{{bot_name}}_{{unique_id}}".encode()).hexdigest()
    if is_duplicate_alert(event_hash):
        return False
    url = BASE_URL + "{S}sendMessage"
    payload = {{"chat_id": CHAT_ID, "text": details_text, "parse_mode": "HTML"}}
    try:
        r = requests.post(url, json=payload, timeout=10)
        if r.status_code == 200:
            save_alert(event_hash, bot_name, symbol, details_text)
            print("[SENT] " + symbol)
            return True
    except Exception as e:
        print("[ERR]", e)
    return False

def send_direct_reply(text):
    try:
        requests.post(BASE_URL + "{S}sendMessage", json={{"chat_id": CHAT_ID, "text": text, "parse_mode": "HTML"}}, timeout=10)
    except Exception:
        pass

def check_arabic_commands(last_update_id):
    try:
        res = requests.get(BASE_URL + "{S}getUpdates", params={{"offset": last_update_id + 1, "timeout": 3}}, timeout=8).json()
        for update in res.get("result", []):
            last_update_id = update["update_id"]
            msg = update.get("message", {{}})
            if str(msg.get("chat", {{}}).get("id", "")) != str(CHAT_ID):
                continue
            txt = msg.get("text", "").strip()
            if "\\u0645\\u0631\\u062d\\u0628\\u0627" in txt or "start" in txt:
                send_direct_reply(MSG_WELCOME)
            elif "\\u0627\\u0644\\u0631\\u0635\\u064a\\u062f" in txt:
                conn = sqlite3.connect(DB_NAME)
                c = conn.cursor()
                c.execute("SELECT balance FROM wallet WHERE id = 1")
                row = c.fetchone()
                bal = row[0] if row else 1000.0
                conn.close()
                send_direct_reply(f"\\U0001f4b0 \\u0627\\u0644\\u0631\\u0635\\u064a\\u062f \\u0627\\u0644\\u062a\\u062c\\u0631\\u064a\\u0628\\u064a: <b>{{bal:.2f}} USDT</b>")
            elif "\\u0627\\u0644\\u062d\\u0627\\u0644\\u0629" in txt:
                send_direct_reply(MSG_STATUS)
            elif "\\u0627\\u0644\\u0635\\u0641\\u0642\\u0627\\u062a" in txt:
                conn = sqlite3.connect(DB_NAME)
                c = conn.cursor()
                c.execute("SELECT COUNT(*) FROM trades")
                row = c.fetchone()
                cnt = row[0] if row else 0
                conn.close()
                send_direct_reply(f"\\U0001f4c8 \\u0639\\u062f\\u062f \\u0627\\u0644\\u0635\\u0641\\u0642\\u0627\\u062a \\u0627\\u0644\\u062a\\u062c\\u0631\\u064a\\u0628\\u064a\\u0629: <b>{{cnt}}</b>")
    except Exception:
        pass
    return last_update_id
"""
open("notifier.py", "w").write(notifier_code)

os.makedirs("bots", exist_ok=True)
open("bots/__init__.py", "w").write("")

scanner_code = f"""import requests, sqlite3
from datetime import datetime
from notifier import send_telegram_alert
from database import DB_NAME

U1 = "{H}://dexscreener.com{S}token-profiles{S}latest{S}v1"
U2 = "{H}://dexscreener.com{S}latest{S}dex{S}tokens{S}"

def execute_paper_trade(symbol, price):
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    c.execute("SELECT balance FROM wallet WHERE id = 1")
    row = c.fetchone()
    bal = row[0] if row else 0
    if bal >= 50.0:
        c.execute("UPDATE wallet SET balance = balance - 50.0 WHERE id = 1")
        now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        c.execute("INSERT INTO trades (symbol, side, entry_price, amount_usd, status, timestamp) VALUES (?, 'BUY', ?, 50.0, 'OPEN', ?)", (symbol, price, now))
        conn.commit()
    conn.close()

def run_new_coins_and_trader():
    print("[Bot 1 & 4 & 5] Scanning new coins & analyzing liquidity...")
    try:
        res = requests.get(U1, timeout=12).json()
        if not isinstance(res, list): return
        for item in res[:10]:
            chain = item.get("chainId", "").lower()
            if chain not in ["solana", "ethereum", "bsc"]: continue
            addr = item.get("tokenAddress", "")
            if not addr: continue
            p_res = requests.get(U2 + addr, timeout=10).json()
            pairs = p_res.get("pairs") or []
            if not pairs: continue
            p = pairs[0]
            sym = p.get("baseToken", {{}}).get("symbol", "TOKEN")
            price = float(p.get("priceUsd") or 0)
            liq = float((p.get("liquidity") or {{}}).get("usd") or 0)
            vol = float((p.get("volume") or {{}}).get("h1") or 0)
            tx = (p.get("txns") or {{}}).get("h1") or {{}}
            buys, sells = int(tx.get("buys") or 0), int(tx.get("sells") or 0)
            url = p.get("url", "{H}dexscreener.com")
            if liq < 5000 or buys < 10: continue
            strong = (liq >= 40000 and buys > sells * 1.2)
            risk = "\\u0645\\u062a\\u0648\\u0633\\u0637\\u0629 \\u2705" if strong else "\\u0645\\u0631\\u062a\\u0641\\u0639\\u0629 \\u26a0\\ufe0f"
            msg = (
                "\\U0001f680 <b>\\u0639\\u0645\\u0644\\u0629 \\u062c\\u062f\\u064a\\u062f\\u0629 + \\u062a\\u062d\\u0644\\u064a\\u0644 \\u0627\\u0644\\u0633\\u064a\\u0648\\u0644\\u0629!</b>\\n\\n"
                f"\\u2022 <b>\\u0627\\u0644\\u0639\\u0645\\u0644\\u0629:</b> {{sym}} ({{chain.upper()}})\\n"
                f"\\u2022 <b>\\u0627\\u0644\\u0633\\u0639\\u0631:</b> ${{price:.8f}}\\n"
                f"\\u2022 <b>\\u0627\\u0644\\u0633\\u064a\\u0648\\u0644\\u0629:</b> ${{liq:,.0f}} | <b>\\u0627\\u0644\\u062d\\u062c\\u0645:</b> ${{vol:,.0f}}\\n"
                f"\\u2022 <b>\\u0627\\u0644\\u0645\\u0634\\u062a\\u0631\\u0648\\u0646/\\u0627\\u0644\\u0628\\u0627\\u0626\\u0639\\u0648\\u0646:</b> {{buys}} / {{sells}}\\n"
                f"\\u2022 <b>\\u0627\\u0644\\u0645\\u062e\\u0627\\u0637\\u0631:</b> {{risk}}\\n"
                f"\\U0001f4cb <code>{{addr}}</code>\\n"
                f"\\U0001f517 <a href='{{url}}'>DexScreener</a>"
            )
            if send_telegram_alert("NewCoins", sym, f"{{chain}}_{{addr}}", msg) and strong:
                execute_paper_trade(sym, price)
    except Exception as e:
        print("[Scanner Err]", e)
"""
open("bots/new_coins.py", "w").write(scanner_code)

news_celeb_code = f"""import requests
from notifier import send_telegram_alert

NEWS_URL = "{H}://cryptocompare.com{S}data{S}v2{S}news{S}?lang=EN"
CELEB_KEYS = ["elon", "musk", "trump", "vitalik", "cz", "saylor", "sec", "etf", "binance", "blackrock"]

def run_news_and_celebs():
    print("[Bot 2 & 3] Checking Crypto News & Celeb Mentions...")
    try:
        res = requests.get(NEWS_URL, timeout=12).json()
        for item in res.get("Data", [])[:8]:
            nid = str(item.get("id", ""))
            title = item.get("title", "")
            url = item.get("url", "")
            src = item.get("source", "News")
            low = title.lower()
            is_celeb = any(k in low for k in CELEB_KEYS)
