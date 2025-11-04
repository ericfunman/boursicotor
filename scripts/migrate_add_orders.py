"""
Database migration to add Order table
Run this script to update the database schema
"""
from backend.models import Base, engine, init_db
from backend.config import logger

def migrate_database():
    """Add Order table to existing database"""
    try:
        logger.info("Starting database migration...")
        
        # This will create only the tables that don't exist yet
        Base.metadata.create_all(bind=engine)
        
        logger.info("✅ Database migration completed successfully")
        logger.info("Order table created (if it didn't exist)")
        
    except Exception as e:
        logger.error(f"❌ Migration failed: {e}")
        raise

if __name__ == "__main__":
    print("=" * 60)
    print("DATABASE MIGRATION: Adding Order Management Tables")
    print("=" * 60)
    
    migrate_database()
    
    print("\n✅ Migration completed!")
    print("\nNew table added:")
    print("  - orders (for live trading order tracking)")
    print("\nYou can now use the Order Placement page in the frontend.")
