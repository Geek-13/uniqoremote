# -*- mode: python ; coding: utf-8 -*-

block_cipher = None

a = Analysis(
    ['src/uniqoremote/ui/__main__.py'],
    pathex=[],
    binaries=[],
    datas=[
        ('resources/config.toml', '.'),
    ],
    hiddenimports=[
        'cryptography',
        'msgpack',
        'numpy',
        'structlog',
        'PySide6',
        'qasync',
        'uniqoremote.core',
        'uniqoremote.transport',
        'uniqoremote.pipeline',
        'uniqoremote.input',
        'uniqoremote.session',
        'uniqoremote.agent',
        'uniqoremote.server',
        'uniqoremote.ai',
        'uniqoremote.ui',
    ],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False,
)

pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name='UniqoRemote',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    console=False,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon='resources/icon.ico',
)

coll = COLLECT(
    exe,
    a.binaries,
    a.zipfiles,
    a.datas,
    strip=False,
    upx=True,
    upx_exclude=[],
    name='UniqoRemote',
)
