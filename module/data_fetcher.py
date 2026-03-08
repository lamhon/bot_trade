import time

import pandas as pd
import pandas_ta as ta
from module.config import exchange

oi_memory = {}

def fetch_market_data(symbol, timeframe, limit=200):
    # bars = exchange.fetch_ohlcv(symbol, timeframe=timeframe, limit=limit)
    # df = pd.DataFrame(bars, columns=['timestamp', 'open', 'high', 'low', 'close', 'volume'])
    # return df

    for i in range(3):  # Thử lại tối đa 3 lần
        try:
            bars = exchange.fetch_ohlcv(symbol, timeframe=timeframe, limit=limit)
            df = pd.DataFrame(bars, columns=['timestamp', 'open', 'high', 'low', 'close', 'volume'])
            return df
        except Exception as e:
            if i < 2:
                time.sleep(2) # Đợi 2 giây rồi thử lại
                continue
            else:
                raise e # Nếu quá 3 lần vẫn lỗi thì mới báo lỗi ra màn hình

def get_smart_money_data(symbol):
    global oi_memory
    try:
        # Lấy Open Interest từ Binance
        oi_data = exchange.fetch_open_interest(symbol)
        current_oi = float(oi_data['baseVolume'])
        
        oi_trend = "FLAT"
        if symbol in oi_memory:
            if current_oi > oi_memory[symbol] * 1.01: oi_trend = "UP"
            elif current_oi < oi_memory[symbol] * 0.99: oi_trend = "DOWN"
        oi_memory[symbol] = current_oi
        
        # Binance Liquidation cần quyền cao, tạm dùng Volume làm bộ lọc thay thế
        ticker = exchange.fetch_ticker(symbol)
        vol_spike = ticker['quoteVolume'] / 1440 # Vol trung bình phút
        
        return {'oi_trend': oi_trend, 'vol_spike': vol_spike}
    except:
        return {'oi_trend': 'FLAT', 'vol_spike': 0}