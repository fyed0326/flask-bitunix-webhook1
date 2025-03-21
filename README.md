
# Bitunix Webhook Flask Bot

## 功能：
接收 TradingView 的 webhook 訊號，自動透過 Bitunix API 下單（市價單）。

## Webhook 格式：
```
{
  "symbol": "BTCUSDT",
  "side": "buy",
  "size": 0.01
}
```

## 部署方式（Render）：
1. 登入 [https://render.com](https://render.com)
2. 建立 Web Service
3. 指定 Build Command: `pip install -r requirements.txt`
4. 指定 Start Command: `python app.py`
5. 新增環境變數：
   - `API_KEY` = 你的 Bitunix API Key
   - `API_SECRET` = 你的 Bitunix API Secret
6. 獲得網址後將 `/webhook` 貼到 TradingView

## 測試：
可用 Postman 或 curl 發送 POST 測試
