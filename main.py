import tkinter as tk
from tkinter import ttk, simpledialog, messagebox
import cv2, face_recognition, os, pickle, requests
from PIL import Image, ImageTk
from datetime import datetime
import cloudinary.uploader
import firebase_admin
from firebase_admin import credentials, firestore, messaging, auth
from utils import HoverButton, load_known_faces, save_encodings

cred = credentials.Certificate("fireKey/[your-firebase-credentials].json")
firebase_admin.initialize_app(cred)
db = firestore.client()

cloudinary.config(
    cloud_name="[your-cloudinary-cloud-name]",
    api_key="[your-cloudinary-api-key]",
    api_secret="[your-cloudinary-api-secret]"
)

BG_COLOR, FG_COLOR, ACCENT_COLOR = "#263238", "#ECEFF1", "#26A69A"
BUTTON_HOVER_COLOR, FONT = "#00796B", ("Segoe UI", 11)
KNOWN_DIR, ENC_FILE = 'known_faces', 'known_faces_encodings.pkl'
TOLERANCE, FRAME_REDUCE, IMAGE_COUNT = 0.5, 0.25, 7
MODEL = 'hog'  # Use 'hog' if no GPU

class FaceApp:
    FIREBASE_API_KEY = "[YOUR_FIREBASE_API_KEY]"

    def __init__(self, root):
        self.root = root
        self.root.title("Face Recognition Door System")
        self.root.geometry("900x600")
        self.setup_styles()

        self.known_faces, self.known_names = load_known_faces(KNOWN_DIR, ENC_FILE)
        self.video = cv2.VideoCapture(0)
        self.admin_uid = None

        self.setup_ui()
        self.update_frame()

    def setup_styles(self):
        s = ttk.Style()
        s.theme_use('clam')
        s.configure("TFrame", background=BG_COLOR)
        s.configure("TLabel", background=BG_COLOR, foreground=FG_COLOR, font=FONT)
        s.configure("Accent.TButton", background=ACCENT_COLOR, foreground=FG_COLOR, font=FONT, padding=10)
        s.map("Accent.TButton", background=[('active', BUTTON_HOVER_COLOR)])
        s.configure("Hover.TButton", background=BUTTON_HOVER_COLOR, foreground=FG_COLOR, font=FONT, padding=10)

    def setup_ui(self):
        main = ttk.Frame(self.root)
        main.pack(fill="both", expand=True, padx=20, pady=20)

        sidebar = ttk.Frame(main, width=200)
        sidebar.pack(side="left", fill="y")

        video_frame = ttk.Frame(main)
        video_frame.pack(side="right", fill="both", expand=True)

        self.label = tk.Label(video_frame, bg="black")
        self.label.pack(expand=True, fill="both", padx=10, pady=10)

        self.status = ttk.Label(sidebar, text="🔒 Awaiting...", font=(FONT[0], 14, "bold"),
                                 foreground=ACCENT_COLOR, background=BG_COLOR, wraplength=180)
        self.status.pack(pady=(0, 30), padx=5)

        HoverButton(sidebar, text="✨ Admin Login", command=self.admin_login, width=18).pack(pady=10)
        self.reg_btn = HoverButton(sidebar, text="➕ Register Face", command=self.sign_in, width=18, state="disabled")
        self.reg_btn.pack(pady=10)
        HoverButton(sidebar, text="🚪 Open Door", command=self.open_door, width=18).pack(pady=10)
        HoverButton(sidebar, text="📜 View Logs", command=self.show_access_log, width=18).pack(pady=10)
        HoverButton(sidebar, text="🗑 Manage Users", command=self.manage_users, width=18).pack(pady=10)
        HoverButton(sidebar, text="❌ Quit", command=self.close, width=18).pack(pady=30)

    def admin_login(self):
        email = simpledialog.askstring("Admin Login", "Email:", parent=self.root)
        pwd = simpledialog.askstring("Admin Login", "Password:", show="*", parent=self.root)
        if not email or not pwd:
            return

        try:
            url = f"https://identitytoolkit.googleapis.com/v1/accounts:signInWithPassword?key={self.FIREBASE_API_KEY}"
            payload = {"email": email, "password": pwd, "returnSecureToken": True}
            response = requests.post(url, json=payload)
            response.raise_for_status()
            user_data = response.json()
            self.admin_uid = user_data["localId"]
            messagebox.showinfo("Success", "Admin authenticated.", parent=self.root)
            self.reg_btn.config(state="normal")
        except requests.exceptions.HTTPError:
            error_msg = response.json().get("error", {}).get("message", "Login failed.")
            messagebox.showerror("Denied", f"Invalid credentials: {error_msg}", parent=self.root)

    def update_frame(self):
        ret, frame = self.video.read()
        if ret:
            rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            imgtk = ImageTk.PhotoImage(Image.fromarray(rgb))
            self.label.imgtk = imgtk
            self.label.config(image=imgtk)
        self.root.after(10, self.update_frame)

    def sign_in(self):
        if not self.admin_uid:
            messagebox.showwarning("Not Authorized", "Please login first.", parent=self.root)
            return
        name = simpledialog.askstring("Register", "Person's name:", parent=self.root)
        if not name:
            return
        path = os.path.join(KNOWN_DIR, name)
        if os.path.exists(path):
            messagebox.showinfo("Duplicate", f"{name} already exists.", parent=self.root)
            return
        os.makedirs(path, exist_ok=True)
        self.capture_count, self.person_dir = 0, path
        self.status.config(text=f"Capturing {IMAGE_COUNT} images…")
        self.capture_images()

    def capture_images(self):
        if self.capture_count < IMAGE_COUNT:
            ret, frame = self.video.read()
            if ret:
                small_frame = cv2.resize(frame, (0, 0), fx=FRAME_REDUCE, fy=FRAME_REDUCE)
                rgb_small = cv2.cvtColor(small_frame, cv2.COLOR_BGR2RGB)
                face_locations = face_recognition.face_locations(rgb_small, model=MODEL)
                if face_locations:
                    cv2.imwrite(os.path.join(self.person_dir, f"{self.capture_count}.jpg"), frame)
                    self.capture_count += 1
                    self.status.config(text=f"Captured {self.capture_count}/{IMAGE_COUNT}")
                else:
                    self.status.config(text="Face not detected, retrying…")
            self.root.after(500, self.capture_images)
        else:
            self.status.config(text="Encoding data…")
            self.encode_faces()

    def encode_faces(self):
        new_faces, new_names = [], []
        for f in os.listdir(self.person_dir):
            img = face_recognition.load_image_file(os.path.join(self.person_dir, f))
            enc = face_recognition.face_encodings(img)
            if enc:
                new_faces.append(enc[0])
                new_names.append(os.path.basename(self.person_dir))
        if new_faces:
            self.known_faces += new_faces
            self.known_names += new_names
            save_encodings(self.known_faces, self.known_names, ENC_FILE)
            self.status.config(text=f"{new_names[0]} registered.")
        else:
            self.status.config(text="Encoding failed.")

    def open_door(self):
        self.status.config(text="Scanning…")
        self.root.update()
        unknown_frames, last_unknown, triggered = 0, None, False
        for _ in range(200):
            ret, frame = self.video.read()
            if not ret:
                continue
            sf = cv2.resize(frame, (0, 0), fx=FRAME_REDUCE, fy=FRAME_REDUCE)
            rgb = cv2.cvtColor(sf, cv2.COLOR_BGR2RGB)
            locs = face_recognition.face_locations(rgb, model=MODEL)
            encs = face_recognition.face_encodings(rgb, locs)
            if not encs:
                self.status.config(text="No face…")
                unknown_frames = 0
                continue

            recognized = False
            for enc in encs:
                dists = face_recognition.face_distance(self.known_faces, enc)
                if dists.size == 0:
                    continue
                idx = dists.argmin()
                if dists[idx] < TOLERANCE:
                    name = self.known_names[idx]
                    self.status.config(text=f"Welcome {name} ✅")
                    self.log_access(name, frame, True)
                    recognized = True
                    break

            if recognized:
                break

            unknown_frames += 1
            last_unknown = frame.copy()
            self.status.config(text=f"Unknown {unknown_frames}/10")

            if unknown_frames >= 10 and not triggered:
                self.status.config(text="🚨 ALERT!")
                self.log_access("Unknown", last_unknown, False)
                self.send_alert(last_unknown)
                triggered = True
        if not triggered and unknown_frames > 0:
            self.status.config(text="Not recognized.")

    def log_access(self, name, frame, success):
        ts = datetime.now().isoformat()
        fname = f"{name}_{ts.replace(':','_')}.jpg"
        os.makedirs("temp", exist_ok=True)
        temp_path = os.path.join("temp", fname)
        cv2.imwrite(temp_path, frame)
        url = cloudinary.uploader.upload(temp_path).get("secure_url", "")
        db.collection("access_logs").add({"name": name, "time": ts, "image_url": url, "success": success})
        if success and name != "Unknown":
            msg = messaging.Message(
                notification=messaging.Notification(title="Door Opened", body=f"{name} entered."),
                topic="entry_notifications"
            )
            messaging.send(msg)
        os.remove(temp_path)

    def send_alert(self, frame):
        alert_path = "alert.jpg"
        cv2.imwrite(alert_path, frame)
        url = cloudinary.uploader.upload(alert_path).get("secure_url", "")
        msg = messaging.Message(
            notification=messaging.Notification(title="🔐 Security Alert", body="Unknown entry attempt.", image=url),
            topic="intruder_alerts"
        )
        messaging.send(msg)
        os.remove(alert_path)

    def show_access_log(self):
        logs = db.collection("access_logs").order_by("time", direction=firestore.Query.DESCENDING).limit(10).stream()
        txt = "\n".join(
            f"{log.to_dict()['time'][:19]} | {log.to_dict()['name']} | {'✔' if log.to_dict()['success'] else '❌'}"
            for log in logs
        )
        messagebox.showinfo("Access Logs", txt or "No logs yet.", parent=self.root)

    def manage_users(self):
        if not self.admin_uid:
            messagebox.showwarning("Unauthorized", "Only admins can delete users.", parent=self.root)
            return
        name = simpledialog.askstring("Delete User", "Enter name to delete:", parent=self.root)
        if name and name in self.known_names:
            idxs = [i for i, n in enumerate(self.known_names) if n == name]
            self.known_faces = [f for i, f in enumerate(self.known_faces) if i not in idxs]
            self.known_names = [n for n in self.known_names if n != name]
            save_encodings(self.known_faces, self.known_names, ENC_FILE)
            path = os.path.join(KNOWN_DIR, name)
            if os.path.isdir(path):
                for f in os.listdir(path):
                    os.remove(os.path.join(path, f))
                os.rmdir(path)
            messagebox.showinfo("Deleted", f"{name} has been removed.", parent=self.root)
        else:
            messagebox.showerror("Error", "User not found.", parent=self.root)

    def close(self):
        self.video.release()
        self.root.destroy()

if __name__ == "__main__":
    root = tk.Tk()
    FaceApp(root)
    root.mainloop()
