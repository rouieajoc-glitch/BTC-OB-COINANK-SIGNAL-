import os, json, requests
r = requests.get(
    "https://open-api.coinank.com/api/indicator/smc",
    headers={"apikey": os.environ["COINANK_API_KEY"]},
    params={"symbol": "BTCUSDT", "interval": "4h", "exchange": "Binance"},
    timeout=10,
).json()
d = r["data"]
print("KEYS:", list(d.keys()))
for k, v in d.items():
    if isinstance(v, list):
        print(k, len(v), json.dumps(v[-4:], indent=1))
    else:
        print(k, json.dumps(v)[:300])
