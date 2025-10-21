"""
Machine Learning models for pattern recognition and prediction
"""
import pandas as pd
import numpy as np
from typing import Dict, List, Tuple, Optional
from sklearn.model_selection import train_test_split, cross_val_score
from sklearn.preprocessing import StandardScaler
from sklearn.ensemble import RandomForestClassifier, GradientBoostingClassifier
from xgboost import XGBClassifier
from sklearn.metrics import accuracy_score, precision_score, recall_score, f1_score, classification_report
import joblib
from datetime import datetime
from pathlib import Path

from backend.config import logger, MODELS_DIR


class MLPatternDetector:
    """Machine Learning pattern detector for trading signals"""
    
    def __init__(self, model_type: str = "random_forest"):
        """
        Initialize ML pattern detector
        
        Args:
            model_type: Type of model ('random_forest', 'xgboost', 'gradient_boosting')
        """
        self.model_type = model_type
        self.model = None
        self.scaler = StandardScaler()
        self.feature_names = []
        self.is_trained = False
        
        # Initialize model
        if model_type == "random_forest":
            self.model = RandomForestClassifier(
                n_estimators=100,
                max_depth=10,
                min_samples_split=5,
                random_state=42
            )
        elif model_type == "xgboost":
            self.model = XGBClassifier(
                n_estimators=100,
                max_depth=6,
                learning_rate=0.1,
                random_state=42
            )
        elif model_type == "gradient_boosting":
            self.model = GradientBoostingClassifier(
                n_estimators=100,
                max_depth=5,
                learning_rate=0.1,
                random_state=42
            )
        else:
            raise ValueError(f"Unknown model type: {model_type}")
    
    def prepare_features(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Prepare features for ML model
        
        Args:
            df: DataFrame with OHLCV and technical indicators
            
        Returns:
            DataFrame with selected features
        """
        features = []
        
        # Price-based features
        if 'close' in df.columns:
            features.extend(['close'])
            # Price changes
            df['price_change_1'] = df['close'].pct_change(1)
            df['price_change_5'] = df['close'].pct_change(5)
            df['price_change_10'] = df['close'].pct_change(10)
            features.extend(['price_change_1', 'price_change_5', 'price_change_10'])
        
        # Volume features
        if 'volume' in df.columns:
            df['volume_change'] = df['volume'].pct_change(1)
            df['volume_sma_5'] = df['volume'].rolling(window=5).mean()
            features.extend(['volume', 'volume_change'])
        
        # Moving averages
        ma_features = ['sma_20', 'sma_50', 'ema_12', 'ema_26']
        for feat in ma_features:
            if feat in df.columns:
                features.append(feat)
                # Distance from price
                df[f'{feat}_dist'] = (df['close'] - df[feat]) / df[feat]
                features.append(f'{feat}_dist')
        
        # Momentum indicators
        momentum_features = ['rsi_14', 'macd', 'macd_signal', 'macd_hist', 
                           'stoch_k', 'stoch_d', 'cci_20', 'roc_12']
        for feat in momentum_features:
            if feat in df.columns:
                features.append(feat)
        
        # Volatility indicators
        volatility_features = ['atr_14', 'bb_width', 'bb_percent']
        for feat in volatility_features:
            if feat in df.columns:
                features.append(feat)
        
        # Trend indicators
        trend_features = ['adx', 'di_plus', 'di_minus']
        for feat in trend_features:
            if feat in df.columns:
                features.append(feat)
        
        # Volume indicators
        volume_indicators = ['obv', 'mfi_14']
        for feat in volume_indicators:
            if feat in df.columns:
                features.append(feat)
        
        self.feature_names = features
        return df[features].copy()
    
    def create_labels(self, df: pd.DataFrame, forward_periods: int = 5, threshold: float = 0.02) -> pd.Series:
        """
        Create labels for supervised learning
        
        Args:
            df: DataFrame with price data
            forward_periods: Number of periods to look ahead
            threshold: Minimum return threshold for positive label
            
        Returns:
            Series with labels (1 for buy, 0 for hold/sell)
        """
        # Calculate forward returns
        forward_returns = df['close'].pct_change(forward_periods).shift(-forward_periods)
        
        # Create labels: 1 if future return > threshold, 0 otherwise
        labels = (forward_returns > threshold).astype(int)
        
        return labels
    
    def train(
        self,
        df: pd.DataFrame,
        forward_periods: int = 5,
        threshold: float = 0.02,
        test_size: float = 0.2
    ) -> Dict:
        """
        Train the ML model
        
        Args:
            df: DataFrame with OHLCV and technical indicators
            forward_periods: Number of periods to look ahead for labels
            threshold: Minimum return threshold for positive label
            test_size: Proportion of data for testing
            
        Returns:
            Training results dictionary
        """
        logger.info(f"Training {self.model_type} model...")
        
        # Prepare features
        X = self.prepare_features(df)
        
        # Create labels
        y = self.create_labels(df, forward_periods, threshold)
        
        # Remove rows with NaN
        valid_idx = X.notna().all(axis=1) & y.notna()
        X = X[valid_idx]
        y = y[valid_idx]
        
        if len(X) < 100:
            raise ValueError("Insufficient data for training (need at least 100 samples)")
        
        logger.info(f"Training with {len(X)} samples, {len(self.feature_names)} features")
        logger.info(f"Positive samples: {y.sum()} ({y.sum()/len(y)*100:.1f}%)")
        
        # Split data
        X_train, X_test, y_train, y_test = train_test_split(
            X, y, test_size=test_size, random_state=42, stratify=y
        )
        
        # Scale features
        X_train_scaled = self.scaler.fit_transform(X_train)
        X_test_scaled = self.scaler.transform(X_test)
        
        # Train model
        self.model.fit(X_train_scaled, y_train)
        self.is_trained = True
        
        # Predictions
        y_pred_train = self.model.predict(X_train_scaled)
        y_pred_test = self.model.predict(X_test_scaled)
        
        # Calculate metrics
        results = {
            'model_type': self.model_type,
            'train_accuracy': accuracy_score(y_train, y_pred_train),
            'test_accuracy': accuracy_score(y_test, y_pred_test),
            'precision': precision_score(y_test, y_pred_test, zero_division=0),
            'recall': recall_score(y_test, y_pred_test, zero_division=0),
            'f1_score': f1_score(y_test, y_pred_test, zero_division=0),
            'n_samples': len(X),
            'n_features': len(self.feature_names),
            'feature_names': self.feature_names,
        }
        
        # Feature importance (if available)
        if hasattr(self.model, 'feature_importances_'):
            feature_importance = pd.DataFrame({
                'feature': self.feature_names,
                'importance': self.model.feature_importances_
            }).sort_values('importance', ascending=False)
            results['feature_importance'] = feature_importance.to_dict('records')
        
        logger.info(f"Training completed - Test Accuracy: {results['test_accuracy']:.3f}")
        logger.info(f"Precision: {results['precision']:.3f}, Recall: {results['recall']:.3f}")
        
        return results
    
    def predict(self, df: pd.DataFrame) -> np.ndarray:
        """
        Make predictions on new data
        
        Args:
            df: DataFrame with features
            
        Returns:
            Array of predictions
        """
        if not self.is_trained:
            raise ValueError("Model not trained yet")
        
        X = self.prepare_features(df)
        X = X[self.feature_names]  # Ensure same features as training
        
        # Handle NaN values
        X = X.fillna(0)
        
        X_scaled = self.scaler.transform(X)
        predictions = self.model.predict(X_scaled)
        
        return predictions
    
    def predict_proba(self, df: pd.DataFrame) -> np.ndarray:
        """
        Get prediction probabilities
        
        Args:
            df: DataFrame with features
            
        Returns:
            Array of probabilities
        """
        if not self.is_trained:
            raise ValueError("Model not trained yet")
        
        X = self.prepare_features(df)
        X = X[self.feature_names]
        X = X.fillna(0)
        
        X_scaled = self.scaler.transform(X)
        probabilities = self.model.predict_proba(X_scaled)
        
        return probabilities
    
    def save(self, filename: str):
        """Save model to file"""
        if not self.is_trained:
            raise ValueError("Cannot save untrained model")
        
        filepath = MODELS_DIR / filename
        
        model_data = {
            'model': self.model,
            'scaler': self.scaler,
            'model_type': self.model_type,
            'feature_names': self.feature_names,
            'trained_at': datetime.now()
        }
        
        joblib.dump(model_data, filepath)
        logger.info(f"Model saved to {filepath}")
    
    def load(self, filename: str):
        """Load model from file"""
        filepath = MODELS_DIR / filename
        
        if not filepath.exists():
            raise FileNotFoundError(f"Model file not found: {filepath}")
        
        model_data = joblib.load(filepath)
        
        self.model = model_data['model']
        self.scaler = model_data['scaler']
        self.model_type = model_data['model_type']
        self.feature_names = model_data['feature_names']
        self.is_trained = True
        
        logger.info(f"Model loaded from {filepath}")
        logger.info(f"Trained at: {model_data.get('trained_at', 'Unknown')}")


if __name__ == "__main__":
    # Test ML model
    print("Testing ML Pattern Detector...")
    
    # Generate sample data
    dates = pd.date_range('2024-01-01', periods=1000, freq='1H')
    df = pd.DataFrame({
        'close': np.random.randn(1000).cumsum() + 100,
        'volume': np.random.randint(1000, 10000, 1000),
        'rsi_14': np.random.uniform(20, 80, 1000),
        'macd': np.random.randn(1000),
        'macd_signal': np.random.randn(1000),
    }, index=dates)
    
    # Train model
    detector = MLPatternDetector(model_type="random_forest")
    results = detector.train(df)
    
    print(f"Test Accuracy: {results['test_accuracy']:.3f}")
    print(f"F1 Score: {results['f1_score']:.3f}")
