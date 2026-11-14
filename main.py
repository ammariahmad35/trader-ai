import time
import sqlite3
import requests
from datetime import datetime
from database import init_db, DB_NAME
from notifier import send_telegram_alert, send_reply, check_arabic_commands
from bots.new_coins import analyze_and_scan_new_coins

init_db()
send_telegram_alert("Sys", "ALL", "v3", "System Started")
send_reply("Bot Started: 5s Auto-Trading + Capital Protection + Hourly Report Active.")

SYMBOLS = ["BTCUSDT", "ETHUSDT", "SOLUSDT", "BNBUSDT", "XRPUSDT"]
last_prices = {}
open_trades = []
hour_wins = 0
hour_losses = 0
hour_pnl = 0.0

lid = 0
lscan = 0
ltrade = 0
lhour = time.time()

def get_live_prices():
    try:
        r = requests.get("https://binance.com", timeout=4)
        if r.status_code == 200:
            return {item["symbol"]: float(item["price"]) for item in r.json() if item["symbol"] in SYMBOLS}
    except Exception:
        pass
    return {}

def manage_and_trade():
    global hour_wins, hour_losses, hour_pnl, open_trades
    prices = get_live_prices()
    if not prices:
        return

    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    c.execute("SELECT balance FROM wallet WHERE id=1")
    row = c.fetchone()
    balance = float(row[0]) if row and row[0] is not None else 1000.0

    remaining = []
    for t in open_trades:
        sym = t["symbol"]
        curr = prices.get(sym, t["entry"])
        change = (curr - t["entry"]) / t["entry"] if t["side"] == "BUY" else (t["entry"] - curr) / t["entry"]

        if change >= 0.0025 or change <= -0.0015:
            pnl = round(t["amount"] * change * 10, 2)
            balance = round(balance + pnl, 2)
            hour_pnl = round(hour_pnl + pnl, 2)
            if pnl > 0:
                hour_wins += 1
            else:
                hour_losses += 1
            c.execute("UPDATE wallet SET balance=? WHERE id=1", (balance,))
            c.execute("INSERT INTO trades (symbol, side, entry, exit_price, pnl, status, created_at) VALUES (?, ?, ?, ?, ?, ?, ?)",
                      (sym, t["side"], t["entry"], curr, pnl, "CLOSED", str(datetime.now())))
        else:
            remaining.append(t)
    open_trades = remaining

    if len(open_trades) < 3 and balance > 50:
        for sym, curr in prices.items():
            if sym in last_prices and not any(x["symbol"] == sym for x in open_trades):
                prev = last_prices[sym]
                diff = (curr - prev) / prev
                if abs(diff) >= 0.0002:
                    side = "BUY" if diff > 0 else "SELL"
                    amount = round(balance * 0.05, 2)
                    open_trades.append({"symbol": sym, "side": side, "entry": curr, "amount": amount})
                    break

    last_prices.update(prices)
    conn.commit()
    conn.close()

while True:
    lid = check_arabic_commands(lid)
    now = time.time()

    if now - ltrade >= 5:
        manage_and_trade()
        ltrade = now

    if now - lscan >= 45:
        analyze_and_scan_new_coins()
        lscan = now

    if now - lhour >= 3600:
        conn = sqlite3.connect(DB_NAME)
        c = conn.cursor()
        c.execute("SELECT balance FROM wallet WHERE id=1")
        row = c.fetchone()
        bal = float(row[0]) if row and row[0] is not None else 1000.0
        conn.close()

        t_title = "\u0627\u0644\u062a\u0642\u0631\u064a\u0631 \u0627\u0644\u0633\u0627\u0639\u064a \u0644\u0644\u0628\u0648\u062a"
        t_win = "\u0627\u0644\u0635\u0641\u0642\u0627\u062a \u0627\u0644\u0631\u0627\u0628\u062d\u0629"
        t_loss = "\u0627\u0644\u0635\u0641\u0642\u0627\u062a \u0627\u0644\u062e\u0627\u0633\u0631\u0629"
        t_pnl = "\u0635\u0627\u0641\u064a \u0631\u0628\u062d \u0627\u0644\u0633\u0627\u0639\u0629"
        t_bal = "\u0631\u0635\u064a\u062f \u0627\u0644\u0645\u062d\u0641\u0638\u0629"

        report = (
            f"{t_title}\n"
            f"--------------\n"
            f"{t_win}: {hour_wins}\n"
            f"{t_loss}: {hour_losses}\n"
            f"{t_pnl}: {hour_pnl:+.2f}$\n"
            f"{t_bal}: {bal:.2f}$"
        )
        send_reply(report)
        hour_wins = 0
        hour_losses = 0
        hour_pnl = 0.0
        lhour = now

    time.sleep(1)
