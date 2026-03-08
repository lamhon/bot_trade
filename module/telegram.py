import requests
from module.config import TELEGRAM_TOKEN, TELEGRAM_CHAT_ID

def send_telegram(message):
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
    payload = {"chat_id": TELEGRAM_CHAT_ID, "text": message, "parse_mode": "Markdown"}
    try:
        requests.post(url, json=payload, timeout=10)
    except Exception as e:
        print(f"⚠️ Không gửi được Telegram (có thể do mạng): {e}")