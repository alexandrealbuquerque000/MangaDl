import customtkinter as ctk
import threading, os
from PIL import Image
from tkinter import filedialog, messagebox
from backend import Engine

ctk.set_appearance_mode("Dark")

class App(ctk.CTk):
    def __init__(self):
        super().__init__()
        self.title("Manga Downloader")
        self.geometry("1100x850")
        self.engine = Engine()
        self.path_cover = None
        self.widgets = []
        self.info = {}
        self.base_dir = "Downloads_Manga"

        self.grid_columnconfigure(1, weight=1)
        self.grid_rowconfigure(0, weight=1)

        # Sidebar
        self.sidebar = ctk.CTkFrame(self, width=300, corner_radius=0)
        self.sidebar.grid(row=0, column=0, rowspan=2, sticky="nsew", padx=10, pady=10)
        
        self.lbl_preview = ctk.CTkLabel(self.sidebar, text="Sem Preview", width=250, height=350, fg_color="#222", corner_radius=10)
        self.lbl_preview.pack(pady=20, padx=20)
        
        ctk.CTkButton(self.sidebar, text="Capa Personalizada", command=self.pick_cover).pack(pady=10)
        self.var_vol = ctk.BooleanVar(value=True)
        ctk.CTkCheckBox(self.sidebar, text="Agrupar Volume", variable=self.var_vol).pack(pady=10)
        self.entry_vol = ctk.CTkEntry(self.sidebar, placeholder_text="Nome Final do Volume")
        self.entry_vol.pack(pady=10, padx=20, fill="x")
        
        self.combo_fmt = ctk.CTkComboBox(self.sidebar, values=["epub", "pdf", "cbz"], state="readonly")
        self.combo_fmt.set("epub")
        self.combo_fmt.pack(pady=10)

        # Main
        self.main = ctk.CTkFrame(self, fg_color="transparent")
        self.main.grid(row=0, column=1, sticky="nsew", padx=10, pady=10)
        self.main.grid_columnconfigure(0, weight=1)
        self.main.grid_rowconfigure(1, weight=1)

        self.entry_url = ctk.CTkEntry(self.main, placeholder_text="Link do mangá...", height=45)
        self.entry_url.grid(row=0, column=0, sticky="ew", padx=10, pady=10)
        ctk.CTkButton(self.main, text="BUSCAR", width=120, height=45, command=self.analisar).grid(row=0, column=1, padx=10)

        self.scroll = ctk.CTkScrollableFrame(self.main, label_text="Capítulos")
        self.scroll.grid(row=1, column=0, columnspan=2, sticky="nsew", padx=10, pady=10)

        self.progress_bar = ctk.CTkProgressBar(self, height=15)
        self.progress_bar.grid(row=1, column=1, sticky="ew", padx=20, pady=(0, 80))
        self.progress_bar.set(0)

        self.btn_go = ctk.CTkButton(self, text="INICIAR PROCESSAMENTO", height=50, fg_color="green", command=self.start)
        self.btn_go.grid(row=1, column=1, sticky="ew", padx=20, pady=20)

        self.protocol("WM_DELETE_WINDOW", self.on_close)

    def on_close(self):
        """Protocolo de fecho para limpar capas e pastas temporárias."""
        if self.info.get('title'):
            try: self.engine.clear_cache(self.base_dir, self.info['title'])
            except: pass
        self.destroy()

    def pick_cover(self):
        p = filedialog.askopenfilename(filetypes=[("Imagens", "*.jpg;*.png;*.webp")])
        if p:
            self.path_cover = p
            img = Image.open(p)
            ctk_img = ctk.CTkImage(light_image=img, dark_image=img, size=(250, 350))
            self.lbl_preview.configure(image=ctk_img, text="")

    def analisar(self):
        url = self.entry_url.get()
        if url: threading.Thread(target=self._th_an, args=(url,), daemon=True).start()

    def _th_an(self, url):
        res = self.engine.analyze(url)
        if res and res[0]:
            info, caps, _ = res
            self.info = info
            if info.get('cover'):
                img = self.engine.get_preview_img(info['cover'])
                if img:
                    ctk_img = ctk.CTkImage(light_image=img, dark_image=img, size=(250, 350))
                    self.after(0, lambda: self.lbl_preview.configure(image=ctk_img, text=""))
            self.after(0, lambda: self._popula(caps))

    def _popula(self, caps):
        for w in self.widgets: w['frame'].destroy()
        self.widgets = []
        for i, c in enumerate(caps):
            f = ctk.CTkFrame(self.scroll, fg_color="transparent")
            f.pack(fill="x", pady=2)
            v = ctk.BooleanVar()
            chk = ctk.CTkCheckBox(f, text=c['name'], variable=v)
            chk.pack(side="left", padx=10)
            lbl = ctk.CTkLabel(f, text="", width=100)
            lbl.pack(side="right", padx=10)
            c['gui_id'] = i
            self.widgets.append({'var': v, 'lbl': lbl, 'data': c, 'frame': f})

    def start(self):
        q = [w['data'] for w in self.widgets if w['var'].get()]
        if q:
            self.btn_go.configure(state="disabled")
            self.progress_bar.set(0)
            threading.Thread(target=self._th_dl, args=(q,), daemon=True).start()

    def _th_dl(self, q):
        v = self.entry_vol.get() or self.info.get('title', 'Manga')
        f = self.combo_fmt.get()
        m = 'volume' if self.var_vol.get() else 'single'
        self.engine.download_queue(q, self.base_dir, m, f, v, self.path_cover, self._upd, self.info.get('title', 'Manga'))
        self.after(0, lambda: [self.btn_go.configure(state="normal"), messagebox.showinfo("Fim", "Concluído!")])

    def _upd(self, idx, msg, progresso):
        color = "green" if msg == "Pronto" else "orange"
        self.after(0, lambda: [
            self.widgets[idx]['lbl'].configure(text=msg, text_color=color),
            self.progress_bar.set(progresso)
        ])

if __name__ == "__main__":
    App().mainloop()