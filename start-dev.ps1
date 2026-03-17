param(
    [switch]$DryRun
)

$ErrorActionPreference = "Stop"

$repoRoot = Split-Path -Parent $MyInvocation.MyCommand.Path
$pythonExe = Join-Path $repoRoot ".venv\Scripts\python.exe"
$frontendDir = Join-Path $repoRoot "frontend-tauri"

if (-not (Test-Path $pythonExe)) {
    throw "Python virtual environment not found at $pythonExe"
}

if (-not (Test-Path $frontendDir)) {
    throw "Frontend Tauri directory not found at $frontendDir"
}

$backendCommand = "Set-Location '$repoRoot'; & '$pythonExe' run.py"
$frontendCommand = "Set-Location '$frontendDir'; pnpm tauri dev"

Write-Host "Starting backend (FastAPI + hotkeys)..."
Write-Host "Starting frontend (Tauri + Svelte)..."

if ($DryRun) {
    Write-Host "[DryRun] Backend command: $backendCommand"
    Write-Host "[DryRun] Frontend command: $frontendCommand"
    exit 0
}

Start-Process -FilePath "pwsh" -ArgumentList @("-NoExit", "-Command", $backendCommand) | Out-Null
Start-Process -FilePath "pwsh" -ArgumentList @("-NoExit", "-Command", $frontendCommand) | Out-Null

Write-Host "Done. Two terminals were opened."
