@echo off
echo Starting AI Job Portal...
echo ----------------------------------------------------
echo Attempting to start Java Spring Boot Backend...
echo ----------------------------------------------------

cd backend
call mvn spring-boot:run
if %errorlevel% equ 0 goto end

echo.
echo ----------------------------------------------------
echo [WARNING] Java/Maven build failed. 
echo Ensure Apache Maven is installed and in your PATH.
echo.
echo Falling back to Python Backend (server.py)...
echo ----------------------------------------------------
echo.
cd ..
".venv\Scripts\python.exe" server.py
pause

:end
pause
