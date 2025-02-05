@echo off

cd /d "%~dp0"

if not exist .venv (
    echo Виртуальное окружение не найдено. Создаю .venv...
    python -m venv .venv
)

call .venv\Scripts\activate.bat

if exist requirements.txt (
    echo Устанавливаю зависимости из requirements.txt...
    pip install -r requirements.txt
) else (
    echo Файл requirements.txt не найден!
)

echo Окружение настроено.
pause