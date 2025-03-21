from flask import Flask, request, jsonify
import time, hmac, hashlib, requests, json
import os
from waitress import serve  # 使用 WSGI 伺服器

app = Flask(__name__)

# 環境變數 (Bitunix API Key)
API_KEY = os.environ.get("API_KEY")
API_SECRET = os.environ.get("API_SECRET")
BASE_URL = "https://fapi.bitunix.com"

# 產生 Bitunix 簽名
def generate_signature(timestamp, method, endpoint, payload):
    message = f"{timestamp}{method}{endpoint}{payload}"
    return hmac.new(API_SECRET.encode(), message.encode(), hashlib.sha256).hexdigest()

# Bitunix 下單函數
def place_order(symbol, side, size):
    endpoint = "/api/v1/order/create"
    url = BASE_URL + endpoint
    method = "POST"
    timestamp = str(int(time.time() * 1000))
    order_data = {
        "symbol": symbol,
        "price": "0",
        "vol": size,
        "leverage": 10,
        "side": 1 if side == "buy" else 2,
        "type": 1,
        "open_type": 1,
        "position_id": 0,
        "external_oid": str(int(time.time())),
        "stop_loss_price": "",
        "take_profit_price": "",
        "position_mode": 1,
        "reduce_only": False
    }
    payload = json.dumps(order_data)
    signature = generate_signature(timestamp, method, endpoint, payload)
    headers = {
        "ApiKey": API_KEY,
        "Request-Time": timestamp,
        "Signature": signature,
        "Content-Type": "application/json"
    }
    response = requests.post(url, headers=headers, data=payload)
    print("Bitunix response:", response.json())  # log response for debugging
    return response.json()

# Webhook 入口
@app.route('/webhook', methods=['POST'])
def webhook():
    data = request.get_json()
    print("Received webhook:", data)  # log received data
    symbol = data.get("symbol")
    side = data.get("side")
    size = data.get("size")
    if not all([symbol, side, size]):
        return jsonify({"error": "Missing parameters"}), 400
    try:
        result = place_order(symbol, side, size)
        return jsonify({"message": "Order executed", "result": result})
    except Exception as e:
        return jsonify({"error": str(e)}), 500

# 新增一個首頁路由，Render 會自動檢查
@app.route("/")
def home():
    return "Bitunix Webhook is Running!", 200

# 使用 Waitress 讓 Flask 運行於 Render（WSGI 伺服器）
if __name__ == "__main__":
    serve(app, host="0.0.0.0", port=10000)
