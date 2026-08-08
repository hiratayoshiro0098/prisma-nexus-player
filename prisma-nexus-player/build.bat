@echo off
echo ========================================
echo Building PrismaNexus Player
echo ========================================
echo.

REM Check if PyInstaller is installed
pip show pyinstaller >nul 2>&1
if errorlevel 1 (
    echo Installing PyInstaller...
    pip install pyinstaller
    echo.
)

echo Building executable...
python build.py

echo.
echo Done! Check the 'release' folder.
pause