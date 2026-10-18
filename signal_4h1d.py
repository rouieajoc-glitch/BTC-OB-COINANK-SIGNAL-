import json
import os
import time
import requests
from datetime import datetime, timezone, timedelta

API_KEY = os.environ["COINANK_API_KEY"]
SYMBOL = "BTCUSDT"

# timeframe -> only alert on blocks formed within this many hours
INTERVALS = {"4h": 1000, "1d": 1000}

STATE_FILE = "seen.json"
PH_TZ = timezone(timedelta(hours=8))
MAX_KEEP = 500       # how many past block times to remember per side
PAUSE_SECONDS = 2    # small pause between requests

HEADERS = {"apikey": API_KEY}
SMC_URL = "https://open-api.coinank.com/api/indicator/smc"
PUSH_URL = "https://open-api.coinank.com/api/webhook/push"


def fmt(p):
    return f"{p:,.1f}"


def get_smc_data(interval):
    params = {"symbol": SYMBOL, "interval": interval, "exchange": "Binance"}
    try:
        r = requests.get(SMC_URL, headers=HEADERS, params=params, timeout=10)
        data = r.json()
        if data.get("success"):
            return data["data"]
        print(interval, "API Error:", data)
    except Exception as e:
        print(interval, "Request failed:", e)
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


def zone_text(ob, price):
    """Return (zone line, distance line) for an order block."""
    h, l = ob.get("h"), ob.get("l")
    if h is None or l is None:
        return None, None
    zone = f"Zone: {fmt(l)} - {fmt(h)}"
    if not price:
        return zone, None
    if l <= price <= h:
        dist = "Distance: price is inside the zone"
    elif price > h:
        pct = (price - h) / price * 100
        dist = f"Distance: {pct:.2f}% below price"
    else:
        pct = (l - price) / price * 100
        dist = f"Distance: {pct:.2f}% above price"
    return zone, dist


def load_state():
    if os.path.exists(STATE_FILE):
        try:
            with open(STATE_FILE) as f:
                state = json.load(f)
        except Exception as e:
            print("State read failed:", e)
            return {}
        # migrate the old BTC-only format ({"bullish": [...], "bearish": [...]})
        # so the existing 4h history carries over and nothing re-alerts
        if "bullish" in state or "bearish" in state:
            state = {
                SYMBOL: {
                    "bullish": state.get("bullish", []),
                    "bearish": state.get("bearish", []),
                }
            }
        return state
    return {}


def save_state(state):
    with open(STATE_FILE, "w") as f:
        json.dump(state, f)


def process_interval(interval, max_age_hours, state):
    data = get_smc_data(interval)
    if not data:
        return  # keep old state for this timeframe untouched

    tf = interval.upper()
    # 4h keeps the original key so existing history carries over
    state_key = SYMBOL if interval == "4h" else f"{SYMBOL}_{interval}"
    # nothing saved yet = first run: record quietly, no alerts
    first_run = state_key not in state
    old = state.get(state_key, {"bullish": [], "bearish": []})

    now_ms = datetime.now(timezone.utc).timestamp() * 1000
    max_age_ms = max_age_hours * 3600 * 1000

    new_state = {"bullish": [], "bearish": []}
    price = None
    price_loaded = False

    for key, icon, label in (
        ("bullish", "\U0001f7e2", "Bullish"),
        ("bearish", "\U0001f534", "Bearish"),
    ):
        seen = list(old.get(key, []))
        for ob in data.get(f"{key}OB", []):
            ts = ob.get("ts")
            if not ts or ts in seen:
                continue
            seen.append(ts)
            if first_run:
                continue
            if now_ms - ts > max_age_ms:
                print("Skipped old block:", interval, key, ts)
                continue
            if not price_loaded:
                price = get_price()
                price_loaded = True
            when = datetime.fromtimestamp(ts / 1000, PH_TZ)
            price_txt = fmt(price) if price else "n/a"
            title = f"{icon} New {label} OB Alert (BTC {tf})"
            zone, dist = zone_text(ob, price)
            extra = "".join(f"{x}\n" for x in (zone, dist) if x)
            body = (
                f"Price: {price_txt}\n"
                f"{extra}"
                f"Time: {when.strftime('%Y-%m-%d %I:%M %p')} PHT\n"
                f"Sent: {datetime.now(PH_TZ).strftime('%Y-%m-%d %I:%M %p')} PHT\n"
                "Trade responsibly by Rouie"
            )
            print(title)
            print(body)
            send_push(title, body)
        new_state[key] = seen[-MAX_KEEP:]

    state[state_key] = new_state


def main():
    state = load_state()
    first = True
    for interval, max_age in INTERVALS.items():
        if not first:
            time.sleep(PAUSE_SECONDS)
        first = False
        try:
            process_interval(interval, max_age, state)
        except Exception as e:
            print(interval, "failed:", e)
    save_state(state)


if __name__ == "__main__":
    main()
