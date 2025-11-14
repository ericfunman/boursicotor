#!/usr/bin/env python
"""Test import of backtesting_engine"""
import sys

# Clear any cached imports
if 'backend.backtesting_engine' in sys.modules:
    del sys.modules['backend.backtesting_engine']

# Import fresh
from backend.backtesting_engine import StrategyGenerator, BacktestingEngine
print(f"✅ StrategyGenerator imported: {StrategyGenerator}")
print(f"✅ BacktestingEngine imported: {BacktestingEngine}")

# Test instantiation
sg = StrategyGenerator(target_return=0.1)
be = BacktestingEngine(initial_capital=10000)
print(f"✅ Instances created successfully")
print(f"✅ All tests passed!")
