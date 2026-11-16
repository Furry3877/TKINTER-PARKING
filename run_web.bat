@echo off
title Smart Parking Web Application (INR Edition)
echo ========================================================
echo  Starting Smart Parking Web Server (INR Edition)
echo  Zone Segregation: Cars, Two-Wheelers, Bicycles
echo  Currency: Indian Rupees (INR)
echo ========================================================

:: Open browser automatically after 2 seconds
start "" cmd /c "timeout /t 2 /nobreak >nul & start http://localhost:5000"

where py >nul 2>&1
if %ERRORLEVEL% EQU 0 (
    py web_server.py 5000
    goto end
)

where python >nul 2>&1
if %ERRORLEVEL% EQU 0 (
    python web_server.py 5000
    goto end
)

if exist "%LOCALAPPDATA%\Programs\Python\Python314\python.exe" (
    "%LOCALAPPDATA%\Programs\Python\Python314\python.exe" web_server.py 5000
    goto end
)

if exist "C:\Users\Harshit Choudhary\AppData\Local\Programs\Python\Python314\python.exe" (
    "C:\Users\Harshit Choudhary\AppData\Local\Programs\Python\Python314\python.exe" web_server.py 5000
    goto end
)

echo [ERROR] Python was not found! Please ensure Python is installed and added to PATH.
pause

:end
