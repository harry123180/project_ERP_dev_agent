@echo off
echo Adding firewall rules for ERP system network access...

rem Add inbound rule for backend port 5000
netsh advfirewall firewall add rule name="ERP Backend Port 5000" dir=in action=allow protocol=TCP localport=5000

rem Add inbound rule for frontend ports 5173-5178
netsh advfirewall firewall add rule name="ERP Frontend Ports 5173-5178" dir=in action=allow protocol=TCP localport=5173-5178

rem Show firewall rules
netsh advfirewall firewall show rule name="ERP Backend Port 5000"
netsh advfirewall firewall show rule name="ERP Frontend Ports 5173-5178"

echo.
echo Firewall rules added. Test network access now.
pause