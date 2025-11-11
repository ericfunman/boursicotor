"""
Strategy Manager - Gestion des stratégies de trading
"""
import json
import sqlite3
from typing import List, Optional, Dict
from datetime import datetime
from sqlalchemy import text

from backend.config import logger
from backend.models import SessionLocal, Strategy as StrategyModel, Backtest as BacktestModel, Ticker
from backend.backtesting_engine import (
    Strategy, BacktestResult, BacktestingEngine,
    MovingAverageCrossover, RSIStrategy, MultiIndicatorStrategy,
    AdvancedMultiIndicatorStrategy, MomentumBreakoutStrategy, MeanReversionStrategy,
    UltraAggressiveStrategy, MegaIndicatorStrategy, HyperAggressiveStrategy, UltimateStrategy,
    EnhancedMovingAverageStrategy, AdvancedIndicators
)


class StrategyManager:
    """Gestionnaire de stratégies"""
    
    @staticmethod
    @staticmethod
    def _convert_numpy_types(obj):
        """Convert numpy types to Python native types"""
        import numpy as np
        if isinstance(obj, dict):
            return {k: StrategyManager._convert_numpy_types(v) for k, v in obj.items()}
        elif isinstance(obj, (list, tuple)):
            return [StrategyManager._convert_numpy_types(item) for item in obj]
        elif isinstance(obj, (np.integer, np.int64, np.int32, np.int16, np.int8)):
            return int(obj)
        elif isinstance(obj, (np.floating, np.float64, np.float32, np.float16)):
            return float(obj)
        elif isinstance(obj, np.ndarray):
            return obj.tolist()
        elif isinstance(obj, np.bool_):
            return bool(obj)
        else:
            return obj
    
    @staticmethod
    def _get_strategy_type(strategy: Strategy) -> str:
        """Determine strategy type from class name"""
        strategy_type = strategy.__class__.__name__
        type_map = {
            "MovingAverageCrossover": "MA",
            "RSIStrategy": "RSI",
            "MultiIndicatorStrategy": "Multi",
            "EnhancedMovingAverageStrategy": "EnhancedMA"
        }
        return type_map.get(strategy_type, strategy_type)
    
    @staticmethod
    def _create_strategy_model(strategy: Strategy, backtest_result: BacktestResult) -> StrategyModel:
        """Create a new strategy database model"""
        strategy_type = StrategyManager._get_strategy_type(strategy)
        logger.info(f"Creating new strategy with type: {strategy_type}")
        
        clean_parameters = StrategyManager._convert_numpy_types(strategy.parameters)
        
        # Use custom description if provided, otherwise create default one
        description = strategy.description if hasattr(strategy, 'description') and strategy.description else f"Strategy with {backtest_result.total_return:.2f}% return on {backtest_result.symbol}"
        
        return StrategyModel(
            name=strategy.name,
            description=description,
            strategy_type=strategy_type,
            parameters=json.dumps(clean_parameters),
            is_active=True
        )
    
    @staticmethod
    def save_strategy(strategy: Strategy, backtest_result: BacktestResult) -> Optional[int]:
        """
        Sauvegarde une stratégie et son résultat de backtest
        
        Args:
            strategy: Stratégie à sauvegarder
            backtest_result: Résultat du backtest
            
        Returns:
            ID de la stratégie sauvegardée
        """
        logger.info(f"Saving strategy: {strategy.name}")
        logger.info(f"Strategy type: {strategy.__class__.__name__}")
        logger.info(f"Backtest symbol: {backtest_result.symbol}")
        
        db = SessionLocal()
        try:
            # Check if strategy already exists
            existing = db.query(StrategyModel).filter(
                StrategyModel.name == strategy.name
            ).first()
            
            if existing:
                logger.info(f"Strategy {strategy.name} already exists, updating...")
                strategy_db = existing
            else:
                strategy_db = StrategyManager._create_strategy_model(strategy, backtest_result)
                db.add(strategy_db)
                db.flush()  # Get the ID
                logger.info(f"Strategy created with ID: {strategy_db.id}, name: {strategy.name}")
            
            # Get ticker - remove .PA suffix if present
            ticker_symbol = backtest_result.symbol.replace('.PA', '')
            logger.info(f"Looking for ticker: {ticker_symbol} (original: {backtest_result.symbol})")
            
            ticker = db.query(Ticker).filter(Ticker.symbol == ticker_symbol).first()
            if not ticker:
                logger.error(f"Ticker {ticker_symbol} not found (original: {backtest_result.symbol})")
                # List available tickers
                available_tickers = db.query(Ticker).all()
                logger.error(f"Available tickers: {[t.symbol for t in available_tickers]}")
                return None
            
            # Save backtest result
            backtest_db = BacktestModel(
                strategy_id=strategy_db.id,
                ticker_id=ticker.id,
                start_date=backtest_result.start_date,
                end_date=backtest_result.end_date,
                initial_capital=backtest_result.initial_capital,
                final_capital=backtest_result.final_capital,
                total_return=backtest_result.total_return,
                sharpe_ratio=backtest_result.sharpe_ratio,
                max_drawdown=backtest_result.max_drawdown,
                win_rate=backtest_result.win_rate,
                total_trades=backtest_result.total_trades,
                winning_trades=backtest_result.winning_trades,
                losing_trades=backtest_result.losing_trades,
                results_json=json.dumps(backtest_result.to_dict())
            )
            db.add(backtest_db)
            
            db.commit()
            
            logger.info(f"✅ Strategy saved: {strategy.name} (ID: {strategy_db.id})")
            return strategy_db.id
            
        except Exception as e:
            db.rollback()
            logger.error(f"Error saving strategy: {e}")
            return None
        finally:
            db.close()
    
    @staticmethod
    def _instantiate_strategy(strategy_type: str, parameters: dict) -> Optional[Strategy]:
        """Instantiate strategy object based on type"""
        strategy_map = {
            'MovingAverageCrossover': MovingAverageCrossover,
            'MA': MovingAverageCrossover,
            'RSIStrategy': RSIStrategy,
            'RSI': RSIStrategy,
            'MultiIndicatorStrategy': MultiIndicatorStrategy,
            'Multi': MultiIndicatorStrategy,
            'AdvancedMultiIndicatorStrategy': AdvancedMultiIndicatorStrategy,
            'MomentumBreakoutStrategy': MomentumBreakoutStrategy,
            'MeanReversionStrategy': MeanReversionStrategy,
            'UltraAggressiveStrategy': UltraAggressiveStrategy,
            'MegaIndicatorStrategy': MegaIndicatorStrategy,
            'HyperAggressiveStrategy': HyperAggressiveStrategy,
            'UltimateStrategy': UltimateStrategy,
            'EnhancedMA': EnhancedMovingAverageStrategy
        }
        
        strategy_class = strategy_map.get(strategy_type)
        if not strategy_class:
            logger.error(f"Unknown strategy type: {strategy_type}")
            return None
        
        return strategy_class(**parameters)
    
    @staticmethod
    def load_strategy(strategy_id: int) -> Optional[Strategy]:
        """
        Charge une stratégie depuis la base de données
        
        Args:
            strategy_id: ID de la stratégie
            
        Returns:
            Strategy object ou None
        """
        db = SessionLocal()
        try:
            strategy_db = db.query(StrategyModel).filter(StrategyModel.id == strategy_id).first()
            
            if not strategy_db:
                logger.error(f"Strategy {strategy_id} not found")
                return None
            
            # Reconstruct strategy object
            parameters = json.loads(strategy_db.parameters)
            strategy_type = strategy_db.strategy_type
            
            # Create strategy based on type
            strategy = StrategyManager._instantiate_strategy(strategy_type, parameters)
            
            if strategy:
                logger.info(f"✅ Strategy loaded: {strategy.name}")
            
            return strategy
            
        except Exception as e:
            logger.error(f"Error loading strategy: {e}")
            return None
        finally:
            db.close()
    
    @staticmethod
    def get_strategy_by_id(strategy_id: int):
        """
        Récupère une stratégie par son ID
        
        Args:
            strategy_id: ID de la stratégie
            
        Returns:
            Objet stratégie ou None si non trouvée
        """
        db = SessionLocal()
        try:
            strategy_db = db.query(StrategyModel).filter(StrategyModel.id == strategy_id).first()
            if strategy_db:
                # Convert to strategy object
                parameters = json.loads(strategy_db.parameters)
                
                # Map strategy type back to class
                if strategy_db.strategy_type == 'MA':
                    strategy = MovingAverageCrossover(**parameters)
                elif strategy_db.strategy_type == 'RSI':
                    strategy = RSIStrategy(**parameters)
                elif strategy_db.strategy_type == 'Multi':
                    strategy = MultiIndicatorStrategy(**parameters)
                elif strategy_db.strategy_type == 'EnhancedMA':
                    strategy = EnhancedMovingAverageStrategy(**parameters)
                elif strategy_db.strategy_type == 'HyperAggressive':
                    strategy = HyperAggressiveStrategy(**parameters)
                elif strategy_db.strategy_type == 'Ultimate':
                    strategy = UltimateStrategy(**parameters)
                else:
                    logger.error(f"Unknown strategy type: {strategy_db.strategy_type}")
                    return None
                
                # Set name and description from database
                strategy.name = strategy_db.name
                strategy.description = strategy_db.description
                
                return strategy
            else:
                logger.error(f"Strategy with ID {strategy_id} not found")
                return None
                
        except Exception as e:
            logger.error(f"Error getting strategy by ID: {e}")
            return None
        finally:
            db.close()
    
    @staticmethod
    def get_all_strategies() -> List[Dict]:
        """
        Récupère toutes les stratégies
        
        Returns:
            Liste des stratégies avec leurs statistiques
        """
        # Use direct SQL to avoid ORM object tracking issues
        import os
        db_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'boursicotor.db')
        
        try:
            conn = sqlite3.connect(db_path)
            conn.row_factory = sqlite3.Row  # Enable column access by name
            cursor = conn.cursor()
            
            # Get all strategies
            cursor.execute("""
                SELECT id, name, description, strategy_type, parameters, is_active, created_at
                FROM strategies
                ORDER BY created_at DESC
            """)
            
            strategies = cursor.fetchall()
            result = []
            
            for s in strategies:
                # Get latest backtest
                cursor.execute("""
                    SELECT total_return, win_rate
                    FROM backtests
                    WHERE strategy_id = ?
                    ORDER BY created_at DESC
                    LIMIT 1
                """, (s['id'],))
                latest = cursor.fetchone()
                
                # Get total backtests count
                cursor.execute("""
                    SELECT COUNT(*) as count
                    FROM backtests
                    WHERE strategy_id = ?
                """, (s['id'],))
                count_row = cursor.fetchone()
                
                result.append({
                    'id': s['id'],
                    'name': s['name'],
                    'description': s['description'],
                    'type': s['strategy_type'],
                    'is_active': bool(s['is_active']),
                    'parameters': json.loads(s['parameters']) if s['parameters'] else {},
                    'latest_return': latest['total_return'] if latest else None,
                    'latest_win_rate': latest['win_rate'] if latest else None,
                    'total_backtests': count_row['count'] if count_row else 0,
                    'created_at': s['created_at']
                })
            
            conn.close()
            return result
            
        except Exception as e:
            logger.error(f"Error getting strategies: {e}")
            return []
    
    @staticmethod
    def get_strategy_backtests(strategy_id: int) -> List[Dict]:
        """
        Récupère tous les backtests d'une stratégie
        
        Args:
            strategy_id: ID de la stratégie
            
        Returns:
            Liste des backtests
        """
        db = SessionLocal()
        try:
            backtests = db.query(BacktestModel).filter(
                BacktestModel.strategy_id == strategy_id
            ).order_by(BacktestModel.created_at.desc()).all()
            
            result = []
            for b in backtests:
                ticker = db.query(Ticker).filter(Ticker.id == b.ticker_id).first()
                
                result.append({
                    'id': b.id,
                    'symbol': ticker.symbol if ticker else 'Unknown',
                    'start_date': b.start_date,
                    'end_date': b.end_date,
                    'initial_capital': b.initial_capital,
                    'final_capital': b.final_capital,
                    'total_return': b.total_return,
                    'sharpe_ratio': b.sharpe_ratio,
                    'max_drawdown': b.max_drawdown,
                    'win_rate': b.win_rate,
                    'total_trades': b.total_trades,
                    'created_at': b.created_at
                })
            
            return result
            
        except Exception as e:
            logger.error(f"Error getting backtests: {e}")
            return []
        finally:
            db.close()
    
    @staticmethod
    def delete_strategy(strategy_id: int) -> bool:
        """
        Supprime une stratégie et tous ses backtests associés
        
        Args:
            strategy_id: ID de la stratégie à supprimer
            
        Returns:
            True si suppression réussie, False sinon
        """
        # Use subprocess to run standalone script to avoid SQLAlchemy interference
        import subprocess
        import sys
        import os
        
        script_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'delete_strategy_standalone.py')
        python_exe = sys.executable
        
        try:
            result = subprocess.run(
                [python_exe, script_path, str(strategy_id)],
                capture_output=True,
                text=True,
                timeout=5
            )
            
            output = result.stdout.strip()
            
            if result.returncode == 0 and output.startswith("SUCCESS:"):
                logger.info(f"✅ {output.split('SUCCESS:')[1]}")
                return True
            else:
                error_msg = output.split('ERROR:')[1] if 'ERROR:' in output else output
                logger.error(f"Failed to delete strategy: {error_msg}")
                return False
                
        except subprocess.TimeoutExpired:
            logger.error(f"Timeout while deleting strategy {strategy_id}")
            return False
        except Exception as e:
            logger.error(f"Error deleting strategy {strategy_id}: {e}")
            return False
    
    @staticmethod
    def replay_strategy(
        strategy_id: int,
        symbol: str,
        start_date: datetime,
        end_date: datetime,
        initial_capital: float = 10000.0
    ) -> Optional[BacktestResult]:
        """
        Rejoue une stratégie sur de nouvelles données
        
        Args:
            strategy_id: ID de la stratégie
            symbol: Symbole du ticker
            start_date: Date de début
            end_date: Date de fin
            initial_capital: Capital initial
            
        Returns:
            Résultat du backtest
        """
        logger.info(f"🔄 Replaying strategy {strategy_id} on {symbol}")
        
        # Load strategy
        strategy = StrategyManager.load_strategy(strategy_id)
        if not strategy:
            return None
        
        # Get data
        db = SessionLocal()
        try:
            from backend.models import HistoricalData
            import pandas as pd
            
            # Remove .PA suffix if present
            ticker_symbol = symbol.replace('.PA', '')
            ticker = db.query(Ticker).filter(Ticker.symbol == ticker_symbol).first()
            if not ticker:
                logger.error(f"Ticker {ticker_symbol} not found (original: {symbol})")
                return None
            
            # Query data
            data = db.query(HistoricalData).filter(
                HistoricalData.ticker_id == ticker.id,
                HistoricalData.timestamp >= start_date,
                HistoricalData.timestamp <= end_date
            ).order_by(HistoricalData.timestamp.asc()).all()
            
            if not data:
                logger.error(f"No data found for {symbol} between {start_date} and {end_date}")
                return None
            
            # Convert to DataFrame
            df = pd.DataFrame([{
                'timestamp': d.timestamp,
                'open': d.open,
                'high': d.high,
                'low': d.low,
                'close': d.close,
                'volume': d.volume
            } for d in data])
            
            df.set_index('timestamp', inplace=True)
            
            logger.info(f"  Loaded {len(df)} data points")
            
            # Run backtest
            engine = BacktestingEngine(initial_capital=initial_capital)
            result = engine.run_backtest(df, strategy, symbol)
            
            # Save result
            StrategyManager.save_strategy(strategy, result)
            
            return result
            
        except Exception as e:
            logger.error(f"Error replaying strategy: {e}")
            return None
        finally:
            db.close()
