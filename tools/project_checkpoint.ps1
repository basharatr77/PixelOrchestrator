param(
    [switch]$RunTests
)

$ErrorActionPreference = "Continue"

$Root = Split-Path -Parent $PSScriptRoot
Set-Location $Root

Write-Host ""
Write-Host "============================================================"
Write-Host " PixelOrchestrator - Project Checkpoint Audit"
Write-Host "============================================================"

$failures = @()

function Test-RequiredFile {
    param([string]$Path)

    if (Test-Path $Path -PathType Leaf) {
        Write-Host "[PASS] $Path"
    } else {
        Write-Host "[FAIL] Missing: $Path"
        $script:failures += "Missing file: $Path"
    }
}

Write-Host ""
Write-Host "===== REQUIRED STATE FILES ====="

Test-RequiredFile ".\PROJECT_STATE.md"
Test-RequiredFile ".\PHASE_PLAN.md"
Test-RequiredFile ".\PROJECT_INSTRUCTIONS.md"

Write-Host ""
Write-Host "===== GIT ====="

$branch = git branch --show-current
$commit = git log -1 --format="%h %s"

Write-Host "Branch : $branch"
Write-Host "Commit : $commit"

$status = @(git status --short)

if ($status.Count -eq 0) {
    Write-Host "[PASS] Working tree clean"
} else {
    Write-Host "[INFO] Working tree has changes:"
    $status | ForEach-Object { Write-Host "       $_" }
}

Write-Host ""
Write-Host "===== STATE FILE HEAD ====="

if (Test-Path ".\PROJECT_STATE.md") {
    Get-Content ".\PROJECT_STATE.md" |
        Select-Object -First 35 |
        ForEach-Object { Write-Host $_ }
}

Write-Host ""
Write-Host "===== PHASE PLAN STATUS ====="

if (Test-Path ".\PHASE_PLAN.md") {
    Select-String -Path ".\PHASE_PLAN.md" `
        -Pattern '^\| (1–34|35|36|37|38|39|40|41|42|43|44|45|46|47|48|49|50) \|' |
        ForEach-Object { Write-Host $_.Line }
}

Write-Host ""
Write-Host "===== COMPILE CHECK ====="

python -m compileall -q .\app .\tests

if ($LASTEXITCODE -eq 0) {
    Write-Host "[PASS] Python compilation"
} else {
    Write-Host "[FAIL] Python compilation"
    $failures += "compileall failed"
}

if ($RunTests) {
    Write-Host ""
    Write-Host "===== TEST SUITE ====="

    python -m pytest -q

    if ($LASTEXITCODE -eq 0) {
        Write-Host "[PASS] pytest"
    } else {
        Write-Host "[FAIL] pytest"
        $failures += "pytest failed"
    }
} else {
    Write-Host ""
    Write-Host "===== TEST SUITE ====="
    Write-Host "[SKIP] Full pytest not requested."
    Write-Host "       Run with: .\tools\project_checkpoint.ps1 -RunTests"
}

Write-Host ""
Write-Host "===== DIFF CHECK ====="

git diff --check

if ($LASTEXITCODE -eq 0) {
    Write-Host "[PASS] git diff --check"
} else {
    Write-Host "[FAIL] git diff --check"
    $failures += "git diff --check failed"
}

Write-Host ""
Write-Host "===== CHECKPOINT RESULT ====="

if ($failures.Count -eq 0) {
    Write-Host "[PASS] Checkpoint audit completed without detected failures."
} else {
    Write-Host "[FAIL] Checkpoint audit detected:"
    $failures | ForEach-Object {
        Write-Host "       - $_"
    }
    exit 1
}

Write-Host ""
Write-Host "NOTE:"
Write-Host "This script is read-only with respect to project state."
Write-Host "It does NOT modify PROJECT_STATE.md or PHASE_PLAN.md."
Write-Host "Phase completion still requires architectural verification and an explicit checkpoint update."
