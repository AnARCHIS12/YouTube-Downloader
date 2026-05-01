$ErrorActionPreference = "Stop"

$RootDir = Split-Path -Parent $PSScriptRoot
$DistDir = Join-Path $RootDir "dist"
$PackageDir = Join-Path $DistDir "packages"
$InstallerScript = Join-Path $RootDir "packaging\windows-installer.iss"
$InstallerExe = Join-Path $PackageDir "YouTubeDownloaderSetup.exe"

Set-Location $RootDir

function Test-ChocolateyShim {
    param(
        [Parameter(Mandatory = $true)]
        [string]$Path
    )

    $parent = Split-Path -Parent $Path
    $grandParent = Split-Path -Parent $parent

    return ((Split-Path -Leaf $parent) -ieq "bin" -and (Split-Path -Leaf $grandParent) -ieq "chocolatey")
}

function Find-RealFfmpegTool {
    param(
        [Parameter(Mandatory = $true)]
        [string]$Name
    )

    $exeName = "$Name.exe"
    $candidates = @()

    if ($env:FFMPEG_BIN_DIR) {
        $candidates += Join-Path $env:FFMPEG_BIN_DIR $exeName
    }

    if ($env:ProgramData) {
        $candidates += Join-Path $env:ProgramData "chocolatey\lib\ffmpeg\tools\ffmpeg\bin\$exeName"
    }

    $pathCommand = Get-Command $Name -ErrorAction SilentlyContinue
    if ($pathCommand) {
        $candidates += $pathCommand.Source
    }

    $shimPath = $null

    foreach ($path in $candidates) {
        if (-not $path -or -not (Test-Path $path)) {
            continue
        }

        $resolvedPath = (Resolve-Path $path).Path
        if (Test-ChocolateyShim $resolvedPath) {
            if (-not $shimPath) {
                $shimPath = $resolvedPath
            }
            continue
        }

        return $resolvedPath
    }

    if ($shimPath) {
        throw "$Name pointe vers le shim Chocolatey ($shimPath), pas vers le vrai binaire. Ajoute le dossier reel ffmpeg\bin au PATH."
    }

    throw "$Name introuvable. Installe ffmpeg pour Windows ou ajoute son dossier bin au PATH avant de compiler."
}

function Test-FfmpegToolStarts {
    param(
        [Parameter(Mandatory = $true)]
        [string]$Name,
        [Parameter(Mandatory = $true)]
        [string]$Path
    )

    & $Path -version | Out-Null
    if ($LASTEXITCODE -ne 0) {
        throw "$Name ne demarre pas correctement : $Path"
    }
}

$ffmpegPath = Find-RealFfmpegTool "ffmpeg"
$ffprobePath = Find-RealFfmpegTool "ffprobe"
$ffmpegBinDir = Split-Path -Parent $ffmpegPath

Test-FfmpegToolStarts "ffmpeg" $ffmpegPath
Test-FfmpegToolStarts "ffprobe" $ffprobePath

if ((Split-Path -Parent $ffprobePath) -ne $ffmpegBinDir) {
    Write-Host "ffmpeg : $ffmpegPath"
    Write-Host "ffprobe: $ffprobePath"
}

$env:FFMPEG_BIN_DIR = $ffmpegBinDir
$env:FFMPEG_PATH = $ffmpegPath
$env:FFPROBE_PATH = $ffprobePath
$env:PATH = "$ffmpegBinDir;$env:PATH"

Write-Host "Binaires FFmpeg embarques depuis : $ffmpegBinDir"

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
