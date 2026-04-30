# YouTube Downloader Mobile

Application Flutter pour la version Android de YouTube Downloader.

## Etat actuel

- Interface Flutter rouge/noir inspiree de YouTube.
- Champ URL, selection de qualite, bouton de telechargement et panneau d'activite.
- Choix du dossier de sortie avec le selecteur de dossier Android.
- Logo d'application partage avec la version desktop.
- Telechargement Android branche via `youtubedl-android`, `yt-dlp` et `ffmpeg`.
- Affichage du detail complet si Android ou `yt-dlp` renvoie une erreur.

## Creer les fichiers natifs Android/iOS

Depuis ce dossier, avec Flutter installe correctement :

```bash
flutter create .
```

Flutter ajoutera les dossiers natifs `android/`, `ios/`, `linux/`, etc. Les fichiers `pubspec.yaml` et `lib/main.dart` existent deja et seront conserves.

## Lancer

```bash
flutter pub get
flutter run
```

## Compiler un APK

```bash
flutter build apk --release
```

Le fichier sortira dans :

```text
build/app/outputs/flutter-apk/app-release.apk
```

## Notes Android

Par defaut, les videos sont enregistrees dans :

```text
Downloads/YouTube Downloader
```

Le bouton **Choisir le dossier de sortie** ouvre le selecteur Android. Le dossier choisi est garde pour les prochains telechargements.

Sur Android 10+, l'app utilise le selecteur de dossier Android ou MediaStore pour rester compatible avec le stockage limite Android.

## Prochaines etapes

- ajouter une notification de progression ;
- ajouter un bouton pour ouvrir le dossier de sortie ;
- ajouter une version iOS separee si necessaire.
