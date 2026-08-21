# PhishLens — install dependencies, train models, launch Streamlit
# Usage:
#   .\scripts\setup_and_run.ps1
#   .\scripts\setup_and_run.ps1 -SkipPipeline   # reuse existing trained models
#   .\scripts\setup_and_run.ps1 -SkipInstall    # skip pip install
#   .\scripts\setup_and_run.ps1 -RunTests       # run pytest before launching

param(
    [switch]$SkipInstall,
    [switch]$SkipPipeline,
    [switch]$RunTests
)

$ErrorActionPreference = "Stop"

$Root = Split-Path -Parent (Split-Path -Parent $MyInvocation.MyCommand.Path)
Set-Location $Root

Write-Host ""
Write-Host "========================================" -ForegroundColor Cyan
Write-Host "  PhishLens — setup & run" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host "Project root: $Root"
Write-Host ""

# --- Python ---
$python = Get-Command python -ErrorAction SilentlyContinue
if (-not $python) {
    Write-Host "ERROR: Python was not found on PATH. Install Python 3.10+ and try again." -ForegroundColor Red
    exit 1
}
Write-Host "[1/4] Python: $(python --version)" -ForegroundColor Green

# --- Virtual environment ---
$venvPath = Join-Path $Root ".venv"
$venvPython = Join-Path $venvPath "Scripts\python.exe"
$venvActivate = Join-Path $venvPath "Scripts\Activate.ps1"

if (-not (Test-Path $venvPython)) {
    Write-Host "[2/4] Creating virtual environment (.venv)..." -ForegroundColor Yellow
    python -m venv .venv
    if (-not (Test-Path $venvPython)) {
        Write-Host "ERROR: Failed to create .venv" -ForegroundColor Red
        exit 1
    }
} else {
    Write-Host "[2/4] Virtual environment already exists." -ForegroundColor Green
}

# --- Install dependencies ---
if ($SkipInstall) {
    Write-Host "[3/4] Skipping dependency install (-SkipInstall)." -ForegroundColor Yellow
} else {
    Write-Host "[3/4] Installing dependencies from requirements.txt..." -ForegroundColor Yellow
    & $venvPython -m pip install --upgrade pip
    & $venvPython -m pip install -r (Join-Path $Root "requirements.txt")
    if ($LASTEXITCODE -ne 0) {
        Write-Host "ERROR: pip install failed." -ForegroundColor Red
        exit 1
    }
    Write-Host "Dependencies installed." -ForegroundColor Green
}

# --- ML pipeline ---
$modelPath = Join-Path $Root "trained_models\ensemble.joblib"
$shouldRunPipeline = -not $SkipPipeline

if ($SkipPipeline -and -not (Test-Path $modelPath)) {
    Write-Host "No trained model found; ignoring -SkipPipeline and running the pipeline." -ForegroundColor Yellow
    $shouldRunPipeline = $true
}

if ($shouldRunPipeline) {
    Write-Host "[4/4] Running ML pipeline (download → train → evaluate → SHAP)..." -ForegroundColor Yellow
    & $venvPython (Join-Path $Root "scripts\run_pipeline.py")
    if ($LASTEXITCODE -ne 0) {
        Write-Host "ERROR: Pipeline failed." -ForegroundColor Red
        exit 1
    }
    Write-Host "Pipeline complete." -ForegroundColor Green
} else {
    Write-Host "[4/4] Skipping pipeline (-SkipPipeline); using existing trained models." -ForegroundColor Yellow
}

# --- Optional tests ---
if ($RunTests) {
    Write-Host "Running tests..." -ForegroundColor Yellow
    & $venvPython -m pytest (Join-Path $Root "tests") -v
    if ($LASTEXITCODE -ne 0) {
        Write-Host "ERROR: Tests failed." -ForegroundColor Red
        exit 1
    }
}

# --- Launch Streamlit ---
Write-Host ""
Write-Host "Launching Streamlit dashboard..." -ForegroundColor Cyan
Write-Host "Open the URL shown below in your browser (usually http://localhost:8501)" -ForegroundColor Cyan
Write-Host "Press Ctrl+C to stop the app." -ForegroundColor DarkGray
Write-Host ""

& $venvPython -m streamlit run (Join-Path $Root "streamlit_app.py")
exit $LASTEXITCODE
