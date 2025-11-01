"""Fix app.py menu - Add Trading page"""

with open('frontend/app.py', 'r', encoding='utf-8') as f:
    content = f.read()

# Fix menu
old_menu = '"📊 Dashboard", "💾 Collecte de Données", "📈 Analyse Technique", \n             "📡 Cours Live", "🔙 Backtesting", "🤖 Trading Automatique", "⚙️ Paramètres"'
new_menu = '"📊 Dashboard", "💾 Collecte de Données", "📈 Analyse Technique", \n             "📡 Cours Live", "💼 Trading", "🔙 Backtesting", "🤖 Trading Automatique", "⚙️ Paramètres"'

content = content.replace(old_menu, new_menu)

# Fix routing
old_routing = '''elif page == "📡 Cours Live":
        live_prices_page()
    elif page == "🔙 Backtesting":'''

new_routing = '''elif page == "📡 Cours Live":
        live_prices_page()
    elif page == "💼 Trading":
        trading_page()
    elif page == "🔙 Backtesting":'''

content = content.replace(old_routing, new_routing)

with open('frontend/app.py', 'w', encoding='utf-8') as f:
    f.write(content)

print("✅ Menu et routing mis à jour")
