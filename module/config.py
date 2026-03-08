import ccxt

API_CONFIG = {
    # 'apiKey': 'cb5v3kgnZXp0P552OqJf6FjYm8A5TOE9WhP19muXPEQNnnDTuxuG4xQC4CpFeZoI', # Mainet
    # 'secret': 'khllhbYlCTPNthPRQCvmU6URjdz0MSKccPYoq0RztDdKslqLuZXVYfI4G6tBkKv4', # Mainet
    'apiKey': 'HNL34A79F0VBsWW5tdQ9PPoM2ig8Sw5Kpf1Zj8YYJ37zGf4zEJiDwfIQm9o5sXiF', # Testnet
    'secret': 'AtBQO3DDGtQqghyeMegVVm2VYJ9BO1NMSm7iXAF48YxADiB2ErumVWD0teSV3C3k', # Testnet
    'enableRateLimit': True,
    'options': {'defaultType': 'future'} # Quan trọng: Chế độ Futures USDS-M
}

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
print("Đang kích hoạt chế độ Sandbox (Testnet)...")
exchange.set_sandbox_mode(True)
print("✅ Kích hoạt chế độ Sandbox (Testnet) thành công!")

print("Đang tải danh sách thị trường (có thể mất 1-2 phút)...")
exchange.load_markets()
print("✅ Đã tải danh sách thị trường!")