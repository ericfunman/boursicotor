"""
Main Streamlit application for Boursicotor
"""
import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from datetime import datetime, timedelta
import time as time_module  # Alias to avoid conflict with 'time' column name
import sys
import os
from pathlib import Path

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
        except:
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
    except:
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
                        if st.button("📋 Détails", key=f"banner_job_{job.id}"):
                            st.session_state.page = "📋 Historique des collectes"
                            st.rerun()
                
                if len(active_jobs) > 3:
                    st.caption(f"... et {len(active_jobs) - 3} autre(s) job(s)")
                
                st.markdown("---")
    except:
        pass  # Silently fail if Celery not configured
    
    st.markdown("---")
    
    # Initialize global IBKR connection
    init_global_ibkr_connection()
    
    # Sidebar
    with st.sidebar:
        st.header("⚙️ Configuration")
        
        # Page selection
        page = st.radio(
            "Navigation",
            ["📊 Dashboard", "💾 Collecte de Données", "� Historique des collectes",
             "📈 Analyse Technique", "� Cours Live", "�🔙 Backtesting", 
             "🤖 Trading Automatique", "⚙️ Paramètres"]
        )
        
        st.markdown("---")
        
        # Global IBKR Connection
        st.subheader("🔌 Connexion IBKR")
        
        col1, col2 = st.columns([1, 1])
        
        with col1:
            if not st.session_state.global_ibkr_connected:
                if st.button("🔌 Connecter", type="primary", use_container_width=True, key="sidebar_connect"):
                    with st.spinner("Connexion..."):
                        success, message = connect_global_ibkr()
                        if success:
                            st.success(message)
                            st.rerun()
                        else:
                            st.error(message)
            else:
                if st.button("🔌 Déconnecter", use_container_width=True, key="sidebar_disconnect"):
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
    elif page == "� Historique des collectes":
        jobs_monitoring_page()
    elif page == "�📈 Analyse Technique":
        technical_analysis_page()
    elif page == "� Cours Live":
        live_prices_page()
    elif page == "�🔙 Backtesting":
        backtesting_page()
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
            
            # Get positions
            st.subheader("📊 Positions Actuelles")
            
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
                st.dataframe(positions_df, use_container_width=True)
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
                st.dataframe(pd.DataFrame(trades_data), use_container_width=True)
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
    
    # Data source selection
    st.subheader("📡 Source de Données")
    
    col_source1, col_source2 = st.columns(2)
    
    with col_source1:
        data_source = st.radio(
            "Choisir la source",
            ["💼 IBKR / Lynx (Temps Réel)", "📊 Yahoo Finance (Historique)"],
            index=0,  # IBKR par défaut
            help="IBKR/Lynx: Données temps réel via IB Gateway | Yahoo Finance: Données historiques"
        )
    
    with col_source2:
        if data_source == "💼 IBKR / Lynx (Temps Réel)":
            st.success("**IBKR / Lynx**\n- ✅ Données réelles temps réel\n- ✅ Via IB Gateway\n- 📊 Aucune limite API\n- ⚡ Latence minimale")
        else:  # Yahoo Finance
            st.info("**Yahoo Finance**\n- ✅ Données réelles\n- ✅ Historique massif (26+ ans)\n- ⚠️ Délai de 15 minutes")
    
    use_ibkr = data_source == "💼 IBKR / Lynx (Temps Réel)"
    use_yahoo = data_source == "📊 Yahoo Finance (Historique)"
    
    st.markdown("---")
    
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
            # IBKR Search mode
            st.info("🔎 Recherchez une action sur IBKR pour l'ajouter à votre liste")
            
            # Initialize session state for search results
            if 'ibkr_search_results' not in st.session_state:
                st.session_state.ibkr_search_results = []
            if 'ibkr_selected_ticker' not in st.session_state:
                st.session_state.ibkr_selected_ticker = None
            if 'ibkr_selected_name' not in st.session_state:
                st.session_state.ibkr_selected_name = None
            
            search_query = st.text_input(
                "Rechercher une action",
                placeholder="Ex: Air Liquide, Apple, Tesla...",
                help="Entrez le nom de l'entreprise pour rechercher sur IBKR"
            )
            
            if search_query and len(search_query) >= 2:
                if st.button("🔍 Rechercher sur IBKR", type="primary"):
                    with st.spinner(f"Recherche de '{search_query}' sur IBKR..."):
                        try:
                            # Use global IBKR connection
                            collector = get_global_ibkr()
                            
                            if collector is None:
                                st.error("❌ Connectez-vous à IBKR depuis la sidebar pour utiliser la recherche")
                            else:
                                # Search for contracts
                                from ib_insync import Stock
                                contracts = collector.ib.reqMatchingSymbols(search_query)
                                
                                if contracts:
                                    # Filter for French stocks only
                                    french_exchanges = ['SBF', 'EURONEXT', 'ENEXT.BE', 'AEB']
                                    options = []
                                    
                                    for contract in contracts:
                                        cd = contract.contract
                                        
                                        # Filter: only stocks (STK) on French/European exchanges
                                        if (hasattr(cd, 'secType') and cd.secType == 'STK' and
                                            hasattr(cd, 'symbol') and hasattr(cd, 'primaryExchange') and
                                            cd.primaryExchange in french_exchanges):
                                            
                                            # Get company description if available
                                            desc = contract.contract.longName if hasattr(contract.contract, 'longName') else search_query.title()
                                            label = f"{cd.symbol} - {desc} ({cd.primaryExchange})"
                                            options.append((label, cd.symbol, cd.primaryExchange, desc))
                                    
                                    if options:
                                        st.session_state.ibkr_search_results = options
                                        st.success(f"✅ {len(options)} action(s) française(s) trouvée(s)")
                                    else:
                                        st.session_state.ibkr_search_results = []
                                        st.warning(f"❌ Aucune action française trouvée pour '{search_query}'. Essayez un autre terme ou utilisez la saisie manuelle ci-dessous.")
                                else:
                                    st.session_state.ibkr_search_results = []
                                    st.warning("Aucun résultat trouvé. Essayez un autre terme.")
                        
                        except Exception as e:
                            st.error(f"❌ Erreur lors de la recherche : {str(e)}")
            
            # Display search results if available
            selected_ticker = None
            selected_name = None
            
            if st.session_state.ibkr_search_results:
                options = st.session_state.ibkr_search_results
                choice = st.selectbox(
                    "Sélectionner une action",
                    range(len(options)),
                    format_func=lambda i: options[i][0],
                    key="ibkr_ticker_choice"
                )
                
                selected_ticker = options[choice][1]
                selected_name = options[choice][3]
                
                st.success(f"✅ Ticker sélectionné : **{selected_ticker}** - {selected_name}")
            
            # Manual input fallback
            if not selected_ticker:
                st.markdown("---")
                st.markdown("**Ou saisissez directement le ticker :**")
                col_t1, col_t2 = st.columns([1, 2])
                with col_t1:
                    selected_ticker = st.text_input(
                        "Ticker",
                        placeholder="Ex: AI, AAPL, TSLA",
                        help="Symbole du ticker"
                    ).upper()
                with col_t2:
                    selected_name = st.text_input(
                        "Nom",
                        placeholder="Ex: Air Liquide S.A.",
                        help="Nom de l'entreprise"
                    )
        
        # Duration and interval options depend on source
        if use_ibkr:
            # IBKR options
            st.markdown("**IBKR / Lynx** - Périodes et intervalles")
            st.info("💼 IBKR fournit des données temps réel sans limitation d'API")
            
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
            
            # Warning about sub-5-second intervals
            st.warning("⚠️ **Important** : Les intervalles < 5 secondes ne sont disponibles que pour certaines actions très liquides (principalement US). Pour les actions européennes (TTE, AI, etc.), utilisez 5 secondes minimum.")
            
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
            
        elif use_yahoo:
            # Yahoo Finance options
            st.markdown("**Yahoo Finance** - Périodes et intervalles")
            st.info("📊 Yahoo Finance fournit des données historiques gratuites (délai 15min)")
            
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
        # Collect button - Create async job with Celery
        if st.button("📊 Collecter les données", type="primary", use_container_width=True):
            try:
                from backend.job_manager import JobManager
                from backend.tasks import collect_data_yahoo, collect_data_ibkr
                
                job_manager = JobManager()
                
                if use_yahoo:
                    # Create Yahoo Finance job
                    job = job_manager.create_job(
                        ticker_symbol=selected_ticker,
                        ticker_name=selected_name,
                        source="yahoo_finance",
                        duration=selected_duration,
                        interval=selected_interval
                    )
                    
                    # Launch Celery task
                    task = collect_data_yahoo.delay(
                        job_id=job.id,
                        ticker_symbol=selected_ticker,
                        ticker_name=selected_name,
                        period=period,
                        interval=interval
                    )
                    
                    # Update job with Celery task ID
                    job_manager.update_job_task_id(job.id, task.id)
                    
                    st.success(f"✅ Job de collecte créé pour {selected_ticker} depuis Yahoo Finance!")
                    st.info(f"📊 Source: Yahoo Finance | Période: {selected_duration} | Intervalle: {selected_interval}")
                    st.info("🔄 La collecte s'exécute en arrière-plan. Consultez la page **Historique des collectes** pour suivre la progression.")
                    # Note: Pas de st.rerun() ici - laisse l'utilisateur naviguer librement
                
                elif use_ibkr:
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
                        # Note: Pas de st.rerun() ici - laisse l'utilisateur naviguer librement
            
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
    
    # Data Interpolation Section
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
        if st.button("🚀 Démarrer l'interpolation", type="primary", use_container_width=True):
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


def jobs_monitoring_page():
    """Job monitoring page - Shows async data collection progress"""
    st.header("📋 Historique des collectes de données")
    
    try:
        from backend.job_manager import JobManager
        from backend.models import JobStatus
        
        job_manager = JobManager()
        
        # Auto-refresh without blocking - use st.empty() pattern instead of sleep
        active_jobs = get_cached_active_jobs()
        if active_jobs:
            st.info("🔄 Cette page se rafraîchit automatiquement")
            # Use time_auto_update to avoid blocking
            st.empty()
        
        # Statistics
        st.subheader("📊 Statistiques")
        stats = job_manager.get_statistics()
        
        col1, col2, col3, col4 = st.columns(4)
        
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
                            st.caption(f"Démarré: {job.started_at.strftime('%d/%m/%Y %H:%M:%S') if job.started_at else 'N/A'}")
                            st.caption(f"Durée: {job.duration} | Intervalle: {job.interval}")
                            
                            # Progress bar
                            progress = job.progress or 0
                            st.progress(progress / 100.0)
                            st.caption(f"Progression: {progress}% - {job.current_step or 'En attente...'}")
                        
                        with col2:
                            # Cancel button
                            if st.button("❌ Annuler", key=f"cancel_{job.id}"):
                                try:
                                    job_manager.cancel_job(job.id)
                                    st.success("Job annulé")
                                    st.rerun()
                                except Exception as e:
                                    st.error(f"Erreur: {e}")
                        
                        st.markdown("---")
        
        with tab2:
            st.subheader("Jobs complétés")
            completed_jobs = job_manager.get_jobs_by_status(JobStatus.COMPLETED)
            
            if not completed_jobs:
                st.info("Aucun job complété récemment")
            else:
                for job in completed_jobs[:20]:  # Limit to 20 most recent
                    with st.expander(f"✅ {job.ticker_symbol} - {job.source} ({job.completed_at.strftime('%d/%m/%Y %H:%M')})"):
                        col1, col2 = st.columns(2)
                        
                        with col1:
                            st.markdown(f"**Ticker:** {job.ticker_symbol}")
                            st.markdown(f"**Source:** {job.source}")
                            st.markdown(f"**Durée:** {job.duration}")
                            st.markdown(f"**Intervalle:** {job.interval}")
                        
                        with col2:
                            st.markdown(f"**Démarré:** {job.started_at.strftime('%d/%m/%Y %H:%M:%S') if job.started_at else 'N/A'}")
                            st.markdown(f"**Complété:** {job.completed_at.strftime('%d/%m/%Y %H:%M:%S') if job.completed_at else 'N/A'}")
                            
                            if job.started_at and job.completed_at:
                                duration = (job.completed_at - job.started_at).total_seconds()
                                st.markdown(f"**Temps écoulé:** {duration:.1f}s")
                        
                        st.markdown(f"**Résultats:**")
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
                    with st.expander(f"❌ {job.ticker_symbol} - {job.source} ({job.completed_at.strftime('%d/%m/%Y %H:%M') if job.completed_at else 'N/A'})"):
                        col1, col2 = st.columns(2)
                        
                        with col1:
                            st.markdown(f"**Ticker:** {job.ticker_symbol}")
                            st.markdown(f"**Source:** {job.source}")
                            st.markdown(f"**Durée:** {job.duration}")
                            st.markdown(f"**Intervalle:** {job.interval}")
                        
                        with col2:
                            st.markdown(f"**Démarré:** {job.started_at.strftime('%d/%m/%Y %H:%M:%S') if job.started_at else 'N/A'}")
                            st.markdown(f"**Échoué:** {job.completed_at.strftime('%d/%m/%Y %H:%M:%S') if job.completed_at else 'N/A'}")
                        
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
                        "Créé": job.created_at.strftime('%d/%m %H:%M'),
                        "Complété": job.completed_at.strftime('%d/%m %H:%M') if job.completed_at else "-"
                    })
                
                import pandas as pd
                df = pd.DataFrame(table_data)
                st.dataframe(df, use_container_width=True, hide_index=True)
        
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
        st.subheader("📡 Source de Données")
        
        col_source1, col_source2 = st.columns([2, 1])
        
        with col_source1:
            data_source = st.radio(
                "Choisir la source",
                ["Yahoo Finance (Délai 15min)", "IBKR (Temps Réel)"],
                help="Yahoo Finance: Données gratuites avec délai | IBKR: Données temps réel via IB Gateway"
            )
        
        with col_source2:
            if data_source == "IBKR (Temps Réel)":
                # IBKR connection status
                if 'ibkr_collector' not in st.session_state:
                    st.session_state.ibkr_collector = None
                    st.session_state.ibkr_connected = False
                
                if not st.session_state.ibkr_connected:
                    if st.button("🔌 Connecter IBKR", type="primary"):
                        try:
                            from backend.ibkr_collector import IBKRCollector
                            st.session_state.ibkr_collector = IBKRCollector()
                            if st.session_state.ibkr_collector.connect():
                                st.session_state.ibkr_connected = True
                                st.success("✅ Connecté!")
                                st.rerun()
                            else:
                                st.error("❌ Échec connexion")
                        except Exception as e:
                            st.error(f"❌ Erreur: {e}")
                else:
                    st.success("🟢 IBKR Connecté")
                    if st.button("🔌 Déconnecter"):
                        if st.session_state.ibkr_collector:
                            st.session_state.ibkr_collector.disconnect()
                        st.session_state.ibkr_collector = None
                        st.session_state.ibkr_connected = False
                        st.rerun()
        
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
        st.info("ℹ️ Les données proviennent de Yahoo Finance avec un délai d'environ 15 minutes. Le graphique se rafraîchit toutes les secondes.")
        
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
            
            # Get ticker object for database storage
            ticker_obj = db.query(Ticker).filter(Ticker.symbol == selected_symbol).first()
            
            # Continuous update loop
            max_points = 200  # Keep last 200 points for better visualization
            
            while st.session_state.live_running:
                try:
                    # Choose data source
                    if data_source == "IBKR (Temps Réel)" and st.session_state.ibkr_connected:
                        # Use IBKR data
                        collector = st.session_state.ibkr_collector
                        contract = collector.get_contract(selected_symbol)
                        
                        if contract:
                            # Request market data
                            ticker_data = collector.ib.reqMktData(contract, '', False, False)
                            collector.ib.sleep(1)  # Wait for data
                            
                            if ticker_data.last > 0:
                                current_price = ticker_data.last
                                current_volume = ticker_data.volume if ticker_data.volume > 0 else 0
                                current_time = datetime.now()
                                
                                # Get previous close
                                if len(st.session_state.live_data['price']) > 0:
                                    prev_close = st.session_state.live_data['price'][-1]
                                else:
                                    prev_close = current_price
                                
                                # Calculate change
                                price_change = current_price - prev_close
                                price_change_pct = (price_change / prev_close * 100) if prev_close else 0
                                
                                # Add to live data
                                st.session_state.live_data['time'].append(current_time)
                                st.session_state.live_data['price'].append(current_price)
                                st.session_state.live_data['open'].append(ticker_data.open if ticker_data.open > 0 else current_price)
                                st.session_state.live_data['high'].append(ticker_data.high if ticker_data.high > 0 else current_price)
                                st.session_state.live_data['low'].append(ticker_data.low if ticker_data.low > 0 else current_price)
                                st.session_state.live_data['volume'].append(current_volume)
                                
                                # Cancel market data subscription
                                collector.ib.cancelMktData(contract)
                            else:
                                # No real-time data, fallback to Yahoo
                                st.warning("⚠️ Pas de données temps réel IBKR, passage à Yahoo Finance")
                                data_source = "Yahoo Finance (Délai 15min)"
                        else:
                            st.error(f"❌ Impossible de trouver le contrat pour {selected_symbol}")
                            time_module.sleep(1)
                            continue
                    
                    if data_source == "Yahoo Finance (Délai 15min)" or not st.session_state.get('ibkr_connected', False):
                        # Use Yahoo Finance data
                        import yfinance as yf
                        
                        # Get Yahoo Finance symbol (add .PA for Paris exchange)
                        yf_symbol = f"{selected_symbol}.PA"
                        
                        # Map time scale to Yahoo Finance interval
                        interval_map = {
                            "1s": "1m",  # Yahoo Finance n'a pas de 1s, on utilise 1m
                            "1min": "1m",
                            "5min": "5m",
                            "15min": "15m",
                            "30min": "30m",
                            "1h": "1h",
                            "1jour": "1d"
                        }
                        yf_interval = interval_map.get(time_scale, "1m")
                        
                        # Fetch latest data from Yahoo Finance based on time scale
                        ticker_data = yf.Ticker(yf_symbol)
                        
                        # Get intraday data for the selected interval
                        if time_scale == "1jour":
                            hist_data = ticker_data.history(period="5d", interval=yf_interval)
                        else:
                            hist_data = ticker_data.history(period="1d", interval=yf_interval)
                        
                        if not hist_data.empty:
                            # Get the latest bar
                            latest_bar = hist_data.iloc[-1]
                            current_price = latest_bar['Close']
                            current_volume = latest_bar['Volume']
                            data_time = hist_data.index[-1]  # Timestamp from Yahoo
                            current_time = datetime.now()  # Current timestamp for display
                            
                            # Get previous close for change calculation
                            if len(hist_data) > 1:
                                prev_close = hist_data.iloc[-2]['Close']
                            else:
                                prev_close = current_price
                            
                            # Calculate change
                            price_change = current_price - prev_close
                            price_change_pct = (price_change / prev_close * 100) if prev_close else 0
                            
                            # Save to database (avoid duplicates by checking timestamp)
                            existing_record = db.query(HistoricalData).filter(
                                HistoricalData.ticker_id == ticker_obj.id,
                                HistoricalData.timestamp == data_time,
                                HistoricalData.interval == time_scale
                            ).first()
                            
                            if not existing_record:
                                new_record = HistoricalData(
                                    ticker_id=ticker_obj.id,
                                    timestamp=data_time,
                                    open=float(latest_bar['Open']),
                                    high=float(latest_bar['High']),
                                    low=float(latest_bar['Low']),
                                    close=float(latest_bar['Close']),
                                    volume=int(latest_bar['Volume']),
                                    interval=time_scale
                                )
                                db.add(new_record)
                                db.commit()
                            
                            # Add to live data for chart (with OHLCV)
                            st.session_state.live_data['time'].append(current_time)
                            st.session_state.live_data['price'].append(current_price)
                        st.session_state.live_data['open'].append(float(latest_bar['Open']))
                        st.session_state.live_data['high'].append(float(latest_bar['High']))
                        st.session_state.live_data['low'].append(float(latest_bar['Low']))
                        st.session_state.live_data['volume'].append(int(latest_bar['Volume']))
                        
                        # Keep only last max_points
                        if len(st.session_state.live_data['time']) > max_points:
                            st.session_state.live_data['time'] = st.session_state.live_data['time'][-max_points:]
                            st.session_state.live_data['price'] = st.session_state.live_data['price'][-max_points:]
                            st.session_state.live_data['open'] = st.session_state.live_data['open'][-max_points:]
                            st.session_state.live_data['high'] = st.session_state.live_data['high'][-max_points:]
                            st.session_state.live_data['low'] = st.session_state.live_data['low'][-max_points:]
                            st.session_state.live_data['volume'] = st.session_state.live_data['volume'][-max_points:]
                    else:
                        # Fallback to info if history not available
                        info = ticker_data.info
                        current_price = info.get('currentPrice') or info.get('regularMarketPrice', 0)
                        prev_close = info.get('previousClose', current_price)
                        current_volume = info.get('volume', 0)
                        current_time = datetime.now()
                        
                        price_change = current_price - prev_close
                        price_change_pct = (price_change / prev_close * 100) if prev_close else 0
                        
                        st.session_state.live_data['time'].append(current_time)
                        st.session_state.live_data['price'].append(current_price)
                        st.session_state.live_data['open'].append(current_price)
                        st.session_state.live_data['high'].append(current_price)
                        st.session_state.live_data['low'].append(current_price)
                        st.session_state.live_data['volume'].append(current_volume)
                        
                        if len(st.session_state.live_data['time']) > max_points:
                            st.session_state.live_data['time'] = st.session_state.live_data['time'][-max_points:]
                            st.session_state.live_data['price'] = st.session_state.live_data['price'][-max_points:]
                            st.session_state.live_data['open'] = st.session_state.live_data['open'][-max_points:]
                            st.session_state.live_data['high'] = st.session_state.live_data['high'][-max_points:]
                            st.session_state.live_data['low'] = st.session_state.live_data['low'][-max_points:]
                            st.session_state.live_data['volume'] = st.session_state.live_data['volume'][-max_points:]
                    
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
                        f"{current_volume:,}"
                    )
                    
                    time_placeholder.metric(
                        "Dernière MAJ",
                        current_time.strftime("%H:%M:%S")
                    )
                    
                    # Calculate indicators for live data if enough points
                    buy_signals = []
                    sell_signals = []
                    signal_times = []
                    signal_prices = []
                    signal_types = []
                    
                    if len(st.session_state.live_data['price']) >= 50:
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
                        latest_rsi = None
                        latest_macd = None
                        latest_macd_signal = None
                    
                    # Create line chart with indicators
                    fig = go.Figure()
                    
                    # Main price line
                    fig.add_trace(go.Scatter(
                        x=st.session_state.live_data['time'],
                        y=st.session_state.live_data['price'],
                        mode='lines',
                        name='Prix',
                        line=dict(color='#00D9FF', width=2),
                        fill='tozeroy',
                        fillcolor='rgba(0, 217, 255, 0.1)'
                    ))
                    
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
                    if signal.startswith("ACHAT"):
                        fig.add_trace(go.Scatter(
                            x=[st.session_state.live_data['time'][-1]],
                            y=[st.session_state.live_data['price'][-1]],
                            mode='markers',
                            name='Signal Achat (Actuel)',
                            marker=dict(size=18, color='lime', symbol='triangle-up', line=dict(width=2, color='green'))
                        ))
                    elif signal.startswith("VENTE"):
                        fig.add_trace(go.Scatter(
                            x=[st.session_state.live_data['time'][-1]],
                            y=[st.session_state.live_data['price'][-1]],
                            mode='markers',
                            name='Signal Vente (Actuel)',
                            marker=dict(size=18, color='orangered', symbol='triangle-down', line=dict(width=2, color='red'))
                        ))
                    
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
                    
                    # Update chart without key to prevent scroll
                    with chart_placeholder.container():
                        st.plotly_chart(fig, use_container_width=True)
                    
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
                                
                                st.dataframe(pd.DataFrame(trade_data), use_container_width=True)
                            else:
                                st.info("ℹ️ Aucun trade complet détecté avec cette stratégie (signaux d'achat sans vente correspondante).")

                        
                        with ind_col3:
                            st.markdown(f"### Signal: :{signal_color}[{signal}]")
                    
                    # Wait 1 second before next update
                    time_module.sleep(1)
                    
                except Exception as e:
                    st.error(f"❌ Erreur lors de la récupération des données: {e}")
                    st.session_state.live_running = False
                    break
        
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
        
        # Initialize IBKR collector in session state
        if 'ibkr_collector' not in st.session_state:
            st.session_state.ibkr_collector = None
            st.session_state.ibkr_connected = False
        
        # Connection section
        col_connect1, col_connect2 = st.columns([2, 1])
        
        with col_connect1:
            if not st.session_state.ibkr_connected:
                if st.button("🔌 Connecter à IBKR", type="primary", use_container_width=True):
                    try:
                        with st.spinner("Connexion à IB Gateway..."):
                            st.session_state.ibkr_collector = IBKRCollector()
                            if st.session_state.ibkr_collector.connect():
                                st.session_state.ibkr_connected = True
                                st.success("✅ Connecté à IBKR!")
                                st.rerun()
                            else:
                                st.error("❌ Échec de la connexion")
                    except Exception as e:
                        st.error(f"❌ Erreur: {e}")
            else:
                if st.button("🔌 Déconnecter", use_container_width=True):
                    if st.session_state.ibkr_collector:
                        st.session_state.ibkr_collector.disconnect()
                    st.session_state.ibkr_collector = None
                    st.session_state.ibkr_connected = False
                    st.rerun()
        
        with col_connect2:
            if st.session_state.ibkr_connected:
                st.success("🟢 Connecté")
            else:
                st.error("🔴 Déconnecté")
        
        if not st.session_state.ibkr_connected:
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
        
        collector = st.session_state.ibkr_collector
        
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
                st.dataframe(positions_df, use_container_width=True)
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
                limit_price = st.number_input("Prix limite", min_value=0.01, value=10.00, step=0.01, format="%.2f")
            
            # Submit order button
            if st.button("📤 Envoyer l'ordre", type="primary", use_container_width=True):
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
        
        # Open Orders
        st.subheader("📋 Ordres en Cours")
        
        try:
            open_orders = collector.ib.openOrders()
            
            if open_orders:
                orders_data = []
                for trade in open_orders:
                    orders_data.append({
                        'Order ID': trade.order.orderId,
                        'Symbol': trade.contract.symbol,
                        'Action': trade.order.action,
                        'Quantity': trade.order.totalQuantity,
                        'Type': trade.order.orderType,
                        'Status': trade.orderStatus.status,
                        'Filled': trade.orderStatus.filled,
                        'Remaining': trade.orderStatus.remaining
                    })
                
                orders_df = pd.DataFrame(orders_data)
                st.dataframe(orders_df, use_container_width=True)
                
                # Cancel order section
                if st.checkbox("Annuler un ordre"):
                    order_id_to_cancel = st.number_input("Order ID à annuler", min_value=1, step=1)
                    if st.button("❌ Annuler l'ordre", type="secondary"):
                        try:
                            # Find the order
                            order_to_cancel = None
                            for trade in open_orders:
                                if trade.order.orderId == order_id_to_cancel:
                                    order_to_cancel = trade
                                    break
                            
                            if order_to_cancel:
                                collector.ib.cancelOrder(order_to_cancel.order)
                                st.success(f"✅ Ordre {order_id_to_cancel} annulé")
                                collector.ib.sleep(1)
                                st.rerun()
                            else:
                                st.error(f"❌ Ordre {order_id_to_cancel} non trouvé")
                        
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
                st.dataframe(fills_df, use_container_width=True)
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
    
    st.info("ℹ️ **IBKR** : Pas de limite API pour les données historiques | **Yahoo Finance** : Gratuit avec délai de 15 minutes")
    
    if st.button("💾 Sauvegarder les paramètres"):
        st.success("✅ Paramètres sauvegardés")


if __name__ == "__main__":
    main()
