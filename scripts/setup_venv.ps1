$ErrorActionPreference = "Stop"

$projectRoot = Split-Path -Parent $PSScriptRoot
$venvPython = Join-Path $projectRoot ".venv\Scripts\python.exe"
$envFile = Join-Path $projectRoot ".env"
$envExample = Join-Path $projectRoot ".env.example"
$localModelFile = Join-Path $projectRoot "models\quote_risk_model.joblib"
$localTextModelFile = Join-Path $projectRoot "models\quote_text_classifier.joblib"

function Resolve-PythonPath {
    $candidates = @(
        "C:\Users\admin\AppData\Local\Programs\Python\Python312\python.exe",
        "C:\Users\admin\AppData\Local\Programs\Python\Python311\python.exe",
        "C:\Python312\python.exe",
        "C:\Python311\python.exe"
    )

    foreach ($candidate in $candidates) {
        if (Test-Path $candidate) {
            return $candidate
        }
    }

    throw "No suitable Python interpreter was found. Install Python 3.11+ first."
}

if (-not (Test-Path $venvPython)) {
    $pythonPath = Resolve-PythonPath
    & $pythonPath -m venv (Join-Path $projectRoot ".venv")
}

& $venvPython -m pip install --upgrade pip
& $venvPython -m pip install -r (Join-Path $projectRoot "requirements.txt")

if (-not (Test-Path $localModelFile)) {
    & $venvPython (Join-Path $projectRoot "scripts\train_local_quote_risk_model.py")
}

if (-not (Test-Path $localTextModelFile)) {
    & $venvPython (Join-Path $projectRoot "scripts\train_local_text_model.py")
}

if (-not (Test-Path $envFile) -and (Test-Path $envExample)) {
    Copy-Item $envExample $envFile
}

Write-Host "Venv is ready at $venvPython"
