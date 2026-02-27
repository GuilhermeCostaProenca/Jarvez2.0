@echo off
setlocal

set "ROOT=%~dp0"
powershell -ExecutionPolicy Bypass -NoProfile -File "%ROOT%start-dev.ps1"

if errorlevel 1 (
  echo.
  echo Falha ao iniciar o Jarvez. Rode setup.ps1 e confira os .env.
  pause
)
