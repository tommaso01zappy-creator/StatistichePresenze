@echo off
cd /d "%~dp0"
python -m pip install -r requirements.txt
python -m pip install pyinstaller
pyinstaller --noconsole --name BaseballPresenze main.py
echo.
echo EXE creato in dist\BaseballPresenze\
pause
