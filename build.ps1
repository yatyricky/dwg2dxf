# Build script: package gui.py into a standalone Windows application
# Output: build/DWG2DXF/  (contains DWG2DXF.exe + all runtime files)

$ErrorActionPreference = "Stop"

$appName = "DWG2DXF"
$scriptDir = Split-Path -Parent $MyInvocation.MyCommand.Definition
$buildDir = Join-Path $scriptDir "build"
$workDir = Join-Path $scriptDir "build_work"
$distDir = Join-Path $buildDir $appName

# Check LibreDWG exists
$libreDwgDir = Join-Path $scriptDir "libredwg-0.13.4-win64"
$libreDwgExe = Join-Path $libreDwgDir "dwg2dxf.exe"

if (-not (Test-Path $libreDwgExe)) {
    Write-Host "ERROR: LibreDWG not found at $libreDwgExe" -ForegroundColor Red
    Write-Host "Please download from:" -ForegroundColor Yellow
    Write-Host "  https://github.com/LibreDWG/libredwg/releases/download/0.13.4/libredwg-0.13.4-win64.zip"
    Write-Host "Then extract to: $libreDwgDir"
    exit 1
}

# Check PyInstaller
$pyi = Get-Command pyinstaller -ErrorAction SilentlyContinue
if (-not $pyi) {
    # Try common path
    $pyiPath = Join-Path $env:LOCALAPPDATA "Programs\Python\Python313\Scripts\pyinstaller.exe"
    if (-not (Test-Path $pyiPath)) {
        $pyiPath = Join-Path $env:APPDATA "Python\Python313\Scripts\pyinstaller.exe"
    }
    if (Test-Path $pyiPath) {
        $pyi = $pyiPath
    } else {
        Write-Host "Installing PyInstaller..."
        python -m pip install pyinstaller
        $pyi = "pyinstaller"
    }
} else {
    $pyi = "pyinstaller"
}

# Clean old build
Write-Host "Cleaning old build..." -ForegroundColor Cyan
if (Test-Path $buildDir) { Remove-Item -Recurse -Force $buildDir }
if (Test-Path $workDir) { Remove-Item -Recurse -Force $workDir }
if (Test-Path "$scriptDir\*.spec") { Remove-Item "$scriptDir\*.spec" -Force }

# Build
Write-Host "Building $appName..." -ForegroundColor Cyan
& $pyi `
    --name $appName `
    --windowed `
    --noconfirm `
    --add-data "tkinterdnd2;tkinterdnd2" `
    --add-data "libredwg-0.13.4-win64;libredwg-0.13.4-win64" `
    --distpath $buildDir `
    --workpath $workDir `
    --specpath $scriptDir `
    gui.py

if ($LASTEXITCODE -ne 0) {
    Write-Host "Build FAILED!" -ForegroundColor Red
    exit 1
}

# Cleanup
Remove-Item -Recurse -Force $workDir
Remove-Item "$scriptDir\*.spec" -Force

# Verify
$exe = Join-Path $distDir "$appName.exe"
if (Test-Path $exe) {
    $sizeMB = [math]::Round((Get-Item $exe).Length / 1MB, 2)
    Write-Host "`nBuild SUCCESS!" -ForegroundColor Green
    Write-Host "Executable: $exe ($sizeMB MB)"
    Write-Host "Distribution folder: $distDir"
    Write-Host "`nTo run: double-click $exe or run: & '$exe'"
} else {
    Write-Host "Build FAILED: executable not found" -ForegroundColor Red
    exit 1
}
