"""
Example scripts for common tasks in Boursicotor
"""
import sys
from pathlib import Path
sys.path.append(str(Path(__file__).parent.parent))

from backend.data_collector import DataCollector
from backend.technical_indicators import calculate_and_update_indicators
from backtesting.engine import BacktestEngine, BacktestConfig
from strategies.base_strategies import get_strategy
from ml_models.pattern_detector import MLPatternDetector
import pandas as pd


def example_1_collect_data():
    """Example 1: Collect historical data for a ticker"""
    print("=" * 50)
    print("Example 1: Collecting Historical Data")
    print("=" * 50)
    
    collector = DataCollector()
    
    # Collect 1 week of 5-minute data for TotalEnergies
    count = collector.collect_historical_data(
        symbol="TTE",
        name="TotalEnergies",
        duration="1 W",
        bar_size="5 mins"
    )
    
    print(f"✅ Collected {count} records for TTE")
    
    # Get latest data
    df = collector.get_latest_data("TTE", limit=20)
    print("\nLatest 5 records:")
    print(df.tail(5))


def example_2_technical_analysis():
    """Example 2: Calculate technical indicators"""
    print("=" * 50)
    print("Example 2: Technical Analysis")
    print("=" * 50)
    
    collector = DataCollector()
    df = collector.get_latest_data("TTE", limit=500)
    
    if df.empty:
        print("⚠️ No data available. Run example_1_collect_data first.")
        return
    
    # Calculate all indicators
    df = calculate_and_update_indicators(df)
    
    print(f"Total indicators calculated: {len(df.columns)}")
    print("\nAvailable indicators:")
    print([col for col in df.columns if col not in ['open', 'high', 'low', 'close', 'volume']])
    
    print("\nLatest indicator values:")
    indicators_to_show = ['close', 'rsi_14', 'macd', 'sma_20', 'sma_50', 'bb_upper', 'bb_lower']
    available_indicators = [col for col in indicators_to_show if col in df.columns]
    print(df[available_indicators].tail(1))


def example_3_simple_backtest():
    """Example 3: Run a simple backtest"""
    print("=" * 50)
    print("Example 3: Simple Backtesting")
    print("=" * 50)
    
    collector = DataCollector()
    df = collector.get_latest_data("TTE", limit=1000)
    
    if df.empty:
        print("⚠️ No data available. Run example_1_collect_data first.")
        return
    
    # Calculate indicators
    df = calculate_and_update_indicators(df)
    
    # Get RSI momentum strategy
    strategy = get_strategy('momentum', rsi_oversold=30, rsi_overbought=70)
    
    # Configure backtest
    config = BacktestConfig(
        initial_capital=10000.0,
        commission=0.001,
        risk_per_trade=0.02
    )
    
    # Run backtest
    engine = BacktestEngine(config)
    results = engine.run_backtest(
        df=df,
        strategy_func=strategy.generate_signal,
        symbol="TTE"
    )
    
    # Display results
    print("\n📊 Backtest Results:")
    print(f"Initial Capital: {results['initial_capital']:.2f} €")
    print(f"Final Capital: {results['final_capital']:.2f} €")
    print(f"Total Return: {results['total_return']:.2f}%")
    print(f"Total Trades: {results['total_trades']}")
    print(f"Win Rate: {results['win_rate']:.2f}%")
    print(f"Sharpe Ratio: {results['sharpe_ratio']:.2f}")
    print(f"Max Drawdown: {results['max_drawdown']:.2f}%")
    print(f"Profit Factor: {results['profit_factor']:.2f}")


def example_4_compare_strategies():
    """Example 4: Compare multiple strategies"""
    print("=" * 50)
    print("Example 4: Comparing Multiple Strategies")
    print("=" * 50)
    
    collector = DataCollector()
    df = collector.get_latest_data("TTE", limit=1000)
    
    if df.empty:
        print("⚠️ No data available. Run example_1_collect_data first.")
        return
    
    df = calculate_and_update_indicators(df)
    
    strategies_to_test = [
        ('momentum', {}),
        ('ma_crossover', {'fast_period': 20, 'slow_period': 50}),
        ('macd', {}),
        ('bollinger_bands', {}),
    ]
    
    config = BacktestConfig(initial_capital=10000.0)
    results_comparison = []
    
    for strategy_name, params in strategies_to_test:
        strategy = get_strategy(strategy_name, **params)
        engine = BacktestEngine(config)
        results = engine.run_backtest(df, strategy.generate_signal, "TTE")
        
        results_comparison.append({
            'Strategy': strategy_name,
            'Return (%)': results['total_return'],
            'Trades': results['total_trades'],
            'Win Rate (%)': results['win_rate'],
            'Sharpe': results['sharpe_ratio'],
            'Max DD (%)': results['max_drawdown']
        })
    
    # Display comparison
    comparison_df = pd.DataFrame(results_comparison)
    print("\n📊 Strategy Comparison:")
    print(comparison_df.to_string(index=False))
    
    # Find best strategy
    best = comparison_df.loc[comparison_df['Return (%)'].idxmax()]
    print(f"\n🏆 Best Strategy: {best['Strategy']} with {best['Return (%)']}% return")


def example_5_train_ml_model():
    """Example 5: Train a machine learning model"""
    print("=" * 50)
    print("Example 5: Training ML Model")
    print("=" * 50)
    
    collector = DataCollector()
    df = collector.get_latest_data("TTE", limit=3000)
    
    if df.empty or len(df) < 500:
        print("⚠️ Insufficient data. Collect at least 500 records first.")
        return
    
    # Calculate indicators
    df = calculate_and_update_indicators(df)
    
    # Train Random Forest model
    print("\n🤖 Training Random Forest model...")
    detector = MLPatternDetector(model_type="random_forest")
    
    try:
        results = detector.train(
            df=df,
            forward_periods=10,  # Predict 10 periods ahead
            threshold=0.02,      # 2% gain threshold
            test_size=0.2
        )
        
        print("\n📊 Training Results:")
        print(f"Model Type: {results['model_type']}")
        print(f"Training Accuracy: {results['train_accuracy']:.3f}")
        print(f"Test Accuracy: {results['test_accuracy']:.3f}")
        print(f"Precision: {results['precision']:.3f}")
        print(f"Recall: {results['recall']:.3f}")
        print(f"F1 Score: {results['f1_score']:.3f}")
        
        if 'feature_importance' in results:
            print("\n🔝 Top 5 Most Important Features:")
            for i, feat in enumerate(results['feature_importance'][:5], 1):
                print(f"{i}. {feat['feature']}: {feat['importance']:.4f}")
        
        # Save model
        detector.save("tte_model_example.pkl")
        print("\n✅ Model saved to ml_models/trained/tte_model_example.pkl")
        
    except Exception as e:
        print(f"❌ Error training model: {e}")


def example_6_use_ml_predictions():
    """Example 6: Use ML model for predictions"""
    print("=" * 50)
    print("Example 6: Using ML Predictions")
    print("=" * 50)
    
    try:
        # Load model
        detector = MLPatternDetector()
        detector.load("tte_model_example.pkl")
        print("✅ Model loaded successfully")
        
        # Get recent data
        collector = DataCollector()
        df = collector.get_latest_data("TTE", limit=100)
        df = calculate_and_update_indicators(df)
        
        # Make predictions
        predictions = detector.predict(df)
        probabilities = detector.predict_proba(df)
        
        print(f"\n📈 Predictions for last 10 periods:")
        for i in range(max(0, len(predictions)-10), len(predictions)):
            pred = "BUY" if predictions[i] == 1 else "HOLD"
            prob = probabilities[i][1] * 100  # Probability of positive class
            timestamp = df.index[i]
            print(f"{timestamp}: {pred} (confidence: {prob:.1f}%)")
        
    except FileNotFoundError:
        print("⚠️ Model not found. Run example_5_train_ml_model first.")
    except Exception as e:
        print(f"❌ Error: {e}")


def example_7_collect_multiple_tickers():
    """Example 7: Collect data for multiple tickers"""
    print("=" * 50)
    print("Example 7: Collecting Multiple Tickers")
    print("=" * 50)
    
    tickers = [
        ("TTE", "TotalEnergies"),
        ("WLN", "Worldline"),
        ("MC", "LVMH"),
    ]
    
    collector = DataCollector()
    collector.collect_multiple_tickers(
        tickers=tickers,
        duration="5 D",
        bar_size="5 mins"
    )
    
    print("\n✅ Data collection completed for all tickers")
    
    # Show summary
    for symbol, name in tickers:
        df = collector.get_latest_data(symbol, limit=10)
        print(f"{symbol}: {len(df)} records available")


def main():
    """Run all examples"""
    print("\n🚀 Boursicotor - Example Scripts")
    print("=" * 50)
    
    examples = [
        ("1", "Collect Historical Data", example_1_collect_data),
        ("2", "Technical Analysis", example_2_technical_analysis),
        ("3", "Simple Backtest", example_3_simple_backtest),
        ("4", "Compare Strategies", example_4_compare_strategies),
        ("5", "Train ML Model", example_5_train_ml_model),
        ("6", "Use ML Predictions", example_6_use_ml_predictions),
        ("7", "Collect Multiple Tickers", example_7_collect_multiple_tickers),
    ]
    
    print("\nAvailable Examples:")
    for num, title, _ in examples:
        print(f"  {num}. {title}")
    print("  0. Run all examples")
    print()
    
    choice = input("Select example to run (0-7): ").strip()
    
    if choice == "0":
        for _, title, func in examples:
            print(f"\n{'='*50}")
            print(f"Running: {title}")
            print('='*50)
            try:
                func()
            except Exception as e:
                print(f"❌ Error: {e}")
            print()
    else:
        for num, title, func in examples:
            if choice == num:
                func()
                break
        else:
            print("Invalid choice!")


if __name__ == "__main__":
    main()
