$ErrorActionPreference = "Stop"

$root = Split-Path -Parent $MyInvocation.MyCommand.Path
$backend = Join-Path $root "backend"
$frontend = Join-Path $root "frontend"
$venvPath = Join-Path $backend ".venv"
$venvPython = Join-Path $venvPath "Scripts\python.exe"

Write-Host "Configurando backend..."
if (!(Test-Path $venvPython)) {
  python -m venv $venvPath
}

& $venvPython -m pip install --upgrade pip
& $venvPython -m pip install -r (Join-Path $backend "requirements.txt")

if (!(Test-Path (Join-Path $backend ".env"))) {
  Copy-Item (Join-Path $backend ".env.example") (Join-Path $backend ".env")
  Write-Host "Arquivo backend/.env criado a partir de .env.example"
}

Write-Host "Configurando frontend..."
if (!(Test-Path (Join-Path $frontend ".env.local"))) {
  Copy-Item (Join-Path $frontend ".env.example") (Join-Path $frontend ".env.local")
  Write-Host "Arquivo frontend/.env.local criado a partir de .env.example"
}

pnpm install --dir $frontend

Write-Host "Setup concluido."

