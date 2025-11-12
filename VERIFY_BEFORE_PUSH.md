# Pre-Push Verification

This project includes an automated verification script that validates code before pushing to GitHub.

## Usage

### Option 1: Manual verification before each push
```bash
python verify_before_push.py
```

### Option 2: Automatic verification with Git hooks

#### Windows (PowerShell)
```powershell
# Configure Git to use PowerShell for hooks
git config core.hooksPath .git/hooks

# The pre-push.ps1 hook will run automatically before each push
```

#### macOS/Linux
```bash
# Make the hook executable
chmod +x .git/hooks/pre-push

# The hook will run automatically before each push
```

## What the verification checks:

1. ✅ **Unit Tests** - All 22 tests in tests/test_security.py must pass
2. ✅ **Python Syntax** - All modified backend files must have valid Python syntax
3. ✅ **Code Quality** - Coverage reports and linting validation

## If verification fails:

The push will be blocked with a clear error message. Fix the issues and try again:
```bash
# Fix the reported issues, then
python verify_before_push.py
git push
```

## Bypassing verification (not recommended)

To force push without verification:
```bash
git push --no-verify
```

## Files involved:

- `verify_before_push.py` - Main verification script
- `.git/hooks/pre-push` - Git hook for Linux/macOS
- `.git/hooks/pre-push.ps1` - Git hook for Windows PowerShell
