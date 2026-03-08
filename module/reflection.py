import sqlite3
from datetime import datetime
from module.telegram import send_telegram

last_report_week = None

def get_risk_multiplier():
    """ Đọc 20 lệnh gần nhất để quyết định hệ số rủi ro """
    try:
        conn = sqlite3.connect('trading_bot.db')
        cursor = conn.cursor()
        cursor.execute("SELECT result FROM trade_history ORDER BY id DESC LIMIT 20")
        results = cursor.fetchall()
        conn.close()
        
        if not results: return 1.0
        wins = results.count(('WIN',))
        win_rate = wins / len(results)
        
        if win_rate < 0.4: return 0.5  # Thua nhiều -> Cắt nửa rủi ro
        elif win_rate > 0.7: return 1.2 # Đang chuỗi thắng -> Tăng nhẹ rủi ro
        return 1.0
    except:
        return 1.0

def weekly_reflection(current_risk_pct):
    global last_report_week
    now = datetime.now()
    
    if now.weekday() == 6 and now.hour == 20: # 20h Chủ Nhật
        current_week = now.isocalendar()[1]
        if last_report_week == current_week: return current_risk_pct
            
        send_telegram("Báo cáo tuần đang được xử lý...")
        last_report_week = current_week
        # Logic tính toán có thể mở rộng thêm ở đây
        return current_risk_pct
        
    return current_risk_pct