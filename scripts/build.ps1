param([switch]$Clean)

$ErrorActionPreference = "Stop"

if ($Clean) {
    Remove-Item -Recurse -Force -ErrorAction SilentlyContinue build, dist
}

Write-Host "Running tests..." -ForegroundColor Cyan
python -m pytest tests/ --tb=short -q --ignore=tests/ui
if ($LASTEXITCODE -ne 0) { throw "Tests failed" }

Write-Host "Running ruff..." -ForegroundColor Cyan
python -m ruff check src/
if ($LASTEXITCODE -ne 0) { throw "Ruff check failed" }

Write-Host "Building with PyInstaller..." -ForegroundColor Cyan
pyinstaller --clean scripts/uniqoremote.spec

Write-Host "Copying FFmpeg..." -ForegroundColor Cyan
$ffmpegPath = Join-Path $env:PROGRAMFILES "ffmpeg\bin\ffmpeg.exe"
if (Test-Path $ffmpegPath) {
    Copy-Item $ffmpegPath dist/UniqoRemote/
}

Write-Host "Build complete: dist/UniqoRemote/" -ForegroundColor Green
