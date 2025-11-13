def live_prices_page():
    """Live streaming prices page - simple version with reqHistoricalData polling"""
    st.header("📊 Cours Live")
    
    # Get tickers with collected data
    from backend.models import SessionLocal, Ticker, HistoricalData
    from sqlalchemy import distinct
    db = SessionLocal()
    
    try:
        # Get ONLY tickers that have HistoricalData (collected data)
        tickers_with_data = db.query(Ticker).join(
            HistoricalData, Ticker.id == HistoricalData.ticker_id
        ).distinct().all()
        
        if not tickers_with_data:
            st.warning("⚠️ Aucune action disponible. Collectez des données d'abord dans l'onglet 'Collecte de Données'.")
            return
        
        # Create ticker selection
        ticker_options = {ticker.symbol: f"{ticker.symbol} - {ticker.name}" for ticker in tickers_with_data}
        
        col1, col2 = st.columns([2, 1])
        
        with col1:
            selected_symbol = st.selectbox(
                "Sélectionner une action",
                options=list(ticker_options.keys()),
                format_func=lambda x: ticker_options[x]
            )
        
        with col2:
            if st.button("▶️ Démarrer le streaming", type="primary"):
                st.session_state.live_streaming = True
                st.rerun()
            
            if st.session_state.get('live_streaming', False):
                if st.button("⏸️ Arrêter"):
                    st.session_state.live_streaming = False
                    st.session_state.live_prices = {'time': [], 'price': []}
                    st.rerun()
        
        st.markdown("---")
        
        # Display metrics
        metric_col1, metric_col2, metric_col3, metric_col4 = st.columns(4)
        
        price_placeholder = metric_col1.empty()
        change_placeholder = metric_col2.empty()
        time_placeholder = metric_col3.empty()
        count_placeholder = metric_col4.empty()
        
        # Chart placeholder
        chart_placeholder = st.empty()
        
        st.info("ℹ️ Les prix sont mis à jour toutes les 3 secondes via les données IBKR (retard ~15min)")
        
        # Initialize live data storage
        if 'live_prices' not in st.session_state:
            st.session_state.live_prices = {'time': [], 'price': []}
        
        # Live streaming loop
        if st.session_state.get('live_streaming', False):
            from backend.data_collector import DataCollector
            import time as time_module
            from datetime import datetime
            import plotly.graph_objects as go
            
            collector = DataCollector()
            last_price = None
            update_count = 0
            
            # Streaming loop - 30 iterations (about 1.5 minutes)
            for i in range(30):
                try:
                    # Get current market price
                    current_price = collector.get_current_market_price(selected_symbol)
                    current_time = datetime.now()
                    
                    if current_price and current_price > 0:
                        # Add to live data
                        st.session_state.live_prices['time'].append(current_time)
                        st.session_state.live_prices['price'].append(current_price)
                        update_count += 1
                        
                        # Calculate change
                        price_change = 0
                        price_change_pct = 0
                        if last_price:
                            price_change = current_price - last_price
                            price_change_pct = (price_change / last_price * 100) if last_price else 0
                        
                        last_price = current_price
                        
                        # Update metrics
                        with price_placeholder.container():
                            st.metric(
                                "📍 Prix Actuel",
                                f"{current_price:.2f}€",
                                f"{price_change:+.2f} ({price_change_pct:+.2f}%)" if price_change != 0 else "Nouveau"
                            )
                        
                        with time_placeholder.container():
                            st.metric("🕐 Dernière MAJ", current_time.strftime("%H:%M:%S"))
                        
                        with count_placeholder.container():
                            st.metric("📊 Points", f"{update_count}")
                        
                        # Display chart if we have data
                        if len(st.session_state.live_prices['price']) > 0:
                            fig = go.Figure()
                            fig.add_trace(go.Scatter(
                                x=st.session_state.live_prices['time'],
                                y=st.session_state.live_prices['price'],
                                mode='lines+markers',
                                name=selected_symbol,
                                line=dict(color='#00D9FF', width=2),
                                fill='tozeroy',
                                fillcolor='rgba(0, 217, 255, 0.1)'
                            ))
                            
                            fig.update_layout(
                                title=f"{selected_symbol} - Streaming en Direct",
                                yaxis_title="Prix (€)",
                                xaxis_title="Temps",
                                template="plotly_dark",
                                height=500,
                                hovermode='x unified',
                                showlegend=True
                            )
                            
                            with chart_placeholder.container():
                                st.plotly_chart(fig, use_container_width=True)
                    
                    # Wait before next update
                    time_module.sleep(3)
                    
                except Exception as e:
                    logger.error(f"Error during streaming: {e}")
                    st.error(f"❌ Erreur: {e}")
                    st.session_state.live_streaming = False
                    break
            
            # End of streaming
            st.success(f"✅ Streaming terminé - {update_count} points collectés")
            st.session_state.live_streaming = False
        
        else:
            # Not streaming - show help
            if len(st.session_state.live_prices['price']) == 0:
                st.info("👆 Cliquez sur 'Démarrer le streaming' pour commencer")
    
    finally:
        db.close()
