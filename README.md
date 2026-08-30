<h1 align="center">YouTube Downloader</h1>

<p align="center">
  <img src="assets/youtube-logo.svg" alt="YouTube Downloader logo" width="120" />
</p>

<p align="center">
  Une application complete (Desktop et Mobile Android) au style YouTube moderne pour telecharger des videos avec <code>yt-dlp</code>. Les versions integrent la <strong>mise a jour automatique et a chaud de yt-dlp</strong> ainsi que <code>ffmpeg</code> embarque pour garantir un fonctionnement permanent sans interruption.
</p>

<p align="center">
  <img src="https://img.shields.io/badge/YouTube-Downloader-FF0033?style=for-the-badge&logo=youtube&logoColor=white" alt="YouTube Downloader" />
  <br />
  <img src="https://img.shields.io/badge/Release-v1.1.0-22c55e?style=flat-square" alt="Release v1.1.0" />
  <img src="https://img.shields.io/badge/Python-3.10+-3776AB?style=flat-square&logo=python&logoColor=white" alt="Python 3.10+" />
  <img src="https://img.shields.io/badge/Flutter-Android-02569B?style=flat-square&logo=flutter&logoColor=white" alt="Flutter Android" />
  <img src="https://img.shields.io/badge/yt--dlp-Auto--Update-FF0033?style=flat-square&logo=youtube&logoColor=white" alt="yt-dlp Auto-Update" />
  <img src="https://img.shields.io/badge/CustomTkinter-UI-111111?style=flat-square" alt="CustomTkinter" />
  <img src="https://img.shields.io/badge/ffmpeg-bundled-007808?style=flat-square&logo=ffmpeg&logoColor=white" alt="ffmpeg bundled" />
  <img src="https://img.shields.io/badge/Fullscreen-F11-303030?style=flat-square" alt="Fullscreen F11" />
</p>

<p align="center">
  <strong>Interface plein ecran sombre rouge/noir sur bureau, avec application Android Flutter assortie.</strong>
</p>

---

## Fonctionnalites cles

- **Mise a jour automatique du moteur yt-dlp** : L'application verifie en arriere-plan et installe les derniers correctifs de YouTube au lancement et a la demande via un bouton dedie.
- **Qualite ajustable** : De 360p jusqu'a 4K (2160p) ou extraction Audio MP3.
- **Tout-en-un et portable** : FFmpeg et FFprobe sont directement embarques et configures.
- **Multi-plateforme** :
  - **Windows** : Installateur autonome `.exe` (Inno Setup)
  - **Linux** : Paquets natifs `.deb` (Debian/Ubuntu), `.rpm` (Fedora/RHEL/openSUSE sans conflit de dependances) et archive portable `.tar.gz`.
  - **Android** : Application Flutter native avec selection du stockage et moteur yt-dlp integre.

---

## Version Desktop (Python / CustomTkinter)

### Lancer depuis les sources

**Prerequis** : Python 3.10+, ffmpeg

```bash
# Installation des dependances
python3 -m pip install -U customtkinter yt-dlp

# Lancement
python3 youtube_downloader.py
```

### Utilisation

1. Collez un lien YouTube avec le bouton **Coller** ou `Ctrl+V`.
2. Choisissez la resolution maximale desiree.
3. Choisissez le dossier de destination (par defaut `Videos/YouTube Downloader`).
4. Cliquez sur **Telecharger**.
5. Raccourcis : **F11** pour basculer en plein ecran, **Echap** pour quitter le plein ecran.

### Mise a jour du moteur yt-dlp

Si YouTube modifie ses algorithmes ou bloque les telechargements :
- **Automatique** : L'application recherche et applique silencieusement les nouvelles versions au demarrage.
- **Manuelle** : Cliquez sur le bouton **Mettre a jour yt-dlp** dans la barre laterale pour recharger immediatement la derniere version sans redemarrer le programme.

---

## Compilation et Paquets Desktop

### Paquets Linux (.deb, .rpm, .tar.gz)

Installez les dependances de build puis lancez le script :

```bash
python3 -m pip install -r requirements-build.txt
./scripts/build_packages.sh
```

Les paquets generes se trouvent dans `dist/packages/` :
- `youtube-downloader_1.1.0_amd64.deb`
- `youtube-downloader-1.1.0-1.x86_64.rpm`
- `youtube-downloader-1.1.0-linux-x86_64.tar.gz`

### Installateur Windows (.exe)

Sur Windows (PowerShell avec Inno Setup 6 et ffmpeg installes) :

```powershell
.\scripts\build_windows.ps1
```

Genere `dist\packages\YouTubeDownloaderSetup.exe`.

### Compilation automatique sur GitHub Actions

Le workflow GitHub Actions [`.github/workflows/build-windows-release.yml`](.github/workflows/build-windows-release.yml) compile automatiquement l'ensemble des paquets Linux et Windows a chaque creation de tag de release (`v*`).

---

## Version Mobile (Android Flutter)

L'application Android se trouve dans le dossier `mobile/`. Elle propose une interface similaire et exploite `youtubedl-android` avec mise a jour en ligne de yt-dlp.

### Compiler l'APK Android

```bash
cd mobile
flutter pub get
flutter build apk --release
```

L'APK genere sera disponible dans :
```text
mobile/build/app/outputs/flutter-apk/app-release.apk
```

---

## Site Web et GitHub Pages

Le site de presentation est defini dans [`index.html`](index.html). Il integre les liens de telechargement directs vers la derniere release GitHub (`v1.1.0`).


