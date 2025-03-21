import time
import hmac
import hashlib
import requests
import json
import os
from flask import Flask, request, jsonify
from waitress import serve  # 使用 WSGI 伺服器

# 環境變數 (Bitunix API Key)
API_KEY = os.environ.get("API_KEY")
SECRET_KEY = os.environ.get("API_SECRET")
BASE_URL = "https://api.bitunix.com"

# 生成簽名
def generate_signature(api_path, params, secret_key):
    sorted_params = '&'.join(f"{key}={params[key]}" for key in sorted(params))
    str_to_sign = f"{api_path}&{sorted_params}"
    signature = hmac.new(secret_key.encode(), str_to_sign.encode(), hashlib.sha256).hexdigest()
    return signature

# Bitunix 下單函數
def place_order(symbol, side, order_type, volume, price):
    api_path = '/api/spot/v1/order/place_order'  # 確保這個路徑正確
    url = BASE_URL + api_path
    timestamp = str(int(time.time() * 1000))

    params = {
        "symbol": symbol,
        "side": side,  # 1: 賣出, 2: 買入
        "type": order_type,  # 1: 限價單, 2: 市價單
        "volume": volume,  # 交易量
        "price": price,  # 價格 (市價單可設為 0)
        "timestamp": timestamp
    }

    signature = generate_signature(api_path, params, SECRET_KEY)
    headers = {
        "X-Bit-Access-Key": API_KEY,
        "Content-Type": "application/json"
    }
    params["signature"] = signature
    response = requests.post(url, headers=headers, json=params)

    # 記錄 API 回應
    print(f"Request URL: {url}")
    print(f"Request Headers: {headers}")
    print(f"Request Body: {params}")
    print(f"Bitunix API Response: {response.status_code} - {response.text}")

    return response.json()

# Webhook 入口
app = Flask(__name__)

@app.route('/webhook', methods=['POST'])
def webhook():
    data = request.get_json()
    print("Received webhook:", data)  # log received data
    symbol = data.get("symbol")
    side = 2 if data.get("side") == "buy" else 1
    size = str(data.get("size"))
    price = "0"  # 預設為市價單
    if not all([symbol, side, size]):
        return jsonify({"error": "Missing parameters"}), 400
    try:
        result = place_order(symbol, side, 2, size, price)  # 使用市價單 (type=2)
        return jsonify({"message": "Order executed", "result": result})
    except Exception as e:
        return jsonify({"error": str(e)}), 500

# 新增首頁路由，Render 會自動檢查
@app.route("/")
def home():
    return "Bitunix Webhook is Running!", 200

# 使用 Waitress 讓 Flask 運行於 Render（WSGI 伺服器）
if __name__ == "__main__":
    serve(app, host="0.0.0.0", port=10000)