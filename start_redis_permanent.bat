@echo off
title Redis Server - Boursicotor
echo ========================================
echo  Redis Server - Demarrage
echo ========================================
echo.
echo Redis se lance...
echo NE FERMEZ PAS CETTE FENETRE !
echo.
cd /d C:\redis
redis-server.exe
echo.
echo Redis s'est arrete.
pause
