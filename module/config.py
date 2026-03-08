import ccxt

# region MAINET
API_CONFIG = {
    'apiKey': 'cb5v3kgnZXp0P552OqJf6FjYm8A5TOE9WhP19muXPEQNnnDTuxuG4xQC4CpFeZoI',
    'secret': 'khllhbYlCTPNthPRQCvmU6URjdz0MSKccPYoq0RztDdKslqLuZXVYfI4G6tBkKv4',
    'enableRateLimit': True,
    'options': {'defaultType': 'future'} # Quan trọng: Chế độ Futures USDS-M
}
# endregion 

# region TESTNET
# API_CONFIG = {
#     # Key lấy từ ảnh image_8f2ffd.png
#     'apiKey': 'HFWP5nT6s9a7ofCnUk4HAfEXaJDm10frvyX3Mhk6xhIb2ljwlXGTsqVPGoJQ rPP4', 
#     'secret': 'JRf05S9O9RBu2d2jUJwGSgZnRZtG48VRRcWyQib6sgAmIVTIsMMKIkMMrm1Go5Yy', 
#     'enableRateLimit': True,
#     'options': {
#         'defaultType': 'future',
#         'urls': {
#             'api': {
#                 # SỬA ĐÚNG URL DEMO (địa chỉ này khác hoàn toàn Testnet cũ)
#                 'public': 'https://demo-fapi.binance.com/fapi/v1',
#                 'private': 'https://demo-fapi.binance.com/fapi/v1',
#             }
#         }
#     }
# }
#endregion

TELEGRAM_TOKEN = '8625315462:AAGOVgmHqBJtVmHmjIvScoy8mRF3aEB22RI'
TELEGRAM_CHAT_ID = '1437886934'

# Danh sách coin đa dạng để bot có nhiều cơ hội quét lệnh
SYMBOLS = ['BTC/USDT', 'ETH/USDT']
HTF = '4h'   
LTF = '15m'  
MAX_OPEN_POSITIONS = 3
WHALE_LIQ_THRESHOLD = 500  

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