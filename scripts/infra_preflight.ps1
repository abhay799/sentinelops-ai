$ErrorActionPreference = "Continue"

Write-Host ""
Write-Host "====================================================" -ForegroundColor Cyan
Write-Host " SENTINELOPS AI - INFRASTRUCTURE PREFLIGHT" -ForegroundColor Cyan
Write-Host "====================================================" -ForegroundColor Cyan

$failed = $false


# ============================================================
# Helper functions
# ============================================================

function Pass {
    param([string]$Name)

    Write-Host "[PASS] $Name" -ForegroundColor Green
}


function Fail {
    param([string]$Name)

    Write-Host "[FAIL] $Name" -ForegroundColor Red
    $script:failed = $true
}


function Check-Command {
    param(
        [string]$Name,
        [string]$Command
    )

    $resolved = Get-Command $Command -ErrorAction SilentlyContinue

    if ($resolved) {
        Pass $Name
    }
    else {
        Fail $Name
    }
}


# ============================================================
# Resolve Helm
# ============================================================

$helmExe = $null

$helmCommand = Get-Command helm -ErrorAction SilentlyContinue

if ($helmCommand) {

    $helmExe = $helmCommand.Source
}
else {

    $helmCandidate = Get-ChildItem `
        "$env:LOCALAPPDATA\Microsoft\WinGet\Packages" `
        -Recurse `
        -Filter "helm.exe" `
        -File `
        -ErrorAction SilentlyContinue |
        Select-Object -First 1 -ExpandProperty FullName

    if ($helmCandidate) {
        $helmExe = $helmCandidate
    }
}


# ============================================================
# CLI tools
# ============================================================

Write-Host "`n[CLI Tools]" -ForegroundColor Yellow

Check-Command "Git" "git"
Check-Command "Docker" "docker"
Check-Command "kubectl" "kubectl"

if ($helmExe -and (Test-Path $helmExe)) {

    Pass "Helm"
    Write-Host "       $helmExe" -ForegroundColor DarkGray
}
else {

    Fail "Helm"
}

Check-Command "Node.js" "node"
Check-Command "npm" "npm"


# ============================================================
# Docker engine
# ============================================================

Write-Host "`n[Docker Engine]" -ForegroundColor Yellow

docker info *> $null
$dockerExitCode = $LASTEXITCODE

if ($dockerExitCode -eq 0) {
    Pass "Docker engine"
}
else {
    Fail "Docker engine"
}


# ============================================================
# Core containers
# ============================================================

Write-Host "`n[Core Containers]" -ForegroundColor Yellow

$containers = @(
    "sentinelops-postgres",
    "sentinelops-redis",
    "sentinelops-kafka",
    "sentinelops-prometheus",
    "sentinelops-grafana",
    "sentinelops-otel"
)

foreach ($container in $containers) {

    $status = docker inspect `
        -f "{{.State.Status}}" `
        $container 2>$null

    if ($status -eq "running") {
        Pass $container
    }
    else {
        Fail $container
    }
}


# ============================================================
# PostgreSQL
# ============================================================

Write-Host "`n[PostgreSQL]" -ForegroundColor Yellow

docker exec sentinelops-postgres `
    pg_isready `
    -U sentinelops `
    -d sentinelops *> $null

$postgresExitCode = $LASTEXITCODE

if ($postgresExitCode -eq 0) {
    Pass "PostgreSQL readiness"
}
else {
    Fail "PostgreSQL readiness"
}


# ============================================================
# Redis
# ============================================================

Write-Host "`n[Redis]" -ForegroundColor Yellow

$redisResult = docker exec sentinelops-redis redis-cli ping 2>$null

if ($redisResult -eq "PONG") {
    Pass "Redis connectivity"
}
else {
    Fail "Redis connectivity"
}


# ============================================================
# Kafka
# ============================================================

Write-Host "`n[Kafka]" -ForegroundColor Yellow

$topics = docker exec sentinelops-kafka `
    /opt/kafka/bin/kafka-topics.sh `
    --bootstrap-server localhost:9092 `
    --list 2>$null

$kafkaExitCode = $LASTEXITCODE

if (
    $kafkaExitCode -eq 0 -and
    ($topics | Select-String -SimpleMatch "sentinelops.telemetry.raw")
) {
    Pass "Kafka telemetry topic"
}
else {
    Fail "Kafka telemetry topic"
}


# ============================================================
# Prometheus
# ============================================================

Write-Host "`n[Prometheus]" -ForegroundColor Yellow

try {

    $prometheus = curl.exe `
        -fsS `
        http://localhost:9090/-/ready 2>$null

    $prometheusExitCode = $LASTEXITCODE

    if (
        $prometheusExitCode -eq 0 -and
        $prometheus -match "Ready"
    ) {
        Pass "Prometheus"
    }
    else {
        Fail "Prometheus"
    }
}
catch {

    Fail "Prometheus"
}


# ============================================================
# Grafana
# ============================================================

Write-Host "`n[Grafana]" -ForegroundColor Yellow

try {

    $grafana = Invoke-RestMethod `
        -Uri "http://localhost:3000/api/health" `
        -Method Get `
        -ErrorAction Stop

    if ($grafana.database -eq "ok") {
        Pass "Grafana"
    }
    else {
        Fail "Grafana"
    }
}
catch {

    Fail "Grafana"
}


# ============================================================
# OpenTelemetry
# ============================================================

Write-Host "`n[OpenTelemetry]" -ForegroundColor Yellow

$otelStatus = docker inspect `
    -f "{{.State.Status}}" `
    sentinelops-otel 2>$null

if ($otelStatus -eq "running") {
    Pass "OpenTelemetry Collector"
}
else {
    Fail "OpenTelemetry Collector"
}


# ============================================================
# Kubernetes
# ============================================================

Write-Host "`n[Kubernetes]" -ForegroundColor Yellow

$context = kubectl config current-context 2>$null

if ($context -eq "docker-desktop") {

    Pass "Kubernetes context"
}
else {

    Fail "Kubernetes context"
}


$readyNodes = kubectl get nodes `
    --no-headers 2>$null |
    Select-String "\sReady\s"

if ($readyNodes) {

    Pass "Kubernetes node"
}
else {

    Fail "Kubernetes node"
}


# ============================================================
# Kubernetes system pods
# ============================================================

$badSystemPods = kubectl get pods `
    -n kube-system `
    --no-headers 2>$null |
    Where-Object {
        $_ -notmatch "\sRunning\s" -and
        $_ -notmatch "\sCompleted\s"
    }

if (-not $badSystemPods) {

    Pass "Kubernetes system pods"
}
else {

    Fail "Kubernetes system pods"

    Write-Host "Unhealthy Kubernetes pods:" -ForegroundColor Red
    $badSystemPods | ForEach-Object {
        Write-Host "  $_" -ForegroundColor DarkRed
    }
}


# ============================================================
# Helm
# ============================================================

Write-Host "`n[Helm]" -ForegroundColor Yellow

if (-not $helmExe) {

    Fail "Helm executable"
}
elseif (-not (Test-Path $helmExe)) {

    Fail "Helm executable"
}
else {

    & $helmExe list -A *> $null

    $helmExitCode = $LASTEXITCODE

    if ($helmExitCode -eq 0) {

        Pass "Helm cluster connectivity"
    }
    else {

        Fail "Helm cluster connectivity"
    }
}


# ============================================================
# Final result
# ============================================================

Write-Host ""
Write-Host "===================================================="

if ($failed) {

    Write-Host "INFRASTRUCTURE PREFLIGHT: FAILED" -ForegroundColor Red
    Write-Host "====================================================" -ForegroundColor Red
    exit 1
}
else {

    Write-Host "INFRASTRUCTURE PREFLIGHT: PASSED" -ForegroundColor Green
    Write-Host "====================================================" -ForegroundColor Green
    exit 0
}