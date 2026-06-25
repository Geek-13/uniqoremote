param(
    [string]$ServerAddr = "",
    [string]$DeviceName = "Test-PC",
    [int]$Fps = 30
)

$ErrorActionPreference = "Stop"

if (-not $ServerAddr) {
    $ServerAddr = Read-Host "Enter server address (e.g. 192.168.1.100:21116)"
}

$deviceId = -join ((48..57) + (97..102) | Get-Random -Count 12 | ForEach-Object { [char]$_ })

$content = @"
[identity]
device_id = "$deviceId"
device_name = "$DeviceName"

[network]
bind_port = 21116
rendezvous_server = "$ServerAddr"

[display]
default_width = 1920
default_height = 1080
max_fps = $Fps

[ai]
enabled = false
model = "deepseek-chat"
api_key = ""
"@

Set-Content -Path "config.toml" -Value $content -Encoding UTF8
Write-Host "config.toml created:" -ForegroundColor Green
Write-Host "  Device ID : $deviceId"
Write-Host "  Server    : $ServerAddr"
Write-Host "  FPS       : $Fps"
