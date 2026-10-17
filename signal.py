import json
import os
import sys
import requests
from datetime import datetime, timezone

API_KEY = os.environ["COINANK_API_KEY"]
SYMBOL = "BTCUSDT"
INTERVAL = "4h"
STATE_FILE = "seen.json"

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


def send_push(title, body):
    payload = {"title": title, "body": body, "sound": "1"}
    try:
        res = requests.post(PUSH_URL, headers=HEADERS, json=payload, timeout=10)
        print("Push sent:", res.status_code)
    except Exception as e:
        print("Push failed:", e)


def strength(ob):
    high, low = ob.get("h", 0), ob.get("l", 0)
    if high == low:
        return 0
    body = abs(ob.get("c", 0) - ob.get("o", 0))
    return round(body / (high - low) * 100, 1)


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

    for key, icon, label in (
        ("bullish", "🟢", "Bullish"),
        ("bearish", "🔴", "Bearish"),
    ):
        for ob in data.get(f"{key}OB", []):
            ts = ob.get("ts")
            if not ts:
                continue
            new_state[key].append(ts)
            if ts not in state[key] and not first_run:
                when = datetime.fromtimestamp(ts / 1000, timezone.utc)
                title = f"{icon} New {label} Order Block (BTC 4H)"
                body = (
                    f"High: {ob.get('h')}\n"
                    f"Low: {ob.get('l')}\n"
                    f"Strength: {strength(ob)}%\n"
                    f"Time: {when.strftime('%Y-%m-%d %H:%M')} UTC"
                )
                print(title)
                print(body)
                send_push(title, body)

    save_state(new_state)


if __name__ == "__main__":
    main()
