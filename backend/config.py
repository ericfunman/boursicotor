"""
Configuration management for Boursicotor
"""
import os
from pathlib import Path
from dotenv import load_dotenv
from loguru import logger

# Load environment variables
load_dotenv()

# Base paths
BASE_DIR = Path(__file__).parent.parent
LOGS_DIR = BASE_DIR / "logs"
DATA_DIR = BASE_DIR / "data"
MODELS_DIR = BASE_DIR / "ml_models" / "trained"

# Create directories if they don't exist
LOGS_DIR.mkdir(exist_ok=True)
DATA_DIR.mkdir(exist_ok=True)
MODELS_DIR.mkdir(exist_ok=True)

# Database Configuration
DB_TYPE = os.getenv("DB_TYPE", "postgresql")

if DB_TYPE == "sqlite":
    DATABASE_URL = f"sqlite:///{BASE_DIR / os.getenv('DB_NAME', 'boursicotor.db')}"
else:
    DB_CONFIG = {
        "host": os.getenv("DB_HOST", "localhost"),
        "port": int(os.getenv("DB_PORT", 5432)),
        "database": os.getenv("DB_NAME", "boursicotor"),
        "user": os.getenv("DB_USER", "postgres"),
        "password": os.getenv("DB_PASSWORD", ""),
    }
    DATABASE_URL = f"postgresql://{DB_CONFIG['user']}:{DB_CONFIG['password']}@{DB_CONFIG['host']}:{DB_CONFIG['port']}/{DB_CONFIG['database']}?client_encoding=utf8"

# Interactive Brokers Configuration
IBKR_CONFIG = {
    "host": os.getenv("IBKR_HOST", "127.0.0.1"),
    "port": int(os.getenv("IBKR_PORT", 7497)),
    "client_id": int(os.getenv("IBKR_CLIENT_ID", 1)),
    "account": os.getenv("IBKR_ACCOUNT", ""),
}

# Trading Configuration
TRADING_CONFIG = {
    "paper_trading": os.getenv("PAPER_TRADING", "True").lower() == "true",
    "max_position_size": float(os.getenv("MAX_POSITION_SIZE", 10000)),
    "risk_per_trade": float(os.getenv("RISK_PER_TRADE", 0.02)),
    "stop_loss_percent": float(os.getenv("STOP_LOSS_PERCENT", 0.05)),
}

# Data Collection Configuration
DATA_CONFIG = {
    "default_interval": os.getenv("DEFAULT_INTERVAL", "1min"),
    "retention_days": int(os.getenv("DATA_RETENTION_DAYS", 365)),
}

# ML Configuration
ML_CONFIG = {
    "retrain_interval_days": int(os.getenv("MODEL_RETRAIN_INTERVAL", 7)),
    "confidence_threshold": float(os.getenv("CONFIDENCE_THRESHOLD", 0.75)),
}

# Logging Configuration
LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")
LOG_FILE = LOGS_DIR / os.getenv("LOG_FILE", "boursicotor.log")

# Configure logger
logger.add(
    LOG_FILE,
    rotation="1 day",
    retention="30 days",
    level=LOG_LEVEL,
    format="{time:YYYY-MM-DD HH:mm:ss} | {level} | {name}:{function}:{line} | {message}"
)

# API Configuration
API_CONFIG = {
    "host": os.getenv("API_HOST", "0.0.0.0"),
    "port": int(os.getenv("API_PORT", 8000)),
}

# Supported intervals for data collection
SUPPORTED_INTERVALS = [
    "1sec", "5secs", "10secs", "15secs", "30secs",
    "1min", "2mins", "3mins", "5mins", "10mins", "15mins", "30mins",
    "1hour", "2hours", "4hours",
    "1day", "1week", "1month"
]

# French market tickers (examples)
FRENCH_TICKERS = {
    "TTE": "TotalEnergies",
    "WLN": "Worldline",
    "MC": "LVMH",
    "OR": "L'Oréal",
    "AIR": "Airbus",
    "SAN": "Sanofi",
    "BNP": "BNP Paribas",
    "SU": "Schneider Electric",
}

logger.info("Configuration loaded successfully")
