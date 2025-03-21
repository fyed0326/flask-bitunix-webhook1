import time
import hmac
import hashlib
import requests
import json
import os
import sys
from flask import Flask, request, jsonify
from waitress import serve

API_KEY = os.environ.get("API_KEY")
SECRET_KEY = os.environ.get("API_SECRET")
BASE_URL = "https://fapi.bitunix.com"

api_path = "/api/v1/futures/trade/place_order"

def generate_signature(nonce, timestamp, api_key, query_params, body, secret_key):
    digest_input = nonce + timestamp + api_key + query_params + body
    digest = hashlib.sha256(digest_input.encode('utf-8')).hexdigest()
    sign_input = digest + secret_key
    sign = hashlib.sha256(sign_input.encode('utf-8')).hexdigest()
    return sign

def place_order(symbol, side, order_type, volume, price, trade_side):
    url = BASE_URL + api_path
    timestamp = str(int(time.time() * 1000))
    nonce = os.urandom(16).hex()

    params = {
        "symbol": symbol,
        "qty": float(volume),  # 確保 `qty` 是數字
        "side": side,
        "tradeSide": trade_side,  # ✅ 根據交易類型設定
        "orderType": order_type,
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

app = Flask(__name__)

@app.route('/webhook', methods=['POST'])
def webhook():
    data = request.get_json()
    print("=== Webhook Received ===", flush=True)
    print(json.dumps(data, indent=2), flush=True)
    sys.stdout.flush()

    if not data:
        return jsonify({"error": "No data received"}), 400

    symbol = data.get("symbol")
    side = "BUY" if data.get("side").lower() == "buy" else "SELL"
    size = float(data.get("size"))  # 確保 `size` 是數字
    price = "0"

    # **判斷開倉還是平倉**
    trade_side = "OPEN"  # ⚠️ 你可以根據交易邏輯改成 "CLOSE"

    try:
        result = place_order(symbol, side, "MARKET", size, price, trade_side)
        return jsonify({"message": "Order executed", "result": result})
    except Exception as e:
        print(f"Error: {str(e)}", flush=True)
        return jsonify({"error": str(e)}), 500

@app.route("/")
def home():
    return "Webhook Server Running!", 200

if __name__ == "__main__":
    serve(app, host="0.0.0.0", port=10000)
