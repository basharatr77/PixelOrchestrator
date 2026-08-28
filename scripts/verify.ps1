param(
    [switch]$RequireClean
)

$ErrorActionPreference = "Stop"

Write-Host ""
Write-Host "============================================"
Write-Host " PixelOrchestrator - Project Verification"
Write-Host "============================================"
Write-Host ""

$root = Split-Path -Parent $PSScriptRoot
Set-Location $root

$failed = $false

function Run-Check {
    param(
        [string]$Name,
        [scriptblock]$Action
    )

    Write-Host ""
    Write-Host ">>> $Name"

    try {
        & $Action

        if ($LASTEXITCODE -ne 0) {
            throw "Command exited with code $LASTEXITCODE"
        }

        Write-Host "[PASS] $Name"
    }
    catch {
        Write-Host "[FAIL] $Name"
        Write-Host $_
        $script:failed = $true
    }
}

Write-Host "Repository: $root"

Write-Host ""
Write-Host ">>> Current Git revision"
git log -1 --oneline

Run-Check "Required project state files" {
    $required = @(
        "PROJECT_STATE.md",
        "PHASE_PLAN.md",
        "PROJECT_INSTRUCTIONS.md"
    )

    foreach ($file in $required) {
        if (-not (Test-Path ".\$file")) {
            throw "Missing required file: $file"
        }
    }
}

Write-Host ""
Write-Host ">>> Git working tree"

$status = @(git status --short)

if ($status.Count -eq 0) {
    Write-Host "[INFO] Working tree is clean."
}
else {
    Write-Host "[INFO] Working tree has changes:"
    $status | ForEach-Object { Write-Host "  $_" }

    if ($RequireClean) {
        $failed = $true
        Write-Host "[FAIL] Clean working tree required."
    }
    else {
        Write-Host "[PASS] Working tree inspection"
        Write-Host "[INFO] Use -RequireClean for strict checkpoint verification."
    }
}

Run-Check "Python compilation" {
    python -m compileall -q .\app .\tests

    if ($LASTEXITCODE -ne 0) {
        throw "compileall failed."
    }
}

Run-Check "Pytest suite" {
    python -m pytest -q

    if ($LASTEXITCODE -ne 0) {
        throw "pytest failed."
    }
}

Run-Check "Git diff check" {
    git diff --check

    if ($LASTEXITCODE -ne 0) {
        throw "git diff --check failed."
    }
}

Run-Check "Legacy device model audit" {
    $matches = Get-ChildItem .\app,.\tests -Recurse -File -Filter *.py -ErrorAction SilentlyContinue |
        Select-String -Pattern 'app\.agents\.device_agent\.device_model'

    if ($matches) {
        $matches | Format-Table -AutoSize
        throw "Legacy device_model reference detected."
    }
}

Run-Check "Legacy device.mode audit" {
    $matches = Get-ChildItem .\app,.\tests -Recurse -File -Filter *.py -ErrorAction SilentlyContinue |
        Select-String -Pattern '\.mode\b'

    if ($matches) {
        $matches | Format-Table -AutoSize
        throw "Potential legacy device.mode reference detected."
    }
}

Write-Host ""
Write-Host "============================================"

if ($failed) {
    Write-Host " VERIFICATION RESULT: FAIL"
    Write-Host "============================================"
    exit 1
}
else {
    Write-Host " VERIFICATION RESULT: PASS"
    Write-Host "============================================"
    exit 0
}
