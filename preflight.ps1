$ErrorActionPreference = "Stop"

Write-Host ""
Write-Host "===================================================" -ForegroundColor Cyan
Write-Host " SENTINELOPS AI - PHASE 0 PREFLIGHT" -ForegroundColor Cyan
Write-Host "===================================================" -ForegroundColor Cyan

$failed = $false

function Check-Pass {
    param(
        [string]$Name,
        [bool]$Condition
    )

    if ($Condition) {
        Write-Host "[PASS] $Name" -ForegroundColor Green
    }
    else {
        Write-Host "[FAIL] $Name" -ForegroundColor Red
        $script:failed = $true
    }
}

Write-Host "`n[Python Environment]" -ForegroundColor Yellow

Check-Pass "Virtual environment exists" (Test-Path ".venv")
Check-Pass "SentinelOps Python package exists" (Test-Path "src\sentinelops\__init__.py")
Check-Pass "pyproject.toml exists" (Test-Path "pyproject.toml")


Write-Host "`n[Configuration]" -ForegroundColor Yellow

$configFiles = @(
    "configs\app.yaml",
    "configs\services.yaml",
    "configs\telemetry.yaml",
    "configs\sentinelguard.yaml",
    "configs\failure_scenarios.yaml",
    "configs\evaluation.yaml",
    "configs\security.yaml"
)

foreach ($file in $configFiles) {
    Check-Pass $file (Test-Path $file)
}


Write-Host "`n[Contracts]" -ForegroundColor Yellow

$schemaFiles = @(
    "src\sentinelops\schemas\telemetry.py",
    "src\sentinelops\schemas\incident.py",
    "src\sentinelops\schemas\rca.py",
    "src\sentinelops\schemas\remediation.py"
)

foreach ($file in $schemaFiles) {
    Check-Pass $file (Test-Path $file)
}


Write-Host "`n[Security]" -ForegroundColor Yellow

Check-Pass ".env.example exists" (Test-Path ".env.example")
Check-Pass ".env exists locally" (Test-Path ".env")

$envIgnored = git check-ignore .env 2>$null
Check-Pass ".env ignored by Git" ($null -ne $envIgnored)


Write-Host "`n[Repository]" -ForegroundColor Yellow

Check-Pass ".gitignore exists" (Test-Path ".gitignore")
Check-Pass "Git repository initialized" (Test-Path ".git")


Write-Host "`n[Contract Tests]" -ForegroundColor Yellow

python -m pytest tests\test_contracts.py -q

$venvPython = Join-Path $PSScriptRoot ".venv\Scripts\python.exe"

if (-not (Test-Path $venvPython)) {
    Write-Host "[FAIL] SentinelOps virtual-environment Python not found" -ForegroundColor Red
    $failed = $true
}
else {
    Write-Host "[PASS] SentinelOps virtual-environment Python" -ForegroundColor Green

    & $venvPython -m pytest tests\test_contracts.py -q

    if ($LASTEXITCODE -eq 0) {
        Write-Host "[PASS] Contract tests" -ForegroundColor Green
    }
    else {
        Write-Host "[FAIL] Contract tests" -ForegroundColor Red
        $failed = $true
    }
}