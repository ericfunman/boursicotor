"""
Main Streamlit application for Boursicotor
"""
import streamlit as st
import pandas as pd
import numpy as np
from numpy.random import default_rng
_rng_frontend = default_rng()
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from datetime import datetime, timedelta
import time as time_module  # Alias to avoid conflict with 'time' column name
import sys
import os
from pathlib import Path

# Set timezone to Europe/Paris at startup
os.environ['TZ'] = 'Europe/Paris'
import time
time.tzset() if hasattr(time, 'tzset') else None  # tzset only works on Unix-like systems

# Auto-refresh for progress bars
try:
    from streamlit_autorefresh import st_autorefresh
except ImportError:
    st_autorefresh = None

# Fix asyncio event loop for IBKR/Streamlit compatibility
try:
    import nest_asyncio
    nest_asyncio.apply()
except ImportError:
    pass

# Add parent directory to path
sys.path.append(str(Path(__file__).parent.parent))

from backend.config import logger, FRENCH_TICKERS
from backend.data_collector import DataCollector
from backend.technical_indicators import calculate_and_update_indicators
from backend.models import SessionLocal, Ticker as TickerModel, HistoricalData, Order, OrderStatus, init_db
from sqlalchemy import func

# Initialize database on startup
init_db()

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


def init_global_ibkr_connection():
    """Initialize global IBKR connection in session_state"""
    if 'global_ibkr' not in st.session_state:
        st.session_state.global_ibkr = None
        st.session_state.global_ibkr_connected = False


def get_global_ibkr():
    """Get or create global IBKR connection"""
    init_global_ibkr_connection()
    
    if st.session_state.global_ibkr_connected and st.session_state.global_ibkr is not None:
        # Trust the connection flag - don't check isConnected() as it can block
        return st.session_state.global_ibkr
    
    return None


def connect_global_ibkr():
    """Connect global IBKR instance"""
    try:
        from backend.ibkr_collector import IBKRCollector
        
        if st.session_state.global_ibkr is None:
            # Use client_id=1 for Streamlit main connection
            st.session_state.global_ibkr = IBKRCollector(client_id=1)
        
        # Check if already connected before calling connect()
        if st.session_state.global_ibkr_connected:
            # Already connected - just verify it's still alive
            try:
                # Quick check: if ib is available, we're probably connected
                if hasattr(st.session_state.global_ibkr, 'ib') and st.session_state.global_ibkr.ib is not None:
                    if hasattr(st.session_state.global_ibkr.ib, 'isConnected') and st.session_state.global_ibkr.ib.isConnected():
                        return True, "✅ Déjà connecté à IBKR"
            except Exception:
                pass  # Fall through to reconnect if check fails
        
        # Not connected yet, or verification failed - connect now
        if st.session_state.global_ibkr.connect():
            st.session_state.global_ibkr_connected = True
            return True, "✅ Connecté à IBKR"
        else:
            st.session_state.global_ibkr = None
            st.session_state.global_ibkr_connected = False
            return False, "❌ Échec de la connexion"
    except Exception as e:
        logger.error(f"Error connecting to IBKR: {e}")
        return False, f"❌ Erreur: {str(e)}"


def disconnect_global_ibkr():
    """Disconnect global IBKR instance"""
    if st.session_state.global_ibkr is not None:
        try:
            st.session_state.global_ibkr.disconnect()
        except Exception:
            pass
        st.session_state.global_ibkr = None
        st.session_state.global_ibkr_connected = False


@st.cache_data(ttl=3)  # Cache for 3 seconds to avoid DB blocking
def get_cached_active_jobs():
    """Get active jobs with caching to avoid blocking UI"""
    try:
        from backend.job_manager import JobManager
        job_manager = JobManager()
        return job_manager.get_active_jobs()
    except Exception:
        return []


def main():
    """Main application"""
    st.title("🚀 Boursicotor - Plateforme de Trading Algorithmique")
    
    # Global progress banner for active jobs
    try:
        active_jobs = get_cached_active_jobs()
        
        if active_jobs:
            with st.container():
                st.markdown("""
                    <div style='background-color: #d1ecf1; color: #0c5460; padding: 10px; border-radius: 5px; border: 1px solid #bee5eb; margin-bottom: 10px;'>
                        <strong>🔄 Collectes en cours</strong>
                    </div>
                """, unsafe_allow_html=True)
                
                for job in active_jobs[:3]:  # Show max 3 active jobs
                    col1, col2, col3 = st.columns([2, 3, 1])
                    
                    with col1:
                        st.text(f"{job.ticker_symbol} ({job.source})")
                    
                    with col2:
                        progress = job.progress or 0
                        st.progress(progress / 100.0)
                        st.caption(f"{progress}% - {job.current_step or 'En cours...'}")
                    
                    with col3:
                        # Removed Details button - use History page directly
                        st.caption("→ Voir Historique")
                
                if len(active_jobs) > 3:
                    st.caption(f"... et {len(active_jobs) - 3} autre(s) job(s)")
                
                st.markdown("---")
    except Exception:
        pass  # Silently fail if Celery not configured
    
    st.markdown("---")
    
    # Initialize global IBKR connection
    init_global_ibkr_connection()
    
    # Auto-connect to IBKR on startup if not already connected
    if not st.session_state.get('global_ibkr_connected', False):
        try:
            # Attempt automatic connection
            success, message = connect_global_ibkr()
            if success:
                st.info(f"🔌 Connexion IBKR automatique réussie: {message}")
            else:
                st.warning(f"⚠️ Connexion IBKR automatique échouée: {message}")
                st.info("💡 Vous pouvez vous connecter manuellement depuis la barre latérale")
        except Exception as e:
            st.warning(f"⚠️ Erreur lors de la connexion automatique IBKR: {e}")
            st.info("💡 Vous pouvez vous connecter manuellement depuis la barre latérale")
    
    # Sidebar
    with st.sidebar:
        st.header("⚙️ Configuration")
        
        # Page selection
        page = st.radio(
            "Navigation",
            ["📊 Dashboard", "💾 Collecte de Données", "📜 Historique des collectes",
             "📈 Analyse Technique", "💹 Cours Live", "🔙 Backtesting",
             "📚 Indicateurs", "📝 Passage d'Ordres", "🤖 Trading Automatique", "⚙️ Paramètres"]
        )
        
        st.markdown("---")
        
        # Global IBKR Connection
        st.subheader("🔌 Connexion IBKR")
        
        col1, col2 = st.columns([1, 1])
        
        with col1:
            if not st.session_state.global_ibkr_connected:
                if st.button("🔌 Connecter", type="primary", width='stretch', key="sidebar_connect"):
                    with st.spinner("Connexion..."):
                        success, message = connect_global_ibkr()
                        if success:
                            st.success(message)
                            st.rerun()
                        else:
                            st.error(message)
            else:
                if st.button("🔌 Déconnecter", width='stretch', key="sidebar_disconnect"):
                    disconnect_global_ibkr()
                    st.success("Déconnecté")
                    st.rerun()
        
        with col2:
            if st.session_state.global_ibkr_connected:
                st.markdown("""
                    <div style='display: flex; align-items: center; height: 38px;'>
                        <div style='background-color: #d4edda; color: #155724; padding: 6px 12px; border-radius: 4px; border: 1px solid #c3e6cb; width: 100%; text-align: center;'>
                            🟢 Connecté
                        </div>
                    </div>
                """, unsafe_allow_html=True)
            else:
                st.markdown("""
                    <div style='display: flex; align-items: center; height: 38px;'>
                        <div style='background-color: #f8d7da; color: #721c24; padding: 6px 12px; border-radius: 4px; border: 1px solid #f5c6cb; width: 100%; text-align: center;'>
                            🔴 Déconnecté
                        </div>
                    </div>
                """, unsafe_allow_html=True)
        
        st.markdown("---")
        st.info("💡 **Connexion partagée**\n\nLa connexion IBKR est partagée entre toutes les pages. Connectez-vous une seule fois ici.")
    
    # Route to selected page
    if page == "📊 Dashboard":
        dashboard_page()
    elif page == "💾 Collecte de Données":
        data_collection_page()
    elif page == "📜 Historique des collectes":
        jobs_monitoring_page()
    elif page == "📈 Analyse Technique":
        technical_analysis_page()
    elif page == "💹 Cours Live":
        live_prices_page()
    elif page == "🔙 Backtesting":
        backtesting_page()
    elif page == "📚 Indicateurs":
        indicators_page()
    elif page == "📝 Passage d'Ordres":
        order_placement_page()
    elif page == "🤖 Trading Automatique":
        auto_trading_page()
    elif page == "⚙️ Paramètres":
        settings_page()


def dashboard_page():
    """Dashboard page - Uses global IBKR connection"""
    st.header("📊 Dashboard")
    
    # Initialize session state
    init_global_ibkr_connection()
    
    # Debug: Show connection state
    # st.caption(f"Debug: Connected={st.session_state.get('global_ibkr_connected', False)}, Collector={st.session_state.get('global_ibkr') is not None}")
    
    # Check connection state BEFORE trying to get collector
    if not st.session_state.get('global_ibkr_connected', False):
        st.warning("⚠️ Connectez-vous à IBKR depuis la barre latérale pour voir les informations de compte.")
        st.info("💡 La connexion IBKR est partagée entre toutes les pages. Utilisez le bouton dans la sidebar.")
        
        # Show placeholder metrics
        st.subheader("💰 Informations du compte")
        
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            st.metric("Valeur Nette", "--- €", "---")
        with col2:
            st.metric("Cash Disponible", "--- €")
        with col3:
            st.metric("P&L Non Réalisé", "--- €")
        with col4:
            st.metric("P&L Réalisé", "--- €")
        
        st.markdown("---")
        st.subheader("📋 Derniers Trades")
        st.info("💡 Connectez-vous à IBKR pour voir vos trades récents")
        
        return
    
    # Get collector only AFTER confirming we're connected
    collector = st.session_state.get('global_ibkr')
    
    if collector is None:
        st.error("❌ Erreur: Connexion IBKR invalide - collector est None")
        st.info("💡 Essayez de vous déconnecter et reconnecter depuis la sidebar")
        # Reset connection state
        st.session_state.global_ibkr_connected = False
        return
    
    # Verify collector has ib attribute
    if not hasattr(collector, 'ib') or collector.ib is None:
        st.error("❌ Erreur: L'objet IBKR n'est pas initialisé correctement")
        st.info("💡 Essayez de vous déconnecter et reconnecter depuis la sidebar")
        # Reset connection state
        st.session_state.global_ibkr_connected = False
        st.session_state.global_ibkr = None
        return
    
    # Connected - show real data
    try:
        # Get account summary with timeout protection
        account_summary = None
        try:
            # Use a simple flag check instead of blocking call
            if hasattr(collector, 'get_account_summary'):
                account_summary = collector.get_account_summary()
        except Exception as e:
            logger.warning(f"Could not get account summary: {e}")
            st.warning(f"⚠️ Impossible de récupérer les données du compte: {e}")
        
        if account_summary:
            st.subheader("💰 Informations du compte")
            
            # Display metrics
            col1, col2, col3, col4 = st.columns(4)
            
            # Format: account_summary[currency][tag]
            # Try to get EUR first, fallback to USD
            currency = 'EUR' if 'EUR' in account_summary else ('USD' if 'USD' in account_summary else list(account_summary.keys())[0])
            
            account_data = account_summary.get(currency, {})
            
            # Extract values
            nav = float(account_data.get('NetLiquidation', 0))
            cash = float(account_data.get('TotalCashValue', 0))
            upnl = float(account_data.get('UnrealizedPnL', 0))
            rpnl = float(account_data.get('RealizedPnL', 0))
            
            # Currency symbol
            curr_symbol = '€' if currency == 'EUR' else '$'
            
            with col1:
                st.metric("Valeur Nette", f"{nav:,.2f} {curr_symbol}", f"{upnl:+.2f} {curr_symbol}")
            with col2:
                st.metric("Cash Disponible", f"{cash:,.2f} {curr_symbol}")
            with col3:
                st.metric("P&L Non Réalisé", f"{upnl:+.2f} {curr_symbol}")
            with col4:
                st.metric("P&L Réalisé", f"{rpnl:+.2f} {curr_symbol}")
            
            st.markdown("---")
            
            # Get positions from OrderManager (trading positions)
            st.subheader("� Positions Trading (via OrderManager)")
            
            if 'order_manager' not in st.session_state or st.session_state.order_manager is None:
                from backend.order_manager import OrderManager
                st.session_state.order_manager = OrderManager(collector)
            
            try:
                trading_positions = st.session_state.order_manager.get_positions()
                
                if trading_positions:
                    import pandas as pd
                    pos_data = []
                    for pos in trading_positions:
                        pos_data.append({
                            'Symbole': pos['symbol'],
                            'Quantité': pos['position'],
                            'Prix Moyen': f"{pos['avg_cost']:.2f} {pos['currency']}",
                            'Prix Marché': f"{pos['market_price']:.2f} {pos['currency']}" if pos['market_price'] else 'N/A',
                            'Valeur': f"{pos['market_value']:.2f} {pos['currency']}" if pos['market_value'] else 'N/A',
                            'P&L Non Réalisé': f"{pos['unrealized_pnl']:+.2f} {pos['currency']}" if pos['unrealized_pnl'] else 'N/A',
                            'Exchange': pos['exchange']
                        })
                    
                    positions_df = pd.DataFrame(pos_data)
                    st.dataframe(positions_df, width='stretch', hide_index=True)
                    
                    # Summary
                    total_value = sum(p['market_value'] for p in trading_positions if p['market_value'])
                    total_upnl = sum(p['unrealized_pnl'] for p in trading_positions if p['unrealized_pnl'])
                    
                    col_pos1, col_pos2, col_pos3 = st.columns(3)
                    with col_pos1:
                        st.metric("Nombre de positions", len(trading_positions))
                    with col_pos2:
                        st.metric("Valeur totale", f"{total_value:,.2f} €")
                    with col_pos3:
                        pnl_color = "normal" if total_upnl >= 0 else "inverse"
                        st.metric("P&L Total Non Réalisé", f"{total_upnl:+,.2f} €", delta_color=pnl_color)
                else:
                    st.info("ℹ️ Aucune position ouverte pour le moment")
                    st.caption("Les positions apparaîtront ici après l'exécution de vos ordres")
                    
            except Exception as e:
                logger.error(f"Error getting trading positions: {e}")
                st.warning(f"⚠️ Impossible de récupérer les positions trading: {e}")
            
            st.markdown("---")
            
            # Get positions
            st.subheader("�📊 Positions Actuelles (via Collector)")
            
            positions = None
            try:
                if hasattr(collector, 'get_positions'):
                    positions = collector.get_positions()
            except Exception as e:
                logger.warning(f"Could not get positions: {e}")
                st.warning(f"⚠️ Impossible de récupérer les positions: {e}")
            
            if positions:
                import pandas as pd
                positions_df = pd.DataFrame(positions)
                st.dataframe(positions_df, width='stretch')
            else:
                st.info("ℹ️ Aucune position ouverte")
            
        else:
            st.warning("⚠️ Impossible de récupérer les données du compte")
        
        st.markdown("---")
        
        # Recent trades
        st.subheader("📋 Derniers Trades")
        
        try:
            # Get trades (fills) with protection
            trades = None
            if hasattr(collector, 'ib') and collector.ib:
                try:
                    trades = collector.ib.fills()
                except Exception as e:
                    logger.warning(f"Could not get fills: {e}")
                    st.warning(f"⚠️ Impossible de récupérer les trades: {e}")
            
            if trades:
                trades_data = []
                for trade in trades[:20]:  # Last 20 trades
                    fill = trade.execution
                    trades_data.append({
                        "Date": fill.time.strftime("%Y-%m-%d %H:%M:%S") if fill.time else "N/A",
                        "Symbole": trade.contract.symbol,
                        "Type": "ACHAT" if fill.side == "BOT" else "VENTE",
                        "Quantité": fill.shares,
                        "Prix": f"{fill.price:.2f}",
                        "Commission": f"{fill.commission:.2f}",
                        "Compte": fill.acctNumber
                    })
                
                import pandas as pd
                st.dataframe(pd.DataFrame(trades_data), width='stretch')
            else:
                st.info("ℹ️ Aucun trade récent. Passez des ordres dans l'onglet 'Trading' !")
        
        except Exception as e:
            st.warning(f"⚠️ Impossible de récupérer les trades: {e}")
    
    except Exception as e:
        st.error(f"❌ Erreur: {e}")
        import traceback
        with st.expander("Détails de l'erreur"):
            st.code(traceback.format_exc())



def data_collection_page():
    """Data collection page"""
    st.header("💾 Collecte de Données")
    
    # Auto-refresh when jobs are active (like in jobs_monitoring_page)
    active_jobs = get_cached_active_jobs()
    if active_jobs and st_autorefresh:
        st_autorefresh(interval=3000, key="collection_page_refresh")  # 3 seconds - faster for immediate visibility
        st.info("🔄 Rafraîchissement automatique activé (3 secondes) - collectes en cours")
    
    # Create tabs for Collection, Data Overview, and Interpolation
    tab_collect, tab_overview, tab_interp = st.tabs(["📥 Collecte IBKR", "📊 Données Collectées", "🔬 Interpolation"])
    
    with tab_collect:
        col1, col2 = st.columns(2)
        
        with col1:
            st.subheader("📥 Récupération de données historiques")
            
            # Ticker search and selection
            st.markdown("### 🔍 Recherche de Ticker")
            
            # Search mode selection
            search_mode = st.radio(
                "Mode de recherche",
                ["📋 Liste existante", "🔎 Recherche IBKR"],
                horizontal=True,
                help="Choisissez parmi les tickers existants ou recherchez de nouvelles actions via IBKR"
            )
        
        if search_mode == "📋 Liste existante":
            # Get tickers from database
            available_tickers = get_available_tickers()
            
            if not available_tickers:
                st.warning("⚠️ Aucun ticker en base de données. Utilisez la recherche IBKR pour ajouter des actions.")
                selected_ticker = None
                selected_name = None
            else:
                # Filter existing tickers
                search_term = st.text_input(
                    "Filtrer les tickers",
                    placeholder="Ex: Air Liquide, TTE, Total...",
                    help="Tapez pour filtrer la liste des tickers déjà collectés"
                )
                
                if search_term:
                    search_lower = search_term.lower()
                    filtered_items = {
                        ticker: name 
                        for ticker, name in available_tickers.items() 
                        if search_lower in ticker.lower() or search_lower in name.lower()
                    }
                else:
                    filtered_items = available_tickers
                
                # Show filtered results
                if filtered_items:
                    ticker_options = list(filtered_items.keys())
                    selected_ticker = st.selectbox(
                        "Sélectionner le ticker",
                        ticker_options,
                        format_func=lambda x: f"{x} - {filtered_items[x]}",
                        help=f"{len(filtered_items)} ticker(s) en base de données"
                    )
                    selected_name = filtered_items[selected_ticker]
                else:
                    st.warning("Aucun ticker trouvé. Essayez un autre terme de recherche.")
                    selected_ticker = None
                    selected_name = None
        
        else:
            # Manual ticker input mode (IBKR search is too slow/unreliable)
            st.info("📝 Entrez directement le symbole du ticker (ex: AAPL, TSLA, TTE...)")
            
            col_t1, col_t2 = st.columns([1, 2])
            with col_t1:
                selected_ticker = st.text_input(
                    "Ticker",
                    placeholder="Ex: AAPL",
                    help="Symbole du ticker (ex: AAPL, TSLA, MSFT, TTE, WLN...)"
                ).upper().strip()
            with col_t2:
                selected_name = st.text_input(
                    "Nom (optionnel)",
                    placeholder="Ex: Apple Inc.",
                    help="Nom de l'entreprise (optionnel)"
                ).strip()
        
        # IBKR options
        st.markdown("**IBKR / Lynx** - Périodes et intervalles")
        
        duration_options = {
            "1 jour": "1 D",
            "3 jours": "3 D",
            "1 semaine": "1 W",
            "2 semaines": "2 W",
            "1 mois": "1 M",
            "3 mois": "3 M",
            "6 mois": "6 M",
            "1 an": "1 Y",
            "2 ans": "2 Y"
        }
        selected_duration = st.selectbox(
            "Période",
            list(duration_options.keys()),
            index=4,  # Default: 1 mois
            help="IBKR: Données temps réel et historiques"
        )
        period = duration_options[selected_duration]
        
        # Interval options for IBKR
        interval_options = {
            "5 secondes": "5 secs",
            "10 secondes": "10 secs",
            "15 secondes": "15 secs",
            "30 secondes": "30 secs",
            "1 minute": "1 min",
            "2 minutes": "2 mins",
            "3 minutes": "3 mins",
            "5 minutes": "5 mins",
            "10 minutes": "10 mins",
            "15 minutes": "15 mins",
            "20 minutes": "20 mins",
            "30 minutes": "30 mins",
            "1 heure": "1 hour",
            "2 heures": "2 hours",
            "3 heures": "3 hours",
            "4 heures": "4 hours",
            "8 heures": "8 hours",
            "1 jour": "1 day",
            "1 semaine": "1 week",
            "1 mois": "1 month"
        }
        selected_interval = st.selectbox(
            "Intervalle",
            list(interval_options.keys()),
            index=4,  # Default: 1 minute
            help="IBKR: Intervalles de 5 secondes à 1 mois (intervalles < 5s limités aux actions US très liquides)"
        )
        interval = interval_options[selected_interval]
        
        # Collect button - Create async job with Celery
        if st.button("📊 Collecter les données", type="primary", width='stretch'):
            try:
                from backend.job_manager import JobManager
                from backend.tasks import collect_data_ibkr
                
                job_manager = JobManager()
                
                # Check IBKR connection
                collector = get_global_ibkr()
                
                if collector is None:
                    st.error("❌ Connectez-vous à IBKR depuis la sidebar pour collecter des données")
                    st.info("💡 Utilisez le bouton de connexion dans la barre latérale")
                else:
                    # Map selected values to database format
                    interval_db_map = {
                            "5 secondes": "5sec",
                            "10 secondes": "10sec",
                            "15 secondes": "15sec",
                            "30 secondes": "30sec",
                            "1 minute": "1min",
                            "2 minutes": "2min",
                            "3 minutes": "3min",
                            "5 minutes": "5min",
                            "10 minutes": "10min",
                            "15 minutes": "15min",
                            "20 minutes": "20min",
                            "30 minutes": "30min",
                            "1 heure": "1h",
                            "2 heures": "2h",
                            "3 heures": "3h",
                            "4 heures": "4h",
                            "8 heures": "8h",
                            "1 jour": "1day",
                            "1 semaine": "1week",
                            "1 mois": "1month"
                    }
                    
                    db_interval = interval_db_map.get(selected_interval, "1min")
                    
                    # Create IBKR job
                    job = job_manager.create_job(
                        ticker_symbol=selected_ticker,
                        ticker_name=selected_name,
                        source="ibkr",
                        duration=selected_duration,
                        interval=selected_interval
                    )
                    
                    # Launch Celery task
                    task = collect_data_ibkr.delay(
                        job_id=job.id,
                        ticker_symbol=selected_ticker,
                        ticker_name=selected_name,
                        duration=period,
                        bar_size=interval,
                        interval_db=db_interval
                    )
                    
                    # Update job with Celery task ID
                    job_manager.update_job_task_id(job.id, task.id)
                    
                    st.success(f"✅ Job de collecte créé pour {selected_ticker} depuis IBKR!")
                    st.info(f"📊 Source: IBKR | Période: {selected_duration} | Intervalle: {selected_interval}")
                    st.info("🔄 La collecte s'exécute en arrière-plan. Consultez la page **Historique des collectes** pour suivre la progression.")
                    
                    # Mark in session state to show updated data on next auto-refresh
                    st.session_state.collection_started = True
            
            except ImportError as e:
                st.error("❌ Celery n'est pas installé ou configuré correctement")
                st.info("� Consultez le fichier CELERY_SETUP.md pour installer et configurer Celery + Redis")
                with st.expander("Détails de l'erreur"):
                    st.code(str(e))
            
            except Exception as e:
                st.error(f"❌ Erreur lors de la création du job: {e}")
                import traceback
                with st.expander("Détails de l'erreur"):
                    st.code(traceback.format_exc())
        
        
    
    # Data Overview tab - Show all collected tickers in a table
    with tab_overview:
        st.subheader("📊 Vue d'ensemble des données collectées")
        st.info("ℹ️ Tableau récapitulatif de tous les tickers collectés avec statistiques sur les données")
        
        db = SessionLocal()
        try:
            from backend.models import Ticker as TickerModel, HistoricalData
            from sqlalchemy import func
            
            # Get all tickers with data
            tickers_with_stats = db.query(
                TickerModel.symbol,
                TickerModel.name,
                func.count(HistoricalData.id).label('total_points'),
                func.min(HistoricalData.timestamp).label('first_date'),
                func.max(HistoricalData.timestamp).label('last_date')
            ).join(
                HistoricalData,
                TickerModel.id == HistoricalData.ticker_id
            ).group_by(
                TickerModel.id,
                TickerModel.symbol,
                TickerModel.name
            ).order_by(TickerModel.symbol).all()
            
            if tickers_with_stats:
                # Prepare data for display
                overview_data = []
                for ticker in tickers_with_stats:
                    days_covered = (ticker.last_date - ticker.first_date).days + 1 if ticker.first_date and ticker.last_date else 0
                    
                    overview_data.append({
                        '📈 Ticker': ticker.symbol,
                        '🏢 Nom': ticker.name,
                        '📊 Points': f"{ticker.total_points:,}",
                        '📅 Début': ticker.first_date.strftime('%Y-%m-%d') if ticker.first_date else 'N/A',
                        '📅 Fin': ticker.last_date.strftime('%Y-%m-%d') if ticker.last_date else 'N/A',
                        '⏱️ Durée (jours)': days_covered
                    })
                
                df_overview = pd.DataFrame(overview_data)
                
                # Display as table
                st.dataframe(
                    df_overview,
                    use_container_width=True,
                    height=400,
                    hide_index=True
                )
                
                # Summary statistics
                st.markdown("---")
                col_summary1, col_summary2, col_summary3 = st.columns(3)
                
                total_tickers = len(tickers_with_stats)
                total_points = sum(t.total_points for t in tickers_with_stats)
                avg_points = int(total_points / total_tickers) if total_tickers > 0 else 0
                
                with col_summary1:
                    st.metric("🎯 Total Tickers", total_tickers)
                with col_summary2:
                    st.metric("📊 Total Points", f"{total_points:,}")
                with col_summary3:
                    st.metric("📈 Points Moyens", f"{avg_points:,}")
                
                # Export option
                st.markdown("---")
                if st.button("💾 Exporter le tableau (CSV)", use_container_width=True):
                    csv = df_overview.to_csv(index=False)
                    st.download_button(
                        label="Télécharger CSV",
                        data=csv,
                        file_name=f"boursicotor_data_overview_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
                        mime="text/csv",
                        use_container_width=True
                    )
            else:
                st.warning("⚠️ Aucune donnée collectée pour le moment.")
                st.info("💡 Utilisez l'onglet **Collecte IBKR** pour commencer à collecter des données sur TTE, WLN, TSL ou d'autres actions.")
        
        except Exception as e:
            st.error(f"❌ Erreur lors du chargement des données : {e}")
            import traceback
            with st.expander("Détails de l'erreur"):
                st.code(traceback.format_exc())
        finally:
            db.close()
    
    # Interpolation tab
    with tab_interp:
        st.subheader("🔬 Interpolation de Données")
        st.info("📊 Générez des données haute fréquence à partir de données basse fréquence existantes (ex: créer des points à la seconde à partir de données minute)")
        
        col_interp1, col_interp2 = st.columns(2)
        
        with col_interp1:
            # Get available tickers
            db_interp = SessionLocal()
            try:
                from backend.models import Ticker as TickerModel, HistoricalData
                from sqlalchemy import func, distinct
                
                # Get tickers with data
                tickers_with_data = db_interp.query(
                    TickerModel.symbol,
                    TickerModel.name
                ).join(
                    HistoricalData,
                    TickerModel.id == HistoricalData.ticker_id
                ).distinct().all()
                
                if tickers_with_data:
                    ticker_options_interp = {t.symbol: f"{t.symbol} - {t.name}" for t in tickers_with_data}
                    selected_ticker_interp = st.selectbox(
                        "Sélectionner le ticker",
                        list(ticker_options_interp.keys()),
                        format_func=lambda x: ticker_options_interp[x],
                        key="interp_ticker"
                )
                
                # Get available intervals for this ticker
                ticker_obj = db_interp.query(TickerModel).filter(TickerModel.symbol == selected_ticker_interp).first()
                
                if ticker_obj:
                    available_intervals = db_interp.query(
                        distinct(HistoricalData.interval),
                        func.count(HistoricalData.id)
                    ).filter(
                        HistoricalData.ticker_id == ticker_obj.id
                    ).group_by(
                        HistoricalData.interval
                    ).all()
                    
                    if available_intervals:
                        interval_info = {interval: f"{interval} ({count:,} points)" for interval, count in available_intervals}
                        source_interval_interp = st.selectbox(
                            "Intervalle source",
                            [interval for interval, _ in available_intervals],
                            format_func=lambda x: interval_info[x],
                            key="source_interval"
                        )
                        
                        # Get available target intervals
                        from backend.data_interpolator import DataInterpolator
                        
                        possible_targets = []
                        all_targets = ['1s', '5s', '10s', '30s', '1min', '5min', '15min', '30min', '1h']
                        
                        for target in all_targets:
                            if DataInterpolator.can_interpolate(source_interval_interp, target):
                                multiplier = DataInterpolator.INTERVAL_MULTIPLIERS[(source_interval_interp, target)]
                                possible_targets.append((target, multiplier))
                        
                        if possible_targets:
                            target_labels = {t: f"{t} (×{m} points)" for t, m in possible_targets}
                            target_interval_interp = st.selectbox(
                                "Intervalle cible",
                                [t for t, _ in possible_targets],
                                format_func=lambda x: target_labels[x],
                                key="target_interval"
                            )
                            
                            # Interpolation method
                            methods = DataInterpolator.get_interpolation_methods()
                            selected_method = st.selectbox(
                                "Méthode d'interpolation",
                                list(methods.keys()),
                                format_func=lambda x: methods[x],
                                key="interp_method"
                            )
                            
                            # Limit records
                            source_count = next(count for interval, count in available_intervals if interval == source_interval_interp)
                            max_limit = min(source_count, 10000)  # Limit to 10k source records max
                            
                            limit_records = st.number_input(
                                "Limiter le nombre d'enregistrements source",
                                min_value=10,
                                max_value=max(max_limit, 10),  # Ensure max >= min
                                value=max(min(1000, max_limit), 10),  # Ensure value >= min_value
                                step=100,
                                help=f"Pour éviter la surcharge, limitez le nombre d'enregistrements à traiter ({source_count:,} disponibles)"
                            )
                            
                            # Calculate expected output
                            multiplier = next(m for t, m in possible_targets if t == target_interval_interp)
                            expected_records = limit_records * multiplier
                            
                            st.info(f"📊 **Estimation**: {limit_records:,} enregistrements source → ~{expected_records:,} enregistrements générés")
                            
                        else:
                            st.warning(f"⚠️ Aucune interpolation possible depuis {source_interval_interp}")
                            target_interval_interp = None
                    else:
                        st.warning("⚠️ Aucune donnée disponible pour ce ticker")
                        target_interval_interp = None
                else:
                    st.warning("⚠️ Aucun ticker avec données historiques")
                    target_interval_interp = None
            
            finally:
                db_interp.close()
        
        with col_interp2:
            st.markdown("### 📋 Comment ça marche ?")
            st.markdown("""
            **Méthodes d'interpolation** :
            
            - **Linéaire** : Interpolation simple entre deux points
            - **Cubique** : Interpolation lisse avec spline cubique
            - **Temporel** : Ajoute une variance aléatoire réaliste
            - **OHLC** : Préserve les patterns Open-High-Low-Close
            
            **Exemple** :
            - Source: 1,000 points à 1min
            - Cible: 1s (×60)
            - Résultat: ~60,000 points
            
            ⚠️ **Attention** : Les données interpolées sont des approximations, pas des données réelles.
            """)
        
        # Interpolation button
        if target_interval_interp:
            if st.button("🚀 Démarrer l'interpolation", type="primary", width='stretch'):
                with st.spinner(f"Interpolation de {selected_ticker_interp} de {source_interval_interp} vers {target_interval_interp}..."):
                    try:
                        from backend.data_interpolator import DataInterpolator
                        
                        result = DataInterpolator.interpolate_and_save(
                            ticker_symbol=selected_ticker_interp,
                            source_interval=source_interval_interp,
                            target_interval=target_interval_interp,
                            method=selected_method,
                            limit=limit_records
                        )
                        
                        if result['success']:
                            st.success(f"✅ {result['message']}")
                            
                            # Display stats
                            col_stat1, col_stat2, col_stat3 = st.columns(3)
                            with col_stat1:
                                st.metric("Records source", f"{result['source_records']:,}")
                            with col_stat2:
                                st.metric("Records générés", f"{result['generated_records']:,}")
                            with col_stat3:
                                st.metric("Nouveaux", f"{result['new_records']:,}")
                            
                            if result['duplicates'] > 0:
                                st.info(f"ℹ️ {result['duplicates']:,} enregistrements déjà existants ignorés")
                        else:
                            st.error(f"❌ {result['message']}")
                        
                    except Exception as e:
                        st.error(f"❌ Erreur lors de l'interpolation: {e}")
                        logger.error(f"Interpolation error: {e}")
    
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
    
    if st.button("📊 Afficher le graphique", width='stretch'):
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
                    st.warning("⚠️ Aucune donnée disponible pour la période sélectionnée")
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
                    
                    st.plotly_chart(fig, use_container_width=True, key="live_price_chart")
                    
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
                    
                    st.plotly_chart(fig_volume, width='stretch', key="live_volume_chart")
                    
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


def jobs_monitoring_page():
    """Job monitoring page - Shows async data collection progress"""
    st.header("📋 Historique des collectes de données")
    
    # Import timezone conversion function
    from backend.models import format_datetime_paris

    # Auto-refresh for progress bars (every 5 seconds when jobs are active)
    active_jobs = get_cached_active_jobs()
    if active_jobs and st_autorefresh:
        st_autorefresh(interval=5000, key="jobs_refresh")  # 5 seconds
        st.info("🔄 Rafraîchissement automatique activé (5 secondes)")

    # Manual refresh button
    col_refresh, col_empty = st.columns([1, 3])
    with col_refresh:
        if st.button("🔄 Actualiser", help="Actualiser manuellement les statuts des jobs"):
            st.rerun()

    try:
        from backend.job_manager import JobManager
        from backend.models import JobStatus, DataCollectionJob, SessionLocal
        from datetime import datetime, timedelta

        job_manager = JobManager()
        db = SessionLocal()
        
        # Statistics
        st.subheader("📊 Statistiques")
        stats = job_manager.get_statistics()
        
        col1, col2, col3, col4, col5 = st.columns([1, 1, 1, 1, 1.5])
        
        with col1:
            st.metric("Total", stats['total'])
        with col2:
            st.metric("En cours", stats['running'], help="Jobs actuellement en exécution")
        with col3:
            st.metric("Complétés", stats['completed'])
        with col4:
            avg_time = stats['average_completion_time']
            if avg_time:
                st.metric("Temps moyen", f"{avg_time:.1f}s")
            else:
                st.metric("Temps moyen", "N/A")
        with col5:
            # Quick action: Cancel all stuck jobs
            if st.button("🧹 Nettoyer jobs bloqués", help="Annule tous les jobs en cours depuis plus de 2h"):
                try:
                    from datetime import timedelta
                    cutoff_time = datetime.utcnow() - timedelta(hours=2)
                    stuck_jobs = db.query(DataCollectionJob).filter(
                        DataCollectionJob.status.in_([JobStatus.PENDING, JobStatus.RUNNING]),
                        DataCollectionJob.started_at < cutoff_time
                    ).all()
                    
                    count = 0
                    for job in stuck_jobs:
                        job.status = JobStatus.CANCELLED
                        job.completed_at = datetime.utcnow()
                        job.error_message = "Job bloqué - annulé automatiquement"
                        count += 1
                    
                    db.commit()
                    if count > 0:
                        st.success(f"✅ {count} job(s) bloqué(s) annulé(s)")
                        st.rerun()
                    else:
                        st.info("ℹ️ Aucun job bloqué détecté")
                except Exception as e:
                    st.error(f"❌ Erreur: {e}")
        
        st.markdown("---")
        
        # Filter tabs
        tab1, tab2, tab3, tab4 = st.tabs(["🔄 En cours", "✅ Complétés", "❌ Échoués", "📜 Tous"])
        
        with tab1:
            st.subheader("Jobs en cours d'exécution")
            active_jobs = job_manager.get_active_jobs()
            
            if not active_jobs:
                st.info("Aucun job en cours d'exécution")
            else:
                for job in active_jobs:
                    with st.container():
                        col1, col2 = st.columns([3, 1])
                        
                        with col1:
                            st.markdown(f"**{job.ticker_symbol}** - {job.source}")
                            st.caption(f"Démarré: {format_datetime_paris(job.started_at) if job.started_at else 'N/A'}")
                            st.caption(f"Durée: {job.duration} | Intervalle: {job.interval}")
                            
                            # Progress bar
                            progress = job.progress or 0
                            st.progress(progress / 100.0)
                            st.caption(f"Progression: {progress}% - {job.current_step or 'En attente...'}")
                        
                        with col2:
                            # Force stop button
                            if st.button("🛑 Forcer l'arrêt", key=f"force_cancel_{job.id}", type="secondary"):
                                try:
                                    # Use static method to cancel job
                                    success = JobManager.cancel_job(job.id)
                                    
                                    if success:
                                        st.success(f"✅ Job {job.id} annulé avec succès")
                                        
                                        # Automatically restart Celery worker
                                        with st.spinner("🔄 Redémarrage du worker Celery..."):
                                            restart_success = JobManager.restart_celery_worker()
                                            if restart_success:
                                                st.success("✅ Worker Celery redémarré automatiquement")
                                            else:
                                                st.warning("⚠️ Impossible de redémarrer automatiquement. Relancez `startboursicotor.bat`")
                                        
                                        st.rerun()
                                    else:
                                        st.error(f"❌ Impossible d'annuler le job {job.id}")
                                        
                                except Exception as e:
                                    st.error(f"❌ Erreur lors de l'annulation: {e}")
                                    logger.error(f"Error cancelling job {job.id}: {e}", exc_info=True)
                        
                        st.markdown("---")
        
        with tab2:
            st.subheader("Jobs complétés")
            completed_jobs = job_manager.get_jobs_by_status(JobStatus.COMPLETED)
            
            if not completed_jobs:
                st.info("Aucun job complété récemment")
            else:
                for job in completed_jobs[:20]:  # Limit to 20 most recent
                    with st.expander(f"✅ {job.ticker_symbol} - {job.source} ({format_datetime_paris(job.completed_at, '%d/%m/%Y %H:%M') if job.completed_at else 'N/A'})"):
                        col1, col2 = st.columns(2)
                        
                        with col1:
                            st.markdown(f"**Ticker:** {job.ticker_symbol}")
                            st.markdown(f"**Source:** {job.source}")
                            st.markdown(f"**Durée:** {job.duration}")
                            st.markdown(f"**Intervalle:** {job.interval}")
                        
                        with col2:
                            st.markdown(f"**Démarré:** {format_datetime_paris(job.started_at) if job.started_at else 'N/A'}")
                            st.markdown(f"**Complété:** {format_datetime_paris(job.completed_at) if job.completed_at else 'N/A'}")
                            
                            if job.started_at and job.completed_at:
                                duration = (job.completed_at - job.started_at).total_seconds()
                                st.markdown(f"**Temps écoulé:** {duration:.1f}s")
                        
                        st.markdown("**Résultats:**")
                        col3, col4, col5 = st.columns(3)
                        with col3:
                            st.metric("Nouveaux", job.records_new or 0)
                        with col4:
                            st.metric("Mis à jour", job.records_updated or 0)
                        with col5:
                            st.metric("Total", job.records_total or 0)
        
        with tab3:
            st.subheader("Jobs échoués")
            failed_jobs = job_manager.get_jobs_by_status(JobStatus.FAILED)
            
            if not failed_jobs:
                st.info("Aucun job échoué récemment")
            else:
                for job in failed_jobs[:20]:  # Limit to 20 most recent
                    with st.expander(f"❌ {job.ticker_symbol} - {job.source} ({format_datetime_paris(job.completed_at, '%d/%m/%Y %H:%M') if job.completed_at else 'N/A'})"):
                        col1, col2 = st.columns(2)
                        
                        with col1:
                            st.markdown(f"**Ticker:** {job.ticker_symbol}")
                            st.markdown(f"**Source:** {job.source}")
                            st.markdown(f"**Durée:** {job.duration}")
                            st.markdown(f"**Intervalle:** {job.interval}")
                        
                        with col2:
                            st.markdown(f"**Démarré:** {format_datetime_paris(job.started_at) if job.started_at else 'N/A'}")
                            st.markdown(f"**Échoué:** {format_datetime_paris(job.completed_at) if job.completed_at else 'N/A'}")
                        
                        if job.error_message:
                            st.error(f"**Erreur:** {job.error_message}")
        
        with tab4:
            st.subheader("Tous les jobs")
            all_jobs = job_manager.get_recent_jobs(limit=50)
            
            if not all_jobs:
                st.info("Aucun job enregistré")
            else:
                # Create table data
                table_data = []
                for job in all_jobs:
                    status_emoji = {
                        JobStatus.PENDING: "⏳",
                        JobStatus.RUNNING: "🔄",
                        JobStatus.COMPLETED: "✅",
                        JobStatus.FAILED: "❌",
                        JobStatus.CANCELLED: "🚫"
                    }.get(job.status, "❓")
                    
                    table_data.append({
                        "Status": status_emoji,
                        "Ticker": job.ticker_symbol,
                        "Source": job.source,
                        "Durée": job.duration,
                        "Intervalle": job.interval,
                        "Progression": f"{job.progress or 0}%",
                        "Créé": format_datetime_paris(job.created_at, '%d/%m %H:%M') if job.created_at else "N/A",
                        "Complété": format_datetime_paris(job.completed_at, '%d/%m %H:%M') if job.completed_at else "-"
                    })
                
                import pandas as pd
                df = pd.DataFrame(table_data)
                st.dataframe(df, width='stretch', hide_index=True)
        
        # Cleanup section
        st.markdown("---")
        st.subheader("🧹 Maintenance")
        
        col1, col2 = st.columns([2, 1])
        
        with col1:
            st.info("💡 Les jobs complétés ou échoués sont automatiquement supprimés après 7 jours")
        
        with col2:
            if st.button("🗑️ Nettoyer maintenant", type="secondary"):
                try:
                    from backend.tasks import cleanup_old_jobs
                    cleanup_old_jobs.delay(days_to_keep=7)
                    st.success("Nettoyage lancé en arrière-plan")
                except Exception as e:
                    st.error(f"Erreur: {e}")
    
    except ImportError as e:
        st.error("❌ Celery n'est pas installé ou configuré correctement")
        st.info("💡 Consultez le fichier CELERY_SETUP.md pour installer et configurer Celery + Redis")
        with st.expander("Détails de l'erreur"):
            st.code(str(e))
    
    except Exception as e:
        st.error(f"❌ Erreur lors de la récupération des jobs: {e}")
        import traceback
        with st.expander("Détails de l'erreur"):
            st.code(traceback.format_exc())
    
    finally:
        # Close database session
        if 'db' in locals():
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
            
            st.plotly_chart(fig, use_container_width=True, key="historical_price_chart")
            
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
    st.plotly_chart(fig, use_container_width=True, key="technical_analysis_chart")
    
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
        st.info("L'algorithme va tester différentes stratégies aléatoires pour trouver la meilleure performance. Configure les paramètres ci-dessous.")
        
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
            # Get total count for ticker (will be updated after date selection)
            db = SessionLocal()
            try:
                ticker_obj = db.query(TickerModel).filter(TickerModel.symbol == selected_ticker).first()
                if ticker_obj:
                    total_count = db.query(HistoricalData).filter(HistoricalData.ticker_id == ticker_obj.id).count()
                    st.metric("Points totaux", f"{total_count:,}")
            finally:
                db.close()
        
        # Period selection
        st.markdown("### 📅 Période d'analyse")
        col_date1, col_date2, col_date3 = st.columns([2, 2, 1])
        
        # Get min/max dates for the ticker
        db = SessionLocal()
        try:
            ticker_obj = db.query(TickerModel).filter(TickerModel.symbol == selected_ticker).first()
            if ticker_obj:
                min_date_query = db.query(HistoricalData.timestamp).filter(
                    HistoricalData.ticker_id == ticker_obj.id
                ).order_by(HistoricalData.timestamp.asc()).first()
                max_date_query = db.query(HistoricalData.timestamp).filter(
                    HistoricalData.ticker_id == ticker_obj.id
                ).order_by(HistoricalData.timestamp.desc()).first()
                
                if min_date_query and max_date_query:
                    min_date = min_date_query[0].date()
                    max_date = max_date_query[0].date()
                    
                    # Calculate default start date: 30 days before max, but not before min
                    default_start = max_date - pd.Timedelta(days=30)
                    if default_start < min_date:
                        default_start = min_date
                    
                    with col_date1:
                        start_date = st.date_input(
                            "Date de début",
                            value=default_start,
                            min_value=min_date,
                            max_value=max_date,
                            help="Début de la période d'analyse"
                        )
                    
                    with col_date2:
                        end_date = st.date_input(
                            "Date de fin",
                            value=max_date,
                            min_value=min_date,
                            max_value=max_date,
                            help="Fin de la période d'analyse"
                        )
                    
                    with col_date3:
                        # Calculate number of days and points in selected period
                        if start_date and end_date:
                            days_diff = (end_date - start_date).days
                            
                            # Count actual data points in the selected period
                            start_datetime = pd.Timestamp(start_date)
                            end_datetime = pd.Timestamp(end_date) + pd.Timedelta(days=1) - pd.Timedelta(seconds=1)
                            
                            filtered_count = db.query(HistoricalData).filter(
                                HistoricalData.ticker_id == ticker_obj.id,
                                HistoricalData.timestamp >= start_datetime,
                                HistoricalData.timestamp <= end_datetime
                            ).count()
                            
                            st.metric("Points période", f"{filtered_count:,}", delta=f"{days_diff} jours")
                else:
                    start_date = None
                    end_date = None
            else:
                start_date = None
                end_date = None
        finally:
            db.close()
        
        # Parallel mode option
        col_mode1, col_mode2 = st.columns([3, 1])
        with col_mode1:
            enable_parallel = st.checkbox(
                "🚀 Mode parallèle (utilise plusieurs CPU cores)",
                value=True,
                help="Accélère l'optimisation en utilisant tous les CPU disponibles (6-8x plus rapide)"
            )
        with col_mode2:
            if enable_parallel:
                from multiprocessing import cpu_count
                num_cpus = cpu_count()
                st.metric("CPU cores", num_cpus)
        
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
                format="%.2",
                help="Commission par trade (achat + vente)"
            )
        
        with col4:
            min_hold_minutes = st.number_input(
                "Min. temps entre trades (min)",
                min_value=0,
                max_value=1440,
                value=5,
                step=1,
                help="Temps minimum à attendre entre deux trades pour éviter le sur-trading"
            )
        
        col5, col6 = st.columns(2)
        
        with col5:
            max_iterations = st.number_input(
                "Max itérations",
                min_value=10,
                max_value=5000,
                value=2000,
                step=100
            )
        
        # Button to start optimization
        if st.button("🚀 Lancer la recherche", type="primary", width='stretch'):
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
                    
                    # Apply date filter if specified
                    if start_date and end_date:
                        start_datetime = pd.Timestamp(start_date)
                        end_datetime = pd.Timestamp(end_date) + pd.Timedelta(days=1) - pd.Timedelta(seconds=1)
                        df = df[(df.index >= start_datetime) & (df.index <= end_datetime)]
                        st.info(f"📊 {len(df):,} points chargés pour l'analyse (période: {start_date} à {end_date})")
                    else:
                        st.info(f"📊 {len(df):,} points chargés pour l'analyse")
                    
                    if len(df) < 100:
                        st.error("Pas assez de données dans la période sélectionnée (minimum 100 points requis)")
                        return
                    
                    # Convert commission % to decimal
                    commission_decimal = commission_pct / 100
                    
                    if enable_parallel:
                        # === MODE PARALLÈLE ===
                        st.info(f"🚀 Mode parallèle activé - utilisation de {cpu_count() - 1} processus")
                        st.warning("📊 **Progression en temps réel** : Consultez les logs dans la console/terminal pour suivre l'avancement détaillé (mise à jour tous les 10 backtests)")
                        
                        with st.spinner("⏳ Optimisation en cours... Consultez les logs pour la progression détaillée"):
                            engine = BacktestingEngine(
                                initial_capital=initial_capital,
                                commission=commission_decimal,
                                allow_short=True,  # Short réactivé
                                min_hold_minutes=min_hold_minutes
                            )
                            
                            # Run parallel optimization (les logs s'affichent dans la console)
                            best_strategy, best_result, all_results = engine.run_parallel_optimization(
                                df=df,
                                symbol=selected_ticker,
                                num_iterations=max_iterations,
                                target_return=target_return,
                                num_processes=None,  # Auto-detect
                                progress_callback=None  # Pas de callback (logs console uniquement)
                            )
                        
                        st.success(f"✅ Optimisation terminée ! {len(all_results)} stratégies testées.")
                        
                        if best_result and best_strategy:
                            best_return = best_result.total_return
                            
                            # Save to session state
                            st.session_state.best_strategy = best_strategy
                            st.session_state.best_result = best_result
                            st.session_state.best_return = best_return
                            st.session_state.selected_ticker = selected_ticker
                            
                            if best_return >= target_return:
                                st.success(f"🎯 Objectif atteint ! Meilleure stratégie : {best_return:.2f}%")
                            else:
                                st.warning(f"⚠️ Objectif non atteint après {max_iterations} itérations")
                                st.info(f"Meilleur résultat obtenu : {best_return:.2f}%")
                            
                            st.info("📊 Résultats affichés ci-dessous")
                        else:
                            st.error("Aucune stratégie n'a pu être générée")
                    
                    else:
                        # === MODE SÉQUENTIEL (ancien code) ===
                        # Progress bar pour le mode séquentiel uniquement
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
                            strategy_type = _rng_frontend.choice(['ma', 'rsi', 'multi', 'enhanced'])
                            
                            if strategy_type == 'ma':
                                from backend.backtesting_engine import MovingAverageCrossover
                                fast = _rng_frontend.integers(5, 20)
                                slow = _rng_frontend.integers(fast + 5, 50)
                                strategy = MovingAverageCrossover(fast_period=fast, slow_period=slow)
                            elif strategy_type == 'rsi':
                                from backend.backtesting_engine import RSIStrategy
                                period = _rng_frontend.integers(10, 20)
                                oversold = _rng_frontend.integers(20, 35)
                                overbought = _rng_frontend.integers(65, 80)
                                strategy = RSIStrategy(rsi_period=period, oversold=oversold, overbought=overbought)
                            elif strategy_type == 'multi':
                                from backend.backtesting_engine import MultiIndicatorStrategy
                                strategy = MultiIndicatorStrategy(
                                    ma_fast=_rng_frontend.integers(5, 15),
                                    ma_slow=_rng_frontend.integers(20, 40),
                                    rsi_period=_rng_frontend.integers(10, 20),
                                    rsi_oversold=_rng_frontend.integers(20, 35),
                                    rsi_overbought=_rng_frontend.integers(65, 80)
                                )
                            else:  # enhanced
                                from backend.backtesting_engine import EnhancedMovingAverageStrategy
                                
                                    # Randomly decide which ultra-complex indicators to use
                                use_supertrend = _rng_frontend.choice([True, False])
                                use_parabolic_sar = _rng_frontend.choice([True, False])
                                use_donchian = _rng_frontend.choice([True, False])
                                use_vwap = _rng_frontend.choice([True, False])
                                use_obv = _rng_frontend.choice([True, False])
                                use_cmf = _rng_frontend.choice([True, False])
                                use_elder_ray = _rng_frontend.choice([True, False])
                                
                                strategy = EnhancedMovingAverageStrategy(
                                    fast_period=_rng_frontend.integers(15, 25),
                                    slow_period=_rng_frontend.integers(35, 50),
                                    roc_period=_rng_frontend.choice([10, 14]),
                                    roc_threshold=_rng_frontend.uniform(1.0, 4.0),
                                    adx_period=_rng_frontend.choice([14, 20]),
                                    adx_threshold=_rng_frontend.integers(20, 35),
                                    volume_ratio_short=_rng_frontend.choice([3, 5, 10]),
                                    volume_ratio_long=_rng_frontend.choice([15, 20, 30]),
                                    volume_threshold=_rng_frontend.uniform(1.1, 1.5),
                                    momentum_period=_rng_frontend.choice([10, 14]),
                                    momentum_threshold=_rng_frontend.uniform(0.5, 2.0),
                                    bb_period=_rng_frontend.choice([20, 25]),
                                    bb_width_threshold=_rng_frontend.uniform(0.03, 0.08),
                                    use_supertrend=use_supertrend,
                                    supertrend_period=_rng_frontend.choice([10, 14, 20]) if use_supertrend else 10,
                                    supertrend_multiplier=_rng_frontend.uniform(2.0, 4.0) if use_supertrend else 3.0,
                                    use_parabolic_sar=use_parabolic_sar,
                                    use_donchian=use_donchian,
                                    donchian_period=_rng_frontend.choice([20, 30, 40]) if use_donchian else 20,
                                    donchian_threshold=_rng_frontend.uniform(0.02, 0.06) if use_donchian else 0.04,
                                    use_vwap=use_vwap,
                                    use_obv=use_obv,
                                    use_cmf=use_cmf,
                                    cmf_period=_rng_frontend.choice([14, 20, 21]) if use_cmf else 20,
                                    cmf_threshold=_rng_frontend.uniform(0.0, 0.15) if use_cmf else 0.05,
                                    use_elder_ray=use_elder_ray,
                                    elder_ray_period=_rng_frontend.choice([13, 21, 34]) if use_elder_ray else 13,
                                    min_signals=_rng_frontend.integers(2, 6)
                                )
                            
                            # Run backtest with custom commission
                            engine = BacktestingEngine(
                                initial_capital=initial_capital,
                                commission=commission_decimal,
                                allow_short=True,  # Short réactivé
                                min_hold_minutes=min_hold_minutes
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
                    
                    # All iterations complete - display best result (mode séquentiel uniquement)
                    if not enable_parallel:
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
            
            if st.button("💾 Sauvegarder la stratégie", type="primary", key="save_strategy_btn", width='stretch'):
                # Log button click
                logger.info(f"Save button clicked for strategy: {strategy_name}")
                
                # Update strategy name before saving
                best_strategy.name = strategy_name
                try:
                    with st.spinner(f"Sauvegarde de '{strategy_name}'..."):
                        logger.info("Calling StrategyManager.save_strategy...")
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
                st.dataframe(trades_df, width='stretch')
    
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
                        if st.button("📊 Voir backtests", key=f"view_{strat['id']}"):
                            backtests = StrategyManager.get_strategy_backtests(strat['id'])
                            if backtests:
                                st.dataframe(pd.DataFrame(backtests), width='stretch')
                    
                    with col_b:
                        if st.button("🗑️ Supprimer", key=f"delete_{strat['id']}", type="secondary"):
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
            
            if st.button("▶️ Lancer le backtest", type="primary", width='stretch'):
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
                            st.dataframe(trades_df, width='stretch')
                        
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
                            if st.button("💾 Sauvegarder", type="primary", width='stretch'):
                                try:
                                    # Get original strategy
                                    from backend.strategy_manager import StrategyManager
                                    original_strategy = StrategyManager.get_strategy_by_id(selected_strategy_id)
                                    
                                    if original_strategy:
                                        # Create new strategy with updated description
                                        new_description = """Stratégie dérivée de '{selected_strategy_name}'
                                        
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


def live_prices_page():
    """Live prices page with real-time chart updates"""
    st.header("📊 Cours Live")
    
    # Get tickers with collected data
    from backend.models import SessionLocal, Ticker
    db = SessionLocal()
    
    try:
        tickers = db.query(Ticker).all()
        
        if not tickers:
            st.warning("⚠️ Aucune action disponible. Collectez des données d'abord dans l'onglet 'Collecte de Données'.")
            return
        
        # Create ticker selection
        ticker_options = {ticker.symbol: f"{ticker.symbol} - {ticker.name}" for ticker in tickers}
        
        # Strategy selection
        from backend.models import Strategy
        from backend.strategy_adapter import StrategyAdapter
        import json
        
        strategies = db.query(Strategy).all()
        strategy_options = ["Aucune stratégie"] + [s.name for s in strategies]
        
        selected_strategy_name = st.selectbox(
            "🎯 Stratégie de trading",
            strategy_options,
            help="Sélectionnez une stratégie pour afficher les signaux d'achat/vente. Toutes les stratégies (simples et complexes) sont supportées !"
        )
        
        selected_strategy = None
        if selected_strategy_name != "Aucune stratégie":
            selected_strategy = db.query(Strategy).filter(Strategy.name == selected_strategy_name).first()
            
            # Display strategy info using adapter
            if selected_strategy:
                try:
                    strategy_info = StrategyAdapter.format_strategy_info(selected_strategy)
                    
                    with st.expander("📊 Détails de la stratégie", expanded=False):
                        st.write(f"**Type:** {strategy_info['type']}")
                        st.write(f"**Description:** {strategy_info['description']}")
                        
                        if strategy_info['indicators']:
                            st.write(f"**Indicateurs utilisés:** {', '.join(strategy_info['indicators'])}")
                        
                        # Affichage spécifique pour EnhancedMA
                        if strategy_info['is_enhanced']:
                            st.markdown("#### 🔧 Paramètres de la stratégie")
                            col1, col2, col3 = st.columns(3)
                            with col1:
                                st.metric("MA Rapide", strategy_info.get('fast_period', 'N/A'))
                            with col2:
                                st.metric("MA Lente", strategy_info.get('slow_period', 'N/A'))
                            with col3:
                                st.metric("Signaux min", strategy_info.get('min_signals', 'N/A'))
                            
                            if strategy_info.get('active_advanced_indicators'):
                                st.markdown("**Indicateurs avancés actifs:**")
                                st.write(", ".join(strategy_info['active_advanced_indicators']))
                        
                        # Affichage pour stratégies simples
                        elif strategy_info['is_simple']:
                            col_buy, col_sell = st.columns(2)
                            with col_buy:
                                st.markdown("**🟢 Conditions d'achat:**")
                                st.code(strategy_info.get('buy_conditions', 'N/A'), language='python')
                            
                            with col_sell:
                                st.markdown("**🔴 Conditions de vente:**")
                                st.code(strategy_info.get('sell_conditions', 'N/A'), language='python')
                
                except Exception as e:
                    st.warning(f"⚠️ Impossible d'afficher les détails de la stratégie: {e}")

        
        # Data source selection
        st.markdown("---")
        st.subheader("📡 Source de Données : IBKR (Temps Réel)")
        st.info("💼 Données temps réel via IB Gateway - Aucune limitation")
        
        # Use global IBKR connection
        init_global_ibkr_connection()
        
        # Check global connection status
        ibkr_connected = st.session_state.get('global_ibkr_connected', False)
        
        if ibkr_connected:
            st.success("🟢 IBKR Connecté (connexion globale)")
        else:
            st.warning("� IBKR Non connecté - Connectez-vous depuis la barre latérale")
            st.info("💡 Utilisez le bouton de connexion IBKR dans la sidebar pour établir la connexion globale")
            return
        
        st.markdown("---")
        
        # Create ticker selection and time scale
        col1, col2, col3 = st.columns([2, 1, 1])
        
        with col1:
            selected_symbol = st.selectbox(
                "Sélectionner une action",
                options=list(ticker_options.keys()),
                format_func=lambda x: ticker_options[x]
            )
        
        with col2:
            # Time scale selector
            time_scale = st.selectbox(
                "Échelle de temps",
                options=["1s", "1min", "5min", "15min", "30min", "1h", "1jour"],
                index=0,
                help="Période d'agrégation des données",
                disabled=st.session_state.get('live_running', False)
            )
        
        with col3:
            # Control buttons
            if 'live_running' not in st.session_state:
                st.session_state.live_running = False
            
            if st.session_state.live_running:
                if st.button("⏸️ Pause", type="primary"):
                    st.session_state.live_running = False
                    st.rerun()
            else:
                if st.button("▶️ Démarrer", type="primary"):
                    st.session_state.live_running = True
                    st.rerun()
        
        st.markdown("---")
        
        # Display area for metrics
        metric_col1, metric_col2, metric_col3, metric_col4 = st.columns(4)
        
        # Placeholders for dynamic updates
        with metric_col1:
            price_placeholder = st.empty()
        with metric_col2:
            change_placeholder = st.empty()
        with metric_col3:
            volume_placeholder = st.empty()
        with metric_col4:
            time_placeholder = st.empty()
        
        # Chart placeholder
        chart_placeholder = st.empty()
        
        # Indicators placeholder
        indicators_placeholder = st.empty()
        
        # Info message
        st.info("ℹ️ Les données proviennent d'IBKR en temps réel. Le graphique se rafraîchit toutes les secondes.")
        
        # Initialize data storage
        if 'live_data' not in st.session_state:
            st.session_state.live_data = {'time': [], 'price': []}
        
        # Check if we need to reload historical data (ticker or time scale changed)
        reload_needed = (
            st.session_state.get('last_ticker') != selected_symbol or
            st.session_state.get('last_time_scale') != time_scale
        )
        
        if reload_needed:
            st.session_state.last_ticker = selected_symbol
            st.session_state.last_time_scale = time_scale
            
            # Initialize live_data only once (on first run for this symbol)
            if 'live_data' not in st.session_state or st.session_state.get('live_symbol') != selected_symbol:
                st.session_state.live_symbol = selected_symbol
                
                # Load historical data from database
                from backend.models import HistoricalData
                ticker_obj = db.query(Ticker).filter(Ticker.symbol == selected_symbol).first()
                
                historical_records = db.query(HistoricalData).filter(
                    HistoricalData.ticker_id == ticker_obj.id,
                    HistoricalData.interval == time_scale
                ).order_by(HistoricalData.timestamp.asc()).all()
                
                if historical_records:
                    st.session_state.live_data = {
                        'time': [rec.timestamp for rec in historical_records],
                        'price': [rec.close for rec in historical_records],
                        'open': [rec.open for rec in historical_records],
                        'high': [rec.high for rec in historical_records],
                        'low': [rec.low for rec in historical_records],
                        'volume': [rec.volume for rec in historical_records]
                    }
                    st.success(f"✅ {len(historical_records)} données historiques chargées depuis la base de données")
                else:
                    st.session_state.live_data = {
                        'time': [], 
                        'price': [],
                        'open': [],
                        'high': [],
                        'low': [],
                        'volume': []
                    }
                    st.info("ℹ️ Aucune donnée historique. Les données seront collectées en temps réel.")
        
        # Live update loop
        if st.session_state.live_running:
            import plotly.graph_objects as go
            from datetime import datetime
            import pandas as pd
            from backend.models import HistoricalData
            import time as time_module_local
            import json
            
            # Get ticker object for database storage
            ticker_obj = db.query(Ticker).filter(Ticker.symbol == selected_symbol).first()
            
            # Start background Celery task if not already running
            if not st.session_state.get('live_task_id'):
                try:
                    from backend.live_data_task import stream_live_data_continuous
                    # Start task in background (30 minutes max)
                    task = stream_live_data_continuous.apply_async(
                        args=[selected_symbol, 1800],  # 30 minutes
                        expires=1800
                    )
                    st.session_state.live_task_id = task.id
                    logger.info(f"[UI] Started live data task {task.id} for {selected_symbol}")
                except Exception as e:
                    logger.warning(f"[UI] Could not start Celery task: {e}")
                    st.session_state.live_task_id = None
            
            # Non-blocking approach: Read latest data from Redis or IBKR
            max_points = 200  # Keep last 200 points for better visualization
            
            # Collect one data point from Redis or IBKR (non-blocking approach)
            current_price = None
            current_volume = None
            current_time = None
            price_change = 0
            price_change_pct = 0
            
            try:
                # Try to get latest data from Redis first
                import redis
                try:
                    redis_client = redis.Redis(host='localhost', port=6379, db=0, decode_responses=True)
                    redis_data = redis_client.get(f"live_data:{selected_symbol}")
                    if redis_data:
                        data_point = json.loads(redis_data)
                        current_price = data_point.get('price')
                        current_volume = data_point.get('volume', 0)
                        current_time = datetime.fromisoformat(data_point.get('timestamp', datetime.now().isoformat()))
                except Exception as redis_err:
                    redis_client = None
                
                # Fallback: Get from IBKR directly if Redis unavailable
                if not current_price and st.session_state.get('global_ibkr_connected', False):
                    collector = st.session_state.global_ibkr
                    contract = collector.get_contract(selected_symbol)
                    
                    if contract:
                        try:
                            # Request market data WITHOUT blocking - set SHORT timeout
                            ticker_data = collector.ib.reqMktData(contract, '', False, False)
                            # Wait max 2 seconds for data (delayed data takes longer)
                            max_wait = 20  # 2 seconds in tenths
                            wait_count = 0
                            while (ticker_data.last == 0 and ticker_data.close == 0) and wait_count < max_wait:
                                collector.ib.sleep(0.1)
                                wait_count += 1
                            
                            # Use 'last' if available, fallback to 'close' for delayed data
                            current_price = ticker_data.last if ticker_data.last > 0 else ticker_data.close
                            
                            if current_price > 0:
                                current_volume = ticker_data.volume if ticker_data.volume > 0 else 0
                                current_time = datetime.now()
                                
                                logger.debug(f"[UI] Got {selected_symbol} from IBKR: {current_price}€ (volume: {current_volume})")
                        finally:
                            # Always cancel market data subscription
                            try:
                                collector.ib.cancelMktData(contract)
                            except Exception:
                                pass
                    else:
                        st.error(f"❌ Impossible de trouver le contrat pour {selected_symbol}")
                        st.session_state.live_running = False
                else:
                    if not st.session_state.get('global_ibkr_connected', False):
                        st.error("❌ Connexion IBKR perdue")
                        st.session_state.live_running = False
            except Exception as e:
                logger.error(f"Error collecting live data: {e}", exc_info=True)
                st.warning(f"⚠️ Erreur lors de la collecte: {e}")
            
            if current_price:  # Only update metrics if we have data
                # Get previous close
                if len(st.session_state.live_data['price']) > 0:
                    prev_close = st.session_state.live_data['price'][-1]
                else:
                    prev_close = current_price
                
                # Calculate change
                price_change = current_price - prev_close
                price_change_pct = (price_change / prev_close * 100) if prev_close else 0
                
                # Add to live data - ALWAYS add to build up history
                # Don't check if price changed - add every point for smooth graphing
                st.session_state.live_data['time'].append(current_time)
                st.session_state.live_data['price'].append(current_price)
                st.session_state.live_data['open'].append(current_price)  # Simplified for live data
                st.session_state.live_data['high'].append(current_price)
                st.session_state.live_data['low'].append(current_price)
                st.session_state.live_data['volume'].append(current_volume)
                
                # Update metrics
                price_placeholder.metric(
                    "Prix Actuel",
                    f"{current_price:.2f} €",
                    f"{price_change:+.2f} ({price_change_pct:+.2f}%)"
                )
                
                change_placeholder.metric(
                    "Variation",
                    f"{price_change_pct:+.2f}%",
                    f"{price_change:+.2f} €"
                )
                
                volume_placeholder.metric(
                    "Volume",
                    f"{int(current_volume):,}" if current_volume else "N/A"
                )
                
                time_placeholder.metric(
                    "Dernière MAJ",
                    current_time.strftime("%H:%M:%S")
                )
            
            # Calculate indicators for live data if enough points
            # (Always do this, even if no new price yet - keeps graph fresh)
            buy_signals = []
            sell_signals = []
            signal_times = []
            signal_prices = []
            signal_types = []
            latest_rsi = None
            latest_macd = None
            latest_macd_signal = None
            
            # Create live DataFrame even with few points
            live_df = None
            if len(st.session_state.live_data['price']) > 0:
                # Create DataFrame for indicator calculation
                live_df = pd.DataFrame({
                    'close': st.session_state.live_data['price'],
                    'time': st.session_state.live_data['time']
                })
                
                # Add OHLCV data if available (from historical data)
                if 'open' in st.session_state.live_data and len(st.session_state.live_data['open']) > 0:
                    live_df['high'] = st.session_state.live_data.get('high', live_df['close'])
                    live_df['low'] = st.session_state.live_data.get('low', live_df['close'])
                    live_df['open'] = st.session_state.live_data.get('open', live_df['close'])
                    live_df['volume'] = st.session_state.live_data.get('volume', [0] * len(live_df))
                else:
                    # Approximation for line chart if no OHLCV data
                    live_df['high'] = live_df['close']
                    live_df['low'] = live_df['close']
                    live_df['open'] = live_df['close']
                    live_df['volume'] = 0
                
                # Only calculate indicators if enough points (50+)
                if len(st.session_state.live_data['price']) >= 50:
                    # Calculate indicators
                    from backend.technical_indicators import calculate_and_update_indicators
                    live_df = calculate_and_update_indicators(live_df, save_to_db=False)
                    
                    # Determine buy/sell signals based on selected strategy
                    latest_rsi = live_df['rsi_14'].iloc[-1] if 'rsi_14' in live_df.columns else None
                    latest_macd = live_df['macd'].iloc[-1] if 'macd' in live_df.columns else None
                    latest_macd_signal = live_df['macd_signal'].iloc[-1] if 'macd_signal' in live_df.columns else None
                    
                    signal = "NEUTRE"
                    signal_color = "gray"
                    
                    # Apply strategy if selected - using StrategyAdapter for ALL strategy types
                    if selected_strategy:
                        try:
                            from backend.strategy_adapter import StrategyAdapter
                            
                            # Generate signals using the adapter (works for simple AND complex strategies)
                            signal_times, signal_prices, signal_types = StrategyAdapter.generate_signals(live_df, selected_strategy)
                            
                            # Get current signal
                            signal, signal_color = StrategyAdapter.get_current_signal(live_df, selected_strategy)
                            
                        except Exception as e:
                            st.warning(f"⚠️ Erreur lors de l'évaluation de la stratégie: {e}")
                            import traceback
                            st.code(traceback.format_exc())
                            # Fallback to simple strategy
                            if latest_rsi and latest_macd and latest_macd_signal:
                                if latest_rsi < 30 and latest_macd > latest_macd_signal:
                                    signal = "ACHAT 🟢"
                                    signal_color = "green"
                                elif latest_rsi > 70 and latest_macd < latest_macd_signal:
                                    signal = "VENTE 🔴"
                                    signal_color = "red"
                    else:
                        # Simple default strategy logic if no strategy selected
                        if latest_rsi and latest_macd and latest_macd_signal:
                            if latest_rsi < 30 and latest_macd > latest_macd_signal:
                                signal = "ACHAT 🟢"
                                signal_color = "green"
                            elif latest_rsi > 70 and latest_macd < latest_macd_signal:
                                signal = "VENTE 🔴"
                                signal_color = "red"
                else:
                    signal = f"Calcul... ({len(st.session_state.live_data['price'])}/50 points)"
                    signal_color = "orange"
            else:
                signal = "En attente de données..."
                signal_color = "orange"
            
            # Create line chart - ALWAYS, even if no data yet
            fig = go.Figure()
            
            # Main price line - only if we have data
            if len(st.session_state.live_data['price']) > 0:
                fig.add_trace(go.Scatter(
                    x=st.session_state.live_data['time'],
                    y=st.session_state.live_data['price'],
                    mode='lines',
                    name='Prix',
                    line=dict(color='#00D9FF', width=2),
                    fill='tozeroy',
                    fillcolor='rgba(0, 217, 255, 0.1)'
                ))
            else:
                # Show empty chart message
                fig.add_annotation(
                    text="En attente de données...",
                    xref="paper", yref="paper",
                    x=0.5, y=0.5, showarrow=False,
                    font=dict(size=20, color="gray")
                )
            
            # Add historical buy/sell markers if strategy is selected
            if signal_times and signal_prices and signal_types:
                buy_times = [t for t, typ in zip(signal_times, signal_types) if typ == 'buy']
                buy_prices = [p for p, typ in zip(signal_prices, signal_types) if typ == 'buy']
                sell_times = [t for t, typ in zip(signal_times, signal_types) if typ == 'sell']
                sell_prices = [p for p, typ in zip(signal_prices, signal_types) if typ == 'sell']
                
                if buy_times:
                    fig.add_trace(go.Scatter(
                        x=buy_times,
                        y=buy_prices,
                        mode='markers',
                        name='Signaux Achat (Historique)',
                        marker=dict(size=12, color='green', symbol='triangle-up', line=dict(width=1, color='darkgreen'))
                    ))
                
                if sell_times:
                    fig.add_trace(go.Scatter(
                        x=sell_times,
                        y=sell_prices,
                        mode='markers',
                        name='Signaux Vente (Historique)',
                        marker=dict(size=12, color='red', symbol='triangle-down', line=dict(width=1, color='darkred'))
                    ))
                    
                    # Show count of signals
                    total_signals = len(buy_times) + len(sell_times)
                    st.info(f"📊 {total_signals} signaux détectés : {len(buy_times)} achats, {len(sell_times)} ventes")
            
            # Add current signal marker if signal is present
            if signal.startswith("ACHAT") and len(st.session_state.live_data['price']) > 0:
                fig.add_trace(go.Scatter(
                    x=[st.session_state.live_data['time'][-1]],
                    y=[st.session_state.live_data['price'][-1]],
                    mode='markers',
                    name='Signal Achat (Actuel)',
                    marker=dict(size=18, color='lime', symbol='triangle-up', line=dict(width=2, color='green'))
                ))
            elif signal.startswith("VENTE") and len(st.session_state.live_data['price']) > 0:
                fig.add_trace(go.Scatter(
                    x=[st.session_state.live_data['time'][-1]],
                    y=[st.session_state.live_data['price'][-1]],
                    mode='markers',
                    name='Signal Vente (Actuel)',
                    marker=dict(size=18, color='orangered', symbol='triangle-down', line=dict(width=2, color='red'))
                ))
            
            # Update layout for all cases - OUTSIDE the conditional blocks
            fig.update_layout(
                title=f"{selected_symbol} - Cours en temps réel ({time_scale}) - Signal: {signal}",
                xaxis_title="Heure",
                yaxis_title="Prix (€)",
                xaxis=dict(
                    tickformat='%H:%M:%S',  # Format avec les secondes
                    tickmode='auto',
                    nticks=10
                ),
                height=500,
                hovermode='x unified',
                showlegend=True,
                margin=dict(l=50, r=50, t=50, b=50)
            )
            
            # Update chart without reloading entire page
            chart_placeholder.plotly_chart(fig, use_container_width=True)
            
            # Display indicators below chart - always show the panel
            with indicators_placeholder.container():
                st.markdown("---")
                st.subheader("📊 Indicateurs Techniques")
                
                ind_col1, ind_col2, ind_col3 = st.columns(3)
                
                with ind_col1:
                    if latest_rsi:
                        rsi_delta = "Suracheté" if latest_rsi > 70 else "Survendu" if latest_rsi < 30 else "Normal"
                        st.metric("RSI (14)", f"{latest_rsi:.2f}", rsi_delta)
                    else:
                        st.metric("RSI (14)", "---", "En attente...")
                
                with ind_col2:
                    if latest_macd:
                        st.metric("MACD", f"{latest_macd:.4f}")
                    else:
                        st.metric("MACD", "---", "En attente...")
                
                with ind_col3:
                    st.markdown(f"### Signal: :{signal_color}[{signal}]")
                
                # Display strategy analysis if strategy selected and signals found
                if selected_strategy and signal_times and signal_prices and signal_types:
                    st.markdown("---")
                    st.subheader(f"🎯 Analyse de la stratégie: {selected_strategy_name}")
                    
                    # Simulate trades based on signals
                    position = None  # None = no position, 'long' = bought
                    trades = []
                    
                    for i, (time, price, typ) in enumerate(zip(signal_times, signal_prices, signal_types)):
                        if typ == 'buy' and position is None:
                            # Open long position
                            position = {'entry_time': time, 'entry_price': price}
                        elif typ == 'sell' and position is not None:
                            # Close long position
                            profit = price - position['entry_price']
                            profit_pct = (profit / position['entry_price']) * 100
                            trades.append({
                                'entry_time': position['entry_time'],
                                'entry_price': position['entry_price'],
                                'exit_time': time,
                                'exit_price': price,
                                'profit': profit,
                                'profit_pct': profit_pct
                            })
                            position = None
                    
                    # Display trade summary
                    if trades:
                        trade_col1, trade_col2, trade_col3, trade_col4 = st.columns(4)
                        
                        total_trades = len(trades)
                        winning_trades = len([t for t in trades if t['profit'] > 0])
                        losing_trades = len([t for t in trades if t['profit'] < 0])
                        win_rate = (winning_trades / total_trades * 100) if total_trades > 0 else 0
                        
                        total_profit = sum([t['profit'] for t in trades])
                        avg_profit = total_profit / total_trades if total_trades > 0 else 0
                        avg_profit_pct = sum([t['profit_pct'] for t in trades]) / total_trades if total_trades > 0 else 0
                        
                        with trade_col1:
                            st.metric("Nombre de trades", f"{total_trades}")
                        
                        with trade_col2:
                            st.metric("Taux de réussite", f"{win_rate:.1f}%", f"{winning_trades}W / {losing_trades}L")
                        
                        with trade_col3:
                            delta_color = "normal" if total_profit >= 0 else "inverse"
                            st.metric("Profit total", f"{total_profit:.2f} €", f"{sum([t['profit_pct'] for t in trades]):.2f}%", delta_color=delta_color)
                        
                        with trade_col4:
                            st.metric("Profit moyen", f"{avg_profit:.2f} €", f"{avg_profit_pct:.2f}%")
                        
                        # Display recent trades table
                        st.markdown("#### 📋 Derniers trades")
                        recent_trades = trades[-10:]  # Last 10 trades
                        trade_data = []
                        for t in reversed(recent_trades):
                            trade_data.append({
                                'Entrée': t['entry_time'].strftime("%Y-%m-%d %H:%M:%S"),
                                'Prix Entrée': f"{t['entry_price']:.2f} €",
                                'Sortie': t['exit_time'].strftime("%Y-%m-%d %H:%M:%S"),
                                'Prix Sortie': f"{t['exit_price']:.2f} €",
                                'Profit': f"{t['profit']:.2f} €",
                                'Profit %': f"{t['profit_pct']:.2f}%"
                            })
                        
                        st.dataframe(pd.DataFrame(trade_data), width='stretch')
                    else:
                        st.info("ℹ️ Aucun trade complet détecté avec cette stratégie (signaux d'achat sans vente correspondante).")
            
            # Schedule next update using Streamlit's rerun
            # Control refresh rate by checking last update time
            if st.session_state.get('live_running'):
                # Track last update time
                current_time = time_module_local.time()
                last_update = st.session_state.get('last_live_update', 0)
                
                # Only rerun every 2 seconds to prevent flickering
                if current_time - last_update >= 2.0:
                    st.session_state.last_live_update = current_time
                    st.rerun()
        else:
            # Not running - show static message
            st.info("👆 Cliquez sur 'Démarrer' pour afficher les cours en temps réel")
            
    finally:
        db.close()




def trading_page():
    """Trading page with IBKR integration"""
    st.header("💼 Trading")
    
    try:
        from backend.ibkr_collector import IBKRCollector
        from ib_insync import Stock, MarketOrder, LimitOrder
        
        # Connection state managed globally (initialized in main())
        
        # Connection section
        col_connect1, col_connect2 = st.columns([2, 1])
        
        with col_connect1:
            if not st.session_state.get('global_ibkr_connected', False):
                if st.button("🔌 Connecter à IBKR", type="primary", width='stretch'):
                    try:
                        with st.spinner("Connexion à IB Gateway..."):
                            # Use global IBKR connection from main()
                            success, message = connect_global_ibkr()
                            if success:
                                st.success("✅ Connecté à IBKR!")
                                st.rerun()
                            else:
                                st.error("❌ Échec de la connexion")
                    except Exception as e:
                        st.error(f"❌ Erreur: {e}")
            else:
                if st.button("🔌 Déconnecter", width='stretch'):
                    disconnect_global_ibkr()
                    st.success("Déconnecté")
                    st.rerun()
        
        with col_connect2:
            if st.session_state.get('global_ibkr_connected', False):
                st.success("🟢 Connecté")
            else:
                st.error("🔴 Déconnecté")
        
        if not st.session_state.get('global_ibkr_connected', False):
            st.info("👆 Connectez-vous à IB Gateway pour commencer le trading")
            st.markdown("---")
            st.markdown("""
            ### 📋 Prérequis
            
            1. **IB Gateway** doit être démarré
            2. **API activée** dans Configuration → API → Settings
            3. **Port configuré** (par défaut: 4002 pour paper trading)
            4. **IP autorisée** (127.0.0.1 dans Trusted IPs)
            """)
            return
        
        # Use global IBKR connection (client_id=1)
        collector = st.session_state.global_ibkr
        
        st.markdown("---")
        
        # Account Summary
        st.subheader("💰 Résumé du Compte")
        
        col_acc1, col_acc2, col_acc3, col_acc4 = st.columns(4)
        
        try:
            account_summary = collector.get_account_summary()
            
            if account_summary and 'EUR' in account_summary:
                eur_data = account_summary['EUR']
                
                with col_acc1:
                    net_liq = float(eur_data.get('NetLiquidation', 0))
                    st.metric("💰 Valeur Nette", f"{net_liq:,.2f} €")
                
                with col_acc2:
                    buying_power = float(eur_data.get('BuyingPower', 0))
                    st.metric("💪 Pouvoir d'Achat", f"{buying_power:,.2f} €")
                
                with col_acc3:
                    unrealized_pnl = float(eur_data.get('UnrealizedPnL', 0))
                    st.metric("📈 P&L Non Réalisé", f"{unrealized_pnl:,.2f} €", 
                             delta=f"{unrealized_pnl:+.2f} €" if unrealized_pnl != 0 else None)
                
                with col_acc4:
                    realized_pnl = float(eur_data.get('RealizedPnL', 0))
                    st.metric("✅ P&L Réalisé", f"{realized_pnl:,.2f} €",
                             delta=f"{realized_pnl:+.2f} €" if realized_pnl != 0 else None)
        
        except Exception as e:
            st.warning(f"⚠️ Impossible de récupérer le résumé du compte: {e}")
        
        st.markdown("---")
        
        # Positions
        st.subheader("📊 Positions Actuelles")
        
        try:
            positions = collector.get_positions()
            
            if positions:
                positions_df = pd.DataFrame(positions)
                st.dataframe(positions_df, width='stretch')
            else:
                st.info("ℹ️ Aucune position ouverte")
        
        except Exception as e:
            st.warning(f"⚠️ Impossible de récupérer les positions: {e}")
        
        st.markdown("---")
        
        # Trading Interface
        st.subheader("📝 Passer un Ordre")
        
        col_order1, col_order2 = st.columns([2, 1])
        
        with col_order1:
            # Get available tickers from database
            available_tickers = get_available_tickers()
            
            if not available_tickers:
                st.warning("⚠️ Aucun ticker en base. Ajoutez des actions via la recherche IBKR dans l'onglet 'Collecte de Données'.")
                symbol = st.text_input("Symbole (saisie manuelle)", value="WLN", help="Ex: WLN, TTE, GLE, MC")
            else:
                # Symbol selection from available tickers
                ticker_options = list(available_tickers.keys())
                selected_ticker = st.selectbox(
                    "Action",
                    ticker_options,
                    format_func=lambda x: f"{x} - {available_tickers[x]}",
                    help="Sélectionnez une action depuis votre base de données"
                )
                symbol = selected_ticker
            
            # Order details
            col_qty, col_action = st.columns(2)
            
            with col_qty:
                quantity = st.number_input("Quantité", min_value=1, value=10, step=1)
            
            with col_action:
                action = st.selectbox("Action", ["BUY", "SELL"])
            
            # Order type
            order_type = st.selectbox("Type d'ordre", ["Market", "Limit"])
            
            limit_price = None
            if order_type == "Limit":
                limit_price = st.number_input("Prix limite", min_value=0.01, value=10.00, step=0.01, format="%.2")
            
            # Submit order button
            if st.button("📤 Envoyer l'ordre", type="primary", width='stretch'):
                try:
                    with st.spinner("Envoi de l'ordre..."):
                        # Get contract
                        contract = collector.get_contract(symbol)
                        
                        if not contract:
                            st.error(f"❌ Impossible de trouver le contrat pour {symbol}")
                        else:
                            # Create order
                            if order_type == "Market":
                                order = MarketOrder(action, quantity)
                            else:
                                order = LimitOrder(action, quantity, limit_price)
                            
                            # Place order
                            trade = collector.ib.placeOrder(contract, order)
                            
                            st.success(f"✅ Ordre envoyé: {action} {quantity} {symbol}")
                            st.json({
                                'orderId': trade.order.orderId,
                                'status': trade.orderStatus.status,
                                'symbol': symbol,
                                'action': action,
                                'quantity': quantity,
                                'type': order_type
                            })
                            
                            # Wait a bit and refresh
                            collector.ib.sleep(1)
                            
                except Exception as e:
                    st.error(f"❌ Erreur lors de l'envoi de l'ordre: {e}")
                    import traceback
                    st.code(traceback.format_exc())
        
        with col_order2:
            st.markdown("### 📋 Info")
            st.markdown("""
            **Types d'ordres** :
            - **Market** : Exécution immédiate au prix du marché
            - **Limit** : Exécution uniquement au prix spécifié ou mieux
            
            **Actions** :
            - **BUY** : Acheter (ouvrir position longue)
            - **SELL** : Vendre (fermer position ou shorter)
            
            ⚠️ **Mode Simulation**
            Vous tradez sur un compte de démonstration.
            """)
        
        st.markdown("---")
        
        # Manual refresh button
        col_refresh1, col_refresh2 = st.columns([3, 1])
        with col_refresh1:
            st.markdown("### 📋 Ordres en Cours")
        with col_refresh2:
            if st.button("🔄 Rafraîchir", key="refresh_orders_btn"):
                st.rerun()
        
        try:
            open_orders = collector.ib.openOrders()
            
            if open_orders:
                orders_data = []
                for trade in open_orders:
                    orders_data.append({
                        'Order ID': trade.order.orderId,
                        'Symbol': trade.contract.symbol,
                        'Action': trade.order.action,
                        'Qty': trade.order.totalQuantity,
                        'Type': trade.order.orderType,
                        'Status': trade.orderStatus.status,
                        'Filled': trade.orderStatus.filled,
                        'Remaining': trade.orderStatus.remaining,
                        'Avg Price': f"{trade.orderStatus.avgFillPrice:.2f}" if trade.orderStatus.avgFillPrice > 0 else "N/A"
                    })
                
                orders_df = pd.DataFrame(orders_data)
                st.dataframe(orders_df, width='stretch', use_container_width=True)
                
                # Action buttons for each order - Direct cancel buttons
                st.markdown("#### Actions rapides")
                
                # Create columns for buttons
                button_cols = st.columns(min(3, len(open_orders)))  # Max 3 buttons per row
                
                for idx, trade in enumerate(open_orders):
                    col = button_cols[idx % len(button_cols)]
                    with col:
                        order_id = trade.order.orderId
                        symbol = trade.contract.symbol
                        qty = trade.order.totalQuantity
                        status = trade.orderStatus.status
                        
                        button_text = f"❌ Annuler\n{symbol} {qty}\n(#{order_id})"
                        
                        if st.button(
                            button_text,
                            type="secondary",
                            use_container_width=True,
                            key=f"cancel_order_{order_id}"
                        ):
                            try:
                                collector.ib.cancelOrder(trade.order)
                                st.success(f"✅ Ordre {order_id} annulé!")
                                collector.ib.sleep(0.5)
                                st.rerun()
                            except Exception as e:
                                st.error(f"❌ Erreur: {e}")
            else:
                st.info("ℹ️ Aucun ordre en cours")
        
        except Exception as e:
            st.warning(f"⚠️ Impossible de récupérer les ordres: {e}")
        
        st.markdown("---")
        
        # Recent Trades
        st.subheader("📜 Historique des Trades")
        
        try:
            fills = collector.ib.fills()
            
            if fills:
                fills_data = []
                for fill in fills:
                    fills_data.append({
                        'Date': fill.time,
                        'Symbol': fill.contract.symbol,
                        'Action': fill.execution.side,
                        'Quantity': fill.execution.shares,
                        'Prix': f"{fill.execution.price:.2f}",
                        'Commission': f"{fill.commissionReport.commission:.2f}" if fill.commissionReport else "N/A"
                    })
                
                fills_df = pd.DataFrame(fills_data)
                st.dataframe(fills_df, width='stretch')
            else:
                st.info("ℹ️ Aucun trade exécuté")
        
        except Exception as e:
            st.warning(f"⚠️ Impossible de récupérer l'historique: {e}")
    
    except ImportError:
        st.error("❌ Module ib_insync non installé")
        st.code("pip install ib_insync")
    
    except Exception as e:
        st.error(f"❌ Erreur: {e}")
        import traceback
        st.code(traceback.format_exc())


def order_placement_page():
    """
    Dedicated page for order placement and management
    Integrated with database tracking and IBKR execution
    """
    st.header("📝 Passage d'Ordres")
    
    # Auto-refresh settings
    if 'auto_refresh_enabled' not in st.session_state:
        st.session_state.auto_refresh_enabled = False
    if 'last_sync_time' not in st.session_state:
        st.session_state.last_sync_time = 0
    if 'previous_order_statuses' not in st.session_state:
        st.session_state.previous_order_statuses = {}
    
    try:
        from backend.order_manager import OrderManager
        from backend.ibkr_collector import IBKRCollector
        from sqlalchemy import func
        
        # Initialize session state
        if 'order_manager' not in st.session_state:
            st.session_state.order_manager = None
        
        # Check IBKR connection
        init_global_ibkr_connection()
        
        # IBKR Connection Status
        col_status1, col_status2, col_status3, col_status4 = st.columns([2, 1, 1, 1])
        
        with col_status1:
            # Use the GLOBAL connection state
            if st.session_state.get('global_ibkr_connected', False):
                st.success("🟢 Connecté à IBKR")
            else:
                st.warning("🟡 Non connecté à IBKR - Les ordres seront enregistrés mais non exécutés")
        
        with col_status2:
            if st.button("🔄 Rafraîchir"):
                st.rerun()
        
        with col_status3:
            # Initialize OrderManager with GLOBAL IBKR collector
            ibkr_collector = st.session_state.get('global_ibkr')
            if not st.session_state.order_manager or st.session_state.order_manager.ibkr_collector != ibkr_collector:
                st.session_state.order_manager = OrderManager(ibkr_collector)
        
        with col_status4:
            # Auto-refresh toggle
            auto_refresh = st.toggle("🔄 Auto-refresh", value=st.session_state.auto_refresh_enabled, help="Synchronise automatiquement toutes les 30 secondes")
            if auto_refresh != st.session_state.auto_refresh_enabled:
                st.session_state.auto_refresh_enabled = auto_refresh
                if auto_refresh:
                    st.session_state.last_sync_time = time_module.time()
                st.rerun()
        
        # Auto-refresh logic
        if st.session_state.auto_refresh_enabled and st.session_state.get('global_ibkr_connected', False):
            current_time = time_module.time()
            # Check if 30 seconds have passed
            if current_time - st.session_state.last_sync_time >= 30:
                # Get current order statuses before sync
                db = SessionLocal()
                try:
                    orders_before = db.query(Order).filter(
                        Order.status.in_([OrderStatus.PENDING, OrderStatus.SUBMITTED])
                    ).all()
                    before_statuses = {order.id: order.status for order in orders_before}
                finally:
                    db.close()
                
                # Sync with IBKR
                count = st.session_state.order_manager.sync_with_ibkr()
                st.session_state.last_sync_time = current_time
                
                # Check for status changes and show notifications
                db = SessionLocal()
                try:
                    orders_after = db.query(Order).all()
                    
                    for order in orders_after:
                        old_status = before_statuses.get(order.id)
                        if old_status and old_status != order.status:
                            # Status changed!
                            if order.status == OrderStatus.FILLED:
                                st.toast(f"🎉 Ordre #{order.id} REMPLI ! {order.action} {order.quantity} {order.ticker.symbol if order.ticker else 'N/A'}", icon="🎉")
                            elif order.status == OrderStatus.CANCELLED:
                                st.toast(f"⚠️ Ordre #{order.id} ANNULÉ", icon="⚠️")
                            elif order.status == OrderStatus.FAILED:
                                st.toast(f"❌ Ordre #{order.id} ÉCHOUÉ", icon="❌")
                finally:
                    db.close()
                
                if count > 0:
                    st.rerun()
            
            # Show countdown to next sync
            time_until_next = 30 - (current_time - st.session_state.last_sync_time)
            if time_until_next > 0:
                st.caption(f"⏱️ Prochaine synchro dans {int(time_until_next)}s")
                time_module.sleep(1)
                st.rerun()
            
            # Sync button
            if st.session_state.get('global_ibkr_connected', False):
                if st.button("🔄 Sync IBKR"):
                    # Get current order statuses before sync
                    db = SessionLocal()
                    try:
                        orders_before = db.query(Order).filter(
                            Order.status.in_([OrderStatus.PENDING, OrderStatus.SUBMITTED])
                        ).all()
                        before_statuses = {order.id: order.status for order in orders_before}
                    finally:
                        db.close()
                    
                    with st.spinner("Synchronisation..."):
                        count = st.session_state.order_manager.sync_with_ibkr()
                        st.session_state.last_sync_time = time_module.time()
                        
                        # Check for status changes and show notifications
                        db = SessionLocal()
                        try:
                            orders_after = db.query(Order).all()
                            
                            for order in orders_after:
                                old_status = before_statuses.get(order.id)
                                if old_status and old_status != order.status:
                                    # Status changed!
                                    if order.status == OrderStatus.FILLED:
                                        st.success(f"🎉 Ordre #{order.id} REMPLI ! {order.action} {order.quantity} {order.ticker.symbol if order.ticker else 'N/A'}")
                                    elif order.status == OrderStatus.CANCELLED:
                                        st.warning(f"⚠️ Ordre #{order.id} ANNULÉ")
                                    elif order.status == OrderStatus.FAILED:
                                        st.error(f"❌ Ordre #{order.id} ÉCHOUÉ")
                        finally:
                            db.close()
                        
                        st.success(f"✅ {count} ordres synchronisés")
                        st.rerun()
        
        st.markdown("---")
        
        # Tabs
        tab1, tab2, tab3, tab4 = st.tabs(["📝 Nouvel Ordre", "📋 Ordres en Cours", "📜 Historique", "📊 Statistiques"])
        
        # ========== TAB 1: NOUVEL ORDRE ==========
        with tab1:
            st.subheader("📝 Créer un Nouvel Ordre")
            
            col_form1, col_form2 = st.columns([2, 1])
            
            with col_form1:
                # Get available tickers
                db = SessionLocal()
                try:
                    from backend.models import Ticker
                    tickers = db.query(Ticker).filter(Ticker.is_active == True).order_by(Ticker.symbol).all()
                    ticker_options = {f"{t.symbol} - {t.name}": t.symbol for t in tickers}
                    
                    if not ticker_options:
                        st.warning("⚠️ Aucune action en base. Ajoutez des actions via 'Collecte de Données'.")
                        selected_symbol = st.text_input("Symbole (saisie manuelle)", value="WLN")
                    else:
                        selected_display = st.selectbox("Action", list(ticker_options.keys()))
                        selected_symbol = ticker_options[selected_display]
                finally:
                    db.close()
                
                # Order parameters
                col_action, col_qty = st.columns(2)
                
                with col_action:
                    action = st.selectbox("Action", ["BUY", "SELL"], help="BUY = Acheter, SELL = Vendre")
                
                with col_qty:
                    quantity = st.number_input("Quantité", min_value=1, value=10, step=1)
                
                # Order type
                order_type = st.selectbox(
                    "Type d'Ordre",
                    ["MARKET", "LIMIT", "STOP", "STOP_LIMIT"],
                    help="""
                    - MARKET: Exécution immédiate au prix du marché
                    - LIMIT: Exécution au prix limite ou mieux
                    - STOP: Ordre stop-loss (devient market si prix atteint)
                    - STOP_LIMIT: Ordre stop-limit combiné
                    """
                )
                
                # Conditional price inputs
                limit_price = None
                stop_price = None
                
                if order_type in ["LIMIT", "STOP_LIMIT"]:
                    limit_price = st.number_input(
                        "Prix Limite €",
                        min_value=0.01,
                        value=10.00,
                        step=0.01,
                        format="%.2",
                        help="Prix maximum (achat) ou minimum (vente)"
                    )
                
                if order_type in ["STOP", "STOP_LIMIT"]:
                    stop_price = st.number_input(
                        "Prix Stop €",
                        min_value=0.01,
                        value=9.50,
                        step=0.01,
                        format="%.2",
                        help="Prix de déclenchement de l'ordre"
                    )
                
                # Strategy selection (optional)
                db = SessionLocal()
                try:
                    from backend.models import Strategy
                    strategies = db.query(Strategy).all()
                    strategy_options = {"Aucune": None}
                    strategy_options.update({s.name: s.id for s in strategies})
                    
                    selected_strategy_name = st.selectbox("Stratégie (optionnel)", list(strategy_options.keys()))
                    strategy_id = strategy_options[selected_strategy_name]
                finally:
                    db.close()
                
                # Notes
                notes = st.text_area("Notes (optionnel)", help="Commentaires ou raison de l'ordre")
                
                # Paper trade toggle
                is_paper = st.checkbox("Mode Simulation (Paper Trade)", value=True, help="Cochez pour simuler sans argent réel")
                
                # Submit button
                st.markdown("---")
                
                col_submit1, col_submit2 = st.columns([2, 1])
                
                with col_submit1:
                    if st.button("📤 Envoyer l'Ordre", type="primary", width="stretch"):
                        error_occurred = False
                        try:
                            # Debug: Vérifier que order_manager existe
                            order_manager = st.session_state.order_manager
                            if not order_manager:
                                st.error("❌ OrderManager non initialisé")
                                st.stop()
                            
                            # Debug: Afficher les paramètres
                            st.info(f"🔍 Création ordre: {action} {quantity} {selected_symbol} @ {order_type}")
                            
                            # Créer l'ordre avec timeout (utilise threading pour éviter bloquer Streamlit)
                            with st.spinner(f"📝 Placement de l'ordre {action} {quantity} {selected_symbol}..."):
                                import threading
                                import time
                                
                                order_result = [None]
                                error_result = [None]
                                
                                def place_order():
                                    """TODO: Add docstring."""
                                    try:
                                        order_result[0] = order_manager.create_order(
                                            symbol=selected_symbol,
                                            action=action,
                                            quantity=quantity,
                                            order_type=order_type,
                                            limit_price=limit_price,
                                            stop_price=stop_price,
                                            strategy_id=strategy_id,
                                            notes=notes,
                                            is_paper_trade=is_paper
                                        )
                                    except Exception as e:
                                        error_result[0] = e
                                
                                # Run order placement in a thread with timeout
                                order_thread = threading.Thread(target=place_order, daemon=True)
                                order_thread.start()
                                order_thread.join(timeout=20)  # Wait max 20 seconds (increased from 15s)
                                
                                if order_thread.is_alive():
                                    st.error("❌ Timeout: L'ordre a pris trop longtemps à créer (>20s)")
                                    st.warning("⚠️ Vérifiez votre connexion IBKR et les logs")
                                    order = None
                                elif error_result[0]:
                                    st.error(f"❌ Erreur: {error_result[0]}")
                                    order = order_result[0]
                                else:
                                    order = order_result[0]
                            
                            if order:
                                st.success(f"✅ Ordre créé avec succès! (ID: {order.id})")
                                st.json({
                                    'ID': order.id,
                                    'Symbol': selected_symbol,
                                    'Action': action,
                                    'Quantity': quantity,
                                    'Type': order_type,
                                    'Status': order.status.value,
                                    'Status Message': order.status_message,
                                    'IBKR Order ID': order.ibkr_order_id
                                })
                                
                                # Wait a bit for IBKR processing
                                if order.ibkr_order_id:
                                    import time
                                    time.sleep(1)
                                
                                st.rerun()
                            else:
                                st.error("❌ Échec de la création de l'ordre")
                                st.warning("⚠️ Vérifiez les logs dans le terminal Streamlit pour plus de détails")
                        
                        except Exception as e:
                            error_occurred = True
                            st.error(f"❌ Erreur: {e}")
                            import traceback
                            st.code(traceback.format_exc())
                
                with col_submit2:
                    # Estimate cost
                    if limit_price and order_type in ["LIMIT", "STOP_LIMIT"]:
                        estimated_cost = quantity * limit_price
                        st.metric("💰 Coût Estimé", f"{estimated_cost:.2f} €")
            
            with col_form2:
                st.markdown("### 📋 Guide")
                st.markdown("""
                **Types d'ordres**:
                
                🔵 **MARKET**
                - Exécution immédiate
                - Au meilleur prix disponible
                - Garanti d'être exécuté
                
                🟢 **LIMIT**
                - Prix maximum (achat)
                - Prix minimum (vente)
                - Peut ne pas être exécuté
                
                🟡 **STOP**
                - Stop-loss
                - Devient MARKET si prix atteint
                - Protection contre pertes
                
                🟣 **STOP_LIMIT**
                - Stop-loss + prix limite
                - Plus de contrôle
                - Peut ne pas être exécuté
                
                ---
                
                ⚠️ **Mode Simulation**
                
                Les ordres en mode simulation sont enregistrés dans la base de données mais **utilisent de l'argent fictif**.
                
                Décochez pour trader avec de l'argent réel.
                """)
        
        # ========== TAB 2: ORDRES EN COURS ==========
        with tab2:
            st.subheader("📋 Ordres en Cours")
            
            order_manager = st.session_state.order_manager
            
            # Get pending and submitted orders
            pending_orders = order_manager.get_orders(
                status=OrderStatus.PENDING,
                limit=50
            )
            submitted_orders = order_manager.get_orders(
                status=OrderStatus.SUBMITTED,
                limit=50
            )
            
            all_active = pending_orders + submitted_orders
            
            if all_active:
                # Cancel actions section at top
                st.markdown("### ❌ Actions d'Annulation")
                
                col_action1, col_action2, col_action3 = st.columns([2, 2, 2])
                
                with col_action1:
                    if st.button("🗑️ Annuler TOUS les ordres", type="primary", width="stretch"):
                        if st.session_state.get('confirm_cancel_all', False):
                            # Actually cancel using optimized method
                            with st.spinner("Annulation de tous les ordres..."):
                                result = order_manager.cancel_all_orders()
                                st.success(f"✅ {result['cancelled']} ordres annulés, {result['failed']} échecs")
                                st.session_state.confirm_cancel_all = False
                                import time
                                time.sleep(1)
                                st.rerun()
                        else:
                            # Ask for confirmation
                            st.session_state.confirm_cancel_all = True
                            st.rerun()
                
                with col_action2:
                    if st.session_state.get('confirm_cancel_all', False):
                        if st.button("❌ Annuler", type="secondary", width="stretch"):
                            st.session_state.confirm_cancel_all = False
                            st.rerun()
                        st.warning(f"⚠️ Confirmer l'annulation de {len(all_active)} ordres ?")
                
                with col_action3:
                    cancel_selected_btn = st.button("❌ Annuler la sélection", type="secondary", width="stretch")
                
                st.markdown("---")
                
                # Initialize selected orders in session state
                if 'selected_orders' not in st.session_state:
                    st.session_state.selected_orders = set()
                
                # Display orders table with checkboxes
                st.markdown("### 📋 Ordres Actifs (cochez pour annuler)")
                
                # Prepare orders data
                orders_data = []
                db = SessionLocal()
                try:
                    from backend.models import Ticker
                    
                    for order in all_active:
                        ticker = db.query(Ticker).filter(Ticker.id == order.ticker_id).first()
                        orders_data.append({
                            'order': order,
                            'ID': order.id,
                            'IBKR ID': order.ibkr_order_id or '-',
                            'Symbole': ticker.symbol if ticker else 'N/A',
                            'Action': order.action,
                            'Type': order.order_type,
                            'Qté': order.quantity,
                            'Prix Limite': f"{order.limit_price:.2f} €" if order.limit_price else '-',
                            'Prix Stop': f"{order.stop_price:.2f} €" if order.stop_price else '-',
                            'Status': order.status.value,
                            'Message': order.status_message or '-',
                            'Créé': order.created_at.strftime('%Y-%m-%d %H:%M:%S')
                        })
                finally:
                    db.close()
                
                if orders_data:
                    # Display each order with checkbox
                    for idx, order_info in enumerate(orders_data):
                        order = order_info['order']
                        
                        # Create columns: checkbox (small) + order info (large)
                        col_check, col_info = st.columns([0.5, 11.5])
                        
                        with col_check:
                            is_selected = st.checkbox(
                                f"Select order {order.id}",
                                key=f"order_checkbox_{order.id}",
                                value=order.id in st.session_state.selected_orders,
                                label_visibility="collapsed"
                            )
                            if is_selected:
                                st.session_state.selected_orders.add(order.id)
                            else:
                                st.session_state.selected_orders.discard(order.id)
                        
                        with col_info:
                            # Display order info in a nice format
                            status_emoji = {
                                'pending': '⏳',
                                'submitted': '📤',
                                'filled': '✅',
                                'cancelled': '❌',
                                'error': '🚨'
                            }.get(order.status.value, '❓')
                            
                            action_color = 'green' if order.action == 'BUY' else 'red'
                            
                            st.markdown("""
                            <div style="padding: 8px; background-color: rgba(0,0,0,0.05); border-radius: 5px; margin-bottom: 5px;">
                                <strong>#{order.id}</strong> | 
                                <strong style="color: {action_color};">{order.action}</strong> 
                                <strong>{order.quantity}</strong> {order_info['Symbole']} @ 
                                <strong>{order.order_type}</strong>
                                {f"(Limite: {order_info['Prix Limite']})" if order.limit_price else ""}
                                {f"(Stop: {order_info['Prix Stop']})" if order.stop_price else ""}
                                | {status_emoji} <em>{order.status.value}</em>
                                {f"| IBKR: {order.ibkr_order_id}" if order.ibkr_order_id else ""}
                                | {order_info['Créé']}
                                <br><small style="color: gray;">{order_info['Message']}</small>
                            </div>
                            """, unsafe_allow_html=True)
                
                # Handle cancel selected button
                if cancel_selected_btn:
                    if st.session_state.selected_orders:
                        with st.spinner(f"Annulation de {len(st.session_state.selected_orders)} ordre(s)..."):
                            # Use optimized batch cancel method
                            results = order_manager.cancel_multiple_orders(list(st.session_state.selected_orders))
                            cancelled_count = sum(1 for success in results.values() if success)
                            failed_count = len(results) - cancelled_count
                            
                            if failed_count > 0:
                                st.warning(f"✅ {cancelled_count} ordres annulés, ❌ {failed_count} échecs")
                            else:
                                st.success(f"✅ {cancelled_count} ordres sélectionnés annulés")
                            
                            st.session_state.selected_orders.clear()
                            import time
                            time.sleep(1)
                            st.rerun()
                    else:
                        st.warning("⚠️ Aucun ordre sélectionné")
                
                # Old single cancel section (kept for backward compatibility)
                st.markdown("---")
                st.markdown("### ❌ Annuler un Ordre Spécifique (par ID)")
                
                col_cancel1, col_cancel2 = st.columns([2, 1])
                
                with col_cancel1:
                    order_id_to_cancel = st.number_input(
                        "ID de l'ordre à annuler",
                        min_value=1,
                        step=1,
                        help="Saisissez l'ID depuis le tableau ci-dessus"
                    )
                
                with col_cancel2:
                    if st.button("❌ Annuler", type="secondary", width="stretch", key="cancel_by_id"):
                        try:
                            with st.spinner("Annulation..."):
                                success = order_manager.cancel_order(order_id_to_cancel)
                                if success:
                                    st.success(f"✅ Ordre {order_id_to_cancel} annulé")
                                    import time
                                    time.sleep(1)
                                    st.rerun()
                                else:
                                    st.error("❌ Échec de l'annulation")
                        except Exception as e:
                            st.error(f"❌ Erreur: {e}")
            
            else:
                st.info("ℹ️ Aucun ordre en cours")
        
        # ========== TAB 3: HISTORIQUE ==========
        with tab3:
            st.subheader("📜 Historique des Ordres")
            
            # Filters
            col_filter1, col_filter2, col_filter3 = st.columns(3)
            
            with col_filter1:
                filter_symbol = st.text_input("Filtrer par symbole", placeholder="Ex: WLN")
            
            with col_filter2:
                filter_status = st.selectbox(
                    "Filtrer par status",
                    ["Tous", "FILLED", "CANCELLED", "PENDING", "SUBMITTED", "ERROR"]
                )
            
            with col_filter3:
                limit = st.number_input("Nombre max", min_value=10, max_value=500, value=100, step=10)
            
            # Clean old stuck orders button
            st.markdown("---")
            col_clean1, col_clean2 = st.columns([3, 1])
            with col_clean2:
                if st.button("🧹 Nettoyer ordres bloqués", help="Marque les ordres submitted de plus de 1 jour comme 'CANCELLED'"):
                    db = SessionLocal()
                    try:
                        from datetime import timedelta
                        # Find orders stuck in SUBMITTED for more than 24 hours
                        cutoff_time = datetime.now() - timedelta(days=1)
                        stuck_orders = db.query(Order).filter(
                            Order.status == OrderStatus.SUBMITTED,
                            Order.created_at < cutoff_time
                        ).all()
                        
                        if stuck_orders:
                            for order in stuck_orders:
                                order.status = OrderStatus.CANCELLED
                                order.notes = (order.notes or "") + f"\n[Auto-cancelled: stuck in SUBMITTED for >24h at {datetime.now().strftime('%Y-%m-%d %H:%M')}]"
                            db.commit()
                            st.success(f"✅ {len(stuck_orders)} ordres bloqués nettoyés")
                            st.rerun()
                        else:
                            st.info("ℹ️ Aucun ordre bloqué trouvé")
                    except Exception as e:
                        logger.error(f"Error cleaning stuck orders: {e}")
                        st.error(f"❌ Erreur: {e}")
                    finally:
                        db.close()
            
            # Get orders
            order_manager = st.session_state.order_manager
            
            status_filter = None
            if filter_status != "Tous":
                status_filter = OrderStatus[filter_status]
            
            symbol_filter = filter_symbol if filter_symbol else None
            
            orders = order_manager.get_orders(
                ticker_symbol=symbol_filter,
                status=status_filter,
                limit=limit
            )
            
            if orders:
                orders_data = []
                db = SessionLocal()
                try:
                    from backend.models import Ticker, Strategy
                    
                    for order in orders:
                        ticker = db.query(Ticker).filter(Ticker.id == order.ticker_id).first()
                        strategy = db.query(Strategy).filter(Strategy.id == order.strategy_id).first() if order.strategy_id else None
                        
                        # Calculate P&L for filled orders
                        pnl_str = '-'
                        if order.status == OrderStatus.FILLED and order.avg_fill_price:
                            # This is simplified - real P&L needs matching buy/sell orders
                            pnl_str = f"{order.avg_fill_price * order.filled_quantity:.2f} €"
                        
                        orders_data.append({
                            'ID': order.id,
                            'Date': order.created_at.strftime('%Y-%m-%d %H:%M'),
                            'Symbole': ticker.symbol if ticker else 'N/A',
                            'Action': order.action,
                            'Type': order.order_type,
                            'Qté': order.quantity,
                            'Rempli': order.filled_quantity if order.filled_quantity else 0,
                            'Prix Moy': f"{order.avg_fill_price:.2f} €" if order.avg_fill_price else '-',
                            'Commission': f"{order.commission:.2f} €" if order.commission else '0.00 €',
                            'Status': order.status.value,
                            'Stratégie': strategy.name if strategy else '-',
                            'Paper': '✅' if order.is_paper_trade else '❌'
                        })
                finally:
                    db.close()
                
                orders_df = pd.DataFrame(orders_data)
                
                # Display with color coding
                st.dataframe(
                    orders_df,
                    width="stretch",
                    hide_index=True
                )
                
                # Export button
                csv = orders_df.to_csv(index=False)
                st.download_button(
                    label="📥 Télécharger CSV",
                    data=csv,
                    file_name=f"orders_history_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
                    mime="text/csv"
                )
            
            else:
                st.info("ℹ️ Aucun ordre dans l'historique")
        
        # ========== TAB 4: STATISTIQUES ==========
        with tab4:
            st.subheader("📊 Statistiques des Ordres")
            
            order_manager = st.session_state.order_manager
            
            # Overall statistics
            stats = order_manager.get_order_statistics()
            
            if stats:
                col_stat1, col_stat2, col_stat3, col_stat4 = st.columns(4)
                
                with col_stat1:
                    st.metric("📝 Total Ordres", stats.get('total_orders', 0))
                
                with col_stat2:
                    st.metric("✅ Exécutés", stats.get('filled', 0))
                
                with col_stat3:
                    st.metric("⏳ En Cours", stats.get('pending', 0))
                
                with col_stat4:
                    fill_rate = stats.get('fill_rate', 0)
                    st.metric("📈 Taux d'Exécution", f"{fill_rate:.1f}%")
                
                st.markdown("---")
                
                col_stat5, col_stat6 = st.columns(2)
                
                with col_stat5:
                    total_vol = stats.get('total_volume', 0)
                    st.metric("💰 Volume Total", f"{total_vol:,.2f} €")
                
                with col_stat6:
                    total_comm = stats.get('total_commission', 0)
                    st.metric("💸 Commissions Totales", f"{total_comm:,.2f} €")
                
                # Performance Charts
                st.markdown("---")
                st.subheader("📈 Graphiques de Performance")
                
                db = SessionLocal()
                try:
                    # Get all filled orders
                    filled_orders = db.query(Order).filter(
                        Order.status == OrderStatus.FILLED
                    ).order_by(Order.filled_at).all()
                    
                    if filled_orders:
                        # Chart 1: P&L over time (cumulative) - TODO: Add P&L calculation to Order model
                        # Temporarily disabled until P&L is properly tracked
                        st.info("� Graphiques P&L à venir - Fonctionnalité en développement")
                        
                        # For now, show simple order count over time
                        st.markdown("**📅 Ordres Remplis par Jour**")
                        
                        # Group by day
                        daily_orders = {}
                        for order in filled_orders:
                            if order.filled_at:
                                day = order.filled_at.date()
                                if day not in daily_orders:
                                    daily_orders[day] = 0
                                daily_orders[day] += 1
                        
                        if daily_orders:
                            sorted_days = sorted(daily_orders.keys())
                            order_counts = [daily_orders[day] for day in sorted_days]
                            
                            fig_bar = go.Figure()
                            fig_bar.add_trace(go.Bar(
                                x=sorted_days,
                                y=order_counts,
                                marker=dict(color='steelblue'),
                                name='Ordres'
                            ))
                            fig_bar.update_layout(
                                height=300,
                                margin=dict(l=0, r=0, t=30, b=0),
                                xaxis_title="Date",
                                yaxis_title="Nombre d'Ordres",
                                hovermode='x unified'
                            )
                            st.plotly_chart(fig_bar, use_container_width=True, key="daily_orders_chart")
                        
                        # Chart 2: Order volume by day
                        st.markdown("**📅 Volume d'Ordres par Jour**")
                        
                        # Group by day
                        daily_volume = {}
                        for order in filled_orders:
                            if order.filled_at:
                                day = order.filled_at.date()
                                if day not in daily_volume:
                                    daily_volume[day] = 0
                                if order.filled_quantity and order.avg_fill_price:
                                    daily_volume[day] += order.filled_quantity * order.avg_fill_price
                        
                        if daily_volume:
                            sorted_days = sorted(daily_volume.keys())
                            volumes = [daily_volume[day] for day in sorted_days]
                            
                            fig_bar = go.Figure()
                            fig_bar.add_trace(go.Bar(
                                x=sorted_days,
                                y=volumes,
                                marker=dict(color='steelblue'),
                                name='Volume'
                            ))
                            fig_bar.update_layout(
                                height=300,
                                margin=dict(l=0, r=0, t=30, b=0),
                                xaxis_title="Date",
                                yaxis_title="Volume (€)",
                                hovermode='x unified'
                            )
                            st.plotly_chart(fig_bar, use_container_width=True, key="daily_volume_chart")
                    else:
                        st.info("📊 Aucun ordre rempli pour générer des graphiques")
                
                finally:
                    db.close()
                
                # Statistics by ticker
                st.markdown("---")
                st.subheader("📊 Par Action")
                
                db = SessionLocal()
                try:
                    # Query orders grouped by ticker
                    from sqlalchemy import case
                    
                    ticker_stats_query = db.query(
                        Ticker.symbol,
                        func.count(Order.id).label('total'),
                        func.sum(case((Order.status == OrderStatus.FILLED, 1), else_=0)).label('filled'),
                        func.sum(case((Order.status == OrderStatus.FILLED, Order.filled_quantity * Order.avg_fill_price), else_=0)).label('volume')
                    ).join(Order).group_by(Ticker.symbol).all()
                    
                    if ticker_stats_query:
                        ticker_stats_data = []
                        for row in ticker_stats_query:
                            ticker_stats_data.append({
                                'Symbole': row.symbol,
                                'Total Ordres': row.total,
                                'Exécutés': row.filled,
                                'Taux': f"{(row.filled / row.total * 100):.1f}%" if row.total > 0 else '0%',
                                'Volume': f"{row.volume:,.2f} €" if row.volume else '0.00 €'
                            })
                        
                        ticker_stats_df = pd.DataFrame(ticker_stats_data)
                        st.dataframe(ticker_stats_df, width="stretch", hide_index=True)
                    else:
                        st.info("Aucune statistique disponible")
                
                finally:
                    db.close()
            
            else:
                st.info("ℹ️ Aucune statistique disponible")
    
    except ImportError as e:
        st.error(f"❌ Module manquant: {e}")
        st.code("pip install ib_insync sqlalchemy")
    
    except Exception as e:
        st.error(f"❌ Erreur: {e}")
        import traceback
        st.code(traceback.format_exc())


def auto_trading_page():
    """Automatic trading page with strategy execution"""
    st.header("🤖 Trading Automatique")
    
    try:
        from backend.auto_trader import AutoTraderManager
        from backend.models import SessionLocal, Ticker, Strategy, AutoTraderSession, AutoTraderStatus
        
        # Initialize global IBKR connection
        init_global_ibkr_connection()
        
        # Initialize or update AutoTraderManager in session state
        ibkr_collector = st.session_state.get('global_ibkr')
        
        if 'auto_trader_manager' not in st.session_state:
            st.session_state.auto_trader_manager = AutoTraderManager(ibkr_collector)
        else:
            # Update IBKR connection if it changed
            st.session_state.auto_trader_manager.ibkr_collector = ibkr_collector
        
        manager = st.session_state.auto_trader_manager
        
        # IBKR Connection Status
        col_status1, col_status2 = st.columns([3, 1])
        
        with col_status1:
            if st.session_state.get('global_ibkr_connected', False):
                st.success("🟢 Connecté à IBKR - Le trading automatique est opérationnel")
            else:
                st.warning("🟡 Non connecté à IBKR - Connectez-vous pour utiliser le trading automatique")
        
        with col_status2:
            if st.button("🔄 Rafraîchir", width='stretch'):
                st.rerun()
        
        st.markdown("---")
        
        # Tabs
        tab1, tab2, tab3 = st.tabs(["🆕 Nouvelle Session", "▶️ Sessions Actives", "📜 Historique"])
        
        # ========== TAB 1: NOUVELLE SESSION ==========
        with tab1:
            st.subheader("🆕 Créer une Session de Trading Automatique")
            
            col_form1, col_form2 = st.columns([2, 1])
            
            with col_form1:
                st.markdown("### Configuration de Base")
                
                # Get available tickers and strategies
                db = SessionLocal()
                try:
                    tickers = db.query(Ticker).filter(Ticker.is_active == True).order_by(Ticker.symbol).all()
                    strategies = db.query(Strategy).all()
                    
                    if not tickers:
                        st.warning("⚠️ Aucune action disponible. Ajoutez des actions via 'Collecte de Données'.")
                        return
                    
                    if not strategies:
                        st.warning("⚠️ Aucune stratégie disponible. Créez une stratégie via 'Backtesting'.")
                        return
                    
                    # Ticker selection
                    ticker_options = {f"{t.symbol} - {t.name}": t.id for t in tickers}
                    selected_ticker_display = st.selectbox("Action à trader", list(ticker_options.keys()))
                    selected_ticker_id = ticker_options[selected_ticker_display]
                    
                    # Strategy selection
                    strategy_options = {f"{s.name}" + (f" ({s.strategy_type})" if s.strategy_type else ""): s.id for s in strategies}
                    selected_strategy_display = st.selectbox("Stratégie de trading", list(strategy_options.keys()))
                    selected_strategy_id = strategy_options[selected_strategy_display]
                    
                finally:
                    db.close()
                
                st.markdown("### Paramètres Avancés")
                
                col_param1, col_param2 = st.columns(2)
                
                with col_param1:
                    polling_interval = st.number_input(
                        "Intervalle de polling (secondes)",
                        min_value=10,
                        max_value=3600,
                        value=60,
                        help="Fréquence de vérification des signaux"
                    )
                    
                    max_position_size = st.number_input(
                        "Taille max de position (actions)",
                        min_value=1,
                        max_value=10000,
                        value=100,
                        help="Nombre maximum d'actions à détenir"
                    )
                    
                    max_daily_trades = st.number_input(
                        "Max trades par jour",
                        min_value=1,
                        max_value=100,
                        value=10,
                        help="Limite de trades quotidiens"
                    )
                
                with col_param2:
                    stop_loss_pct = st.number_input(
                        "Stop Loss (%)",
                        min_value=0.1,
                        max_value=50.0,
                        value=2.0,
                        step=0.1,
                        help="Pourcentage de perte pour stop automatique"
                    )
                    
                    take_profit_pct = st.number_input(
                        "Take Profit (%)",
                        min_value=0.1,
                        max_value=100.0,
                        value=5.0,
                        step=0.1,
                        help="Pourcentage de gain pour prise de profit automatique"
                    )
                
                st.markdown("---")
                
                if st.button("🚀 Créer et Démarrer Session", type="primary", width='stretch'):
                    if not st.session_state.get('global_ibkr_connected', False):
                        st.error("❌ Connectez-vous d'abord à IBKR")
                    else:
                        with st.spinner("Création de la session..."):
                            config = {
                                'polling_interval': polling_interval,
                                'max_position_size': max_position_size,
                                'max_daily_trades': max_daily_trades,
                                'stop_loss_pct': stop_loss_pct,
                                'take_profit_pct': take_profit_pct
                            }
                            
                            session_id = manager.create_session(
                                ticker_id=selected_ticker_id,
                                strategy_id=selected_strategy_id,
                                config=config
                            )
                            
                            manager.start_session(session_id)
                            
                            st.success(f"✅ Session #{session_id} créée et démarrée !")
                            time_module.sleep(1)
                            st.rerun()
            
            with col_form2:
                st.info("""
                ### ℹ️ Comment ça marche ?
                
                **1. Sélection**
                - Choisissez une action
                - Choisissez une stratégie
                
                **2. Configuration**
                - Définissez les limites de risque
                - Configurez la fréquence d'analyse
                
                **3. Exécution Automatique**
                - Le système surveille en continu
                - Calcule les indicateurs
                - Détecte les signaux BUY/SELL
                - Passe des ordres automatiquement
                
                **⚠️ Important**
                - Nécessite connexion IBKR active
                - Respecte les limites définies
                - Arrêtez la session à tout moment
                """)
        
        # ========== TAB 2: SESSIONS ACTIVES ==========
        with tab2:
            st.subheader("▶️ Sessions de Trading en Cours")
            
            # Auto-refresh toggle for active sessions
            col_refresh1, col_refresh2 = st.columns([3, 1])
            
            with col_refresh1:
                auto_refresh = st.toggle("🔄 Auto-refresh (5s)", value=False, help="Rafraîchit automatiquement toutes les 5 secondes")
            
            with col_refresh2:
                if st.button("🔄 Rafraîchir maintenant", width='stretch'):
                    st.rerun()
            
            # Get all sessions
            all_sessions = manager.get_all_sessions()
            active_sessions = [s for s in all_sessions if s['is_active']]
            
            if not active_sessions:
                st.info("ℹ️ Aucune session active. Créez-en une dans l'onglet 'Nouvelle Session'.")
            else:
                for session in active_sessions:
                    with st.expander(f"📊 {session['ticker']} - {session['strategy']} (Session #{session['id']})", expanded=True):
                        # Get detailed status
                        trader = manager.traders.get(session['id'])
                        if trader:
                            status = trader.get_status()
                            
                            col1, col2, col3, col4 = st.columns(4)
                            
                            with col1:
                                st.metric("📈 Position", status['current_position'])
                            
                            with col2:
                                st.metric("📝 Ordres", status['total_orders'])
                            
                            with col3:
                                pnl = status['total_pnl']
                                st.metric("💰 P&L", f"{pnl:.2f} €", delta=f"{pnl:.2f} €" if pnl != 0 else None)
                            
                            with col4:
                                st.metric("📊 Buffer", f"{status['buffer_size']} points")
                            
                            st.markdown("---")
                            
                            col_info1, col_info2 = st.columns(2)
                            
                            with col_info1:
                                if status['last_signal']:
                                    signal_color = "🟢" if status['last_signal'] == "BUY" else "🔴"
                                    st.write(f"**Dernier Signal:** {signal_color} {status['last_signal']}")
                                    if status['last_signal_at']:
                                        st.caption(f"à {status['last_signal_at'].strftime('%H:%M:%S')}")
                                
                                if status['last_check_at']:
                                    st.write(f"**Dernière vérification:** {status['last_check_at'].strftime('%H:%M:%S')}")
                            
                            with col_info2:
                                if status['started_at']:
                                    st.write(f"**Démarré:** {status['started_at'].strftime('%Y-%m-%d %H:%M')}")
                                
                                uptime = datetime.now() - status['started_at'] if status['started_at'] else timedelta(0)
                                hours = int(uptime.total_seconds() // 3600)
                                minutes = int((uptime.total_seconds() % 3600) // 60)
                                st.write(f"**Uptime:** {hours}h {minutes}m")
                            
                            # Live Chart with Price Buffer
                            st.markdown("---")
                            st.markdown("**📈 Cours en Temps Réel & Indicateurs**")
                            
                            if trader.price_buffer and len(trader.price_buffer) > 0:
                                # Convert buffer to DataFrame
                                buffer_df = pd.DataFrame(trader.price_buffer)
                                
                                # Calculate indicators for visualization
                                try:
                                    # Try to import strategy runner, but it's optional
                                    try:
                                        from backend.strategy_runner import StrategyRunner
                                        runner = StrategyRunner()
                                        use_indicators = True
                                    except (ImportError, ModuleNotFoundError):
                                        use_indicators = False
                                    
                                    if use_indicators:
                                        buffer_df_copy = buffer_df.copy()
                                        buffer_df_copy['date'] = buffer_df_copy['timestamp']
                                        buffer_df_copy = buffer_df_copy.set_index('date')
                                        
                                        signals_df = runner.generate_signals(buffer_df_copy, trader.strategy)
                                    else:
                                        signals_df = None
                                    
                                    if signals_df is not None and not signals_df.empty:
                                        # Create chart
                                        fig = go.Figure()
                                        
                                        # Price line
                                        fig.add_trace(go.Scatter(
                                            x=signals_df.index,
                                            y=signals_df['close'],
                                            mode='lines',
                                            name='Prix',
                                            line=dict(color='blue', width=2)
                                        ))
                                        
                                        # Add indicators if present
                                        if 'sma' in signals_df.columns:
                                            fig.add_trace(go.Scatter(
                                                x=signals_df.index,
                                                y=signals_df['sma'],
                                                mode='lines',
                                                name='SMA',
                                                line=dict(color='orange', dash='dash')
                                            ))
                                        
                                        if 'ema' in signals_df.columns:
                                            fig.add_trace(go.Scatter(
                                                x=signals_df.index,
                                                y=signals_df['ema'],
                                                mode='lines',
                                                name='EMA',
                                                line=dict(color='purple', dash='dash')
                                            ))
                                        
                                        # Mark BUY/SELL signals
                                        if 'signal' in signals_df.columns:
                                            buy_signals = signals_df[signals_df['signal'] == 1]
                                            sell_signals = signals_df[signals_df['signal'] == -1]
                                            
                                            if not buy_signals.empty:
                                                fig.add_trace(go.Scatter(
                                                    x=buy_signals.index,
                                                    y=buy_signals['close'],
                                                    mode='markers',
                                                    name='BUY',
                                                    marker=dict(color='green', size=12, symbol='triangle-up')
                                                ))
                                            
                                            if not sell_signals.empty:
                                                fig.add_trace(go.Scatter(
                                                    x=sell_signals.index,
                                                    y=sell_signals['close'],
                                                    mode='markers',
                                                    name='SELL',
                                                    marker=dict(color='red', size=12, symbol='triangle-down')
                                                ))
                                        
                                        fig.update_layout(
                                            height=400,
                                            margin=dict(l=0, r=0, t=30, b=0),
                                            xaxis_title="Temps",
                                            yaxis_title="Prix (€)",
                                            hovermode='x unified',
                                            showlegend=True
                                        )
                                        
                                        st.plotly_chart(
                                            fig,
                                            use_container_width=True,
                                            key=f"signals_chart_{session['id']}"
                                        )
                                        
                                        # Show latest indicator values
                                        st.markdown("**📊 Dernières Valeurs des Indicateurs**")
                                        
                                        latest = signals_df.iloc[-1]
                                        indicator_cols = st.columns(min(4, len([c for c in signals_df.columns if c not in ['open', 'high', 'low', 'close', 'volume', 'signal', 'position']])))
                                        
                                        col_idx = 0
                                        for col in signals_df.columns:
                                            if col not in ['open', 'high', 'low', 'close', 'volume', 'signal', 'position', 'timestamp']:
                                                if col_idx < len(indicator_cols):
                                                    with indicator_cols[col_idx]:
                                                        value = latest[col]
                                                        if pd.notna(value):
                                                            st.metric(col.upper(), f"{value:.2f}")
                                                    col_idx += 1
                                    else:
                                        st.info("Calcul des indicateurs en cours...")
                                
                                except Exception as e:
                                    st.warning(f"Graphique non disponible: {e}")
                                    
                                    # Fallback: simple price chart
                                    fig = go.Figure()
                                    fig.add_trace(go.Scatter(
                                        x=buffer_df['timestamp'],
                                        y=buffer_df['close'],
                                        mode='lines+markers',
                                        name='Prix',
                                        line=dict(color='blue')
                                    ))
                                    fig.update_layout(
                                        height=300,
                                        margin=dict(l=0, r=0, t=30, b=0),
                                        xaxis_title="Temps",
                                        yaxis_title="Prix (€)"
                                    )
                                    st.plotly_chart(
                                        fig,
                                        use_container_width=True,
                                        key=f"fallback_chart_{session['id']}"
                                    )
                            else:
                                st.info("⏳ En attente de données... Le système récupère les cours.")
                            
                            st.markdown("---")
                            
                            col_btn1, col_btn2 = st.columns(2)
                            
                            with col_btn1:
                                if st.button(f"🛑 Arrêter Session #{session['id']}", type="secondary", width='stretch'):
                                    manager.stop_session(session['id'])
                                    st.success(f"Session #{session['id']} arrêtée")
                                    time_module.sleep(1)
                                    st.rerun()
                            
                            with col_btn2:
                                if st.button("📊 Voir Ordres", key=f"orders_{session['id']}", width='stretch'):
                                    st.info("Consultez l'onglet 'Passage d'Ordres' pour voir tous les ordres")
            
            # Auto-refresh logic
            if auto_refresh:
                time_module.sleep(5)
                st.rerun()
        
        # ========== TAB 3: HISTORIQUE ==========
        with tab3:
            st.subheader("📜 Historique des Sessions")
            
            # Get all sessions
            all_sessions = manager.get_all_sessions()
            
            if not all_sessions:
                st.info("ℹ️ Aucune session enregistrée")
            else:
                # Create DataFrame
                sessions_data = []
                for session in all_sessions:
                    sessions_data.append({
                        'ID': session['id'],
                        'Action': session['ticker'],
                        'Stratégie': session['strategy'],
                        'Statut': session['status'],
                        'Acti': '✅' if session['is_active'] else '❌',
                        'Position': session['current_position'],
                        'Ordres': session['total_orders'],
                        'P&L (€)': f"{session['total_pnl']:.2f}",
                        'Démarré': session['started_at'].strftime('%Y-%m-%d %H:%M') if session['started_at'] else 'N/A',
                        'Arrêté': session['stopped_at'].strftime('%Y-%m-%d %H:%M') if session['stopped_at'] else 'N/A'
                    })
                
                sessions_df = pd.DataFrame(sessions_data)
                st.dataframe(sessions_df, width='stretch', hide_index=True)
                
                # Statistics
                st.markdown("---")
                st.subheader("📊 Statistiques Globales")
                
                total_sessions = len(all_sessions)
                active_count = len([s for s in all_sessions if s['is_active']])
                total_pnl = sum(s['total_pnl'] for s in all_sessions)
                total_orders_all = sum(s['total_orders'] for s in all_sessions)
                
                col_stat1, col_stat2, col_stat3, col_stat4 = st.columns(4)
                
                with col_stat1:
                    st.metric("📝 Total Sessions", total_sessions)
                
                with col_stat2:
                    st.metric("▶️ Actives", active_count)
                
                with col_stat3:
                    st.metric("💰 P&L Total", f"{total_pnl:.2f} €", delta=f"{total_pnl:.2f} €" if total_pnl != 0 else None)
                
                with col_stat4:
                    st.metric("📋 Ordres Générés", total_orders_all)
    
    except ImportError as e:
        st.error(f"❌ Module manquant: {e}")
        st.code("pip install ib_insync sqlalchemy pandas")
    
    except Exception as e:
        st.error(f"❌ Erreur: {e}")
        import traceback
        st.code(traceback.format_exc())


def indicators_page():
    """Page d'explication des indicateurs techniques"""
    st.header("📚 Indicateurs Techniques")
    st.write("Guide complet des indicateurs utilisés dans les stratégies de trading")
    
    # Tabs pour les différentes catégories
    tab1, tab2, tab3, tab4 = st.tabs(["📈 Tendance", "⚡ Momentum", "📊 Volatilité", "📦 Volume"])
    
    # ========== INDICATEURS DE TENDANCE ==========
    with tab1:
        st.subheader("📈 Indicateurs de Tendance")
        st.write("Ces indicateurs aident à identifier la direction et la force d'une tendance.")
        
        # SMA (Simple Moving Average)
        with st.expander("🔵 SMA - Moyenne Mobile Simple", expanded=True):
            st.markdown("""
            **Définition**: Moyenne arithmétique des prix sur une période donnée.
            
            **Calcul**: 
            ```
            SMA = (P1 + P2 + ... + Pn) / n
            ```
            où P = prix de clôture, n = période
            
            **Périodes courantes**:
            - SMA 20: Tendance court terme
            - SMA 50: Tendance moyen terme  
            - SMA 200: Tendance long terme
            
            **Interprétation**:
            - 📈 **Signal haussier**: Prix > SMA ou croisement SMA courte > SMA longue (Golden Cross)
            - 📉 **Signal baissier**: Prix < SMA ou croisement SMA courte < SMA longue (Death Cross)
            - 📊 **Support/Résistance**: La SMA agit souvent comme niveau de support (tendance haussière) ou résistance (tendance baissière)
            
            **Avantages**: Simple, élimine le bruit, identifie les tendances
            **Inconvénients**: Retard important, moins sensible aux changements récents
            """)
        
        # EMA (Exponential Moving Average)
        with st.expander("🟢 EMA - Moyenne Mobile Exponentielle"):
            st.markdown("""
            **Définition**: Moyenne mobile qui donne plus de poids aux prix récents.
            
            **Calcul**:
            ```
            Multiplicateur = 2 / (n + 1)
            EMA = Prix_actuel × Multiplicateur + EMA_précédent × (1 - Multiplicateur)
            ```
            
            **Périodes courantes**:
            - EMA 12 et EMA 26: Utilisées pour le MACD
            - EMA 9: Signal line du MACD
            - EMA 50 et EMA 200: Tendances moyen/long terme
            
            **Interprétation**:
            - 📈 **Signal haussier**: Prix > EMA, pente EMA ascendante
            - 📉 **Signal baissier**: Prix < EMA, pente EMA descendante
            - ⚡ **Réactivité**: Réagit plus vite que la SMA aux changements
            
            **Avantages**: Plus réactive, suit mieux les tendances récentes
            **Inconvénients**: Peut générer plus de faux signaux
            """)
        
        # MACD
        with st.expander("🔶 MACD - Moving Average Convergence Divergence"):
            st.markdown("""
            **Définition**: Indicateur de momentum basé sur la différence entre deux EMA.
            
            **Calcul**:
            ```
            MACD Line = EMA(12) - EMA(26)
            Signal Line = EMA(9) du MACD Line
            Histogramme = MACD Line - Signal Line
            ```
            
            **Interprétation**:
            - 📈 **Signal d'achat**: 
              - MACD croise au-dessus de la Signal Line
              - Histogramme passe en positif
              - MACD croise au-dessus de zéro
            - 📉 **Signal de vente**:
              - MACD croise en-dessous de la Signal Line
              - Histogramme passe en négatif
              - MACD croise en-dessous de zéro
            - 🔀 **Divergence**: 
              - Divergence haussière: Prix fait des plus bas mais MACD remonte
              - Divergence baissière: Prix fait des plus hauts mais MACD baisse
            
            **Avantages**: Combine tendance et momentum, identifie les divergences
            **Inconvénients**: Peut donner des signaux tardifs en marché volatile
            """)
        
        # ADX
        with st.expander("🟣 ADX - Average Directional Index"):
            st.markdown("""
            **Définition**: Mesure la force d'une tendance (sans indiquer sa direction).
            
            **Calcul**: Basé sur le Directional Movement Index (DMI)
            ```
            +DI = Mouvement directionnel haussier
            -DI = Mouvement directionnel baissier
            ADX = EMA de la différence absolue entre +DI et -DI
            ```
            
            **Interprétation des valeurs**:
            - ADX < 20: ❌ Pas de tendance, marché en consolidation
            - ADX 20-25: ⚠️ Tendance faible
            - ADX 25-50: ✅ Tendance forte
            - ADX > 50: 🔥 Tendance très forte
            
            **Interprétation avec DI**:
            - 📈 **Tendance haussière forte**: ADX > 25 et +DI > -DI
            - 📉 **Tendance baissière forte**: ADX > 25 et -DI > +DI
            
            **Avantages**: Identifie la force de la tendance, évite les faux signaux en range
            **Inconvénients**: Ne donne pas la direction, peut être en retard
            """)
    
    # ========== INDICATEURS DE MOMENTUM ==========
    with tab2:
        st.subheader("⚡ Indicateurs de Momentum")
        st.write("Ces indicateurs mesurent la vitesse et la force des mouvements de prix.")
        
        # RSI
        with st.expander("🔴 RSI - Relative Strength Index", expanded=True):
            st.markdown("""
            **Définition**: Oscillateur qui mesure la vitesse et l'amplitude des mouvements de prix.
            
            **Calcul**:
            ```
            RS = Moyenne des gains / Moyenne des pertes (sur 14 périodes)
            RSI = 100 - (100 / (1 + RS))
            ```
            
            **Zones clés**:
            - RSI > 70: 🔥 Zone de surachat (potentiel retournement baissier)
            - RSI 30-70: ⚖️ Zone neutre
            - RSI < 30: ❄️ Zone de survente (potentiel retournement haussier)
            
            **Interprétation**:
            - 📈 **Signal d'achat**:
              - RSI sort de la zone de survente (> 30)
              - Divergence haussière: Prix fait des plus bas mais RSI remonte
            - 📉 **Signal de vente**:
              - RSI sort de la zone de surachat (< 70)
              - Divergence baissière: Prix fait des plus hauts mais RSI baisse
            
            **Avantages**: Identifie surachat/survente, détecte les divergences
            **Inconvénients**: Peut rester en zone extrême longtemps en tendance forte
            """)
        
        # Stochastic
        with st.expander("🟡 Stochastique - Stochastic Oscillator"):
            st.markdown("""
            **Définition**: Compare le prix de clôture à sa fourchette de prix sur une période.
            
            **Calcul**:
            ```
            %K = 100 × (Close - Low14) / (High14 - Low14)
            %D = SMA(3) de %K (signal line)
            ```
            
            **Zones clés**:
            - Stoch > 80: 🔥 Surachat
            - Stoch 20-80: ⚖️ Zone neutre
            - Stoch < 20: ❄️ Survente
            
            **Interprétation**:
            - 📈 **Signal d'achat**:
              - %K croise au-dessus de %D en zone de survente
              - Sortie de la zone < 20
            - 📉 **Signal de vente**:
              - %K croise en-dessous de %D en zone de surachat
              - Sortie de la zone > 80
            
            **Types**:
            - **Fast Stochastic**: %K brut (plus réactif, plus de bruit)
            - **Slow Stochastic**: %K lissé (moins de faux signaux)
            
            **Avantages**: Très sensible, bons signaux en range
            **Inconvénients**: Beaucoup de faux signaux en tendance
            """)
        
        # CCI
        with st.expander("🔵 CCI - Commodity Channel Index"):
            st.markdown("""
            **Définition**: Mesure l'écart du prix par rapport à sa moyenne statistique.
            
            **Calcul**:
            ```
            TP = (High + Low + Close) / 3 (Typical Price)
            CCI = (TP - SMA(TP)) / (0.015 × Mean Deviation)
            ```
            
            **Zones clés**:
            - CCI > +100: 🔥 Surachat, tendance haussière forte
            - CCI -100 à +100: ⚖️ Zone neutre
            - CCI < -100: ❄️ Survente, tendance baissière forte
            
            **Interprétation**:
            - 📈 **Signal d'achat**: CCI croise au-dessus de -100
            - 📉 **Signal de vente**: CCI croise en-dessous de +100
            - ⚡ **Momentum**: Valeurs extrêmes (>200 ou <-200) indiquent un mouvement fort
            
            **Avantages**: Identifie les mouvements cycliques, bon pour le timing
            **Inconvénients**: Peut donner beaucoup de signaux en marché volatile
            """)
        
        # Williams %R
        with st.expander("🟢 Williams %R"):
            st.markdown("""
            **Définition**: Oscillateur de momentum similaire au Stochastique.
            
            **Calcul**:
            ```
            %R = -100 × (High14 - Close) / (High14 - Low14)
            ```
            
            **Zones clés**:
            - %R > -20: 🔥 Surachat
            - %R -20 à -80: ⚖️ Zone neutre
            - %R < -80: ❄️ Survente
            
            **Interprétation**:
            - 📈 **Signal d'achat**: 
              - %R sort de -80 (survente)
              - Divergence haussière
            - 📉 **Signal de vente**:
              - %R sort de -20 (surachat)
              - Divergence baissière
            
            **Avantages**: Très réactif, identifie bien les retournements
            **Inconvénients**: Beaucoup de faux signaux, nécessite confirmation
            """)
        
        # ROC
        with st.expander("🟣 ROC - Rate of Change"):
            st.markdown("""
            **Définition**: Mesure le pourcentage de changement du prix sur une période.
            
            **Calcul**:
            ```
            ROC = ((Prix_actuel - Prix_n_périodes) / Prix_n_périodes) × 100
            ```
            
            **Interprétation**:
            - ROC > 0: 📈 Momentum haussier
            - ROC = 0: ⚖️ Pas de changement
            - ROC < 0: 📉 Momentum baissier
            - ⚡ Valeurs extrêmes: Momentum très fort (attention au retournement)
            
            **Utilisation**:
            - Identifier les divergences
            - Confirmer les tendances
            - Détecter les zones de surachat/survente
            
            **Avantages**: Simple, détecte bien l'accélération/décélération
            **Inconvénients**: Sensible aux gaps, peut être erratique
            """)
    
    # ========== INDICATEURS DE VOLATILITÉ ==========
    with tab3:
        st.subheader("📊 Indicateurs de Volatilité")
        st.write("Ces indicateurs mesurent l'amplitude des variations de prix.")
        
        # Bollinger Bands
        with st.expander("🔵 Bandes de Bollinger", expanded=True):
            st.markdown("""
            **Définition**: Enveloppe de volatilité autour d'une moyenne mobile.
            
            **Calcul**:
            ```
            Bande Moyenne = SMA(20)
            Bande Supérieure = SMA(20) + (2 × Écart-type)
            Bande Inférieure = SMA(20) - (2 × Écart-type)
            ```
            
            **Interprétation**:
            - 📏 **Largeur des bandes**:
              - Bandes larges: Forte volatilité
              - Bandes étroites: Faible volatilité (squeeze, précède souvent un mouvement fort)
            
            - 📈 **Signaux d'achat**:
              - Prix touche la bande inférieure (survente)
              - Rebond sur la bande inférieure
              - Squeeze suivi d'un breakout haussier
            
            - 📉 **Signaux de vente**:
              - Prix touche la bande supérieure (surachat)
              - Rejet de la bande supérieure
              - Squeeze suivi d'un breakout baissier
            
            - 🎯 **Walking the bands**: En forte tendance, le prix peut "marcher" le long d'une bande
            
            **Avantages**: Adaptatif à la volatilité, identifie surachat/survente
            **Inconvénients**: Peut donner des faux signaux en tendance forte
            """)
        
        # ATR
        with st.expander("🟢 ATR - Average True Range"):
            st.markdown("""
            **Définition**: Mesure la volatilité moyenne en calculant la fourchette réelle des prix.
            
            **Calcul**:
            ```
            True Range = Max de:
              - High - Low
              - |High - Close_précédent|
              - |Low - Close_précédent|
            
            ATR = EMA(14) du True Range
            ```
            
            **Interprétation**:
            - 📈 **ATR élevé**: Forte volatilité, grands mouvements, risque élevé
            - 📉 **ATR faible**: Faible volatilité, petits mouvements, consolidation
            - 📊 **Tendance ATR**:
              - ATR montant: Volatilité en augmentation
              - ATR descendant: Volatilité en diminution
            
            **Utilisation**:
            - ⚙️ **Dimensionnement de position**: Ajuster la taille selon la volatilité
            - 🎯 **Stop-loss**: Placer le stop à 2-3× ATR du prix d'entrée
            - 📊 **Filtrage**: Ne trader que si ATR > seuil (éviter les marchés calmes)
            
            **Avantages**: Mesure objective de la volatilité, utile pour le risk management
            **Inconvénients**: Ne donne pas de direction, seulement l'amplitude
            """)
    
    # ========== INDICATEURS DE VOLUME ==========
    with tab4:
        st.subheader("📦 Indicateurs de Volume")
        st.write("Ces indicateurs analysent le volume des transactions pour confirmer les mouvements.")
        
        # OBV
        with st.expander("🔵 OBV - On-Balance Volume", expanded=True):
            st.markdown("""
            **Définition**: Indicateur de momentum basé sur le volume cumulé.
            
            **Calcul**:
            ```
            Si Close > Close_précédent: OBV = OBV_précédent + Volume
            Si Close < Close_précédent: OBV = OBV_précédent - Volume
            Si Close = Close_précédent: OBV = OBV_précédent
            ```
            
            **Interprétation**:
            - 📈 **Signal haussier**:
              - OBV en hausse: Pression acheteuse
              - OBV monte + Prix monte: Confirmation de la tendance haussière
              - Divergence haussière: Prix baisse mais OBV monte (accumulation)
            
            - 📉 **Signal baissier**:
              - OBV en baisse: Pression vendeuse
              - OBV baisse + Prix baisse: Confirmation de la tendance baissière
              - Divergence baissière: Prix monte mais OBV baisse (distribution)
            
            - 🔀 **Divergences**: Très importantes pour anticiper les retournements
            
            **Avantages**: Confirme les tendances, détecte l'accumulation/distribution
            **Inconvénients**: Peut être erratique sur les petites timeframes
            """)
        
        # Volume SMA
        with st.expander("🟢 Volume SMA - Moyenne Mobile du Volume"):
            st.markdown("""
            **Définition**: Moyenne mobile appliquée au volume pour identifier les niveaux anormaux.
            
            **Calcul**:
            ```
            Volume SMA = SMA(Volume, période)
            Période courante: 20 périodes
            ```
            
            **Interprétation**:
            - 📊 **Volume > SMA**: 
              - ⚡ Activité élevée, intérêt fort
              - Confirme la validité du mouvement de prix
            
            - 📉 **Volume < SMA**:
              - 😴 Activité faible, manque de conviction
              - Mouvement de prix moins fiable
            
            **Utilisation avec les prix**:
            - 📈 **Volume fort + Prix monte**: Tendance haussière saine
            - 📉 **Volume fort + Prix baisse**: Tendance baissière saine
            - ⚠️ **Volume faible + Prix monte**: Tendance fragile (risque de retournement)
            - ⚠️ **Volume faible + Prix baisse**: Correction technique (pas de panique)
            
            **Avantages**: Simple, identifie les pics d'activité
            **Inconvénients**: Retard inhérent aux moyennes mobiles
            """)
        
        # Volume Ratio
        with st.expander("🟣 Ratio de Volume"):
            st.markdown("""
            **Définition**: Ratio entre le volume actuel et sa moyenne.
            
            **Calcul**:
            ```
            Volume Ratio = Volume / SMA(Volume, 20)
            ```
            
            **Interprétation**:
            - Ratio > 2.0: 🔥 Volume extrêmement élevé (2× la moyenne)
            - Ratio > 1.5: ⚡ Volume très élevé
            - Ratio 0.8-1.2: ⚖️ Volume normal
            - Ratio < 0.5: 😴 Volume très faible
            
            **Signaux**:
            - 📈 **Breakout valide**: Ratio > 1.5 lors de la cassure
            - 🎯 **Point d'entrée**: Ratio élevé confirme le momentum
            - ⚠️ **Faux signal**: Mouvement sans volume (ratio < 0.8)
            
            **Avantages**: Normalise le volume, facile à interpréter
            **Inconvénients**: Sensible aux pics isolés
            """)
    
    # Section bonus: Combinaisons d'indicateurs
    st.markdown("---")
    st.subheader("🎯 Combinaisons Efficaces")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("""
        **📈 Stratégie Trend-Following**:
        - SMA 50 et SMA 200 (direction)
        - ADX > 25 (force de tendance)
        - Volume > SMA (confirmation)
        
        **⚡ Stratégie Momentum**:
        - RSI + Stochastique (surachat/survente)
        - MACD (timing d'entrée)
        - OBV (confirmation volume)
        """)
    
    with col2:
        st.markdown("""
        **📊 Stratégie Mean-Reversion**:
        - Bollinger Bands (zones extrêmes)
        - RSI < 30 ou > 70 (survente/surachat)
        - Volume faible (manque de conviction)
        
        **🔀 Stratégie Breakout**:
        - Bollinger Squeeze (consolidation)
        - Volume Ratio > 1.5 (confirmation)
        - ADX montant (tendance naissante)
        """)
    
    # Note importante
    st.info("""
    💡 **Conseil**: Aucun indicateur n'est parfait. Utilisez toujours plusieurs indicateurs 
    complémentaires pour confirmer vos signaux et réduire les faux signaux. 
    La combinaison tendance + momentum + volume est souvent la plus fiable.
    """)


def settings_page():
    """Settings page"""
    st.header("⚙️ Paramètres")
    
    st.subheader("💼 Configuration IBKR / Lynx")
    
    # IBKR connection info
    col1, col2 = st.columns(2)
    
    with col1:
        st.text_input("Host", value=os.getenv("IBKR_HOST", "127.0.0.1"), disabled=True)
        st.text_input("Port", value=os.getenv("IBKR_PORT", "4002"), disabled=True)
    
    with col2:
        st.text_input("Client ID", value=os.getenv("IBKR_CLIENT_ID", "1"), disabled=True)
        st.text_input("Account", value=os.getenv("IBKR_ACCOUNT", ""), disabled=True)
    
    st.markdown("---")
    
    st.subheader("⚙️ Configuration de Trading")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.checkbox("Mode Simulation", value=True, disabled=True, help="Mode simulation activé par défaut pour éviter les trades réels accidentels")
        st.number_input("Taille maximale de position (€)", value=10000, step=1000)
    
    with col2:
        st.slider("Risque par trade (%)", min_value=0.5, max_value=5.0, value=2.0, step=0.5)
        st.slider("Stop-loss (%)", min_value=1.0, max_value=10.0, value=5.0, step=0.5)
    
    st.markdown("---")
    
    st.subheader("📊 Paramètres de collecte de données")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.number_input("Délai entre requêtes (secondes)", value=1, min_value=0, max_value=10, help="Délai pour éviter le rate limiting des APIs")
    
    with col2:
        st.checkbox("Utiliser données simulées si API échoue", value=True, help="Génère des données réalistes si l'API n'est pas disponible")
    
    st.info("ℹ️ **IBKR** : Pas de limite API pour les données historiques et temps réel")
    
    if st.button("💾 Sauvegarder les paramètres"):
        st.success("✅ Paramètres sauvegardés")


if __name__ == "__main__":
    main()
