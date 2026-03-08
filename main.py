print("Chương trình đã bắt đầu khởi chạy...")
from datetime import datetime
import time
from module.config import SYMBOLS, BASE_RISK, MAIN_LOOP_SLEEP
from module.database import init_db
from module.strategy import check_closed_trades, manage_trade
from module.reflection import get_risk_multiplier, weekly_reflection
from module.telegram import send_telegram 

print("Đang khởi tạo Database...")
init_db()
print("✅ Database đã sẵn sàng!")

print("Đang gửi thông báo khởi động tới Telegram...")
send_telegram("⚡ *BINANCE BOT ONLINE*")
print("✅ Đã xử lý xong phần Telegram!")

while True:
    # Lấy thời gian hiện tại theo định dạng Giờ:Phút:Giây
    current_time = datetime.now().strftime("%H:%M:%S")
    
    print(f"\n--- [{current_time}] Đang quét thị trường ---")
    risk_mult = get_risk_multiplier()
    current_risk = BASE_RISK * risk_mult
    
    # Cập nhật rủi ro hàng tuần
    BASE_RISK = weekly_reflection(BASE_RISK)

    for symbol in SYMBOLS:
        try:
            manage_trade(symbol, current_risk)
            time.sleep(1) # Binance cho phép rate limit cao hơn
        except Exception as e:
            print(f"Lỗi: {e}")

    # 2. KIỂM TRA LỆNH ĐÃ ĐÓNG ĐỂ CẬP NHẬT DASHBOARD
    print(f"--- Đang kiểm tra trạng thái các lệnh cũ ---")
    check_closed_trades()

    time.sleep(MAIN_LOOP_SLEEP)