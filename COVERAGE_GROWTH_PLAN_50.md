# 🚀 Coverage Growth Strategy - Target 50%+

**Current Status:** 44.3% on SonarCloud ✅  
**Goal:** 50%+ coverage  
**Gap:** +5.7%  
**Strategy:** Targeted module testing

---

## 📊 Coverage Priority Matrix

Based on typical backend project structure, prioritize:

### TIER 1: Highest Impact (Large modules, low coverage)
**Focus area for maximum gain**

Estimated modules (~500+ lines each, <15% coverage):
- `order_manager.py` (~520 lines, ~9%) → **+2-3%** if 40% coverage
- `ibkr_collector.py` (~640 lines, ~34%) → **+1-2%** if 50% coverage
- `data_collector.py` (~233 lines, ~58%) → **+1-2%** if 75% coverage
- `ibkr_connector.py` (~159 lines, ~3%) → **+0.5%** if 30% coverage

**Estimated total gain:** +5-7% → **50%+** ✅

### TIER 2: Quick Wins (Small modules, 0% coverage)
**Easy targets**
- Any <100 line modules at 0% coverage
- New modules added recently

### TIER 3: Maintenance (Already 60%+)
**Maintain quality**
- technical_indicators.py (96%)
- security.py (95%)
- Keep these stable

---

## 🎯 Action Plan

### Phase 1: Create order_manager Tests (45 min)
**File:** `tests/test_order_manager_critical.py`  
**Target:** 40%+ coverage → +2-3% global

```python
TestOrderManagerCore:
  ✓ test_create_order_basic
  ✓ test_create_order_with_defaults
  ✓ test_create_order_validation
  ✓ test_cancel_existing_order
  ✓ test_cancel_non_existent_order
  ✓ test_get_order_status
  ✓ test_update_order_fields
  ✓ test_order_persistence
  ✓ test_order_state_transitions
  (15-20 test methods)
```

**Estimated Coverage Improvement:**
- order_manager.py: 9% → 40% = +31% points
- Global impact: +0.93% (520/3453 * 31%)

### Phase 2: Create IBKR Connector Tests (30 min)
**File:** `tests/test_ibkr_connector_critical.py`  
**Target:** 30%+ coverage → +0.5% global

```python
TestIBKRConnectorCore (mocked):
  ✓ test_connector_initialization
  ✓ test_connection_status
  ✓ test_contract_conversion
  ✓ test_error_handling
  ✓ test_rate_limiting
  (10-12 test methods)
```

### Phase 3: Improve data_collector Tests (30 min)
**File:** Enhance `test_data_collector.py` or create `test_data_collector_enhanced.py`  
**Target:** 75%+ coverage → +1% global

```python
TestDataCollectorEnhanced:
  ✓ test_historical_data_edge_cases
  ✓ test_error_recovery
  ✓ test_data_interpolation
  ✓ test_storage_optimization
  (8-12 additional test methods)
```

---

## 🔨 Implementation Strategy

### Test File Structure

**test_order_manager_critical.py** (~250 lines)
```python
import pytest
from unittest.mock import Mock, patch, MagicMock
from backend.order_manager import OrderManager

@pytest.fixture
def order_manager():
    """Create order manager with mocked database"""
    with patch('backend.models.db_session') as mock_db:
        manager = OrderManager()
        manager.db = mock_db
        yield manager

class TestOrderManagerCore:
    """Core order manager functionality"""
    
    def test_create_order_basic(self, order_manager):
        """Test basic order creation"""
        result = order_manager.create_order(
            symbol='AAPL',
            quantity=100,
            price=150.0,
            order_type='BUY'
        )
        assert result is not None
        assert result.symbol == 'AAPL'
        
    def test_create_order_validation(self, order_manager):
        """Test order validation"""
        with pytest.raises(ValueError):
            order_manager.create_order(
                symbol='AAPL',
                quantity=-100,  # Invalid
                price=150.0,
                order_type='BUY'
            )
    
    # ... more tests
```

**test_ibkr_connector_critical.py** (~200 lines)
```python
import pytest
from unittest.mock import Mock, patch
from backend.ibkr_connector import IBKRConnector

@pytest.fixture
def connector():
    """Create connector with mocked IBAPI"""
    with patch('backend.ibkr_connector.IB') as mock_ib:
        connector = IBKRConnector()
        connector.ib = mock_ib
        yield connector

class TestIBKRConnectorCore:
    """Core IBKR connector functionality"""
    
    def test_connector_initialization(self, connector):
        """Test connector can be initialized"""
        assert connector is not None
        assert connector.ib is not None
        
    def test_contract_conversion(self, connector):
        """Test stock symbol to contract conversion"""
        contract = connector._symbol_to_contract('AAPL')
        assert contract.symbol == 'AAPL'
        
    # ... more tests
```

---

## 📈 Expected Results

### Coverage Gains by Module

| Module | Current | Target | Gain | Global Impact |
|--------|---------|--------|------|---------|
| order_manager | 9% | 40% | +31% | +0.93% |
| ibkr_connector | 3% | 30% | +27% | +0.12% |
| data_collector | 58% | 75% | +17% | +0.13% |
| others | - | - | - | +0.3% (misc) |
| **TOTAL** | **44.3%** | **50%+** | - | **+1.5%** |

**Expected SonarCloud Result:** 44.3% → **45.8%+** ✅

---

## ⏱️ Timeline

| Phase | Task | Time | Expected Result |
|-------|------|------|---------|
| 1 | Create order_manager tests | 45 min | +0.93% |
| 2 | Create ibkr_connector tests | 30 min | +0.12% |
| 3 | Improve data_collector tests | 30 min | +0.13% |
| 4 | Validate + commit | 15 min | Ready to push |
| **TOTAL** | **All phases** | **2 hours** | **50%+** ✅ |

---

## 🎯 Success Criteria

- [ ] order_manager coverage: 40%+
- [ ] ibkr_connector coverage: 30%+
- [ ] data_collector coverage: 75%+
- [ ] Local coverage: 50%+
- [ ] All tests passing (>95%)
- [ ] Commits clean and pushed

---

## 🚀 Ready to Start?

Press go and I'll:
1. Create test_order_manager_critical.py (45 min work)
2. Create test_ibkr_connector_critical.py (30 min work)
3. Enhance data_collector tests (30 min work)
4. Validate coverage (15 min work)
5. Commit and push to GitHub

**Expected result: 50%+ local coverage, ~45-46% on SonarCloud**

Let's do it! 💪
