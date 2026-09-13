@echo off
cd /d "%~dp0"
py -3 full_install.py
if errorlevel 1 pause

