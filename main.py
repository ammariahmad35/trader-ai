import time
from database import init_db
from notifier import send_telegram_alert, check_arabic_commands
from bots.new_coins import analyze_and_scan_new_coins

init_db()
send_telegram_alert("Sys", "ALL", "v3", "System Started")
lid, lscan = 0, 0
while True:
    lid = check_arabic_commands(lid)
    if time.time() - lscan >= 45:
        analyze_and_scan_new_coins()
        lscan = time.time()
    time.sleep(2)
