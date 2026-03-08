import sqlite3
from datetime import datetime
from module.config import (
    DATABASE_NAME,
    WIN_RATE_CHECK_COUNT,
    WIN_RATE_LOW_THRESHOLD,
    WIN_RATE_LOW_RISK_MULTIPLIER,
    WIN_RATE_HIGH_THRESHOLD,
    WIN_RATE_HIGH_RISK_MULTIPLIER,
    WEEKLY_REPORT_DAY,
    WEEKLY_REPORT_HOUR
)
from module.telegram import send_telegram

last_report_week = None

def get_risk_multiplier():
    """ Đọc 20 lệnh gần nhất để quyết định hệ số rủi ro """
    try:
        conn = sqlite3.connect(DATABASE_NAME)
        cursor = conn.cursor()
        cursor.execute(f"SELECT result FROM trade_history ORDER BY id DESC LIMIT {WIN_RATE_CHECK_COUNT}")
        results = cursor.fetchall()
        conn.close()
        
        if not results: return 1.0
        wins = results.count(('WIN',))
        win_rate = wins / len(results)
        
        if win_rate < WIN_RATE_LOW_THRESHOLD: return WIN_RATE_LOW_RISK_MULTIPLIER  # Thua nhiều -> Cắt nửa rủi ro
        elif win_rate > WIN_RATE_HIGH_THRESHOLD: return WIN_RATE_HIGH_RISK_MULTIPLIER # Đang chuỗi thắng -> Tăng nhẹ rủi ro
        return 1.0
    except:
        return 1.0

def weekly_reflection(current_risk_pct):
    global last_report_week
    now = datetime.now()
    
    if now.weekday() == WEEKLY_REPORT_DAY and now.hour == WEEKLY_REPORT_HOUR: # 20h Chủ Nhật
        current_week = now.isocalendar()[1]
        if last_report_week == current_week: return current_risk_pct
            
        send_telegram("Báo cáo tuần đang được xử lý...")
        last_report_week = current_week
        # Logic tính toán có thể mở rộng thêm ở đây
        return current_risk_pct
        
    return current_risk_pct