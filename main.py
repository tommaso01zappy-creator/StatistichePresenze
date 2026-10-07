
import sqlite3
import tkinter as tk
from tkinter import ttk, messagebox
from datetime import date, timedelta
from pathlib import Path

try:
    import matplotlib.pyplot as plt
    from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
except ImportError:
    plt = None

APP_DIR = Path(__file__).resolve().parent
DB_FILE = APP_DIR / "presenze.db"

def connect():
    con = sqlite3.connect(DB_FILE)
    con.execute("PRAGMA foreign_keys=ON")
    con.execute("""CREATE TABLE IF NOT EXISTS players(
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT NOT NULL UNIQUE
    )""")
    con.execute("""CREATE TABLE IF NOT EXISTS attendance(
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        player_id INTEGER NOT NULL,
        day TEXT NOT NULL,
        status INTEGER NOT NULL DEFAULT 0,
        UNIQUE(player_id, day),
        FOREIGN KEY(player_id) REFERENCES players(id) ON DELETE CASCADE
    )""")
    con.commit()
    return con

def percent(present, total):
    return round((present / total) * 100, 1) if total else 0.0

class App(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Baseball • Gestione Presenze")
        self.geometry("1180x760")
        self.minsize(980, 650)
        self.configure(bg="#0f1117")
        self.selected_date = date.today()
        self.setup_style()
        self.build()
        self.show_page("Dashboard")

    def setup_style(self):
        s = ttk.Style(self)
        s.theme_use("clam")
        s.configure(".", background="#151821", foreground="#f2f4f8",
                    fieldbackground="#202532", borderwidth=0)
        s.configure("Treeview", background="#171b24", foreground="#f2f4f8",
                    fieldbackground="#171b24", rowheight=36, borderwidth=0)
        s.configure("Treeview.Heading", background="#232938", foreground="#dfe3ea",
                    font=("Segoe UI", 10, "bold"), padding=8)
        s.map("Treeview", background=[("selected","#5b35d5")])
        s.configure("TButton", background="#5b35d5", foreground="white",
                    font=("Segoe UI",10,"bold"), padding=(12,8))
        s.map("TButton", background=[("active","#704be5")])
        s.configure("TEntry", padding=8)
        s.configure("TCombobox", padding=7)

    def build(self):
        self.sidebar = tk.Frame(self, bg="#141722", width=220)
        self.sidebar.pack(side="left", fill="y")
        self.sidebar.pack_propagate(False)

        tk.Label(self.sidebar, text="⚾  BASEBALL", bg="#141722", fg="white",
                 font=("Segoe UI",18,"bold")).pack(pady=(28,4))
        tk.Label(self.sidebar, text="GESTIONE PRESENZE", bg="#141722", fg="#8e96a8",
                 font=("Segoe UI",9,"bold")).pack(pady=(0,28))

        self.buttons = {}
        for name, icon in [("Dashboard","▦"),("Giocatori","♟"),("Calendario","▣"),("Statistiche","◒")]:
            b=tk.Button(self.sidebar, text=f"  {icon}   {name}", anchor="w",
                        relief="flat", bd=0, bg="#141722", fg="#aeb5c5",
                        activebackground="#252a3a", activeforeground="white",
                        font=("Segoe UI",11), padx=22, pady=13,
                        command=lambda n=name:self.show_page(n))
            b.pack(fill="x", padx=12, pady=2)
            self.buttons[name]=b

        self.content=tk.Frame(self,bg="#0f1117")
        self.content.pack(side="right",fill="both",expand=True)

        self.pages={}
        for name, cls in [("Dashboard",DashboardPage),("Giocatori",PlayersPage),
                          ("Calendario",CalendarPage),("Statistiche",StatsPage)]:
            self.pages[name]=cls(self,self.content)

    def show_page(self,name):
        for p in self.pages.values(): p.pack_forget()
        self.pages[name].pack(fill="both",expand=True)
        for n,b in self.buttons.items():
            b.configure(bg="#252a3a" if n==name else "#141722",
                        fg="white" if n==name else "#aeb5c5")
        self.pages[name].refresh()

    def refresh_all(self):
        for p in self.pages.values(): p.refresh()

class BasePage(tk.Frame):
    def __init__(self, app, parent):
        super().__init__(parent,bg="#0f1117")
        self.app=app

    def header(self,title,subtitle=""):
        f=tk.Frame(self,bg="#0f1117"); f.pack(fill="x",padx=30,pady=(28,18))
        tk.Label(f,text=title,bg="#0f1117",fg="white",
                 font=("Segoe UI",25,"bold")).pack(anchor="w")
        if subtitle:
            tk.Label(f,text=subtitle,bg="#0f1117",fg="#8e96a8",
                     font=("Segoe UI",10)).pack(anchor="w",pady=(5,0))

class DashboardPage(BasePage):
    def __init__(self,app,parent):
        super().__init__(app,parent)
        self.header("Dashboard","Panoramica della squadra e delle presenze")
        self.cards=tk.Frame(self,bg="#0f1117"); self.cards.pack(fill="x",padx=30)
        self.card_values={}
        for i,(key,label) in enumerate([("players","Giocatori"),("days","Giornate"),
                                        ("present","Presenze"),("average","Media squadra")]):
            c=tk.Frame(self.cards,bg="#191d27",height=115)
            c.grid(row=0,column=i,padx=(0,12),sticky="nsew")
            self.cards.grid_columnconfigure(i,weight=1)
            tk.Label(c,text=label,bg="#191d27",fg="#8e96a8",
                     font=("Segoe UI",10,"bold")).pack(anchor="w",padx=18,pady=(16,3))
            v=tk.Label(c,text="0",bg="#191d27",fg="white",
                       font=("Segoe UI",24,"bold"))
            v.pack(anchor="w",padx=18); self.card_values[key]=v
        box=tk.Frame(self,bg="#191d27"); box.pack(fill="both",expand=True,padx=30,pady=20)
        tk.Label(box,text="Percentuale di presenza",bg="#191d27",fg="white",
                 font=("Segoe UI",14,"bold")).pack(anchor="w",padx=20,pady=16)
        self.chart_frame=tk.Frame(box,bg="#191d27"); self.chart_frame.pack(fill="both",expand=True,padx=10,pady=5)

    def refresh(self):
        con=connect()
        players=con.execute("SELECT COUNT(*) FROM players").fetchone()[0]
        days=con.execute("SELECT COUNT(DISTINCT day) FROM attendance").fetchone()[0]
        present=con.execute("SELECT COUNT(*) FROM attendance WHERE status=1").fetchone()[0]
        rows=con.execute("""SELECT p.id,COALESCE(SUM(a.status),0)
                            FROM players p LEFT JOIN attendance a ON p.id=a.player_id
                            GROUP BY p.id""").fetchall()
        avg=round(sum(percent(x[1],days) for x in rows)/players,1) if players and days else 0
        for k,v in [("players",players),("days",days),("present",present),("average",f"{avg}%")]:
            self.card_values[k].configure(text=v)
        for w in self.chart_frame.winfo_children(): w.destroy()
        data=con.execute("""SELECT p.name,COALESCE(SUM(a.status),0)
                            FROM players p LEFT JOIN attendance a ON p.id=a.player_id
                            GROUP BY p.id ORDER BY p.name""").fetchall()
        con.close()
        if plt is None:
            tk.Label(self.chart_frame,text="Installa le dipendenze con: pip install -r requirements.txt",
                     bg="#191d27",fg="#f0c94a").pack(pady=30)
            return
        fig,ax=plt.subplots(figsize=(8,3.6),dpi=100)
        fig.patch.set_facecolor("#191d27"); ax.set_facecolor("#191d27")
        names=[x[0] for x in data]; vals=[percent(x[1],days) for x in data]
        ax.bar(names,vals)
        ax.set_ylim(0,100); ax.set_ylabel("%",color="white"); ax.tick_params(colors="white")
        ax.set_xticklabels(names,rotation=35,ha="right",fontsize=8)
        for sp in ax.spines.values(): sp.set_visible(False)
        fig.tight_layout()
        canvas=FigureCanvasTkAgg(fig,master=self.chart_frame); canvas.draw()
        canvas.get_tk_widget().pack(fill="both",expand=True)

class PlayersPage(BasePage):
    def __init__(self,app,parent):
        super().__init__(app,parent)
        self.header("Giocatori","Aggiungi, modifica o rimuovi i membri della squadra")
        bar=tk.Frame(self,bg="#0f1117"); bar.pack(fill="x",padx=30,pady=(0,12))
        ttk.Button(bar,text="+ Aggiungi giocatore",command=self.add).pack(side="left")
        ttk.Button(bar,text="Modifica",command=self.edit).pack(side="left",padx=8)
        ttk.Button(bar,text="Elimina",command=self.delete).pack(side="left")
        self.table=ttk.Treeview(self,columns=("name","pres","pct"),show="headings")
        for c,t in [("name","Nome e cognome"),("pres","Presenze"),("pct","Percentuale")]:
            self.table.heading(c,text=t)
        self.table.column("name",width=500); self.table.column("pres",width=130,anchor="center")
        self.table.column("pct",width=160,anchor="center")
        self.table.pack(fill="both",expand=True,padx=30,pady=8)
        self.table.bind("<Double-1>",lambda e:self.edit())

    def refresh(self):
        for x in self.table.get_children(): self.table.delete(x)
        con=connect(); days=con.execute("SELECT COUNT(DISTINCT day) FROM attendance").fetchone()[0]
        rows=con.execute("""SELECT p.id,p.name,COALESCE(SUM(a.status),0)
                            FROM players p LEFT JOIN attendance a ON p.id=a.player_id
                            GROUP BY p.id ORDER BY p.name""").fetchall(); con.close()
        for pid,name,pres in rows:
            self.table.insert("", "end", iid=str(pid), values=(name,pres,f"{percent(pres,days)}%"))

    def selected(self):
        s=self.table.selection()
        return int(s[0]) if s else None

    def add(self):
        d=SimpleDialog(self,"Aggiungi giocatore","Nome e cognome")
        if d.result:
            try:
                con=connect(); con.execute("INSERT INTO players(name) VALUES(?)",(d.result,)); con.commit(); con.close()
                self.app.refresh_all()
            except sqlite3.IntegrityError: messagebox.showerror("Errore","Questo giocatore esiste già.")

    def edit(self):
        pid=self.selected()
        if not pid: return
        con=connect(); old=con.execute("SELECT name FROM players WHERE id=?",(pid,)).fetchone()[0]; con.close()
        d=SimpleDialog(self,"Modifica giocatore","Nome e cognome",old)
        if d.result:
            try:
                con=connect(); con.execute("UPDATE players SET name=? WHERE id=?",(d.result,pid)); con.commit(); con.close()
                self.app.refresh_all()
            except sqlite3.IntegrityError: messagebox.showerror("Errore","Questo nome esiste già.")

    def delete(self):
        pid=self.selected()
        if not pid:return
        if messagebox.askyesno("Conferma","Eliminare il giocatore e tutte le sue presenze?"):
            con=connect(); con.execute("DELETE FROM players WHERE id=?",(pid,)); con.commit(); con.close()
            self.app.refresh_all()

class SimpleDialog(tk.Toplevel):
    def __init__(self,parent,title,label,value=""):
        super().__init__(parent); self.result=None; self.title(title); self.configure(bg="#191d27")
        self.transient(parent); self.grab_set(); self.geometry("390x170")
        tk.Label(self,text=label,bg="#191d27",fg="white",font=("Segoe UI",11,"bold")).pack(anchor="w",padx=22,pady=(20,6))
        self.entry=ttk.Entry(self); self.entry.pack(fill="x",padx=22); self.entry.insert(0,value); self.entry.focus()
        f=tk.Frame(self,bg="#191d27"); f.pack(fill="x",padx=22,pady=18)
        ttk.Button(f,text="Annulla",command=self.destroy).pack(side="right")
        ttk.Button(f,text="Salva",command=self.save).pack(side="right",padx=8)
        self.bind("<Return>",lambda e:self.save())
        self.wait_window()
    def save(self):
        v=self.entry.get().strip()
        if not v:return
        self.result=v; self.destroy()

class CalendarPage(BasePage):
    def __init__(self,app,parent):
        super().__init__(app,parent)
        self.header("Calendario","Seleziona una giornata e registra le presenze")
        top=tk.Frame(self,bg="#0f1117"); top.pack(fill="x",padx=30,pady=(0,15))
        ttk.Button(top,text="‹",width=3,command=lambda:self.change_day(-1)).pack(side="left")
        self.date_label=tk.Label(top,text="",bg="#0f1117",fg="white",font=("Segoe UI",15,"bold"))
        self.date_label.pack(side="left",padx=15)
        ttk.Button(top,text="›",width=3,command=lambda:self.change_day(1)).pack(side="left")
        ttk.Button(top,text="Oggi",command=self.today).pack(side="left",padx=10)
        ttk.Button(top,text="Salva presenze",command=self.save).pack(side="right")
        self.table=ttk.Treeview(self,columns=("name","status"),show="headings")
        self.table.heading("name",text="Giocatore"); self.table.heading("status",text="Presenza")
        self.table.column("name",width=500); self.table.column("status",width=220,anchor="center")
        self.table.pack(fill="both",expand=True,padx=30,pady=8)
        self.table.bind("<Double-1>",self.toggle)

    def change_day(self,n):
        self.app.selected_date += timedelta(days=n); self.refresh()
    def today(self):
        self.app.selected_date=date.today(); self.refresh()
    def toggle(self,event=None):
        item=self.table.identify_row(event.y) if event else None
        if item:
            vals=self.table.item(item,"values")
            self.table.item(item,values=(vals[0],"Presente" if vals[1]!="Presente" else "Assente"))
    def refresh(self):
        self.date_label.configure(text=self.app.selected_date.strftime("%A %d %B %Y").capitalize())
        for x in self.table.get_children():self.table.delete(x)
        day=self.app.selected_date.isoformat(); con=connect()
        rows=con.execute("""SELECT p.id,p.name,COALESCE(a.status,0)
                            FROM players p LEFT JOIN attendance a
                            ON p.id=a.player_id AND a.day=? ORDER BY p.name""",(day,)).fetchall(); con.close()
        for pid,name,status in rows:
            self.table.insert("", "end", iid=str(pid), values=(name,"Presente" if status else "Assente"))

    def save(self):
        day=self.app.selected_date.isoformat(); con=connect()
        for iid in self.table.get_children():
            status=1 if self.table.item(iid,"values")[1]=="Presente" else 0
            con.execute("""INSERT INTO attendance(player_id,day,status) VALUES(?,?,?)
                           ON CONFLICT(player_id,day) DO UPDATE SET status=excluded.status""",
                        (int(iid),day,status))
        con.commit(); con.close(); self.app.refresh_all()
        messagebox.showinfo("Salvato","Le presenze sono state salvate.")

class StatsPage(BasePage):
    def __init__(self,app,parent):
        super().__init__(app,parent)
        self.header("Statistiche","Classifica e andamento delle presenze")
        self.chart_frame=tk.Frame(self,bg="#191d27"); self.chart_frame.pack(fill="both",expand=True,padx=30,pady=10)

    def refresh(self):
        for w in self.chart_frame.winfo_children():w.destroy()
        con=connect()
        days=con.execute("SELECT COUNT(DISTINCT day) FROM attendance").fetchone()[0]
        rows=con.execute("""SELECT p.name,COALESCE(SUM(a.status),0)
                            FROM players p LEFT JOIN attendance a ON p.id=a.player_id
                            GROUP BY p.id ORDER BY SUM(a.status) DESC,p.name""").fetchall(); con.close()
        if plt is None:return
        fig,ax=plt.subplots(figsize=(9,5),dpi=100); fig.patch.set_facecolor("#191d27"); ax.set_facecolor("#191d27")
        names=[x[0] for x in rows]; vals=[percent(x[1],days) for x in rows]
        ax.barh(names[::-1],vals[::-1]); ax.set_xlim(0,100); ax.set_xlabel("Percentuale di presenza",color="white")
        ax.tick_params(colors="white")
        for sp in ax.spines.values():sp.set_visible(False)
        fig.tight_layout()
        c=FigureCanvasTkAgg(fig,master=self.chart_frame); c.draw(); c.get_tk_widget().pack(fill="both",expand=True)

if __name__=="__main__":
    connect().close()
    app=App()
    app.mainloop()
