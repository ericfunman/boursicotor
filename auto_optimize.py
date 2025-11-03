"""
Script d'auto-optimisation autonome pour Boursicotor
Boucle sur les stratégies en ajoutant des indicateurs si nécessaire
"""
import sys
import pandas as pd
from datetime import datetime
from backend.config import logger
from backend.models import SessionLocal, Ticker, HistoricalData
from backend.backtesting_engine import StrategyGenerator, BacktestingEngine
from backend.strategy_manager import StrategyManager


class AutoOptimizer:
    """Optimiseur autonome de stratégies"""
    
    def __init__(self, symbol: str = "WLN", capital: float = 1000.0, iterations: int = 500):
        self.symbol = symbol
        self.capital = capital
        self.iterations = iterations
        self.best_return = -float('inf')
        self.best_strategy = None
        self.best_result = None
        self.history = []
        
    def load_data(self):
        """Charge les données depuis la base"""
        logger.info(f"📊 Chargement des données pour {self.symbol}...")
        db = SessionLocal()
        try:
            ticker = db.query(Ticker).filter(Ticker.symbol == self.symbol).first()
            if not ticker:
                logger.error(f"❌ Ticker {self.symbol} non trouvé")
                return None
            
            # Charger toutes les données historiques
            data = db.query(HistoricalData).filter(
                HistoricalData.ticker_id == ticker.id
            ).order_by(HistoricalData.timestamp.asc()).all()
            
            if len(data) < 100:
                logger.error(f"❌ Pas assez de données pour {self.symbol} (minimum 100 points)")
                return None
            
            # Convertir en DataFrame
            df = pd.DataFrame([{
                'timestamp': d.timestamp,
                'open': d.open,
                'high': d.high,
                'low': d.low,
                'close': d.close,
                'volume': d.volume
            } for d in data])
            
            df.set_index('timestamp', inplace=True)
            
            logger.info(f"✅ {len(df)} points de données chargés ({df.index.min()} - {df.index.max()})")
            return df
            
        finally:
            db.close()
    
    def run_cycle(self, cycle_num: int, target_return: float = 5.0):
        """
        Exécute un cycle d'optimisation
        
        Args:
            cycle_num: Numéro du cycle
            target_return: Objectif de retour en %
            
        Returns:
            (best_strategy, best_result, achieved_target)
        """
        print(f"\n{'='*80}")
        print(f"🔄 CYCLE {cycle_num} - Objectif: {target_return}% | Itérations: {self.iterations}")
        print(f"{'='*80}\n")
        
        # Charger les données
        df = self.load_data()
        if df is None:
            return None, None, False
        
        # Créer le générateur de stratégies
        generator = StrategyGenerator(target_return=target_return)
        engine = BacktestingEngine(initial_capital=self.capital)
        
        cycle_best_return = -float('inf')
        cycle_best_strategy = None
        cycle_best_result = None
        
        # Statistiques du cycle
        strategy_counts = {
            'ultimate': 0, 'hyper': 0, 'mega': 0, 'ultra': 0,
            'advanced': 0, 'multi': 0, 'others': 0
        }
        
        print(f"🚀 Démarrage de {self.iterations} itérations...\n")
        
        for i in range(self.iterations):
            # Générer stratégie aléatoire (priorité ULTIMATE à 85%)
            import numpy as np
            strategy_type = np.random.choice(
                ['ma', 'rsi', 'multi', 'advanced', 'momentum', 'mean_reversion', 
                 'ultra_aggressive', 'mega', 'hyper', 'ultimate', 'ultimate', 'ultimate'],
                p=[0.01, 0.01, 0.01, 0.01, 0.01, 0.02, 0.03, 0.03, 0.02, 0.283, 0.283, 0.284]
            )
            
            # Compter les types de stratégies
            if strategy_type == 'ultimate':
                strategy = generator.generate_random_ultimate_strategy()
                strategy_counts['ultimate'] += 1
            elif strategy_type == 'hyper':
                strategy = generator.generate_random_hyper_strategy()
                strategy_counts['hyper'] += 1
            elif strategy_type == 'mega':
                strategy = generator.generate_random_mega_strategy()
                strategy_counts['mega'] += 1
            elif strategy_type == 'ultra_aggressive':
                strategy = generator.generate_random_ultra_aggressive_strategy()
                strategy_counts['ultra'] += 1
            elif strategy_type == 'advanced':
                strategy = generator.generate_random_advanced_multi_strategy()
                strategy_counts['advanced'] += 1
            elif strategy_type == 'multi':
                strategy = generator.generate_random_multi_strategy()
                strategy_counts['multi'] += 1
            elif strategy_type == 'ma':
                strategy = generator.generate_random_ma_strategy()
                strategy_counts['others'] += 1
            elif strategy_type == 'rsi':
                strategy = generator.generate_random_rsi_strategy()
                strategy_counts['others'] += 1
            elif strategy_type == 'momentum':
                strategy = generator.generate_random_momentum_strategy()
                strategy_counts['others'] += 1
            else:
                strategy = generator.generate_random_mean_reversion_strategy()
                strategy_counts['others'] += 1
            
            # Backtester
            result = engine.run_backtest(df, strategy, self.symbol)
            
            # Vérifier si c'est le meilleur
            if result.total_return > cycle_best_return:
                cycle_best_return = result.total_return
                cycle_best_strategy = strategy
                cycle_best_result = result
                
                # Afficher les progrès
                if i % 50 == 0 or result.total_return > 0:
                    print(f"  ✨ Iter {i+1:3d}/{self.iterations} - Nouveau best: {result.total_return:+7.2f}% "
                          f"| {strategy.name} | Trades: {result.total_trades}")
            
            # Afficher progression tous les 100
            elif (i+1) % 100 == 0:
                print(f"  ⏳ Iter {i+1:3d}/{self.iterations} - Best actuel: {cycle_best_return:+7.2f}%")
        
        # Résumé du cycle
        print(f"\n{'─'*80}")
        print(f"📊 RÉSULTATS CYCLE {cycle_num}")
        print(f"{'─'*80}")
        print(f"🎯 Meilleur retour: {cycle_best_return:+.2f}% (objectif: {target_return}%)")
        print(f"📈 Stratégie: {cycle_best_strategy.name if cycle_best_strategy else 'N/A'}")
        
        if cycle_best_result:
            print(f"💼 Capital final: {cycle_best_result.final_capital:.2f} € (initial: {self.capital} €)")
            print(f"🔄 Trades totaux: {cycle_best_result.total_trades}")
            print(f"✅ Win rate: {cycle_best_result.win_rate:.1f}%")
            print(f"📉 Max drawdown: {cycle_best_result.max_drawdown:.2f}%")
            if cycle_best_result.sharpe_ratio is not None:
                print(f"📊 Sharpe ratio: {cycle_best_result.sharpe_ratio:.2f}")
        
        print(f"\n🎲 Distribution des stratégies testées:")
        print(f"   ULTIMATE:  {strategy_counts['ultimate']:3d} ({strategy_counts['ultimate']/self.iterations*100:.1f}%)")
        print(f"   HYPER:     {strategy_counts['hyper']:3d} ({strategy_counts['hyper']/self.iterations*100:.1f}%)")
        print(f"   MEGA:      {strategy_counts['mega']:3d} ({strategy_counts['mega']/self.iterations*100:.1f}%)")
        print(f"   ULTRA:     {strategy_counts['ultra']:3d} ({strategy_counts['ultra']/self.iterations*100:.1f}%)")
        print(f"   ADVANCED:  {strategy_counts['advanced']:3d} ({strategy_counts['advanced']/self.iterations*100:.1f}%)")
        print(f"   MULTI:     {strategy_counts['multi']:3d} ({strategy_counts['multi']/self.iterations*100:.1f}%)")
        print(f"   AUTRES:    {strategy_counts['others']:3d} ({strategy_counts['others']/self.iterations*100:.1f}%)")
        
        # Sauvegarder si meilleur global
        if cycle_best_return > self.best_return:
            self.best_return = cycle_best_return
            self.best_strategy = cycle_best_strategy
            self.best_result = cycle_best_result
            
            # Sauvegarder dans la base
            if cycle_best_strategy and cycle_best_result:
                strategy_id = StrategyManager.save_strategy(cycle_best_strategy, cycle_best_result)
                print(f"\n💾 Nouvelle meilleure stratégie sauvegardée (ID: {strategy_id})")
        
        # Enregistrer dans l'historique
        self.history.append({
            'cycle': cycle_num,
            'return': cycle_best_return,
            'strategy': cycle_best_strategy.name if cycle_best_strategy else None,
            'trades': cycle_best_result.total_trades if cycle_best_result else 0,
            'win_rate': cycle_best_result.win_rate if cycle_best_result else 0,
            'achieved_target': cycle_best_return >= target_return
        })
        
        achieved = cycle_best_return >= target_return
        
        if achieved:
            print(f"\n🎉 OBJECTIF ATTEINT ! {cycle_best_return:.2f}% >= {target_return}%")
        else:
            print(f"\n⚠️  Objectif non atteint: {cycle_best_return:.2f}% < {target_return}%")
            print(f"💡 Prochaine étape: Ajuster les paramètres ou augmenter les indicateurs")
        
        print(f"{'='*80}\n")
        
        return cycle_best_strategy, cycle_best_result, achieved
    
    def run_optimization(self, num_cycles: int = 5, target_return: float = 5.0):
        """
        Lance l'optimisation complète sur plusieurs cycles
        
        Args:
            num_cycles: Nombre de cycles à exécuter
            target_return: Objectif de retour en %
        """
        print(f"\n{'█'*80}")
        print(f"🤖 AUTO-OPTIMISATION BOURSICOTOR")
        print(f"{'█'*80}")
        print(f"📅 Début: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"🎯 Objectif: {target_return}% de retour")
        print(f"🔢 Nombre de cycles: {num_cycles}")
        print(f"🔄 Itérations par cycle: {self.iterations}")
        print(f"💰 Capital initial: {self.capital} €")
        print(f"📊 Symbole: {self.symbol}")
        print(f"{'█'*80}\n")
        
        start_time = datetime.now()
        
        for cycle in range(1, num_cycles + 1):
            strategy, result, achieved = self.run_cycle(cycle, target_return)
            
            # Si objectif atteint, on peut s'arrêter
            if achieved:
                print(f"🏆 SUCCÈS ! Objectif atteint au cycle {cycle}/{num_cycles}")
                print(f"🎯 Meilleur retour global: {self.best_return:.2f}%")
                break
            
            # Sinon, continuer avec le cycle suivant
            if cycle < num_cycles:
                print(f"🔄 Passage au cycle suivant ({cycle+1}/{num_cycles})...\n")
        
        # Résumé final
        end_time = datetime.now()
        duration = (end_time - start_time).total_seconds()
        
        print(f"\n{'█'*80}")
        print(f"📊 RÉSUMÉ FINAL DE L'OPTIMISATION")
        print(f"{'█'*80}")
        print(f"⏱️  Durée totale: {duration:.1f} secondes ({duration/60:.1f} minutes)")
        print(f"🔢 Cycles complétés: {len(self.history)}/{num_cycles}")
        print(f"🎯 Meilleur retour global: {self.best_return:+.2f}%")
        
        if self.best_strategy:
            print(f"🏆 Meilleure stratégie: {self.best_strategy.name}")
            print(f"💼 Capital final: {self.best_result.final_capital:.2f} €")
            print(f"🔄 Trades: {self.best_result.total_trades}")
            print(f"✅ Win rate: {self.best_result.win_rate:.1f}%")
        
        print(f"\n📈 Progression des cycles:")
        for h in self.history:
            status = "✅" if h['achieved_target'] else "❌"
            print(f"   Cycle {h['cycle']}: {h['return']:+7.2f}% | {h['strategy']} | "
                  f"{h['trades']} trades | WR: {h['win_rate']:.1f}% {status}")
        
        print(f"{'█'*80}\n")
        
        return self.best_strategy, self.best_result


def main():
    """Point d'entrée du script"""
    # Paramètres par défaut
    num_cycles = 5
    capital = 1000.0
    iterations = 500
    target_return = 5.0
    symbol = "WLN"
    
    # Lire les arguments de ligne de commande si fournis
    if len(sys.argv) > 1:
        num_cycles = int(sys.argv[1])
    if len(sys.argv) > 2:
        capital = float(sys.argv[2])
    if len(sys.argv) > 3:
        iterations = int(sys.argv[3])
    if len(sys.argv) > 4:
        target_return = float(sys.argv[4])
    
    print(f"\n🎮 Configuration:")
    print(f"   - Nombre de cycles: {num_cycles}")
    print(f"   - Capital: {capital} €")
    print(f"   - Itérations/cycle: {iterations}")
    print(f"   - Objectif: {target_return}%")
    print(f"   - Symbole: {symbol}\n")
    
    # Créer et lancer l'optimiseur
    optimizer = AutoOptimizer(symbol=symbol, capital=capital, iterations=iterations)
    best_strategy, best_result = optimizer.run_optimization(num_cycles, target_return)
    
    if best_strategy and best_result:
        print(f"✅ Optimisation terminée avec succès !")
        print(f"🎯 Meilleur résultat: {best_result.total_return:+.2f}%")
    else:
        print(f"⚠️  Aucune stratégie profitable trouvée")
    
    return 0


if __name__ == "__main__":
    sys.exit(main())
