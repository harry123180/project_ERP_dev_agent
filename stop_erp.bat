@echo off
echo ========================================
echo Stopping ERP System...
echo ========================================

echo Stopping Backend Server...
taskkill /FI "WindowTitle eq ERP Backend*" /T /F 2>nul
if %errorlevel% == 0 (
    echo Backend stopped successfully.
) else (
    echo Backend was not running.
)

echo Stopping Frontend Server...
taskkill /FI "WindowTitle eq ERP Frontend*" /T /F 2>nul
if %errorlevel% == 0 (
    echo Frontend stopped successfully.
) else (
    echo Frontend was not running.
)

:: 也停止任何 node 和 python 進程（可選）
:: taskkill /IM node.exe /F 2>nul
:: taskkill /IM python.exe /F 2>nul

echo.
echo ========================================
echo ERP System stopped.
echo ========================================
echo Press any key to exit...
pause > nul