$ErrorActionPreference = "Stop"

$root = Split-Path -Parent $MyInvocation.MyCommand.Path
$backend = Join-Path $root "backend"
$frontend = Join-Path $root "frontend"
$venvActivate = Join-Path $backend ".venv\Scripts\Activate.ps1"

if (!(Test-Path $venvActivate)) {
  throw "Ambiente Python nao encontrado. Rode .\setup.ps1 primeiro."
}

$backendCommand = "Set-Location '$backend'; . '$venvActivate'; python agent.py dev"
$frontendCommand = "Set-Location '$frontend'; pnpm dev"

Start-Process powershell -ArgumentList "-NoExit", "-Command", $backendCommand
Start-Process powershell -ArgumentList "-NoExit", "-Command", $frontendCommand

Write-Host "Jarvez iniciado:"
Write-Host "- Janela 1: backend (LiveKit Agent)"
Write-Host "- Janela 2: frontend (Next.js)"

