
@echo off
:menu
echo.
echo Select an option:
echo 1. Run System
echo 2. View Database
echo 3. Exit
set /p choice=Enter your choice (1, 2, or 3): 

if "%choice%"=="1" (
    REM Check if Python is installed
    python --version >nul 2>&1
    IF ERRORLEVEL 1 (
        echo Python is not installed. Please install Python first.
        pause
        exit /b 1
    )

    REM Check for virtual environment
    IF EXIST venv\Scripts\activate.bat (
        call venv\Scripts\activate.bat
        echo Activated virtual environment.
    ) ELSE (
        echo No virtual environment found. Creating one...
        python -m venv venv
        IF EXIST venv\Scripts\activate.bat (
            call venv\Scripts\activate.bat
            echo Virtual environment created and activated.
        ) ELSE (
            echo Failed to create virtual environment.
            pause
            exit /b 1
        )
    )

    REM Check if requirements are installed
    python -m pip show flask >nul 2>&1
    IF ERRORLEVEL 1 (
        echo Installing requirements from requirements.txt...
        python -m pip install -r requirements.txt
    ) ELSE (
        echo Requirements already installed.
    )

    REM Start Flask app
    python run.py
    goto menu
) else if "%choice%"=="2" (
    REM Check for virtual environment
    IF EXIST venv\Scripts\activate.bat (
        call venv\Scripts\activate.bat
        echo Activated virtual environment.
    ) ELSE (
        echo No virtual environment found. Creating one...
        python -m venv venv
        IF EXIST venv\Scripts\activate.bat (
            call venv\Scripts\activate.bat
            echo Virtual environment created and activated.
        ) ELSE (
            echo Failed to create virtual environment.
            pause
            exit /b 1
        )
    )

    REM Run view_db.py
    python view_db.py
    goto menu
) else if "%choice%"=="3" (
    echo Exiting...
    exit /b 0
) else (
    echo Invalid choice. Please try again.
    goto menu
)
