import sqlite3

def init_db():
    conn = sqlite3.connect('trading_bot.db')
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS trade_history (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            symbol TEXT,
            strategy TEXT,
            side TEXT,
            entry_price REAL,
            adx_value REAL,
            result TEXT DEFAULT 'UNKNOWN',
            timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    conn.commit()
    conn.close()

def update_trade_result(symbol, result, pnl):
    conn = sqlite3.connect('trading_bot.db')
    cursor = conn.cursor()
    # Sử dụng Subquery để tìm ID của lệnh UNKNOWN mới nhất của symbol đó
    cursor.execute('''
        UPDATE trade_history 
        SET result = ?, pnl = ?
        WHERE id = (
            SELECT id FROM trade_history 
            WHERE symbol = ? AND result = 'UNKNOWN'
            ORDER BY timestamp DESC LIMIT 1
        )
    ''', (result, pnl, symbol))
    conn.commit()
    conn.close()

def log_trade(symbol, strategy, side, entry_price, adx_value):
    conn = sqlite3.connect('trading_bot.db')
    cursor = conn.cursor()
    cursor.execute('''
        INSERT INTO trade_history (symbol, strategy, side, entry_price, adx_value)
        VALUES (?, ?, ?, ?, ?)
    ''', (symbol, strategy, side, entry_price, adx_value))
    conn.commit()
    conn.close()