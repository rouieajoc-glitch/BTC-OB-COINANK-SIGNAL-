import json
import os
import requests
from datetime import datetime, timezone, timedelta

API_KEY = os.environ["COINANK_API_KEY"]
SYMBOL = "BTCUSDT"
INTERVAL = "1h"
STATE_FILE = "seen_1h.json"
PH_TZ = timezone(timedelta(hours=8))

HEADERS = {"apikey": API_KEY}
SMC_URL = "https://open-api.coinank.com/api/indicator/smc"
PUSH_URL = "https://open-api.coinank.com/api/webhook/push"


def get_smc_data():
    params = {"symbol": SYMBOL, "interval": INTERVAL, "exchange": "Binance"}
    try:
        r = requests.get(SMC_URL, headers=HEADERS, params=params, timeout=10)
        data = r.json()
        if data.get("success"):
            return data["data"]
        print("API Error:", data)
    except Exception as e:
        print("Request failed:", e)
    return None


def get_price():
    for base in ("https://data-api.binance.vision", "https://api.binance.com"):
        try:
            r = requests.get(
                f"{base}/api/v3/ticker/price",
                params={"symbol": SYMBOL},
                timeout=10,
            )
            return float(r.json()["price"])
        except Exception as e:
            print("Price failed:", base, e)
    return None


def send_push(title, body):
    payload = {"title": title, "body": body, "sound": "1"}
    try:
        res = requests.post(PUSH_URL, headers=HEADERS, json=payload, timeout=10)
        print("Push sent:", res.status_code, res.text)
    except Exception as e:
        print("Push failed:", e)

    token = os.environ.get("TELEGRAM_BOT_TOKEN")
    chat_id = os.environ.get("TELEGRAM_CHAT_ID")
    if token and chat_id:
        try:
            r = requests.post(
                f"https://api.telegram.org/bot{token}/sendMessage",
                json={"chat_id": chat_id, "text": f"{title}\n{body}"},
                timeout=10,
            )
            print("Telegram sent:", r.status_code)
        except Exception as e:
            print("Telegram failed:", e)


def load_state():
    if os.path.exists(STATE_FILE):
        with open(STATE_FILE) as f:
            return json.load(f)
    return None


def save_state(state):
    with open(STATE_FILE, "w") as f:
        json.dump(state, f)


def main():
    data = get_smc_data()
    if not data:
        return

    state = load_state()
    first_run = state is None
    if first_run:
        state = {"bullish": [], "bearish": []}

    new_state = {"bullish": [], "bearish": []}
    price = None
    price_loaded = False

    for key, icon, label in (
        ("bullish", "\U0001f7e2", "Bullish"),
        ("bearish", "\U0001f534", "Bearish"),
    ):
        for ob in data.get(f"{key}OB", []):
            ts = ob.get("ts")
            if not ts:
                continue
            new_state[key].append(ts)
            if ts not in state[key] and not first_run:
                if not price_loaded:
                    price = get_price()
                    price_loaded = True
                when = datetime.fromtimestamp(ts / 1000, PH_TZ)
                price_txt = f"{price:,.1f}" if price else "n/a"
                title = f"{icon} New {label} OB Alert (BTC 1H)"
                body = (
                    f"Price: {price_txt}\n"
                    f"Time: {when.strftime('%Y-%m-%d %H:%M')} PST\n"
                    f"Sent: {datetime.now(PH_TZ).strftime('%Y-%m-%d %H:%M')} PST\n"
                    "Trade responsibly by Rouie"
                )
                print(title)
                print(body)
                send_push(title, body)

    save_state(new_state)


if __name__ == "__main__":
    main()
