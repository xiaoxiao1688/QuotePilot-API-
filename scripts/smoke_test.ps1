param(
    [int]$Port = 18080
)

$ErrorActionPreference = "Stop"

$projectRoot = Split-Path -Parent $PSScriptRoot
$venvPython = Join-Path $projectRoot ".venv\Scripts\python.exe"

if (-not (Test-Path $venvPython)) {
    throw ".venv is missing. Run .\scripts\setup_venv.ps1 first."
}

Set-Location $projectRoot
$process = Start-Process -FilePath $venvPython -ArgumentList "-m uvicorn app.main:app --host 127.0.0.1 --port $Port" -PassThru -WindowStyle Hidden

try {
    Start-Sleep -Seconds 4
    $response = Invoke-WebRequest -UseBasicParsing "http://127.0.0.1:$Port/api/v1/health"
    Write-Host $response.Content
}
finally {
    if ($process -and -not $process.HasExited) {
        Stop-Process -Id $process.Id -Force
    }
}
