Param(
  [switch]$SkipFrontend,
  [switch]$SkipBackend
)

$ErrorActionPreference = "Stop"
$root = Split-Path -Parent $PSScriptRoot

Write-Host "== Jarvez E2E Smoke =="

if (-not $SkipBackend) {
  Write-Host "`n[1/4] Backend compile"
  Push-Location "$root\backend"
  .\.venv\Scripts\python.exe -m py_compile agent.py actions.py prompts.py voice_biometrics.py

  Write-Host "`n[2/4] Backend unit tests"
  .\.venv\Scripts\python.exe -m unittest test_actions.py test_memory_scope.py test_voice_biometrics.py
  Pop-Location
}

if (-not $SkipFrontend) {
  Write-Host "`n[3/4] Frontend check"
  Push-Location "$root\frontend"
  npm run check
  Pop-Location
}

Write-Host "`n[4/4] Manual acceptance checklist"
Write-Host "- Falar 3s e executar: 'cadastre meu perfil de voz como Guil'."
Write-Host "- Executar: 'verifique minha identidade por voz'."
Write-Host "- Se score medio/baixo, validar pedido de PIN (step-up)."
Write-Host "- Testar segredo sem auth (deve bloquear) e com auth (deve liberar)."
Write-Host "- Testar acao HA: 'ligue a luz ...' + confirmacao two-step."
Write-Host ""
Write-Host "Smoke finalizado."
