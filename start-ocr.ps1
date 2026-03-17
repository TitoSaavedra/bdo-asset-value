param(
    [switch]$DryRun
)

$ErrorActionPreference = "Stop"

$repoRoot = Split-Path -Parent $MyInvocation.MyCommand.Path
$pythonExe = Join-Path $repoRoot ".venv\Scripts\python.exe"
$ocrEntry = Join-Path $repoRoot "python-ocr-worker\main.py"

$apiHost = if ($env:API_HOST) { $env:API_HOST } else { "127.0.0.1" }
$apiPort = if ($env:API_PORT) { $env:API_PORT } else { "8000" }
$apiBaseUrl = if ($env:API_BASE_URL) { $env:API_BASE_URL } else { "http://$apiHost`:$apiPort" }

if (-not (Test-Path $pythonExe)) {
    throw "Python virtual environment not found at $pythonExe"
}

if (-not (Test-Path $ocrEntry)) {
    throw "OCR entrypoint not found at $ocrEntry"
}

$ocrCommand = "Set-Location '$repoRoot'; `$env:API_HOST='$apiHost'; `$env:API_PORT='$apiPort'; `$env:API_BASE_URL='$apiBaseUrl'; & '$pythonExe' '$ocrEntry'"

Write-Host "Starting OCR worker (host)..."

if ($DryRun) {
    Write-Host "[DryRun] OCR command: $ocrCommand"
    exit 0
}

Start-Process -FilePath "pwsh" -ArgumentList @("-NoExit", "-Command", $ocrCommand) | Out-Null
Write-Host "Done. OCR worker terminal opened."
