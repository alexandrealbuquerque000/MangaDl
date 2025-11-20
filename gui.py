import customtkinter as ctk
import threading
import os
import json
from tkinter import filedialog, messagebox
from backend import Engine

ctk.set_appearance_mode("Dark")

class App(ctk.CTk):
    def __init__(self):
        super().__init__()
        self.title("Manga Downloader")
        self.geometry("1000x700")
        self.engine = Engine()
        self.caps = []
        self.info = {}
        self.widgets = []
        
        self.root_dir = os.path.dirname(os.path.abspath(__file__))
        self.cfg_path = os.path.join(self.root_dir, "config.json")
        self.load_cfg()

        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(2, weight=1)

        # Topo
        self.fr_top = ctk.CTkFrame(self)
        self.fr_top.grid(row=0, column=0, sticky="ew", padx=10, pady=10)
        self.entry = ctk.CTkEntry(self.fr_top, placeholder_text="Link do mangá...")
        self.entry.pack(side="left", fill="x", expand=True, padx=5)
        ctk.CTkButton(self.fr_top, text="BUSCAR", width=100, command=self.analisar).pack(side="right", padx=5)

        # Info
        self.fr_info = ctk.CTkFrame(self, height=150)
        self.fr_info.grid(row=1, column=0, sticky="ew", padx=10, pady=(0, 10))
        self.fr_info.pack_propagate(False)
        self.lbl_capa = ctk.CTkLabel(self.fr_info, text="[Capa]", width=100, height=130, fg_color="#222", corner_radius=5)
        self.lbl_capa.pack(side="left", padx=10, pady=10)
        self.fr_text = ctk.CTkFrame(self.fr_info, fg_color="transparent")
        self.fr_text.pack(side="left", fill="both", expand=True, padx=5, pady=5)
        self.lbl_titulo = ctk.CTkLabel(self.fr_text, text="---", font=("Arial", 18, "bold"), anchor="w")
        self.lbl_titulo.pack(fill="x")
        self.txt_desc = ctk.CTkTextbox(self.fr_text, fg_color="transparent", height=80, wrap="word", text_color="gray80")
        self.txt_desc.pack(fill="both", expand=True)
        self.txt_desc.insert("0.0", "Aguardando...")
        self.txt_desc.configure(state="disabled")

        # Lista
        self.scroll = ctk.CTkScrollableFrame(self, label_text="Capítulos")
        self.scroll.grid(row=2, column=0, sticky="nsew", padx=10)

        # Opções
        self.fr_opt = ctk.CTkFrame(self)
        self.fr_opt.grid(row=3, column=0, sticky="ew", padx=10, pady=10)
        self.fr_sel = ctk.CTkFrame(self.fr_opt, fg_color="transparent")
        self.fr_sel.pack(side="left", padx=10)
        ctk.CTkButton(self.fr_sel, text="Todos", width=60, command=self.sel_all).pack(side="left", padx=2)
        ctk.CTkButton(self.fr_sel, text="Nenhum", width=60, command=self.sel_none).pack(side="left", padx=2)
        ctk.CTkButton(self.fr_sel, text="1-10", width=60, command=self.sel_range).pack(side="left", padx=2)

        self.fr_cfg = ctk.CTkFrame(self.fr_opt, fg_color="transparent")
        self.fr_cfg.pack(side="left", padx=20)
        self.var_vol = ctk.BooleanVar()
        ctk.CTkCheckBox(self.fr_cfg, text="Agrupar Volume", variable=self.var_vol, command=self.toggle_vol).pack(anchor="w")
        self.entry_vol = ctk.CTkEntry(self.fr_cfg, placeholder_text="Nome Volume", state="disabled")
        self.entry_vol.pack(pady=5)

        self.fr_fmt = ctk.CTkFrame(self.fr_opt, fg_color="transparent")
        self.fr_fmt.pack(side="left", padx=20)
        self.path_cover = None
        self.btn_cover = ctk.CTkButton(self.fr_fmt, text="Escolher Capa", command=self.pick_cover, state="disabled", fg_color="#555")
        self.btn_cover.pack(pady=2)
        
        # REMOVIDO EPUB
        self.combo_fmt = ctk.CTkComboBox(self.fr_fmt, values=["folder", "cbz", "pdf"])
        self.combo_fmt.pack(pady=2)

        self.btn_go = ctk.CTkButton(self.fr_opt, text="BAIXAR", fg_color="green", width=120, height=50, command=self.start)
        self.btn_go.pack(side="right", padx=20)
        self.lbl_status = ctk.CTkLabel(self, text="Pronto.")
        self.lbl_status.grid(row=4, column=0, sticky="w", padx=10)

    def load_cfg(self):
        try:
            with open(self.cfg_path, "r") as f: self.save_dir = json.load(f).get("save_dir", "Manga_Downloads")
        except: self.save_dir = "Manga_Downloads"

    def save_cfg(self):
        try:
            with open(self.cfg_path, "w") as f: json.dump({"save_dir": self.save_dir}, f)
        except: pass

    def analisar(self):
        u = self.entry.get()
        if not u: return
        self.lbl_status.configure(text="Analisando...")
        for w in self.widgets: 
            w['chk'].destroy(); w['lbl'].destroy(); w['frame'].destroy()
        self.widgets = []
        threading.Thread(target=self._th_an, args=(u,), daemon=True).start()

    def _th_an(self, u):
        info, caps, msg = self.engine.analyze(u)
        self.after(0, lambda: self._pos_an(info, caps, msg))

    def _pos_an(self, i, c, m):
        if not i:
            messagebox.showerror("Erro", m)
            self.lbl_status.configure(text="Erro")
            return
        self.info = i
        self.caps = c
        self.title(f"Manga Downloader - {i['title']}")
        self.lbl_titulo.configure(text=i['title'])
        self.txt_desc.configure(state="normal")
        self.txt_desc.delete("0.0", "end")
        self.txt_desc.insert("0.0", i.get('desc', ''))
        self.txt_desc.configure(state="disabled")
        if i.get('cover'): threading.Thread(target=self._load_cover_gui, args=(i['cover'],), daemon=True).start()
        self.lbl_status.configure(text=f"{len(c)} capítulos.")
        for idx, cap in enumerate(c):
            f = ctk.CTkFrame(self.scroll, fg_color="transparent")
            f.pack(fill="x", pady=1)
            var = ctk.BooleanVar()
            chk = ctk.CTkCheckBox(f, text=cap['name'], variable=var)
            chk.pack(side="left")
            lbl = ctk.CTkLabel(f, text="", width=80)
            lbl.pack(side="right")
            self.widgets.append({'var': var, 'lbl': lbl, 'data': cap, 'idx': idx, 'frame': f, 'chk': chk})

    def _load_cover_gui(self, url):
        img = self.engine.baixar_imagem_ram(url)
        if img:
            ctk_img = ctk.CTkImage(light_image=img, dark_image=img, size=(100, 130))
            self.after(0, lambda: self.lbl_capa.configure(image=ctk_img, text=""))

    def toggle_vol(self):
        st = "normal" if self.var_vol.get() else "disabled"
        self.entry_vol.configure(state=st)
        self.btn_cover.configure(state=st)

    def pick_cover(self):
        p = filedialog.askopenfilename(filetypes=[("Images", "*.jpg;*.png")])
        if p: 
            self.path_cover = p
            self.btn_cover.configure(text="Capa OK", fg_color="green")

    def sel_all(self):
        for w in self.widgets: w['var'].set(True)
    def sel_none(self):
        for w in self.widgets: w['var'].set(False)
    def sel_range(self):
        inp = ctk.CTkInputDialog(text="1-10", title="Range").get_input()
        if inp and '-' in inp:
            try:
                s, e = map(float, inp.split('-'))
                for w in self.widgets:
                    if s <= w['data']['num'] <= e: w['var'].set(True)
            except: pass

    def start(self):
        q = []
        for w in self.widgets:
            if w['var'].get():
                d = w['data'].copy()
                d['gui_id'] = w['idx']
                d['title'] = self.info['title']
                d['cover'] = self.info.get('cover')
                q.append(d)
        if not q: return
        
        mode = 'volume' if self.var_vol.get() else 'single'
        fmt = self.combo_fmt.get()
        vol = self.entry_vol.get() or self.info['title']
        cover_input = self.path_cover

        self.btn_go.configure(state="disabled")
        threading.Thread(target=self._th_dl, args=(q, mode, fmt, vol, cover_input), daemon=True).start()

    def _th_dl(self, q, m, f, v, c):
        self.engine.download_queue(q, self.save_dir, m, f, v, c, self._upd)
        self.after(0, lambda: [self.btn_go.configure(state="normal"), messagebox.showinfo("Fim", "Concluído")])

    def _upd(self, idx, msg, state):
        c = {"working":"orange", "done":"green", "error":"red"}.get(state, "gray")
        self.after(0, lambda: self.widgets[idx]['lbl'].configure(text=msg, text_color=c))

if __name__ == "__main__":
    App().mainloop()