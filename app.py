# app.py - 市價查詢改回無簽名方式，其餘保留簽名驗證

from flask import Flask, request, jsonify
import time
import hmac
import hashlib
import requests
import os
import json

app = Flask(__name__)

API_KEY = os.getenv("BITUNIX_API_KEY", "your_api_key_here")
API_SECRET = os.getenv("BITUNIX_API_SECRET", "your_api_secret_here")
BASE_URL = "https://fapi.bitunix.com"
ORDER_ENDPOINT = "/api/v1/futures/trade/place_order"
CANCEL_ENDPOINT = "/api/v1/futures/trade/cancel_order"
OPEN_ORDERS_ENDPOINT = "/api/v1/futures/trade/open_orders"
MARKET_ENDPOINT = "/api/v1/futures/market/ticker/24h"

SYMBOLS = ["BTCUSDT", "ETHUSDT", "SOLUSDT"]
ORDER_QTY = 0.001
DISTANCE_PERCENT = 0.2
CANCEL_THRESHOLD = 0.5

@app.route("/maker", methods=["POST"])
def maker_order():
    results = {}
    for symbol in SYMBOLS:
        price = get_market_price(symbol)
        if not price:
            results[symbol] = {"error": "無法獲取市價"}
            continue

        buy_price = round(price * (1 - DISTANCE_PERCENT / 100), 4)
        sell_price = round(price * (1 + DISTANCE_PERCENT / 100), 4)

        cancel_old_orders(symbol, price)

        buy_result = place_limit_order(symbol, "BUY", buy_price)
        sell_result = place_limit_order(symbol, "SELL", sell_price)

        results[symbol] = {
            "buy_result": buy_result,
            "sell_result": sell_result
        }

    return jsonify({"message": "已處理掛單", "results": results})

def cancel_old_orders(symbol, market_price):
    timestamp, nonce = gen_time_nonce()
    params = {"symbol": symbol}
    query = json_encode(params)
    message = f"{OPEN_ORDERS_ENDPOINT}\n{timestamp}\n{nonce}\n{query}"
    signature = hmac.new(API_SECRET.encode(), message.encode(), hashlib.sha256).hexdigest()
    headers = {
        "api-key": API_KEY,
        "timestamp": timestamp,
        "nonce": nonce,
        "sign": signature,
        "Content-Type": "application/json"
    }
    res = requests.get(BASE_URL + OPEN_ORDERS_ENDPOINT, headers=headers, params=params)
    if res.status_code != 200:
        return
    orders = res.json().get("data", [])
    for order in orders:
        order_price = float(order.get("price", 0))
        if abs(order_price - market_price) / market_price * 100 > CANCEL_THRESHOLD:
            cancel_order(symbol, order.get("orderId"))

def cancel_order(symbol, order_id):
    timestamp, nonce = gen_time_nonce()
    data = {"symbol": symbol, "orderId": order_id}
    body = json_encode(data)
    message = f"{CANCEL_ENDPOINT}\n{timestamp}\n{nonce}\n{body}"
    signature = hmac.new(API_SECRET.encode(), message.encode(), hashlib.sha256).hexdigest()
    headers = {
        "api-key": API_KEY,
        "timestamp": timestamp,
        "nonce": nonce,
        "sign": signature,
        "Content-Type": "application/json"
    }
    res = requests.post(BASE_URL + CANCEL_ENDPOINT, headers=headers, data=body)
    print(f"⛔ 撤單 {symbol} {order_id} 回應:", res.json())

def get_market_price(symbol):
    try:
        url = f"{BASE_URL}{MARKET_ENDPOINT}?symbol={symbol}"
        res = requests.get(url)
        return float(res.json().get("data", {}).get("lastPrice", 0))
    except:
        return None

def place_limit_order(symbol, side, price):
    timestamp, nonce = gen_time_nonce()
    body = {
        "symbol": symbol,
        "qty": ORDER_QTY,
        "side": side,
        "tradeSide": "OPEN",
        "orderType": "LIMIT",
        "price": str(price)
    }
    body_encoded = json_encode(body)
    message = f"{ORDER_ENDPOINT}\n{timestamp}\n{nonce}\n{body_encoded}"
    signature = hmac.new(API_SECRET.encode(), message.encode(), hashlib.sha256).hexdigest()
    headers = {
        "api-key": API_KEY,
        "timestamp": timestamp,
        "nonce": nonce,
        "sign": signature,
        "Content-Type": "application/json"
    }
    res = requests.post(BASE_URL + ORDER_ENDPOINT, headers=headers, data=body_encoded)
    try:
        return res.json()
    except:
        return {"error": "API 回傳格式錯誤"}

def json_encode(data):
    return json.dumps(data, separators=(",", ":"))

def gen_time_nonce():
    timestamp = str(int(time.time() * 1_000_000))
    nonce = hashlib.md5(timestamp.encode()).hexdigest()
    return timestamp, nonce

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=10000)