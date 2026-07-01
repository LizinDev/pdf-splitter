# Builds a standalone PDFSplitter.exe (no Python needed to run it).
#
# Usage:  right-click > Run with PowerShell,  or:  powershell -File build.ps1
# Output: dist\PDFSplitter.exe

$ErrorActionPreference = "Stop"
Set-Location -Path $PSScriptRoot

Write-Host "Building PDFSplitter.exe ..." -ForegroundColor Cyan

python -m PyInstaller `
    --noconfirm `
    --clean `
    --onefile `
    --windowed `
    --name PDFSplitter `
    run_gui.pyw

if ($LASTEXITCODE -eq 0) {
    Write-Host "`nDone. Your file is at:" -ForegroundColor Green
    Write-Host "    $PSScriptRoot\dist\PDFSplitter.exe"
    Write-Host "Send that single file to your coworker."
} else {
    Write-Host "`nBuild failed (exit $LASTEXITCODE)." -ForegroundColor Red
}
