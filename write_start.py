content = """$exe = 'C:\\Users\\yatyr\\workspace\\dwg2dxf\\libredwg-0.13.4-win64\\dwg2dxf.exe'
$freshDir = 'C:\\Users\\yatyr\\workspace\\dwg2dxf\\dxf_fresh'
$outDir = 'C:\\Users\\yatyr\\workspace\\dwg2dxf\\dxf_output'
$fixScript = 'C:\\Users\\yatyr\\workspace\\dwg2dxf\\fix_dxf.py'
$srcDir = 'C:\\Users\\yatyr\\workspace\\dwg2dxf\\secured-dwg\\103E11~1.26'

# Clean old files first (Force mode)
Remove-Item '$freshDir\\*.dxf' -Force -ErrorAction SilentlyContinue
Remove-Item '$outDir\\*.dxf' -Force -ErrorAction SilentlyContinue

New-Item -ItemType Directory -Force -Path $freshDir | Out-Null
New-Item -ItemType Directory -Force -Path $outDir | Out-Null

# Step 1: Convert DWG -> DXF with LibreDWG
$files = Get-ChildItem '$srcDir\\*.dwg'
$total = $files.Count
$convSuccess = 0
$convFailed = 0

Write-Host '=== Step 1: Convert DWG to DXF ===' -ForegroundColor Cyan
foreach ($f in $files) {
    $outfile = Join-Path $freshDir ($f.BaseName + '.dxf')

    Write-Host -NoNewline '  [$($convSuccess+$convFailed+1)/$total] $($f.Name) ... '

    $cmdline = 'cd /d "' + $freshDir + '" && "' + $exe + '" --as r2007 -y -o "' + $outfile + '" "' + $f.FullName + '"'
    $null = cmd /c $cmdline 2>$null

    if ($LASTEXITCODE -eq 0 -and (Test-Path $outfile)) {
        $sizeKB = [math]::Round((Get-Item $outfile).Length / 1KB, 1)
        Write-Host 'OK (${sizeKB} KB)' -ForegroundColor Green
        $convSuccess++
    } else {
        Write-Host 'FAILED' -ForegroundColor Red
        $convFailed++
    }
}

Write-Host 'Convert done. Success: $convSuccess, Failed: $convFailed' -ForegroundColor Cyan

# Step 2: Fix DXF (encoding + layer colors + codepage)
Write-Host ''
Write-Host '=== Step 2: Fix DXF encoding & layer colors ===' -ForegroundColor Cyan

$fixResult = python '$fixScript' 2>&1
if ($LASTEXITCODE -ne 0) {
    Write-Host '  fix_dxf.py failed!' -ForegroundColor Red
    Write-Host $fixResult
} else {
    Write-Host '  fix_dxf.py OK' -ForegroundColor Green
}

# Step 3: Copy results to dxf_output
Write-Host ''
Write-Host '=== Step 3: Copy to dxf_output ===' -ForegroundColor Cyan
$fixedFiles = Get-ChildItem '$freshDir\\*.dxf'
foreach ($f in $fixedFiles) {
    $dest = Join-Path $outDir $f.Name
    Copy-Item $f.FullName $dest -Force
    Write-Host '  $($f.Name)'
}

Write-Host ''
Write-Host '=== All Done ===' -ForegroundColor Green
Get-ChildItem $outDir -Filter *.dxf | Select-Object Name, @{N='SizeMB';E={[math]::Round($_.Length/1MB,2)}} | Format-Table

Write-Host 'Press any key to exit...'
$null = $Host.UI.RawUI.ReadKey('NoEcho,IncludeKeyDown')
"""

with open('C:\\Users\\yatyr\\workspace\\dwg2dxf\\start.ps1', 'w', encoding='utf-8') as f:
    f.write(content)
print('Done')
