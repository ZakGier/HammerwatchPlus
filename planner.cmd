@echo off
rem Double-click to open the class planner in your browser (same as: python -m planner).
cd /d "%~dp0"
where py >nul 2>nul
if %errorlevel%==0 (py -3 -m planner %*) else (python -m planner %*)
if errorlevel 1 pause
