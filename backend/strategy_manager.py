"""
Strategy Manager - Gestion des stratégies de trading
"""
import json
from typing import List, Optional, Dict
from datetime import datetime

from backend.config import logger
from backend.models import SessionLocal, Strategy as StrategyModel, Backtest as BacktestModel, Ticker
from backend.backtesting_engine import Strategy, BacktestResult, BacktestingEngine


class StrategyManager:
    """Gestionnaire de stratégies"""
    
    @staticmethod
    def save_strategy(strategy: Strategy, backtest_result: BacktestResult) -> int:
        """
        Sauvegarde une stratégie et son résultat de backtest
        
        Args:
            strategy: Stratégie à sauvegarder
            backtest_result: Résultat du backtest
            
        Returns:
            ID de la stratégie sauvegardée
        """
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
                # Create new strategy
                strategy_db = StrategyModel(
                    name=strategy.name,
                    description=f"Auto-generated strategy with {backtest_result.total_return:.2f}% return",
                    strategy_type=strategy.name,
                    parameters=json.dumps(strategy.parameters),
                    is_active=True
                )
                db.add(strategy_db)
                db.flush()  # Get the ID
            
            # Get ticker
            ticker = db.query(Ticker).filter(Ticker.symbol == backtest_result.symbol).first()
            if not ticker:
                logger.error(f"Ticker {backtest_result.symbol} not found")
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
            strategy_data = {
                'name': strategy_db.strategy_type,
                'parameters': parameters
            }
            
            strategy = Strategy.from_dict(strategy_data)
            logger.info(f"✅ Strategy loaded: {strategy.name}")
            return strategy
            
        except Exception as e:
            logger.error(f"Error loading strategy: {e}")
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
        db = SessionLocal()
        try:
            strategies = db.query(StrategyModel).all()
            
            result = []
            for s in strategies:
                # Get latest backtest
                latest_backtest = db.query(BacktestModel).filter(
                    BacktestModel.strategy_id == s.id
                ).order_by(BacktestModel.created_at.desc()).first()
                
                result.append({
                    'id': s.id,
                    'name': s.name,
                    'description': s.description,
                    'type': s.strategy_type,
                    'is_active': s.is_active,
                    'parameters': json.loads(s.parameters),
                    'latest_return': latest_backtest.total_return if latest_backtest else None,
                    'latest_win_rate': latest_backtest.win_rate if latest_backtest else None,
                    'total_backtests': db.query(BacktestModel).filter(
                        BacktestModel.strategy_id == s.id
                    ).count(),
                    'created_at': s.created_at
                })
            
            return result
            
        except Exception as e:
            logger.error(f"Error getting strategies: {e}")
            return []
        finally:
            db.close()
    
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
            
            ticker = db.query(Ticker).filter(Ticker.symbol == symbol).first()
            if not ticker:
                logger.error(f"Ticker {symbol} not found")
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
    
    @staticmethod
    def delete_strategy(strategy_id: int) -> bool:
        """
        Supprime une stratégie
        
        Args:
            strategy_id: ID de la stratégie
            
        Returns:
            True si succès
        """
        db = SessionLocal()
        try:
            strategy = db.query(StrategyModel).filter(StrategyModel.id == strategy_id).first()
            
            if not strategy:
                logger.error(f"Strategy {strategy_id} not found")
                return False
            
            db.delete(strategy)
            db.commit()
            
            logger.info(f"✅ Strategy {strategy_id} deleted")
            return True
            
        except Exception as e:
            db.rollback()
            logger.error(f"Error deleting strategy: {e}")
            return False
        finally:
            db.close()
