"""
Script to fix the dashboard_page function
"""

dashboard_function = '''def dashboard_page():
    """Dashboard page - Uses global IBKR connection"""
    st.header("📊 Dashboard")
    
    # Use global IBKR connection
    collector = get_global_ibkr()
    
    if not st.session_state.global_ibkr_connected:
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
    
    # Connected - show real data
    try:
        # Get account summary
        account_summary = collector.get_account_summary()
        
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
            
            positions = collector.get_positions()
            
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
            # Get trades (fills) from today
            from datetime import datetime
            trades = collector.ib.fills()
            
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

'''

# Read the file
with open('frontend/app.py', 'r', encoding='utf-8') as f:
    content = f.read()

# Find the start of dashboard_page
start_marker = 'def dashboard_page():'
start_idx = content.find(start_marker)

if start_idx == -1:
    print("Could not find dashboard_page function!")
    exit(1)

# Find the next function definition
next_func_marker = '\ndef data_collection_page():'
end_idx = content.find(next_func_marker, start_idx)

if end_idx == -1:
    print("Could not find end of dashboard_page!")
    exit(1)

# Replace the function
new_content = content[:start_idx] + dashboard_function + '\n' + content[end_idx:]

# Write back
with open('frontend/app.py', 'w', encoding='utf-8') as f:
    f.write(new_content)

print("✅ dashboard_page function fixed!")
