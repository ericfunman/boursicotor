#!/usr/bin/env python3
"""
Script de diagnostic pour comprendre les ordres SUBMITTED vs FILLED

Cela explique pourquoi beaucoup d'ordres sont "submitted" mais pas "filled"
"""

import sys
sys.path.insert(0, '/home/lapin/Developpement/Boursicotor')

from backend.models import SessionLocal, Order, OrderStatus
from datetime import datetime, timedelta
import pandas as pd

db = SessionLocal()

try:
    print("=" * 80)
    print("📊 DIAGNOSTIC ORDRES SUBMITTED vs FILLED")
    print("=" * 80)
    
    # Get all orders
    all_orders = db.query(Order).all()
    
    print(f"\n📈 STATISTIQUES GLOBALES")
    print(f"Total ordres: {len(all_orders)}")
    
    # Count by status
    status_counts = {}
    for status in OrderStatus:
        count = db.query(Order).filter(Order.status == status).count()
        status_counts[status.value] = count
    
    print(f"\nRépartition par statut:")
    for status, count in sorted(status_counts.items(), key=lambda x: x[1], reverse=True):
        print(f"  • {status.upper()}: {count}")
    
    # Submitted orders
    submitted_orders = db.query(Order).filter(Order.status == OrderStatus.SUBMITTED).all()
    
    print(f"\n🔍 ANALYSE DES ORDRES {len(submitted_orders)} SUBMITTED")
    
    if submitted_orders:
        # Group by age
        now = datetime.now()
        very_old = []  # > 7 days
        old = []       # 1-7 days
        recent = []    # < 1 day
        
        for order in submitted_orders:
            age = now - order.created_at
            if age > timedelta(days=7):
                very_old.append(order)
            elif age > timedelta(days=1):
                old.append(order)
            else:
                recent.append(order)
        
        print(f"\n  Par ancienneté:")
        print(f"  • Très anciens (>7j):  {len(very_old)} ⚠️ À NETTOYER")
        print(f"  • Anciens (1-7j):      {len(old)} ⚠️ À SURVEILLER")
        print(f"  • Récents (<1j):       {len(recent)} ✅ NORMAL")
        
        print(f"\n  Détails des ordres SUBMITTED récents:")
        for order in recent[:5]:  # Show first 5
            age_min = int((now - order.created_at).total_seconds() / 60)
            print(f"    - ID {order.id}: {order.action} {order.quantity} {order.ticker.symbol if order.ticker else '?'}")
            print(f"      Créé il y a {age_min} min | Rempli: {order.filled_quantity or 0}/{order.quantity}")
            print(f"      Type: {order.order_type} | Prix: {order.limit_price or 'market'}")
    
    # Filled orders
    filled_orders = db.query(Order).filter(Order.status == OrderStatus.FILLED).all()
    
    print(f"\n✅ ANALYSE DES ORDRES {len(filled_orders)} FILLED")
    if filled_orders:
        # Calculate success rate
        avg_fill_price = sum(o.avg_fill_price or 0 for o in filled_orders) / len(filled_orders) if filled_orders else 0
        total_qty = sum(o.quantity for o in filled_orders)
        
        print(f"  • Quantité totale remplie: {total_qty}")
        print(f"  • Prix moyen de remplissage: {avg_fill_price:.2f} €")
        
        # Filled in progress (partially filled)
        partial = db.query(Order).filter(
            Order.filled_quantity > 0,
            Order.filled_quantity < Order.quantity,
            Order.status != OrderStatus.FILLED
        ).all()
        
        if partial:
            print(f"\n⏳ ORDRES PARTIELLEMENT REMPLIS: {len(partial)}")
            for order in partial[:3]:
                pct = (order.filled_quantity / order.quantity * 100) if order.quantity > 0 else 0
                print(f"  - ID {order.id}: {order.filled_quantity}/{order.quantity} ({pct:.0f}%)")
    
    # Potential issues
    print(f"\n⚠️  DIAGNOSTIC D'ANOMALIES")
    
    # Orders stuck in SUBMITTED
    stuck = db.query(Order).filter(
        Order.status == OrderStatus.SUBMITTED,
        Order.created_at < (now - timedelta(hours=1))
    ).all()
    
    if stuck:
        print(f"\n  {len(stuck)} ORDRES BLOQUÉS depuis > 1h:")
        for order in stuck[:3]:
            hours_ago = int((now - order.created_at).total_seconds() / 3600)
            print(f"    - ID {order.id}: {order.action} {order.quantity} {order.ticker.symbol if order.ticker else '?'} (depuis {hours_ago}h)")
        
        print(f"\n  SOLUTION: Utilisez le bouton '🧹 Nettoyer ordres bloqués' dans la page Trading")
    
    # Cancelled orders
    cancelled = db.query(Order).filter(Order.status == OrderStatus.CANCELLED).all()
    
    if cancelled:
        print(f"\n  {len(cancelled)} ORDRES ANNULÉS (normal après nettoyage)")
    
    print(f"\n" + "=" * 80)
    print("ℹ️  EXPLICATION: C'EST NORMAL!")
    print("=" * 80)
    print("""
    Les ordres "SUBMITTED" non remplis peuvent être:
    
    1. ✅ LIMIT ORDERS EN ATTENTE
       - Order placé à un prix spécifique
       - En attente que le marché atteigne ce prix
       - Peut rester "SUBMITTED" plusieurs jours!
    
    2. ✅ MARKET ORDERS EN FILE D'ATTENTE
       - Ordre de marché non exécuté immédiatement
       - Pas assez de liquidité disponible
       - Attend la prochaine opportunité
    
    3. ✅ ORDRES TRÈS RÉCENTS
       - Juste envoyés à IBKR
       - Pas encore synchronisés avec la DB
       - Seront FILLED dans les secondes/minutes
    
    4. ⚠️  ORDRES ANCIENS BLOQUÉS (> 24h)
       - Peut indiquer une déconnexion TWS
       - IBKR a annulé automatiquement
       - Doit être nettoyé manuellement
    
    ACTION RECOMMANDÉE:
    • Les ordres récents (<1 jour): ✅ OK, laisser tranquille
    • Les ordres anciens (>7 jours): 🧹 Cliquer "Nettoyer ordres bloqués"
    """)
    
    print("=" * 80)

finally:
    db.close()
