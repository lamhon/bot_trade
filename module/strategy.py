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

#region --- HÀM HỖ TRỢ: KIỂM TRA KHOẢNG NGHỈ (COOL-DOWN) ---
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
#endregion

def manage_trade(symbol, current_risk_pct):
    #region 1. Kiểm tra vị thế hiện tại
    #Des: Giúp không để vào quá nhiều lệnh chồng chéo trên cùng 1 đồng

    # Lấy danh sách các vị thế (Lệnh đang chạy)
    positions = exchange.fetch_positions([symbol])

    # Quét qua danh sách vị thế vừa lấy về
    if any(float(p['contracts']) != 0 for p in positions if p['symbol'] == symbol):
        print(f"   [-] {symbol}: Đã có vị thế đang mở. Bỏ qua.")
        return
    #endrgion

    # 2. Kiểm tra khoảng nghỉ (Cool-down) để tránh overtrading
    # if is_in_cooldown(symbol, hours=1):
    #     print(f"   [!] {symbol}: Đang trong thời gian nghỉ 1h sau lệnh trước.")
    #     return

    # region Quản lý rủi ro trên toàn bộ tàì khoản
    # Des: Nếu số vị thế = MAX_OPEN_POSITIONS thì sẽ không mở thêm vị thế
    active_pos_count = len([p for p in exchange.fetch_positions() if float(p['contracts']) != 0])
    if active_pos_count >= MAX_OPEN_POSITIONS:
        print(f"   [-] {symbol}: Đạt giới hạn tối đa ({MAX_OPEN_POSITIONS}) lệnh.")
        return
    # endregion
    
    # region Lấy dữ liệu Đa khung thời gian
    # Des:  Kiểm tra xu hướng chủ đạo của thị trường dựa trên HTF trong config
    #       Giúp bot không mở lệnh trái với xu hướng chính (bot sẽ mở lệnh ở khung 15m)
    df_htf = fetch_market_data(symbol, HTF)
    df_htf['ema200'] = ta.ema(df_htf['close'], length=200)
    # Xác định xu hướng khung lớn: Chỉ đánh thuận theo EMA 200
    # Nếu giá < EMA200: UP || Giá > EMA200: DOWN
    htf_trend = "UP" if df_htf.iloc[-1]['close'] > df_htf.iloc[-1]['ema200'] else "DOWN"
    # endregion

    #region Kiểm tra market đang ở dạng nào để chọn chiến lược đánh
    # Lấy dữ liệu ở khung tg thấp (LTF) để tính toán chỉ báo
    df_ltf = fetch_market_data(symbol, LTF)
    # Đo độ mạnh xu hướng => bot nhận diện market đang giao động mạnh hay sideway
    df_ltf['adx'] = ta.adx(df_ltf['high'], df_ltf['low'], df_ltf['close'])['ADX_14']
    # Đo lường độ biến động trung bình của giá: Trong 14 nến gần nhất, TB giá nhảy bao nhiêu đơn vị
    df_ltf['atr'] = ta.atr(df_ltf['high'], df_ltf['low'], df_ltf['close'])
    #endregion

    # region:   Thiết lập Bollinger Bands
    # Des:      Xác định vùng "oversold" hoặc "overbuy" tại khung vào lệnh (15m)
    #           Trong chế độ GRID: Bot tìm cách đánh đảo chiều
    #           Trong chế độ TREND: Bot tìm cách đánh theo đà phá vỡ (Breakout).

    # Tính toán chỉ báo BB dựa trên giá đóng cửa, length=20: chu kỳ 20 nến gần nhất
    bb = ta.bbands(df_ltf['close'], length=20, std=2)

    #Lấy cột đầu tiên của kết quả (thường là dải dưới - Lower Band). Đây được coi là vùng Hỗ trợ động.
    df_ltf['bb_lower'] = bb.iloc[:, 0]

    #Lấy cột thứ hai (đường trung bình giữa - Middle Band/SMA 20). Đây là trục cân bằng của giá.
    df_ltf['bb_middle'] = bb.iloc[:, 1]

    #Lấy cột thứ ba (dải trên - Upper Band). Đây được coi là vùng Kháng cự động.
    df_ltf['bb_upper'] = bb.iloc[:, 2]
    #endregion

    #region Thu thập data thực tế trước khi đưa ra quyết định
    # df_ltf: là bảng dữ liệu chứa hàng trăm cây nến 15 phút.
    # .iloc[-1] lệnh cho bot chỉ lấy ra hàng cuối cùng (cây nến hiện tại đang chạy hoặc vừa đóng cửa). Đây là dữ liệu nóng nhất để bot xử lý.
    
    # Bot lấy giá trị cụ thể của ADX và ATR từ cây nến cuối cùng đó.
    last = df_ltf.iloc[-1]

    #adx_value: Dùng để chọn chế độ đánh (Trend nếu >= ADX, Grid nếu < ADX).
    adx_value = last['adx']

    #Dùng để tính toán khoảng cách dừng lỗ an toàn (2.5 x ATR)
    atr_value = last['atr']

    #Bot gọi một hàm phụ trợ để lấy dữ liệu từ các "Cá mập" (Smart Money), thường là chỉ số Open Interest (OI)
    smart = get_smart_money_data(symbol)

    # Kiểm tra số dư ví
    balance = exchange.fetch_balance()['total']['USDT']

    # region Xác định chế độ
    # Des:  Xác định trạng thái market
    is_trend_mode = adx_value >= 25 
    mode_label = "📈 TREND" if is_trend_mode else "↔️ GRID"
    
    strategy, side, sl_raw, tp_raw = None, None, 0, 0
    reasons = []
    #endregion

    # region --- LOGIC QUYẾT ĐỊNH ---
    if is_trend_mode:
        # CHIẾN LƯỢC TREND: Chỉ đánh thuận HTF
        if htf_trend == "UP":
            # Giá phải đóng cửa vượt ra ngoài dải Bollinger Bands
            # Chỉ số Open Interest (OI) phải đang tăng (xác nhận rằng "Cá mập" đang thực sự đổ tiền vào để đẩy giá đi tiếp)
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
    #endregion

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