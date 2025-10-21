"""
Main Streamlit application for Boursicotor
"""
import streamlit as st
import pandas as pd
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

# IBKR client is optional
try:
    from brokers.ibkr_client import ibkr_client
    IBKR_AVAILABLE = True
except Exception as e:
    logger.warning(f"IBKR not available: {e}")
    IBKR_AVAILABLE = False
    ibkr_client = None

# Saxo Bank client
try:
    from brokers.saxo_client import SaxoClient
    SAXO_AVAILABLE = True
except Exception as e:
    logger.warning(f"Saxo Bank not available: {e}")
    SAXO_AVAILABLE = False

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
        # Try to load existing tokens
        if SAXO_AVAILABLE:
            try:
                with open('.saxo_tokens', 'r') as f:
                    lines = f.readlines()
                    if lines:
                        st.session_state.saxo_client = SaxoClient()
                        access_token = lines[0].split('=')[1].strip()
                        st.session_state.saxo_client.access_token = access_token
                        st.session_state.saxo_client.connected = True
                        st.session_state.saxo_connected = True
                        logger.info("✅ Saxo tokens loaded from file")
            except Exception as e:
                logger.warning(f"No existing Saxo tokens: {e}")
    
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
    st.header("💾 Collecte de Données Saxo Bank")
    
    # Search section
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
                "Ou choisir dans la liste prédéfinie",
                ticker_options,
                format_func=lambda x: f"{x} - {FRENCH_TICKERS[x]}"
            )
            selected_name = FRENCH_TICKERS[selected_ticker]
        
        # Duration
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
        
        if st.button("📊 Collecter les données", type="primary"):
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
                    st.success(f"✅ {inserted} nouveaux enregistrements ajoutés !")
                else:
                    st.info("ℹ️ Données déjà en base ou aucune donnée disponible")
    
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
                st.text(f"{ticker.symbol}: {count:,} points")
        
        finally:
            db.close()
    
    st.markdown("---")
    
    # Visualisation des données collectées
    st.subheader("📈 Visualisation des données")
    
    # Get list of tickers from database or use predefined
    from backend.models import SessionLocal, Ticker as TickerModel
    db = SessionLocal()
    try:
        db_tickers = [t.symbol for t in db.query(TickerModel).all()]
        if db_tickers:
            viz_ticker_options = db_tickers
        else:
            viz_ticker_options = list(FRENCH_TICKERS.keys())
    finally:
        db.close()
    
    viz_ticker = st.selectbox(
        "Ticker à visualiser",
        viz_ticker_options,
        format_func=lambda x: FRENCH_TICKERS.get(x, x),
        key="viz_ticker"
    )
    
    if st.button("📊 Afficher le graphique"):
        from backend.data_collector import DataCollector
        import plotly.graph_objects as go
        
        collector = DataCollector(use_saxo=False)  # No need to connect
        df = collector.get_latest_data(viz_ticker, limit=288)
        
        if df is not None and len(df) > 0:
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
                title=f"{viz_ticker} - {FRENCH_TICKERS.get(viz_ticker, viz_ticker)}",
                xaxis_title="Date/Heure",
                yaxis_title="Prix (EUR)",
                height=500,
                xaxis_rangeslider_visible=False
            )
            
            st.plotly_chart(fig, use_container_width=True)
            
            # Volume chart
            fig_volume = go.Figure(data=[go.Bar(
                x=df.index,
                y=df['volume'],
                name='Volume'
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
        else:
            st.warning("⚠️ Aucune donnée disponible pour ce ticker. Collectez d'abord les données !")


def technical_analysis_page():
    """Technical analysis page"""
    st.header("📈 Analyse Technique")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("Récupération de données historiques")
        
        # Ticker selection
        ticker_options = list(FRENCH_TICKERS.keys())
        selected_ticker = st.selectbox(
            "Sélectionner un ticker",
            ticker_options,
            format_func=lambda x: f"{x} - {FRENCH_TICKERS[x]}"
        )
        
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
                    name=FRENCH_TICKERS[selected_ticker],
                    duration=duration_options[duration],
                    bar_size=bar_size_options[bar_size]
                )
                
                if count > 0:
                    st.success(f"✅ {count} enregistrements ajoutés pour {selected_ticker}")
                else:
                    st.warning("⚠️ Aucune donnée récupérée")
    
    with col2:
        st.subheader("Collecte multiple")
        
        selected_tickers = st.multiselect(
            "Sélectionner plusieurs tickers",
            ticker_options,
            format_func=lambda x: f"{x} - {FRENCH_TICKERS[x]}"
        )
        
        if st.button("📥 Télécharger tous les tickers sélectionnés"):
            if not selected_tickers:
                st.warning("Veuillez sélectionner au moins un ticker")
            else:
                with st.spinner("Téléchargement en cours..."):
                    collector = DataCollector()
                    tickers_list = [(t, FRENCH_TICKERS[t]) for t in selected_tickers]
                    collector.collect_multiple_tickers(
                        tickers_list,
                        duration=duration_options[duration],
                        bar_size=bar_size_options[bar_size]
                    )
                    st.success(f"✅ Données récupérées pour {len(selected_tickers)} tickers")
    
    st.markdown("---")
    
    # Display recent data
    st.subheader("📊 Aperçu des données récentes")
    
    if selected_ticker:
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
                title=f"{selected_ticker} - {FRENCH_TICKERS[selected_ticker]}",
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
    
    # Ticker selection
    ticker_options = list(FRENCH_TICKERS.keys())
    selected_ticker = st.selectbox(
        "Sélectionner un ticker",
        ticker_options,
        format_func=lambda x: f"{x} - {FRENCH_TICKERS[x]}"
    )
    
    # Get data
    collector = DataCollector()
    df = collector.get_latest_data(selected_ticker, limit=500)
    
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
        fig.add_hline(y=70, line_dash="dash", line_color="red", row=2, col=1)
        fig.add_hline(y=30, line_dash="dash", line_color="green", row=2, col=1)
    
    # MACD
    if 'macd' in df.columns:
        fig.add_trace(go.Scatter(x=df.index, y=df['macd'], name='MACD', line=dict(color='blue')), row=3, col=1)
        fig.add_trace(go.Scatter(x=df.index, y=df['macd_signal'], name='Signal', line=dict(color='red')), row=3, col=1)
        fig.add_trace(go.Bar(x=df.index, y=df['macd_hist'], name='Histogram'), row=3, col=1)
    
    # Volume
    fig.add_trace(go.Bar(x=df.index, y=df['volume'], name='Volume'), row=4, col=1)
    
    fig.update_layout(height=1000, showlegend=True, xaxis_rangeslider_visible=False)
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
    st.header("🔙 Backtesting")
    st.info("🚧 Module de backtesting en cours de développement")
    
    st.markdown("""
    ### Fonctionnalités à venir:
    - Sélection de stratégie
    - Période de test configurable
    - Métriques de performance (Sharpe ratio, drawdown, etc.)
    - Visualisation des trades
    - Comparaison de stratégies
    """)


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
