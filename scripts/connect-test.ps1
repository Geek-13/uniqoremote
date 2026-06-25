param(
    [string]$RemoteDeviceId = "",
    [string]$ServerAddr = ""
)

$ErrorActionPreference = "Stop"
$VenvPython = ".\.venv\Scripts\python.exe"

if (-not $RemoteDeviceId) {
    $RemoteDeviceId = Read-Host "Enter remote device ID"
}
if (-not $ServerAddr) {
    $cfg = Get-Content "config.toml" -Raw
    if ($cfg -match 'rendezvous_server = "(.+?)"') { $ServerAddr = $Matches[1] }
    if (-not $ServerAddr) { $ServerAddr = Read-Host "Enter server address (e.g. ip:port)" }
}

Write-Host "Connecting to $RemoteDeviceId via $ServerAddr ..." -ForegroundColor Cyan

$script = @"
import asyncio
import sys
from pathlib import Path
sys.path.insert(0, 'src')

from uniqoremote.core.config import load_config
from uniqoremote.session.manager import SessionManager
from uniqoremote.transport.p2p import P2PTransport, StunClient
from uniqoremote.transport.tcp import TcpTransport

async def main():
    config = load_config(Path('config.toml'))
    host, port_str = '$ServerAddr'.rsplit(':', 1)
    server_addr = (host, int(port_str))

    mgr = SessionManager()
    stun = StunClient()
    p2p = P2PTransport()
    relay = TcpTransport()

    print(f'Discovering public address via STUN...')
    addr = await stun.discover()
    print(f'Public address: {addr}')

    print(f'Connecting to {$RemoteDeviceId}...')
    try:
        session = await mgr.connect(
            remote_device_id='$RemoteDeviceId',
            server_addr=server_addr,
            stun=stun,
            p2p=p2p,
            relay=relay,
            config_device_id=config.identity.device_id,
        )
        print(f'Connected! Session state: {session.state}')
        print(f'Session ID: {session.session_id}')
    except Exception as e:
        print(f'Connection failed: {e}')
        sys.exit(1)

asyncio.run(main())
"@

& $VenvPython -c $script
