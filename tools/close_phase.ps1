param(
    [Parameter(Mandatory = $true)]
    [string]$Phase,

    [Parameter(Mandatory = $true)]
    [string]$Conclusion,

    [Parameter(Mandatory = $true)]
    [string]$Next,

    [switch]$Apply
)

$ErrorActionPreference = "Stop"

$Root = Split-Path -Parent $PSScriptRoot
Set-Location $Root

$files = @(
    ".\PROJECT_STATE.md",
    ".\PHASE_PLAN.md",
    ".\PROJECT_INSTRUCTIONS.md"
)

foreach ($file in $files) {
    if (-not (Test-Path $file -PathType Leaf)) {
        throw "Required continuity file is missing: $file"
    }
}

$block = @"

Phase $Phase closure:

    $Conclusion

Next:

    $Next

Closure recorded by tools/close_phase.ps1

Continuity rule:

    Preserve unrelated working-tree changes. Do not reopen completed
    checkpoints without new evidence.
"@

Write-Host ""
Write-Host "============================================================"
Write-Host " PixelOrchestrator - Phase Closure"
Write-Host "============================================================"
Write-Host ""
Write-Host "Phase      : $Phase"
Write-Host "Conclusion : $Conclusion"
Write-Host "Next       : $Next"
Write-Host ""

if (-not $Apply) {
    Write-Host "[PREVIEW] No files will be modified."
    Write-Host ""
    Write-Host "Would append to:"
    $files | ForEach-Object {
        Write-Host "  $_"
    }

    Write-Host ""
    Write-Host "Use -Apply only after verifying the closure information."
    exit 0
}

Write-Host "[APPLY] Append-only mode enabled."
Write-Host ""

foreach ($file in $files) {
    Add-Content -Path $file -Value $block -Encoding UTF8
    Write-Host "[PASS] Appended to $file"
}

Write-Host ""
Write-Host "===== CLOSURE COMPLETE ====="
Write-Host ""
Write-Host "No Git commands were executed."
Write-Host "No existing content was replaced or deleted."
Write-Host "Only append-only writes were performed."
