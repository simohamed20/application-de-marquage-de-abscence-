import os
import sqlite3
import tkinter as tk
from tkinter import messagebox, filedialog
from PIL import Image, ImageTk
import cv2
import face_recognition

# Configuration de l'application Tkinter
root = tk.Tk()
root.title("Application de Marquage de Présence")
root.geometry("600x400")

# Couleurs et styles
bg_color = "#f0f0f0"
primary_color = "#0066cc"
secondary_color = "#cc0000"
font_primary = ("Arial", 12)
font_title = ("Arial", 20, "bold")

# Configurer la couleur de fond de l'application
root.configure(bg=bg_color)

UPLOAD_FOLDER = 'data/photos'

# Création du dossier pour stocker les photos si nécessaire
if not os.path.exists(UPLOAD_FOLDER):
    os.makedirs(UPLOAD_FOLDER)

# Connexion à la base de données SQLite
conn = sqlite3.connect('data/students.db', check_same_thread=False)
c = conn.cursor()

# Création de la table des étudiants
c.execute('''
CREATE TABLE IF NOT EXISTS students (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    nom TEXT NOT NULL,
    prenom TEXT NOT NULL,
    code_massar TEXT NOT NULL,
    email TEXT NOT NULL,
    telephone TEXT NOT NULL,
    photo_filename TEXT NOT NULL
)
''')
conn.commit()

# Fonction pour vérifier si un fichier est autorisé
def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in {'png', 'jpg', 'jpeg'}

# Fonction pour basculer entre les pages
def show_frame(frame):
    frame.tkraise()

# Fonction pour l'inscription
def inscription():
    def enregistrer_etudiant():
        nom = entry_nom.get()
        prenom = entry_prenom.get()
        code_massar = entry_code_massar.get()
        email = entry_email.get()
        telephone = entry_telephone.get()
        photo_path = entry_photo.get()

        if allowed_file(photo_path):
            filename = os.path.basename(photo_path)
            destination = os.path.join(UPLOAD_FOLDER, filename)
            os.rename(photo_path, destination)

            c.execute(
                "INSERT INTO students (nom, prenom, code_massar, email, telephone, photo_filename) VALUES (?, ?, ?, ?, ?, ?)",
                (nom, prenom, code_massar, email, telephone, filename))
            conn.commit()
            messagebox.showinfo("Succès", "Étudiant enregistré avec succès!")
            show_frame(main_frame)
        else:
            messagebox.showerror("Erreur", "Format de fichier non autorisé!")

    tk.Label(inscription_frame, text="Nom:", bg=bg_color, font=font_primary).grid(row=0, column=0, sticky="w", padx=10, pady=5)
    entry_nom = tk.Entry(inscription_frame, font=font_primary)
    entry_nom.grid(row=0, column=1, pady=5)

    tk.Label(inscription_frame, text="Prénom:", bg=bg_color, font=font_primary).grid(row=1, column=0, sticky="w", padx=10, pady=5)
    entry_prenom = tk.Entry(inscription_frame, font=font_primary)
    entry_prenom.grid(row=1, column=1, pady=5)

    tk.Label(inscription_frame, text="Code Massar:", bg=bg_color, font=font_primary).grid(row=2, column=0, sticky="w", padx=10, pady=5)
    entry_code_massar = tk.Entry(inscription_frame, font=font_primary)
    entry_code_massar.grid(row=2, column=1, pady=5)

    tk.Label(inscription_frame, text="Email:", bg=bg_color, font=font_primary).grid(row=3, column=0, sticky="w", padx=10, pady=5)
    entry_email = tk.Entry(inscription_frame, font=font_primary)
    entry_email.grid(row=3, column=1, pady=5)

    tk.Label(inscription_frame, text="Numéro de téléphone:", bg=bg_color, font=font_primary).grid(row=4, column=0, sticky="w", padx=10, pady=5)
    entry_telephone = tk.Entry(inscription_frame, font=font_primary)
    entry_telephone.grid(row=4, column=1, pady=5)

    tk.Label(inscription_frame, text="Photo:", bg=bg_color, font=font_primary).grid(row=5, column=0, sticky="w", padx=10, pady=5)
    entry_photo = tk.Entry(inscription_frame, font=font_primary)
    entry_photo.grid(row=5, column=1, pady=5)
    tk.Button(inscription_frame, text="Parcourir", command=lambda: entry_photo.insert(0, filedialog.askopenfilename()), font=font_primary).grid(row=5, column=2, padx=10, pady=5)

    tk.Button(inscription_frame, text="Enregistrer", command=enregistrer_etudiant, bg=secondary_color, fg="white", font=font_primary).grid(row=6, columnspan=3, pady=10)
    tk.Button(inscription_frame, text="Retour", command=lambda: show_frame(main_frame), font=font_primary).grid(row=7, columnspan=3, pady=5)

# Fonction pour la connexion
def connexion():
    known_face_encodings = []
    known_face_metadata = []

    c.execute("SELECT nom, prenom, photo_filename FROM students")
    rows = c.fetchall()

    for row in rows:
        nom, prenom, photo_filename = row
        photo_path = os.path.join(UPLOAD_FOLDER, photo_filename)
        image = face_recognition.load_image_file(photo_path)
        face_encoding = face_recognition.face_encodings(image)[0]
        known_face_encodings.append(face_encoding)
        known_face_metadata.append((nom, prenom))

    def video_loop():
        ret, frame = video_capture.read()
        if ret:
            # Redimensionner la frame à la moitié de sa taille originale
            frame = cv2.resize(frame, (0, 0), fx=0.5, fy=0.5)
            rgb_frame = frame[:, :, ::-1]
            face_locations = face_recognition.face_locations(rgb_frame)
            face_encodings = face_recognition.face_encodings(rgb_frame, face_locations)

            for (top, right, bottom, left), face_encoding in zip(face_locations, face_encodings):
                matches = face_recognition.compare_faces(known_face_encodings, face_encoding)

                if True in matches:
                    first_match_index = matches.index(True)
                    nom, prenom = known_face_metadata[first_match_index]
                    cv2.rectangle(frame, (left, top), (right, bottom), (0, 255, 0), 2)
                    cv2.putText(frame, f"Bonjour {nom} {prenom}", (left + 6, bottom - 6), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 255), 1)
                else:
                    cv2.rectangle(frame, (left, top), (right, bottom), (0, 0, 255), 2)
                    cv2.putText(frame, "Inconnu", (left + 6, bottom - 6), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 255), 1)

            cv2_image = cv2.cvtColor(frame, cv2.COLOR_BGR2RGBA)
            img = Image.fromarray(cv2_image)
            imgtk = ImageTk.PhotoImage(image=img)
            lmain.imgtk = imgtk
            lmain.configure(image=imgtk)
        lmain.after(10, video_loop)

    video_capture = cv2.VideoCapture(0)
    video_frame = tk.Frame(connexion_frame, bg=bg_color)
    video_frame.pack(padx=10, pady=10)
    lmain = tk.Label(video_frame)
    lmain.pack()

    tk.Button(connexion_frame, text="Retour", command=lambda: [video_capture.release(), show_frame(main_frame)], font=font_primary).pack(pady=10)

    video_loop()

# Création des frames pour chaque page
main_frame = tk.Frame(root, bg=bg_color)
inscription_frame = tk.Frame(root, bg=bg_color)
connexion_frame = tk.Frame(root, bg=bg_color)

for frame in (main_frame, inscription_frame, connexion_frame):
    frame.grid(row=0, column=0, sticky='nsew')

# Interface principale
tk.Label(main_frame, text="BTS-SIDI-KACEM", font=font_title, bg=bg_color).pack(pady=20)

# Centrage des boutons et ajout du logo
button_logo_frame = tk.Frame(main_frame, bg=bg_color)
button_logo_frame.pack(expand=True)

button_frame = tk.Frame(button_logo_frame, bg=bg_color)
button_frame.pack(side=tk.LEFT, padx=20)

tk.Button(button_frame, text="Inscription", command=lambda: show_frame(inscription_frame), font=font_primary, bg=secondary_color, fg="white").pack(pady=10, fill=tk.X)
tk.Button(button_frame, text="Connexion", command=lambda: [show_frame(connexion_frame), connexion()], font=font_primary, bg=primary_color, fg="white").pack(pady=10, fill=tk.X)

# Ajout du logo
logo_path = "C:/Users\Pc\Desktop\pfe_final\logo/vt.png"  # Remplacez par le chemin réel de l'image du logo
logo_image = Image.open(logo_path)
logo_image = logo_image.resize((100, 100), Image.Resampling.LANCZOS)  # Utilisation de Image.Resampling.LANCZOS
logo_photo = ImageTk.PhotoImage(logo_image)
logo_label = tk.Label(button_logo_frame, image=logo_photo, bg=bg_color)
logo_label.pack(side=tk.RIGHT, padx=20)

# Appel de la fonction inscription pour initialiser le formulaire
inscription()

# Affichage de la frame principale au démarrage
show_frame(main_frame)

root.mainloop()
