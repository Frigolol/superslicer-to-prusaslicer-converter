@echo off
rem Build dist\ss2ps.exe (requires: pip install pyinstaller)
cd /d "%~dp0"
python -m PyInstaller --onefile --windowed --name ss2ps --clean --noconfirm ss2ps.py
