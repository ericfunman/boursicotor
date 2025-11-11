"""
Adaptateur pour utiliser les stratégies EnhancedMA sur la page Cours Live
Permet de générer des signaux avec toutes les stratégies existantes
"""

import pandas as pd
import json
from typing import Dict, List, Tuple, Optional
from backend.models import SessionLocal, Strategy as StrategyModel
from backend.backtesting_engine import EnhancedMovingAverageStrategy
from backend.strategy_manager import StrategyManager


class StrategyAdapter:
    """Adaptateur pour utiliser toutes les stratégies sur la page Cours Live"""
    
    @staticmethod
    def is_simple_strategy(strategy: StrategyModel) -> bool:
        """Vérifie si une stratégie est simple (buy_conditions/sell_conditions)"""
        try:
            params = json.loads(strategy.parameters) if strategy.parameters else {}
            return 'buy_conditions' in params and 'sell_conditions' in params
        except (ValueError, TypeError):
            return False
    
    @staticmethod
    def is_enhanced_strategy(strategy: StrategyModel) -> bool:
        """Vérifie si une stratégie est de type EnhancedMA"""
        return strategy.strategy_type == 'EnhancedMA'
    
    @staticmethod
    def _get_enhanced_ma_indicators(params: dict) -> List[str]:
        """Get indicators for EnhancedMA strategy"""
        indicators = ['MA_Fast', 'MA_Slow', 'ROC', 'ADX', 'Volume_Ratio', 
                     'Momentum', 'Bollinger_Bands']
        
        optional_indicators = {
            'use_supertrend': 'Supertrend',
            'use_parabolic_sar': 'Parabolic_SAR',
            'use_donchian': 'Donchian_Channels',
            'use_vwap': 'VWAP',
            'use_obv': 'OBV',
            'use_cmf': 'CMF',
            'use_elder_ray': 'Elder_Ray'
        }
        
        for param_key, indicator_name in optional_indicators.items():
            if params.get(param_key, False):
                indicators.append(indicator_name)
        
        return indicators
    
    @staticmethod
    def get_strategy_indicators(strategy: StrategyModel) -> List[str]:
        """Retourne la liste des indicateurs utilisés par une stratégie"""
        try:
            params = json.loads(strategy.parameters) if strategy.parameters else {}
            
            # Pour les stratégies simples
            if 'indicators' in params:
                return params['indicators']
            
            # Pour les stratégies EnhancedMA
            if strategy.strategy_type == 'EnhancedMA':
                return StrategyAdapter._get_enhanced_ma_indicators(params)
            
            return []
        except Exception as e:
            print(f"Erreur get_strategy_indicators: {e}")
            return []
    
    @staticmethod
    def _prepare_signal_variables(df: pd.DataFrame, i: int) -> dict:
        """Prepare variables for signal evaluation"""
        return {
            'rsi': df['rsi_14'].iloc[i] if 'rsi_14' in df.columns else None,
            'macd': df['macd'].iloc[i] if 'macd' in df.columns else None,
            'macd_signal': df['macd_signal'].iloc[i] if 'macd_signal' in df.columns else None,
            'price': df['close'].iloc[i],
        }
    
    @staticmethod
    def _evaluate_conditions(params: dict, variables: dict) -> Tuple[bool, bool]:
        """Evaluate buy and sell conditions"""
        buy_condition = False
        sell_condition = False
        
        if 'buy_conditions' in params:
            buy_condition = eval(params['buy_conditions'], variables)
        
        if 'sell_conditions' in params:
            sell_condition = eval(params['sell_conditions'], variables)
        
        return buy_condition, sell_condition
    
    @staticmethod
    def generate_signals_simple(df: pd.DataFrame, strategy: StrategyModel) -> Tuple[List, List, List]:
        """
        Génère des signaux pour une stratégie simple
        
        Returns:
            Tuple (signal_times, signal_prices, signal_types)
        """
        signal_times = []
        _ = []
        signal_types = []
        
        try:
            params = json.loads(strategy.parameters)
            
            # Parcourir toutes les données
            for i in range(1, len(df)):
                try:
                    # Préparer les variables pour eval
                    variables = StrategyAdapter._prepare_signal_variables(df, i)
                    
                    # Évaluer les conditions
                    buy_condition, sell_condition = StrategyAdapter._evaluate_conditions(params, variables)
                    
                    # Ajouter les signaux
                    if buy_condition:
                        signal_times.append(df['time'].iloc[i])
                        signal_prices.append(df['close'].iloc[i])
                        signal_types.append('buy')
                    elif sell_condition:
                        signal_times.append(df['time'].iloc[i])
                        signal_prices.append(df['close'].iloc[i])
                        signal_types.append('sell')
                
                except Exception:
                    continue
        
        except Exception as e:
            print(f"Erreur generate_signals_simple: {e}")
        
        return signal_times, _, signal_types
    
    @staticmethod
    def generate_signals_enhanced(df: pd.DataFrame, strategy: StrategyModel) -> Tuple[List, List, List]:
        """
        Génère des signaux pour une stratégie EnhancedMA
        
        Returns:
            Tuple (signal_times, signal_prices, signal_types)
        """
        signal_times = []
        _ = []
        signal_types = []
        
        try:
            # Charger la stratégie via son ID plutôt que son nom
            strategy_obj = StrategyManager.get_strategy_by_id(strategy.id)
            
            if strategy_obj is None:
                print(f"Impossible de charger la stratégie ID {strategy.id}")
                return signal_times, signal_prices, signal_types
            
            # Préparer le DataFrame avec les colonnes nécessaires
            df_copy = df.copy()
            
            # S'assurer que 'time' est présent
            if 'time' not in df_copy.columns and df_copy.index.name == 'time':
                df_copy = df_copy.reset_index()
            
            # Générer les signaux
            signals = strategy_obj.generate_signals(df_copy)
            
            # Extraire les signaux d'achat et de vente
            for i in range(len(signals)):
                if signals.iloc[i] == 1:  # Signal d'achat
                    signal_times.append(df_copy['time'].iloc[i])
                    signal_prices.append(df_copy['close'].iloc[i])
                    signal_types.append('buy')
                elif signals.iloc[i] == -1:  # Signal de vente
                    signal_times.append(df_copy['time'].iloc[i])
                    signal_prices.append(df_copy['close'].iloc[i])
                    signal_types.append('sell')
        
        except Exception as e:
            print(f"Erreur generate_signals_enhanced: {e}")
            import traceback
            traceback.print_exc()
        
        return signal_times, signal_prices, signal_types
    
    @staticmethod
    def generate_signals(df: pd.DataFrame, strategy: StrategyModel) -> Tuple[List, List, List]:
        """
        Génère des signaux pour n'importe quelle stratégie (simple ou complexe)
        
        Args:
            df: DataFrame avec les données OHLCV et indicateurs
            strategy: Objet Strategy de la base de données
        
        Returns:
            Tuple (signal_times, signal_prices, signal_types)
        """
        if StrategyAdapter.is_simple_strategy(strategy):
            return StrategyAdapter.generate_signals_simple(df, strategy)
        elif StrategyAdapter.is_enhanced_strategy(strategy):
            return StrategyAdapter.generate_signals_enhanced(df, strategy)
        else:
            print(f"Type de stratégie non supporté: {strategy.strategy_type}")
            return [], [], []
    
    @staticmethod
    def get_current_signal(df: pd.DataFrame, strategy: StrategyModel) -> Tuple[str, str]:
        """
        Détermine le signal actuel (pour le dernier point de données)
        
        Returns:
            Tuple (signal_text, signal_color)
            ex: ("ACHAT 🟢 (WLN_42.47%)", "green")
        """
        try:
            # Générer tous les signaux
            signal_times, _, signal_types = StrategyAdapter.generate_signals(df, strategy)
            
            # Vérifier le dernier signal
            if signal_times and len(signal_times) > 0:
                last_signal_time = signal_times[-1]
                last_data_time = df['time'].iloc[-1]
                
                # Tolérance de quelques secondes pour considérer que c'est le signal actuel
                time_diff = abs((last_data_time - last_signal_time).total_seconds())
                
                if time_diff < 60:  # Moins d'une minute de différence
                    if signal_types[-1] == 'buy':
                        return f"ACHAT 🟢 ({strategy.name})", "green"
                    elif signal_types[-1] == 'sell':
                        return f"VENTE 🔴 ({strategy.name})", "red"
            
            return "NEUTRE", "gray"
        
        except Exception as e:
            print(f"Erreur get_current_signal: {e}")
            return "ERREUR", "orange"
    
    @staticmethod
    def _get_active_indicators(params: dict) -> List[str]:
        """Get list of active advanced indicators for EnhancedMA"""
        active_indicators = []
        indicator_map = {
            'use_supertrend': 'Supertrend',
            'use_parabolic_sar': 'Parabolic SAR',
            'use_donchian': 'Donchian',
            'use_vwap': 'VWAP',
            'use_obv': 'OBV',
            'use_cmf': 'CMF',
            'use_elder_ray': 'Elder Ray'
        }
        
        for param_key, indicator_name in indicator_map.items():
            if params.get(param_key, False):
                active_indicators.append(indicator_name)
        
        return active_indicators
    
    @staticmethod
    def format_strategy_info(strategy: StrategyModel) -> Dict:
        """
        Formate les informations d'une stratégie pour affichage
        
        Returns:
            Dict avec type, description, indicateurs, paramètres
        """
        try:
            params = json.loads(strategy.parameters) if strategy.parameters else {}
            indicators = StrategyAdapter.get_strategy_indicators(strategy)
            
            info = {
                'name': strategy.name,
                'type': strategy.strategy_type,
                'description': strategy.description,
                'indicators': indicators,
                'is_simple': StrategyAdapter.is_simple_strategy(strategy),
                'is_enhanced': StrategyAdapter.is_enhanced_strategy(strategy),
            }
            
            # Ajouter les paramètres clés pour EnhancedMA
            if strategy.strategy_type == 'EnhancedMA':
                info['fast_period'] = params.get('fast_period', 'N/A')
                info['slow_period'] = params.get('slow_period', 'N/A')
                info['min_signals'] = params.get('min_signals', 'N/A')
                info['active_advanced_indicators'] = StrategyAdapter._get_active_indicators(params)
            
            # Ajouter les conditions pour stratégies simples
            elif StrategyAdapter.is_simple_strategy(strategy):
                info['buy_conditions'] = params.get('buy_conditions', 'N/A')
                info['sell_conditions'] = params.get('sell_conditions', 'N/A')
            
            return info
        
        except Exception as e:
            print(f"Erreur format_strategy_info: {e}")
            return {
                'name': strategy.name,
                'type': strategy.strategy_type,
                'description': 'Erreur de formatage',
                'indicators': [],
                'is_simple': False,
                'is_enhanced': False,
            }
