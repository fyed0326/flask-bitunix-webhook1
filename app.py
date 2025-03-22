import time
import hmac
import hashlib
import requests
import json
import os
import sys
from flask import Flask, request, jsonify
from waitress import serve

# Bitunix API 設定
API_KEY = os.environ.get("API_KEY")
SECRET_KEY = os.environ.get("API_SECRET")
BASE_URL = "https://fapi.bitunix.com"
api_path = "/api/v1/futures/trade/place_order"

# 最多允許的未平倉訂單數量
MAX_OPEN_ORDERS = 5
open_orders = []  # 儲存當前未平倉訂單 ID

# 生成 Bitunix API 簽名
def generate_signature(nonce, timestamp, api_key, query_params, body, secret_key):
    digest_input = nonce + timestamp + api_key + query_params + body
    digest = hashlib.sha256(digest_input.encode('utf-8')).hexdigest()
    sign_input = digest + secret_key
    sign = hashlib.sha256(sign_input.encode('utf-8')).hexdigest()
    return sign

# 下單函數
def place_order(symbol, side, volume, price, trade_side):
    url = BASE_URL + api_path
    timestamp = str(int(time.time() * 1000))
    nonce = os.urandom(16).hex()

    params = {
        "symbol": symbol,
        "qty": float(volume),
        "side": side,
        "tradeSide": trade_side,
        "orderType": "MARKET",
        "price": price
    }

    query_params = ""
    body = json.dumps(params, separators=(',', ':'))

    signature = generate_signature(nonce, timestamp, API_KEY, query_params, body, SECRET_KEY)
    headers = {
        "api-key": API_KEY,
        "nonce": nonce,
        "timestamp": timestamp,
        "sign": signature,
        "Content-Type": "application/json"
    }

    response = requests.post(url, headers=headers, data=body)
    print(f"Request URL: {url}", flush=True)
    print(f"Request Headers: {headers}", flush=True)
    print(f"Request Body: {body}", flush=True)
    print(f"Bitunix API Response: {response.status_code} - {response.text}", flush=True)

    return response.json()

# 紀錄訂單 ID 並限制最多單數
def record_order(order_id):
    if len(open_orders) >= MAX_OPEN_ORDERS:
        return False
    open_orders.append(order_id)
    return True

# Flask App 啟動
app = Flask(__name__)

@app.route('/webhook', methods=['POST'])
def webhook():
    data = request.get_json()
    print("=== Webhook Received ===", flush=True)
    print(json.dumps(data, indent=2), flush=True)
    sys.stdout.flush()

    symbol = data.get("symbol", "BTCUSDT")
    action = data.get("action", "").lower()
    size = float(data.get("size", 0.0001))
    price = str(data.get("price", "0"))

    if action == "buy":
        side = "BUY"
        trade_side = "OPEN"
    elif action == "sell":
        side = "SELL"
        trade_side = "OPEN"
    else:
        return jsonify({"error": "Invalid action"}), 400

    # 限制最多同時持有的單數
    if len(open_orders) >= MAX_OPEN_ORDERS:
        print("❌ 超過最多持有 5 單限制，不下單", flush=True)
        return jsonify({"message": "Order limit reached. No order sent."}), 200

    try:
        result = place_order(symbol, side, size, price, trade_side)
        order_id = result.get("data", {}).get("orderId")
        if order_id and record_order(order_id):
            return jsonify({"message": "Order executed", "result": result})
        else:
            return jsonify({"message": "Order not recorded or limit reached", "result": result})
    except Exception as e:
        print(f"Error: {str(e)}", flush=True)
        return jsonify({"error": str(e)}), 500

@app.route("/")
def home():
    return "Webhook Server Running!", 200

if __name__ == "__main__":
    serve(app, host="0.0.0.0", port=10000)