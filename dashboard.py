import streamlit as st
import pandas as pd
import sqlite3
import plotly.express as px

st.set_page_config(page_title="Binance Bot Monitor", layout="wide")

def get_data():
    conn = sqlite3.connect('trading_bot.db')
    df = pd.read_sql_query("SELECT * FROM trade_history", conn)
    conn.close()
    df['timestamp'] = pd.to_datetime(df['timestamp'])
    return df

st.title("📊 Binance Trading Bot - Performance Dashboard")

try:
    df = get_data()
    
    if not df.empty:
        # --- 1. TÍNH TOÁN CÁC CHỈ SỐ (METRICS) ---
        total_trades = len(df)
        wins = len(df[df['result'] == 'WIN'])
        losses = len(df[df['result'] == 'LOSS'])
        
        # Công thức tính tỷ lệ thắng: $Win\ Rate = \frac{Wins}{Total\ Trades} \times 100\%$
        win_rate = (wins / total_trades * 100) if total_trades > 0 else 0
        
        # Lợi nhuận gộp: $Total\ PnL = \sum PnL_i$
        total_pnl = df['pnl'].sum() if 'pnl' in df.columns else 0.0

        # --- 2. HIỂN THỊ CHỈ SỐ LÊN TRÊN CÙNG ---
        col1, col2, col3, col4 = st.columns(4)
        
        col1.metric("Tổng số lệnh", total_trades)
        col2.metric("Tỷ lệ thắng", f"{win_rate:.1f}%", delta=f"{wins} Thắng - {losses} Thua")
        
        # Hiển thị màu xanh nếu lãi, màu đỏ nếu lỗ
        pnl_color = "normal" if total_pnl >= 0 else "inverse"
        col3.metric("Tổng lợi nhuận (USDT)", f"{total_pnl:.2f}$", delta_color=pnl_color)
        
        # Giả định vốn ban đầu là 40$ để tính % tăng trưởng
        growth = (total_pnl / 40) * 100
        col4.metric("Tăng trưởng tài khoản", f"{growth:.2f}%")

        # --- 3. BIỂU ĐỒ TĂNG TRƯỞNG LỢI NHUẬN (CUMULATIVE PNL) ---
        st.subheader("📈 Biểu đồ tăng trưởng lợi nhuận")
        
        # Sắp xếp theo thời gian và tính lợi nhuận lũy kế
        df_sorted = df.sort_values('timestamp')
        df_sorted['cumulative_pnl'] = df_sorted['pnl'].cumsum()
        
        fig_line = px.line(df_sorted, x='timestamp', y='cumulative_pnl', 
                          title='Lợi nhuận tích lũy theo thời gian',
                          labels={'cumulative_pnl': 'USDT', 'timestamp': 'Thời gian'})
        st.plotly_chart(fig_line, use_container_width=True)

        

        # --- 4. PHÂN BỔ CHIẾN LƯỢC & NHẬT KÝ ---
        col_left, col_right = st.columns(2)
        
        with col_left:
            st.subheader("🎯 Phân bổ chiến lược")
            fig_pie = px.pie(df, names='strategy', hole=0.4)
            st.plotly_chart(fig_pie, use_container_width=True)

        with col_right:
            st.subheader("📋 Nhật ký 5 lệnh gần nhất")
            st.table(df.sort_values(by='timestamp', ascending=False).head(5)[['symbol', 'strategy', 'result', 'pnl']])

        # --- 5. BẢNG DỮ LIỆU CHI TIẾT ---
        st.subheader("📂 Toàn bộ lịch sử giao dịch")
        st.dataframe(df.sort_values(by='timestamp', ascending=False), use_container_width=True)
        
    else:
        st.info("Chưa có dữ liệu giao dịch. Đang chờ bot thực hiện lệnh đầu tiên...")

except Exception as e:
    st.error(f"Lỗi hiển thị Dashboard: {e}")