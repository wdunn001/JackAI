# Run API + frontend from project root. Installs deps if missing. Ctrl+C kills both.

Set-Location $PSScriptRoot
$frontendPath = Join-Path $PSScriptRoot "frontend"

# --- Backend: ensure Poetry and deps installed ---
$poetry = Get-Command poetry -ErrorAction SilentlyContinue
if (-not $poetry) {
    Write-Host "Poetry not found. Installing Poetry..."
    (Invoke-WebRequest -Uri https://install.python-poetry.org -UseBasicParsing).Content | python -
    $env:Path = "$env:APPDATA\Python\Scripts;$env:Path"
    $poetry = Get-Command poetry -ErrorAction SilentlyContinue
    if (-not $poetry) {
        Write-Host "Error: Poetry install may have completed but is not in PATH. Restart the terminal or add $env:APPDATA\Python\Scripts to PATH." -ForegroundColor Red
        exit 1
    }
}
Write-Host "Using Poetry for backend..."
poetry install
# Scanner uses Playwright Chromium; ensure browsers are installed (idempotent, quick if already present)
poetry run playwright install chromium
if ($LASTEXITCODE -ne 0) {
    Write-Host "Warning: Playwright Chromium install failed. Scanner may fail. Run: poetry run playwright install" -ForegroundColor Yellow
}
$runApi = @("run", "jackai", "serve")
$apiExe = "poetry"

# --- Frontend: ensure deps installed ---
$nodeModules = Join-Path $frontendPath "node_modules"
if (-not (Test-Path $nodeModules)) {
    Write-Host "Installing frontend dependencies..."
    Set-Location $frontendPath
    npm install
    Set-Location $PSScriptRoot
}
$npm = Get-Command npm -ErrorAction SilentlyContinue
if (-not $npm) {
    Write-Host "Error: npm not found. Install Node.js and try again." -ForegroundColor Red
    exit 1
}

Write-Host "Starting API (port 8000) and frontend..."
$api = Start-Process -PassThru -NoNewWindow $apiExe -ArgumentList $runApi
Start-Sleep -Seconds 2
$front = Start-Process -PassThru -NoNewWindow -WorkingDirectory $frontendPath npm -ArgumentList "run", "dev"

try {
    Wait-Process -Id $api.Id, $front.Id -ErrorAction SilentlyContinue
} finally {
    Stop-Process -Id $api.Id, $front.Id -Force -ErrorAction SilentlyContinue
    Write-Host "Shut down."
}
