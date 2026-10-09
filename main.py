import tkinter as tk
from tkinter import messagebox
import database as db
from auth import Session
from utils import valid_email, error, info, apply_icon, load_logo
from applicant_ui import RegistrationWindow, ApplicantDashboard
from admin_ui import AdminDashboard

#patch toplevel so every new window automatically gets the icon
_orig_toplevel_init = tk.Toplevel.__init__
def _patched_toplevel_init(self, *args, **kwargs):
    _orig_toplevel_init(self, *args, **kwargs)
    apply_icon(self, self.title() or "JAMS")
tk.Toplevel.__init__ = _patched_toplevel_init

class LoginWindow(tk.Tk):
    def __init__(self):
        super().__init__()
        apply_icon(self, "JAMS Login")
        self.title("Job Application Management System - Login")
        self.geometry("420x430")
        self.configure(bg="#f4f6f8")
        
        logo = load_logo("assests/logo.png", max_width=300, max_height=130)
        if logo:
            self._logo_ref = logo 
            tk.Label(self, image=logo, bg="#f4f6f8").pack(pady=(18, 4))
        else:
            # fallback text title if no logo file is found
            tk.Label(self, text="JAMS",
                    font=("Arial", 22, "bold"),
                    bg="#f4f6f8", fg='#1a237e').pack(pady=(22, 4))
            
        tk.Label(self, text="Job Application Management System",
                 font=("Arial", 11, "italic"),
                 bg="#f4f6f8", fg="#555").pack(pady=(0, 14))
        
        tk.Label(self, text="JAMS Login", font=("Arial", 20, "bold"),
                 bg="#f4f6f8", fg="#1a237e").pack(pady=20)
        
        tk.Label(self, text="Email", bg="#f4f6f8").pack(anchor="w", padx=40)
        self.email = tk.Entry(self, width=35)
        self.email.pack(pady=4)

        tk.Label(self, text="Password", bg="#f4f6f8").pack(anchor="w", padx=40)
        self.pwd = tk.Entry(self, width=35, show="*")
        self.pwd.pack(pady=4)

        tk.Button(self, text="Login", width=20, bg="#2e7d32", fg="white",
                  command=self.login).pack(pady=14)
        tk.Button(self, text="Register as Applicant", width=20,
                  command=self.open_register).pack()

    def open_register(self):
        RegistrationWindow(self)

    def login(self):
        email = self.email.get().strip()
        pwd = self.pwd.get()
        if not valid_email(email):
            return error("Invalid email")
        row = db.authenticate(email, pwd)
        if not row:
            return error("Invalid credentials")
        applicant = db.get_applicant_by_user(row[0]) if row[2] == "Applicant" else None
        Session.login(row, applicant)
        self.withdraw()
        if row[2] == "Admin":
            AdminDashboard(self)
        else:
            ApplicantDashboard(self)
            
if __name__ == "__main__":
    db.init_db()
    LoginWindow().mainloop()