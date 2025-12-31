@echo off
echo ========================================
echo Research Assistant - Final Build
echo ========================================
echo.
echo Building the conversational GUI version...
echo.

echo [1/2] Testing the app first...
python gui_app_final.py --version 2>nul
if %errorlevel% neq 0 (
    echo Testing app... Press Ctrl+C after you see the window
    timeout /t 3 >nul
)
echo.

echo [2/2] Building executable...
pyinstaller build_app_lite.spec --clean
if %errorlevel% neq 0 (
    echo ERROR: Build failed
    pause
    exit /b 1
)
echo.

echo ========================================
echo SUCCESS!
echo ========================================
echo.
echo Executable created at: dist\ResearchAssistant.exe
echo.
echo File size:
dir dist\ResearchAssistant.exe | find "ResearchAssistant.exe"
echo.
echo You can now:
echo 1. Test it: cd dist ^&^& ResearchAssistant.exe
echo 2. Share it: Just send the ResearchAssistant.exe file
echo.
echo Users will need to:
echo - Click Settings to enter their API keys
echo - Start chatting with the AI to begin research
echo.
pause
