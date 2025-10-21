#!/usr/bin/env python3
"""
Script d'optimisation amélioré - Stratégies hybrides MA + indicateurs avancés
Combine la stratégie MA gagnante (19,42) avec de nouveaux indicateurs pour atteindre >5%
"""

import sys
import os
import time
import numpy as np
import pandas as pd
from concurrent.futures import ProcessPoolExecutor, as_completed
from typing import Tuple, Optional, Dict, Any, List
import sqlite3

# Ajouter le répertoire parent au path pour les imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from backend.backtesting_engine import (
    MovingAverageCrossover,
    BacktestingEngine,
    BacktestResult
)

class AdvancedIndicators:
    """Classe pour calculer les indicateurs avancés"""

    @staticmethod
    def calculate_roc(df: pd.DataFrame, period: int = 10) -> pd.Series:
        """Rate of Change (ROC)"""
        return ((df['close'] - df['close'].shift(period)) / df['close'].shift(period) * 100).fillna(0)

    @staticmethod
    def calculate_atr(df: pd.DataFrame, period: int = 14) -> pd.Series:
        """Average True Range (ATR)"""
        high = df['high']
        low = df['low']
        close = df['close']

        tr1 = high - low
        tr2 = (high - close.shift(1)).abs()
        tr3 = (low - close.shift(1)).abs()

        tr = pd.concat([tr1, tr2, tr3], axis=1).max(axis=1)
        atr = tr.rolling(window=period).mean()
        return atr.fillna(0)

    @staticmethod
    def calculate_adx(df: pd.DataFrame, period: int = 14) -> pd.Series:
        """Average Directional Index (ADX)"""
        high = df['high']
        low = df['low']
        close = df['close']

        # Calcul des mouvements directionnels
        dm_plus = np.where((high - high.shift(1)) > (low.shift(1) - low),
                          np.maximum(high - high.shift(1), 0), 0)
        dm_minus = np.where((low.shift(1) - low) > (high - high.shift(1)),
                           np.maximum(low.shift(1) - low, 0), 0)

        # True Range
        tr = pd.concat([high - low,
                       (high - close.shift(1)).abs(),
                       (low - close.shift(1)).abs()], axis=1).max(axis=1)

        # Moyennes mobiles
        atr = tr.rolling(window=period).mean()
        di_plus = (pd.Series(dm_plus).rolling(window=period).mean() / atr * 100).fillna(0)
        di_minus = (pd.Series(dm_minus).rolling(window=period).mean() / atr * 100).fillna(0)

        # ADX
        dx = (abs(di_plus - di_minus) / (di_plus + di_minus) * 100).fillna(0)
        adx = dx.rolling(window=period).mean().fillna(0)

        return adx

    @staticmethod
    def calculate_volume_ratio(df: pd.DataFrame, short_period: int = 5, long_period: int = 20) -> pd.Series:
        """Volume Ratio (volume court terme / volume long terme)"""
        volume_short = df['volume'].rolling(window=short_period).mean()
        volume_long = df['volume'].rolling(window=long_period).mean()
        ratio = (volume_short / volume_long).fillna(1)
        return ratio

    @staticmethod
    def calculate_momentum(df: pd.DataFrame, period: int = 10) -> pd.Series:
        """Momentum Oscillator"""
        return (df['close'] / df['close'].shift(period) - 1).fillna(0) * 100

    @staticmethod
    def calculate_bb_width(df: pd.DataFrame, period: int = 20, std: float = 2.0) -> pd.Series:
        """Bollinger Bands Width (mesure de volatilité)"""
        sma = df['close'].rolling(window=period).mean()
        std_dev = df['close'].rolling(window=period).std()
        upper = sma + (std_dev * std)
        lower = sma - (std_dev * std)
        width = ((upper - lower) / sma).fillna(0)
        return width

    @staticmethod
    def calculate_stochastic(df: pd.DataFrame, k_period: int = 14, d_period: int = 3) -> pd.Series:
        """Stochastic Oscillator %K"""
        lowest_low = df['low'].rolling(window=k_period).min()
        highest_high = df['high'].rolling(window=k_period).max()
        stoch_k = ((df['close'] - lowest_low) / (highest_high - lowest_low) * 100).fillna(50)
        # %D is the moving average of %K
        stoch_d = stoch_k.rolling(window=d_period).mean().fillna(50)
        return stoch_k

    @staticmethod
    def calculate_williams_r(df: pd.DataFrame, period: int = 14) -> pd.Series:
        """Williams %R"""
        highest_high = df['high'].rolling(window=period).max()
        lowest_low = df['low'].rolling(window=period).min()
        williams_r = ((highest_high - df['close']) / (highest_high - lowest_low) * -100).fillna(-50)
        return williams_r

    @staticmethod
    def calculate_cci(df: pd.DataFrame, period: int = 20) -> pd.Series:
        """Commodity Channel Index (CCI)"""
        typical_price = (df['high'] + df['low'] + df['close']) / 3
        sma = typical_price.rolling(window=period).mean()
        mad = typical_price.rolling(window=period).apply(lambda x: np.mean(np.abs(x - x.mean())), raw=False)
        cci = (typical_price - sma) / (0.015 * mad)
        return cci.fillna(0)

    @staticmethod
    def calculate_trix(df: pd.DataFrame, period: int = 15) -> pd.Series:
        """TRIX (Triple Exponential Average)"""
        ema1 = df['close'].ewm(span=period).mean()
        ema2 = ema1.ewm(span=period).mean()
        ema3 = ema2.ewm(span=period).mean()
        trix = (ema3 - ema3.shift(1)) / ema3.shift(1) * 100
        return trix.fillna(0)

    @staticmethod
    def calculate_keltner_channels(df: pd.DataFrame, period: int = 20, multiplier: float = 2.0) -> pd.Series:
        """Keltner Channels Width (mesure de volatilité)"""
        typical_price = (df['high'] + df['low'] + df['close']) / 3
        ema = typical_price.ewm(span=period).mean()
        atr = AdvancedIndicators.calculate_atr(df, period)
        upper = ema + (atr * multiplier)
        lower = ema - (atr * multiplier)
        width = ((upper - lower) / ema).fillna(0)
        return width

    @staticmethod
    def calculate_ichimoku_conversion(df: pd.DataFrame, period: int = 9) -> pd.Series:
        """Ichimoku Conversion Line (Tenkan-sen)"""
        conversion = (df['high'].rolling(window=period).max() + df['low'].rolling(window=period).min()) / 2
        return conversion

    @staticmethod
    def calculate_ichimoku_base(df: pd.DataFrame, period: int = 26) -> pd.Series:
        """Ichimoku Base Line (Kijun-sen)"""
        base = (df['high'].rolling(window=period).max() + df['low'].rolling(window=period).min()) / 2
        return base

    @staticmethod
    def calculate_ichimoku_cloud(df: pd.DataFrame, conversion_period: int = 9, base_period: int = 26, span_b_period: int = 52) -> pd.Series:
        """Ichimoku Cloud Thickness (Senkou Span A - Senkou Span B)"""
        conversion = AdvancedIndicators.calculate_ichimoku_conversion(df, conversion_period)
        base = AdvancedIndicators.calculate_ichimoku_base(df, base_period)
        span_a = ((conversion + base) / 2).shift(base_period)

        span_b_low = df['low'].rolling(window=span_b_period).min()
        span_b_high = df['high'].rolling(window=span_b_period).max()
        span_b = ((span_b_high + span_b_low) / 2).shift(base_period)

        cloud_thickness = (span_a - span_b).fillna(0)
        return cloud_thickness

    @staticmethod
    def precalculate_all_indicators(df: pd.DataFrame) -> pd.DataFrame:
        """Pré-calcule tous les indicateurs pour optimiser les performances"""
        df = df.copy()

        # Indicateurs de momentum
        df['roc_10'] = AdvancedIndicators.calculate_roc(df, 10)
        df['roc_14'] = AdvancedIndicators.calculate_roc(df, 14)
        df['momentum_10'] = AdvancedIndicators.calculate_momentum(df, 10)
        df['momentum_14'] = AdvancedIndicators.calculate_momentum(df, 14)

        # Indicateurs de tendance
        df['adx_14'] = AdvancedIndicators.calculate_adx(df, 14)
        df['adx_20'] = AdvancedIndicators.calculate_adx(df, 20)

        # Indicateurs de volume
        df['volume_ratio_5_20'] = AdvancedIndicators.calculate_volume_ratio(df, 5, 20)
        df['volume_ratio_10_30'] = AdvancedIndicators.calculate_volume_ratio(df, 10, 30)

        # Indicateurs de volatilité
        df['bb_width_20'] = AdvancedIndicators.calculate_bb_width(df, 20)
        df['bb_width_25'] = AdvancedIndicators.calculate_bb_width(df, 25)
        df['atr_14'] = AdvancedIndicators.calculate_atr(df, 14)
        df['keltner_width_20'] = AdvancedIndicators.calculate_keltner_channels(df, 20)

        # Oscillateurs
        df['stoch_k_14'] = AdvancedIndicators.calculate_stochastic(df, 14)
        df['williams_r_14'] = AdvancedIndicators.calculate_williams_r(df, 14)
        df['cci_20'] = AdvancedIndicators.calculate_cci(df, 20)
        df['trix_15'] = AdvancedIndicators.calculate_trix(df, 15)

        # Ichimoku
        df['ichimoku_conversion_9'] = AdvancedIndicators.calculate_ichimoku_conversion(df, 9)
        df['ichimoku_base_26'] = AdvancedIndicators.calculate_ichimoku_base(df, 26)
        df['ichimoku_cloud'] = AdvancedIndicators.calculate_ichimoku_cloud(df)

        return df

class EnhancedMovingAverageStrategy:
    """Stratégie MA améliorée avec indicateurs avancés"""

    def __init__(self,
                 fast_period: int = 19,
                 slow_period: int = 42,
                 # Indicateurs avancés existants
                 roc_period: int = 10,
                 roc_threshold: float = 2.0,
                 atr_period: int = 14,
                 atr_multiplier: float = 1.5,
                 adx_period: int = 14,
                 adx_threshold: int = 25,
                 volume_ratio_short: int = 5,
                 volume_ratio_long: int = 20,
                 volume_threshold: float = 1.2,
                 momentum_period: int = 10,
                 momentum_threshold: float = 1.0,
                 bb_period: int = 20,
                 bb_width_threshold: float = 0.05,
                 # Nouveaux indicateurs
                 use_stochastic: bool = False,
                 stoch_threshold: float = 80.0,
                 use_williams_r: bool = False,
                 williams_threshold: float = -20.0,
                 use_cci: bool = False,
                 cci_threshold: float = 100.0,
                 use_trix: bool = False,
                 trix_threshold: float = 0.1,
                 use_keltner: bool = False,
                 keltner_threshold: float = 0.03,
                 use_ichimoku: bool = False,
                 ichimoku_threshold: float = 0.0,
                 # Filtres
                 min_signals: int = 2):
        self.fast_period = fast_period
        self.slow_period = slow_period
        # Indicateurs existants
        self.roc_period = roc_period
        self.roc_threshold = roc_threshold
        self.atr_period = atr_period
        self.atr_multiplier = atr_multiplier
        self.adx_period = adx_period
        self.adx_threshold = adx_threshold
        self.volume_ratio_short = volume_ratio_short
        self.volume_ratio_long = volume_ratio_long
        self.volume_threshold = volume_threshold
        self.momentum_period = momentum_period
        self.momentum_threshold = momentum_threshold
        self.bb_period = bb_period
        self.bb_width_threshold = bb_width_threshold
        # Nouveaux indicateurs
        self.use_stochastic = use_stochastic
        self.stoch_threshold = stoch_threshold
        self.use_williams_r = use_williams_r
        self.williams_threshold = williams_threshold
        self.use_cci = use_cci
        self.cci_threshold = cci_threshold
        self.use_trix = use_trix
        self.trix_threshold = trix_threshold
        self.use_keltner = use_keltner
        self.keltner_threshold = keltner_threshold
        self.use_ichimoku = use_ichimoku
        self.ichimoku_threshold = ichimoku_threshold
        # Filtres
        self.min_signals = min_signals

    def generate_signals(self, df: pd.DataFrame) -> pd.Series:
        """Génère les signaux de trading avec filtres avancés"""
        signals = pd.Series(0, index=df.index, dtype=int)

        # Calcul des MAs de base
        fast_ma = df['close'].rolling(window=self.fast_period).mean()
        slow_ma = df['close'].rolling(window=self.slow_period).mean()

        # Utiliser les colonnes pré-calculées pour les indicateurs existants
        roc_col = f'roc_{self.roc_period}'
        adx_col = f'adx_{self.adx_period}'
        volume_col = f'volume_ratio_{self.volume_ratio_short}_{self.volume_ratio_long}'
        momentum_col = f'momentum_{self.momentum_period}'
        bb_col = f'bb_width_{self.bb_period}'

        # Indicateurs existants
        if roc_col in df.columns:
            roc = df[roc_col]
        else:
            roc = AdvancedIndicators.calculate_roc(df, self.roc_period)

        if adx_col in df.columns:
            adx = df[adx_col]
        else:
            adx = AdvancedIndicators.calculate_adx(df, self.adx_period)

        if volume_col in df.columns:
            volume_ratio = df[volume_col]
        else:
            volume_ratio = AdvancedIndicators.calculate_volume_ratio(df, self.volume_ratio_short, self.volume_ratio_long)

        if momentum_col in df.columns:
            momentum = df[momentum_col]
        else:
            momentum = AdvancedIndicators.calculate_momentum(df, self.momentum_period)

        if bb_col in df.columns:
            bb_width = df[bb_col]
        else:
            bb_width = AdvancedIndicators.calculate_bb_width(df, self.bb_period)

        # Nouveaux indicateurs
        stoch_k = df.get('stoch_k_14', AdvancedIndicators.calculate_stochastic(df, 14)) if self.use_stochastic else None
        williams_r = df.get('williams_r_14', AdvancedIndicators.calculate_williams_r(df, 14)) if self.use_williams_r else None
        cci = df.get('cci_20', AdvancedIndicators.calculate_cci(df, 20)) if self.use_cci else None
        trix = df.get('trix_15', AdvancedIndicators.calculate_trix(df, 15)) if self.use_trix else None
        keltner_width = df.get('keltner_width_20', AdvancedIndicators.calculate_keltner_channels(df, 20)) if self.use_keltner else None
        ichimoku_cloud = df.get('ichimoku_cloud', AdvancedIndicators.calculate_ichimoku_cloud(df)) if self.use_ichimoku else None

        # Conditions de base (croisement MA)
        fast_ma_prev = fast_ma.shift(1)
        slow_ma_prev = slow_ma.shift(1)

        bullish_cross = (fast_ma > slow_ma) & (fast_ma_prev <= slow_ma_prev) & fast_ma.notna() & slow_ma.notna()
        bearish_cross = (fast_ma < slow_ma) & (fast_ma_prev >= slow_ma_prev) & fast_ma.notna() & slow_ma.notna()

        # Liste des filtres actifs
        filters = []

        # Filtres existants
        roc_filter = pd.Series(False, index=df.index)
        roc_filter[roc.notna()] = roc[roc.notna()] > self.roc_threshold
        filters.append(roc_filter)

        adx_filter = pd.Series(False, index=df.index)
        adx_filter[adx.notna()] = adx[adx.notna()] > self.adx_threshold
        filters.append(adx_filter)

        volume_filter = pd.Series(False, index=df.index)
        volume_filter[volume_ratio.notna()] = volume_ratio[volume_ratio.notna()] > self.volume_threshold
        filters.append(volume_filter)

        momentum_filter = pd.Series(False, index=df.index)
        momentum_filter[momentum.notna()] = momentum[momentum.notna()] > self.momentum_threshold
        filters.append(momentum_filter)

        volatility_filter = pd.Series(False, index=df.index)
        volatility_filter[bb_width.notna()] = bb_width[bb_width.notna()] > self.bb_width_threshold
        filters.append(volatility_filter)

        # Nouveaux filtres
        if self.use_stochastic:
            stoch_filter = pd.Series(False, index=df.index)
            stoch_filter[stoch_k.notna()] = stoch_k[stoch_k.notna()] > self.stoch_threshold
            filters.append(stoch_filter)

        if self.use_williams_r:
            williams_filter = pd.Series(False, index=df.index)
            williams_filter[williams_r.notna()] = williams_r[williams_r.notna()] < self.williams_threshold
            filters.append(williams_filter)

        if self.use_cci:
            cci_filter = pd.Series(False, index=df.index)
            cci_filter[cci.notna()] = cci[cci.notna()].abs() > self.cci_threshold
            filters.append(cci_filter)

        if self.use_trix:
            trix_filter = pd.Series(False, index=df.index)
            trix_filter[trix.notna()] = trix[trix.notna()] > self.trix_threshold
            filters.append(trix_filter)

        if self.use_keltner:
            keltner_filter = pd.Series(False, index=df.index)
            keltner_filter[keltner_width.notna()] = keltner_width[keltner_width.notna()] > self.keltner_threshold
            filters.append(keltner_filter)

        if self.use_ichimoku:
            ichimoku_filter = pd.Series(False, index=df.index)
            ichimoku_filter[ichimoku_cloud.notna()] = ichimoku_cloud[ichimoku_cloud.notna()] > self.ichimoku_threshold
            filters.append(ichimoku_filter)

        # Combiner les filtres (au moins min_signals doivent être vrais)
        combined_filters = sum(filters) >= self.min_signals

        # Appliquer les signaux avec filtres
        signals.loc[bullish_cross & combined_filters] = 1   # Achat
        signals.loc[bearish_cross & combined_filters] = -1  # Vente

        return signals

class EnhancedStrategyGenerator:
    """Générateur de stratégies MA améliorées avec paramètres aléatoires"""

    def generate_enhanced_ma_strategy(self) -> EnhancedMovingAverageStrategy:
        """Génère une stratégie MA améliorée avec paramètres aléatoires"""
        return EnhancedMovingAverageStrategy(
            # MA de base (autour des valeurs gagnantes)
            fast_period=np.random.randint(15, 25),  # Autour de 19-22
            slow_period=np.random.randint(35, 50),  # Autour de 35-42

            # ROC
            roc_period=np.random.choice([10, 14]),
            roc_threshold=np.random.uniform(1.0, 4.0),

            # ADX
            adx_period=np.random.choice([14, 20]),
            adx_threshold=np.random.randint(20, 35),

            # Volume Ratio
            volume_ratio_short=np.random.choice([3, 5, 10]),
            volume_ratio_long=np.random.choice([15, 20, 30]),
            volume_threshold=np.random.uniform(1.1, 1.5),

            # Momentum
            momentum_period=np.random.choice([10, 14]),
            momentum_threshold=np.random.uniform(0.5, 2.0),

            # Bollinger Bands
            bb_period=np.random.choice([20, 25]),
            bb_width_threshold=np.random.uniform(0.03, 0.08),

            # Nouveaux indicateurs (activation aléatoire)
            use_stochastic=np.random.choice([True, False]),
            stoch_threshold=np.random.uniform(70.0, 85.0),

            use_williams_r=np.random.choice([True, False]),
            williams_threshold=np.random.uniform(-30.0, -15.0),

            use_cci=np.random.choice([True, False]),
            cci_threshold=np.random.uniform(80.0, 120.0),

            use_trix=np.random.choice([True, False]),
            trix_threshold=np.random.uniform(0.05, 0.2),

            use_keltner=np.random.choice([True, False]),
            keltner_threshold=np.random.uniform(0.02, 0.06),

            use_ichimoku=np.random.choice([True, False]),
            ichimoku_threshold=np.random.uniform(-0.01, 0.01),

            # Nombre minimum de signaux de confirmation (adapté au nombre d'indicateurs)
            min_signals=np.random.randint(2, 5)
        )

def run_single_enhanced_backtest(args: Tuple[pd.DataFrame, str, float]) -> Tuple[Dict[str, Any], BacktestResult]:
    """Fonction pour exécuter un seul backtest amélioré (pour parallélisation)"""
    df, symbol, commission = args

    # Générer stratégie améliorée
    generator = EnhancedStrategyGenerator()
    strategy = generator.generate_enhanced_ma_strategy()

    # Créer un wrapper pour l'engine de backtest
    class EnhancedStrategyWrapper:
        def __init__(self, enhanced_strategy):
            self.enhanced_strategy = enhanced_strategy
            self.name = "EnhancedMA"

        def generate_signals(self, df):
            return self.enhanced_strategy.generate_signals(df)

    wrapped_strategy = EnhancedStrategyWrapper(strategy)

    # Exécuter le backtest
    engine = BacktestingEngine(initial_capital=1000.0, commission=commission)
    result = engine.run_backtest(df, wrapped_strategy, symbol)

    # Retourner les infos de la stratégie et le résultat
    strategy_info = {
        'type': 'enhanced_ma',
        'params': strategy.__dict__,
        'return': result.total_return,
        'win_rate': result.win_rate,
        'max_drawdown': result.max_drawdown,
        'sharpe_ratio': result.sharpe_ratio,
        'total_trades': result.total_trades
    }

    return strategy_info, result

def load_worldline_data() -> pd.DataFrame:
    """Charge les données Worldline depuis la base de données"""
    db_path = os.path.join(os.path.dirname(__file__), 'boursicotor.db')

    if not os.path.exists(db_path):
        raise FileNotFoundError(f"Base de données non trouvée: {db_path}")

    conn = sqlite3.connect(db_path)

    # Charger les données WLN (Worldline) depuis historical_data
    query = """
    SELECT timestamp, open, high, low, close, volume
    FROM historical_data
    WHERE ticker_id = (SELECT id FROM tickers WHERE symbol = 'WLN' LIMIT 1)
    ORDER BY timestamp ASC
    """

    df = pd.read_sql_query(query, conn)
    conn.close()

    if df.empty:
        raise ValueError("Aucune donnée trouvée pour WLN")

    df['timestamp'] = pd.to_datetime(df['timestamp'])
    df.set_index('timestamp', inplace=True)

    # PRÉ-CALCULER TOUS LES INDICATEURS POUR OPTIMISER LES PERFORMANCES
    print("⚡ Pré-calcul des indicateurs avancés...")
    df = AdvancedIndicators.precalculate_all_indicators(df)
    print("✅ Indicateurs pré-calculés")

    return df

def main():
    """Fonction principale"""
    print("🚀 Script d'optimisation amélioré - Stratégies MA + indicateurs avancés")
    print("=" * 70)

    # Configuration
    MAX_ITERATIONS = 1000
    INITIAL_CAPITAL = 1000.0
    COMMISSION_PCT = 0.09  # 0.09% par côté (0.18% round-trip)
    COMMISSION_DECIMAL = COMMISSION_PCT / 100  # Convertir en décimal
    SYMBOL = "WLN"
    NUM_WORKERS = min(8, os.cpu_count() or 4)  # Nombre de processus parallèles

    print(f"📊 Configuration:")
    print(f"   - Itérations: {MAX_ITERATIONS}")
    print(f"   - Capital initial: {INITIAL_CAPITAL}€")
    print(f"   - Commission: {COMMISSION_PCT}% par côté")
    print(f"   - Symbole: {SYMBOL}")
    print(f"   - Processus parallèles: {NUM_WORKERS}")
    print(f"   - Stratégie: MA améliorée avec indicateurs avancés")
    print()

    # Charger les données
    print("📈 Chargement des données Worldline...")
    try:
        df = load_worldline_data()
        print(f"✅ {len(df)} points de données chargés")
    except Exception as e:
        print(f"❌ Erreur lors du chargement des données: {e}")
        return
    print()

    # Préparer les arguments pour la parallélisation
    args_list = [(df, SYMBOL, COMMISSION_DECIMAL)] * MAX_ITERATIONS

    # Variables pour suivre le meilleur résultat
    best_strategy = None
    best_result = None
    best_return = -np.inf

    # Démarrer le chronomètre
    start_time = time.time()

    # Exécuter les backtests en parallèle
    print("🔄 Exécution des backtests améliorés en parallèle...")
    print("0% complété", end="", flush=True)

    completed = 0
    last_progress = 0

    with ProcessPoolExecutor(max_workers=NUM_WORKERS) as executor:
        # Soumettre tous les jobs
        future_to_args = {executor.submit(run_single_enhanced_backtest, args): args for args in args_list}

        # Traiter les résultats au fur et à mesure
        for future in as_completed(future_to_args):
            try:
                strategy_info, result = future.result()

                # Mettre à jour le meilleur résultat
                if result.total_return > best_return:
                    best_return = result.total_return
                    best_strategy = strategy_info
                    best_result = result

                completed += 1

                # Afficher le progrès
                progress = int((completed / MAX_ITERATIONS) * 100)
                if progress > last_progress:
                    print(f"\r{progress}% complété (meilleur: {best_return:.2f}%)", end="", flush=True)
                    last_progress = progress

            except Exception as e:
                print(f"❌ Erreur dans un backtest: {e}")
                completed += 1

    # Calculer le temps écoulé
    elapsed_time = time.time() - start_time

    print(f"\r100% complété en {elapsed_time:.1f}s")
    print()

    # Afficher le récapitulatif final
    print("📊 RÉCAPITULATIF FINAL - STRATÉGIES AMÉLIORÉES")
    print("=" * 50)

    if best_strategy and best_result:
        print(f"🏆 Meilleure stratégie trouvée:")
        print(f"   Type: MA Améliorée avec {len([k for k in best_strategy['params'].keys() if not k.startswith('fast') and not k.startswith('slow')])} indicateurs avancés")
        print(f"   Retour total: {best_result.total_return:.2f}%")
        print(f"   Capital final: {best_result.final_capital:.2f}€")
        print(f"   Taux de réussite: {best_result.win_rate:.1f}%")
        print(f"   Nombre de trades: {best_result.total_trades}")
        print(f"   Drawdown maximum: {best_result.max_drawdown:.2f}%")
        print(f"   Ratio Sharpe: {best_result.sharpe_ratio:.2f}")
        print()

        # Afficher les paramètres MA de base
        print("⚙️ Paramètres MA de base:")
        print(f"   Fast MA: {best_strategy['params']['fast_period']}")
        print(f"   Slow MA: {best_strategy['params']['slow_period']}")
        print()

        # Afficher les indicateurs avancés
        print("🔬 Indicateurs avancés utilisés:")
        advanced_indicators = {
            'roc_period': f"ROC ({best_strategy['params']['roc_period']}) > {best_strategy['params']['roc_threshold']:.1f}%",
            'adx_period': f"ADX ({best_strategy['params']['adx_period']}) > {best_strategy['params']['adx_threshold']}",
            'volume_ratio_short': f"Volume Ratio ({best_strategy['params']['volume_ratio_short']}/{best_strategy['params']['volume_ratio_long']}) > {best_strategy['params']['volume_threshold']:.1f}",
            'momentum_period': f"Momentum ({best_strategy['params']['momentum_period']}) > {best_strategy['params']['momentum_threshold']:.1f}%",
            'bb_period': f"BB Width ({best_strategy['params']['bb_period']}) > {best_strategy['params']['bb_width_threshold']:.3f}",
            'min_signals': f"Min {best_strategy['params']['min_signals']} signaux requis"
        }

        for key, desc in advanced_indicators.items():
            if key in best_strategy['params']:
                print(f"   • {desc}")
        print()

    print(f"⏱️ Temps total: {elapsed_time:.1f} secondes")
    print(f"⚡ Performance: {MAX_ITERATIONS/elapsed_time:.1f} itérations/seconde")

    # Évaluation par rapport à l'objectif
    if best_result and best_result.total_return >= 5.0:
        print("🎯 OBJECTIF ATTEINT: Retour >= 5% !")
        print("🎉 La combinaison d'indicateurs avancés a fonctionné !")
    else:
        print(f"⚠️ Objectif non atteint. Meilleur résultat: {best_return:.2f}%")
        if best_return > -1.64:
            print("📈 Amélioration par rapport aux stratégies simples !")
        else:
            print("📉 Résultat similaire aux stratégies simples. Ajustement nécessaire.")

if __name__ == "__main__":
    main()