@echo off
set "IBC_LAUNCHER=C:\IBC\start_gateway.bat"
echo Testing: %IBC_LAUNCHER%
if not exist "%IBC_LAUNCHER%" (
    echo INSIDE IF BLOCK - File NOT found
    pause
) else (
    echo INSIDE ELSE BLOCK - File found
    pause
)
echo After IF block
pause
