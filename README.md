# 🤖 BINANCE SMART TRADING BOT (Futures)
>Hệ thống giao dịch tiền điện tử tự động trên sàn Binance Futures, được tối ưu hóa đặc biệt để bảo vệ nguồn vốn nhỏ (~40 USDT) thông qua quản lý rủi ro dựa trên độ biến động thực tế và bộ lọc xu hướng đa khung thời gian.

## Chiến thuật Giao dịch (Trading Strategy)
>Bot vận hành dựa trên sự kết hợp giữa xu hướng dài hạn và xung lực ngắn hạn để loại bỏ các tín hiệu giả (noise)
1. **Bộ lọc Xu hướng (4H):** Sử dụng đường EMA 200 làm kim chỉ nam. Bot tuyệt đối chỉ mở lệnh thuận theo xu hướng khung lớn: LONG khi giá > EMA 200 và SHORT khi giá < EMA 200.
2. **Điểm kích hoạt (15M):** Tự động chuyển đổi chế độ dựa trên chỉ báo ADX (độ mạnh xu hướng):
    - **TREND Mode (ADX >= 25):** Đánh phá vỡ (Breakout) khi giá vượt dải Bollinger Bands kèm theo sự xác nhận từ dòng tiền thông minh (Open Interest - OI).
    - **GRID Mode (ADX < 20):** Đánh đảo chiều trong vùng tích lũy tại biên Bollinger Bands, nhưng vẫn bắt buộc tuân thủ xu hướng khung 4H để tránh bị quét sóng.

## Quản lý rủi ro (Risk Management)
> Đây là lớp bảo vệ "sống còn" cho tài khoản sau khi rút kinh nghiệm từ chuỗi lệnh thua trước đó:
1. **Hệ số SL (ATR) 2.5:** Điểm dừng lỗ được tính động bằng **2.5 x ATR**. Khoảng cách này đủ xa để sống sót qua các cú quét râu nến (wicks) thường thấy trên sàn.
2. **Tỷ lệ R:R mục tiêu:** Chốt lời (TP) được đặt ở mức **4.0 x ATR** cho lệnh Trend, tạo ra tỷ lệ lợi nhuận/rủi ro tối ưu.
3. **Khoảng nghỉ (Cool-down):** Tự động tạm dừng giao dịch 1 giờ trên mỗi cặp tiền sau khi đóng lệnh để ngăn chặn tâm lý giao dịch trả thù (Revenge trading).
4. **Dọn dẹp lệnh rác:** Tự động hủy toàn bộ các lệnh TP/SL thừa ngay khi vị thế chính đã đóng.

## Cấu hình Môi trường (Environment Setup)
> Bot đã được cập nhật để tương thích với hệ thống Binance Demo Trading mới nhất:
- *Endpoint:* ``https://demo-fapi.binance.com/fapi/v1``
- *API Setup:* Cần tạo mã tại trang Demo Trading và cấp quyền "Enable Futures".

## Hướng dẫn khởi động
1. **Cài đặt thư viện:**
`pip install ccxt pandas pandas_ta streamlit plotly`
2. **Cấu hình API:** Cập nhật ``apiKey`` và ``secret`` vào file ``module/config.py``.
3. **Chạy Bot:**
``python main.py``
4. **Xem Dashboard:**
``streamlit run dashboard.py``