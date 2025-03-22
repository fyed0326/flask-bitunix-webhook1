from flask import Flask, request, jsonify
from waitress import serve
import time, hmac, hashlib, requests, os, json

app = Flask(__name__)

# === API Key 環境變數（在 Render 設定） ===
API_KEY = os.environ.get("API_KEY")
API_SECRET = os.environ.get("API_SECRET")
BASE_URL = "https://fapi.bitunix.com"
ENDPOINT = "/api/v1/futures/trade/place_order"

# === 控制最大持倉 5 單 ===
MAX_ORDERS = 5
open_orders = []

def record_order(symbol, order_id):
    global open_orders
    open_orders = [o for o in open_orders if o["symbol"] == symbol]
    if len(open_orders) >= MAX_ORDERS:
        return False
    open_orders.append({"symbol": symbol, "order_id": order_id})
    return True

def generate_signature(nonce, timestamp, api_key, query, body, secret):
    data = nonce + timestamp + api_key + query + body
    digest = hashlib.sha256(data.encode()).hexdigest()
    sign = hashlib.sha256((digest + secret).encode()).hexdigest()
    return sign

def place_order(symbol, side, qty, price, tradeSide="OPEN"):
    url = BASE_URL + ENDPOINT
    timestamp = str(int(time.time() * 1000))
    nonce = os.urandom(16).hex()

    body_data = {
        "symbol": symbol,
        "qty": qty,
        "side": side.upper(),
        "orderType": "MARKET",
        "price": price,
        "tradeSide": tradeSide
    }

    body_str = json.dumps(body_data, separators=(',', ':'))
    signature = generate_signature(nonce, timestamp, API_KEY, "", body_str, API_SECRET)

    headers = {
        "api-key": API_KEY,
        "nonce": nonce,
        "timestamp": timestamp,
        "sign": signature,
        "Content-Type": "application/json"
    }

    response = requests.post(url, headers=headers, data=body_str)
    print(f"[Bitunix 回應] {response.status_code} - {response.text}", flush=True)
    return response.json()

@app.route("/")
def home():
    return "✅ Bitunix Webhook Bot Online!", 200

@app.route("/webhook", methods=["POST"])
def webhook():
    data = request.get_json()
    print("\n[Webhook 收到] ↓↓↓")
    print(json.dumps(data, indent=2), flush=True)

    symbol = data.get("symbol", "BTCUSDT")
    action = data.get("action", "").lower()
    reason = data.get("reason", "")
    price = str(data.get("price", "0"))
    size = float(data.get("size", 0.001))  # 修正：Bitunix 最小 0.001 BTC

    if action not in ["buy", "sell"]:
        return jsonify({"error": "Invalid action"}), 400

    side = "BUY" if action == "buy" else "SELL"
    trade_side = "CLOSE" if reason else "OPEN"

    if trade_side == "OPEN" and len([o for o in open_orders if o["symbol"] == symbol]) >= MAX_ORDERS:
        return jsonify({"message": "❌ 超過最大開單數量 5 單"}), 200

    result = place_order(symbol, side, size, price, trade_side)

    # 錯誤處理：Bitunix 錯誤碼非 0
    if result.get("code") != 0:
        print(f"⚠️ Bitunix 錯誤：{result.get('msg')}", flush=True)
        return jsonify({"message": "Bitunix 錯誤", "result": result}), 200

    data_obj = result.get("data") or {}  # 防止 .get 報錯
    order_id = data_obj.get("orderId")

    if trade_side == "OPEN" and order_id:
        record_order(symbol, order_id)

    return jsonify({"message": "✅ Webhook 處理完成", "result": result}), 200

if __name__ == "__main__":
    serve(app, host="0.0.0.0", port=10000)
