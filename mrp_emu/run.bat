@echo off
cd /d "%~dp0"
rem Pick an interpreter that has unicorn/pygame/numpy installed.
set PY=python
python -c "import unicorn, pygame, numpy" >nul 2>nul
if not errorlevel 1 goto RUN
py -3.12 -c "import unicorn, pygame, numpy" >nul 2>nul
if not errorlevel 1 (
  set PY=py -3.12
  goto RUN
)
echo [!] Missing dependencies. Run: pip install -r requirements.txt
pause
exit /b 1
:RUN
%PY% run.py %*
pause
