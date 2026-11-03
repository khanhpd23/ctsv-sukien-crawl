import os
import requests
from bs4 import BeautifulSoup
from flask import Flask, jsonify

app = Flask(__name__)

# Lưu trữ nội dung của lần quét gần nhất trong bộ nhớ
last_content = None

# Lấy thông tin cấu hình từ biến môi trường
TARGET_URL = os.environ.get("TARGET_URL", "")
CSS_SELECTOR = os.environ.get("CSS_SELECTOR", "body")
TELEGRAM_TOKEN = os.environ.get("TELEGRAM_TOKEN", "")
CHAT_ID = os.environ.get("CHAT_ID", "")

def send_telegram(message):
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
    payload = {
        "chat_id": CHAT_ID,
        "text": message
    }
    requests.post(url, json=payload, timeout=10)

@app.route("/")
def index():
    return "Hoạt động!"

@app.route("/check")
def check_website():
    global last_content

    try:
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36"
        }
        response = requests.get(TARGET_URL, headers=headers, timeout=15)
        response.raise_for_status()

        soup = BeautifulSoup(response.text, "html.parser")
        target_element = soup.select_one(CSS_SELECTOR)

        if not target_element:
            return jsonify({
                "status": "error",
                "message": "Không tìm thấy vùng dữ liệu theo CSS_SELECTOR"
            }), 400

        # Trích xuất văn bản
        current_content = " ".join(target_element.get_text().split())

        # Lần chạy đầu tiên: lưu mốc dữ liệu ban đầu
        if last_content is None:
            last_content = current_content
            send_telegram(f"Đã bắt đầu theo dõi web\n\nMốc dữ liệu hiện tại:\n{current_content[:300]}")
            return jsonify({"status": "initialized", "message": "Đã lưu mốc dữ liệu ban đầu"})

        # Phát hiện thay đổi so với lần kiểm tra trước
        if current_content != last_content:
            send_telegram(
                f"Phát hiện thay đổi trên trang web!\n\n"
                f"Trước đó:\n{last_content[:250]}\n\n"
                f"Hiện tại:\n{current_content[:250]}\n\n"
                f"🔗 Xem tại: {TARGET_URL}"
            )
            last_content = current_content
            return jsonify({"status": "changed", "message": "Có thay đổi"})

        return jsonify({"status": "unchanged", "message": "Không có thay đổi"})

    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 10000))
    app.run(host="0.0.0.0", port=port)
