@echo off

cd /d %~dp0

echo ==========================
echo Running Python script...
echo ==========================

py main.py

echo.
echo ==========================
echo Finished
echo ==========================

exit