# final_fix.ps1 – PySide6 DLL Error Fix (Windows)
Write-Host "======================================" -ForegroundColor Cyan
Write-Host "  Pixel Orchestrator – Final Fix" -ForegroundColor Yellow
Write-Host "======================================" -ForegroundColor Cyan

$projectPath = "C:\Users\AndroFixX\Desktop\PixelOrchestrator_Enterprise"
cd $projectPath

# 1. Purani environment hatao
Write-Host "`n[1/5] Removing old environment (if any)..." -ForegroundColor Yellow
Remove-Item -Recurse -Force venv -ErrorAction SilentlyContinue
Remove-Item -Recurse -Force pixel_env -ErrorAction SilentlyContinue

# 2. Naya virtual environment banayo
Write-Host "[2/5] Creating fresh Python virtual environment..." -ForegroundColor Yellow
python -m venv venv
.\venv\Scripts\Activate.ps1

# 3. PySide6 ka stable version install karo (6.5.0)
Write-Host "[3/5] Installing PySide6 6.5.0 (stable)..." -ForegroundColor Yellow
pip install --upgrade pip
pip install PySide6==6.5.0

# 4. DLL directory wala hack add karo main_launcher.py mein
Write-Host "[4/5] Patching main_launcher.py with DLL directory fix..." -ForegroundColor Yellow
$launcherContent = Get-Content main_launcher.py -Raw
if ($launcherContent -notmatch "add_dll_directory") {
    $dllCode = @'
import os
import sys
if sys.platform == 'win32':
    venv_dll = os.path.join(os.path.dirname(sys.executable), 'Lib', 'site-packages', 'PySide6')
    if os.path.exists(venv_dll):
        os.add_dll_directory(venv_dll)
'@
    $newContent = $dllCode + "`n" + $launcherContent
    Set-Content -Path main_launcher.py -Value $newContent -Encoding utf8
    Write-Host "     Patched!" -ForegroundColor Green
}

# 5. Test import
Write-Host "[5/5] Testing PySide6 import..." -ForegroundColor Yellow
$testResult = python -c "from PySide6.QtWidgets import QApplication; print('SUCCESS')" 2>&1
if ($testResult -match "SUCCESS") {
    Write-Host "     ✅ PySide6 is working!" -ForegroundColor Green
    Write-Host "`nLaunching Pixel Orchestrator..." -ForegroundColor Cyan
    python main_launcher.py
} else {
    Write-Host "     ❌ Still failing. Trying alternative..." -ForegroundColor Red
    # Fallback: use conda if available
    if (Get-Command conda -ErrorAction SilentlyContinue) {
        Write-Host "     Conda found. Creating conda environment..." -ForegroundColor Yellow
        conda create -n pixel_fix python=3.10 -y
        conda activate pixel_fix
        conda install -c conda-forge pyside6 -y
        python main_launcher.py
    } else {
        Write-Host "     ERROR: Please install Visual C++ Redistributable from:" -ForegroundColor Red
        Write-Host "     https://aka.ms/vs/17/release/vc_redist.x64.exe" -ForegroundColor Yellow
        Write-Host "     Then restart your PC and run this script again." -ForegroundColor Yellow
    }
}

pause