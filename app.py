
from flask import Flask, request, jsonify
import time

app = Flask(__name__)

@app.route("/")
def index():
    return "Bitunix Maker Bot Online"

@app.route("/maker", methods=["POST"])
def maker():
    data = request.json
    print("🟢 收到 Webhook 訊號：", data)

    results = {
        "BTCUSDT": {"status": "success", "orderId": f"demo-{int(time.time())}"},
        "ETHUSDT": {"status": "success", "orderId": f"demo-{int(time.time())}"},
        "SOLUSDT": {"status": "success", "orderId": f"demo-{int(time.time())}"}
    }

    print("✅ 已模擬掛單結果：", results)

    return jsonify({"message": "已處理掛單", "results": results})

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=10000)
