import os, hashlib, requests, sqlite3
from dotenv import load_dotenv
from database import is_duplicate_alert, save_alert, DB_NAME
load_dotenv()
S = chr(47)
TOKEN = os.getenv("TELEGRAM_TOKEN")
CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")
BASE = "https:" + S*2 + "api.telegram.org" + S + "bot" + str(TOKEN)
MSG_W = "\u0623\u0647\u0644\u0627\u064b \u0628\u0643 \u064a\u0627 \u0645\u0644\u0643! \U0001f916 \u0627\u0644\u0645\u0646\u0638\u0648\u0645\u0629 \u0627\u0644\u0643\u0627\u0645\u0644\u0629 \u062a\u0639\u0645\u0644 \u0627\u0644\u0622\u0646!"
def send_telegram_alert(b, sym, uid, txt):
    h = hashlib.md5(f"{b}_{uid}".encode()).hexdigest()
    if is_duplicate_alert(h): return False
    try:
        r = requests.post(BASE + S + "sendMessage", json={"chat_id": CHAT_ID, "text": txt, "parse_mode": "HTML"}, timeout=10)
        if r.status_code == 200:
            save_alert(h, b, sym, txt); print("[SENT]", sym); return True
    except Exception as e: print("[ERR]", e)
    return False
def send_reply(t):
    try: requests.post(BASE + S + "sendMessage", json={"chat_id": CHAT_ID, "text": t, "parse_mode": "HTML"}, timeout=8)
    except Exception: pass
def check_arabic_commands(last_id):
    try:
        res = requests.get(BASE + S + "getUpdates", params={"offset": last_id+1, "timeout": 3}, timeout=8).json()
        for u in res.get("result", []):
            last_id = u["update_id"]; m = u.get("message", {})
            if str(m.get("chat", {}).get("id", "")) != str(CHAT_ID): continue
            txt = m.get("text", "")
            if "\u0627\u0644\u0631\u0635\u064a\u062f" in txt:
                conn = sqlite3.connect(DB_NAME); c = conn.cursor(); c.execute("SELECT balance FROM wallet WHERE id=1")
                bal = c.fetchone()[0]; conn.close()
                send_reply(f"\U0001f4b0 \u0627\u0644\u0631\u0635\u064a\u062f: <b>{bal:.2f} USDT</b>")
            else: send_reply(MSG_W)
    except Exception: pass
    return last_id
