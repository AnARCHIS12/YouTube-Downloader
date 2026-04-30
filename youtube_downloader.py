import customtkinter as ctk
from tkinter import messagebox, filedialog
import threading
import os
import requests
import re

# ==================== CONFIGURATION ====================
ctk.set_appearance_mode("Dark")
ctk.set_default_color_theme("blue")

# Liste d'instances publiques Cobalt (serveurs qui téléchargent pour nous)
COBALT_INSTANCES = [
    "https://api.cobalt.tools",
    "https://cobalt-api.kwiatekmiki.com",
    "https://cobalt.api.timelessnesses.me",
]

# ==================== LOGIQUE DE TÉLÉCHARGEMENT ====================

def get_working_instance():
    """Trouve une instance Cobalt qui fonctionne."""
    for url in COBALT_INSTANCES:
        try:
            r = requests.get(url, timeout=5, headers={"Accept": "application/json"})
            if r.status_code in (200, 302, 405):  # L'API répond
                return url
        except Exception:
            continue
    return None

def download_with_cobalt(video_url, quality="1080"):
    """Télécharge une vidéo via l'API Cobalt (sans navigateur, sans cookies)."""
    
    instance = get_working_instance()
    if not instance:
        return None, "Aucun serveur Cobalt disponible. Réessayez plus tard."
    
    headers = {
        "Accept": "application/json",
        "Content-Type": "application/json",
    }
    
    payload = {
        "url": video_url,
        "videoQuality": quality,
        "filenameStyle": "pretty",
    }
    
    try:
        response = requests.post(instance, json=payload, headers=headers, timeout=30)
        data = response.json()
        
        status = data.get("status", "")
        
        if status == "tunnel" or status == "redirect":
            download_url = data.get("url", "")
            filename = data.get("filename", "video.mp4")
            if not download_url:
                return None, "URL de téléchargement vide"
            return download_url, filename
        
        elif status == "picker":
            # Plusieurs options (ex: vidéo + audio séparés)
            items = data.get("picker", [])
            if items:
                download_url = items[0].get("url", "")
                filename = "video.mp4"
                return download_url, filename
            return None, "Aucun flux disponible"
        
        elif status == "error":
            error_code = data.get("error", {}).get("code", "unknown")
            error_msg = {
                "error.api.youtube.decipher": "YouTube a changé son chiffrement. Réessayez plus tard.",
                "error.api.content.video.unavailable": "Cette vidéo est indisponible.",
                "error.api.fetch.critical": "Erreur serveur. Réessayez.",
                "error.api.content.post.unavailable": "Contenu indisponible.",
            }.get(error_code, f"Erreur Cobalt : {error_code}")
            return None, error_msg
        
        else:
            return None, f"Réponse inattendue : {data}"
            
    except requests.Timeout:
        return None, "Délai d'attente dépassé. Réessayez."
    except Exception as e:
        return None, f"Erreur réseau : {e}"

def download_file(url, filename, progress_callback=None):
    """Télécharge le fichier depuis l'URL vers le dossier courant."""
    # Nettoyer le nom de fichier
    filename = re.sub(r'[<>:"/\\|?*]', '', filename)
    if not filename:
        filename = "video.mp4"
    
    filepath = os.path.join(os.getcwd(), filename)
    
    try:
        response = requests.get(url, stream=True, timeout=120)
        response.raise_for_status()
        
        total_size = int(response.headers.get('content-length', 0))
        downloaded = 0
        
        with open(filepath, 'wb') as f:
            for chunk in response.iter_content(chunk_size=8192):
                if chunk:
                    f.write(chunk)
                    downloaded += len(chunk)
                    if progress_callback and total_size > 0:
                        progress = downloaded / total_size
                        progress_callback(progress, downloaded, total_size)
        
        return filepath
    except Exception as e:
        # Supprimer le fichier partiel
        if os.path.exists(filepath):
            os.remove(filepath)
        raise e

def format_size(bytes_size):
    """Formate une taille en octets en format lisible."""
    for unit in ['o', 'Ko', 'Mo', 'Go']:
        if bytes_size < 1024:
            return f"{bytes_size:.1f} {unit}"
        bytes_size /= 1024
    return f"{bytes_size:.1f} To"

# ==================== INTERFACE ====================

def lancer_telechargement():
    url = entree_url.get().strip()
    qualite = combo_qualite.get()
    
    if not url:
        messagebox.showwarning("Erreur", "Veuillez entrer une URL valide.")
        return
    
    if "youtube.com" not in url and "youtu.be" not in url:
        messagebox.showwarning("Erreur", "Veuillez entrer un lien YouTube valide.")
        return
    
    threading.Thread(target=telecharger_video, args=(url, qualite), daemon=True).start()

def telecharger_video(url, qualite):
    bouton_telecharger.configure(state="disabled", text="⏳ En cours...")
    progress_bar.set(0)
    progress_bar.pack(pady=(0, 5), padx=25, fill="x")
    
    # Étape 1 : Demander le lien de téléchargement à Cobalt
    label_status.configure(text="🔍 Analyse de la vidéo...", text_color="#facc15")
    
    download_url, result = download_with_cobalt(url, qualite)
    
    if not download_url:
        label_status.configure(text=f"❌ {result}", text_color="#f87171")
        messagebox.showerror("Erreur", result)
        bouton_telecharger.configure(state="normal", text="⬇ Télécharger")
        progress_bar.pack_forget()
        return
    
    filename = result  # Le 2ème retour est le nom du fichier si succès
    
    # Étape 2 : Télécharger le fichier
    label_status.configure(text="⬇ Téléchargement en cours...", text_color="#60a5fa")
    
    def on_progress(progress, downloaded, total):
        progress_bar.set(progress)
        label_status.configure(
            text=f"⬇ {format_size(downloaded)} / {format_size(total)} ({int(progress*100)}%)",
            text_color="#60a5fa"
        )
    
    try:
        filepath = download_file(download_url, filename, on_progress)
        progress_bar.set(1.0)
        label_status.configure(text=f"✅ Enregistré : {os.path.basename(filepath)}", text_color="#4ade80")
        messagebox.showinfo("Succès", f"Vidéo téléchargée ! 🎉\n\n{os.path.basename(filepath)}")
    except Exception as e:
        label_status.configure(text="❌ Échec du téléchargement", text_color="#f87171")
        messagebox.showerror("Erreur", f"Échec du téléchargement :\n{e}")
    finally:
        bouton_telecharger.configure(state="normal", text="⬇ Télécharger")
        progress_bar.pack_forget()

# ==================== INTERFACE GRAPHIQUE ====================

fenetre = ctk.CTk()
fenetre.title("Téléchargeur YouTube")
fenetre.geometry("540x380")
fenetre.resizable(False, False)

# Titre
titre_label = ctk.CTkLabel(
    fenetre, text="⬇ Téléchargeur YouTube",
    font=ctk.CTkFont(size=24, weight="bold")
)
titre_label.pack(pady=(20, 5))

sous_titre = ctk.CTkLabel(
    fenetre, text="Sans navigateur • Sans cookies • 100% automatique",
    font=ctk.CTkFont(size=13), text_color="#94a3b8"
)
sous_titre.pack(pady=(0, 10))

# Cadre principal
cadre = ctk.CTkFrame(fenetre, corner_radius=12)
cadre.pack(pady=10, padx=25, fill="both", expand=True)

# URL
label_url = ctk.CTkLabel(cadre, text="🔗  Lien de la vidéo", font=ctk.CTkFont(size=13, weight="bold"))
label_url.pack(pady=(15, 3), anchor="w", padx=20)

entree_url = ctk.CTkEntry(
    cadre, width=420, height=38,
    placeholder_text="https://www.youtube.com/watch?v=..."
)
entree_url.pack(pady=(0, 10), padx=20)

# Qualité
frame_qualite = ctk.CTkFrame(cadre, fg_color="transparent")
frame_qualite.pack(pady=(0, 15), padx=20, fill="x")

label_qualite = ctk.CTkLabel(frame_qualite, text="🎬  Qualité :", font=ctk.CTkFont(size=13, weight="bold"))
label_qualite.pack(side="left")

combo_qualite = ctk.CTkComboBox(
    frame_qualite, values=["2160", "1440", "1080", "720", "480", "360"],
    state="readonly", width=100
)
combo_qualite.set("1080")
combo_qualite.pack(side="left", padx=10)

label_qualite_info = ctk.CTkLabel(frame_qualite, text="pixels", font=ctk.CTkFont(size=12), text_color="#64748b")
label_qualite_info.pack(side="left")

# Barre de statut
label_status = ctk.CTkLabel(
    fenetre, text="Prêt — aucun navigateur requis ✨", font=ctk.CTkFont(size=12),
    text_color="#94a3b8"
)
label_status.pack(pady=(5, 0))

# Barre de progression (cachée par défaut)
progress_bar = ctk.CTkProgressBar(fenetre, mode="determinate")
progress_bar.set(0)

# Bouton Télécharger
bouton_telecharger = ctk.CTkButton(
    fenetre, text="⬇ Télécharger",
    command=lancer_telechargement, height=45,
    font=ctk.CTkFont(size=15, weight="bold"),
    corner_radius=10
)
bouton_telecharger.pack(pady=(8, 20), padx=25, fill="x")

fenetre.mainloop()
