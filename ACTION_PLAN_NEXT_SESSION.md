# Action Plan - Next Session

## Priority Overview

**Current State:**
- Local Coverage: **45%** ✅
- Test Pass Rate: **94%**
- Failing Tests: **27** (DB/API connection issues)
- SonarCloud: Pending re-analysis

**Session Goal:** Reach **50%+ coverage** by fixing failing tests and adding critical module tests.

---

## Phase 1: Fix Failing Tests (30 minutes) 🔧

### Task 1.1: Database Connection Issues (16 tests)

**Files to Fix:**
- `tests/test_data_collector.py` (13 failures)
- `tests/test_config.py` (2 failures)
- `tests/test_job_strategy_managers_comprehensive.py` (8 failures)

**Root Causes:**
1. SQLite database lock issues (multiple tests accessing same DB)
2. Missing connection cleanup
3. Uncommitted transactions blocking other tests

**Solution Implementation:**
```python
# Pattern for all DB tests
import pytest
from unittest.mock import patch, MagicMock

@pytest.fixture(autouse=True)
def cleanup_db():
    """Clean up database connections after each test"""
    yield
    # Force cleanup
    import gc
    gc.collect()

# Example fixture
@pytest.fixture
def db_session_mock():
    """Mock database session to avoid real DB access"""
    with patch('backend.models.db_session') as mock:
        yield mock
```

**Steps:**
1. Add `conftest.py` in tests/ folder with base fixtures
2. Update each failing test to use mocked DB sessions
3. Use `@patch` decorator for SQLAlchemy operations
4. Replace real DB calls with mocks

**Expected Result:** 
- 16 tests: FAILING → PASSING

---

### Task 1.2: External API/Service Issues (11 tests)

**Files to Fix:**
- `tests/test_frontend.py` (1 failure)
- `tests/test_connection_strategy.py` (1 error)

**Root Causes:**
1. Celery broker not running
2. IBAPI import failures
3. Missing service mocks

**Solution Implementation:**
```python
# Patch external services
@patch('backend.celery_config.celery')
@patch('backend.tasks.celery')
def test_something(mock_celery):
    mock_celery.task = MagicMock()
    # Test code here
```

**Steps:**
1. Add service mocks to `conftest.py`
2. Update frontend tests to mock data sources
3. Ensure IBAPI imports are properly skipped/mocked
4. Verify Celery tasks are mocked

**Expected Result:**
- 11 tests: FAILING/ERROR → PASSING/SKIPPED

---

## Phase 2: Add High-Impact Module Tests (1-2 hours) 📊

### Task 2.1: Order Manager Tests (520 lines, 9% coverage)

**File:** `backend/order_manager.py`

**Current Coverage:** 9% (only 54 lines covered)

**Key Methods to Test:**
- `create_order()` - Create new order
- `cancel_order()` - Cancel order
- `get_order_status()` - Query status
- `update_order()` - Update existing order
- `get_all_orders()` - List all orders

**Test Strategy:**
```python
# tests/test_order_manager_enhanced.py
class TestOrderManagerCore:
    def test_create_order_basic(self):
        """Test basic order creation"""
        
    def test_create_order_validation(self):
        """Test order validation"""
        
    def test_cancel_order(self):
        """Test order cancellation"""
        
    def test_order_status_transitions(self):
        """Test status workflow"""
        
    def test_database_persistence(self):
        """Test order saved to DB"""
```

**Coverage Target:** 9% → 40%+

**File to Create:**
- `tests/test_order_manager_enhanced.py` (~200 lines, 15-20 tests)

---

### Task 2.2: IBKR Connector Tests (159 lines, 3% coverage)

**File:** `backend/ibkr_connector.py`

**Current Coverage:** 3% (only 4 lines covered)

**Challenge:** Requires IBAPI library (proprietary)

**Mitigation Strategy:**
1. Mock IBAPI completely
2. Test only connection/error logic
3. Skip full integration tests

**Test Strategy:**
```python
# tests/test_ibkr_connector_mocked.py
@patch('backend.ibkr_connector.IB')
class TestIBKRConnectorMocked:
    def test_connector_initialization(self, mock_ib):
        """Test connector can be created"""
        
    def test_connection_error_handling(self, mock_ib):
        """Test error handling"""
        
    def test_contract_conversion(self, mock_ib):
        """Test contract object creation"""
```

**Coverage Target:** 3% → 30%+

**File to Create:**
- `tests/test_ibkr_connector_mocked.py` (~150 lines, 12-15 tests)

---

## Phase 3: Validation & Measurement (15 minutes) ✅

### Task 3.1: Run Full Test Suite
```bash
cd "c:\Users\Eric LAPINA\Documents\Boursicotor"
python -m pytest tests/ -q --cov=backend --cov-report=term
```

**Expected Results:**
- Tests: 598/599 passing (1 skipped)
- Coverage: **50%+** local
- No failed tests

### Task 3.2: Generate Reports
```bash
python -m pytest tests/ -q --cov=backend --cov-report=html
```

### Task 3.3: Commit & Push
```bash
git add tests/
git commit -m "Fix 27 failing tests and add high-impact module tests - achieve 50%+ coverage"
git push origin main
```

---

## Phase 4: SonarCloud Analysis (Automatic) ⏳

**Timeline:**
- Next CI/CD run: SonarCloud re-analyzes code
- Expected SonarCloud coverage: 30-35% (up from 22.5%)
- Expected issue count: 100-120 (down from 212)

**What to Monitor:**
- SonarCloud dashboard for new measurements
- Per-module coverage breakdown
- Issue severity distribution

---

## Detailed Test Checklist

### Test File: `tests/test_order_manager_enhanced.py`

```python
# Classes and methods to implement
TestOrderCreation
  ✓ test_create_order_with_valid_params
  ✓ test_create_order_invalid_quantity
  ✓ test_create_order_invalid_price
  ✓ test_create_order_saves_to_db
  ✓ test_create_order_returns_order_object

TestOrderCancellation
  ✓ test_cancel_existing_order
  ✓ test_cancel_non_existent_order
  ✓ test_cancel_already_completed_order

TestOrderQuery
  ✓ test_get_order_by_id
  ✓ test_get_all_orders
  ✓ test_get_orders_by_status
  ✓ test_get_orders_by_symbol

TestOrderStatus
  ✓ test_status_pending
  ✓ test_status_filled
  ✓ test_status_cancelled
  ✓ test_status_transition_validation

TestOrderUpdate
  ✓ test_update_order_quantity
  ✓ test_update_order_price
  ✓ test_update_completed_order_fails
```

### Test File: `tests/test_ibkr_connector_mocked.py`

```python
TestIBKRInitialization
  ✓ test_connector_can_be_created
  ✓ test_connector_attributes_exist
  ✓ test_default_configuration

TestIBKRConnectionLogic
  ✓ test_connection_status_check
  ✓ test_connection_error_propagation
  ✓ test_reconnection_attempt

TestContractConversion
  ✓ test_ibkr_contract_creation
  ✓ test_contract_validation
  ✓ test_invalid_contract_handling

TestIBKRExceptions
  ✓ test_connection_timeout
  ✓ test_invalid_credentials
  ✓ test_rate_limiting
```

---

## Success Criteria

✅ **Must Have:**
- [x] 598/599 tests passing
- [x] 50%+ local coverage
- [x] No database connection errors
- [x] No external service errors
- [x] Clear commit history

✅ **Nice to Have:**
- [ ] 55%+ local coverage
- [ ] 35%+ SonarCloud coverage
- [ ] <100 SonarCloud issues
- [ ] <10 seconds test execution time

---

## Estimated Time

| Phase | Task | Time | Status |
|-------|------|------|--------|
| 1 | Fix DB Tests | 15 min | 🔄 TODO |
| 1 | Fix API Tests | 15 min | 🔄 TODO |
| 2 | Order Manager Tests | 45 min | 🔄 TODO |
| 2 | IBKR Connector Tests | 30 min | 🔄 TODO |
| 3 | Validation & Commit | 15 min | 🔄 TODO |
| **TOTAL** | **All Phases** | **2 hours** | **🔄 READY** |

---

## Notes for Next Session

### Key Insights Learned
1. **Backend coverage requires backend imports** - Generic tests don't count
2. **Database tests need fixtures** - Mock or use in-memory DB
3. **API tests need mocks** - Don't depend on external services
4. **Large modules need breaking down** - Test in focused classes

### Potential Blockers
1. IBAPI library not installed - Will use mocks
2. Database connections timing out - Will use connection pooling
3. Celery broker not running - Will mock tasks

### Tools/Resources Needed
- pytest fixtures documentation
- unittest.mock reference
- SQLAlchemy test patterns

---

## Before Starting

1. **Ensure pytest is working:** `python -m pytest --version`
2. **Check coverage tool:** `pip list | grep pytest-cov`
3. **Verify database:** SQLite file exists at `boursicotor.db`
4. **Review current failures:** Check test output above

---

## Success Message

When all tasks are complete, you should see:

```
======================== test session starts ========================
platform win32 -- Python 3.13.7, pytest-8.4.2, pluggy-1.6.0
collected 625 items

tests\... ............................................        [100%]

======================== 598 passed, 1 skipped in 8.42s ========================
TOTAL: 50% coverage
```

Good luck! 🚀
