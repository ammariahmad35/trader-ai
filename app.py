import os, time, hashlib, sqlite3, requests
from datetime import datetime
from dotenv import load_dotenv

load_dotenv()
S = chr(47)
H = "https:" + S * 2
TOKEN = os.getenv("TELEGRAM_TOKEN")
CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")
TG_URL = H + "api." + "telegram.org" + S + "bot" + str(TOKEN)
DB = "crypto_system.db"

def init_db():
    conn = sqlite3.connect(DB)
    c = conn.cursor()
    c.execute("CREATE TABLE IF NOT EXISTS alerts (id INTEGER PRIMARY KEY AUTOINCREMENT, h TEXT UNIQUE, bot TEXT, sym TEXT, msg TEXT, dt TEXT)")
    c.execute("CREATE TABLE IF NOT EXISTS wallet (id INTEGER PRIMARY KEY, bal REAL)")
    c.execute("INSERT OR IGNORE INTO wallet VALUES (1, 1000.0)")
    c.execute("CREATE TABLE IF NOT EXISTS trades (id INTEGER PRIMARY KEY AUTOINCREMENT, sym TEXT, side TEXT, price REAL, usd REAL, status TEXT, dt TEXT)")
    conn.commit()
    conn.close()

def send_tg(bot, sym, uid, text):
    h = hashlib.md5(f"{bot}_{uid}".encode()).hexdigest()
    conn = sqlite3.connect(DB)
    c = conn.cursor()
    c.execute("SELECT 1 FROM alerts WHERE h=?", (h,))
    if c.fetchone():
        conn.close()
        return False
    try:
        r = requests.post(TG_URL + S + "sendMessage", json={"chat_id": CHAT_ID, "text": text, "parse_mode": "HTML"}, timeout=10)
        if r.status_code == 200:
            c.execute("INSERT INTO alerts VALUES (NULL,?,?,?,?,?)", (h, bot, sym, text, datetime.now().strftime("%Y-%m-%d %H:%M:%S")))
            conn.commit()
            conn.close()
            print("[SENT]", sym)
            return True
    except Exception as e:
        print("[TG ERR]", e)
    conn.close()
    return False

def reply_tg(text):
    try:
        requests.post(TG_URL + S + "sendMessage", json={"chat_id": CHAT_ID, "text": text, "parse_mode": "HTML"}, timeout=8)
    except Exception:
        pass

def check_cmds(last_id):
    try:
        res = requests.get(TG_URL + S + "getUpdates", params={"offset": last_id + 1, "timeout": 2}, timeout=8).json()
        for u in res.get("result", []):
            last_id = u["update_id"]
            m = u.get("message", {})
            if str(m.get("chat", {}).get("id", "")) != str(CHAT_ID):
                continue
            txt = m.get("text", "")
            conn = sqlite3.connect(DB)
            c = conn.cursor()
            if "\u0627\u0644\u0631\u0635\u064a\u062f" in txt:
                c.execute("SELECT bal FROM wallet WHERE id=1")
                bal = list(c.fetchone()).pop(0)
                reply_tg(f"\U0001f4b0 \u0627\u0644\u0631\u0635\u064a\u062f \u0627\u0644\u062a\u062c\u0631\u064a\u0628\u064a: <b>{bal:.2f} USDT</b>")
            elif "\u0627\u0644\u0635\u0641\u0642\u0627\u062a" in txt:
                c.execute("SELECT COUNT(*) FROM trades")
                cnt = list(c.fetchone()).pop(0)
                reply_tg(f"\U0001f4c8 \u0639\u062f\u062f \u0627\u0644\u0635\u0641\u0642\u0627\u062a \u0627\u0644\u062a\u062c\u0631\u064a\u0628\u064a\u0629: <b>{cnt}</b>")
            else:
                reply_tg("\u2705 \u0627\u0644\u0645\u0646\u0638\u0648\u0645\u0629 \u062a\u0639\u0645\u0644! \u0627\u0643\u062a\u0628 <b>\u0627\u0644\u0631\u0635\u064a\u062f</b> \u0623\u0648 <b>\u0627\u0644\u0635\u0641\u0642\u0627\u062a</b>")
            conn.close()
    except Exception:
        pass
    return last_id

def scan_market():
    print("[Scanning] Coins, Liquidity, News & Celebs...")
    dex_u1 = H + "api." + "dexscreener.com" + S + "token-profiles" + S + "latest" + S + "v1"
    dex_u2 = H + "api." + "dexscreener.com" + S + "latest" + S + "dex" + S + "tokens" + S
    try:
        tokens = requests.get(dex_u1, timeout=10).json()
        for item in (tokens if isinstance(tokens, list) else [])[:10]:
            ch = item.get("chainId", "").lower()
            if ch not in ["solana", "ethereum", "bsc"]:
                continue
            addr = item.get("tokenAddress", "")
            pairs = requests.get(dex_u2 + addr, timeout=8).json().get("pairs") or []
            if not pairs:
                continue
            p = pairs.pop(0)
            sym = p.get("baseToken", {}).get("symbol", "COIN")
            liq = float((p.get("liquidity") or {}).get("usd") or 0)
            buys = int(((p.get("txns") or {}).get("h1") or {}).get("buys") or 0)
            sells = int(((p.get("txns") or {}).get("h1") or {}).get("sells") or 0)
            url = p.get("url", H + "dexscreener.com")
            if liq < 5000 or buys < 10:
                continue
            strong = (liq >= 40000 and buys > sells * 1.2)
            risk = "\u0645\u062a\u0648\u0633\u0637\u0629 \u2705" if strong else "\u0645\u0631\u062a\u0641\u0639\u0629 \u26a0\ufe0f"
            msg = (
                f"\U0001f680 <b>\u0639\u0645\u0644\u0629 \u062c\u062f\u064a\u062f\u0629:</b> {sym} ({ch.upper()})\n"
                f"\u2022 \u0627\u0644\u0633\u064a\u0648\u0644\u0629: ${liq:,.0f} | \u0627\u0644\u0645\u0634\u062a\u0631\u0648\u0646: {buys} | \u0627\u0644\u0628\u0627\u0626\u0639\u0648\u0646: {sells}\n"
                f"\u2022 \u0627\u0644\u0645\u062e\u0627\u0637\u0631: {risk}\n"
                f"\U0001f4cb <code>{addr}</code>\n"
                f"\U0001f517 <a href='{url}'>DexScreener</a>"
            )
            if send_tg("CoinBot", sym, addr, msg) and strong:
                conn = sqlite3.connect(DB)
                c = conn.cursor()
                c.execute("SELECT bal FROM wallet WHERE id=1")
                bal = list(c.fetchone()).pop(0)
                if bal >= 50:
                    c.execute("UPDATE wallet SET bal=bal-50 WHERE id=1")
                    c.execute("INSERT INTO trades VALUES (NULL,?,'BUY',?,50.0,'OPEN',?)", (sym, float(p.get("priceUsd") or 0), datetime.now().strftime("%Y-%m-%d %H:%M:%S")))
                    conn.commit()
                conn.close()
    except Exception as e:
        print("[CoinErr]", e)

    news_u = H + "cointelegraph.com" + S + "rss"
    try:
        import xml.etree.ElementTree as ET
        xml_data = requests.get(news_u, headers={"User-Agent": "Mozilla/5.0"}, timeout=10).text
        items = ET.fromstring(xml_data).findall(".//item")[:6]
        for n in items:
            t = n.findtext("title", "")
            u = n.findtext("link", "")
            is_c = any(k in t.lower() for k in ["elon", "musk", "trump", "vitalik", "cz", "sec", "etf"])
            tag = "\U0001f31f <b>\u0645\u0634\u0627\u0647\u064a\u0631/\u062d\u062f\u062b:</b> " if is_c else "\U0001f4f0 <b>\u062e\u0628\u0631:</b> "
            send_tg("NewsBot", "NEWS", t[:30], f"{tag}{t}\n<a href='{u}'>\u0627\u0644\u0631\u0627\u0628\u0637</a>")
    except Exception as e:
        print("[NewsErr]", e)

if __name__ == "__main__":
    init_db()
    send_tg("Sys", "START", "run_final_1", "\U0001f916 <b>\u0628\u062f\u0623 \u0627\u0644\u0641\u062d\u0635 \u0627\u0644\u062d\u064a \u0644\u0644\u0639\u0645\u0644\u0627\u062a \u0648\u0627\u0644\u0623\u062e\u0628\u0627\u0631!</b>")
    lid, lscan = 0, 0
    while True:
        lid = check_cmds(lid)
        if time.time() - lscan >= 45:
            scan_market()
            lscan = time.time()
        time.sleep(2)
