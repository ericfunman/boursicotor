-- Boursicotor Database Schema
-- PostgreSQL

-- Tickers table
CREATE TABLE IF NOT EXISTS tickers (
    id SERIAL PRIMARY KEY,
    symbol VARCHAR(10) UNIQUE NOT NULL,
    name VARCHAR(100) NOT NULL,
    exchange VARCHAR(50) DEFAULT 'EURONEXT',
    currency VARCHAR(3) DEFAULT 'EUR',
    sector VARCHAR(100),
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_tickers_symbol ON tickers(symbol);

-- Historical data table
CREATE TABLE IF NOT EXISTS historical_data (
    id SERIAL PRIMARY KEY,
    ticker_id INTEGER NOT NULL REFERENCES tickers(id) ON DELETE CASCADE,
    timestamp TIMESTAMP NOT NULL,
    open FLOAT NOT NULL,
    high FLOAT NOT NULL,
    low FLOAT NOT NULL,
    close FLOAT NOT NULL,
    volume INTEGER NOT NULL,
    interval VARCHAR(10) DEFAULT '1min',
    
    -- Technical indicators
    sma_20 FLOAT,
    sma_50 FLOAT,
    ema_12 FLOAT,
    ema_26 FLOAT,
    rsi_14 FLOAT,
    macd FLOAT,
    macd_signal FLOAT,
    macd_hist FLOAT,
    bb_upper FLOAT,
    bb_middle FLOAT,
    bb_lower FLOAT,
    
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_historical_ticker ON historical_data(ticker_id);
CREATE INDEX idx_historical_timestamp ON historical_data(timestamp);
CREATE INDEX idx_historical_ticker_timestamp ON historical_data(ticker_id, timestamp);
CREATE INDEX idx_historical_ticker_interval_timestamp ON historical_data(ticker_id, interval, timestamp);

-- Unique constraint to prevent duplicate data
CREATE UNIQUE INDEX idx_unique_historical_data ON historical_data(ticker_id, timestamp, interval);

-- Strategies table
CREATE TABLE IF NOT EXISTS strategies (
    id SERIAL PRIMARY KEY,
    name VARCHAR(100) UNIQUE NOT NULL,
    description TEXT,
    strategy_type VARCHAR(50),
    parameters TEXT,  -- JSON
    is_active BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_strategies_name ON strategies(name);

-- Backtests table
CREATE TABLE IF NOT EXISTS backtests (
    id SERIAL PRIMARY KEY,
    strategy_id INTEGER NOT NULL REFERENCES strategies(id) ON DELETE CASCADE,
    ticker_id INTEGER NOT NULL REFERENCES tickers(id) ON DELETE CASCADE,
    start_date TIMESTAMP NOT NULL,
    end_date TIMESTAMP NOT NULL,
    initial_capital FLOAT NOT NULL,
    final_capital FLOAT NOT NULL,
    total_return FLOAT,
    sharpe_ratio FLOAT,
    max_drawdown FLOAT,
    win_rate FLOAT,
    total_trades INTEGER,
    winning_trades INTEGER,
    losing_trades INTEGER,
    avg_win FLOAT,
    avg_loss FLOAT,
    profit_factor FLOAT,
    results_json TEXT,  -- Detailed results as JSON
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_backtests_strategy ON backtests(strategy_id);
CREATE INDEX idx_backtests_ticker ON backtests(ticker_id);

-- Trades table
CREATE TABLE IF NOT EXISTS trades (
    id SERIAL PRIMARY KEY,
    ticker_id INTEGER NOT NULL REFERENCES tickers(id) ON DELETE CASCADE,
    strategy_id INTEGER REFERENCES strategies(id) ON DELETE SET NULL,
    order_type VARCHAR(10) NOT NULL,  -- BUY, SELL
    quantity INTEGER NOT NULL,
    entry_price FLOAT NOT NULL,
    exit_price FLOAT,
    stop_loss FLOAT,
    take_profit FLOAT,
    entry_time TIMESTAMP NOT NULL,
    exit_time TIMESTAMP,
    pnl FLOAT,
    pnl_percent FLOAT,
    status VARCHAR(20) DEFAULT 'OPEN',  -- OPEN, CLOSED, CANCELLED
    is_paper_trade BOOLEAN DEFAULT TRUE,
    commission FLOAT DEFAULT 0.0,
    notes TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_trades_ticker ON trades(ticker_id);
CREATE INDEX idx_trades_strategy ON trades(strategy_id);
CREATE INDEX idx_trades_entry_time ON trades(entry_time);
CREATE INDEX idx_trades_status ON trades(status);

-- ML Models table
CREATE TABLE IF NOT EXISTS ml_models (
    id SERIAL PRIMARY KEY,
    name VARCHAR(100) NOT NULL,
    model_type VARCHAR(50) NOT NULL,
    version VARCHAR(20) NOT NULL,
    file_path VARCHAR(255) NOT NULL,
    training_start_date TIMESTAMP,
    training_end_date TIMESTAMP,
    accuracy FLOAT,
    precision_score FLOAT,
    recall FLOAT,
    f1_score FLOAT,
    parameters TEXT,  -- JSON
    feature_importance TEXT,  -- JSON
    is_active BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    trained_at TIMESTAMP
);

CREATE INDEX idx_ml_models_name ON ml_models(name);
CREATE INDEX idx_ml_models_type ON ml_models(model_type);

-- Insert some default strategies
INSERT INTO strategies (name, description, strategy_type, is_active) VALUES
    ('RSI Momentum', 'Simple RSI-based momentum strategy', 'momentum', FALSE),
    ('MA Crossover', 'Moving average crossover strategy', 'trend_following', FALSE),
    ('MACD Signal', 'MACD signal line crossover', 'momentum', FALSE),
    ('Bollinger Bands', 'Mean reversion using Bollinger Bands', 'mean_reversion', FALSE),
    ('Multi-Indicator', 'Combined signal from multiple indicators', 'hybrid', FALSE)
ON CONFLICT (name) DO NOTHING;

-- Views for quick access

-- Active positions view
CREATE OR REPLACE VIEW active_positions AS
SELECT 
    t.id,
    tk.symbol,
    tk.name,
    t.order_type,
    t.quantity,
    t.entry_price,
    t.entry_time,
    t.stop_loss,
    t.take_profit,
    s.name as strategy_name,
    t.is_paper_trade
FROM trades t
JOIN tickers tk ON t.ticker_id = tk.id
LEFT JOIN strategies s ON t.strategy_id = s.id
WHERE t.status = 'OPEN'
ORDER BY t.entry_time DESC;

-- Performance summary view
CREATE OR REPLACE VIEW performance_summary AS
SELECT 
    tk.symbol,
    COUNT(*) as total_trades,
    SUM(CASE WHEN t.pnl > 0 THEN 1 ELSE 0 END) as winning_trades,
    SUM(CASE WHEN t.pnl <= 0 THEN 1 ELSE 0 END) as losing_trades,
    ROUND(AVG(CASE WHEN t.pnl > 0 THEN t.pnl ELSE NULL END)::numeric, 2) as avg_win,
    ROUND(AVG(CASE WHEN t.pnl <= 0 THEN t.pnl ELSE NULL END)::numeric, 2) as avg_loss,
    ROUND(SUM(t.pnl)::numeric, 2) as total_pnl,
    ROUND((SUM(CASE WHEN t.pnl > 0 THEN 1 ELSE 0 END)::float / COUNT(*)::float * 100)::numeric, 2) as win_rate
FROM trades t
JOIN tickers tk ON t.ticker_id = tk.id
WHERE t.status = 'CLOSED'
GROUP BY tk.symbol;
