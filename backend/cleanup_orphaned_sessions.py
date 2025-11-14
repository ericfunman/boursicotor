"""
Cleanup utility for orphaned AutoTraderSession records
Removes sessions with NULL or invalid foreign key references
"""
from backend.models import SessionLocal, AutoTraderSession, Ticker, Strategy
from loguru import logger


def cleanup_orphaned_sessions(verbose: bool = True) -> int:
    """
    Delete AutoTraderSession records with NULL ticker_id or strategy_id
    
    Args:
        verbose: Print detailed logs
        
    Returns:
        Number of sessions deleted
    """
    db = SessionLocal()
    try:
        # Find sessions with NULL references
        orphaned = db.query(AutoTraderSession).filter(
            (AutoTraderSession.ticker_id == None) | 
            (AutoTraderSession.strategy_id == None)
        ).all()
        
        count = len(orphaned)
        
        if count > 0 and verbose:
            logger.warning(f"Found {count} session(s) with NULL references")
        
        for session in orphaned:
            if verbose:
                logger.warning(f"  → Deleting session #{session.id} (ticker_id={session.ticker_id}, strategy_id={session.strategy_id})")
            db.delete(session)
        
        if orphaned:
            db.commit()
            if verbose:
                logger.info(f"✅ Deleted {count} orphaned session(s)")
        else:
            if verbose:
                logger.info("✅ No orphaned sessions with NULL references found")
        
        return count
        
    except Exception as e:
        logger.error(f"❌ Error during cleanup: {e}", exc_info=True)
        db.rollback()
        return 0
    finally:
        db.close()


def cleanup_invalid_strategy_references(verbose: bool = True) -> int:
    """
    Delete AutoTraderSession records referencing non-existent Strategy IDs
    
    Args:
        verbose: Print detailed logs
        
    Returns:
        Number of sessions deleted
    """
    db = SessionLocal()
    try:
        # Get all valid strategy IDs
        valid_strategy_ids = [s[0] for s in db.query(Strategy.id).all()]
        
        # Find sessions with invalid strategy references (where relationship is None)
        all_sessions = db.query(AutoTraderSession).all()
        to_delete = [s for s in all_sessions if s.strategy is None and s.strategy_id is not None]
        
        count = len(to_delete)
        
        if count > 0 and verbose:
            logger.warning(f"Found {count} session(s) with invalid strategy references")
        
        for session in to_delete:
            if verbose:
                logger.warning(f"  → Deleting session #{session.id} (invalid strategy_id={session.strategy_id})")
            db.delete(session)
        
        if to_delete:
            db.commit()
            if verbose:
                logger.info(f"✅ Deleted {count} session(s) with invalid strategy references")
        else:
            if verbose:
                logger.info("✅ No sessions with invalid strategy references found")
        
        return count
        
    except Exception as e:
        logger.error(f"❌ Error during cleanup: {e}", exc_info=True)
        db.rollback()
        return 0
    finally:
        db.close()


def cleanup_invalid_ticker_references(verbose: bool = True) -> int:
    """
    Delete AutoTraderSession records referencing non-existent Ticker IDs
    
    Args:
        verbose: Print detailed logs
        
    Returns:
        Number of sessions deleted
    """
    db = SessionLocal()
    try:
        # Get all valid ticker IDs
        valid_ticker_ids = [t[0] for t in db.query(Ticker.id).all()]
        
        # Find sessions with invalid ticker references (where relationship is None)
        all_sessions = db.query(AutoTraderSession).all()
        to_delete = [s for s in all_sessions if s.ticker is None and s.ticker_id is not None]
        
        count = len(to_delete)
        
        if count > 0 and verbose:
            logger.warning(f"Found {count} session(s) with invalid ticker references")
        
        for session in to_delete:
            if verbose:
                logger.warning(f"  → Deleting session #{session.id} (invalid ticker_id={session.ticker_id})")
            db.delete(session)
        
        if to_delete:
            db.commit()
            if verbose:
                logger.info(f"✅ Deleted {count} session(s) with invalid ticker references")
        else:
            if verbose:
                logger.info("✅ No sessions with invalid ticker references found")
        
        return count
        
    except Exception as e:
        logger.error(f"❌ Error during cleanup: {e}", exc_info=True)
        db.rollback()
        return 0
    finally:
        db.close()


def cleanup_all(verbose: bool = True) -> int:
    """
    Run all cleanup operations
    
    Args:
        verbose: Print detailed logs
        
    Returns:
        Total number of sessions deleted
    """
    if verbose:
        logger.info("🧹 Starting database cleanup...")
    
    total_deleted = 0
    
    # Step 1: Cleanup NULL references
    deleted = cleanup_orphaned_sessions(verbose=verbose)
    total_deleted += deleted
    
    # Step 2: Cleanup invalid strategy references
    deleted = cleanup_invalid_strategy_references(verbose=verbose)
    total_deleted += deleted
    
    # Step 3: Cleanup invalid ticker references
    deleted = cleanup_invalid_ticker_references(verbose=verbose)
    total_deleted += deleted
    
    if verbose:
        logger.info(f"✅ Database cleanup complete! Total sessions deleted: {total_deleted}")
    
    return total_deleted


if __name__ == "__main__":
    cleanup_all(verbose=True)
