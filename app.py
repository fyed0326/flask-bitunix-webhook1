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
BASE_URL = "https://api.bitunix.com"

# ⚠️ 期貨交易的 API 路徑
api_path = "/api/futures/v1/order/place_order"

def generate_signature(api_path, params, secret_key):
    sorted_params = '&'.join(f"{key}={params[key]}" for key in sorted(params))
    str_to_sign = f"{api_path}&{sorted_params}"
    signature = hmac.new(secret_key.encode(), str_to_sign.encode(), hashlib.sha256).hexdigest()
    return signature

def place_order(symbol, side, order_type, volume, price):
    url = BASE_URL + api_path
    timestamp = str(int(time.time() * 1000))

    params = {
        "symbol": symbol,
        "side": side,
        "type": order_type,
        "volume": volume,
        "price": price,
        "timestamp": timestamp
    }

    signature = generate_signature(api_path, params, SECRET_KEY)
    headers = {
        "X-Bit-Access-Key": API_KEY,
        "Content-Type": "application/json"
    }
    params["signature"] = signature
    response = requests.post(url, headers=headers, json=params)

    print(f"Request URL: {url}", flush=True)
    print(f"Request Headers: {headers}", flush=True)
    print(f"Request Body: {params}", flush=True)
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
    side = 2 if data.get("side") == "buy" else 1
    size = str(data.get("size"))
    price = "0"  

    try:
        result = place_order(symbol, side, 2, size, price)
        return jsonify({"message": "Order executed", "result": result})
    except Exception as e:
        print(f"Error: {str(e)}", flush=True)
        return jsonify({"error": str(e)}), 500

@app.route("/")
def home():
    return "Webhook Server Running!", 200

if __name__ == "__main__":
    serve(app, host="0.0.0.0", port=10000)
