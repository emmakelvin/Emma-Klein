import tkinter as tk
from tkinter import ttk
import database as db
from auth import Session
from utils import info, error, confirm, require_fields

class AdminDashboard(tk.Toplevel):
    def __init__(self, master):
        super().__init__(master)
        self.title(f"Administrator Dashboard - {Session.name}")
        self.geometry("1000x620")
        self.configure(bg="#5f93ed")

        tk.Label(self, text="ADMINISTRATOR DASHBOARD",
                 font=("Arial", 18, "bold"), bg="#eef1f6",
                 fg="#1a237e").pack(pady=10)

        self.stats_frame = tk.Frame(self, bg="#eef1f6")
        self.stats_frame.pack(pady=4)
        self.refresh_stats()

        toolbar = tk.Frame(self, bg="#eef1f6")
        toolbar.pack(fill="x", padx=10, pady=8)
        for text, cmd in [
            ("Manage Jobs", self.manage_jobs),
            ("View Applications", self.view_apps),
            ("Shortlisted", lambda: self.view_apps("Shortlisted")),
            ("Interviews", self.interviews),
            ("Reports", self.reports),
            ("Logout", self.logout),
        ]:
            tk.Button(toolbar, text=text, width=16, bg="#3949ab", fg="white",
                      command=cmd).pack(side="left", padx=4)

        # Job list preview
        tk.Label(self, text="All Jobs", bg="#eef1f6",
                 font=("Arial", 12, "bold")).pack(anchor="w", padx=14)
        self.tree = ttk.Treeview(self, columns=("ID","Title","Department","Location","Deadline","Status"),
                                 show="headings", height=14)
        for c in self.tree["columns"]:
            self.tree.heading(c, text=c); self.tree.column(c, width=140)
        self.tree.pack(fill="both", expand=True, padx=10, pady=6)
        self.load_jobs()

    def refresh_stats(self):
        for w in self.stats_frame.winfo_children():
            w.destroy()
        s = db.get_stats()
        labels = [
            ("Total Jobs", s["jobs"]), ("Applicants", s["applicants"]),
            ("Applications", s["applications"]), ("Shortlisted", s["shortlisted"]),
            ("Interviews", s["interviews"]), ("Accepted", s["accepted"]),
            ("Rejected", s["rejected"]),
        ]
        for i, (k, v) in enumerate(labels):
            f = tk.Frame(self.stats_frame, bg="white", bd=1, relief="solid")
            f.grid(row=0, column=i, padx=6, pady=4, ipadx=14, ipady=6)
            tk.Label(f, text=k, bg="white", fg="#555").pack()
            tk.Label(f, text=str(v), bg="white", fg="#1a237e",
                     font=("Arial", 14, "bold")).pack()

    def load_jobs(self):
        for i in self.tree.get_children():
            self.tree.delete(i)
        for job in db.list_jobs():
            self.tree.insert("", "end", values=job)

    # ---------- Manage Jobs ----------
    def manage_jobs(self):
        win = tk.Toplevel(self); win.title("Manage Jobs"); win.geometry("880x500"), win.configure(bg="#5f93ed")
        tree = ttk.Treeview(win, columns=("ID","Title","Dept","Location","Deadline","Status"),
                            show="headings")
        for c in tree["columns"]:
            tree.heading(c, text=c); tree.column(c, width=130)
        tree.pack(fill="both", expand=True, padx=10, pady=10)

        def reload():
            for i in tree.get_children(): tree.delete(i)
            for job in db.list_jobs(): tree.insert("", "end", values=job)
        reload()

        bar = tk.Frame(win); bar.pack(pady=6)
        def add():
            JobForm(win, on_save=reload)
        def edit():
            sel = tree.selection()
            if not sel: return error("Select a job.")
            jid = int(tree.item(sel[0], "values")[0])
            JobForm(win, job_id=jid, on_save=reload)
        def delete():
            sel = tree.selection()
            if not sel: return error("Select a job.")
            jid = int(tree.item(sel[0], "values")[0])
            if confirm("Delete this job?"):
                db.delete_job(jid); reload(); info("Deleted.")
        def close_job():
            sel = tree.selection()
            if not sel: return error("Select a job.")
            jid = int(tree.item(sel[0], "values")[0])
            j = db.get_job(jid)
            db.update_job(jid, j[1], j[2], j[3], j[4], j[5], j[6], j[7], j[8],
                          "Closed" if j[9] == "Open" else "Open")
            reload()

        for text, cmd in [("Add", add), ("Edit", edit), ("Close/Open", close_job),
                          ("Delete", delete)]:
            tk.Button(bar, text=text, width=12, bg="#3949ab", fg="white",
                      command=cmd).pack(side="left", padx=6)

    # ---------- Applications ----------
    def view_apps(self, status_filter=None):
        win = tk.Toplevel(self); win.title("Applications"); win.geometry("1000x520"), win.configure(bg="#5f93ed")
        cols = ("ID","Applicant","Email","Job","Department","Date","Status")
        tree = ttk.Treeview(win, columns=cols, show="headings")
        for c in cols:
            tree.heading(c, text=c); tree.column(c, width=130)
        tree.pack(fill="both", expand=True, padx=10, pady=10)

        def reload():
            for i in tree.get_children(): tree.delete(i)
            for row in db.all_applications(status_filter):
                tree.insert("", "end", values=row[:7])

        reload()

        def set_status(new_status):
            sel = tree.selection()
            if not sel: return error("Select an application.")
            app_id = int(tree.item(sel[0], "values")[0])
            db.update_application_status(app_id, new_status)
            info(f"Application marked as {new_status}.")
            reload(); self.refresh_stats()

        bar = tk.Frame(win); bar.pack(pady=6)
        for text, st in [("Under Review","Under Review"),
                         ("Shortlist","Shortlisted"),
                         ("Reject","Rejected"),
                         ("Accept","Accepted")]:
            tk.Button(bar, text=text, bg="#2e7d32", fg="white", width=13,
                      command=lambda s=st: set_status(s)).pack(side="left", padx=5)

        def schedule():
            sel = tree.selection()
            if not sel: return error("Select an application.")
            app_id = int(tree.item(sel[0], "values")[0])
            InterviewForm(win, app_id)
            reload()
        tk.Button(bar, text="Schedule Interview", bg="#c62828", fg="white",
                  width=18, command=schedule).pack(side="left", padx=5)

    # ---------- Interviews ----------
    def interviews(self):
        win = tk.Toplevel(self); win.title("Interviews"); win.geometry("950x480"); win.configure(bg="#5f93ed")
        cols = ("ID","Applicant","Job","Date","Time","Location","Result")
        tree = ttk.Treeview(win, columns=cols, show="headings")
        for c in cols:
            tree.heading(c, text=c); tree.column(c, width=125)
        tree.pack(fill="both", expand=True, padx=10, pady=10)

        def reload():
            for i in tree.get_children(): tree.delete(i)
            for row in db.list_interviews():
                tree.insert("", "end", values=row[:7])
        reload()

        def record(result):
            sel = tree.selection()
            if not sel: return error("Select an interview.")
            vals = tree.item(sel[0], "values")
            app_id = int(vals[0])  # Note: interview_id shown first
            # fetch app_id via interviews row
            for r in db.list_interviews():
                if r[0] == app_id:
                    real_app_id = r[7]
                    db.record_interview_result(real_app_id, result)
                    if result == "Passed":
                        db.update_application_status(real_app_id, "Accepted")
                    elif result == "Failed":
                        db.update_application_status(real_app_id, "Rejected")
                    break
            info("Result recorded."); reload(); self.refresh_stats()

        bar = tk.Frame(win); bar.pack(pady=6)
        tk.Button(bar, text="Mark Passed", bg="#2e7d32", fg="white",
                  command=lambda: record("Passed")).pack(side="left", padx=6)
        tk.Button(bar, text="Mark Failed", bg="#c62828", fg="white",
                  command=lambda: record("Failed")).pack(side="left", padx=6)

    # ---------- Reports ----------
    def reports(self):
        s = db.get_stats()
        win = tk.Toplevel(self); win.title("Reports"); win.geometry("450x420"), win.configure(bg="#5f93ed")
        tk.Label(win, text="RECRUITMENT REPORT", font=("Arial", 14, "bold")).pack(pady=12)
        report = (
            f"Total Jobs:          {s['jobs']}\n"
            f"Total Applicants:    {s['applicants']}\n"
            f"Total Applications:  {s['applications']}\n"
            f"Shortlisted:         {s['shortlisted']}\n"
            f"Interviews:          {s['interviews']}\n"
            f"Accepted:            {s['accepted']}\n"
            f"Rejected:            {s['rejected']}\n"
        )
        tk.Label(win, text=report, justify="left",
                 font=("Consolas", 12)).pack(padx=20, pady=10)

        def export():
            from reportlab.lib.pagesizes import A4
            from reportlab.pdfgen import canvas
            c = canvas.Canvas("recruitment_report.pdf", pagesize=A4)
            c.setFont("Helvetica-Bold", 14)
            c.drawString(60, 780, "Job Application Management System Report")
            c.setFont("Helvetica", 11)
            y = 750
            for line in report.strip().split("\n"):
                c.drawString(60, y, line); y -= 18
            c.save()
            info("Report saved as recruitment_report.pdf")
        try:
            import reportlab  # noqa
            tk.Button(win, text="Export to PDF", bg="#3949ab", fg="white",
                      command=export).pack(pady=14)
        except ImportError:
            tk.Label(win, text="(Install reportlab for PDF export)",
                     fg="gray").pack()

    def logout(self):
        Session.logout()
        self.destroy()
        self.master.deiconify()


# ---------- Job Form ----------
class JobForm(tk.Toplevel):
    def __init__(self, master, job_id=None, on_save=None):
        super().__init__(master)
        self.title("Job Form"); self.geometry("440x560")
        self.job_id = job_id; self.on_save = on_save
        self.configure(bg="#5f93ed")

        fields = ["Title","Department","Description","Qualification",
                  "Experience","Location","Salary","Deadline (YYYY-MM-DD)","Status"]
        self.entries = {}
        for i, f in enumerate(fields):
            tk.Label(self, text=f).grid(row=i, column=0, padx=10, pady=5, sticky="w")
            e = tk.Entry(self, width=36)
            e.grid(row=i, column=1, padx=10, pady=5)
            self.entries[f] = e

        if job_id:
            j = db.get_job(job_id)
            for k, v in zip(fields, [j[1],j[2],j[3],j[4],j[5],j[6],j[7],j[8],j[9]]):
                self.entries[k].insert(0, v or "")
        else:
            self.entries["Status"].insert(0, "Open")

        tk.Button(self, text="Save", bg="#2e7d32", fg="white", width=14,
                  command=self.save).grid(row=len(fields), column=0,
                                          columnspan=2, pady=15)

    def save(self):
        e = self.entries
        vals = [e[f].get().strip() for f in
                ["Title","Department","Description","Qualification",
                 "Experience","Location","Salary","Deadline (YYYY-MM-DD)","Status"]]
        if not require_fields(vals[0], vals[7]):
            return error("Title and Deadline are required.")
        if self.job_id:
            db.update_job(self.job_id, *vals)
        else:
            db.add_job(*vals[:8])
        info("Saved."); self.on_save and self.on_save(); self.destroy()


# ---------- Interview Form ----------
class InterviewForm(tk.Toplevel):
    def __init__(self, master, application_id):
        super().__init__(master)
        self.title("Schedule Interview"); self.geometry("400x260")
        self.configure(bg="#5f93ed")
        self.app_id = application_id
        labels = ["Date (YYYY-MM-DD)", "Time (HH:MM)", "Location"]
        self.entries = {}
        for i, l in enumerate(labels):
            tk.Label(self, text=l).grid(row=i, column=0, padx=10, pady=8, sticky="w")
            e = tk.Entry(self, width=28)
            e.grid(row=i, column=1, padx=10, pady=8)
            self.entries[l] = e
        tk.Button(self, text="Schedule", bg="#2e7d32", fg="white",
                  command=self.save).grid(row=3, column=0, columnspan=2, pady=14)

    def save(self):
        d = self.entries["Date (YYYY-MM-DD)"].get().strip()
        t = self.entries["Time (HH:MM)"].get().strip()
        loc = self.entries["Location"].get().strip()
        if not require_fields(d, t, loc):
            return error("All fields required.")
        ok, msg = db.schedule_interview(self.app_id, d, t, loc)
        db.update_application_status(self.app_id, "Interview")
        info(msg); self.destroy()
        
