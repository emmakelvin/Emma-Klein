import tkinter as tk
import re 
from tkinter import messagebox, filedialog, PhotoImage
import shutil, os
import sys
from datetime import date

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
ASSETS_DIR = os.path.join(BASE_DIR, "assests")
ICON_ico = os.path.join(ASSETS_DIR, "jams.ico")
ICON_PNG = os.path.join(ASSETS_DIR, "jams.png")

def apply_icon(window, title="Job Application Management System"):
    icon_set = False
    
    #----windows: use .ico best for taskbar
    if sys.platform.startswith("win") and os.path.exists(ICON_ico):
        try:
            window.iconbitmap(ICON_ico)
            icon_set = True
        except Exception:
            pass
    
    #----- cross-platform: use .png via pillow
    if os.path.exists(ICON_PNG):
        try:
            from PIL import Image,ImageTk
            img = Image.open(ICON_PNG)
            photo = ImageTk.PhotoImage(img)
            window.iconphoto(True, photo)
            #keep a reference so Tk doesn't garbage-collect the image
            window._icon_ref = photo
            icon_set = True
        except ImportError:
            try:
                photo = PhotoImage(file=ICON_PNG)
                window.iconphoto(True, photo)
                window._icon_ref = photo
                icon_set = True
            except Exception:
                pass
        except Exception:
            pass
    
    return icon_set

def load_logo(path="assets/logo.png", max_width=320, max_height=140):
    if not os.path.exists(path):
        return None
    try:
        from PIL import Image, ImageTk
        img = Image.open(path).convert("RGBA")
        
        # preserve aspect ratio
        ratio = min(max_width / img.width, max_height / img.height, 1.0)
        new_size = (int(img.width * ratio), int(img.height * ratio))
        img = img.resize(new_size, Image.LANCZOS)
        
        return ImageTk.PhotoImage(img)
    except ImportError:
        try:
            return tk.PhotoImage(img)
        except Exception:
            return None
        
EMAIL_RE = re.compile(r"^[\w\.\-]+@[\w\-]+\.[a-zA-Z]{2,}$")

def valid_email(email):
    return bool(EMAIL_RE.match(email))

def require_fields(*values):
    return all(v and str(v).strip() for v in values)

def info(msg, title="Info"):
    messagebox.showinfo(title, msg)
    
def error(msg, title="Error"):
    messagebox.showerror(title, msg)
    
def confirm(msg, title="Confirm"):
    return messagebox.askyesno(title, msg)

def pick_cv():
    path = filedialog.askopenfilename(
        title="Select cv",
        filetypes=[("Documents", "*.pdf *.docx *.doc"), ("All files", "*.*")])
    return path

def save_cv(src_path, user_id):
    if not src_path:
        return None
    ext = os.path.splitext(src_path)[1]
    dest = os.path.join("uploads", f"cv_user{user_id}{ext}")
    shutil.copyfile(src_path, dest)
    return dest

def is_deadline_passed(deadline_str):
    try:
        y, m, d = map(int, deadline_str.split("-"))
        return date(y, m, d) < date.today()
    except Exception:
        return False