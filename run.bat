@echo off
title Smart Parking Desktop Application (INR Edition)
echo ========================================================
echo  Starting Smart Parking System (Cars, Bikes, Bicycles)
echo  Currency: Indian Rupees (INR)
echo ========================================================

where py >nul 2>&1
if %ERRORLEVEL% EQU 0 (
    py main.py
    goto end
)

where python >nul 2>&1
if %ERRORLEVEL% EQU 0 (
    python main.py
    goto end
)

if exist "%LOCALAPPDATA%\Programs\Python\Python314\python.exe" (
    "%LOCALAPPDATA%\Programs\Python\Python314\python.exe" main.py
    goto end
)

if exist "C:\Users\Harshit Choudhary\AppData\Local\Programs\Python\Python314\python.exe" (
    "C:\Users\Harshit Choudhary\AppData\Local\Programs\Python\Python314\python.exe" main.py
    goto end
)

echo [ERROR] Python was not found! Please ensure Python is installed and added to PATH.
pause

:end
