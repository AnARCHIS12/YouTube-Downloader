# -*- mode: python ; coding: utf-8 -*-

import shutil
from PyInstaller.utils.hooks import collect_data_files, collect_submodules


block_cipher = None

datas = [
    ("assets/youtube-logo.svg", "assets"),
    ("assets/youtube-logo.ico", "assets"),
]
datas += collect_data_files("customtkinter")

hiddenimports = collect_submodules("yt_dlp")

binaries = []
for tool in ("ffmpeg", "ffprobe"):
    path = shutil.which(tool)
    if path:
        binaries.append((path, "."))

a = Analysis(
    ["youtube_downloader.py"],
    pathex=[],
    binaries=binaries,
    datas=datas,
    hiddenimports=hiddenimports,
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
    a.binaries,
    a.zipfiles,
    a.datas,
    [],
    name="YouTubeDownloader",
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=False,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon="assets/youtube-logo.ico",
)
