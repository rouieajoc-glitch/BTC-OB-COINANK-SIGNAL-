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
