# import sqlite3

# import pandas_ta as ta
# import pandas as pd
# from module.config import exchange, HTF, LTF, MAX_OPEN_POSITIONS
# from module.data_fetcher import fetch_market_data, get_smart_money_data
# from module.execution import format_price, calculate_binance_qty, execute_trade_with_tpsl
# from module.database import log_trade, update_trade_result

# def manage_trade(symbol, current_risk_pct):
#     # Kiểm tra vị thế hiện tại
#     positions = exchange.fetch_positions([symbol])
#     if any(float(p['contracts']) != 0 for p in positions if p['symbol'] == symbol):
#         print(f"   [-] {symbol}: Đã có vị thế đang mở. Bỏ qua.")
#         return

#     active_pos_count = len([p for p in exchange.fetch_positions() if float(p['contracts']) != 0])
#     if active_pos_count >= MAX_OPEN_POSITIONS:
#         print(f"   [-] {symbol}: Đã đạt giới hạn số lượng lệnh tối đa ({MAX_OPEN_POSITIONS}).")
#         return
    
#     # Lấy dữ liệu
#     df_htf = fetch_market_data(symbol, HTF)
#     df_htf['ema200'] = ta.ema(df_htf['close'], length=200)
#     htf_trend = "LONG" if df_htf.iloc[-1]['close'] > df_htf.iloc[-1]['ema200'] else "SHORT"

#     df_ltf = fetch_market_data(symbol, LTF)
#     df_ltf['adx'] = ta.adx(df_ltf['high'], df_ltf['low'], df_ltf['close'])['ADX_14']
#     df_ltf['atr'] = ta.atr(df_ltf['high'], df_ltf['low'], df_ltf['close'])
    
#     bb = ta.bbands(df_ltf['close'], length=20, std=2)
#     # SỬA LỖI Ở ĐÂY: Dùng iloc để tránh lỗi đặt tên cột
#     df_ltf['bb_lower'] = bb.iloc[:, 0]
#     df_ltf['bb_middle'] = bb.iloc[:, 1]
#     df_ltf['bb_upper'] = bb.iloc[:, 2]

#     last = df_ltf.iloc[-1]
#     smart = get_smart_money_data(symbol)
#     balance = exchange.fetch_balance()['total']['USDT']

#     # Xác định chế độ dựa trên ADX
#     adx_value = last['adx']
#     is_trend_mode = adx_value >= 25
#     mode_label = "📈 TREND" if is_trend_mode else "↔️ GRID"
    
#     strategy, side, sl_raw, tp_raw = None, None, 0, 0
#     reasons = [] # Danh sách lưu các lý do không khớp

#     # --- PHÂN TÍCH THEO CHẾ ĐỘ ---

#     if is_trend_mode:
#         # LOGIC ĐÁNH THEO TREND
#         if df_htf.iloc[-1]['close'] > df_htf.iloc[-1]['ema200']: # HTF LONG
#             if last['close'] > last['bb_upper']:
#                 if smart['oi_trend'] == "UP":
#                     strategy, side = "TREND_FOLLOW_LONG", "LONG"
#                     sl_raw = last['close'] - (2 * last['atr'])
#                     tp_raw = last['close'] + (3 * last['atr'])
#                 else:
#                     reasons.append(f"Chờ Cá voi (OI hiện tại: {smart['oi_trend']})")
#             else:
#                 reasons.append(f"Chờ phá vỡ dải trên BB ({last['close']} < {last['bb_upper']:.2f})")
#         else: # HTF SHORT
#             if last['close'] < last['bb_lower']:
#                 if smart['oi_trend'] == "UP":
#                     strategy, side = "TREND_FOLLOW_SHORT", "SHORT"
#                     sl_raw = last['close'] + (2 * last['atr'])
#                     tp_raw = last['close'] - (3 * last['atr'])
#                 else:
#                     reasons.append(f"Chờ Cá voi (OI hiện tại: {smart['oi_trend']})")
#             else:
#                 reasons.append(f"Chờ phá vỡ dải dưới BB ({last['close']} > {last['bb_lower']:.2f})")

#     else:
#         # LOGIC ĐÁNH GRID (Sideway)
#         if last['close'] <= last['bb_lower']:
#             strategy, side = "GRID_REVERSAL_LONG", "LONG"
#             sl_raw = last['bb_lower'] - last['atr']
#             tp_raw = last['bb_middle']
#         elif last['close'] >= last['bb_upper']:
#             strategy, side = "GRID_REVERSAL_SHORT", "SHORT"
#             sl_raw = last['bb_upper'] + last['atr']
#             tp_raw = last['bb_middle']
#         else:
#             reasons.append("Giá đang dao động trong vùng an toàn (Chưa chạm biên BB)")

#     # --- HIỂN THỊ LOG & VÀO LỆNH ---
#     if strategy:
#         sl = format_price(symbol, sl_raw)
#         tp = format_price(symbol, tp_raw)
#         qty = calculate_binance_qty(symbol, balance * current_risk_pct, abs(last['close'] - sl))
        
#         if qty > 0:
#             # Thông báo Telegram cũng sẽ ghi rõ chiến lược
#             msg = f"🔔 *KÍCH HOẠT CHIẾN LƯỢC {mode_label}*\nCặp: {symbol}\nLệnh: {side}\nGiá: {last['close']}\nSL: {sl} | TP: {tp}"
#             if execute_trade_with_tpsl(symbol, side, qty, sl, tp, msg):
#                 log_trade(symbol, strategy, side, last['close'], adx_value)
#     else:
#         # In log trạng thái quét thị trường kèm chế độ
#         reason_str = " & ".join(reasons)
#         print(f"   [{mode_label}] {symbol} (ADX: {adx_value:.1f}): {reason_str}")

# def check_closed_trades():
#     conn = sqlite3.connect('trading_bot.db')
#     # Lấy danh sách các cặp tiền đang có lệnh 'UNKNOWN'
#     df_pending = pd.read_sql_query("SELECT symbol FROM trade_history WHERE result = 'UNKNOWN'", conn)
#     conn.close()

#     for symbol in df_pending['symbol'].unique():
#         # 1. Kiểm tra vị thế trên sàn
#         pos = exchange.fetch_positions([symbol])
#         has_position = any(float(p['contracts']) != 0 for p in pos if p['symbol'] == symbol)

#         # 2. Nếu KHÔNG còn vị thế -> Lệnh đã chạm TP hoặc SL
#         if not has_position:
#             # --- BỔ SUNG: HỦY TOÀN BỘ LỆNH TREO CÒN LẠI ---
#             try:
#                 exchange.cancel_all_orders(symbol) 
#                 print(f"   [!] {symbol}: Đã dọn dẹp các lệnh TP/SL thừa.")
#             except Exception as e:
#                 print(f"   [!] Không thể hủy lệnh thừa cho {symbol}: {e}")

#             # 3. Cập nhật kết quả vào Database
#             closed_orders = exchange.fetch_closed_orders(symbol, limit=5)
#             if closed_orders:
#                 last_order = closed_orders[-1]
#                 pnl = last_order.get('info', {}).get('realizedPnl', 0)
#                 result = "WIN" if float(pnl) > 0 else "LOSS"
#                 update_trade_result(symbol, result, float(pnl))
#                 print(f"✅ Đã cập nhật kết quả cho {symbol}: {result}")




import sqlite3
import pandas as pd
import pandas_ta as ta
from datetime import datetime, timedelta
from module.config import exchange, HTF, LTF, MAX_OPEN_POSITIONS
from module.data_fetcher import fetch_market_data, get_smart_money_data
from module.execution import format_price, calculate_binance_qty, execute_trade_with_tpsl
from module.database import log_trade, update_trade_result

# --- HÀM HỖ TRỢ: KIỂM TRA KHOẢNG NGHỈ (COOL-DOWN) ---
# def is_in_cooldown(symbol, hours=1):
#     """Ngăn bot vào lệnh liên tục trên cùng một cặp tiền sau khi vừa đóng lệnh"""
#     conn = sqlite3.connect('trading_bot.db')
#     query = f"SELECT timestamp FROM trade_history WHERE symbol = '{symbol}' ORDER BY timestamp DESC LIMIT 1"
#     last_trade = pd.read_sql_query(query, conn)
#     conn.close()
    
#     if not last_trade.empty:
#         # Chuyển đổi timestamp từ DB sang đối tượng datetime
#         last_time = pd.to_datetime(last_trade.iloc[0]['timestamp'])
#         if datetime.now() < last_time + timedelta(hours=hours):
#             return True
#     return False

def manage_trade(symbol, current_risk_pct):
    # 1. Kiểm tra vị thế hiện tại
    positions = exchange.fetch_positions([symbol])
    if any(float(p['contracts']) != 0 for p in positions if p['symbol'] == symbol):
        print(f"   [-] {symbol}: Đã có vị thế đang mở. Bỏ qua.")
        return

    # 2. Kiểm tra khoảng nghỉ (Cool-down) để tránh overtrading
    # if is_in_cooldown(symbol, hours=1):
    #     print(f"   [!] {symbol}: Đang trong thời gian nghỉ 1h sau lệnh trước.")
    #     return

    active_pos_count = len([p for p in exchange.fetch_positions() if float(p['contracts']) != 0])
    if active_pos_count >= MAX_OPEN_POSITIONS:
        print(f"   [-] {symbol}: Đạt giới hạn tối đa ({MAX_OPEN_POSITIONS}) lệnh.")
        return
    
    # 3. Lấy dữ liệu Đa khung thời gian
    df_htf = fetch_market_data(symbol, HTF)
    df_htf['ema200'] = ta.ema(df_htf['close'], length=200)
    # Xác định xu hướng khung lớn: Chỉ đánh thuận theo EMA 200
    htf_trend = "UP" if df_htf.iloc[-1]['close'] > df_htf.iloc[-1]['ema200'] else "DOWN"

    df_ltf = fetch_market_data(symbol, LTF)
    # Thắt chặt bộ lọc ADX: Hạ xuống 20 để nhận diện xu hướng sớm hơn
    df_ltf['adx'] = ta.adx(df_ltf['high'], df_ltf['low'], df_ltf['close'])['ADX_14']
    df_ltf['atr'] = ta.atr(df_ltf['high'], df_ltf['low'], df_ltf['close'])
    
    bb = ta.bbands(df_ltf['close'], length=20, std=2)
    df_ltf['bb_lower'] = bb.iloc[:, 0]
    df_ltf['bb_middle'] = bb.iloc[:, 1]
    df_ltf['bb_upper'] = bb.iloc[:, 2]

    last = df_ltf.iloc[-1]
    adx_value = last['adx']
    atr_value = last['atr']
    smart = get_smart_money_data(symbol)
    balance = exchange.fetch_balance()['total']['USDT']

    # Xác định chế độ: Thắt chặt Grid chỉ khi ADX < 20
    is_trend_mode = adx_value >= 20 
    mode_label = "📈 TREND" if is_trend_mode else "↔️ GRID"
    
    strategy, side, sl_raw, tp_raw = None, None, 0, 0
    reasons = []

    # --- 4. PHÂN TÍCH LOGIC CẢI TIẾN ---

    if is_trend_mode:
        # CHIẾN LƯỢC TREND: Chỉ đánh thuận HTF
        if htf_trend == "UP":
            if last['close'] > last['bb_upper'] and smart['oi_trend'] == "UP":
                strategy, side = "TREND_FOLLOW_LONG", "LONG"
                # Cải thiện SL: Dùng ATR x 2.5 để tránh quét râu
                sl_raw = last['close'] - (2.5 * atr_value)
                tp_raw = last['close'] + (4.0 * atr_value) # Tăng R:R lên 1:1.6
            else:
                reasons.append(f"Chờ breakout & OI (OI: {smart['oi_trend']})")
        
        elif htf_trend == "DOWN":
            if last['close'] < last['bb_lower'] and smart['oi_trend'] == "UP":
                strategy, side = "TREND_FOLLOW_SHORT", "SHORT"
                sl_raw = last['close'] + (2.5 * atr_value)
                tp_raw = last['close'] - (4.0 * atr_value)
            else:
                reasons.append(f"Chờ breakout & OI (OI: {smart['oi_trend']})")

    else:
        # CHIẾN LƯỢC GRID THÔNG MINH: Vẫn phải thuận HTF
        if htf_trend == "UP" and last['close'] <= last['bb_lower']:
            strategy, side = "GRID_SMART_LONG", "LONG"
            sl_raw = last['close'] - (2.5 * atr_value)
            tp_raw = last['bb_middle']
        elif htf_trend == "DOWN" and last['close'] >= last['bb_upper']:
            strategy, side = "GRID_SMART_SHORT", "SHORT"
            sl_raw = last['close'] + (2.5 * atr_value)
            tp_raw = last['bb_middle']
        else:
            reasons.append(f"Sideway ngược xu hướng chính hoặc chưa chạm biên")

    # --- 5. HIỂN THỊ LOG & VÀO LỆNH ---
    if strategy:
        sl = format_price(symbol, sl_raw)
        tp = format_price(symbol, tp_raw)
        qty = calculate_binance_qty(symbol, balance * current_risk_pct, abs(last['close'] - sl))
        
        if qty > 0:
            msg = f"🔔 *KÍCH HOẠT {mode_label}*\nCặp: {symbol}\nLệnh: {side}\nGiá: {last['close']}\nSL: {sl} | TP: {tp}"
            # Gửi lệnh với order_side đã fix (buy/sell)
            if execute_trade_with_tpsl(symbol, side, qty, sl, tp, msg):
                log_trade(symbol, strategy, side, last['close'], adx_value)
    else:
        reason_str = " & ".join(reasons)
        print(f"   [{mode_label}] {symbol} (ADX: {adx_value:.1f}): {reason_str}")

def check_closed_trades():
    """Kiểm tra lệnh đã đóng và dọn dẹp lệnh treo thừa"""
    conn = sqlite3.connect('trading_bot.db')
    df_pending = pd.read_sql_query("SELECT symbol FROM trade_history WHERE result = 'UNKNOWN'", conn)
    conn.close()

    for symbol in df_pending['symbol'].unique():
        pos = exchange.fetch_positions([symbol])
        has_position = any(float(p['contracts']) != 0 for p in pos if p['symbol'] == symbol)

        if not has_position:
            # Hủy lệnh thừa để tránh 'rác' sàn
            try:
                exchange.cancel_all_orders(symbol) 
                print(f"   [!] {symbol}: Đã dọn dẹp các lệnh thừa.")
            except:
                pass

            # Cập nhật kết quả lãi/lỗ thực tế
            try:
                closed_orders = exchange.fetch_closed_orders(symbol, limit=5)
                if closed_orders:
                    last_order = closed_orders[-1]
                    pnl = last_order.get('info', {}).get('realizedPnl', 0)
                    result = "WIN" if float(pnl) > 0 else "LOSS"
                    update_trade_result(symbol, result, float(pnl))
                    print(f"✅ Đã cập nhật kết quả cho {symbol}: {result} (PnL: {pnl})")
            except Exception as e:
                print(f"   [!] Lỗi cập nhật DB cho {symbol}: {e}")