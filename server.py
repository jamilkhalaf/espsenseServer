
from flask import Flask, request
import requests
import os
import time

app = Flask(__name__)
BOT_TOKEN = "8177057089:AAHdxKnxs3uwVehwacE-tyDYV9TMs01qq74"
CHAT_ID = "7167447500"
TELEGRAM_API = f"https://api.telegram.org/bot{BOT_TOKEN}"
UPLOAD_FOLDER = "uploads"
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

# Track triggers
last_message_id = None
manual_triggered = False


@app.route("/trigger", methods=["POST"])
def manual_trigger():
    global manual_triggered
    manual_triggered = True
    print("✅ Manual trigger set.")
    return "OK", 200


@app.route("/ready")
def check_for_trigger():
    global last_message_id, manual_triggered

    # ✅ Prioritize manual trigger
    if manual_triggered:
        manual_triggered = False
        print("📸 Manual trigger activated via /ready")
        return "OK", 200

    try:
        updates = requests.get(f"{TELEGRAM_API}/getUpdates").json()
        messages = updates.get("result", [])
        if not messages:
            return "No messages", 204

        latest = messages[-1]
        msg_id = latest["message"]["message_id"]

        print(f"Latest msg_id: {msg_id} | Last seen: {last_message_id}")

        if msg_id != last_message_id and "text" in latest["message"]:
            last_message_id = msg_id
            print("📩 New Telegram message received, telling ESP32 to capture")
            return "OK", 200

        return "No new trigger", 204

    except Exception as e:
        print("⚠️ Error polling Telegram:", e)
        return "Error", 500


@app.route("/upload", methods=["POST"])
def handle_upload():
    if 'file' not in request.files:
        return "No file", 400

    os.makedirs(UPLOAD_FOLDER, exist_ok=True)
    path = os.path.join(UPLOAD_FOLDER, "doorbell.jpg")
    request.files['file'].save(path)

    # Send to Telegram
    with open(path, 'rb') as photo:
        res = requests.post(
            f"{TELEGRAM_API}/sendPhoto",
            data={"chat_id": CHAT_ID},
            files={"photo": photo}
        )

    if res.ok:
        print("📸 Image sent to Telegram")
        return "OK", 200
    else:
        print("❌ Telegram error:", res.text)
        return "Fail", 500


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5050)
