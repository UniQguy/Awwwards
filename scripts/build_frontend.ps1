# Builds frontend production assets with Vite
$ErrorActionPreference = "Stop"
Write-Host "Building ELECTROCART production frontend assets with Vite..." -ForegroundColor Cyan
npm run build
if ($LASTEXITCODE -ne 0) {
    Write-Error "Vite build failed with exit code $LASTEXITCODE"
    exit $LASTEXITCODE
}
Write-Host "Vite production build succeeded." -ForegroundColor Green
