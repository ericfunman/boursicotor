@echo off
REM Launch IB Gateway directly with API enabled (no IBC)

echo Lancement d'IB Gateway...

REM Set Java options to ensure API is writable
set "JAVA_OPTS=-Dsun.java2d.noddraw=true"

REM Launch IB Gateway directly
start "IB Gateway" "C:\Jts\ibgateway\1037\ibgateway.exe"

echo IB Gateway lance. Veuillez vous connecter manuellement.
echo Username: ericlapinasimu
echo Password: bouh806simu
echo Mode: Paper Trading
echo.
echo IMPORTANT: Verifiez que 'Read-Only API' est bien DECOCHE dans Settings > API
echo.
pause
