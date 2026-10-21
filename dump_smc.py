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

for k, n in (("bearishOB", 14), ("bullishOB", 14),
             ("breakerBearish", 8), ("breakerBullish", 8)):
    print(k)
    for o in d[k][-n:]:
        print(t(o["ts"]), "h", o["h"], "l", o["l"])
