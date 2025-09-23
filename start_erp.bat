@echo off
echo ========================================
echo Starting ERP System...
echo ========================================

:: 啟動後端
echo [1/2] Starting Backend Server...
start "ERP Backend" cmd /k "cd /d %~dp0backend && python app.py"

:: 等待後端啟動
echo Waiting for backend to start...
timeout /t 5 /nobreak > nul

:: 啟動前端
echo [2/2] Starting Frontend Server...
start "ERP Frontend" cmd /k "cd /d %~dp0frontend && npm run dev"

echo.
echo ========================================
echo ERP System is starting...
echo ========================================
echo Backend:  http://localhost:5000
echo Frontend: http://localhost:5174
echo.
echo Press any key to exit this window...
pause > nul