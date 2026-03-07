$ErrorActionPreference = "Stop"

$root = Split-Path -Parent $MyInvocation.MyCommand.Path
$backend = Join-Path $root "backend"
$frontend = Join-Path $root "frontend"
$venvActivate = Join-Path $backend ".venv\Scripts\Activate.ps1"

if (!(Test-Path $venvActivate)) {
  throw "Ambiente Python nao encontrado. Rode .\setup.ps1 primeiro."
}

$backendCommand = "Set-Location '$backend'; . '$venvActivate'; python agent.py dev"

$frontendRunCmd = $null
if (Get-Command pnpm -ErrorAction SilentlyContinue) {
  $frontendRunCmd = "if (Test-Path '.next') { cmd /c rmdir /s /q .next }; pnpm dev"
}
elseif (Get-Command npm -ErrorAction SilentlyContinue) {
  $frontendRunCmd = "if (Test-Path '.next') { cmd /c rmdir /s /q .next }; npm run dev"
}
else {
  throw "Nem pnpm nem npm foram encontrados no PATH."
}

$frontendCommand = "Set-Location '$frontend'; $frontendRunCmd"

Start-Process powershell -ArgumentList "-NoExit", "-Command", $backendCommand
Start-Process powershell -ArgumentList "-NoExit", "-Command", $frontendCommand

Write-Host "Jarvez iniciado:"
Write-Host "- Janela 1: backend (LiveKit Agent)"
Write-Host "- Janela 2: frontend (Next.js via $frontendRunCmd)"
