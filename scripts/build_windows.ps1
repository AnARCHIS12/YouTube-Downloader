$ErrorActionPreference = "Stop"

$RootDir = Split-Path -Parent $PSScriptRoot
$DistDir = Join-Path $RootDir "dist"
$PackageDir = Join-Path $DistDir "packages"
$InstallerScript = Join-Path $RootDir "packaging\windows-installer.iss"
$InstallerExe = Join-Path $PackageDir "YouTubeDownloaderSetup.exe"

Set-Location $RootDir

foreach ($command in @("ffmpeg", "ffprobe")) {
    if (-not (Get-Command $command -ErrorAction SilentlyContinue)) {
        throw "$command introuvable. Installe-le ou ajoute-le au PATH avant de compiler Windows."
    }
}

$python = Get-Command "py" -ErrorAction SilentlyContinue
if ($python) {
    & py -m pip install -r requirements-build.txt
    & py -m PyInstaller --clean --noconfirm YouTubeDownloader.spec
}
else {
    $python = Get-Command "python" -ErrorAction SilentlyContinue
    if (-not $python) {
        throw "Python introuvable. Installe Python 3.10+ ou ajoute-le au PATH."
    }

    & python -m pip install -r requirements-build.txt
    & python -m PyInstaller --clean --noconfirm YouTubeDownloader.spec
}

New-Item -ItemType Directory -Force -Path $PackageDir | Out-Null

$isccPath = $null
$iscc = Get-Command "ISCC.exe" -ErrorAction SilentlyContinue
if ($iscc) {
    $isccPath = $iscc.Source
}

if (-not $isccPath) {
    $possiblePaths = @(
        "${env:ProgramFiles(x86)}\Inno Setup 6\ISCC.exe",
        "${env:ProgramFiles}\Inno Setup 6\ISCC.exe"
    )

    foreach ($path in $possiblePaths) {
        if (Test-Path $path) {
            $isccPath = $path
            break
        }
    }
}

if (-not $isccPath) {
    Write-Host "EXE cree : dist\YouTubeDownloader.exe"
    Write-Host "Installe Inno Setup 6 pour creer l'installateur : https://jrsoftware.org/isinfo.php"
    throw "ISCC.exe introuvable, installateur non cree."
}

& $isccPath $InstallerScript

if (-not (Test-Path $InstallerExe)) {
    throw "Installateur attendu introuvable : $InstallerExe"
}

Write-Host ""
Write-Host "Build Windows termine :"
Write-Host "  EXE         : dist\YouTubeDownloader.exe"
Write-Host "  Installateur: dist\packages\YouTubeDownloaderSetup.exe"
