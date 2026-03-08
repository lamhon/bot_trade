from module.config import exchange
from module.telegram import send_telegram

def format_price(symbol, price):
    return float(exchange.price_to_precision(symbol, price))

def calculate_binance_qty(symbol, risk_usdt, sl_distance):
    try:
        # Lấy thông tin thị trường để biết các giới hạn (Filters)
        market = exchange.market(symbol)
        ticker = exchange.fetch_ticker(symbol)
        current_price = ticker['last']
        
        # Công thức tính khối lượng dựa trên rủi ro:
        # $$PositionSize = \frac{RiskAmount}{SL_Distance}$$
        raw_qty = risk_usdt / sl_distance
        
        # 1. Làm tròn theo bước nhảy của sàn (Step Size/Precision)
        qty = float(exchange.amount_to_precision(symbol, raw_qty))
        
        # 2. Kiểm tra giới hạn số lượng tối thiểu (Min Quantity)
        min_qty = market['limits']['amount']['min']
        if qty < min_qty:
            qty = min_qty
            
        # 3. Kiểm tra giá trị lệnh tối thiểu (Min Notional)
        # Binance Futures thường yêu cầu lệnh tối thiểu 5 hoặc 10 USDT
        min_cost = market['limits']['cost']['min'] if market['limits']['cost']['min'] else 5.0
        
        if (qty * current_price) < min_cost:
            # Nếu giá trị lệnh quá nhỏ, buộc phải tăng Qty lên mức tối thiểu của sàn
            qty = float(exchange.amount_to_precision(symbol, (min_cost + 0.1) / current_price))
            print(f"   ⚠️ {symbol}: Giá trị lệnh quá thấp. Đã điều chỉnh Qty lên {qty} để đạt {min_cost} USDT.")

        return qty
    except Exception as e:
        print(f"❌ Lỗi khi tính toán Qty cho {symbol}: {e}")
        return 0

def execute_trade_with_tpsl(symbol, side, qty, sl_price, tp_price, message):
    try:
        # Chuyển đổi từ thuật ngữ chiến lược sang thuật ngữ lệnh của sàn
        # side đang là "LONG" hoặc "SHORT"
        if side == "LONG":
            order_side = 'buy'
            close_side = 'sell'
        else:
            order_side = 'sell'
            close_side = 'buy'

        # 1. Lệnh Market chính (Sửa chỗ side thành order_side)
        order = exchange.create_market_order(symbol, order_side, qty)
        
        # 2. Lệnh Stop Loss (Binance dùng STOP_MARKET)
        exchange.create_order(
            symbol=symbol, 
            type='STOP_MARKET', 
            side=close_side, 
            amount=qty, 
            params={'stopPrice': sl_price, 'reduceOnly': True}
        )

        # 3. Lệnh Take Profit (Binance dùng TAKE_PROFIT_MARKET)
        if tp_price:
            exchange.create_order(
                symbol=symbol, 
                type='TAKE_PROFIT_MARKET', 
                side=close_side, 
                amount=qty, 
                params={'stopPrice': tp_price, 'reduceOnly': True}
            )
        
        send_telegram(f"{message}\n✅ *BINANCE EXECUTION SUCCESS*")
        return True
    except Exception as e:
        # Gửi lỗi chi tiết về Telegram để mình biết đường fix
        send_telegram(f"❌ *ORDER FAILED*: {symbol}\nLỗi: {e}")
        return False