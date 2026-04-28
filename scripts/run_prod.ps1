param(
    [string]$Host = "0.0.0.0",
    [int]$Port = 8000
)

$ErrorActionPreference = "Stop"

$projectRoot = Split-Path -Parent $PSScriptRoot
$venvPython = Join-Path $projectRoot ".venv\Scripts\python.exe"

if (-not (Test-Path $venvPython)) {
    throw ".venv is missing. Run .\scripts\setup_venv.ps1 first."
}

Set-Location $projectRoot
& $venvPython -m uvicorn app.main:app --host $Host --port $Port
