"""
Test du collecteur Yahoo Finance
"""
import sys
from pathlib import Path
sys.path.append(str(Path(__file__).parent))

from backend.yahoo_finance_collector import demo_yahoo_finance

if __name__ == "__main__":
    demo_yahoo_finance()
