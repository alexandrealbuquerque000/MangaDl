import customtkinter as ctk
import threading
from tkinter import filedialog, messagebox
from backend import Engine

ctk.set_appearance_mode("Dark")

class App(ctk.CTk):
    def __init__(self):
        super().__init__()
        self.title("Manga Downloader - Pro Edition")
        self.geometry("1200x750")
        self.minsize(1100, 700)
        self.engine = Engine()
        self.widgets = []
        self.info = {}
        self.base_dir = "Downloads_Manga"

        self.grid_columnconfigure(1, weight=1)
        self.grid_rowconfigure(0, weight=1)

        # ---------------- SIDEBAR ----------------
        self.sidebar = ctk.CTkScrollableFrame(self, width=340, corner_radius=0)
        self.sidebar.grid(row=0, column=0, rowspan=2, sticky="nsew", padx=10, pady=10)

        ctk.CTkLabel(self.sidebar, text="📱 Perfil do Dispositivo", font=("Arial", 13, "bold"), text_color="#00a8cc").pack(anchor="w", padx=10, pady=(5, 5))
        
        # DOC: A chave 'stretch' foi removida de todos os dicionários de configuração
        self.presets = {
            "Kindle Paperwhite 11": {
                'fmt': "epub", 'w': "1236", 'h': "1648", 'rtl': True, 
                'crop': True, "fill": False, 'gray': True, 'contrast_val': 1.2, 'dp_mode': "Rotacionar", 'qual': 85
            },
            "Galaxy Tab S10 Lite": {
                'fmt': "cbz", 'w': "1320", 'h': "2112", 'rtl': False, 
                'crop': False, "fill": False, 'gray': False, 'contrast_val': 1.0, 'dp_mode': "Manter", 'qual': 100
            },
            "Personalizado": {
                'fmt': "pdf", 'w': "1200", 'h': "1600", 'rtl': False, 
                'crop': False, "fill": False, 'gray': False, 'contrast_val': 1.0, 'dp_mode': "Manter", 'qual': 100
            }
        }
        self.combo_dev = ctk.CTkComboBox(self.sidebar, values=list(self.presets.keys()), command=self._on_dev_change)
        self.combo_dev.pack(pady=5, padx=15, fill="x")
        
        self.fr_res = ctk.CTkFrame(self.sidebar, fg_color="transparent")
        self.fr_res.pack(fill="x", padx=15, pady=2)
        self.entry_w = ctk.CTkEntry(self.fr_res, width=70, placeholder_text="Largura")
        self.entry_w.pack(side="left", padx=(0, 5))
        ctk.CTkLabel(self.fr_res, text="x").pack(side="left")
        self.entry_h = ctk.CTkEntry(self.fr_res, width=70, placeholder_text="Altura")
        self.entry_h.pack(side="left", padx=(5, 0))

        ctk.CTkLabel(self.sidebar, text="📂 Formato de Saída", font=("Arial", 13, "bold"), text_color="#00a8cc").pack(anchor="w", padx=10, pady=(15, 5))
        self.combo_fmt = ctk.CTkComboBox(self.sidebar, values=["epub", "pdf", "cbz"])
        self.combo_fmt.pack(pady=5, padx=15, fill="x")

        ctk.CTkLabel(self.sidebar, text="📖 Comportamento (Páginas Duplas)", font=("Arial", 13, "bold"), text_color="#00a8cc").pack(anchor="w", padx=10, pady=(15, 5))
        self.var_double_page = ctk.StringVar(value="Rotacionar")
        self.seg_double_page = ctk.CTkSegmentedButton(self.sidebar, values=["Dividir", "Rotacionar", "Manter"], variable=self.var_double_page)
        self.seg_double_page.pack(pady=4, padx=15, fill="x")

        ctk.CTkLabel(self.sidebar, text="⚙️ Ajustes Visuais Finos", font=("Arial", 13, "bold"), text_color="#00a8cc").pack(anchor="w", padx=10, pady=(15, 5))
        
        self.var_rtl = ctk.BooleanVar(value=True)
        self.chk_rtl = ctk.CTkCheckBox(self.sidebar, text="Leitura Oriental (Dir p/ Esq)", variable=self.var_rtl)
        self.chk_rtl.pack(pady=4, padx=15, anchor="w")
        
        self.var_autocrop = ctk.BooleanVar(value=True)
        self.chk_autocrop = ctk.CTkCheckBox(self.sidebar, text="Auto-Crop (Remover Bordas)", variable=self.var_autocrop)
        self.chk_autocrop.pack(pady=4, padx=15, anchor="w")

        self.var_fill_screen = ctk.BooleanVar(value=True)
        self.chk_fill_screen = ctk.CTkCheckBox(self.sidebar, text="Preencher Tela (Esticando)", variable=self.var_fill_screen)
        self.chk_fill_screen.pack(pady=4, padx=15, anchor="w")
        
        self.var_gray = ctk.BooleanVar(value=True)
        self.chk_gray = ctk.CTkCheckBox(self.sidebar, text="Forçar Preto e Branco", variable=self.var_gray)
        self.chk_gray.pack(pady=4, padx=15, anchor="w")
        
        ctk.CTkLabel(self.sidebar, text="Ajuste de Contraste (1.0 = Original):", font=("Arial", 11)).pack(anchor="w", padx=15, pady=(10, 0))
        self.fr_slider = ctk.CTkFrame(self.sidebar, fg_color="transparent")
        self.fr_slider.pack(fill="x", padx=15, pady=2)
        self.lbl_contrast_val = ctk.CTkLabel(self.fr_slider, text="1.2", font=("Arial", 11))
        self.lbl_contrast_val.pack(side="right")
        self.slider_contrast = ctk.CTkSlider(self.fr_slider, from_=1.0, to=2.0, number_of_steps=10, command=lambda v: self.lbl_contrast_val.configure(text=f"{v:.1f}"))
        self.slider_contrast.set(1.2)
        self.slider_contrast.pack(side="left", fill="x", expand=True, padx=(0, 10))

        ctk.CTkLabel(self.sidebar, text="Qualidade da Imagem:", font=("Arial", 11)).pack(anchor="w", padx=15, pady=(10, 0))
        self.fr_qual = ctk.CTkFrame(self.sidebar, fg_color="transparent")
        self.fr_qual.pack(fill="x", padx=15, pady=2)
        self.lbl_qual = ctk.CTkLabel(self.fr_qual, text="85%", font=("Arial", 11))
        self.lbl_qual.pack(side="right")
        self.slider_qual = ctk.CTkSlider(self.fr_qual, from_=50, to=100, number_of_steps=50, command=lambda v: self.lbl_qual.configure(text=f"{int(v)}%"))
        self.slider_qual.set(85)
        self.slider_qual.pack(side="left", fill="x", expand=True, padx=(0, 10))

        self.btn_local = ctk.CTkButton(self.sidebar, text="Converter Pastas Locais", fg_color="#005580", command=self.converter_local)
        self.btn_local.pack(pady=(20, 10), padx=20, fill="x")

        self._on_dev_change("Kindle Paperwhite 11")

        # ---------------- MAIN AREA ----------------
        self.main = ctk.CTkFrame(self, fg_color="transparent")
        self.main.grid(row=0, column=1, sticky="nsew", padx=10, pady=10)
        self.main.grid_columnconfigure(0, weight=1)
        self.main.grid_rowconfigure(4, weight=1)

        self.entry_title = ctk.CTkEntry(self.main, placeholder_text="Título do Mangá (Obrigatório)", height=40)
        self.entry_title.grid(row=0, column=0, columnspan=2, sticky="ew", padx=10, pady=(10, 5))

        self.txt_urls = ctk.CTkTextbox(self.main, height=80)
        self.txt_urls.grid(row=1, column=0, sticky="ew", padx=10, pady=5)
        self.txt_urls.insert("0.0", "Cole os links dos capítulos aqui (um por linha)...")
        self.txt_urls.bind("<FocusIn>", lambda e: self.txt_urls.delete("0.0", "end") if "Cole os links" in self.txt_urls.get("1.0", "end-1c") else None)

        self.btn_analisar = ctk.CTkButton(self.main, text="CARREGAR\nLINKS", width=120, height=80, command=self.analisar)
        self.btn_analisar.grid(row=1, column=1, padx=10, pady=5)
        
        # --- GESTOR DE VOLUMES E CAPAS ---
        self.fr_assign = ctk.CTkFrame(self.main, fg_color="#1a1a1a", corner_radius=8)
        self.fr_assign.grid(row=2, column=0, columnspan=2, sticky="ew", padx=10, pady=10)
        
        ctk.CTkLabel(self.fr_assign, text="Agrupar Volume:", font=("Arial", 12, "bold")).pack(side="left", padx=10, pady=10)
        self.entry_assign = ctk.CTkEntry(self.fr_assign, placeholder_text="Ex: Volume 01", width=130)
        self.entry_assign.pack(side="left", padx=5)
        
        ctk.CTkButton(self.fr_assign, text="Atribuir Volume", fg_color="#005580", width=120, command=self.atribuir_volume).pack(side="left", padx=5)
        ctk.CTkButton(self.fr_assign, text="Atribuir Capa", fg_color="#b35900", width=120, command=self.atribuir_capa).pack(side="left", padx=5)
        ctk.CTkButton(self.fr_assign, text="Resetar", fg_color="#800000", width=100, command=self.resetar_volume).pack(side="left", padx=5)

        self.fr_selection = ctk.CTkFrame(self.main, fg_color="transparent")
        self.fr_selection.grid(row=3, column=0, columnspan=2, sticky="ew", padx=10, pady=0)
        ctk.CTkButton(self.fr_selection, text="Marcar Todos", fg_color="#333", width=100, command=self.selecionar_todos).pack(side="left", padx=5)
        ctk.CTkButton(self.fr_selection, text="Marcar Intervalo", fg_color="#333", width=110, command=self.selecionar_intervalo).pack(side="left", padx=5)
        ctk.CTkButton(self.fr_selection, text="Desmarcar Todos", fg_color="#555", width=110, command=self.limpar_selecao).pack(side="left", padx=5)
        
        self.scroll = ctk.CTkScrollableFrame(self.main, label_text="Capítulos (As caixas de seleção servem apenas para atribuir Volumes/Capas)")
        self.scroll.grid(row=4, column=0, columnspan=2, sticky="nsew", padx=10, pady=10)

        self.progress_bar = ctk.CTkProgressBar(self.main, height=15)
        self.progress_bar.grid(row=5, column=0, sticky="ew", padx=10, pady=10)
        self.progress_bar.set(0)

        self.btn_go = ctk.CTkButton(self.main, text="INICIAR DOWNLOAD E PROCESSAMENTO", height=45, fg_color="green", font=("Arial", 12, "bold"), command=self.start)
        self.btn_go.grid(row=5, column=1, sticky="ew", padx=10, pady=10)

        self.protocol("WM_DELETE_WINDOW", self.on_close)

    def _on_dev_change(self, val):
        p = self.presets.get(val)
        if not p: return

        # DOC: 'self.combo_stretch' foi removido desta lista de controlo
        widgets_control = [
            self.entry_w, self.entry_h, self.seg_double_page, 
            self.chk_rtl, self.chk_autocrop, self.chk_fill_screen, self.chk_gray, 
            self.slider_contrast, self.slider_qual, self.combo_fmt
        ]
        
        for w in widgets_control:
            w.configure(state="normal")
            
        self.combo_fmt.set(p['fmt'])
        
        self.entry_w.delete(0, 'end')
        if p['w']: self.entry_w.insert(0, p['w'])
        
        self.entry_h.delete(0, 'end')
        if p['h']: self.entry_h.insert(0, p['h'])
        
        self.var_rtl.set(p['rtl'])
        self.var_autocrop.set(p['crop'])
        self.var_fill_screen.set(p['fill'])
        self.var_gray.set(p['gray'])
        
        self.slider_contrast.set(p['contrast_val'])
        self.lbl_contrast_val.configure(text=f"{p['contrast_val']:.1f}")
        
        self.slider_qual.set(p['qual'])
        self.lbl_qual.configure(text=f"{int(p['qual'])}%")
        
        self.var_double_page.set(p['dp_mode'])

        if val != "Personalizado":
            for w in widgets_control:
                w.configure(state="disabled")
        else:
            self.combo_fmt.configure(state="readonly")

    def atribuir_volume(self):
        vol_name = self.entry_assign.get().strip()
        if not vol_name:
            messagebox.showwarning("Aviso", "Digite o nome do volume na caixa ao lado.")
            return
        for w in self.widgets:
            if w['var'].get():
                w['data']['vol'] = vol_name
                cover_txt = " | 🖼️ Capa OK" if w['data'].get('cover') else ""
                w['lbl_vol'].configure(text=f"📁 {vol_name}{cover_txt}")

    def atribuir_capa(self):
        selecionados = [w for w in self.widgets if w['var'].get()]
        if not selecionados:
            messagebox.showwarning("Aviso", "Selecione pelo menos um capítulo na lista marcando as caixas para atribuir uma capa.")
            return
            
        p = filedialog.askopenfilename(filetypes=[("Imagens", "*.jpg;*.png;*.webp")])
        if p:
            for w in selecionados:
                w['data']['cover'] = p
                vol_txt = w['data'].get('vol')
                prefix = f"📁 {vol_txt}" if vol_txt else "📄 Separado"
                w['lbl_vol'].configure(text=f"{prefix} | 🖼️ Capa OK")

    def resetar_volume(self):
        for w in self.widgets:
            if w['var'].get():
                w['data']['vol'] = None
                w['data']['cover'] = None
                w['lbl_vol'].configure(text="📄 Separado")

    def get_options(self):
        w = self.entry_w.get()
        h = self.entry_h.get()
        return {
            'rtl': self.var_rtl.get(),
            'autocrop': self.var_autocrop.get(),
            'grayscale': self.var_gray.get(),
            'contrast': (self.slider_contrast.get() > 1.0),
            'contrast_factor': float(self.slider_contrast.get()),
            'width': int(w) if w.isdigit() else 0,
            'height': int(h) if h.isdigit() else 0,
            'double_page_mode': self.var_double_page.get(),
            'quality': int(self.slider_qual.get()),
            'fill_screen': self.var_fill_screen.get()
        }

    def on_close(self):
        if self.info.get('title'):
            try: self.engine.clear_cache(self.base_dir, self.info['title'])
            except: pass
        self.destroy()

    def selecionar_todos(self):
        for w in self.widgets: w['var'].set(True)

    def limpar_selecao(self):
        for w in self.widgets: w['var'].set(False)

    def selecionar_intervalo(self):
        dialog = ctk.CTkInputDialog(text="Digite o intervalo (ex: 10-25):", title="Intervalo")
        entrada = dialog.get_input()
        if entrada and "-" in entrada:
            try:
                inicio, fim = map(float, entrada.split("-"))
                for w in self.widgets:
                    w['var'].set(inicio <= w['data']['num'] <= fim)
            except ValueError:
                messagebox.showerror("Erro", "Formato inválido. Use número-número (ex: 1-15).")
                
    def analisar(self):
        urls = self.txt_urls.get("1.0", "end-1c").strip().split('\n')
        manga_title = self.entry_title.get().strip()
        
        if not manga_title:
            messagebox.showerror("Aviso", "Por favor, digite o Título do Mangá.")
            return
        if not urls or urls[0] == "":
            messagebox.showerror("Aviso", "Por favor, cole os links dos capítulos.")
            return
            
        threading.Thread(target=self._th_an, args=(urls, manga_title), daemon=True).start()

    def _th_an(self, urls, manga_title):
        self.after(0, lambda: self.btn_analisar.configure(state="disabled", text="Analisando\nHTML..."))
        info, caps, msg = self.engine.analyze_links(urls, manga_title)
        
        if caps:
            self.info = info
            self.after(0, lambda: self._popula(caps))
        else:
            self.after(0, lambda: messagebox.showerror("Erro de Leitura", msg))
            
        self.after(0, lambda: self.btn_analisar.configure(state="normal", text="CARREGAR\nLINKS"))

    def _popula(self, caps):
        for w in self.widgets: w['frame'].destroy()
        self.widgets = []
        for i, c in enumerate(caps):
            c['vol'] = None
            c['cover'] = None
            
            f = ctk.CTkFrame(self.scroll, fg_color="transparent")
            f.pack(fill="x", pady=2)
            v = ctk.BooleanVar(value=True)
            chk = ctk.CTkCheckBox(f, text=c['name'], variable=v, width=140)
            chk.pack(side="left", padx=5)
            
            lbl_vol = ctk.CTkLabel(f, text="📄 Separado", text_color="#888", width=180, anchor="w")
            lbl_vol.pack(side="left", padx=5)
            
            lbl_status = ctk.CTkLabel(f, text="", width=90)
            lbl_status.pack(side="right", padx=5)
            
            c['gui_id'] = i
            self.widgets.append({'var': v, 'lbl_vol': lbl_vol, 'lbl_status': lbl_status, 'data': c, 'frame': f})

    def start(self):
        q = [w['data'] for w in self.widgets]
        if q:
            for w in self.widgets:
                w['lbl_status'].configure(text="Aguardando...", text_color="gray")
            
            self.btn_go.configure(state="disabled")
            self.progress_bar.set(0)
            threading.Thread(target=self._th_dl, args=(q,), daemon=True).start()
        else:
            messagebox.showwarning("Aviso", "Nenhum capítulo carregado para download.")

    def _th_dl(self, q):
        f = self.combo_fmt.get()
        opts = self.get_options()
        self.engine.download_queue(q, self.base_dir, f, self._upd, self.info.get('title', 'Manga'), opts)
        self.after(0, lambda: [self.btn_go.configure(state="normal"), messagebox.showinfo("Fim", "Processamento Concluído!")])

    def _upd(self, idx, msg, progresso):
        color = "green" if msg == "Pronto" else "orange"
        self.after(0, lambda: [
            self.widgets[idx]['lbl_status'].configure(text=msg, text_color=color),
            self.progress_bar.set(progresso)
        ])

    def converter_local(self):
        diretorio = filedialog.askdirectory(title="Selecione a pasta principal do Mangá")
        if diretorio:
            formato = self.combo_fmt.get()
            opts = self.get_options()
            
            self.btn_local.configure(text="Processando...", state="disabled")
            self.btn_go.configure(state="disabled")
            self.progress_bar.set(0)
            threading.Thread(target=self._th_local, args=(diretorio, formato, opts), daemon=True).start()

    def _th_local(self, diretorio, formato, opts):
        self.engine.convert_local_volumes(diretorio, formato, self._upd_local, opts)
        self.after(0, lambda: [
            self.btn_go.configure(state="normal"), 
            self.btn_local.configure(text="Converter Pastas Locais", state="normal"),
            messagebox.showinfo("Fim", "Conversão local concluída!")
        ])

    def _upd_local(self, msg, progresso):
        self.after(0, lambda: [
            self.btn_local.configure(text=msg) if msg != "Pronto" else None,
            self.progress_bar.set(progresso)
        ])

if __name__ == "__main__":
    App().mainloop()
