$ErrorActionPreference = "Stop"

$root = Split-Path -Parent $MyInvocation.MyCommand.Path | Split-Path -Parent
$bridge = Join-Path $root "references\whatsapp-mcp\whatsapp-bridge"

if (!(Test-Path $bridge)) {
  throw "Bridge nao encontrado em references\\whatsapp-mcp\\whatsapp-bridge."
}

$machinePath = [System.Environment]::GetEnvironmentVariable("Path", "Machine")
$userPath = [System.Environment]::GetEnvironmentVariable("Path", "User")
$env:Path = "$machinePath;$userPath"
$env:CGO_ENABLED = "1"

$host.UI.RawUI.WindowTitle = "Jarvez WhatsApp MCP"

Set-Location $bridge
$binary = Join-Path $bridge "whatsapp-client.exe"
if (!(Test-Path $binary)) {
  go build .
}

& $binary
