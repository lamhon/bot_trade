import ccxt

# ==================== API CONFIG ====================
# region MAINET
# API_CONFIG = {
#     'apiKey': 'cb5v3kgnZXp0P552OqJf6FjYm8A5TOE9WhP19muXPEQNnnDTuxuG4xQC4CpFeZoI',
#     'secret': 'khllhbYlCTPNthPRQCvmU6URjdz0MSKccPYoq0RztDdKslqLuZXVYfI4G6tBkKv4',
#     'enableRateLimit': True,
#     'options': {'defaultType': 'future'} # Quan trọng: Chế độ Futures USDS-M
# }
# endregion 

# region TESTNET
API_CONFIG = {
    # Key lấy từ ảnh image_8f2ffd.png
    'apiKey': 'HFWP5nT6s9a7ofCnUk4HAfEXaJDm10frvyX3Mhk6xhIb2ljwlXGTsqVPGoJQrPP4', 
    'secret': 'JRf05S9O9RBu2d2jUJwGSgZnRZtG48VRRcWyQib6sgAmIVTIsMMKIkMMrm1Go5Yy', 
    'enableRateLimit': True,
    'options': {
        'defaultType': 'future',
        'urls': {
            'api': {
                # SỬA ĐÚNG URL DEMO (địa chỉ này khác hoàn toàn Testnet cũ)
                'public': 'https://demo-fapi.binance.com',
                'private': 'https://demo-fapi.binance.com',
            }
        }
    }
}
#endregion

# ==================== TELEGRAM CONFIG ====================
TELEGRAM_TOKEN = '8625315462:AAGOVgmHqBJtVmHmjIvScoy8mRF3aEB22RI'
TELEGRAM_CHAT_ID = '1437886934'

# ==================== TRADING CONFIG ====================
# Danh sách coin đa dạng để bot có nhiều cơ hội quét lệnh
SYMBOLS = ['BTC/USDT', 'ETH/USDT']
HTF = '4h'   
LTF = '15m'  
MAX_OPEN_POSITIONS = 3
WHALE_LIQ_THRESHOLD = 500
BASE_RISK = 0.03  # Khởi điểm 3% để phù hợp với vốn 40$

# ==================== DATABASE CONFIG ====================
DATABASE_NAME = 'trading_bot.db'

# ==================== DATA FETCHER CONFIG ====================
DATA_FETCH_RETRY_COUNT = 3
DATA_FETCH_RETRY_DELAY = 2  # giây
OI_UP_THRESHOLD = 1.01
OI_DOWN_THRESHOLD = 0.99
AVG_VOLUME_DIVISOR = 1440  # số phút trong ngày

# ==================== STRATEGY CONFIG ====================
EMA_LENGTH = 200
ADX_PERIOD = 14
ADX_TRENDING_THRESHOLD = 25
BB_LENGTH = 20
BB_STD = 2
ATR_MULTIPLIER_SL = 2
ATR_MULTIPLIER_TP = 3

# ==================== EXECUTION CONFIG ====================
MIN_NOTIONAL_DEFAULT = 5.0  # USDT
MIN_NOTIONAL_BUFFER = 0.1  # USDT

# ==================== REFLECTION CONFIG ====================
WIN_RATE_CHECK_COUNT = 20
WIN_RATE_LOW_THRESHOLD = 0.4  # 40%
WIN_RATE_LOW_RISK_MULTIPLIER = 0.5
WIN_RATE_HIGH_THRESHOLD = 0.7  # 70%
WIN_RATE_HIGH_RISK_MULTIPLIER = 1.2
WEEKLY_REPORT_DAY = 6  # Chủ Nhật
WEEKLY_REPORT_HOUR = 20  # 20h

# ==================== TIMING CONFIG ====================
MAIN_LOOP_SLEEP = 300  # giây (5 phút)
TELEGRA_REQUEST_TIMEOUT = 10  # giây

print("Đang kết nối Binance...")
exchange = ccxt.binance(API_CONFIG)
print("✅ Kết nối Binance thành công!")

# QUAN TRỌNG: Kích hoạt chế độ Sandbox (Testnet)
# print("Đang kích hoạt chế độ Sandbox (Testnet)...")
# exchange.set_sandbox_mode(True)
# print("✅ Kích hoạt chế độ Sandbox (Testnet) thành công!")

print("Đang tải danh sách thị trường (có thể mất 1-2 phút)...")
exchange.load_markets()
print("✅ Đã tải danh sách thị trường!")