@echo off
REM ========================================
REM  Boursicotor - Stop Script
REM  Arrete tous les processus Streamlit
REM ========================================

echo.
echo ========================================
echo  Arret de Boursicotor
echo ========================================
echo.

REM Tuer tous les processus Streamlit
echo Arret des processus Streamlit...
taskkill /F /IM streamlit.exe 2>nul

if %errorlevel%==0 (
    echo.
    echo [OK] Boursicotor arrete avec succes !
) else (
    echo.
    echo [INFO] Aucun processus Streamlit en cours
)

echo.
pause
