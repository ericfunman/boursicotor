#!/usr/bin/env python3
"""
Script d'optimisation rapide utilisant seulement les stratégies simples
comme l'application web, avec parallélisation pour les performances.
"""

import sys
import os
import time
import numpy as np
import pandas as pd
from concurrent.futures import ProcessPoolExecutor, as_completed
from typing import Tuple, Optional, Dict, Any
import sqlite3

# Ajouter le répertoire parent au path pour les imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from backend.backtesting_engine import (
    MovingAverageCrossover,
    RSIStrategy,
    MultiIndicatorStrategy,
    BacktestingEngine,
    BacktestResult
)

class SimpleStrategyGenerator:
    """Générateur de stratégies simples seulement (comme l'app web)"""

    def generate_random_ma_strategy(self) -> MovingAverageCrossover:
        """Génère une stratégie MA aléatoire"""
        fast = np.random.randint(5, 20)
        slow = np.random.randint(fast + 5, 50)
        return MovingAverageCrossover(fast_period=fast, slow_period=slow)

    def generate_random_rsi_strategy(self) -> RSIStrategy:
        """Génère une stratégie RSI aléatoire"""
        period = np.random.randint(10, 20)
        oversold = np.random.randint(20, 35)
        overbought = np.random.randint(65, 80)
        return RSIStrategy(rsi_period=period, oversold=oversold, overbought=overbought)

    def generate_random_multi_strategy(self) -> MultiIndicatorStrategy:
        """Génère une stratégie multi-indicateurs aléatoire"""
        return MultiIndicatorStrategy(
            ma_fast=np.random.randint(5, 15),
            ma_slow=np.random.randint(20, 40),
            rsi_period=np.random.randint(10, 20),
            rsi_oversold=np.random.randint(20, 35),
            rsi_overbought=np.random.randint(65, 80),
            macd_fast=np.random.randint(10, 15),
            macd_slow=np.random.randint(20, 30),
            macd_signal=np.random.randint(7, 12)
        )

    def generate_random_strategy(self) -> Tuple[str, Any]:
        """Génère une stratégie aléatoire parmi les 3 types simples"""
        strategy_type = np.random.choice(['ma', 'rsi', 'multi'])

        if strategy_type == 'ma':
            strategy = self.generate_random_ma_strategy()
        elif strategy_type == 'rsi':
            strategy = self.generate_random_rsi_strategy()
        else:  # multi
            strategy = self.generate_random_multi_strategy()

        return strategy_type, strategy

def run_single_backtest(args: Tuple[pd.DataFrame, str, float]) -> Tuple[Dict[str, Any], BacktestResult]:
    """Fonction pour exécuter un seul backtest (pour parallélisation)"""
    df, symbol, commission = args

    # Générer stratégie dans le processus enfant
    generator = SimpleStrategyGenerator()
    strategy_type, strategy = generator.generate_random_strategy()

    # Exécuter le backtest
    engine = BacktestingEngine(initial_capital=1000.0, commission=commission)
    result = engine.run_backtest(df, strategy, symbol)

    # Retourner les infos de la stratégie et le résultat
    strategy_info = {
        'type': strategy_type,
        'params': strategy.__dict__ if hasattr(strategy, '__dict__') else {},
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

    return df

def main():
    """Fonction principale"""
    print("🚀 Script d'optimisation rapide - Stratégies simples seulement")
    print("=" * 60)

    # Configuration
    MAX_ITERATIONS = 1000
    INITIAL_CAPITAL = 1000.0
    COMMISSION_PCT = 0.09  # 0.09% par côté (0.18% aller-retour)
    COMMISSION_DECIMAL = COMMISSION_PCT / 100  # Convertir en décimal
    SYMBOL = "WLN"
    NUM_WORKERS = min(8, os.cpu_count() or 4)  # Nombre de processus parallèles

    print(f"📊 Configuration:")
    print(f"   - Itérations: {MAX_ITERATIONS}")
    print(f"   - Capital initial: {INITIAL_CAPITAL}€")
    print(f"   - Commission: {COMMISSION_PCT}% par côté")
    print(f"   - Symbole: {SYMBOL}")
    print(f"   - Processus parallèles: {NUM_WORKERS}")
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
    print("🔄 Exécution des backtests en parallèle...")
    print("0% complété", end="", flush=True)

    completed = 0
    last_progress = 0

    with ProcessPoolExecutor(max_workers=NUM_WORKERS) as executor:
        # Soumettre tous les jobs
        future_to_args = {executor.submit(run_single_backtest, args): args for args in args_list}

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
    print("📊 RÉCAPITULATIF FINAL")
    print("=" * 40)

    if best_strategy and best_result:
        print(f"🏆 Meilleure stratégie trouvée:")
        print(f"   Type: {best_strategy['type'].upper()}")
        print(f"   Retour total: {best_result.total_return:.2f}%")
        print(f"   Capital final: {best_result.final_capital:.2f}€")
        print(f"   Taux de réussite: {best_result.win_rate:.1f}%")
        print(f"   Nombre de trades: {best_result.total_trades}")
        print(f"   Drawdown maximum: {best_result.max_drawdown:.2f}%")
        print(f"   Ratio Sharpe: {best_result.sharpe_ratio:.2f}")
        print()

        # Afficher les paramètres de la stratégie
        print("⚙️ Paramètres de la stratégie:")
        for key, value in best_strategy['params'].items():
            print(f"   {key}: {value}")
        print()

    print(f"⏱️ Temps total: {elapsed_time:.1f} secondes")
    print(f"⚡ Performance: {MAX_ITERATIONS/elapsed_time:.1f} itérations/seconde")

    # Évaluation par rapport à l'objectif
    if best_result and best_result.total_return >= 5.0:
        print("🎯 OBJECTIF ATTEINT: Retour >= 5% !")
    else:
        print(f"⚠️ Objectif non atteint. Meilleur résultat: {best_return:.2f}%")
        print("💡 Proposition: Ajouter de la complexité aux stratégies pour le prochain run")

if __name__ == "__main__":
    main()