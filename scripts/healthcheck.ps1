param(
    [string]$ServerAddr = ""
)

$ErrorActionPreference = "Stop"
$VenvPython = ".\.venv\Scripts\python.exe"

Write-Host "=== UniqoRemote Health Check ===" -ForegroundColor Cyan

Write-Host "[1/6] Python version..." -ForegroundColor Yellow
& $VenvPython -c "import sys; v=sys.version_info; print(f'Python {v.major}.{v.minor}.{v.micro}'); assert v >= (3,11), 'Need Python 3.11+'"

Write-Host "[2/6] Dependencies..." -ForegroundColor Yellow
& $VenvPython -c "import cryptography, msgpack, numpy, structlog, PySide6, qasync; print('OK')"

Write-Host "[3/6] FFmpeg..." -ForegroundColor Yellow
$ffmpeg = $null
@("ffmpeg.exe", "$env:PROGRAMFILES\ffmpeg\bin\ffmpeg.exe") | ForEach-Object {
    if (-not $ffmpeg -and (Get-Command $_ -ErrorAction SilentlyContinue)) { $ffmpeg = $_ }
}
if ($ffmpeg) { Write-Host "  Found: $ffmpeg" -ForegroundColor Green }
else { Write-Host "  NOT FOUND - install from https://ffmpeg.org/download.html" -ForegroundColor Red }

Write-Host "[4/6] Port availability..." -ForegroundColor Yellow
$ports = @(21116, 21117, 9510)
foreach ($p in $ports) {
    $inUse = netstat -ano | Select-String ":$p "
    if ($inUse) { Write-Host "  Port $p : IN USE" -ForegroundColor Red }
    else { Write-Host "  Port $p : free" -ForegroundColor Green }
}

Write-Host "[5/6] Server connectivity..." -ForegroundColor Yellow
if ($ServerAddr) {
    $hostname, $portStr = $ServerAddr -split ":", 2
    $port = [int]$portStr
    $udp = New-Object System.Net.Sockets.UdpClient
    try {
        $udp.Connect($hostname, $port)
        $udp.Send([byte[]]@(0), 1)
        $udp.Client.ReceiveTimeout = 3000
        try { $udp.Receive([ref](New-Object System.Net.IPEndPoint([System.Net.IPAddress]::Any, 0))) | Out-Null }
        catch [System.Net.Sockets.SocketException] {}
        Write-Host "  Server $ServerAddr : reachable" -ForegroundColor Green
    } catch {
        Write-Host "  Server $ServerAddr : UNREACHABLE" -ForegroundColor Red
    } finally { $udp.Close() }
} else {
    Write-Host "  Skipped (no --ServerAddr given)" -ForegroundColor DarkGray
}

Write-Host "[6/6] Config..." -ForegroundColor Yellow
if (Test-Path "config.toml") {
    $cfg = Get-Content "config.toml" -Raw
    if ($cfg -match 'rendezvous_server = ""') {
        Write-Host "  config.toml exists but rendezvous_server is empty" -ForegroundColor Yellow
    } else {
        Write-Host "  config.toml OK" -ForegroundColor Green
    }
} else {
    Write-Host "  config.toml not found (will be auto-created on first run)" -ForegroundColor Yellow
}

Write-Host "`n=== Done ===" -ForegroundColor Cyan
