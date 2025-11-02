@echo off
setlocal enabledelayedexpansion

echo ========================================
echo   IBC (IB Controller) Installation
echo ========================================
echo.

REM Get script directory
set "SCRIPT_DIR=%~dp0"
if "%SCRIPT_DIR:~-1%"=="\" set "SCRIPT_DIR=%SCRIPT_DIR:~0,-1%"

REM Configuration
set "IBC_VERSION=3.20.0"
set "IBC_URL=https://github.com/IbcAlpha/IBC/releases/download/%IBC_VERSION%/IBCWin-%IBC_VERSION%.zip"
set "INSTALL_DIR=C:\IBC"
set "DOWNLOAD_FILE=%TEMP%\IBC.zip"
set "IB_GATEWAY_DIR=C:\Jts\ibgateway\1037"
set "CONFIG_FILE=%SCRIPT_DIR%\ibgateway_config.ini"

REM Check if IBC already installed
if exist "%INSTALL_DIR%\Scripts\StartIBC.bat" (
    echo [INFO] IBC is already installed at %INSTALL_DIR%
    choice /C YN /M "Do you want to reinstall"
    if errorlevel 2 goto :configure_only
    echo [INFO] Removing existing installation...
    rmdir /S /Q "%INSTALL_DIR%" 2>nul
)

REM Create installation directory
echo [1/5] Creating installation directory...
if not exist "%INSTALL_DIR%" mkdir "%INSTALL_DIR%"

REM Download IBC
echo [2/5] Downloading IBC %IBC_VERSION%...
powershell -Command "& {[Net.ServicePointManager]::SecurityProtocol = [Net.SecurityProtocolType]::Tls12; Invoke-WebRequest -Uri '%IBC_URL%' -OutFile '%DOWNLOAD_FILE%'}"
if errorlevel 1 (
    echo [ERROR] Failed to download IBC
    exit /b 1
)

REM Extract IBC
echo [3/5] Extracting IBC...
powershell -Command "Expand-Archive -Path '%DOWNLOAD_FILE%' -DestinationPath '%INSTALL_DIR%' -Force"
if errorlevel 1 (
    echo [ERROR] Failed to extract IBC
    del "%DOWNLOAD_FILE%" 2>nul
    exit /b 1
)

REM Cleanup download
del "%DOWNLOAD_FILE%" 2>nul

:configure_only
REM Read credentials from ibgateway_config.ini
echo [4/5] Configuring IBC with your credentials...

if not exist "%CONFIG_FILE%" (
    echo.
    echo [ERROR] Configuration file not found: %CONFIG_FILE%
    echo [ERROR] Please create ibgateway_config.ini first
    echo.
    pause
    exit /b 1
)

REM Parse config file
for /f "usebackq tokens=1,2 delims==" %%a in ("%CONFIG_FILE%") do (
    set "key=%%a"
    set "value=%%b"
    REM Remove leading/trailing spaces
    for /f "tokens=* delims= " %%x in ("!key!") do set "key=%%x"
    for /f "tokens=* delims= " %%x in ("!value!") do set "value=%%x"
    
    if "!key!"=="Username" set "IB_USERNAME=!value!"
    if "!key!"=="Password" set "IB_PASSWORD=!value!"
    if "!key!"=="TradingMode" set "IB_TRADING_MODE=!value!"
    if "!key!"=="Port" set "IB_PORT=!value!"
)

REM Validate credentials
if not defined IB_USERNAME (
    echo.
    echo [ERROR] Username not found in config file
    echo.
    pause
    exit /b 1
)
if not defined IB_PASSWORD (
    echo.
    echo [ERROR] Password not found in config file
    echo.
    pause
    exit /b 1
)

REM Create IBC configuration file
set "IBC_CONFIG=%INSTALL_DIR%\config.ini"
echo # IBC Configuration > "%IBC_CONFIG%"
echo # Generated automatically by install_ibc.bat >> "%IBC_CONFIG%"
echo. >> "%IBC_CONFIG%"
echo IbLoginId=%IB_USERNAME% >> "%IBC_CONFIG%"
echo IbPassword=%IB_PASSWORD% >> "%IBC_CONFIG%"
echo. >> "%IBC_CONFIG%"
echo # Trading mode: live or paper >> "%IBC_CONFIG%"
if /i "%IB_TRADING_MODE%"=="paper" (
    echo TradingMode=paper >> "%IBC_CONFIG%"
) else (
    echo TradingMode=live >> "%IBC_CONFIG%"
)
echo. >> "%IBC_CONFIG%"
echo # Gateway API port >> "%IBC_CONFIG%"
echo IbApiPort=%IB_PORT% >> "%IBC_CONFIG%"
echo. >> "%IBC_CONFIG%"
echo # Auto-close dialogs >> "%IBC_CONFIG%"
echo AcceptIncomingConnectionAction=accept >> "%IBC_CONFIG%"
echo AcceptNonBrokerageAccountWarningAction=yes >> "%IBC_CONFIG%"
echo IbAutoClosedown=no >> "%IBC_CONFIG%"
echo ClosedownAt= >> "%IBC_CONFIG%"
echo AllowBlindTrading=no >> "%IBC_CONFIG%"
echo DismissPasswordExpiryWarning=yes >> "%IBC_CONFIG%"
echo DismissNSEComplianceNotice=yes >> "%IBC_CONFIG%"
echo SaveTwsSettingsAt= >> "%IBC_CONFIG%"
echo IbDir= >> "%IBC_CONFIG%"
echo StoreSettingsOnServer=no >> "%IBC_CONFIG%"
echo MinimizeMainWindow=yes >> "%IBC_CONFIG%"
echo ExistingSessionDetectedAction=primary >> "%IBC_CONFIG%"
echo OverrideTwsApiPort=no >> "%IBC_CONFIG%"
echo ReadOnlyLogin=no >> "%IBC_CONFIG%"
echo ReadOnlyApi=no >> "%IBC_CONFIG%"
echo FIX=no >> "%IBC_CONFIG%"
echo IbAutoRestartTime= >> "%IBC_CONFIG%"
echo LogComponents= >> "%IBC_CONFIG%"

echo [SUCCESS] IBC configuration created at %IBC_CONFIG%

REM Create launcher script
echo [5/5] Creating IBC launcher script...
set "LAUNCHER=%INSTALL_DIR%\start_gateway.bat"
echo @echo off > "%LAUNCHER%"
echo REM IB Gateway Launcher with IBC >> "%LAUNCHER%"
echo. >> "%LAUNCHER%"
echo set "IBC_PATH=%INSTALL_DIR%" >> "%LAUNCHER%"
echo set "TWS_PATH=C:\Jts" >> "%LAUNCHER%"
echo set "CONFIG_PATH=%IBC_CONFIG%" >> "%LAUNCHER%"
echo. >> "%LAUNCHER%"
echo cd /d "%%IBC_PATH%%" >> "%LAUNCHER%"
echo start "" "%%IBC_PATH%%\Scripts\StartIBC.bat" 1037 /Gateway /TwsPath:%%TWS_PATH%% /Config:%%CONFIG_PATH%% >> "%LAUNCHER%"

echo.
echo ========================================
echo   Installation Complete!
echo ========================================
echo.
echo IBC installed at: %INSTALL_DIR%
echo Configuration file: %IBC_CONFIG%
echo Launcher script: %LAUNCHER%
echo.
echo [NEXT STEP] Update startBoursicotor.bat to use IBC
echo Replace the IB Gateway launch line with:
echo   call "%LAUNCHER%"
echo.
pause
