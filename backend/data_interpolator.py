"""
Data Interpolator - Generate high-frequency data from lower-frequency historical data
"""
import pandas as pd
import numpy as np
from datetime import timedelta
from backend.config import logger
from backend.models import SessionLocal, HistoricalData, Ticker as TickerModel
from sqlalchemy import and_


class DataInterpolator:
    """Interpolate historical data to create higher frequency data points"""
    
    INTERVAL_MULTIPLIERS = {
        # From 1min to seconds
        ('1min', '1s'): 60,
        ('1min', '5s'): 12,
        ('1min', '10s'): 6,
        ('1min', '30s'): 2,
        
        # From 5min to lower
        ('5min', '1s'): 300,
        ('5min', '5s'): 60,
        ('5min', '10s'): 30,
        ('5min', '30s'): 10,
        ('5min', '1min'): 5,
        
        # From 15min to lower
        ('15min', '1min'): 15,
        ('15min', '5min'): 3,
        
        # From 30min to lower
        ('30min', '1min'): 30,
        ('30min', '5min'): 6,
        ('30min', '15min'): 2,
        
        # From 1h to lower
        ('1h', '1min'): 60,
        ('1h', '5min'): 12,
        ('1h', '15min'): 4,
        ('1h', '30min'): 2,
        
        # From 1day to lower
        ('1day', '1h'): 24,
        ('1day', '30min'): 48,
        ('1day', '15min'): 96,
    }
    
    @staticmethod
    def get_timedelta(interval: str):
        """Convert interval string to timedelta"""
        mapping = {
            '1s': timedelta(seconds=1),
            '5s': timedelta(seconds=5),
            '10s': timedelta(seconds=10),
            '30s': timedelta(seconds=30),
            '1min': timedelta(minutes=1),
            '5min': timedelta(minutes=5),
            '15min': timedelta(minutes=15),
            '30min': timedelta(minutes=30),
            '1h': timedelta(hours=1),
            '1day': timedelta(days=1),
        }
        return mapping.get(interval)
    
    @staticmethod
    def can_interpolate(source_interval: str, target_interval: str) -> bool:
        """Check if interpolation is possible between two intervals"""
        return (source_interval, target_interval) in DataInterpolator.INTERVAL_MULTIPLIERS
    
    @staticmethod
    def get_interpolation_methods():
        """Get available interpolation methods"""
        return {
            'linear': 'Linéaire - Interpolation linéaire simple',
            'cubic': 'Cubique - Spline cubique (plus lisse)',
            'time': 'Temporel - Interpolation temporelle avec variance',
            'ohlc': 'OHLC - Préserve les patterns OHLC'
        }
    
    @staticmethod
    def interpolate_data(
        df: pd.DataFrame,
        source_interval: str,
        target_interval: str,
        method: str = 'linear'
    ) -> pd.DataFrame:
        """
        Interpolate data from source interval to target interval
        
        Args:
            df: DataFrame with OHLCV data
            source_interval: Original interval (e.g., '1min')
            target_interval: Target interval (e.g., '1s')
            method: Interpolation method ('linear', 'cubic', 'time', 'ohlc')
        
        Returns:
            Interpolated DataFrame
        """
        if not DataInterpolator.can_interpolate(source_interval, target_interval):
            raise ValueError(f"Cannot interpolate from {source_interval} to {target_interval}")
        
        multiplier = DataInterpolator.INTERVAL_MULTIPLIERS[(source_interval, target_interval)]
        target_delta = DataInterpolator.get_timedelta(target_interval)
        
        logger.info(f"Interpolating {len(df)} points from {source_interval} to {target_interval} (x{multiplier})")
        
        interpolated_data = []
        
        for i in range(len(df) - 1):
            current_row = df.iloc[i]
            next_row = df.iloc[i + 1]
            
            current_time = current_row['timestamp']
            
            # Generate intermediate points
            for j in range(multiplier):
                new_time = current_time + (target_delta * j)
                
                if method == 'linear':
                    # Simple linear interpolation
                    ratio = j / multiplier
                    new_row = {
                        'timestamp': new_time,
                        'open': current_row['open'] + (next_row['open'] - current_row['open']) * ratio,
                        'high': current_row['high'] + (next_row['high'] - current_row['high']) * ratio,
                        'low': current_row['low'] + (next_row['low'] - current_row['low']) * ratio,
                        'close': current_row['close'] + (next_row['close'] - current_row['close']) * ratio,
                        'volume': int(current_row['volume'] / multiplier),
                    }
                
                elif method == 'cubic':
                    # Cubic spline interpolation (smoother)
                    ratio = j / multiplier
                    # Use cubic Hermite interpolation
                    t = ratio
                    t2 = t * t
                    t3 = t2 * t
                    h00 = 2*t3 - 3*t2 + 1
                    h10 = t3 - 2*t2 + t
                    h01 = -2*t3 + 3*t2
                    h11 = t3 - t2
                    
                    new_row = {
                        'timestamp': new_time,
                        'open': h00 * current_row['open'] + h01 * next_row['open'],
                        'high': h00 * current_row['high'] + h01 * next_row['high'],
                        'low': h00 * current_row['low'] + h01 * next_row['low'],
                        'close': h00 * current_row['close'] + h01 * next_row['close'],
                        'volume': int(current_row['volume'] / multiplier),
                    }
                
                elif method == 'time':
                    # Time-based with random variance
                    ratio = j / multiplier
                    variance = 0.001  # 0.1% variance
                    
                    new_row = {
                        'timestamp': new_time,
                        'open': current_row['open'] + (next_row['open'] - current_row['open']) * ratio * (1 + np.random.uniform(-variance, variance)),
                        'high': max(current_row['high'], next_row['high']) * (1 + np.random.uniform(0, variance)),
                        'low': min(current_row['low'], next_row['low']) * (1 - np.random.uniform(0, variance)),
                        'close': current_row['close'] + (next_row['close'] - current_row['close']) * ratio * (1 + np.random.uniform(-variance, variance)),
                        'volume': int(current_row['volume'] / multiplier * (1 + np.random.uniform(-0.2, 0.2))),
                    }
                
                elif method == 'ohlc':
                    # OHLC-aware interpolation
                    ratio = j / multiplier
                    
                    # Create realistic OHLC bars
                    base_price = current_row['close'] + (next_row['close'] - current_row['close']) * ratio
                    price_range = abs(next_row['close'] - current_row['close']) / multiplier
                    
                    new_row = {
                        'timestamp': new_time,
                        'open': base_price + np.random.uniform(-price_range/2, price_range/2),
                        'close': base_price + np.random.uniform(-price_range/2, price_range/2),
                        'volume': int(current_row['volume'] / multiplier),
                    }
                    # High/Low must encompass Open/Close
                    new_row['high'] = max(new_row['open'], new_row['close']) + np.random.uniform(0, price_range/2)
                    new_row['low'] = min(new_row['open'], new_row['close']) - np.random.uniform(0, price_range/2)
                
                interpolated_data.append(new_row)
        
        # Add the last original point
        last_row = df.iloc[-1]
        interpolated_data.append({
            'timestamp': last_row['timestamp'],
            'open': last_row['open'],
            'high': last_row['high'],
            'low': last_row['low'],
            'close': last_row['close'],
            'volume': int(last_row['volume']),
        })
        
        result_df = pd.DataFrame(interpolated_data)
        logger.info(f"Interpolation complete: {len(result_df)} points generated")
        
        return result_df
    
    @staticmethod
    def interpolate_and_save(
        ticker_symbol: str,
        source_interval: str,
        target_interval: str,
        method: str = 'linear',
        limit: int = None
    ) -> dict:
        """
        Interpolate historical data and save to database
        
        Args:
            ticker_symbol: Ticker symbol
            source_interval: Source interval (e.g., '1min')
            target_interval: Target interval (e.g., '1s')
            method: Interpolation method
            limit: Max number of source records to process (None = all)
        
        Returns:
            Dict with success status, message, and stats
        """
        db = SessionLocal()
        try:
            # Get ticker
            ticker = db.query(TickerModel).filter(TickerModel.symbol == ticker_symbol).first()
            if not ticker:
                return {'success': False, 'message': f"Ticker {ticker_symbol} not found"}
            
            # Get source data
            query = db.query(HistoricalData).filter(
                and_(
                    HistoricalData.ticker_id == ticker.id,
                    HistoricalData.interval == source_interval
                )
            ).order_by(HistoricalData.timestamp)
            
            if limit:
                query = query.limit(limit)
            
            source_data = query.all()
            
            if not source_data:
                return {'success': False, 'message': f"No data found for {ticker_symbol} at {source_interval} interval"}
            
            # Convert to DataFrame
            df = pd.DataFrame([{
                'timestamp': d.timestamp,
                'open': d.open,
                'high': d.high,
                'low': d.low,
                'close': d.close,
                'volume': d.volume
            } for d in source_data])
            
            # Interpolate
            interpolated_df = DataInterpolator.interpolate_data(df, source_interval, target_interval, method)
            
            # Save to database
            new_records = 0
            duplicates = 0
            
            for _, row in interpolated_df.iterrows():
                # Check if already exists
                existing = db.query(HistoricalData).filter(
                    and_(
                        HistoricalData.ticker_id == ticker.id,
                        HistoricalData.timestamp == row['timestamp'],
                        HistoricalData.interval == target_interval
                    )
                ).first()
                
                if not existing:
                    new_record = HistoricalData(
                        ticker_id=ticker.id,
                        timestamp=row['timestamp'],
                        open=float(row['open']),
                        high=float(row['high']),
                        low=float(row['low']),
                        close=float(row['close']),
                        volume=int(row['volume']),
                        interval=target_interval
                    )
                    db.add(new_record)
                    new_records += 1
                else:
                    duplicates += 1
            
            db.commit()
            
            return {
                'success': True,
                'message': f"Interpolation réussie: {new_records:,} nouveaux enregistrements créés",
                'source_records': len(source_data),
                'generated_records': len(interpolated_df),
                'new_records': new_records,
                'duplicates': duplicates
            }
            
        except Exception as e:
            db.rollback()
            logger.error(f"Interpolation error: {e}")
            return {'success': False, 'message': f"Erreur: {str(e)}"}
        
        finally:
            db.close()
