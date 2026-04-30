# ⬇️ Téléchargeur YouTube (Cobalt Version)

Une application de bureau moderne et légère pour télécharger des vidéos YouTube sans les tracas des cookies ou des navigateurs verrouillés.

## ✨ Caractéristiques

- **🚀 Sans Navigateur :** Contrairement aux solutions basées sur `yt-dlp`, cette application n'a pas besoin d'accéder aux cookies de votre navigateur (Edge, Chrome, etc.).
- **🔒 Sans Cookies :** Utilise l'API Cobalt pour traiter les téléchargements côté serveur, évitant ainsi les erreurs de déchiffrement DPAPI et les blocages anti-bot locaux.
- **🎨 Interface Moderne :** Une interface sombre et élégante construite avec `CustomTkinter`.
- **📊 Progression en Temps Réel :** Suivez la vitesse et l'état de votre téléchargement avec une barre de progression précise.
- **⚙️ Qualité Flexible :** Choisissez votre résolution préférée, de 360p jusqu'à la 4K (2160p).
- **🔗 Instances Redondantes :** Bascule automatiquement entre plusieurs serveurs Cobalt pour garantir une disponibilité maximale.

## 📋 Prérequis

- **Python 3.10+**
- Les bibliothèques suivantes :
  - `customtkinter`
  - `requests`

## 🛠️ Installation

1. Clonez ou téléchargez ce dépôt.
2. Installez les dépendances nécessaires :

```bash
pip install customtkinter requests
```

## 🚀 Utilisation

Lancez simplement le script Python :

```bash
python youtube_downloader.py
```

1. Copiez le lien de la vidéo YouTube souhaitée.
2. Collez-le dans le champ "Lien de la vidéo".
3. Sélectionnez la qualité désirée.
4. Cliquez sur **Télécharger**.
5. La vidéo sera enregistrée dans le même dossier que le script.

## 🛡️ Pourquoi cette version ?

Les versions précédentes utilisant `yt-dlp` rencontraient souvent des erreurs de type `Failed to decrypt with DPAPI` à cause des nouvelles sécurités de Chrome et Edge (App-Bound Encryption). Cette version résout définitivement ce problème en utilisant des instances **Cobalt** distantes pour extraire les flux vidéo, rendant le processus 100% fiable et indépendant de votre configuration de navigateur.

## 📜 Licence

Ce projet est destiné à un usage personnel et éducatif. Veuillez respecter les droits d'auteur et les conditions d'utilisation de YouTube.
