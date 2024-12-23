@echo off
echo Starting YouTube Scraper...
cd /d "%~dp0"
start /b pythonw youtube_scraper.py
echo Scraper started in background. Check youtube_scraper.log for details.
pause
