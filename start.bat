@echo off
chcp 65001 >nul
set PYTHONIOENCODING=utf-8

echo.
echo =========================================
echo   FoodResQ AI - Starting Server
echo =========================================
echo.

IF EXIST "venv\Scripts\activate.bat" (
    echo Activating virtual environment...
    call venv\Scripts\activate.bat
)

echo.
echo Starting FoodResQ AI server...
echo -----------------------------------------
echo   Frontend App:   http://localhost:8000
echo   Swagger UI:     http://localhost:8000/docs
echo -----------------------------------------
echo Press Ctrl+C to stop the server.
echo.

python -m uvicorn backend.main:app --host 127.0.0.1 --port 8000 --reload

pause
