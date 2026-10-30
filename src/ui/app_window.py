import customtkinter as ctk
import threading
from tkinter import filedialog, messagebox
from src.core.engine import MangaEngine
from src.core.config import APP_TITLE, APP_GEOMETRY, APP_MIN_SIZE, DEFAULT_DOWNLOAD_DIR, DEVICE_PRESETS
from src.core.logger import logger

ctk.set_appearance_mode("Dark")

class MangaApp(ctk.CTk):
    """
    Main graphical user interface application window built using CustomTkinter,
    managing device profiles, conversion options, download queues, and real-time feedback.
    """
    def __init__(self):
        super().__init__()
        self.title(APP_TITLE)
        self.geometry(APP_GEOMETRY)
        self.minsize(*APP_MIN_SIZE)
        self.engine = MangaEngine()
        self.widgets = []
        self.info = {}
        self.base_dir = DEFAULT_DOWNLOAD_DIR

        self.grid_columnconfigure(1, weight=1)
        self.grid_rowconfigure(0, weight=1)

        # ---------------- SIDEBAR ----------------
        self.sidebar = ctk.CTkScrollableFrame(self, width=340, corner_radius=0)
        self.sidebar.grid(row=0, column=0, rowspan=2, sticky="nsew", padx=10, pady=10)

        ctk.CTkLabel(self.sidebar, text="📱 Device Profile", font=("Arial", 13, "bold"), text_color="#00a8cc").pack(anchor="w", padx=10, pady=(5, 5))
        
        self.presets = DEVICE_PRESETS
        self.combo_dev = ctk.CTkComboBox(self.sidebar, values=list(self.presets.keys()), command=self._on_device_change)
        self.combo_dev.pack(pady=5, padx=15, fill="x")
        
        self.fr_res = ctk.CTkFrame(self.sidebar, fg_color="transparent")
        self.fr_res.pack(fill="x", padx=15, pady=2)
        self.entry_w = ctk.CTkEntry(self.fr_res, width=70, placeholder_text="Width")
        self.entry_w.pack(side="left", padx=(0, 5))
        ctk.CTkLabel(self.fr_res, text="x").pack(side="left")
        self.entry_h = ctk.CTkEntry(self.fr_res, width=70, placeholder_text="Height")
        self.entry_h.pack(side="left", padx=(5, 0))

        ctk.CTkLabel(self.sidebar, text="📂 Output Format", font=("Arial", 13, "bold"), text_color="#00a8cc").pack(anchor="w", padx=10, pady=(15, 5))
        self.combo_fmt = ctk.CTkComboBox(self.sidebar, values=["epub", "pdf", "cbz"])
        self.combo_fmt.pack(pady=5, padx=15, fill="x")

        ctk.CTkLabel(self.sidebar, text="📖 Double Page Behavior", font=("Arial", 13, "bold"), text_color="#00a8cc").pack(anchor="w", padx=10, pady=(15, 5))
        self.var_double_page = ctk.StringVar(value="Rotacionar")
        self.seg_double_page = ctk.CTkSegmentedButton(self.sidebar, values=["Dividir", "Rotacionar", "Manter"], variable=self.var_double_page)
        self.seg_double_page.pack(pady=4, padx=15, fill="x")

        ctk.CTkLabel(self.sidebar, text="🔍 Resize Mode", font=("Arial", 13, "bold"), text_color="#00a8cc").pack(anchor="w", padx=10, pady=(15, 5))
        self.var_resize_mode = ctk.StringVar(value="Keep")
        self.seg_resize_mode = ctk.CTkSegmentedButton(self.sidebar, values=["Keep", "Stretch", "Zoom"], variable=self.var_resize_mode)
        self.seg_resize_mode.pack(pady=4, padx=15, fill="x")

        ctk.CTkLabel(self.sidebar, text="⚙️ Fine Visual Adjustments", font=("Arial", 13, "bold"), text_color="#00a8cc").pack(anchor="w", padx=10, pady=(15, 5))
        
        self.var_rtl = ctk.BooleanVar(value=True)
        self.chk_rtl = ctk.CTkCheckBox(self.sidebar, text="Eastern Reading (RTL)", variable=self.var_rtl)
        self.chk_rtl.pack(pady=4, padx=15, anchor="w")
        
        self.var_autocrop = ctk.BooleanVar(value=True)
        self.chk_autocrop = ctk.CTkCheckBox(self.sidebar, text="Auto-Crop (Remove Borders)", variable=self.var_autocrop)
        self.chk_autocrop.pack(pady=4, padx=15, anchor="w")
        
        self.var_gray = ctk.BooleanVar(value=True)
        self.chk_gray = ctk.CTkCheckBox(self.sidebar, text="Force Grayscale", variable=self.var_gray)
        self.chk_gray.pack(pady=4, padx=15, anchor="w")
        
        ctk.CTkLabel(self.sidebar, text="Contrast Adjustment (1.0 = Original):", font=("Arial", 11)).pack(anchor="w", padx=15, pady=(10, 0))
        self.fr_slider = ctk.CTkFrame(self.sidebar, fg_color="transparent")
        self.fr_slider.pack(fill="x", padx=15, pady=2)
        self.lbl_contrast_val = ctk.CTkLabel(self.fr_slider, text="1.2", font=("Arial", 11))
        self.lbl_contrast_val.pack(side="right")
        self.slider_contrast = ctk.CTkSlider(self.fr_slider, from_=1.0, to=2.0, number_of_steps=10, command=lambda v: self.lbl_contrast_val.configure(text=f"{v:.1f}"))
        self.slider_contrast.set(1.2)
        self.slider_contrast.pack(side="left", fill="x", expand=True, padx=(0, 10))

        ctk.CTkLabel(self.sidebar, text="Image Quality:", font=("Arial", 11)).pack(anchor="w", padx=15, pady=(10, 0))
        self.fr_qual = ctk.CTkFrame(self.sidebar, fg_color="transparent")
        self.fr_qual.pack(fill="x", padx=15, pady=2)
        self.lbl_qual = ctk.CTkLabel(self.fr_qual, text="85%", font=("Arial", 11))
        self.lbl_qual.pack(side="right")
        self.slider_qual = ctk.CTkSlider(self.fr_qual, from_=50, to=100, number_of_steps=50, command=lambda v: self.lbl_qual.configure(text=f"{int(v)}%"))
        self.slider_qual.set(85)
        self.slider_qual.pack(side="left", fill="x", expand=True, padx=(0, 10))

        self.btn_local = ctk.CTkButton(self.sidebar, text="Convert Local Folders", fg_color="#005580", command=self.convert_local_folders)
        self.btn_local.pack(pady=(20, 10), padx=20, fill="x")

        self._on_device_change("Kindle Paperwhite 11")

        # ---------------- MAIN AREA  ----------------

        self.main = ctk.CTkFrame(self, fg_color="transparent")
        self.main.grid(row=0, column=1, sticky="nsew", padx=10, pady=10)
        
        self.main.grid_columnconfigure(0, weight=1)
        self.main.grid_rowconfigure(4, weight=1) 

        self.entry_title = ctk.CTkEntry(self.main, placeholder_text="Manga Title (Required)", height=35)
        self.entry_title.grid(row=0, column=0, columnspan=2, sticky="ew", padx=5, pady=(0, 5))

        self.txt_urls = ctk.CTkTextbox(self.main, height=70)
        self.txt_urls.grid(row=1, column=0, sticky="nsew", padx=5, pady=0) # nsew faz a caixa esticar
        self.txt_urls.insert("0.0", "Paste chapter links here (one per line)...")
        self.txt_urls.bind("<FocusIn>", lambda e: self.txt_urls.delete("0.0", "end") if "Paste chapter links" in self.txt_urls.get("1.0", "end-1c") else None)

        self.btn_analyze = ctk.CTkButton(self.main, text="LOAD LINKS", width=100, command=self.analyze_chapters)
        self.btn_analyze.grid(row=1, column=1, sticky="nsew", padx=(5, 5), pady=0) 
        
        self.fr_assign = ctk.CTkFrame(self.main, fg_color="#1a1a1a", corner_radius=6)
        self.fr_assign.grid(row=2, column=0, columnspan=2, sticky="ew", padx=5, pady=(10, 5))
        
        for i in range(1, 5): 
            self.fr_assign.grid_columnconfigure(i, weight=1)
            
        ctk.CTkLabel(self.fr_assign, text="Vol:", font=("Arial", 11, "bold")).grid(row=0, column=0, sticky="e", padx=(10, 2), pady=5)
        self.entry_assign = ctk.CTkEntry(self.fr_assign, placeholder_text="Ex: Vol 01", height=28)
        self.entry_assign.grid(row=0, column=1, sticky="ew", padx=2, pady=5)
        
        ctk.CTkButton(self.fr_assign, text="Set Vol", fg_color="#005580", height=28, command=self.assign_volume).grid(row=0, column=2, sticky="ew", padx=2, pady=5)
        ctk.CTkButton(self.fr_assign, text="Set Cover", fg_color="#b35900", height=28, command=self.assign_cover).grid(row=0, column=3, sticky="ew", padx=2, pady=5)
        ctk.CTkButton(self.fr_assign, text="Reset", fg_color="#800000", height=28, command=self.reset_selection).grid(row=0, column=4, sticky="ew", padx=(2, 10), pady=5)

        # --- SELECTION MANAGER ---
        self.fr_selection = ctk.CTkFrame(self.main, fg_color="transparent")
        self.fr_selection.grid(row=3, column=0, columnspan=2, sticky="ew", padx=5, pady=0)
        
        for i in range(3):
            self.fr_selection.grid_columnconfigure(i, weight=1)
            
        ctk.CTkButton(self.fr_selection, text="Select All", fg_color="#333", height=26, command=self.select_all).grid(row=0, column=0, sticky="ew", padx=2)
        ctk.CTkButton(self.fr_selection, text="Select Range", fg_color="#333", height=26, command=self.select_range).grid(row=0, column=1, sticky="ew", padx=2)
        ctk.CTkButton(self.fr_selection, text="Deselect All", fg_color="#555", height=26, command=self.clear_selection).grid(row=0, column=2, sticky="ew", padx=2)
        
        self.scroll = ctk.CTkScrollableFrame(self.main, label_text="Chapters (Checkboxes are used exclusively for assigning Volumes/Covers)")
        self.scroll.grid(row=4, column=0, columnspan=2, sticky="nsew", padx=5, pady=(5, 10))

        self.progress_bar = ctk.CTkProgressBar(self.main, height=15)
        self.progress_bar.grid(row=5, column=0, sticky="ew", padx=5, pady=(0, 5))
        self.progress_bar.set(0)

        self.btn_go = ctk.CTkButton(self.main, text="Start Download", height=35, fg_color="green", font=("Arial", 12, "bold"), command=self.start_process)
        self.btn_go.grid(row=5, column=1, sticky="ew", padx=5, pady=(0, 5))

        self.protocol("WM_DELETE_WINDOW", self.on_close)

    def _on_device_change(self, val):
        p = self.presets.get(val)
        if not p: 
            return

        widgets_control = [
            self.entry_w, self.entry_h, self.seg_double_page, 
            self.chk_rtl, self.chk_autocrop, self.seg_resize_mode, self.chk_gray, 
            self.slider_contrast, self.slider_qual, self.combo_fmt
        ]
        
        for w in widgets_control:
            w.configure(state="normal")
            
        self.combo_fmt.set(p['fmt'])
        
        self.entry_w.delete(0, 'end')
        if p['w']: 
            self.entry_w.insert(0, p['w'])
        
        self.entry_h.delete(0, 'end')
        if p['h']: 
            self.entry_h.insert(0, p['h'])
        
        self.var_rtl.set(p['rtl'])
        self.var_autocrop.set(p['crop'])
        self.var_resize_mode.set(p['resize'])
        self.var_gray.set(p['gray'])
        
        self.slider_contrast.set(p['contrast_val'])
        self.lbl_contrast_val.configure(text=f"{p['contrast_val']:.1f}")
        
        self.slider_qual.set(p['qual'])
        self.lbl_qual.configure(text=f"{int(p['qual'])}%")
        
        self.var_double_page.set(p['dp_mode'])

        if val != "Custom":
            for w in widgets_control:
                w.configure(state="disabled")
        else:
            self.combo_fmt.configure(state="readonly")

    def assign_volume(self):
        vol_name = self.entry_assign.get().strip()
        if not vol_name:
            messagebox.showwarning("Warning", "Please enter the volume name in the adjacent box.")
            return
        for w in self.widgets:
            if w['var'].get():
                w['data']['vol'] = vol_name
                cover_txt = " | 🖼️ Cover OK" if w['data'].get('cover') else ""
                w['lbl_vol'].configure(text=f"📁 {vol_name}{cover_txt}")

    def assign_cover(self):
        selected = [w for w in self.widgets if w['var'].get()]
        if not selected:
            messagebox.showwarning("Warning", "Select at least one chapter by checking the boxes to assign a cover.")
            return
            
        path = filedialog.askopenfilename(filetypes=[("Images", "*.jpg;*.png;*.webp")])
        if path:
            for w in selected:
                w['data']['cover'] = path
                vol_txt = w['data'].get('vol')
                prefix = f"📁 {vol_txt}" if vol_txt else "📄 Individual"
                w['lbl_vol'].configure(text=f"{prefix} | 🖼️ Cover OK")

    def reset_selection(self):
        for w in self.widgets:
            if w['var'].get():
                w['data']['vol'] = None
                w['data']['cover'] = None
                w['lbl_vol'].configure(text="📄 Individual")

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
            'resize_mode': self.var_resize_mode.get()
        }

    def on_close(self):
        if self.info.get('title'):
            try: 
                self.engine.clear_cache(self.base_dir, self.info['title'])
            except Exception: 
                pass
        self.destroy()

    def select_all(self):
        for w in self.widgets: 
            w['var'].set(True)

    def clear_selection(self):
        for w in self.widgets: 
            w['var'].set(False)

    def select_range(self):
        dialog = ctk.CTkInputDialog(text="Enter range (e.g., 10-25):", title="Range Selection")
        entry = dialog.get_input()
        if entry and "-" in entry:
            try:
                start, end = map(float, entry.split("-"))
                for w in self.widgets:
                    w['var'].set(start <= w['data']['num'] <= end)
            except ValueError:
                messagebox.showerror("Error", "Invalid format. Use number-number (e.g., 1-15).")
                
    def analyze_chapters(self):
        urls = self.txt_urls.get("1.0", "end-1c").strip().split('\n')
        manga_title = self.entry_title.get().strip()
        
        if not manga_title:
            messagebox.showerror("Warning", "Please enter the Manga Title.")
            return
        if not urls or urls[0] == "":
            messagebox.showerror("Warning", "Please paste the chapter links.")
            return
            
        threading.Thread(target=self._thread_analyze, args=(urls, manga_title), daemon=True).start()

    def _thread_analyze(self, urls, manga_title):
        self.after(0, lambda: self.btn_analyze.configure(state="disabled", text="Analyzing\nHTML..."))
        info, chapters, msg = self.engine.analyze_links(urls, manga_title)
        
        if chapters:
            self.info = info
            self.after(0, lambda: self._populate_list(chapters))
        else:
            self.after(0, lambda: messagebox.showerror("Reading Error", msg))
            
        self.after(0, lambda: self.btn_analyze.configure(state="normal", text="LOAD\nLINKS"))

    def _populate_list(self, chapters):
        for w in self.widgets: 
            w['frame'].destroy()
        self.widgets = []
        for i, c in enumerate(chapters):
            c['vol'] = None
            c['cover'] = None
            
            f = ctk.CTkFrame(self.scroll, fg_color="transparent", height=25)
            f.pack(fill="x", pady=1) 
            f.pack_propagate(False) 
            
            v = ctk.BooleanVar(value=True)
            chk = ctk.CTkCheckBox(f, text=c['name'], variable=v, width=140, checkbox_width=18, checkbox_height=18, font=("Arial", 12))
            chk.pack(side="left", padx=5, pady=2)
            
            # Adicionado o 'expand=True, fill="x"' aqui para o texto central preencher o vazio
            lbl_vol = ctk.CTkLabel(f, text="📄 Individual", text_color="#888", anchor="w", font=("Arial", 11))
            lbl_vol.pack(side="left", padx=5, expand=True, fill="x")
            
            lbl_status = ctk.CTkLabel(f, text="", width=90, font=("Arial", 11))
            lbl_status.pack(side="right", padx=5)
            
            c['gui_id'] = i
            self.widgets.append({'var': v, 'lbl_vol': lbl_vol, 'lbl_status': lbl_status, 'data': c, 'frame': f})

    def start_process(self):
        q = [w['data'] for w in self.widgets]
        if q:
            for w in self.widgets:
                w['lbl_status'].configure(text="Waiting...", text_color="gray")
            
            self.btn_go.configure(state="disabled")
            self.progress_bar.set(0)
            threading.Thread(target=self._thread_download, args=(q,), daemon=True).start()
        else:
            messagebox.showwarning("Warning", "No chapters loaded for download.")

    def _thread_download(self, q):
        f = self.combo_fmt.get()
        opts = self.get_options()
        self.engine.download_queue(q, self.base_dir, f, self._update_status, self.info.get('title', 'Manga'), opts)
        logger.info("Manga download and conversion batch completed successfully.")
        self.after(0, lambda: [self.btn_go.configure(state="normal"), messagebox.showinfo("Done", "Processing Completed!")])

    def _update_status(self, idx, msg, progress):
        color = "green" if msg == "Ready" else "orange"
        self.after(0, lambda: [
            self.widgets[idx]['lbl_status'].configure(text=msg, text_color=color),
            self.progress_bar.set(progress)
        ])

    def convert_local_folders(self):
        directory = filedialog.askdirectory(title="Select Main Manga Directory")
        if directory:
            format_type = self.combo_fmt.get()
            opts = self.get_options()
            
            self.btn_local.configure(text="Processing...", state="disabled")
            self.btn_go.configure(state="disabled")
            self.progress_bar.set(0)
            threading.Thread(target=self._thread_local_conversion, args=(directory, format_type, opts), daemon=True).start()

    def _thread_local_conversion(self, directory, format_type, opts):
        self.engine.convert_local_volumes(directory, format_type, self._update_local_status, opts)
        logger.info("Local folder conversion batch completed successfully.")
        self.after(0, lambda: [
            self.btn_go.configure(state="normal"), 
            self.btn_local.configure(text="Convert Local Folders", state="normal"),
            messagebox.showinfo("Done", "Local conversion completed!")
        ])

    def _update_local_status(self, msg, progress):
        self.after(0, lambda: [
            self.btn_local.configure(text=msg) if msg != "Ready" else None,
            self.progress_bar.set(progress)
        ])
