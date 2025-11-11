# Sonar Issues Fix Strategy

## Current Status
- **Sonar Coverage**: 5.6%
- **Total Issues**: 163 OPEN
- **Goal**: Fix as many issues as possible, focus on high-impact ones

## Issue Breakdown (Estimated from Sonar)

### High Priority (Easy fixes, high impact)

#### S1192 - Duplicated Strings (~40 issues)
**Impact**: Extract duplicated strings to constants
**Effort**: Low (regex + constants file)
**Status**: Created constants.py, but need safe implementation

**Top duplicated:**
- "timestamp" (25x)
- "chunk_days" (23x)  
- "high", "low", "open", "close", "volume" (20+ each)

**Approach**:
1. ✅ Created backend/constants.py with common constants
2. ✅ Identified 91 duplicated strings
3. ⏳ Need: Careful manual replacement in key files

#### S7498 - dict() Literals (~38 issues)
**Impact**: Use {} instead of dict() for clarity
**Effort**: Very Low (regex replacement)
**Status**: Searched, no simple dict() found (likely dict(...args))

**Approach**:
1. Search for `dict()` - mostly empty dict calls
2. Replace with `{}`
3. No dict(arg1=x, arg2=y) style (keep as-is)

### Medium Priority (Requires thought)

#### S3776 - Cognitive Complexity (~27 issues)
**Impact**: Reduce method complexity
**Effort**: Medium (refactoring long methods)
**Status**: Identified 56 long functions (>30 lines)

**Top candidates:**
- backend/ibkr_collector.py - many complex methods
- backend/auto_trader.py - trading logic is complex
- backend/data_collector.py - data processing chains

**Approach**:
1. Break long methods into smaller ones
2. Extract helper methods
3. Reduce nesting depth

#### S1481 - Unused Variables (~16 issues)
**Impact**: Remove unused variables
**Effort**: Low (identify and remove or prefix with _)
**Status**: Script attempted, but needs manual review

**Approach**:
1. Review except blocks - add _ prefix to unused exceptions
2. Review loop variables - prefix unused ones
3. Remove truly unused assignments

### Low Priority (Context-dependent)

#### S1172 - Unused Parameters (3 issues)
**Approach**: Add _ prefix to unused params or remove

#### S117 - Naming Convention (14 issues)
**Approach**: Rename variables to follow snake_case

#### S5886, S3358, S1066, S5713 - Other rules
**Approach**: Case-by-case review

## Implementation Plan

### Phase 1: Foundation (Current)
- ✅ Created constants.py for string reuse
- ⏳ Setup: Manual string replacement in critical files

### Phase 2: Quick Wins
- [ ] Replace dict() with {} (30-40 issues)
- [ ] Prefix unused variables with _ (16 issues)
- [ ] Fix naming conventions (14 issues)

**Expected Result**: ~60-70 issues fixed

### Phase 3: Complex Fixes
- [ ] Refactor long functions (S3776)
- [ ] Extract duplicated strings carefully (S1192)

**Expected Result**: 50+ more issues fixed

### Phase 4: Validation
- [ ] Run tests
- [ ] Commit and push
- [ ] Verify Sonar scan

## Files with Most Issues

1. **backend/ibkr_collector.py** (643 lines, complex)
2. **backend/order_manager.py** (507 lines, complex)
3. **backend/auto_trader.py** (262 lines, trading logic)
4. **backend/data_collector.py** (222 lines, data processing)
5. **backend/ibkr_connector.py** (158 lines)

## Quick Win Candidates

### S7498 (dict literals)
Files likely affected:
- data_collector.py
- auto_trader.py
- ibkr_collector.py

### S1481 (unused variables)
Common patterns:
- `except Exception as e:` (not used)
- `for item in items:` (item not used)
- `result = func()` (result not used)

### S117 (naming)
Look for:
- Single letter variables (x, y, i, j - except in loops)
- Camel case instead of snake_case
- All-uppercase non-constants

## Success Metrics

| Metric | Current | Target |
|--------|---------|--------|
| Total Issues | 163 | <50 |
| Coverage | 5.6% | TBD (focus is issues first) |
| Test Status | ✅ All pass | ✅ All pass |

## Manual Fix Examples

### Example 1: S1192 (duplicated strings)
```python
# Before
df["timestamp"] = ...
df["timestamp"] = ...
result["timestamp"] = ...

# After
from backend.constants import CONST_TIMESTAMP
df[CONST_TIMESTAMP] = ...
df[CONST_TIMESTAMP] = ...
result[CONST_TIMESTAMP] = ...
```

### Example 2: S1481 (unused variable)
```python
# Before
except Exception as e:
    logger.error("Error occurred")

# After
except Exception as _e:
    logger.error("Error occurred")
```

### Example 3: S7498 (dict literal)
```python
# Before
result = dict()

# After
result = {}
```

## Next Steps

1. Focus on S7498 (dict() replacements) - safest, highest confidence
2. Then S1481 (unused variables) - straightforward prefixing
3. Then carefully handle S1192 (string constants)
4. Finally S3776 (refactoring) if time permits
