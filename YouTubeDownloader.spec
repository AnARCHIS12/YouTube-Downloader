# -*- mode: python ; coding: utf-8 -*-

import os
import shutil
from PyInstaller.utils.hooks import collect_data_files, collect_submodules


block_cipher = None


def _path_parts(path):
    return os.path.normcase(os.path.abspath(path)).split(os.sep)


def _is_chocolatey_shim(path):
    parts = _path_parts(path)
    return len(parts) >= 3 and parts[-3] == "chocolatey" and parts[-2] == "bin"


def _tool_candidates(tool):
    executable = tool + (".exe" if os.name == "nt" else "")
    env_path = os.environ.get(f"{tool.upper()}_PATH")
    env_bin_dir = os.environ.get("FFMPEG_BIN_DIR")

    if env_path:
        yield env_path

    if env_bin_dir:
        yield os.path.join(env_bin_dir, executable)

    if os.name == "nt":
        program_data = os.environ.get("ProgramData", r"C:\ProgramData")
        yield os.path.join(program_data, "chocolatey", "lib", "ffmpeg", "tools", "ffmpeg", "bin", executable)

    for path_dir in os.environ.get("PATH", "").split(os.pathsep):
        if path_dir:
            yield os.path.join(path_dir, executable)

    which_path = shutil.which(tool)
    if which_path:
        yield which_path


def find_tool_binary(tool):
    shim_fallback = None

    for candidate in _tool_candidates(tool):
        if not candidate or not os.path.isfile(candidate):
            continue

        if _is_chocolatey_shim(candidate):
            shim_fallback = shim_fallback or candidate
            continue

        return candidate

    if shim_fallback:
        raise RuntimeError(
            f"{tool} pointe vers le shim Chocolatey {shim_fallback}. "
            "Ajoute le dossier reel ffmpeg\\bin au PATH ou definis FFMPEG_BIN_DIR."
        )

    return None

datas = [
    ("assets/youtube-logo.svg", "assets"),
    ("assets/youtube-logo.ico", "assets"),
]
datas += collect_data_files("customtkinter")

hiddenimports = collect_submodules("yt_dlp")

binaries = []
for tool in ("ffmpeg", "ffprobe"):
    path = find_tool_binary(tool)
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
