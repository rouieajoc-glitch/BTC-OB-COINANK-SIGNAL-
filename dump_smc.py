import os, requests
from datetime import datetime, timezone

d = requests.get(
    "https://open-api.coinank.com/api/indicator/smc",
    headers={"apikey": os.environ["COINANK_API_KEY"]},
    params={"symbol": "BTCUSDT", "interval": "4h", "exchange": "Binance"},
    timeout=10,
).json()["data"]

def t(ms):
    return datetime.fromtimestamp(ms / 1000, timezone.utc).strftime("%m-%d %H:%M")

for k in ("swingHighs", "swingLows"):
    print(k)
    for s in d[k][-25:]:
        print(t(s["ts"]), s["price"])
