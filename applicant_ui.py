import tkinter as tk
from tkinter import ttk
import database as db
from auth import Session
from utils import (valid_email, require_fields, info, error, pick_cv, is_deadline_passed, save_cv)

#------------- Registration -----------
class RegistrationWindow(tk.Toplevel):
    def __init__(self, master):
        super().__init__(master)
        self.title("Applicant Registration")
        self.geometry("400x420")
        fields = ["Full Name", "Email", "Phone", "Address", "Password", "Confirm Password"]
        self.entries = {}
        for i, f in enumerate(fields):
            tk.Label(self, text=f).grid(row=i, column=0, sticky="w", padx=10, pady=6)
            e = tk.Entry(self, width=30, show="*" if "Password" in f else "")
            e.grid(row=i, column=1, padx=10, pady=6)
            self.entries[f] = e
        tk.Button(self, text="Register", bg="#2e7d32", fg="white", 
                  command=self.register).grid(row=len(fields), column=0, columnspan=2, pady=15)
    
    def register(self):
        e = self.entries
        name = e["Full Name"].get().strip()
        email = e["Email"].get().strip()
        phone = e["Phone"].get().strip()
        addr = e["Address"].get().strip()
        pwd = e["Password"].get()
        cpwd = e["Confirm Password"].get()
        
        if not require_fields(name, email, phone, addr, pwd):
            return error("All fields are required.")
        if not valid_email(email):
            return error("Invalid email format.")
        if pwd != cpwd:
            return error("Passwords do not match.")
        
        ok, msg = db.create_applicant(name, email, phone, pwd, addr)
        info(msg) if ok else error(msg)
        if ok:
            self.destroy()
            
#----------- Applicant Dashboard ---------
class ApplicantDashboard(tk.Toplevel):
    def __init__(self, master):
        super().__init__(master)
        self.title(f"Applicant Dashboard - {Session.name}")
        self.geometry("900x560")
        self.configure(bg="#f4f6f8")

        tk.Label(self, text=f"Welcome, {Session.name}", font=("Arial", 16, "bold"),
                 bg="#f4f6f8", fg="#1a237e").pack(pady=10)

        toolbar = tk.Frame(self, bg="#f4f6f8")
        toolbar.pack(fill="x", padx=10)
        for text, cmd in [
            ("Search Jobs", self.search_jobs),
            ("My Applications", self.my_apps),
            ("My Profile", self.profile),
            ("Upload CV", self.upload_cv),
            ("Logout", self.logout),
        ]:
            tk.Button(toolbar, text=text, width=16, bg="#3949ab", fg="white",
                      command=cmd).pack(side="left", padx=4)

        self.tree = ttk.Treeview(self, columns=("ID","Title","Dept","Location",
                                                "Salary","Deadline","Status"),
                                 show="headings", height=18)
        for col in self.tree["columns"]:
            self.tree.heading(col, text=col)
            self.tree.column(col, width=120)
        self.tree.pack(fill="both", expand=True, padx=10, pady=10)
        self.tree.bind("<Double-1>", self.apply_job)
        self.load_jobs()

    def load_jobs(self, search="", location="", department=""):
        for i in self.tree.get_children():
            self.tree.delete(i)
        for job in db.list_jobs(search, location, department, only_open=True):
            self.tree.insert("", "end", values=job)

    def search_jobs(self):
        win = tk.Toplevel(self); win.title("Search Jobs"); win.geometry("380x220")
        labels = ["Title", "Location", "Department"]
        entries = {}
        for i, l in enumerate(labels):
            tk.Label(win, text=l).grid(row=i, column=0, padx=10, pady=6, sticky="w")
            e = tk.Entry(win, width=30); e.grid(row=i, column=1, padx=10, pady=6)
            entries[l] = e
        def do():
            self.load_jobs(entries["Title"].get().strip(),
                           entries["Location"].get().strip(),
                           entries["Department"].get().strip())
            win.destroy()
        tk.Button(win, text="Search", bg="#2e7d32", fg="white",
                  command=do).grid(row=3, column=0, columnspan=2, pady=10)

    def apply_job(self, event):
        sel = self.tree.selection()
        if not sel: return
        vals = self.tree.item(sel[0], "values")
        job_id = int(vals[0])
        job = db.get_job(job_id)
        if job[9] != "Open":
            return error("This vacancy is closed.")
        if is_deadline_passed(job[8]):
            return error("Application deadline has passed.")
        
        # Show details in a popup
        win = tk.Toplevel(self); win.title(job[1]); win.geometry("520x420")
        tk.Label(win, text=job[1], font=("Arial", 14, "bold")).pack(pady=6)
        for label, value in [("Department", job[2]), ("Location", job[6]),
                             ("Salary", job[7]), ("Deadline", job[8]),
                             ("Qualification", job[4]), ("Experience", job[5]),
                             ("Description", job[3])]:
            tk.Label(win, text=f"{label}: {value}", wraplength=480,
                     justify="left").pack(anchor="w", padx=12, pady=2)
        def confirm_apply():
            if not db.get_applicant_by_user(Session.user_id)[6]:
                if not tk.messagebox.askyesno("CV missing",
                    "You have not uploaded a CV. Continue anyway?"):
                    return
            ok, msg = db.submit_application(Session.applicant_id, job_id)
            info(msg) if ok else error(msg)
            if ok: win.destroy()
        tk.Button(win, text="Submit Application", bg="#2e7d32", fg="white",
                  command=confirm_apply).pack(pady=12)

    def my_apps(self):
        win = tk.Toplevel(self); win.title("My Applications"); win.geometry("700x380")
        cols = ("ID","Job","Department","Location","Date","Status")
        tree = ttk.Treeview(win, columns=cols, show="headings")
        for c in cols:
            tree.heading(c, text=c); tree.column(c, width=110)
        tree.pack(fill="both", expand=True, padx=10, pady=10)
        for row in db.my_applications(Session.applicant_id):
            tree.insert("", "end", values=row)

    def profile(self):
        app = db.get_applicant_by_user(Session.user_id)
        win = tk.Toplevel(self); win.title("My Profile"); win.geometry("420x380")
        labels = ["Phone", "Address", "Education", "Experience"]
        entries = {}
        for i, l in enumerate(labels):
            tk.Label(win, text=l).grid(row=i, column=0, padx=10, pady=6, sticky="w")
            e = tk.Entry(win, width=35)
            e.grid(row=i, column=1, padx=10, pady=6)
            e.insert(0, app[2+i] or "")
            entries[l] = e
        tk.Label(win, text=f"CV: {app[6] or 'Not uploaded'}").grid(
            row=5, column=0, columnspan=2, pady=6)
        def save():
            db.update_applicant_profile(Session.user_id,
                                        entries["Phone"].get(),
                                        entries["Address"].get(),
                                        entries["Education"].get(),
                                        entries["Experience"].get())
            info("Profile updated."); win.destroy()
        tk.Button(win, text="Save", bg="#2e7d32", fg="white",
                  command=save).grid(row=6, column=0, columnspan=2, pady=12)

    def upload_cv(self):
        path = pick_cv()
        if not path: return
        dest = save_cv(path, Session.user_id)
        db.update_cv_path(Session.user_id, dest)
        info(f"CV uploaded: {dest}")

    def logout(self):
        Session.logout()
        self.destroy()
        self.master.deiconify()
        
