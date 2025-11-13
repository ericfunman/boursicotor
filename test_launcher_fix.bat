@echo off
REM ========================================
REM  Test: Streamlit Launcher
REM ========================================

echo.
echo Testing Streamlit launcher fix...
echo.

cd /d "%~dp0"

echo [1] Activating virtual environment...
call venv\Scripts\activate.bat
if errorlevel 1 (
    echo ERROR: Could not activate venv
    pause
    exit /b 1
)

echo [OK] venv activated

echo [2] Testing streamlit via python -m...
python -m streamlit --version
if errorlevel 1 (
    echo ERROR: streamlit not working
    pause
    exit /b 1
)

echo [OK] Streamlit module working

echo.
echo ========================================
echo SUCCESS: Launcher fix verified!
echo ========================================
echo.
echo You can now run: startBoursicotor.bat
echo.
pause
