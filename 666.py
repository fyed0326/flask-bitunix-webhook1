# app.py - Flask Webhook 打水掛單機器人

from flask import Flask, request, jsonify
import time
import hmac
import hashlib
import requests
import os
import json

app = Flask(__name__)

API_KEY = os.getenv("BITUNIX_API_KEY", "你的 API KEY")
API_SECRET = os.getenv("BITUNIX_API_SECRET", "你的 API SECRET")
BASE_URL = "https://fapi.bitunix.com"
ORDER_ENDPOINT = "/api/v1/futures/trade/place_order"
MARKET_ENDPOINT = "/api/v1/futures/market/ticker/24h"

# 打水參數
TRADE_SYMBOL = "BTCUSDT"
ORDER_QTY = 0.001  # 每單下單量
DISTANCE_PERCENT = 0.2  # 掛單距離（上下 %）

@app.route("/maker", methods=["POST"])
def maker_order():
    try:
        price = get_market_price(TRADE_SYMBOL)
        if not price:
            return jsonify({"error": "無法獲取市價"}), 400

        buy_price = round(price * (1 - DISTANCE_PERCENT / 100), 2)
        sell_price = round(price * (1 + DISTANCE_PERCENT / 100), 2)

        # 建立 Buy/Sell 掛單
        buy_result = place_limit_order("BUY", buy_price)
        sell_result = place_limit_order("SELL", sell_price)

        return jsonify({
            "message": "已送出 Buy / Sell 掛單",
            "buy_result": buy_result,
            "sell_result": sell_result
        })
    except Exception as e:
        print("[錯誤]", e)
        return jsonify({"error": str(e)}), 500

# === 工具函式 ===
def get_market_price(symbol):
    url = f"{BASE_URL}{MARKET_ENDPOINT}?symbol={symbol}"
    res = requests.get(url)
    if res.status_code == 200:
        return float(res.json().get("data", {}).get("lastPrice", 0))
    return None

def place_limit_order(side, price):
    timestamp = str(int(time.time() * 1_000_000))
    nonce = hashlib.md5(timestamp.encode()).hexdigest()

    body = {
        "symbol": TRADE_SYMBOL,
        "qty": ORDER_QTY,
        "side": side,
        "tradeSide": "OPEN",
        "orderType": "LIMIT",
        "price": str(price)
    }

    message = f"{ORDER_ENDPOINT}\n{timestamp}\n{nonce}\n{json_encode(body)}"
    signature = hmac.new(API_SECRET.encode(), message.encode(), hashlib.sha256).hexdigest()

    headers = {
        "api-key": API_KEY,
        "timestamp": timestamp,
        "nonce": nonce,
        "sign": signature,
        "Content-Type": "application/json"
    }

    res = requests.post(BASE_URL + ORDER_ENDPOINT, headers=headers, data=json.dumps(body))
    try:
        return res.json()
    except:
        return {"error": "API 回傳格式錯誤"}

def json_encode(data):
    return json.dumps(data, separators=(",", ":"))

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=10000)
