param()

$ErrorActionPreference = "Stop"

$Root = Split-Path -Parent $PSScriptRoot
Set-Location $Root

Write-Host ""
Write-Host "============================================================"
Write-Host " PixelOrchestrator - Project Status"
Write-Host "============================================================"

Write-Host ""
Write-Host "===== GIT ====="

$branch = git branch --show-current
$commit = git log -1 --format="%h %s"
$status = @(git status --short)

Write-Host "Branch : $branch"
Write-Host "Commit : $commit"

if ($status.Count -eq 0) {
    Write-Host "[PASS] Working tree clean"
} else {
    Write-Host "[INFO] Working tree has $($status.Count) change(s):"
    $status | ForEach-Object {
        Write-Host "       $_"
    }
}

Write-Host ""
Write-Host "===== CONTINUITY FILES ====="

$requiredFiles = @(
    ".\PROJECT_STATE.md",
    ".\PHASE_PLAN.md",
    ".\PROJECT_INSTRUCTIONS.md"
)

foreach ($file in $requiredFiles) {
    if (Test-Path $file -PathType Leaf) {
        Write-Host "[PASS] $file"
    } else {
        Write-Host "[FAIL] Missing: $file"
    }
}

Write-Host ""
Write-Host "===== CURRENT STATE ====="

if (Test-Path ".\PROJECT_STATE.md") {
    $state = Get-Content ".\PROJECT_STATE.md"

    $phaseLines = $state |
        Select-String -Pattern '^Phase [0-9]+-[A-Z0-9-]+ (conclusion|closure|status):'

    if ($phaseLines) {
        Write-Host "Latest checkpoint:"
        $phaseLines | Select-Object -Last 1 |
            ForEach-Object { Write-Host "  $($_.Line)" }
    }

    $nextIndex = -1

    for ($i = 0; $i -lt $state.Count; $i++) {
        if ($state[$i] -match '^Next:\s*$') {
            $nextIndex = $i
        }
    }

    if ($nextIndex -ge 0) {
        Write-Host ""
        Write-Host "Next:"

        for ($i = $nextIndex + 1; $i -lt $state.Count; $i++) {
            $line = $state[$i]

            if ($line -match '^\S') {
                break
            }

            if (-not [string]::IsNullOrWhiteSpace($line)) {
                Write-Host "  $($line.Trim())"
            }
        }
    }
}

Write-Host ""
Write-Host "===== TOOLS ====="

if (Test-Path ".\tools") {
    Get-ChildItem ".\tools" -File |
        Sort-Object Name |
        ForEach-Object {
            Write-Host "  $($_.Name)"
        }
} else {
    Write-Host "[INFO] tools directory missing"
}

Write-Host ""
Write-Host "===== STATUS COMPLETE ====="
Write-Host ""
Write-Host "This utility is read-only."
