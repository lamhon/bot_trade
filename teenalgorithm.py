"""
=============================================================================
 TEENALGORITHM.PY - CRYPTO TRADING BOT
 Tích hợp: Thuật toán 4 giai đoạn tối ưu WinRate + OKX API + Telegram Alert
=============================================================================
 Yêu cầu cài đặt thư viện:
   pip install pandas numpy pandas-ta ccxt python-telegram-bot requests
=============================================================================
 Cấu hình: Điền API Key và Token vào phần CONFIG bên dưới trước khi chạy.
=============================================================================
"""

import os
import time
import logging
import asyncio
import pandas as pd
import pandas_ta as ta
import numpy as np
import ccxt
import requests

# ─────────────────────────────────────────────────────────────────
# LOGGING - Ghi lại toàn bộ hoạt động bot ra file và console
# ─────────────────────────────────────────────────────────────────
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(message)s',
    handlers=[
        logging.FileHandler("teenalgorithm.log", encoding="utf-8"),
        logging.StreamHandler()
    ]
)
log = logging.getLogger(__name__)

# ─────────────────────────────────────────────────────────────────
# ██████████████ CẤU HÌNH - ĐIỀN THÔNG TIN CỦA BẠN VÀO ĐÂY ██████
# ─────────────────────────────────────────────────────────────────
CONFIG = {
    # === OKX API ===
    # Lấy tại: OKX → Dashboard → API Management (Bật quyền Trade)
    "OKX_API_KEY"       : "YOUR_OKX_API_KEY",
    "OKX_SECRET_KEY"    : "YOUR_OKX_SECRET_KEY",
    "OKX_PASSPHRASE"    : "YOUR_OKX_PASSPHRASE",

    # === TELEGRAM ===
    # Token bot: Tạo bot tại @BotFather trên Telegram
    # Chat ID: Gửi tin nhắn bất kỳ cho bot, sau đó lấy ID tại
    #   https://api.telegram.org/bot<TOKEN>/getUpdates
    "TELEGRAM_TOKEN"    : "YOUR_TELEGRAM_BOT_TOKEN",
    "TELEGRAM_CHAT_ID"  : "YOUR_TELEGRAM_CHAT_ID",

    # === THAM SỐ GIAO DỊCH ===
    "SYMBOL"            : "BTC/USDT:USDT",  # Cặp giao dịch (Perpetual Futures)
    "TIMEFRAME"         : "1h",             # Khung thời gian nến
    "CANDLE_LIMIT"      : 300,              # Số nến lấy về để tính chỉ báo (cần ≥ 210 cho EMA200)
    "TRADE_SIZE_USDT"   : 10.0,             # Số USDT mỗi lệnh (rủi ro mỗi lệnh)
    "LEVERAGE"          : 5,                # Đòn bẩy (x5) - KHÔNG ĐẶT QUÁ CAO

    # === THAM SỐ THUẬT TOÁN ===
    "ADX_THRESHOLD"     : 25,              # ADX > 25 = thị trường có xu hướng đủ mạnh
    "ATR_SL_MULT"       : 1.5,             # Stop-loss = 1.5 * ATR
    "ATR_TP_MULT"       : 3.0,             # Take-profit = 3.0 * ATR (R:R = 1:2)
    "MAX_BARS_IN_TRADE" : 20,              # Tối đa 20 nến/lệnh rồi tự thoát

    # === CHẾ ĐỘ CHẠY ===
    "DRY_RUN"           : True,            # True = Chạy giả lập (không đặt lệnh thật)
                                           # False = Vào lệnh thật trên OKX
    "LOOP_INTERVAL_SEC" : 60,             # Kiểm tra tín hiệu mỗi 60 giây
}

# ─────────────────────────────────────────────────────────────────
# MODULE 1: KẾT NỐI OKX
# ─────────────────────────────────────────────────────────────────
def create_exchange() -> ccxt.okx:
    """Khởi tạo đối tượng kết nối OKX với thông tin API trong CONFIG."""
    exchange = ccxt.okx({
        'apiKey'    : CONFIG["OKX_API_KEY"],
        'secret'    : CONFIG["OKX_SECRET_KEY"],
        'password'  : CONFIG["OKX_PASSPHRASE"],
        'options'   : {'defaultType': 'swap'},  # Chế độ Perpetual Futures
    })
    exchange.set_sandbox_mode(False)
    return exchange


def fetch_ohlcv(exchange: ccxt.okx) -> pd.DataFrame:
    """
    Lấy dữ liệu nến OHLCV từ OKX.
    Trả về DataFrame với các cột: Open, High, Low, Close, Volume.
    """
    raw = exchange.fetch_ohlcv(
        symbol    = CONFIG["SYMBOL"],
        timeframe = CONFIG["TIMEFRAME"],
        limit     = CONFIG["CANDLE_LIMIT"]
    )
    df = pd.DataFrame(raw, columns=["Timestamp", "Open", "High", "Low", "Close", "Volume"])
    df["Timestamp"] = pd.to_datetime(df["Timestamp"], unit="ms")
    df.set_index("Timestamp", inplace=True)
    return df


# ─────────────────────────────────────────────────────────────────
# MODULE 2: THUẬT TOÁN 4 GIAI ĐOẠN (Tối ưu WinRate)
# ─────────────────────────────────────────────────────────────────
def compute_indicators(df: pd.DataFrame) -> pd.DataFrame:
    """
    Tính toán tất cả chỉ báo kỹ thuật cần thiết.
    [Giai đoạn 1 & 2]: Chuẩn bị dữ liệu để lọc nhiễu và xác định trend.
    """
    # Trend chính (EMA 200): Bot chỉ LONG khi giá TRÊN đường này.
    df['EMA_200'] = ta.ema(df['Close'], length=200)

    # Sức mạnh xu hướng (ADX 14): Lọc thị trường sideway.
    adx_df = ta.adx(df['High'], df['Low'], df['Close'], length=14)
    df['ADX'] = adx_df['ADX_14'] if adx_df is not None else 0.0

    # Tín hiệu cụ thể (EMA Cross 10/20): Phát hiện bứt phá ngắn hạn.
    df['EMA_10'] = ta.ema(df['Close'], length=10)
    df['EMA_20'] = ta.ema(df['Close'], length=20)

    # Xác nhận khối lượng: Cá voi vào hàng.
    df['Vol_SMA_20'] = ta.sma(df['Volume'], length=20)

    # Biến động thực tế (ATR 14): Giai đoạn 3 - Tính SL/TP động.
    df['ATR'] = ta.atr(df['High'], df['Low'], df['Close'], length=14)

    return df.dropna()


def detect_signal(df: pd.DataFrame) -> dict | None:
    """
    Phân tích nến MỚI NHẤT (nến vừa đóng xong) và kiểm tra xem có tín hiệu LONG không.
    [Giai đoạn 1-4]: Tổng hợp toàn bộ bộ lọc trước khi ra quyết định.
    Trả về dict thông tin tín hiệu hoặc None nếu không có tín hiệu.
    """
    # Dùng nến gần nhất đã đóng (index -1 là nến đang hình thành, -2 là đã đóng)
    last  = df.iloc[-2]
    prev  = df.iloc[-3]

    # ─── BỘ LỌC GIAI ĐOẠN 1 & 2: Loại bỏ nhiễu ───
    above_ema200  = last['Close'] > last['EMA_200']            # Xu hướng chính tăng
    trend_strong  = last['ADX'] > CONFIG["ADX_THRESHOLD"]      # Sóng có lực đủ mạnh
    ema_crossover = (last['EMA_10'] > last['EMA_20']) and \
                    (prev['EMA_10'] <= prev['EMA_20'])          # Golden Cross 10/20
    vol_confirm   = last['Volume'] > last['Vol_SMA_20']        # Khối lượng xác nhận

    if not (above_ema200 and trend_strong and ema_crossover and vol_confirm):
        return None  # Không đủ điều kiện → Không vào lệnh

    # ─── GIAI ĐOẠN 3: Tính SL / TP động theo ATR ───
    entry_price = last['Close']
    atr         = last['ATR']
    stop_loss   = round(entry_price - CONFIG["ATR_SL_MULT"] * atr, 2)
    take_profit = round(entry_price + CONFIG["ATR_TP_MULT"] * atr, 2)
    risk_pct    = round(((entry_price - stop_loss) / entry_price) * 100, 2)

    return {
        "symbol"      : CONFIG["SYMBOL"],
        "side"        : "LONG",
        "entry"       : round(entry_price, 2),
        "stop_loss"   : stop_loss,
        "take_profit" : take_profit,
        "atr"         : round(atr, 2),
        "adx"         : round(last['ADX'], 2),
        "risk_pct"    : risk_pct,
        "timestamp"   : str(df.index[-2]),
    }


# ─────────────────────────────────────────────────────────────────
# MODULE 3: GỬI TÍN HIỆU TELEGRAM
# ─────────────────────────────────────────────────────────────────
def send_telegram(message: str) -> None:
    """Gửi tin nhắn text về Telegram qua Bot API."""
    url = f"https://api.telegram.org/bot{CONFIG['TELEGRAM_TOKEN']}/sendMessage"
    payload = {
        "chat_id"    : CONFIG["TELEGRAM_CHAT_ID"],
        "text"       : message,
        "parse_mode" : "HTML",
    }
    try:
        resp = requests.post(url, json=payload, timeout=10)
        if resp.status_code != 200:
            log.warning(f"Telegram gửi thất bại: {resp.text}")
        else:
            log.info("📨 Đã gửi tín hiệu về Telegram.")
    except Exception as e:
        log.error(f"Lỗi khi gửi Telegram: {e}")


def format_signal_message(signal: dict, order_result: dict | None = None) -> str:
    """Tạo nội dung tin nhắn Telegram đẹp, dễ đọc cho trader."""
    mode_label = "🧪 <b>[DRY-RUN - Giả Lập]</b>" if CONFIG["DRY_RUN"] else "🚀 <b>[LIVE ORDER]</b>"

    msg = (
        f"{mode_label}\n"
        f"━━━━━━━━━━━━━━━━━━━━━━\n"
        f"🔔 <b>TEEN ALGORITHM - TÍN HIỆU MUA</b>\n"
        f"━━━━━━━━━━━━━━━━━━━━━━\n"
        f"📌 Cặp giao dịch : <b>{signal['symbol']}</b>\n"
        f"📈 Hướng lệnh    : <b>{signal['side']}</b>\n"
        f"🕐 Thời gian     : <b>{signal['timestamp']}</b>\n"
        f"━━━━━━━━━━━━━━━━━━━━━━\n"
        f"💰 Giá vào lệnh  : <b>${signal['entry']:,}</b>\n"
        f"🛑 Stop-Loss     : <b>${signal['stop_loss']:,}</b>  ({signal['risk_pct']}% rủi ro)\n"
        f"🎯 Take-Profit   : <b>${signal['take_profit']:,}</b>  (R:R = 1:2)\n"
        f"━━━━━━━━━━━━━━━━━━━━━━\n"
        f"📊 ADX (Lực trend): <b>{signal['adx']}</b> (> {CONFIG['ADX_THRESHOLD']} ✅)\n"
        f"📉 ATR (Độ giật) : <b>${signal['atr']}</b>\n"
    )

    if order_result:
        msg += (
            f"━━━━━━━━━━━━━━━━━━━━━━\n"
            f"✅ Order ID OKX: <code>{order_result.get('id', 'N/A')}</code>\n"
        )

    msg += "━━━━━━━━━━━━━━━━━━━━━━"
    return msg


# ─────────────────────────────────────────────────────────────────
# MODULE 4: THỰC THI LỆNH TRÊN OKX
# ─────────────────────────────────────────────────────────────────
def place_order(exchange: ccxt.okx, signal: dict) -> dict | None:
    """
    Đặt lệnh Market Long thực tế lên OKX kèm SL/TP tích hợp.
    Chỉ được gọi khi DRY_RUN = False.
    """
    try:
        symbol   = CONFIG["SYMBOL"]
        leverage = CONFIG["LEVERAGE"]
        size_usd = CONFIG["TRADE_SIZE_USDT"]

        # Thiết lập đòn bẩy
        exchange.set_leverage(leverage, symbol)

        # Tính số lượng hợp đồng dựa trên số USDT muốn đặt
        price      = signal['entry']
        amount_btc = (size_usd * leverage) / price  # Số coin tương đương

        # Đặt lệnh Market Long + SL/TP tích hợp (TP/SL theo giá Mark)
        order = exchange.create_order(
            symbol   = symbol,
            type     = 'market',
            side     = 'buy',
            amount   = round(amount_btc, 4),
            params   = {
                'tdMode'   : 'cross',          # Chế độ ký quỹ chéo
                'tpTriggerPx' : str(signal['take_profit']),
                'tpOrdPx'     : '-1',          # -1 = Market TP
                'slTriggerPx' : str(signal['stop_loss']),
                'slOrdPx'     : '-1',          # -1 = Market SL
            }
        )
        log.info(f"✅ Đặt lệnh thành công! Order ID: {order['id']}")
        return order

    except ccxt.InsufficientFunds as e:
        log.error(f"❌ Không đủ số dư: {e}")
    except ccxt.ExchangeError as e:
        log.error(f"❌ Lỗi từ sàn OKX: {e}")
    except Exception as e:
        log.error(f"❌ Lỗi không xác định khi đặt lệnh: {e}")
    return None


# ─────────────────────────────────────────────────────────────────
# VÒNG LẶP CHÍNH - CHẠY BOT LIÊN TỤC
# ─────────────────────────────────────────────────────────────────
def run_bot():
    """
    Vòng lặp chính của bot.
    Cứ mỗi LOOP_INTERVAL_SEC giây, bot sẽ:
      1. Lấy dữ liệu nến mới từ OKX
      2. Tính toán chỉ báo
      3. Kiểm tra tín hiệu (4 giai đoạn)
      4. Nếu có tín hiệu → Gửi Telegram + Đặt lệnh (nếu LIVE)
    """
    log.info("=" * 60)
    log.info("   TEEN ALGORITHM BOT - KHỞI ĐỘNG")
    log.info(f"   Chế độ   : {'🧪 DRY-RUN (Giả lập)' if CONFIG['DRY_RUN'] else '🚀 LIVE TRADING'}")
    log.info(f"   Symbol   : {CONFIG['SYMBOL']}  |  TF: {CONFIG['TIMEFRAME']}")
    log.info(f"   Đòn bẩy  : x{CONFIG['LEVERAGE']}  |  Vốn/lệnh: ${CONFIG['TRADE_SIZE_USDT']}")
    log.info("=" * 60)

    # Gửi thông báo bot khởi động về Telegram
    send_telegram(
        f"🤖 <b>TEEN ALGORITHM BOT ĐÃ KHỞI ĐỘNG</b>\n"
        f"━━━━━━━━━━━━━━━━━━━━━━\n"
        f"Symbol: <b>{CONFIG['SYMBOL']}</b>\n"
        f"Timeframe: <b>{CONFIG['TIMEFRAME']}</b>\n"
        f"Chế độ: <b>{'DRY-RUN' if CONFIG['DRY_RUN'] else 'LIVE TRADING'}</b>\n"
        f"Bot đang theo dõi thị trường... 👀"
    )

    exchange = create_exchange()

    while True:
        try:
            log.info(f"🔄  Đang quét tín hiệu [{CONFIG['SYMBOL']} - {CONFIG['TIMEFRAME']}]...")

            # Bước 1: Lấy dữ liệu nến từ OKX
            df = fetch_ohlcv(exchange)

            # Bước 2: Tính chỉ báo
            df = compute_indicators(df)

            if len(df) < 5:
                log.warning("Chưa đủ dữ liệu nến để phân tích. Đợi nến tiếp theo...")
                time.sleep(CONFIG["LOOP_INTERVAL_SEC"])
                continue

            # Bước 3: Phát hiện tín hiệu (4 bộ lọc kết hợp)
            signal = detect_signal(df)

            if signal is None:
                log.info("❌ Không có tín hiệu → Bỏ qua, đợi nến tiếp theo.")
            else:
                log.info(f"⚡ PHÁT HIỆN TÍN HIỆU LONG! Entry=${signal['entry']} | SL=${signal['stop_loss']} | TP=${signal['take_profit']}")

                order_result = None

                if CONFIG["DRY_RUN"]:
                    # Chế độ giả lập: Chỉ log và gửi Telegram, KHÔNG vào lệnh thật.
                    log.info("🧪 DRY-RUN: Bỏ qua bước đặt lệnh thật.")
                else:
                    # Chế độ thật: Đặt lệnh lên OKX
                    order_result = place_order(exchange, signal)

                # Bước 4: Thông báo về Telegram
                msg = format_signal_message(signal, order_result)
                send_telegram(msg)

        except ccxt.NetworkError as e:
            log.warning(f"⚠️  Mất kết nối mạng: {e}. Thử lại sau 30 giây...")
            time.sleep(30)

        except Exception as e:
            log.error(f"💥 Lỗi nghiêm trọng không mong đợi: {e}", exc_info=True)
            send_telegram(f"⚠️ <b>TEEN ALGORITHM - LỖI BOT</b>\n<code>{str(e)}</code>")
            time.sleep(60)

        # Đợi đến chu kỳ quét tiếp theo
        log.info(f"⏳ Đợi {CONFIG['LOOP_INTERVAL_SEC']} giây đến lần quét tiếp theo...\n")
        time.sleep(CONFIG["LOOP_INTERVAL_SEC"])


# ─────────────────────────────────────────────────────────────────
# ĐIỂM KHỞI CHẠY
# ─────────────────────────────────────────────────────────────────
if __name__ == "__main__":
    run_bot()
