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

# 正確的期貨下單 API 路徑
api_path = "/api/v1/futures/trade/place_order"

def generate_signature(nonce, timestamp, api_key, query_params, body, secret_key):
    # 第一步：計算 digest
    digest_input = nonce + timestamp + api_key + query_params + body
    digest = hashlib.sha256(digest_input.encode('utf-8')).hexdigest()

    # 第二步：計算簽名
    sign_input = digest + secret_key
    sign = hashlib.sha256(sign_input.encode('utf-8')).hexdigest()

    return sign

def place_order(symbol, side, order_type, volume, price):
    url = BASE_URL + api_path
    timestamp = str(int(time.time() * 1000))
    nonce = os.urandom(16).hex()

    params = {
        "symbol": symbol,
        "qty": volume,
        "side": side,
        "tradeSide": "OPEN",
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
    size = str(data.get("size"))
    price = "0"  # 市價單價格設為0

    try:
        result = place_order(symbol, side, "MARKET", size, price)
        return jsonify({"message": "Order executed", "result": result})
    except Exception as e:
        print(f"Error: {str(e)}", flush=True)
        return jsonify({"error": str(e)}), 500

@app.route("/")
def home():
    return "Webhook Server Running!", 200

if __name__ == "__main__":
    serve(app, host="0.0.0.0", port=10000)