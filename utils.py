import os, pickle
import tkinter as tk
from tkinter import ttk

class HoverButton(ttk.Button):
    def __init__(self, master=None, **kw):
        super().__init__(master=master, **kw)
        self.default, self.hover = "Accent.TButton", "Hover.TButton"
        self.config(style=self.default)
        self.bind("<Enter>", lambda e: self.config(style=self.hover))
        self.bind("<Leave>", lambda e: self.config(style=self.default))

def load_known_faces(known_dir, enc_file):
    if os.path.exists(enc_file):
        with open(enc_file,'rb') as f:
            return pickle.load(f)
    os.makedirs(known_dir, exist_ok=True)
    return [], []

def save_encodings(kfs, kns, enc_file):
    with open(enc_file,'wb') as f:
        pickle.dump((kfs, kns), f)
