# Boursicotor CI/CD Verification Guide

## Quick Start

### Before each push (Local validation)
```bash
python verify_before_push.py
```
This validates:
- ✓ 22 unit tests pass
- ✓ Python syntax is valid
- ✓ No import errors

### After each push (Monitor GitHub Actions)
```bash
python verify_after_push.py
```
This shows:
- Link to GitHub Actions dashboard
- Expected status of each job
- What to look for in logs if failures occur

### Complete workflow (do both at once)
```bash
python pre_and_post_push.py
git push
python verify_after_push.py
```

## What GitHub Actions Checks

The CI/CD pipeline runs 4 jobs:

### 1. test (3.9, 3.10, 3.11)
- Runs all unit tests on 3 Python versions
- Generates coverage reports
- Status: Must pass (RED = block push)

### 2. sonarcloud
- Sends coverage to SonarCloud dashboard
- Status: Optional (yellow OK, continues even if fails)

### 3. notify
- Final status notification
- Status: Always OK (informational only)

## If Tests Fail Locally

```bash
# Run tests with details
pytest tests/test_security.py -v

# Check Python syntax on specific file
python -m py_compile backend/filename.py

# Run with coverage report
pytest tests/test_security.py --cov=backend --cov-report=html
open htmlcov/index.html  # View coverage in browser
```

## If GitHub Actions Fails

1. Check the workflow page:
   https://github.com/ericfunman/boursicotor/actions

2. Click on the failed job to see logs

3. Common issues:
   - **exit code 3**: Dependency issue, check installation
   - **ModuleNotFoundError**: Missing import, check requirements
   - **FAILED pytest**: Test logic error

## Files Involved

- `verify_before_push.py` - Local pre-push validation
- `verify_after_push.py` - Post-push monitoring
- `pre_and_post_push.py` - Combined workflow
- `.github/workflows/ci-cd.yml` - GitHub Actions workflow
- `pytest.ini` - Test configuration
- `.gitignore` - Excludes temporary scripts

## Important Notes

⚠️ **Always run `verify_before_push.py` before pushing**

✓ The pre-push hook automatically runs verification (optional)

✓ GitHub Actions may take 1-2 minutes to complete

✓ Workflow status shows "Success" even if sonarcloud is optional

## Troubleshooting

### "exit code 3" on GitHub Actions
- Usually a dependency issue
- Check that shell: bash is specified for bash commands
- Verify python -m is used instead of just command name

### Tests pass locally but fail on GitHub
- Dependency differences between local and CI environment
- Check Python version compatibility
- Run pytest with same flags as CI/CD

### Pre-push hook not running
- Ensure `.git/hooks/pre-push` is executable
- Or use `git push --no-verify` to bypass (not recommended)

## Support

Run any of these scripts with Python 3.9+ on Windows, macOS, or Linux.

All scripts are Windows-compatible (no emoji/special characters).
