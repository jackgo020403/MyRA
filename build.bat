@echo off
echo ========================================
echo Research Assistant - Build Script
echo ========================================
echo.

echo [1/3] Installing GUI dependencies...
pip install -r requirements-gui.txt
if %errorlevel% neq 0 (
    echo ERROR: Failed to install dependencies
    pause
    exit /b 1
)
echo.

echo [2/3] Building executable with PyInstaller...
pyinstaller build_app.spec --clean
if %errorlevel% neq 0 (
    echo ERROR: Build failed
    pause
    exit /b 1
)
echo.

echo [3/3] Build complete!
echo.
echo ========================================
echo SUCCESS!
echo ========================================
echo.
echo Executable location: dist\ResearchAssistant.exe
echo.
echo You can now run the application by double-clicking:
echo   dist\ResearchAssistant.exe
echo.
echo To distribute, share the dist\ResearchAssistant.exe file.
echo Users will need to configure API keys on first run.
echo.
pause
