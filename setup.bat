@echo off
echo ================================================================================
echo RA ORCHESTRATOR - Automated Setup (Windows)
echo ================================================================================
echo.

echo [1/5] Checking Python installation...
python --version
if errorlevel 1 (
    echo ERROR: Python not found. Please install Python 3.8 or higher.
    pause
    exit /b 1
)
echo.

echo [2/5] Creating virtual environment...
python -m venv venv
if errorlevel 1 (
    echo ERROR: Failed to create virtual environment.
    pause
    exit /b 1
)
echo Virtual environment created.
echo.

echo [3/5] Activating virtual environment...
call venv\Scripts\activate
echo.

echo [4/5] Installing dependencies...
pip install -r requirements.txt
if errorlevel 1 (
    echo ERROR: Failed to install dependencies.
    pause
    exit /b 1
)
echo Dependencies installed.
echo.

echo [5/5] Checking for .env file...
if not exist .env (
    echo WARNING: .env file not found.
    echo Creating .env from template...
    copy .env.example .env
    echo.
    echo IMPORTANT: Edit .env and add your ANTHROPIC_API_KEY
    echo.
)
echo.

echo ================================================================================
echo Setup complete!
echo ================================================================================
echo.
echo Next steps:
echo   1. Edit .env file and add your Anthropic API key
echo   2. Run validation: python validate_setup.py
echo   3. Run the tool: python -m ra_orchestrator.main
echo.
echo Press any key to exit...
pause >nul
