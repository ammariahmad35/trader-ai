import time
from database import init_db
from notifier import send_telegram_alert, check_arabic_commands, MSG_W
from bots.engine import scan_all
init_db()
send_telegram_alert("Sys", "ALL", "v3", MSG_W)
lid, lscan = 0, 0
while True:
    lid = check_arabic_commands(lid)
    if time.time() - lscan >= 45:
        scan_all()
        lscan = time.time()
    time.sleep(2)
