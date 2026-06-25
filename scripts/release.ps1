param(
    [switch]$Clean
)

$ErrorActionPreference = "Stop"
$VenvPython = ".\.venv\Scripts\python.exe"

if ($Clean) {
    Remove-Item -Recurse -Force -ErrorAction SilentlyContinue build, dist, release
}

Write-Host "=== 1/4 Running tests..." -ForegroundColor Cyan
& $VenvPython -m pytest tests/ --tb=short -q --ignore=tests/ui
if ($LASTEXITCODE -ne 0) { throw "Tests failed" }

Write-Host "=== 2/4 Building..." -ForegroundColor Cyan
Remove-Item -Recurse -Force -ErrorAction SilentlyContinue build, dist
& $VenvPython -m PyInstaller --noconsole --onedir --name UniqoRemote src/uniqoremote/ui/__main__.py
if ($LASTEXITCODE -ne 0) { throw "Build failed" }

Write-Host "=== 3/4 Bundling FFmpeg..." -ForegroundColor Cyan
$ffmpegPaths = @(
    "$env:PROGRAMFILES\ffmpeg\bin\ffmpeg.exe",
    "C:\ffmpeg\bin\ffmpeg.exe",
    (Get-Command ffmpeg.exe -ErrorAction SilentlyContinue | Select-Object -ExpandProperty Source)
)
$ffmpeg = $null
foreach ($p in $ffmpegPaths) { if ($p -and (Test-Path $p)) { $ffmpeg = $p; break } }
if ($ffmpeg) {
    Copy-Item $ffmpeg dist/UniqoRemote/
    Write-Host "  ffmpeg.exe bundled" -ForegroundColor Green
} else {
    Write-Host "  FFmpeg not found - skipped" -ForegroundColor Yellow
}

Write-Host "=== 4/4 Creating release package..." -ForegroundColor Cyan
Remove-Item -Recurse -Force -ErrorAction SilentlyContinue release
New-Item -ItemType Directory release/UniqoRemote | Out-Null
Copy-Item -Recurse dist/UniqoRemote/* release/UniqoRemote/

@'
@echo off
setlocal
cd /d "%~dp0"
start "" "UniqoRemote.exe"
'@ | Out-File -FilePath release/UniqoRemote/启动.bat -Encoding Default

Compress-Archive -Path release/UniqoRemote -DestinationPath release/UniqoRemote.zip -Force

$zip = Get-Item release/UniqoRemote.zip
Write-Host "`n=== Done ===" -ForegroundColor Green
Write-Host "  Package: release/UniqoRemote.zip ($([math]::Round($zip.Length/1MB,1)) MB)"
Write-Host "  Send this zip to the other machine and extract + run 启动.bat"
