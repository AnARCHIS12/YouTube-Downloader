import io
import json
import os
import re
import shutil
import sys
import threading
import tkinter as tk
from tkinter import filedialog, messagebox
import urllib.request
import zipfile

import customtkinter as ctk

# ==================== GESTION DYNAMIQUE DU MOTEUR (YT-DLP) ====================

def get_engine_dir():
    """Retourne le répertoire utilisateur dédié aux mises à jour de yt-dlp."""
    if os.name == "nt":
        base = os.environ.get("APPDATA") or os.path.expanduser("~")
        path = os.path.join(base, "YouTube Downloader", "engine")
    else:
        path = os.path.join(os.path.expanduser("~"), ".local", "share", "youtube-downloader", "engine")
    os.makedirs(path, exist_ok=True)
    return path

def setup_engine_path():
    """Ajoute le répertoire moteur utilisateur en tête de sys.path."""
    engine_dir = get_engine_dir()
    if engine_dir not in sys.path:
        sys.path.insert(0, engine_dir)

setup_engine_path()
import yt_dlp

# ==================== CONFIGURATION ====================
ctk.set_appearance_mode("Dark")
ctk.set_default_color_theme("dark-blue")

BG_COLOR = "#0f0f0f"
SIDEBAR_COLOR = "#050505"
PANEL_COLOR = "#181818"
PANEL_ALT_COLOR = "#212121"
INPUT_COLOR = "#121212"
BORDER_COLOR = "#303030"
TEXT_MUTED = "#aaaaaa"
TEXT_SOFT = "#e5e5e5"
YOUTUBE_RED = "#ff0033"
YOUTUBE_RED_DARK = "#cc0029"
YOUTUBE_RED_SOFT = "#3a1017"
SUCCESS = "#22c55e"
WARNING = "#f59e0b"
ERROR = "#ff4e45"
WHITE = "#ffffff"

# ==================== LOGIQUE DU MOTEUR YT-DLP & MISES À JOUR ====================

def parse_version(v_str):
    """Transforme une chaîne de version en tuple d'entiers pour comparaison fiable."""
    if not v_str:
        return (0,)
    parts = []
    for part in re.split(r"[\.\-_]", str(v_str)):
        digits = re.findall(r"\d+", part)
        if digits:
            parts.append(int(digits[0]))
    return tuple(parts) if parts else (0,)

def get_current_ytdlp_version():
    """Retourne la version actuellement chargée de yt-dlp."""
    try:
        return yt_dlp.version.__version__
    except Exception:
        return "inconnue"

def reload_ytdlp_module():
    """Recharge dynamiquement yt_dlp et tous ses sous-modules pour utiliser la nouvelle version."""
    global yt_dlp
    modules_to_remove = [name for name in sys.modules if name == "yt_dlp" or name.startswith("yt_dlp.")]
    for name in modules_to_remove:
        del sys.modules[name]

    setup_engine_path()
    import yt_dlp as reloaded_ytdlp
    yt_dlp = reloaded_ytdlp
    return yt_dlp

def fetch_latest_ytdlp_info():
    """Récupère les informations de la dernière version de yt-dlp depuis PyPI ou GitHub."""
    headers = {"User-Agent": "YouTube-Downloader/1.0 (Desktop App)"}

    # 1. Tentative principale via l'API PyPI
    try:
        req = urllib.request.Request("https://pypi.org/pypi/yt-dlp/json", headers=headers)
        with urllib.request.urlopen(req, timeout=12) as resp:
            data = json.loads(resp.read().decode("utf-8"))
            version = data.get("info", {}).get("version")
            wheel_url = None
            tar_url = None
            for file_info in data.get("urls", []):
                packagetype = file_info.get("packagetype")
                filename = file_info.get("filename", "")
                if packagetype == "bdist_wheel" and filename.endswith("-none-any.whl"):
                    wheel_url = file_info.get("url")
                    break
                elif packagetype == "sdist" or filename.endswith(".tar.gz"):
                    tar_url = file_info.get("url")

            download_url = wheel_url or tar_url
            if version and download_url:
                return version, download_url
    except Exception:
        pass

    # 2. Tentative de secours via l'API GitHub Releases
    try:
        req = urllib.request.Request("https://api.github.com/repos/yt-dlp/yt-dlp/releases/latest", headers=headers)
        with urllib.request.urlopen(req, timeout=12) as resp:
            data = json.loads(resp.read().decode("utf-8"))
            tag_name = data.get("tag_name", "").lstrip("v")
            download_url = None
            for asset in data.get("assets", []):
                name = asset.get("name", "")
                if name.endswith(".whl"):
                    download_url = asset.get("browser_download_url")
                    break
            if not download_url:
                download_url = data.get("zipball_url") or data.get("tarball_url")
            if tag_name and download_url:
                return tag_name, download_url
    except Exception:
        pass

    return None, None

def download_and_apply_ytdlp_update(download_url, new_version):
    """Télécharge l'archive yt-dlp et l'extrait dans le répertoire moteur utilisateur."""
    headers = {"User-Agent": "YouTube-Downloader/1.0 (Desktop App)"}
    req = urllib.request.Request(download_url, headers=headers)
    with urllib.request.urlopen(req, timeout=45) as resp:
        archive_bytes = resp.read()

    engine_dir = get_engine_dir()
    tmp_extract_dir = os.path.join(engine_dir, "yt_dlp_tmp")
    if os.path.exists(tmp_extract_dir):
        shutil.rmtree(tmp_extract_dir, ignore_errors=True)
    os.makedirs(tmp_extract_dir, exist_ok=True)

    if download_url.endswith(".whl") or download_url.endswith(".zip") or b"PK\x03\x04" in archive_bytes[:10]:
        with zipfile.ZipFile(io.BytesIO(archive_bytes)) as zf:
            for member in zf.infolist():
                if member.filename.startswith("yt_dlp/") or member.filename.startswith("yt_dlp\\"):
                    zf.extract(member, tmp_extract_dir)
    else:
        import tarfile
        with tarfile.open(fileobj=io.BytesIO(archive_bytes), mode="r:*") as tf:
            for member in tf.getmembers():
                if "/yt_dlp/" in member.name or member.name.endswith("/yt_dlp") or member.name.startswith("yt_dlp/"):
                    tf.extract(member, tmp_extract_dir)

    extracted_package = os.path.join(tmp_extract_dir, "yt_dlp")
    target_package = os.path.join(engine_dir, "yt_dlp")

    if not os.path.exists(extracted_package):
        for root, dirs, _ in os.walk(tmp_extract_dir):
            if "yt_dlp" in dirs:
                extracted_package = os.path.join(root, "yt_dlp")
                break

    if not os.path.exists(extracted_package):
        raise RuntimeError("Paquet yt_dlp introuvable dans l'archive téléchargée.")

    target_backup = os.path.join(engine_dir, "yt_dlp_backup")
    if os.path.exists(target_backup):
        shutil.rmtree(target_backup, ignore_errors=True)

    if os.path.exists(target_package):
        try:
            os.rename(target_package, target_backup)
        except OSError:
            shutil.rmtree(target_package, ignore_errors=True)

    shutil.move(extracted_package, target_package)
    shutil.rmtree(tmp_extract_dir, ignore_errors=True)
    if os.path.exists(target_backup):
        shutil.rmtree(target_backup, ignore_errors=True)

    version_file = os.path.join(engine_dir, "version.txt")
    try:
        with open(version_file, "w", encoding="utf-8") as vf:
            vf.write(new_version)
    except OSError:
        pass

    reload_ytdlp_module()

is_updating_moteur = False

def lancer_mise_a_jour_moteur(interactive=True):
    global is_updating_moteur
    if is_updating_moteur:
        if interactive:
            messagebox.showinfo("Mise à jour", "Une vérification de mise à jour est déjà en cours.")
        return
    threading.Thread(target=check_and_update_ytdlp, args=(interactive,), daemon=True).start()

def check_and_update_ytdlp(interactive=False):
    global is_updating_moteur
    is_updating_moteur = True
    current_ver = get_current_ytdlp_version()

    if interactive:
        safe_ui(bouton_maj_moteur.configure, state="disabled", text="Vérification...")
        set_detail("Recherche d'une mise à jour de yt-dlp...")

    try:
        latest_ver, download_url = fetch_latest_ytdlp_info()
        if not latest_ver or not download_url:
            if interactive:
                safe_ui(messagebox.showwarning, "Mise à jour", "Impossible de vérifier les mises à jour (connexion Internet indisponible).")
                set_detail("Vérification de mise à jour échouée (hors ligne).")
            return

        if parse_version(latest_ver) > parse_version(current_ver):
            safe_ui(version_label.configure, text=f"yt-dlp {current_ver} ➜ {latest_ver}")
            safe_ui(bouton_maj_moteur.configure, state="disabled", text="Téléchargement...")
            set_status("Mise à jour du moteur", WARNING)
            set_detail(f"Téléchargement et installation de yt-dlp v{latest_ver}...")

            download_and_apply_ytdlp_update(download_url, latest_ver)
            new_ver = get_current_ytdlp_version()

            safe_ui(version_label.configure, text=f"yt-dlp {new_ver}")
            safe_ui(side_status_text.configure, text=f"yt-dlp v{new_ver} (à jour)\nffmpeg fusionne audio + vidéo")
            set_status("Moteur à jour", SUCCESS)
            set_detail(f"yt-dlp a été mis à jour avec succès vers la version {new_ver} !")

            if interactive:
                safe_ui(messagebox.showinfo, "Mise à jour réussie", f"yt-dlp a été mis à jour avec succès vers la version {new_ver} ! 🎉")
        else:
            safe_ui(version_label.configure, text=f"yt-dlp {current_ver}")
            safe_ui(side_status_text.configure, text=f"yt-dlp v{current_ver} (à jour)\nffmpeg fusionne audio + vidéo")
            if interactive:
                set_status("Moteur à jour", SUCCESS)
                set_detail(f"yt-dlp est déjà à jour (version {current_ver}).")
                safe_ui(messagebox.showinfo, "À jour", f"yt-dlp est déjà à jour (version {current_ver}).")
    except Exception as error:
        if interactive:
            set_status("Échec mise à jour", ERROR)
            set_detail("Échec de la mise à jour de yt-dlp.")
            safe_ui(messagebox.showerror, "Erreur de mise à jour", f"Impossible de mettre à jour yt-dlp :\n{error}")
    finally:
        is_updating_moteur = False
        safe_ui(bouton_maj_moteur.configure, state="normal", text="🔄 Mettre à jour yt-dlp")

# ==================== LOGIQUE DE TÉLÉCHARGEMENT ====================

def get_runtime_dir():
    if getattr(sys, "frozen", False):
        return getattr(sys, "_MEIPASS", os.path.dirname(sys.executable))
    return os.path.dirname(os.path.abspath(__file__))

def get_ffmpeg_location():
    runtime_dir = get_runtime_dir()
    candidates = [
        os.path.join(runtime_dir, "ffmpeg"),
        os.path.join(runtime_dir, "ffmpeg.exe"),
        os.path.join(os.path.dirname(sys.executable), "ffmpeg"),
        os.path.join(os.path.dirname(sys.executable), "ffmpeg.exe"),
    ]

    for candidate in candidates:
        if os.path.isfile(candidate) and os.access(candidate, os.X_OK):
            return os.path.dirname(candidate)

    ffmpeg_path = shutil.which("ffmpeg")
    if ffmpeg_path:
        return os.path.dirname(ffmpeg_path)

    return None

def get_videos_dir():
    home_dir = os.path.expanduser("~")
    user_dirs_file = os.path.join(home_dir, ".config", "user-dirs.dirs")

    if os.path.isfile(user_dirs_file):
        try:
            with open(user_dirs_file, "r", encoding="utf-8") as file:
                for line in file:
                    if line.startswith("XDG_VIDEOS_DIR="):
                        value = line.split("=", 1)[1].strip().strip('"')
                        return value.replace("$HOME", home_dir)
        except OSError:
            pass

    for folder_name in ("Vidéos", "Videos"):
        candidate = os.path.join(home_dir, folder_name)
        if os.path.isdir(candidate):
            return candidate

    return os.path.join(home_dir, "Videos")

def get_default_output_dir():
    output_dir = os.path.join(get_videos_dir(), "YouTube Downloader")
    try:
        os.makedirs(output_dir, exist_ok=True)
        return output_dir
    except OSError:
        return os.getcwd()

def format_size(bytes_size):
    """Formate une taille en octets en format lisible."""
    if bytes_size is None:
        return "Taille inconnue"
    for unit in ["o", "Ko", "Mo", "Go"]:
        if bytes_size < 1024:
            return f"{bytes_size:.1f} {unit}"
        bytes_size /= 1024
    return f"{bytes_size:.1f} To"

def safe_ui(callback, *args, **kwargs):
    """Exécute une mise à jour Tkinter depuis le thread principal."""
    fenetre.after(0, lambda: callback(*args, **kwargs))

def set_status(text, color):
    safe_ui(label_status.configure, text=text, text_color=color)

def set_detail(text):
    safe_ui(label_detail.configure, text=text)

def explain_yt_dlp_error(error):
    message = str(error)
    lower_message = message.lower()

    if "sign in" in lower_message or "login" in lower_message or "cookies" in lower_message:
        return (
            "YouTube demande une session/cookies pour cette vidéo.\n\n"
            "Essaie une autre vidéo publique ou clique sur '🔄 Mettre à jour yt-dlp' pour obtenir les derniers correctifs."
        )

    if "ffmpeg" in lower_message:
        return "Erreur ffmpeg. Le binaire inclus est introuvable ou ne démarre pas."

    if "requested format is not available" in lower_message or "format is not available" in lower_message:
        return "La qualité demandée n'est pas disponible pour cette vidéo. Essaie une qualité plus basse ou mets à jour yt-dlp."

    if "private video" in lower_message:
        return "Cette vidéo est privée."

    if "video unavailable" in lower_message or "unavailable" in lower_message:
        return "Cette vidéo est indisponible, bloquée ou restreinte."

    if "unsupported url" in lower_message:
        return "URL non prise en charge par yt-dlp."

    if "signature" in lower_message or "n-sig" in lower_message or "extractor" in lower_message or "403" in lower_message:
        return (
            f"Erreur d'extraction YouTube ({message}).\n\n"
            "YouTube a mis à jour ses algorithmes. Clique sur '🔄 Mettre à jour yt-dlp' dans la barre latérale pour appliquer les derniers correctifs."
        )

    return f"{message}\n\n(Astuce : Si le problème persiste, clique sur '🔄 Mettre à jour yt-dlp' dans la barre latérale.)"

def lancer_telechargement():
    url = entree_url.get().strip()
    qualite = qualite_var.get()
    dossier_sortie = dossier_var.get().strip() or os.getcwd()

    if not url:
        messagebox.showwarning("Erreur", "Veuillez entrer une URL valide.")
        return

    if "youtube.com" not in url and "youtu.be" not in url:
        messagebox.showwarning("Erreur", "Veuillez entrer un lien YouTube valide.")
        return

    try:
        os.makedirs(dossier_sortie, exist_ok=True)
    except OSError:
        pass

    if not os.path.isdir(dossier_sortie):
        messagebox.showwarning("Erreur", "Le dossier de sortie n'existe pas.")
        return

    threading.Thread(target=telecharger_video, args=(url, qualite, dossier_sortie), daemon=True).start()

def telecharger_video(url, qualite, dossier_sortie):
    safe_ui(bouton_telecharger.configure, state="disabled", text="Téléchargement...")
    safe_ui(progress_bar.set, 0)
    set_status("Analyse de la vidéo", WARNING)
    set_detail("Connexion à YouTube avec yt-dlp.")

    def progress_hook(data):
        status = data.get("status")

        if status == "downloading":
            total_bytes = data.get("total_bytes") or data.get("total_bytes_estimate")
            downloaded_bytes = data.get("downloaded_bytes", 0)

            if total_bytes:
                progress = min(downloaded_bytes / total_bytes, 1)
                speed = data.get("_speed_str", "").strip()
                safe_ui(progress_bar.set, progress)
                set_status("Téléchargement en cours", YOUTUBE_RED)
                set_detail(f"{format_size(downloaded_bytes)} / {format_size(total_bytes)} • {int(progress * 100)}% • {speed}")
            else:
                set_status("Téléchargement en cours", YOUTUBE_RED)
                set_detail(f"{format_size(downloaded_bytes)} reçus.")

        elif status == "finished":
            safe_ui(progress_bar.set, 1)
            set_status("Fusion audio/vidéo", WARNING)
            set_detail("ffmpeg prépare le fichier final.")

    ydl_opts = {
        "format": f"bestvideo[height<={qualite}]+bestaudio/best[height<={qualite}]/best",
        "outtmpl": os.path.join(dossier_sortie, "%(title).200s.%(ext)s"),
        "merge_output_format": "mp4",
        "progress_hooks": [progress_hook],
        "quiet": True,
        "no_warnings": True,
        "noplaylist": True,
    }

    ffmpeg_location = get_ffmpeg_location()
    if ffmpeg_location:
        ydl_opts["ffmpeg_location"] = ffmpeg_location

    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=True)
            filename = ydl.prepare_filename(info)

        if not filename.lower().endswith(".mp4"):
            base, _ = os.path.splitext(filename)
            mp4_filename = base + ".mp4"
            if os.path.exists(mp4_filename):
                filename = mp4_filename

        safe_ui(progress_bar.set, 1.0)
        set_status("Téléchargement terminé", SUCCESS)
        set_detail(f"Enregistré : {os.path.basename(filename)}")
        safe_ui(messagebox.showinfo, "Succès", f"Vidéo téléchargée ! 🎉\n\n{os.path.basename(filename)}")

    except Exception as error:
        set_status("Échec du téléchargement", ERROR)
        set_detail("Consulte le message d'erreur pour le détail.")
        safe_ui(messagebox.showerror, "Erreur", f"Échec :\n{explain_yt_dlp_error(error)}")

    finally:
        safe_ui(bouton_telecharger.configure, state="normal", text="Télécharger")

def coller_url():
    try:
        entree_url.delete(0, "end")
        entree_url.insert(0, fenetre.clipboard_get().strip())
        set_status("URL collée", SUCCESS)
        set_detail("Prêt à télécharger.")
    except Exception:
        messagebox.showwarning("Presse-papiers", "Impossible de lire le presse-papiers.")

def effacer_url():
    entree_url.delete(0, "end")
    progress_bar.set(0)
    set_status("Prêt", TEXT_MUTED)
    set_detail("Colle une URL YouTube pour commencer.")

def choisir_dossier():
    dossier = filedialog.askdirectory(initialdir=dossier_var.get() or os.getcwd())
    if dossier:
        dossier_var.set(dossier)

def set_fullscreen(enabled):
    fenetre.attributes("-fullscreen", enabled)
    if "bouton_plein_ecran" in globals():
        bouton_plein_ecran.configure(text="Mode fenêtre" if enabled else "Plein écran")

def basculer_plein_ecran(event=None):
    set_fullscreen(not bool(fenetre.attributes("-fullscreen")))

def quitter_plein_ecran(event=None):
    set_fullscreen(False)

def creer_icone_youtube(size=64):
    image = tk.PhotoImage(width=size, height=size)
    for y in range(size):
        for x in range(size):
            image.put("#0f0f0f", (x, y))

    left, top = 8, 15
    right, bottom = size - 8, size - 15
    radius = 11

    for y in range(top, bottom):
        for x in range(left, right):
            in_left_round = x < left + radius and y < top + radius and (x - left - radius) ** 2 + (y - top - radius) ** 2 > radius ** 2
            in_right_round = x >= right - radius and y < top + radius and (x - right + radius) ** 2 + (y - top - radius) ** 2 > radius ** 2
            in_bottom_left_round = x < left + radius and y >= bottom - radius and (x - left - radius) ** 2 + (y - bottom + radius) ** 2 > radius ** 2
            in_bottom_right_round = x >= right - radius and y >= bottom - radius and (x - right + radius) ** 2 + (y - bottom + radius) ** 2 > radius ** 2
            if not (in_left_round or in_right_round or in_bottom_left_round or in_bottom_right_round):
                image.put(YOUTUBE_RED, (x, y))

    triangle = [(27, 23), (27, 41), (43, 32)]
    for y in range(22, 43):
        for x in range(26, 45):
            x1, y1 = triangle[0]
            x2, y2 = triangle[1]
            x3, y3 = triangle[2]
            denominator = (y2 - y3) * (x1 - x3) + (x3 - x2) * (y1 - y3)
            a = ((y2 - y3) * (x - x3) + (x3 - x2) * (y - y3)) / denominator
            b = ((y3 - y1) * (x - x3) + (x1 - x3) * (y - y3)) / denominator
            c = 1 - a - b
            if a >= 0 and b >= 0 and c >= 0:
                image.put(WHITE, (x, y))

    return image

# ==================== INTERFACE GRAPHIQUE ====================

fenetre = ctk.CTk()
fenetre.title("YouTube Downloader")
fenetre.geometry("1200x760")
fenetre.minsize(980, 640)
fenetre.configure(fg_color=BG_COLOR)
fenetre.grid_columnconfigure(0, weight=0)
fenetre.grid_columnconfigure(1, weight=1)
fenetre.grid_rowconfigure(0, weight=1)
fenetre.bind("<F11>", basculer_plein_ecran)
fenetre.bind("<Escape>", quitter_plein_ecran)
app_icon = creer_icone_youtube()
fenetre.iconphoto(True, app_icon)

dossier_var = ctk.StringVar(value=get_default_output_dir())
qualite_var = ctk.StringVar(value="1080")

sidebar = ctk.CTkFrame(fenetre, fg_color=SIDEBAR_COLOR, corner_radius=0)
sidebar.grid(row=0, column=0, sticky="nsew")
sidebar.grid_rowconfigure(7, weight=1)

logo_card = ctk.CTkFrame(sidebar, fg_color=YOUTUBE_RED, corner_radius=10, width=72, height=50)
logo_card.grid(row=0, column=0, sticky="w", padx=28, pady=(34, 0))
logo_card.grid_propagate(False)

logo_play = ctk.CTkLabel(
    logo_card,
    text="▶",
    font=ctk.CTkFont(size=28, weight="bold"),
    text_color=WHITE,
)
logo_play.place(relx=0.54, rely=0.5, anchor="center")

marque_label = ctk.CTkLabel(
    sidebar,
    text="YouTube",
    font=ctk.CTkFont(size=28, weight="bold"),
    text_color=WHITE,
)
marque_label.grid(row=1, column=0, sticky="w", padx=28, pady=(16, 0))

nom_app_label = ctk.CTkLabel(
    sidebar,
    text="Downloader",
    font=ctk.CTkFont(size=20, weight="bold"),
    text_color=TEXT_SOFT,
)
nom_app_label.grid(row=2, column=0, sticky="w", padx=28, pady=(0, 4))

version_label = ctk.CTkLabel(
    sidebar,
    text=f"yt-dlp {get_current_ytdlp_version()}",
    font=ctk.CTkFont(size=12, weight="bold"),
    text_color=WHITE,
    fg_color=YOUTUBE_RED_SOFT,
    corner_radius=6,
    padx=10,
    pady=4,
)
version_label.grid(row=3, column=0, sticky="w", padx=28, pady=(10, 12))

bouton_maj_moteur = ctk.CTkButton(
    sidebar,
    text="🔄 Mettre à jour yt-dlp",
    command=lambda: lancer_mise_a_jour_moteur(interactive=True),
    width=190,
    height=34,
    font=ctk.CTkFont(size=12, weight="bold"),
    fg_color="#242424",
    hover_color="#333333",
    corner_radius=6,
)
bouton_maj_moteur.grid(row=4, column=0, sticky="ew", padx=28, pady=(0, 20))

sidebar_hint = ctk.CTkLabel(
    sidebar,
    text="F11 : plein écran\nÉchap : quitter le plein écran",
    font=ctk.CTkFont(size=13),
    text_color=TEXT_MUTED,
    justify="left",
)
sidebar_hint.grid(row=5, column=0, sticky="w", padx=28, pady=(0, 22))

bouton_plein_ecran = ctk.CTkButton(
    sidebar,
    text="Mode fenêtre",
    command=basculer_plein_ecran,
    width=190,
    height=42,
    fg_color=PANEL_ALT_COLOR,
    hover_color="#303030",
    corner_radius=8,
)
bouton_plein_ecran.grid(row=6, column=0, sticky="ew", padx=28, pady=(0, 12))

side_status = ctk.CTkFrame(sidebar, fg_color=PANEL_COLOR, corner_radius=8)
side_status.grid(row=7, column=0, sticky="new", padx=28, pady=(8, 0))

side_status_title = ctk.CTkLabel(
    side_status,
    text="Moteur",
    font=ctk.CTkFont(size=12, weight="bold"),
    text_color=TEXT_SOFT,
)
side_status_title.grid(row=0, column=0, sticky="w", padx=16, pady=(14, 2))

side_status_text = ctk.CTkLabel(
    side_status,
    text=f"yt-dlp v{get_current_ytdlp_version()}\nffmpeg fusionne audio + vidéo",
    font=ctk.CTkFont(size=12),
    text_color=TEXT_MUTED,
    justify="left",
)
side_status_text.grid(row=1, column=0, sticky="w", padx=16, pady=(0, 14))

main = ctk.CTkFrame(fenetre, fg_color=BG_COLOR, corner_radius=0)
main.grid(row=0, column=1, sticky="nsew")
main.grid_columnconfigure(0, weight=1)
main.grid_rowconfigure(1, weight=1)

header = ctk.CTkFrame(main, fg_color="transparent")
header.grid(row=0, column=0, sticky="ew", padx=38, pady=(34, 18))
header.grid_columnconfigure(0, weight=1)

page_title = ctk.CTkLabel(
    header,
    text="Télécharger une vidéo YouTube",
    font=ctk.CTkFont(size=34, weight="bold"),
    text_color=WHITE,
)
page_title.grid(row=0, column=0, sticky="w")

page_subtitle = ctk.CTkLabel(
    header,
    text="Colle un lien, choisis la qualité, lance le téléchargement. Le reste est automatique.",
    font=ctk.CTkFont(size=14),
    text_color=TEXT_MUTED,
)
page_subtitle.grid(row=1, column=0, sticky="w", pady=(4, 0))

content = ctk.CTkFrame(main, fg_color="transparent")
content.grid(row=1, column=0, sticky="nsew", padx=38, pady=(0, 34))
content.grid_columnconfigure(0, weight=3)
content.grid_columnconfigure(1, weight=2)
content.grid_rowconfigure(0, weight=1)

controls_panel = ctk.CTkFrame(
    content,
    fg_color=PANEL_COLOR,
    border_width=1,
    border_color=BORDER_COLOR,
    corner_radius=8,
)
controls_panel.grid(row=0, column=0, sticky="nsew", padx=(0, 18))
controls_panel.grid_columnconfigure(0, weight=1)

activity_panel = ctk.CTkFrame(
    content,
    fg_color=PANEL_COLOR,
    border_width=1,
    border_color=BORDER_COLOR,
    corner_radius=8,
)
activity_panel.grid(row=0, column=1, sticky="nsew")
activity_panel.grid_columnconfigure(0, weight=1)
activity_panel.grid_rowconfigure(5, weight=1)

label_url = ctk.CTkLabel(
    controls_panel,
    text="Lien YouTube",
    font=ctk.CTkFont(size=16, weight="bold"),
    text_color=WHITE,
)
label_url.grid(row=0, column=0, sticky="w", padx=26, pady=(26, 8))

url_frame = ctk.CTkFrame(controls_panel, fg_color="transparent")
url_frame.grid(row=1, column=0, sticky="ew", padx=26)
url_frame.grid_columnconfigure(0, weight=1)

entree_url = ctk.CTkEntry(
    url_frame,
    height=52,
    fg_color=INPUT_COLOR,
    border_color=BORDER_COLOR,
    text_color=WHITE,
    font=ctk.CTkFont(size=14),
    placeholder_text="https://www.youtube.com/watch?v=...",
)
entree_url.grid(row=0, column=0, sticky="ew", padx=(0, 10))

bouton_coller = ctk.CTkButton(
    url_frame,
    text="Coller",
    width=88,
    height=52,
    fg_color=PANEL_ALT_COLOR,
    hover_color="#303030",
    command=coller_url,
)
bouton_coller.grid(row=0, column=1, padx=(0, 8))

bouton_effacer = ctk.CTkButton(
    url_frame,
    text="Effacer",
    width=88,
    height=52,
    fg_color=PANEL_ALT_COLOR,
    hover_color="#303030",
    command=effacer_url,
)
bouton_effacer.grid(row=0, column=2)

quality_label = ctk.CTkLabel(
    controls_panel,
    text="Qualité maximale",
    font=ctk.CTkFont(size=16, weight="bold"),
    text_color=WHITE,
)
quality_label.grid(row=2, column=0, sticky="w", padx=26, pady=(28, 10))

qualite_segment = ctk.CTkSegmentedButton(
    controls_panel,
    values=["360", "480", "720", "1080", "1440", "2160"],
    variable=qualite_var,
    height=42,
    selected_color=YOUTUBE_RED,
    selected_hover_color=YOUTUBE_RED_DARK,
    unselected_color=PANEL_ALT_COLOR,
    unselected_hover_color="#303030",
    text_color=WHITE,
)
qualite_segment.grid(row=3, column=0, sticky="ew", padx=26)
qualite_segment.set("1080")

output_label = ctk.CTkLabel(
    controls_panel,
    text="Dossier de sortie",
    font=ctk.CTkFont(size=16, weight="bold"),
    text_color=WHITE,
)
output_label.grid(row=4, column=0, sticky="w", padx=26, pady=(28, 10))

dossier_frame = ctk.CTkFrame(controls_panel, fg_color="transparent")
dossier_frame.grid(row=5, column=0, sticky="ew", padx=26)
dossier_frame.grid_columnconfigure(0, weight=1)

entree_dossier = ctk.CTkEntry(
    dossier_frame,
    textvariable=dossier_var,
    height=46,
    fg_color=INPUT_COLOR,
    border_color=BORDER_COLOR,
    text_color=TEXT_SOFT,
    font=ctk.CTkFont(size=13),
)
entree_dossier.grid(row=0, column=0, sticky="ew", padx=(0, 10))

bouton_dossier = ctk.CTkButton(
    dossier_frame,
    text="Parcourir",
    width=116,
    height=46,
    fg_color=PANEL_ALT_COLOR,
    hover_color="#303030",
    command=choisir_dossier,
)
bouton_dossier.grid(row=0, column=1)

bouton_telecharger = ctk.CTkButton(
    controls_panel,
    text="Télécharger",
    command=lancer_telechargement,
    height=56,
    font=ctk.CTkFont(size=17, weight="bold"),
    fg_color=YOUTUBE_RED,
    hover_color=YOUTUBE_RED_DARK,
    corner_radius=8,
)
bouton_telecharger.grid(row=6, column=0, sticky="ew", padx=26, pady=(34, 26))

activity_title = ctk.CTkLabel(
    activity_panel,
    text="Activité",
    font=ctk.CTkFont(size=22, weight="bold"),
    text_color=WHITE,
)
activity_title.grid(row=0, column=0, sticky="w", padx=24, pady=(26, 4))

activity_subtitle = ctk.CTkLabel(
    activity_panel,
    text="État du téléchargement en temps réel",
    font=ctk.CTkFont(size=13),
    text_color=TEXT_MUTED,
)
activity_subtitle.grid(row=1, column=0, sticky="w", padx=24, pady=(0, 22))

status_frame = ctk.CTkFrame(activity_panel, fg_color=INPUT_COLOR, corner_radius=8)
status_frame.grid(row=2, column=0, sticky="ew", padx=24)
status_frame.grid_columnconfigure(0, weight=1)

label_status = ctk.CTkLabel(
    status_frame,
    text="Prêt",
    font=ctk.CTkFont(size=18, weight="bold"),
    text_color=TEXT_MUTED,
)
label_status.grid(row=0, column=0, sticky="w", padx=18, pady=(18, 2))

label_detail = ctk.CTkLabel(
    status_frame,
    text="Colle une URL YouTube pour commencer.",
    font=ctk.CTkFont(size=13),
    text_color=TEXT_MUTED,
    anchor="w",
    justify="left",
    wraplength=360,
)
label_detail.grid(row=1, column=0, sticky="ew", padx=18, pady=(0, 16))

progress_bar = ctk.CTkProgressBar(status_frame, mode="determinate", height=10, progress_color=YOUTUBE_RED)
progress_bar.set(0)
progress_bar.grid(row=2, column=0, sticky="ew", padx=18, pady=(0, 18))

info_panel = ctk.CTkFrame(activity_panel, fg_color=PANEL_ALT_COLOR, corner_radius=8)
info_panel.grid(row=3, column=0, sticky="ew", padx=24, pady=(18, 0))

info_title = ctk.CTkLabel(
    info_panel,
    text="Sortie",
    font=ctk.CTkFont(size=13, weight="bold"),
    text_color=TEXT_SOFT,
)
info_title.grid(row=0, column=0, sticky="w", padx=18, pady=(16, 2))

info_text = ctk.CTkLabel(
    info_panel,
    text="Les fichiers sont enregistrés dans le dossier choisi. Le nom final vient du titre YouTube.",
    font=ctk.CTkFont(size=12),
    text_color=TEXT_MUTED,
    justify="left",
    wraplength=340,
)
info_text.grid(row=1, column=0, sticky="w", padx=18, pady=(0, 16))

warning_panel = ctk.CTkFrame(activity_panel, fg_color=YOUTUBE_RED_SOFT, corner_radius=8)
warning_panel.grid(row=4, column=0, sticky="ew", padx=24, pady=(14, 0))

warning_text = ctk.CTkLabel(
    warning_panel,
    text="Certaines vidéos peuvent demander une connexion ou une version à jour de yt-dlp.",
    font=ctk.CTkFont(size=12),
    text_color="#ffb3bd",
    justify="left",
    wraplength=340,
)
warning_text.grid(row=0, column=0, sticky="w", padx=18, pady=14)

footer = ctk.CTkFrame(activity_panel, fg_color="transparent")
footer.grid(row=6, column=0, sticky="sew", padx=24, pady=(0, 24))
footer.grid_columnconfigure(0, weight=1)

quit_button = ctk.CTkButton(
    footer,
    text="Quitter",
    command=fenetre.destroy,
    height=42,
    fg_color=PANEL_ALT_COLOR,
    hover_color="#303030",
    corner_radius=8,
)
quit_button.grid(row=0, column=0, sticky="ew")

set_fullscreen(True)

# Vérification silencieuse et automatique des mises à jour 1.5 seconde après le lancement
fenetre.after(1500, lambda: lancer_mise_a_jour_moteur(interactive=False))

fenetre.mainloop()

