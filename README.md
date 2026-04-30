<h1 align="center">YouTube Downloader</h1>

<p align="center">
  <img src="assets/youtube-logo.svg" alt="YouTube Downloader logo" width="120" />
</p>

<p align="center">
  Une application de bureau CustomTkinter au style YouTube moderne pour télécharger des vidéos avec <code>yt-dlp</code>. Les paquets compilés embarquent aussi <code>ffmpeg</code>.
</p>

<p align="center">
  <img src="https://img.shields.io/badge/YouTube-Downloader-FF0033?style=for-the-badge&logo=youtube&logoColor=white" alt="YouTube Downloader" />
  <br />
  <img src="https://img.shields.io/badge/Python-3.10+-3776AB?style=flat-square&logo=python&logoColor=white" alt="Python 3.10+" />
  <img src="https://img.shields.io/badge/yt--dlp-2026.03.17-FF0033?style=flat-square&logo=youtube&logoColor=white" alt="yt-dlp" />
  <img src="https://img.shields.io/badge/CustomTkinter-UI-111111?style=flat-square" alt="CustomTkinter" />
  <img src="https://img.shields.io/badge/ffmpeg-bundled-007808?style=flat-square&logo=ffmpeg&logoColor=white" alt="ffmpeg bundled" />
  <img src="https://img.shields.io/badge/Fullscreen-F11-303030?style=flat-square" alt="Fullscreen F11" />
</p>

<p align="center">
  <strong>Interface plein écran rouge/noir inspirée de YouTube.</strong>
</p>

## Prérequis pour lancer le code source

- Python 3.10+
- `customtkinter`
- `yt-dlp`
- `ffmpeg`

## Installation

```bash
python -m pip install -U customtkinter yt-dlp
```

Sur Fedora, `ffmpeg` doit aussi être installé pour lancer le code source directement.

## Utilisation

```bash
python youtube_downloader.py
```

L'application démarre en plein écran avec une interface sombre rouge/noir inspirée de YouTube.

1. Collez un lien YouTube ou utilisez **Coller**.
2. Choisissez la qualité maximale avec le sélecteur.
3. Les vidéos vont par défaut dans `Vidéos/YouTube Downloader`. Sélectionnez un autre dossier si besoin.
4. Cliquez sur **Télécharger**.

Raccourcis :

- **F11** : basculer plein écran / fenêtre
- **Échap** : sortir du plein écran

La zone **Activité** affiche la progression du téléchargement et l'étape de fusion audio/vidéo.

## Créer les paquets Linux

Installez les dépendances de build :

```bash
python -m pip install -r requirements-build.txt
```

Puis générez l'application compilée avec `yt-dlp`, `ffmpeg` et `ffprobe` embarqués, le `.deb`, le `.rpm` et une archive Linux :

```bash
./scripts/build_packages.sh
```

Les fichiers sortent dans :

```bash
dist/packages/
```

Le logo d'application est installé depuis :

```bash
assets/youtube-logo.svg
```

Les paquets compilés embarquent `ffmpeg` et `ffprobe` depuis la machine de build pour fusionner l'audio et la vidéo.

## Page GitHub Pages

La page de présentation est dans :

```text
index.html
```

Pour la publier :

1. Envoyez le dépôt sur GitHub.
2. Ouvrez **Settings** > **Pages**.
3. Dans **Build and deployment**, choisissez **Deploy from a branch**.
4. Sélectionnez la branche `main` et le dossier `/ (root)`.
5. Créez une release GitHub et ajoutez les fichiers de `dist/packages/`.
6. Pour Windows, ajoutez aussi `YouTubeDownloaderSetup.exe` dans la release après l'avoir compilé depuis Windows.

Les boutons de téléchargement de la page pointent vers la release GitHub `v1.0.0` pour Debian/Ubuntu, Fedora/RPM, Linux portable et Windows.

## Créer l'installateur Windows

L'installateur Windows doit être compilé depuis Windows pour embarquer les bons binaires `.exe` et `.dll`.

Installez d'abord :

- Python 3.10+
- ffmpeg pour Windows, avec `ffmpeg.exe` et `ffprobe.exe` dans le `PATH`
- Inno Setup 6 pour créer l'installateur

```powershell
.\scripts\build_windows.ps1
```

Les fichiers Windows seront dans :

```text
dist\YouTubeDownloader.exe
dist\packages\YouTubeDownloaderSetup.exe
```

Depuis GitHub, l'installateur peut aussi être généré automatiquement :

1. Ouvrez l'onglet **Actions** du dépôt.
2. Lancez **Build Windows installer**.
3. Gardez le tag `v1.0.0`.
4. Le workflow compile `YouTubeDownloaderSetup.exe` et l'ajoute à la release GitHub.

## Mise à jour yt-dlp

Si YouTube change quelque chose et que les téléchargements échouent :

```bash
python -m pip install -U yt-dlp
```
