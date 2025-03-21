from flask import Flask, request, jsonify
from waitress import serve

app = Flask(__name__)

@app.route('/webhook', methods=['POST'])
def webhook():
    data = request.get_json()
    print("=== Webhook Received ===")  # 這行會印到 Render Logs
    print(data)  # 這行會印到 Render Logs
    return jsonify({"message": "Webhook received", "data": data}), 200

@app.route("/")
def home():
    return "Webhook Server Running!", 200

if __name__ == "__main__":
    serve(app, host="0.0.0.0", port=10000)
