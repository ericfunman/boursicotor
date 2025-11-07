"""Check order status in database"""
from backend.models import SessionLocal, Order
from sqlalchemy import desc

db = SessionLocal()

# Get last 5 orders
orders = db.query(Order).order_by(desc(Order.id)).limit(5).all()

print("\n=== DERNIERS ORDRES ===\n")
for order in orders:
    print(f"ID: {order.id}")
    print(f"  Action: {order.action} {order.quantity} (Ticker ID: {order.ticker_id})")
    print(f"  Type: {order.order_type}")
    print(f"  Status: {order.status.value}")
    print(f"  Status Message: {order.status_message}")
    print(f"  IBKR Order ID: {order.ibkr_order_id}")
    print(f"  Created: {order.created_at}")
    print(f"  Submitted: {order.submitted_at}")
    print()

db.close()
