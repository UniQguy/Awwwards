# PowerShell Clean-Clone Reproducibility Audit Script for ELECTROCART
# Clones repository to a temporary workspace, provisions fresh venv, installs deps,
# builds frontend, runs migrations, catalog import, demo seed, and executes full test suite.

$ErrorActionPreference = "Stop"
$repoRoot = (Resolve-Path "$PSScriptRoot\..").Path
$tempBase = Join-Path $env:TEMP ("electrocart_clone_" + [System.Guid]::NewGuid().ToString().Substring(0,8))

Write-Host "=================================================================" -ForegroundColor Cyan
Write-Host "ELECTROCART CLEAN-CLONE REPRODUCIBILITY AUDIT" -ForegroundColor Cyan
Write-Host "Source Repository : $repoRoot"
Write-Host "Target Temp Dir   : $tempBase"
Write-Host "=================================================================" -ForegroundColor Cyan

try {
    # 1. Clone repository
    Write-Host "`n[1/7] Cloning local git repository to clean temp folder..." -ForegroundColor Yellow
    git clone $repoRoot $tempBase
    if ($LASTEXITCODE -ne 0) { throw "Git clone failed" }

    # 2. Create fresh virtual environment
    Write-Host "`n[2/7] Creating clean Python virtual environment..." -ForegroundColor Yellow
    python -m venv "$tempBase\.venv"
    $venvPy = "$tempBase\.venv\Scripts\python.exe"
    $venvPip = "$tempBase\.venv\Scripts\pip.exe"

    # 3. Install requirements
    Write-Host "`n[3/7] Installing dependencies into fresh venv..." -ForegroundColor Yellow
    & $venvPip install -r "$tempBase\requirements-dev.txt"
    if ($LASTEXITCODE -ne 0) { throw "pip install failed" }

    # 4. Prepare data and environment
    Write-Host "`n[4/7] Preparing .env configuration and data files..." -ForegroundColor Yellow
    Copy-Item "$tempBase\.env.example" "$tempBase\.env"
    
    # Configure required env vars in temporary .env
    $envContent = Get-Content "$tempBase\.env"
    $envContent = $envContent -replace '^SECRET_KEY=.*', 'SECRET_KEY=clean-clone-reproducibility-key-50-characters-long-minimum!'
    $envContent = $envContent -replace '^SELLER_STATE=.*', 'SELLER_STATE=Karnataka'
    $envContent = $envContent -replace '^DATABASE_URL=.*', "DATABASE_URL=sqlite:///$($tempBase.Replace('\', '/'))/clean_db.sqlite3"
    $envContent | Set-Content "$tempBase\.env"

    # Copy CSV dataset if present in source
    $srcCsv = "$repoRoot\data\electronics_product.csv"
    if (Test-Path $srcCsv) {
        New-Item -ItemType Directory -Force -Path "$tempBase\data" | Out-Null
        Copy-Item $srcCsv "$tempBase\data\electronics_product.csv"
        Write-Host "   -> Copied source CSV dataset to $tempBase\data\electronics_product.csv" -ForegroundColor Green
    }

    # 5. Build front-end assets if Node.js is present
    Write-Host "`n[5/7] Building frontend assets..." -ForegroundColor Yellow
    if (Get-Command npm -ErrorAction SilentlyContinue) {
        Push-Location $tempBase
        try {
            npm ci
            npm run build
            Write-Host "   -> Front-end build completed successfully." -ForegroundColor Green
        } finally {
            Pop-Location
        }
    } else {
        Write-Host "   -> Node/npm not available in path. Skipping Vite bundle build." -ForegroundColor Gray
    }

    # 6. Database migrations, import & seed
    Write-Host "`n[6/7] Running migrations, catalog import, and demo seeding..." -ForegroundColor Yellow
    Push-Location $tempBase
    try {
        & $venvPy manage.py migrate --no-input
        if ($LASTEXITCODE -ne 0) { throw "Database migration failed" }

        if (Test-Path "$tempBase\data\electronics_product.csv") {
            & $venvPy manage.py import_products --csv "$tempBase\data\electronics_product.csv"
            if ($LASTEXITCODE -ne 0) { throw "Catalog import failed" }
        }

        & $venvPy manage.py seed_demo
        if ($LASTEXITCODE -ne 0) { throw "Demo seeding failed" }

        & $venvPy manage.py check
        if ($LASTEXITCODE -ne 0) { throw "Django system check failed" }
    } finally {
        Pop-Location
    }

    # 7. Execute test suite
    Write-Host "`n[7/7] Running full test suite in clean clone..." -ForegroundColor Yellow
    Push-Location $tempBase
    try {
        & $venvPy manage.py test --no-input
        if ($LASTEXITCODE -ne 0) { throw "Clean clone test suite execution failed" }
    } finally {
        Pop-Location
    }

    Write-Host "`n=================================================================" -ForegroundColor Green
    Write-Host "SUCCESS: Clean-clone reproducibility check passed completely!" -ForegroundColor Green
    Write-Host "All dependencies, migrations, imports, checks, and tests green." -ForegroundColor Green
    Write-Host "=================================================================" -ForegroundColor Green

} catch {
    Write-Host "`n=================================================================" -ForegroundColor Red
    Write-Host "FAILURE: Clean clone check failed with error:" -ForegroundColor Red
    Write-Host $_.Exception.Message -ForegroundColor Red
    Write-Host "=================================================================" -ForegroundColor Red
    exit 1
} finally {
    # Cleanup temporary workspace
    Write-Host "`nCleaning up temporary workspace..." -ForegroundColor Gray
    try {
        Remove-Item -Recurse -Force $tempBase -ErrorAction SilentlyContinue
        Write-Host "Temporary workspace deleted." -ForegroundColor Gray
    } catch {
        Write-Host "Could not automatically remove $tempBase (files may be in use). Remove manually." -ForegroundColor Yellow
    }
}
