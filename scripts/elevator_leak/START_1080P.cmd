@echo off
setlocal
pushd "%~dp0\..\.."
python -u scripts\elevator_leak\produce_v2.py --version 3 --resolution 1080
set "renderExitCode=%ERRORLEVEL%"
popd
if not "%renderExitCode%"=="0" echo Render stopped. Run this launcher again to resume completed frames.
pause
exit /b %renderExitCode%
