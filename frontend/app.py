"""
Main Streamlit application for Boursicotor
"""
import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from datetime import datetime, timedelta
import sys
import os
from pathlib import Path

# Add parent directory to path
sys.path.append(str(Path(__file__).parent.parent))

from backend.config import logger, FRENCH_TICKERS
from backend.data_collector import DataCollector
from backend.technical_indicators import calculate_and_update_indicators
from backend.models import SessionLocal, Ticker as TickerModel, HistoricalData
from sqlalchemy import func

# IBKR client is optional - loaded lazily to avoid event loop warnings
IBKR_AVAILABLE = False
ibkr_client = None

def get_available_tickers():
    """Get only tickers that have collected data in the database"""
    db = SessionLocal()
    try:
        # Get tickers that have data in historical_data table
        tickers_with_data = db.query(TickerModel.symbol, TickerModel.name).join(
            HistoricalData,
            TickerModel.id == HistoricalData.ticker_id
        ).distinct().all()
        
        # Return as dict {symbol: name}
        return {ticker.symbol: ticker.name for ticker in tickers_with_data}
    except Exception as e:
        logger.error(f"Error getting available tickers: {e}")
        return {}
    finally:
        db.close()

# Saxo Bank client is optional
SAXO_AVAILABLE = False
saxo_client = None

# Page configuration
st.set_page_config(
    page_title="Boursicotor - Trading Algorithmique",
    page_icon="📈",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS
st.markdown("""
    <style>
    .main {
        padding: 0rem 1rem;
    }
    .stMetric {
        background-color: #f0f2f6;
        padding: 10px;
        border-radius: 5px;
    }
    </style>
""", unsafe_allow_html=True)


def main():
    """Main application"""
    st.title("🚀 Boursicotor - Plateforme de Trading Algorithmique")
    st.markdown("---")
    
    # Initialize session state for Saxo client
    if 'saxo_client' not in st.session_state:
        st.session_state.saxo_client = None
        st.session_state.saxo_connected = False
        # Try to load existing tokens (lazy loading)
        try:
            with open('.saxo_tokens', 'r') as f:
                lines = f.readlines()
                if lines:
                    # Import SaxoClient only when needed
                    try:
                        from brokers.saxo_client import SaxoClient
                        st.session_state.saxo_client = SaxoClient()
                        access_token = lines[0].split('=')[1].strip()
                        st.session_state.saxo_client.access_token = access_token
                        st.session_state.saxo_client.connected = True
                        st.session_state.saxo_connected = True
                        logger.info("✅ Saxo tokens loaded from file")
                    except ImportError as ie:
                        logger.debug(f"Saxo client not available: {ie}")
        except FileNotFoundError:
            pass  # No tokens file, normal on first run
        except Exception as e:
            logger.debug(f"Could not load Saxo tokens: {e}")
    
    # Sidebar
    with st.sidebar:
        st.header("⚙️ Configuration")
        
        # Page selection
        page = st.radio(
            "Navigation",
            ["📊 Dashboard", "💾 Collecte de Données", "📈 Analyse Technique", 
             "🔙 Backtesting", "🤖 Trading Automatique", "⚙️ Paramètres"]
        )
        
        st.markdown("---")
        
        # Connection status
        st.subheader("État des connexions")
        
        # Saxo Bank connection
        if SAXO_AVAILABLE:
            if st.session_state.saxo_connected:
                st.success("✅ Saxo Bank Connecté")
                if st.button("🔄 Renouveler connexion Saxo"):
                    st.info("⚠️ Exécutez: python authenticate_saxo.py")
            else:
                st.warning("⚠️ Saxo Bank Déconnecté")
                st.info("📝 Pour vous connecter:\n1. Fermez Streamlit\n2. Exécutez: python authenticate_saxo.py\n3. Relancez Streamlit")
        
        # IBKR connection (legacy)
        if IBKR_AVAILABLE and ibkr_client:
            if st.button("🔌 Connecter à IBKR"):
                with st.spinner("Connexion en cours..."):
                    if ibkr_client.connect():
                        st.success("✅ Connecté à Interactive Brokers")
                    else:
                        st.error("❌ Échec de la connexion")
            
            if ibkr_client.connected:
                st.success("✅ IBKR Connecté")
            else:
                st.warning("⚠️ IBKR Déconnecté")
        
        # Show data source
        st.markdown("---")
        if st.session_state.saxo_connected:
            st.info("📡 Source: **Saxo Bank API**")
        elif IBKR_AVAILABLE and ibkr_client and ibkr_client.connected:
            st.info("📡 Source: **Interactive Brokers**")
        else:
            st.info("📡 Source: **Données simulées**")
    
    # Route to selected page
    if page == "📊 Dashboard":
        dashboard_page()
    elif page == "💾 Collecte de Données":
        data_collection_page()
    elif page == "📈 Analyse Technique":
        technical_analysis_page()
    elif page == "🔙 Backtesting":
        backtesting_page()
    elif page == "🤖 Trading Automatique":
        auto_trading_page()
    elif page == "⚙️ Paramètres":
        settings_page()


def dashboard_page():
    """Dashboard page"""
    st.header("📊 Dashboard")
    
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric("Portefeuille", "10 000 €", "+250 €")
    with col2:
        st.metric("Positions ouvertes", "3", "+1")
    with col3:
        st.metric("Gain journalier", "+2.5%", "+0.5%")
    with col4:
        st.metric("Win Rate", "65%", "+5%")
    
    st.markdown("---")
    
    # Recent trades
    st.subheader("📋 Derniers Trades")
    
    # Placeholder data
    trades_data = {
        "Date": ["2024-01-20 14:30", "2024-01-20 11:15", "2024-01-19 16:45"],
        "Symbole": ["TTE", "WLN", "TTE"],
        "Type": ["ACHAT", "VENTE", "VENTE"],
        "Quantité": [50, 30, 40],
        "Prix": ["62.5 €", "45.2 €", "61.8 €"],
        "P&L": ["+125 €", "+85 €", "-40 €"],
        "Status": ["✅ Fermé", "✅ Fermé", "✅ Fermé"]
    }
    
    st.dataframe(trades_data, use_container_width=True)


def data_collection_page():
    """Data collection page"""
    st.header("💾 Collecte de Données")
    
    # Data source selection
    st.subheader("📡 Source de Données")
    
    col_source1, col_source2 = st.columns(2)
    
    with col_source1:
        data_source = st.radio(
            "Choisir la source",
            ["🏦 Saxo Bank (Temps Réel)", "📊 Yahoo Finance (Historique)", "📈 Alpha Vantage (Historique)", "🔷 Polygon.io (Temps Réel)"],
            help="Saxo Bank: Prix temps réel simulés | Yahoo Finance: Historique massif réel | Alpha Vantage: Historique détaillé | Polygon.io: Données temps réel"
        )
    
    with col_source2:
        if data_source == "🏦 Saxo Bank (Temps Réel)":
            st.info("**Saxo Bank**\n- ✅ Prix temps réel\n- ⚠️ Données simulées (mode démo)\n- 📊 Limite: 1,200 points")
        elif data_source == "📊 Yahoo Finance (Historique)":
            st.success("**Yahoo Finance**\n- ✅ Données réelles\n- ✅ Historique massif (26+ ans)\n- 📊 Aucune limite stricte")
        elif data_source == "📈 Alpha Vantage (Historique)":
            st.success("**Alpha Vantage**\n- ✅ Données réelles\n- ✅ Historique détaillé (20+ ans)\n- 📊 Limite: 5 appels/min, 500/jour")
        else:  # Polygon.io
            st.success("**Polygon.io**\n- ✅ Données temps réel\n- ✅ API moderne et rapide\n- 📊 Limite: 5 appels/min, 2M/jour")
    
    use_yahoo = data_source == "📊 Yahoo Finance (Historique)"
    use_alpha_vantage = data_source == "📈 Alpha Vantage (Historique)"
    use_polygon = data_source == "🔷 Polygon.io (Temps Réel)"
    
    st.markdown("---")
    
    # Search section (available for both sources)
    st.subheader("🔍 Recherche d'actions françaises")
    
    col_search1, col_search2 = st.columns([3, 1])
    
    with col_search1:
        search_query = st.text_input(
            "Rechercher une action (ticker ou nom)",
            placeholder="Ex: GLE, Société Générale, LVMH, MC...",
            help="Entrez le ticker (ex: GLE) ou le nom de la société (ex: Société Générale)"
        )
    
    with col_search2:
        search_button = st.button("🔍 Rechercher", type="secondary", use_container_width=True)
    
    # Initialize session state for search results
    if 'search_results' not in st.session_state:
        st.session_state.search_results = []
    if 'selected_stock' not in st.session_state:
        st.session_state.selected_stock = None
    
    # Perform search
    if search_button and search_query:
        with st.spinner(f"Recherche de '{search_query}'..."):
            try:
                from backend.saxo_search import SaxoInstrumentSearch
                searcher = SaxoInstrumentSearch()
                st.session_state.search_results = searcher.search_french_stocks(search_query, limit=10)
                
                if st.session_state.search_results:
                    st.success(f"✅ {len(st.session_state.search_results)} résultat(s) trouvé(s)")
                else:
                    st.warning("⚠️ Aucune action française trouvée pour cette recherche")
            except Exception as e:
                st.error(f"❌ Erreur lors de la recherche: {e}")
                logger.error(f"Search error: {e}")
        
        # Display search results
        if st.session_state.search_results:
            st.markdown("---")
            st.markdown("**📋 Résultats de recherche:**")
            
            # Create a selection list
            for i, stock in enumerate(st.session_state.search_results):
                col_result1, col_result2 = st.columns([4, 1])
                
                with col_result1:
                    st.markdown(f"""
                    **{stock['ticker']}** - {stock['name']}  
                    <small>Exchange: {stock['exchange']} | Currency: {stock['currency']} | UIC: {stock['uic']}</small>
                    """, unsafe_allow_html=True)
                
                with col_result2:
                    if st.button("Sélectionner", key=f"select_{i}", use_container_width=True):
                        st.session_state.selected_stock = stock
                        st.rerun()
        
        st.markdown("---")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("📥 Récupération de données historiques")
        
        # Ticker selection - either from search or predefined list
        if st.session_state.selected_stock:
            st.info(f"🎯 **Action sélectionnée:** {st.session_state.selected_stock['ticker']} - {st.session_state.selected_stock['name']}")
            selected_ticker = st.session_state.selected_stock['ticker']
            selected_name = st.session_state.selected_stock['name']
            
            if st.button("❌ Effacer la sélection"):
                st.session_state.selected_stock = None
                st.session_state.search_results = []
                st.rerun()
        else:
            # Fallback to predefined list
            ticker_options = list(FRENCH_TICKERS.keys())
            selected_ticker = st.selectbox(
                "Ticker",
                ticker_options,
                format_func=lambda x: f"{x} - {FRENCH_TICKERS[x]}"
            )
            selected_name = FRENCH_TICKERS[selected_ticker]
        
        # Duration and interval options depend on source
        if use_yahoo:
            # Yahoo Finance options
            st.markdown("**Yahoo Finance** - Périodes et intervalles")
            st.info("📊 Yahoo Finance ne supporte pas les intervalles < 1 minute. Utilisez Saxo Bank pour des données à la seconde.")
            
            duration_options = {
                "1 jour": "1d",
                "5 jours": "5d",
                "1 mois": "1mo",
                "3 mois": "3mo",
                "6 mois": "6mo",
                "1 an": "1y",
                "2 ans": "2y",
                "5 ans": "5y",
                "10 ans": "10y",
                "Maximum": "max"
            }
            selected_duration = st.selectbox(
                "Période",
                list(duration_options.keys()),
                index=7,  # Default: 5 ans
                help="Yahoo Finance: 1d à max (26+ ans disponibles)"
            )
            period = duration_options[selected_duration]
            
            # Interval options for Yahoo
            interval_options = {
                "1 minute": "1m",
                "2 minutes": "2m",
                "5 minutes": "5m",
                "15 minutes": "15m",
                "30 minutes": "30m",
                "1 heure": "1h",
                "1 jour": "1d",
                "1 semaine": "1wk",
                "1 mois": "1mo"
            }
            selected_interval = st.selectbox(
                "Intervalle",
                list(interval_options.keys()),
                index=6,  # Default: 1 jour
                help="⚠️ Limitations Yahoo:\n1m: max 7 jours\n2-30m: max 60 jours\n1h+: plusieurs mois\n1d+: illimité"
            )
            interval = interval_options[selected_interval]
            
            # Warning for intraday limitations
            if interval == "1m":
                if selected_duration not in ["1 jour", "5 jours"]:
                    st.error("❌ Intervalle 1 minute limité à 7 jours maximum par Yahoo Finance")
            elif interval in ["2m", "5m", "15m", "30m"]:
                if selected_duration in ["3 mois", "6 mois", "1 an", "2 ans", "5 ans", "10 ans", "Maximum"]:
                    st.warning("⚠️ Ces intervalles sont limités à 60 jours maximum par Yahoo Finance")
            elif interval == "1h":
                if selected_duration in ["2 ans", "5 ans", "10 ans", "Maximum"]:
                    st.warning("⚠️ Intervalle 1 heure: données limitées au-delà de quelques mois")
                    
        elif use_alpha_vantage:
            # Alpha Vantage options
            st.markdown("**Alpha Vantage** - Périodes et intervalles")
            st.info("📈 Alpha Vantage fournit des données historiques détaillées avec limite de 5 appels/minute.")
            
            duration_options = {
                "1 mois": "1M",
                "3 mois": "3M", 
                "6 mois": "6M",
                "1 an": "1Y",
                "2 ans": "2Y",
                "5 ans": "5Y",
                "10 ans": "10Y",
                "20 ans": "20Y"
            }
            selected_duration = st.selectbox(
                "Période",
                list(duration_options.keys()),
                index=3,  # Default: 1 an
                help="Alpha Vantage: historique disponible selon le ticker"
            )
            period = duration_options[selected_duration]
            
            # Interval options for Alpha Vantage
            interval_options = {
                "1 minute": "1min",
                "5 minutes": "5min",
                "15 minutes": "15min",
                "30 minutes": "30min",
                "1 heure": "60min",
                "1 jour": "1day"
            }
            selected_interval = st.selectbox(
                "Intervalle",
                list(interval_options.keys()),
                index=4,  # Default: 1 heure
                help="Alpha Vantage: données intraday limitées aux 1-2 derniers mois"
            )
            interval = interval_options[selected_interval]
            
            if interval != "1day" and selected_duration not in ["1 mois", "3 mois"]:
                st.warning("⚠️ Données intraday limitées aux 1-2 derniers mois par Alpha Vantage")
                
        elif use_polygon:
            # Polygon.io options
            st.markdown("**Polygon.io** - Périodes et intervalles")
            st.info("🔷 Polygon.io fournit des données temps réel avec limite de 5 appels/minute.")
            
            duration_options = {
                "1 jour": "1D",
                "3 jours": "3D",
                "1 semaine": "1W", 
                "2 semaines": "2W",
                "1 mois": "1M",
                "3 mois": "3M",
                "6 mois": "6M"
            }
            selected_duration = st.selectbox(
                "Période",
                list(duration_options.keys()),
                index=2,  # Default: 1 semaine
                help="Polygon.io: données récentes avec historique limité"
            )
            period = duration_options[selected_duration]
            
            # Interval options for Polygon
            interval_options = {
                "1 minute": "1min",
                "5 minutes": "5min",
                "15 minutes": "15min",
                "30 minutes": "30min",
                "1 heure": "1hour",
                "1 jour": "1day"
            }
            selected_interval = st.selectbox(
                "Intervalle",
                list(interval_options.keys()),
                index=0,  # Default: 1 minute
                help="Polygon.io: support complet des intervalles"
            )
            interval = interval_options[selected_interval]
        
        else:
            # Saxo Bank options
            st.markdown("**Saxo Bank** - Durées et intervalles")
            st.info("⚡ Saxo Bank supporte les intervalles à la seconde (1s, 5s, 10s, 30s) mais données simulées en mode démo.")
            
            duration_options = {
                "1 heure": "1H",
                "4 heures": "4H",
                "1 jour": "1D",
                "2 jours": "2D",
                "3 jours": "3D",
                "5 jours": "5D",
                "1 semaine": "1W",
                "2 semaines": "2W",
                "1 mois": "1M",
                "2 mois": "2M",
                "3 mois": "3M",
                "6 mois": "6M",
                "1 an": "1Y"
            }
            selected_duration = st.selectbox(
                "Durée",
                list(duration_options.keys()),
                index=4  # Default: 3 jours
            )
            duration = duration_options[selected_duration]
            
            # Bar size
            bar_size_options = {
                "1 seconde": "1sec",
                "5 secondes": "5sec",
                "10 secondes": "10sec",
                "30 secondes": "30sec",
                "1 minute": "1min",
                "2 minutes": "2min",
                "3 minutes": "3min",
                "5 minutes": "5min",
                "10 minutes": "10min",
                "15 minutes": "15min",
                "30 minutes": "30min",
                "1 heure": "1hour",
                "2 heures": "2hour",
                "4 heures": "4hour",
                "1 jour": "1day",
                "1 semaine": "1week"
            }
            selected_bar_size = st.selectbox(
                "Intervalle",
                list(bar_size_options.keys()),
                index=4  # Default: 1 minute
            )
            bar_size = bar_size_options[selected_bar_size]
        
        # Collect button
        if st.button("📊 Collecter les données", type="primary", use_container_width=True):
            
            if use_yahoo:
                # Yahoo Finance collection with chunking and progress
                from backend.yahoo_finance_collector import YahooFinanceCollector
                
                collector = YahooFinanceCollector()
                
                # Create progress bar and status text
                progress_bar = st.progress(0)
                status_text = st.empty()
                
                # Progress callback
                def update_progress(current, total, message):
                    progress = current / total
                    progress_bar.progress(progress)
                    status_text.text(f"⏳ {message} ({int(progress * 100)}%)")
                
                # Use chunked collection with progress
                inserted = collector.collect_and_store_chunked(
                    symbol=selected_ticker,
                    name=selected_name,
                    period=period,
                    interval=interval,
                    progress_callback=update_progress
                )
                
                # Clear progress indicators
                progress_bar.empty()
                status_text.empty()
                
                if inserted > 0:
                    st.success(f"✅ {inserted} nouveaux enregistrements ajoutés depuis Yahoo Finance !")
                    st.info(f"📊 Source: Yahoo Finance | Période: {selected_duration} | Intervalle: {selected_interval}")
                else:
                    # Check if ticker exists in database
                    from backend.models import SessionLocal, Ticker, HistoricalData
                    db = SessionLocal()
                    try:
                        ticker_obj = db.query(Ticker).filter(Ticker.symbol == selected_ticker).first()
                        if ticker_obj:
                            count = db.query(HistoricalData).filter(HistoricalData.ticker_id == ticker_obj.id).count()
                            st.info(f"ℹ️ Aucune nouvelle donnée. {count} enregistrements déjà présents en base pour {selected_ticker}")
                        else:
                            st.warning(f"⚠️ Aucune donnée disponible pour {selected_ticker}. Vérifiez le ticker ou les paramètres de période/intervalle.")
                    finally:
                        db.close()
                        
            elif use_alpha_vantage:
                # Alpha Vantage collection
                with st.spinner(f"Collecte depuis Alpha Vantage pour {selected_ticker}..."):
                    from backend.data_collector import DataCollector
                    
                    collector = DataCollector(use_saxo=False)  # Don't use Saxo for Alpha Vantage
                    inserted = collector.collect_historical_data(
                        symbol=selected_ticker,
                        name=selected_name,
                        duration=period,
                        bar_size=interval
                    )
                    
                    if inserted > 0:
                        st.success(f"✅ {inserted} nouveaux enregistrements ajoutés depuis Alpha Vantage !")
                        st.info(f"📈 Source: Alpha Vantage | Période: {selected_duration} | Intervalle: {selected_interval}")
                    else:
                        st.warning(f"⚠️ Aucune donnée récupérée depuis Alpha Vantage pour {selected_ticker}")
                        
            elif use_polygon:
                # Polygon.io collection
                with st.spinner(f"Collecte depuis Polygon.io pour {selected_ticker}..."):
                    from backend.data_collector import DataCollector
                    
                    collector = DataCollector(use_saxo=False)  # Don't use Saxo for Polygon
                    inserted = collector.collect_historical_data(
                        symbol=selected_ticker,
                        name=selected_name,
                        duration=period,
                        bar_size=interval
                    )
                    
                    if inserted > 0:
                        st.success(f"✅ {inserted} nouveaux enregistrements ajoutés depuis Polygon.io !")
                        st.info(f"🔷 Source: Polygon.io | Période: {selected_duration} | Intervalle: {selected_interval}")
                    else:
                        st.warning(f"⚠️ Aucune donnée récupérée depuis Polygon.io pour {selected_ticker}")
            
            else:
                # Saxo Bank collection
                with st.spinner(f"Collecte en cours pour {selected_ticker}..."):
                    from backend.data_collector import DataCollector
                    
                    collector = DataCollector(use_saxo=True)
                    inserted = collector.collect_historical_data(
                        symbol=selected_ticker,
                        name=selected_name,
                        duration=duration,
                        bar_size=bar_size
                    )
                    
                    if inserted > 0:
                        st.success(f"✅ {inserted} nouveaux enregistrements ajoutés depuis Saxo Bank !")
                        st.info(f"📊 Source: Saxo Bank (simulé) | Durée: {selected_duration} | Intervalle: {selected_bar_size}")
                    else:
                        # Check if ticker exists in database
                        from backend.models import SessionLocal, Ticker, HistoricalData
                        db = SessionLocal()
                        try:
                            ticker_obj = db.query(Ticker).filter(Ticker.symbol == selected_ticker).first()
                            if ticker_obj:
                                count = db.query(HistoricalData).filter(HistoricalData.ticker_id == ticker_obj.id).count()
                                st.info(f"ℹ️ Aucune nouvelle donnée. {count} enregistrements déjà présents en base pour {selected_ticker}")
                            else:
                                st.warning(f"⚠️ Aucune donnée disponible pour {selected_ticker}. Données simulées car Chart API indisponible en mode démo.")
                        finally:
                            db.close()

    
    with col2:
        st.subheader("📊 Données en base")
        
        from backend.models import SessionLocal, Ticker, HistoricalData
        db = SessionLocal()
        
        try:
            # Statistics
            ticker_count = db.query(Ticker).count()
            data_count = db.query(HistoricalData).count()
            
            st.metric("Tickers", ticker_count)
            st.metric("Points de données", f"{data_count:,}")
            
            # Detail by ticker
            st.markdown("---")
            st.markdown("**Détail par ticker:**")
            
            for ticker in db.query(Ticker).all():
                count = db.query(HistoricalData).filter(
                    HistoricalData.ticker_id == ticker.id
                ).count()
                
                col_ticker, col_delete = st.columns([3, 1])
                with col_ticker:
                    st.text(f"{ticker.symbol}: {count:,} points")
                with col_delete:
                    if st.button("🗑️", key=f"delete_{ticker.symbol}", help=f"Supprimer {ticker.symbol}"):
                        # Confirmation dialog
                        if f"confirm_delete_{ticker.symbol}" not in st.session_state:
                            st.session_state[f"confirm_delete_{ticker.symbol}"] = True
                            st.rerun()
            
            # Handle deletion confirmations
            for ticker in db.query(Ticker).all():
                if st.session_state.get(f"confirm_delete_{ticker.symbol}", False):
                    st.warning(f"⚠️ Confirmer la suppression de **{ticker.symbol}** ?")
                    col_yes, col_no = st.columns(2)
                    
                    with col_yes:
                        if st.button("✅ Oui", key=f"yes_{ticker.symbol}", type="primary"):
                            from backend.yahoo_finance_collector import YahooFinanceCollector
                            result = YahooFinanceCollector.delete_ticker_data(ticker.symbol)
                            
                            if result['success']:
                                st.success(result['message'])
                                del st.session_state[f"confirm_delete_{ticker.symbol}"]
                                st.rerun()
                            else:
                                st.error(result['message'])
                    
                    with col_no:
                        if st.button("❌ Non", key=f"no_{ticker.symbol}"):
                            del st.session_state[f"confirm_delete_{ticker.symbol}"]
                            st.rerun()
        
        finally:
            db.close()
    
    st.markdown("---")
    
    # Visualisation des données collectées
    st.subheader("📈 Visualisation des données")
    
    # Get tickers with collected data
    available_tickers = get_available_tickers()
    
    if not available_tickers:
        st.warning("⚠️ Aucune donnée disponible. Collectez des données d'abord dans l'onglet 'Collecte de Données'.")
        return
    
    col_viz1, col_viz2 = st.columns([2, 1])
    
    with col_viz1:
        viz_ticker = st.selectbox(
            "Ticker à visualiser",
            list(available_tickers.keys()),
            format_func=lambda x: f"{x} - {available_tickers[x]}",
            key="viz_ticker"
        )
    
    with col_viz2:
        # Get date range for this ticker
        db = SessionLocal()
        try:
            ticker_obj = db.query(TickerModel).filter(TickerModel.symbol == viz_ticker).first()
            if ticker_obj:
                min_date_row = db.query(HistoricalData).filter(
                    HistoricalData.ticker_id == ticker_obj.id
                ).order_by(HistoricalData.timestamp.asc()).first()
                
                max_date_row = db.query(HistoricalData).filter(
                    HistoricalData.ticker_id == ticker_obj.id
                ).order_by(HistoricalData.timestamp.desc()).first()
                
                if min_date_row and max_date_row:
                    min_date = min_date_row.timestamp.date()
                    max_date = max_date_row.timestamp.date()
                    
                    # Quick period selector
                    period_options = {
                        "Tout": None,
                        "Dernières 24h": 1,
                        "Derniers 7 jours": 7,
                        "Derniers 30 jours": 30,
                        "Derniers 90 jours": 90,
                        "Personnalisé": "custom"
                    }
                    
                    selected_period = st.selectbox(
                        "Période",
                        list(period_options.keys()),
                        key="viz_period"
                    )
                else:
                    min_date = None
                    max_date = None
                    selected_period = "Tout"
            else:
                min_date = None
                max_date = None
                selected_period = "Tout"
        finally:
            db.close()
    
    # Custom date range if selected
    use_custom_dates = False
    if selected_period == "Personnalisé" and min_date and max_date:
        use_custom_dates = True
        col_date1, col_date2 = st.columns(2)
        
        with col_date1:
            start_date = st.date_input(
                "Date de début",
                value=max_date - pd.Timedelta(days=7),
                min_value=min_date,
                max_value=max_date,
                key="viz_start_date"
            )
        
        with col_date2:
            end_date = st.date_input(
                "Date de fin",
                value=max_date,
                min_value=min_date,
                max_value=max_date,
                key="viz_end_date"
            )
    
    if st.button("📊 Afficher le graphique", use_container_width=True):
        from backend.data_collector import DataCollector
        import plotly.graph_objects as go
        from datetime import datetime, timedelta
        
        # Determine date range
        db = SessionLocal()
        try:
            ticker_obj = db.query(TickerModel).filter(TickerModel.symbol == viz_ticker).first()
            
            if not ticker_obj:
                st.warning(f"⚠️ Aucune donnée disponible pour {viz_ticker}")
            else:
                # Build query
                query = db.query(HistoricalData).filter(HistoricalData.ticker_id == ticker_obj.id)
                
                # Apply date filters
                if use_custom_dates:
                    query = query.filter(
                        HistoricalData.timestamp >= datetime.combine(start_date, datetime.min.time()),
                        HistoricalData.timestamp <= datetime.combine(end_date, datetime.max.time())
                    )
                elif period_options[selected_period] is not None:
                    days = period_options[selected_period]
                    cutoff_date = datetime.now() - timedelta(days=days)
                    query = query.filter(HistoricalData.timestamp >= cutoff_date)
                
                # Execute query
                data = query.order_by(HistoricalData.timestamp.asc()).all()
                
                if not data:
                    st.warning(f"⚠️ Aucune donnée disponible pour la période sélectionnée")
                else:
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
                    
                    st.info(f"📊 {len(df)} points de données affichés")
                    
                    # Create candlestick chart
                    fig = go.Figure(data=[go.Candlestick(
                        x=df.index,
                        open=df['open'],
                        high=df['high'],
                        low=df['low'],
                        close=df['close'],
                        name=viz_ticker
                    )])
                    
                    fig.update_layout(
                        title=f"{viz_ticker} - {available_tickers.get(viz_ticker, viz_ticker)}",
                        xaxis_title="Date/Heure",
                        yaxis_title="Prix (EUR)",
                        height=500,
                        xaxis=dict(rangeslider=dict(visible=False)),
                        hovermode='x'
                    )
                    
                    st.plotly_chart(fig, use_container_width=True)
                    
                    # Volume chart
                    fig_volume = go.Figure(data=[go.Bar(
                        x=df.index,
                        y=df['volume'],
                        name='Volume',
                        marker=dict(color='rgba(100, 150, 255, 0.7)')
                    )])
                    
                    fig_volume.update_layout(
                        title="Volume",
                        xaxis_title="Date/Heure",
                        yaxis_title="Volume",
                        height=200
                    )
                    
                    st.plotly_chart(fig_volume, use_container_width=True)
                    
                    # Statistics
                    col1, col2, col3, col4 = st.columns(4)
                    with col1:
                        st.metric("Prix actuel", f"{df['close'].iloc[-1]:.2f} €")
                    with col2:
                        st.metric("Plus haut", f"{df['high'].max():.2f} €")
                    with col3:
                        st.metric("Plus bas", f"{df['low'].min():.2f} €")
                    with col4:
                        variation = ((df['close'].iloc[-1] - df['close'].iloc[0]) / df['close'].iloc[0]) * 100
                        st.metric("Variation", f"{variation:+.2f}%")
        finally:
            db.close()


def technical_analysis_page():
    """Technical analysis page"""
    st.header("📈 Analyse Technique")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("Récupération de données historiques")
        
        # Get tickers with collected data  
        available_tickers = get_available_tickers()
        
        if not available_tickers:
            st.warning("⚠️ Aucune donnée disponible. Collectez des données d'abord dans l'onglet 'Collecte de Données'.")
            ticker_options = []
        else:
            ticker_options = list(available_tickers.keys())
        
        # Ticker selection
        if ticker_options:
            selected_ticker = st.selectbox(
                "Sélectionner un ticker",
                ticker_options,
                format_func=lambda x: f"{x} - {available_tickers[x]}"
            )
        else:
            st.info("Aucun ticker disponible")
            return
        
        # Duration
        duration_options = {
            "1 jour": "1D",
            "5 jours": "5 D",
            "1 semaine": "1 W",
            "1 mois": "1 M",
            "3 mois": "3 M",
            "6 mois": "6 M",
            "1 an": "1 Y"
        }
        duration = st.selectbox("Durée", list(duration_options.keys()))
        
        # Bar size
        bar_size_options = {
            "1 seconde": "1 secs",
            "5 secondes": "5 secs",
            "10 secondes": "10 secs",
            "30 secondes": "30 secs",
            "1 minute": "1 min",
            "5 minutes": "5 mins",
            "15 minutes": "15 mins",
            "30 minutes": "30 mins",
            "1 heure": "1 hour",
            "1 jour": "1 day"
        }
        bar_size = st.selectbox("Intervalle", list(bar_size_options.keys()))
        
        if st.button("📥 Télécharger les données", type="primary"):
            with st.spinner("Téléchargement en cours..."):
                collector = DataCollector()
                count = collector.collect_historical_data(
                    symbol=selected_ticker,
                    name=available_tickers[selected_ticker],
                    duration=duration_options[duration],
                    bar_size=bar_size_options[bar_size]
                )
                
                if count > 0:
                    st.success(f"✅ {count} enregistrements ajoutés pour {selected_ticker}")
                else:
                    st.warning("⚠️ Aucune donnée récupérée")
    
    with col2:
        st.subheader("Collecte multiple")
        
        if ticker_options:
            selected_tickers = st.multiselect(
                "Sélectionner plusieurs tickers",
                ticker_options,
                format_func=lambda x: f"{x} - {available_tickers[x]}"
            )
        else:
            selected_tickers = []
        
        if st.button("📥 Télécharger tous les tickers sélectionnés"):
            if not selected_tickers:
                st.warning("Veuillez sélectionner au moins un ticker")
            else:
                with st.spinner("Téléchargement en cours..."):
                    collector = DataCollector()
                    tickers_list = [(t, available_tickers[t]) for t in selected_tickers]
                    collector.collect_multiple_tickers(
                        tickers_list,
                        duration=duration_options[duration],
                        bar_size=bar_size_options[bar_size]
                    )
                    st.success(f"✅ Données récupérées pour {len(selected_tickers)} tickers")
    
    st.markdown("---")
    
    # Display recent data
    st.subheader("📊 Aperçu des données récentes")
    
    if selected_ticker and available_tickers:
        collector = DataCollector()
        df = collector.get_latest_data(selected_ticker, limit=100)
        
        if not df.empty:
            # Create candlestick chart
            fig = go.Figure(data=[go.Candlestick(
                x=df.index,
                open=df['open'],
                high=df['high'],
                low=df['low'],
                close=df['close'],
                name=selected_ticker
            )])
            
            fig.update_layout(
                title=f"{selected_ticker} - {available_tickers[selected_ticker]}",
                yaxis_title="Prix (€)",
                xaxis_title="Date",
                height=500
            )
            
            st.plotly_chart(fig, use_container_width=True)
            
            # Data table
            st.dataframe(df.tail(20), use_container_width=True)
        else:
            st.info("Aucune donnée disponible pour ce ticker. Téléchargez des données d'abord.")


def technical_analysis_page():
    """Technical analysis page"""
    st.header("📈 Analyse Technique")
    
    # Get tickers with collected data
    available_tickers = get_available_tickers()
    
    if not available_tickers:
        st.warning("⚠️ Aucune donnée disponible. Collectez des données d'abord dans l'onglet 'Collecte de Données'.")
        return
    
    # Ticker selection
    ticker_options = list(available_tickers.keys())
    selected_ticker = st.selectbox(
        "Sélectionner un ticker",
        ticker_options,
        format_func=lambda x: f"{x} - {available_tickers[x]}"
    )
    
    # Period selection
    period_options = {
        "100 points": 100,
        "200 points": 200,
        "500 points": 500,
        "1000 points": 1000,
        "2000 points": 2000
    }
    selected_period = st.selectbox(
        "Période d'analyse",
        list(period_options.keys()),
        index=2  # Default to 500 points
    )
    limit = period_options[selected_period]
    
    # Get data
    collector = DataCollector()
    df = collector.get_latest_data(selected_ticker, limit=limit)
    
    if df.empty:
        st.warning("⚠️ Aucune donnée disponible. Collectez des données d'abord.")
        return
    
    # Calculate indicators
    with st.spinner("Calcul des indicateurs..."):
        df = calculate_and_update_indicators(df)
    
    # Create subplots
    fig = make_subplots(
        rows=4, cols=1,
        shared_xaxes=True,
        vertical_spacing=0.03,
        subplot_titles=(f'{selected_ticker} - Prix et Moyennes Mobiles', 
                       'RSI', 'MACD', 'Volume'),
        row_heights=[0.5, 0.15, 0.15, 0.2]
    )
    
    # Candlestick
    fig.add_trace(
        go.Candlestick(
            x=df.index, open=df['open'], high=df['high'],
            low=df['low'], close=df['close'], name='Prix'
        ),
        row=1, col=1
    )
    
    # Moving averages
    if 'sma_20' in df.columns:
        fig.add_trace(go.Scatter(x=df.index, y=df['sma_20'], name='SMA 20', line=dict(color='orange')), row=1, col=1)
    if 'sma_50' in df.columns:
        fig.add_trace(go.Scatter(x=df.index, y=df['sma_50'], name='SMA 50', line=dict(color='blue')), row=1, col=1)
    
    # Bollinger Bands
    if 'bb_upper' in df.columns:
        fig.add_trace(go.Scatter(x=df.index, y=df['bb_upper'], name='BB Upper', line=dict(color='gray', dash='dash')), row=1, col=1)
        fig.add_trace(go.Scatter(x=df.index, y=df['bb_lower'], name='BB Lower', line=dict(color='gray', dash='dash')), row=1, col=1)
    
    # RSI
    if 'rsi_14' in df.columns:
        fig.add_trace(go.Scatter(x=df.index, y=df['rsi_14'], name='RSI', line=dict(color='purple')), row=2, col=1)
        fig.add_hline(y=70, line=dict(dash="dash", color="red"), row=2, col=1)
        fig.add_hline(y=30, line=dict(dash="dash", color="green"), row=2, col=1)
    
    # MACD
    if 'macd' in df.columns:
        fig.add_trace(go.Scatter(x=df.index, y=df['macd'], name='MACD', line=dict(color='blue')), row=3, col=1)
        fig.add_trace(go.Scatter(x=df.index, y=df['macd_signal'], name='Signal', line=dict(color='red')), row=3, col=1)
        fig.add_trace(go.Bar(x=df.index, y=df['macd_hist'], name='Histogram'), row=3, col=1)
    
    # Volume
    fig.add_trace(go.Bar(x=df.index, y=df['volume'], name='Volume'), row=4, col=1)
    
    fig.update_layout(height=1000, showlegend=True, xaxis=dict(rangeslider=dict(visible=False)))
    st.plotly_chart(fig, use_container_width=True)
    
    # Indicator values
    st.subheader("📊 Valeurs actuelles des indicateurs")
    
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        if 'rsi_14' in df.columns:
            rsi_value = df['rsi_14'].iloc[-1]
            st.metric("RSI (14)", f"{rsi_value:.2f}", 
                     "Suracheté" if rsi_value > 70 else "Survendu" if rsi_value < 30 else "Neutre")
    
    with col2:
        if 'macd' in df.columns:
            macd_value = df['macd'].iloc[-1]
            st.metric("MACD", f"{macd_value:.4f}")
    
    with col3:
        if 'sma_20' in df.columns and 'close' in df.columns:
            sma_diff = ((df['close'].iloc[-1] - df['sma_20'].iloc[-1]) / df['sma_20'].iloc[-1]) * 100
            st.metric("Prix vs SMA20", f"{sma_diff:+.2f}%")
    
    with col4:
        if 'bb_percent' in df.columns:
            bb_pct = df['bb_percent'].iloc[-1] * 100
            st.metric("Position BB", f"{bb_pct:.1f}%")


def backtesting_page():
    """Backtesting page"""
    st.header("🔙 Backtesting & Génération de Stratégies")
    
    # Import necessary modules
    from backend.models import SessionLocal, Ticker as TickerModel, HistoricalData
    from backend.strategy_manager import StrategyManager
    
    # Tabs for different sections
    tab1, tab2, tab3 = st.tabs(["🔍 Générer Stratégie", "💾 Stratégies Sauvegardées", "🔄 Rejouer Stratégie"])
    
    with tab1:
        st.subheader("🔍 Recherche de Stratégie Profitable")
        st.info("L'algorithme va tester différentes stratégies jusqu'à trouver un gain ≥ 10% (ou arrêt après 100 itérations)")
        
        # Get tickers with collected data
        available_tickers = get_available_tickers()
        
        if not available_tickers:
            st.warning("⚠️ Aucune donnée disponible. Collectez d'abord des données historiques dans l'onglet 'Collecte de Données'.")
            return
        
        col1, col2 = st.columns(2)
        
        with col1:
            selected_ticker = st.selectbox(
                "Action",
                list(available_tickers.keys()),
                format_func=lambda x: f"{x} - {available_tickers[x]}",
                key="backtest_ticker"
            )
        
        with col2:
            # Get date range for ticker
            db = SessionLocal()
            try:
                ticker_obj = db.query(TickerModel).filter(TickerModel.symbol == selected_ticker).first()
                if ticker_obj:
                    count = db.query(HistoricalData).filter(HistoricalData.ticker_id == ticker_obj.id).count()
                    st.metric("Points de données", f"{count:,}")
            finally:
                db.close()
        
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            initial_capital = st.number_input(
                "Capital initial (€)",
                min_value=1000.0,
                max_value=1000000.0,
                value=10000.0,
                step=1000.0
            )
        
        with col2:
            target_return = st.number_input(
                "Objectif de gain (%)",
                min_value=1.0,
                max_value=100.0,
                value=10.0,
                step=1.0
            )
        
        with col3:
            commission_pct = st.number_input(
                "Commission (%)",
                min_value=0.0,
                max_value=5.0,
                value=0.09,
                step=0.01,
                format="%.2f",
                help="Commission par trade (achat + vente)"
            )
        
        with col4:
            max_iterations = st.number_input(
                "Max itérations",
                min_value=10,
                max_value=5000,
                value=2000,
                step=100
            )
        
        # Button to start optimization
        if st.button("🚀 Lancer la recherche", type="primary", use_container_width=True):
            # Clear previous results
            st.session_state.best_strategy = None
            st.session_state.best_result = None
            st.session_state.best_return = None
            st.session_state.selected_ticker = None
            st.session_state.save_status = None
            
            from backend.backtesting_engine import StrategyGenerator, BacktestingEngine
            
            with st.spinner(f"Recherche en cours sur {selected_ticker}..."):
                # Load data
                db = SessionLocal()
                try:
                    ticker = db.query(TickerModel).filter(TickerModel.symbol == selected_ticker).first()
                    
                    if not ticker:
                        st.error(f"Ticker {selected_ticker} not found")
                        return
                    
                    # Get all data
                    data = db.query(HistoricalData).filter(
                        HistoricalData.ticker_id == ticker.id
                    ).order_by(HistoricalData.timestamp.asc()).all()
                    
                    if len(data) < 100:
                        st.error("Pas assez de données (minimum 100 points requis)")
                        return
                    
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
                    
                    st.info(f"📊 {len(df)} points chargés pour l'analyse")
                    
                    # Progress bar
                    progress_bar = st.progress(0)
                    status_text = st.empty()
                    results_container = st.empty()
                    
                    # Search for strategy
                    generator = StrategyGenerator(target_return=target_return)
                    
                    best_return = -np.inf
                    best_strategy = None
                    best_result = None
                    iterations_done = 0
                    
                    for i in range(max_iterations):
                        iterations_done = i + 1
                        progress = (i + 1) / max_iterations
                        progress_bar.progress(progress)
                        
                        # Generate random strategy - Include EnhancedMA
                        strategy_type = np.random.choice(['ma', 'rsi', 'multi', 'enhanced'])
                        
                        if strategy_type == 'ma':
                            from backend.backtesting_engine import MovingAverageCrossover
                            fast = np.random.randint(5, 20)
                            slow = np.random.randint(fast + 5, 50)
                            strategy = MovingAverageCrossover(fast_period=fast, slow_period=slow)
                        elif strategy_type == 'rsi':
                            from backend.backtesting_engine import RSIStrategy
                            period = np.random.randint(10, 20)
                            oversold = np.random.randint(20, 35)
                            overbought = np.random.randint(65, 80)
                            strategy = RSIStrategy(rsi_period=period, oversold=oversold, overbought=overbought)
                        elif strategy_type == 'multi':
                            from backend.backtesting_engine import MultiIndicatorStrategy
                            strategy = MultiIndicatorStrategy(
                                ma_fast=np.random.randint(5, 15),
                                ma_slow=np.random.randint(20, 40),
                                rsi_period=np.random.randint(10, 20),
                                rsi_oversold=np.random.randint(20, 35),
                                rsi_overbought=np.random.randint(65, 80)
                            )
                        else:  # enhanced
                            from backend.backtesting_engine import EnhancedMovingAverageStrategy
                            
                            # Randomly decide which ultra-complex indicators to use
                            use_supertrend = np.random.choice([True, False])
                            use_parabolic_sar = np.random.choice([True, False])
                            use_donchian = np.random.choice([True, False])
                            use_vwap = np.random.choice([True, False])
                            use_obv = np.random.choice([True, False])
                            use_cmf = np.random.choice([True, False])
                            use_elder_ray = np.random.choice([True, False])
                            
                            strategy = EnhancedMovingAverageStrategy(
                                fast_period=np.random.randint(15, 25),
                                slow_period=np.random.randint(35, 50),
                                roc_period=np.random.choice([10, 14]),
                                roc_threshold=np.random.uniform(1.0, 4.0),
                                adx_period=np.random.choice([14, 20]),
                                adx_threshold=np.random.randint(20, 35),
                                volume_ratio_short=np.random.choice([3, 5, 10]),
                                volume_ratio_long=np.random.choice([15, 20, 30]),
                                volume_threshold=np.random.uniform(1.1, 1.5),
                                momentum_period=np.random.choice([10, 14]),
                                momentum_threshold=np.random.uniform(0.5, 2.0),
                                bb_period=np.random.choice([20, 25]),
                                bb_width_threshold=np.random.uniform(0.03, 0.08),
                                use_supertrend=use_supertrend,
                                supertrend_period=np.random.choice([10, 14, 20]) if use_supertrend else 10,
                                supertrend_multiplier=np.random.uniform(2.0, 4.0) if use_supertrend else 3.0,
                                use_parabolic_sar=use_parabolic_sar,
                                use_donchian=use_donchian,
                                donchian_period=np.random.choice([20, 30, 40]) if use_donchian else 20,
                                donchian_threshold=np.random.uniform(0.02, 0.06) if use_donchian else 0.04,
                                use_vwap=use_vwap,
                                use_obv=use_obv,
                                use_cmf=use_cmf,
                                cmf_period=np.random.choice([14, 20, 21]) if use_cmf else 20,
                                cmf_threshold=np.random.uniform(0.0, 0.15) if use_cmf else 0.05,
                                use_elder_ray=use_elder_ray,
                                elder_ray_period=np.random.choice([13, 21, 34]) if use_elder_ray else 13,
                                min_signals=np.random.randint(2, 6)
                            )
                        
                        # Run backtest with custom commission
                        commission_decimal = commission_pct / 100  # Convert % to decimal (0.09% → 0.0009)
                        engine = BacktestingEngine(
                            initial_capital=initial_capital,
                            commission=commission_decimal,
                            allow_short=True
                        )
                        result = engine.run_backtest(df, strategy, selected_ticker)
                        
                        # Update best if this result is better
                        if result.total_return > best_return:
                            best_return = result.total_return
                            best_strategy = strategy
                            best_result = result
                            
                            with results_container.container():
                                col_a, col_b, col_c = st.columns(3)
                                with col_a:
                                    st.metric("Meilleur retour", f"{best_return:.2f}%")
                                with col_b:
                                    st.metric("Itération", f"{iterations_done}/{max_iterations}")
                                with col_c:
                                    st.metric("Win Rate", f"{best_result.win_rate:.1f}%")
                        
                        # Show progress (continue through all iterations)
                        objective_status = "🎯 Objectif atteint!" if best_return >= target_return else "⏳ Recherche en cours..."
                        status_text.text(f"{objective_status} | Itération {iterations_done}/{max_iterations} | Meilleur: {best_return:.2f}%")
                    
                    # All iterations complete - display best result
                    progress_bar.progress(1.0)
                    status_text.empty()
                    
                    if best_result and best_strategy:
                        # Save to session state for persistence across reruns
                        st.session_state.best_strategy = best_strategy
                        st.session_state.best_result = best_result
                        st.session_state.best_return = best_return
                        st.session_state.selected_ticker = selected_ticker
                        
                        if best_return >= target_return:
                            st.success(f"🎯 Objectif atteint ! Meilleure stratégie : {best_return:.2f}%")
                        else:
                            st.warning(f"⚠️ Objectif non atteint après {max_iterations} itérations")
                            st.info(f"Meilleur résultat obtenu : {best_return:.2f}%")
                        
                        st.info("� Résultats affichés ci-dessous")
                    else:
                        st.error("Aucune stratégie n'a pu être générée")
                
                finally:
                    db.close()
        
        # Display results if they exist in session state (outside button block)
        if 'best_strategy' in st.session_state and st.session_state.best_strategy is not None:
            best_strategy = st.session_state.best_strategy
            best_result = st.session_state.best_result
            best_return = st.session_state.best_return
            selected_ticker = st.session_state.selected_ticker
            
            st.markdown("---")
            st.subheader("✅ Meilleure Stratégie Trouvée")
            
            col1, col2, col3, col4 = st.columns(4)
            with col1:
                st.metric("Retour Total", f"{best_result.total_return:.2f}%", 
                         delta=f"{best_result.total_return - target_return:.2f}%")
            with col2:
                st.metric("Capital Final", f"{best_result.final_capital:.2f}€",
                         delta=f"{best_result.final_capital - initial_capital:.2f}€")
            with col3:
                st.metric("Trades", best_result.total_trades)
            with col4:
                st.metric("Win Rate", f"{best_result.win_rate:.1f}%")
            
            col1, col2, col3 = st.columns(3)
            with col1:
                st.metric("Sharpe Ratio", f"{best_result.sharpe_ratio:.2f}")
            with col2:
                st.metric("Max Drawdown", f"{best_result.max_drawdown:.2f}%")
            with col3:
                st.metric("Winning/Losing", f"{best_result.winning_trades}/{best_result.losing_trades}")
            
            # Strategy details
            st.markdown("---")
            st.markdown("**📋 Détails de la stratégie:**")
            st.json(best_strategy.to_dict())
            
            # Save strategy button
            st.markdown("---")
            ticker_name = selected_ticker.replace('.PA', '')  # Remove .PA suffix
            suggested_name = f"{ticker_name}_{best_return:.2f}%"
            
            # Initialize session state for save status
            if 'save_status' not in st.session_state:
                st.session_state.save_status = None
            
            strategy_name = st.text_input(
                "Nom de la stratégie à sauvegarder",
                value=suggested_name,
                key="strategy_save_name"
            )
            
            # Debug info
            st.caption(f"📝 Nom actuel : {strategy_name}")
            
            if st.button("💾 Sauvegarder la stratégie", type="primary", key="save_strategy_btn", use_container_width=True):
                # Log button click
                logger.info(f"Save button clicked for strategy: {strategy_name}")
                
                # Update strategy name before saving
                best_strategy.name = strategy_name
                try:
                    with st.spinner(f"Sauvegarde de '{strategy_name}'..."):
                        logger.info(f"Calling StrategyManager.save_strategy...")
                        strategy_id = StrategyManager.save_strategy(best_strategy, best_result)
                        logger.info(f"Save returned ID: {strategy_id}")
                    
                    if strategy_id:
                        st.session_state.save_status = ('success', strategy_name, strategy_id)
                        st.rerun()  # Rerun to show success message
                    else:
                        st.session_state.save_status = ('error', strategy_name, None)
                except Exception as e:
                    import traceback
                    logger.error(f"Exception during save: {e}")
                    logger.error(traceback.format_exc())
                    st.session_state.save_status = ('exception', strategy_name, str(e), traceback.format_exc())
            
            # Display save status
            if st.session_state.save_status:
                status = st.session_state.save_status
                if status[0] == 'success':
                    st.success(f"✅ Stratégie '{status[1]}' sauvegardée avec succès ! (ID: {status[2]})")
                    st.info("👉 Consultez l'onglet 'Stratégies Sauvegardées' pour la retrouver")
                    if st.button("🔄 Nouvelle optimisation", key="reset_opt"):
                        st.session_state.best_strategy = None
                        st.session_state.best_result = None
                        st.session_state.best_return = None
                        st.session_state.selected_ticker = None
                        st.session_state.save_status = None
                        st.rerun()
                elif status[0] == 'error':
                    st.error(f"❌ Erreur lors de la sauvegarde de '{status[1]}' (ID None)")
                    st.error("Vérifiez les logs pour plus de détails")
                elif status[0] == 'exception':
                    st.error(f"❌ Exception lors de la sauvegarde de '{status[1]}' : {status[2]}")
                    with st.expander("Voir le détail de l'erreur"):
                        st.code(status[3])
            
            # Trades table
            if best_result.trades:
                st.markdown("**📈 Historique des trades:**")
                trades_df = pd.DataFrame(best_result.trades)
                trades_df['entry_date'] = pd.to_datetime(trades_df['entry_date'])
                trades_df['exit_date'] = pd.to_datetime(trades_df['exit_date'])
                st.dataframe(trades_df, use_container_width=True)
    
    with tab2:
        st.subheader("💾 Stratégies Sauvegardées")
        
        # Add refresh button
        col_refresh1, col_refresh2 = st.columns([1, 5])
        with col_refresh1:
            if st.button("🔄 Rafraîchir", key="refresh_strategies"):
                st.rerun()
        
        from backend.strategy_manager import StrategyManager
        
        try:
            strategies = StrategyManager.get_all_strategies()
        except Exception as e:
            st.error(f"Erreur lors du chargement des stratégies : {str(e)}")
            import traceback
            st.code(traceback.format_exc())
            strategies = []
        
        if not strategies:
            st.info("Aucune stratégie sauvegardée. Générez-en une dans l'onglet 'Générer Stratégie'.")
        else:
            st.write(f"**{len(strategies)} stratégie(s) trouvée(s)**")
            for strat in strategies:
                with st.expander(f"📊 {strat['name']} - {strat['type']}", expanded=False):
                    col1, col2, col3, col4 = st.columns(4)
                    
                    with col1:
                        st.metric("Dernier retour", f"{strat['latest_return']:.2f}%" if strat['latest_return'] else "N/A")
                    with col2:
                        st.metric("Win Rate", f"{strat['latest_win_rate']:.1f}%" if strat['latest_win_rate'] else "N/A")
                    with col3:
                        st.metric("Backtests", strat['total_backtests'])
                    with col4:
                        st.metric("Active", "✅" if strat['is_active'] else "❌")
                    
                    st.markdown("**Description:**")
                    st.write(strat['description'])
                    
                    st.markdown("**Paramètres:**")
                    st.json(strat['parameters'])
                    
                    # Actions
                    col_a, col_b = st.columns(2)
                    with col_a:
                        if st.button(f"📊 Voir backtests", key=f"view_{strat['id']}"):
                            backtests = StrategyManager.get_strategy_backtests(strat['id'])
                            if backtests:
                                st.dataframe(pd.DataFrame(backtests), use_container_width=True)
                    
                    with col_b:
                        if st.button(f"🗑️ Supprimer", key=f"delete_{strat['id']}", type="secondary"):
                            try:
                                if StrategyManager.delete_strategy(strat['id']):
                                    st.success(f"✅ Stratégie '{strat['name']}' supprimée avec succès")
                                    st.rerun()
                                else:
                                    st.error("❌ Erreur lors de la suppression")
                            except Exception as e:
                                st.error(f"❌ Erreur : {str(e)}")
    
    with tab3:
        st.subheader("🔄 Rejouer une Stratégie")
        
        from backend.strategy_manager import StrategyManager
        
        strategies = StrategyManager.get_all_strategies()
        
        if not strategies:
            st.info("Aucune stratégie disponible. Générez-en une d'abord.")
        else:
            strategy_options = {f"{s['name']} ({s['type']})": s['id'] for s in strategies}
            
            selected_strategy_name = st.selectbox(
                "Stratégie à rejouer",
                list(strategy_options.keys())
            )
            
            selected_strategy_id = strategy_options[selected_strategy_name]
            
            # Get tickers with collected data
            available_tickers = get_available_tickers()
            
            if not available_tickers:
                st.warning("⚠️ Aucune donnée disponible. Collectez d'abord des données historiques dans l'onglet 'Collecte de Données'.")
                return
            
            col1, col2 = st.columns(2)
            
            with col1:
                replay_ticker = st.selectbox(
                    "Action",
                    list(available_tickers.keys()),
                    format_func=lambda x: f"{x} - {available_tickers[x]}",
                    key="replay_ticker"
                )
            
            with col2:
                replay_capital = st.number_input(
                    "Capital initial (€)",
                    min_value=1000.0,
                    max_value=1000000.0,
                    value=10000.0,
                    step=1000.0,
                    key="replay_capital"
                )
            
            # Date range
            db = SessionLocal()
            try:
                ticker_obj = db.query(TickerModel).filter(TickerModel.symbol == replay_ticker).first()
                if ticker_obj:
                    min_date_row = db.query(HistoricalData).filter(
                        HistoricalData.ticker_id == ticker_obj.id
                    ).order_by(HistoricalData.timestamp.asc()).first()
                    
                    max_date_row = db.query(HistoricalData).filter(
                        HistoricalData.ticker_id == ticker_obj.id
                    ).order_by(HistoricalData.timestamp.desc()).first()
                    
                    if min_date_row and max_date_row:
                        col1, col2 = st.columns(2)
                        
                        with col1:
                            start_date = st.date_input(
                                "Date de début",
                                value=min_date_row.timestamp.date(),
                                min_value=min_date_row.timestamp.date(),
                                max_value=max_date_row.timestamp.date()
                            )
                        
                        with col2:
                            end_date = st.date_input(
                                "Date de fin",
                                value=max_date_row.timestamp.date(),
                                min_value=min_date_row.timestamp.date(),
                                max_value=max_date_row.timestamp.date()
                            )
            finally:
                db.close()
            
            if st.button("▶️ Lancer le backtest", type="primary", use_container_width=True):
                from datetime import datetime
                
                with st.spinner("Exécution du backtest..."):
                    result = StrategyManager.replay_strategy(
                        strategy_id=selected_strategy_id,
                        symbol=replay_ticker,
                        start_date=datetime.combine(start_date, datetime.min.time()),
                        end_date=datetime.combine(end_date, datetime.max.time()),
                        initial_capital=replay_capital
                    )
                    
                    if result:
                        st.success("✅ Backtest terminé !")
                        
                        # Display results
                        col1, col2, col3, col4 = st.columns(4)
                        with col1:
                            st.metric("Retour Total", f"{result.total_return:.2f}%")
                        with col2:
                            st.metric("Capital Final", f"{result.final_capital:.2f}€")
                        with col3:
                            st.metric("Trades", result.total_trades)
                        with col4:
                            st.metric("Win Rate", f"{result.win_rate:.1f}%")
                        
                        # Additional metrics
                        col1, col2, col3 = st.columns(3)
                        with col1:
                            st.metric("Sharpe Ratio", f"{result.sharpe_ratio:.2f}")
                        with col2:
                            st.metric("Max Drawdown", f"{result.max_drawdown:.2f}%")
                        with col3:
                            st.metric("Winning/Losing", f"{result.winning_trades}/{result.losing_trades}")
                        
                        # Trades
                        if result.trades:
                            st.markdown("---")
                            st.markdown("**📈 Historique des trades:**")
                            trades_df = pd.DataFrame(result.trades)
                            trades_df['entry_date'] = pd.to_datetime(trades_df['entry_date'])
                            trades_df['exit_date'] = pd.to_datetime(trades_df['exit_date'])
                            st.dataframe(trades_df, use_container_width=True)
                        
                        # Save replayed strategy option
                        st.markdown("---")
                        st.markdown("**💾 Sauvegarder cette stratégie appliquée à une nouvelle action**")
                        
                        col1, col2 = st.columns([2, 1])
                        with col1:
                            new_strategy_name = st.text_input(
                                "Nom de la nouvelle stratégie",
                                value=f"{selected_strategy_name}_{replay_ticker}_{result.total_return:.1f}%",
                                help="Donnez un nom descriptif à cette stratégie appliquée à une nouvelle action"
                            )
                        
                        with col2:
                            if st.button("💾 Sauvegarder", type="primary", use_container_width=True):
                                try:
                                    # Get original strategy
                                    from backend.strategy_manager import StrategyManager
                                    original_strategy = StrategyManager.get_strategy_by_id(selected_strategy_id)
                                    
                                    if original_strategy:
                                        # Create new strategy with updated description
                                        new_description = f"""Stratégie dérivée de '{selected_strategy_name}'
                                        
📊 Résultats originaux ({original_strategy.description.split('(')[1].split(')')[0] if '(' in original_strategy.description else 'N/A'}):
{original_strategy.description}

🔄 Appliquée à {replay_ticker} - {available_tickers.get(replay_ticker, replay_ticker)}:
- Retour Total: {result.total_return:.2f}%
- Capital Final: {result.final_capital:.2f}€
- Nombre de trades: {result.total_trades}
- Win Rate: {result.win_rate:.1f}%
- Sharpe Ratio: {result.sharpe_ratio:.2f}
- Max Drawdown: {result.max_drawdown:.2f}%"""

                                        # Create new strategy with same parameters but new name and description
                                        # Copy all attributes except name and description
                                        strategy_params = {k: v for k, v in original_strategy.__dict__.items() 
                                                          if k not in ['name', 'description', 'parameters']}
                                        
                                        # Debug logging
                                        logger.info(f"New strategy name: {new_strategy_name}")
                                        logger.info(f"Strategy params keys: {list(strategy_params.keys())}")
                                        
                                        # Create new strategy instance with custom name and description
                                        new_strategy = original_strategy.__class__(
                                            name=new_strategy_name,
                                            description=new_description,
                                            **strategy_params
                                        )
                                        
                                        # Verify the name is set
                                        logger.info(f"Created strategy with name: {new_strategy.name}")
                                        logger.info(f"Created strategy with description: {new_strategy.description[:50]}...")
                                        
                                        # Save the new strategy
                                        saved_id = StrategyManager.save_strategy(new_strategy, result)
                                        
                                        if saved_id:
                                            st.success(f"✅ Stratégie '{new_strategy_name}' sauvegardée avec succès ! (ID: {saved_id})")
                                            st.info("👉 Consultez l'onglet 'Stratégies Sauvegardées' pour la retrouver")
                                            st.balloons()
                                        else:
                                            st.error("❌ Erreur lors de la sauvegarde")
                                    else:
                                        st.error("❌ Stratégie originale introuvable")
                                        
                                except Exception as e:
                                    st.error(f"❌ Erreur: {str(e)}")
                                    logger.error(f"Error saving replayed strategy: {e}")
                        
                    else:
                        st.error("Erreur lors de l'exécution du backtest")


def auto_trading_page():
    """Auto trading page"""
    st.header("🤖 Trading Automatique")
    st.warning("⚠️ Mode Paper Trading activé")
    
    st.info("🚧 Module de trading automatique en cours de développement")
    
    st.markdown("""
    ### Fonctionnalités à venir:
    - Configuration des stratégies actives
    - Gestion des risques (stop-loss, take-profit)
    - Monitoring en temps réel
    - Alertes et notifications
    - Historique des trades automatiques
    """)


def settings_page():
    """Settings page"""
    st.header("⚙️ Paramètres")
    
    st.subheader("🏦 Configuration Saxo Bank")
    
    # Saxo Bank connection info
    col1, col2 = st.columns(2)
    
    with col1:
        st.text_input("Base URL", value=os.getenv("SAXO_BASE_URL", "https://gateway.saxobank.com/sim/openapi"), disabled=True)
        st.text_input("App Key", value=os.getenv("SAXO_APP_KEY", "")[:20] + "...", disabled=True, type="password")
    
    with col2:
        st.text_input("Auth URL", value=os.getenv("SAXO_AUTH_URL", "https://sim.logonvalidation.net"), disabled=True)
        st.text_input("Redirect URI", value=os.getenv("SAXO_REDIRECT_URI", "http://localhost:8501/callback"), disabled=True)
    
    # Connection status
    st.markdown("---")
    st.subheader("📡 État de la connexion")
    
    if st.session_state.saxo_connected:
        st.success("✅ Connecté à Saxo Bank (Mode Simulation)")
        
        # Token info
        try:
            with open('.saxo_tokens', 'r') as f:
                lines = f.readlines()
                if len(lines) >= 3:
                    expires_at_str = lines[2].split('=')[1].strip()
                    from datetime import datetime
                    expires_at = datetime.fromisoformat(expires_at_str)
                    time_left = expires_at - datetime.now()
                    
                    if time_left.total_seconds() > 0:
                        hours_left = int(time_left.total_seconds() // 3600)
                        minutes_left = int((time_left.total_seconds() % 3600) // 60)
                        st.info(f"⏱️ Token expire dans : {hours_left}h {minutes_left}min")
                    else:
                        st.warning("⚠️ Token expiré - Veuillez vous reconnecter")
        except Exception as e:
            st.warning("⚠️ Impossible de lire les informations du token")
        
        if st.button("🔄 Renouveler l'authentification"):
            st.info("Pour renouveler l'authentification :\n1. Fermez Streamlit\n2. Exécutez: `python authenticate_saxo.py`\n3. Relancez Streamlit")
    else:
        st.error("❌ Non connecté à Saxo Bank")
        st.info("Pour vous connecter :\n1. Fermez Streamlit\n2. Exécutez: `python authenticate_saxo.py`\n3. Suivez les instructions\n4. Relancez Streamlit")
    
    st.markdown("---")
    
    st.subheader("⚙️ Configuration de Trading")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.checkbox("Mode Simulation", value=True, disabled=True, help="Mode simulation Saxo Bank activé par défaut")
        st.number_input("Taille maximale de position (€)", value=10000, step=1000)
    
    with col2:
        st.slider("Risque par trade (%)", min_value=0.5, max_value=5.0, value=2.0, step=0.5)
        st.slider("Stop-loss (%)", min_value=1.0, max_value=10.0, value=5.0, step=0.5)
    
    st.markdown("---")
    
    st.subheader("📊 Paramètres de collecte de données")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.number_input("Délai entre requêtes (secondes)", value=1, min_value=0, max_value=10, help="Délai pour éviter le rate limiting de l'API Saxo Bank")
    
    with col2:
        st.checkbox("Utiliser données simulées si API échoue", value=True, help="Génère des données réalistes si l'API Chart n'est pas disponible")
    
    st.info("ℹ️ **Limite API Saxo Bank** : Maximum 1200 points par requête (contrainte de l'API)")
    
    if st.button("💾 Sauvegarder les paramètres"):
        st.success("✅ Paramètres sauvegardés")


if __name__ == "__main__":
    main()
