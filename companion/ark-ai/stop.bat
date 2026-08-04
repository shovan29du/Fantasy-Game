@echo off
echo Stopping Ark_AI background process...
taskkill /f /im pythonw.exe >nul 2>&1
echo Done.
timeout /t 2 >nul
