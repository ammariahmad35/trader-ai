import requests
from notifier import send_telegram_alert

S = chr(47)
DEX_PROFILES_URL = "https:" + S*2 + "://dexscreener.com" + S + "token-profiles" + S + "latest" + S + "v1"
DEX_TOKEN_URL = "https:" + S*2 + "://dexscreener.com" + S + "latest" + S + "dex" + S + "tokens" + S

def analyze_and_scan_new_coins():
    print("[Scanner] Checking latest tokens on Solana, Ethereum, BSC...")
    try:
        res = requests.get(DEX_PROFILES_URL, timeout=12)
        if res.status_code != 200:
            return
        tokens = res.json()
        if not isinstance(tokens, list):
            return

        for item in tokens[:12]:
            chain = item.get("chainId", "").lower()
            if chain not in ["solana", "ethereum", "bsc"]:
                continue

            address = item.get("tokenAddress", "")
            if not address:
                continue

            pair_res = requests.get(DEX_TOKEN_URL + address, timeout=10)
            if pair_res.status_code != 200:
                continue

            pairs = pair_res.json().get("pairs") or []
            if not pairs:
                continue

            p = pairs[0]
            symbol = p.get("baseToken", {}).get("symbol", "UNKNOWN")
            price = float(p.get("priceUsd") or 0)
            liq = float((p.get("liquidity") or {}).get("usd") or 0)
            vol_h1 = float((p.get("volume") or {}).get("h1") or 0)
            txns = (p.get("txns") or {}).get("h1") or {}
            buys = int(txns.get("buys") or 0)
            sells = int(txns.get("sells") or 0)
            dex_url = p.get("url", "https:" + S*2 + "dexscreener.com")

            if liq < 5000 or buys < 10:
                continue

            if liq >= 50000 and buys > sells * 1.3:
                risk_txt = "\u0645\u0646\u062e\u0641\u0636\u0629 \u0625\u0644\u0649 \u0645\u062a\u0648\u0633\u0637\u0629 \u2705"
                reason_txt = "\u0633\u064a\u0648\u0644\u0629 \u0642\u0648\u064a\u0629 \u0648\u0636\u063a\u0637 \u0634\u0631\u0627\u0621 \u0645\u0631\u062a\u0641\u0639"
            else:
                risk_txt = "\u0645\u0631\u062a\u0641\u0639\u0629 (\u0639\u0645\u0644\u0629 \u062c\u062f\u064a\u062f\u0629) \u26a0\ufe0f"
                reason_txt = "\u062a\u062f\u0641\u0642 \u0645\u0634\u062a\u0631\u064a\u0646 \u062c\u062f\u062f \u0628\u0639\u062f \u0627\u0644\u0625\u0637\u0644\u0627\u0642 \u0645\u0628\u0627\u0634\u0631\u0629"

            msg = (
                "\U0001f680 <b>\u0627\u0643\u062a\u0634\u0627\u0641 \u0639\u0645\u0644\u0629 \u062c\u062f\u064a\u062f\u0629 + \u062a\u062d\u0644\u064a\u0644 \u0627\u0644\u0633\u064a\u0648\u0644\u0629!</b>\n\n"
                f"\u2022 <b>\u0627\u0644\u0639\u0645\u0644\u0629:</b> {symbol}\n"
                f"\u2022 <b>\u0627\u0644\u0634\u0628\u0643\u0629:</b> {chain.upper()}\n"
                f"\u2022 <b>\u0627\u0644\u0633\u0639\u0631:</b> ${price:.8f}\n"
                f"\u2022 <b>\u0627\u0644\u0633\u064a\u0648\u0644\u0629:</b> ${liq:,.0f}\n"
                f"\u2022 <b>\u062d\u062c\u0645 \u0627\u0644\u062a\u062f\u0627\u0648\u0644 (\u0633\u0627\u0639\u0629):</b> ${vol_h1:,.0f}\n"
                f"\u2022 <b>\u0627\u0644\u0645\u0634\u062a\u0631\u0648\u0646 / \u0627\u0644\u0628\u0627\u0626\u0639\u0648\u0646:</b> {buys} \u0634\u0631\u0627\u0621 | {sells} \u0628\u064a\u0639\n"
                f"\u2022 <b>\u0633\u0628\u0628 \u0627\u0644\u0627\u0643\u062a\u0634\u0627\u0641:</b> {reason_txt}\n"
                f"\u2022 <b>\u0627\u0644\u0645\u062e\u0627\u0637\u0631 \u0627\u0644\u0645\u062d\u062a\u0645\u0644\u0629:</b> {risk_txt}\n\n"
                f"\U0001f4cb <b>\u0639\u0646\u0648\u0627\u0646 \u0627\u0644\u0639\u0642\u062f:</b>\n<code>{address}</code>\n\n"
                f"\U0001f517 <a href='{dex_url}'>\u0641\u062a\u062d \u0627\u0644\u0639\u0645\u0644\u0629 \u0639\u0644\u0649 DexScreener</a>"
            )
            send_telegram_alert("NewCoinsBot", symbol, f"{chain}_{address}", msg)
    except Exception as e:
        print("[Scanner Error]", e)
