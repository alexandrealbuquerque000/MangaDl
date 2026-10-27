import os, re, json, requests, shutil, concurrent.futures, stat, statistics
from bs4 import BeautifulSoup
from PIL import Image
from io import BytesIO
import converters

class Engine:
    def __init__(self, config_filename="sites.json"):
        import sys
        self.root_dir = os.path.dirname(sys.executable) if getattr(sys, 'frozen', False) else os.path.dirname(os.path.abspath(__file__))
        self.config_path = os.path.join(self.root_dir, config_filename)
        self.session = requests.Session()
        self.session.headers.update({'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) Chrome/120.0.0.0 Safari/537.36'})
        self.sites = self._load_cfg()
        
        self.TAG_IMAGEM = "img"
        self.ATRIBUTOS_POSSIVEIS = ["data-src", "data-lazy-src", "src"]

    def _load_cfg(self):
        try:
            with open(self.config_path, 'r', encoding='utf-8') as f: return json.load(f)
        except: return {}

    def get_preview_img(self, url):
        try:
            r = self.session.get(url, timeout=10)
            return Image.open(BytesIO(r.content))
        except: return None

    def analyze_links(self, urls, manga_title):
        info = {'title': manga_title}
        mensagens_gui = []
        domain_rules = {}
        
        unique_domains = {}
        for u in urls:
            u = u.strip()
            if not u: continue
            domain = u.split('/')[2] if '//' in u else u.split('/')[0]
            domain = domain.replace('www.', '')
            if domain not in unique_domains: unique_domains[domain] = u

        for domain, u in unique_domains.items():
            regras = None
            for k, v in self.sites.items():
                chave_limpa = k.replace('https://', '').replace('http://', '').replace('www.', '')
                if chave_limpa in domain or chave_limpa in u:
                    regras = v
                    break

            if not regras:
                try:
                    r = self.session.get(u, timeout=10)
                    soup = BeautifulSoup(r.content, 'html.parser')
                    found = False
                    for site_key, site_data in self.sites.items():
                        sel_container = site_data['selectors'].get('container_imagens')
                        sel_nome = site_data['selectors'].get('nome_capitulo', 'title') 
                        
                        if sel_container:
                            cont = soup.select_one(sel_container)
                            if cont and cont.select(self.TAG_IMAGEM):
                                regras = {'selectors': {'container_imagens': sel_container, 'nome_capitulo': sel_nome}}
                                mensagens_gui.append(f"✅ Site '{domain}' autodetectado com sucesso!")
                                domain_rules[domain] = regras
                                found = True
                                break
                    if not found:
                        domain_rules[domain] = None
                except:
                    domain_rules[domain] = None
            else:
                domain_rules[domain] = regras

        caps = []
        def process_url(i, u):
            u = u.strip()
            if not u: return None
            domain = u.split('/')[2] if '//' in u else u.split('/')[0]
            domain = domain.replace('www.', '')
            regras = domain_rules.get(domain)
            if not regras: return None 
            
            name = None
            sel_nome = regras['selectors'].get('nome_capitulo', 'title')
            try:
                r = self.session.get(u, timeout=5)
                soup = BeautifulSoup(r.content, 'html.parser')
                name_el = soup.select_one(sel_nome)
                if name_el: name = name_el.get_text(strip=True)
            except: pass
            
            if not name:
                match = re.search(r'(?:capitulo|cap|c|-)(\d+(?:\.\d+)?)', u.lower())
                num = float(match.group(1)) if match else float(i + 1)
                name = f"Capítulo {num:03g}"
                
            match_num = re.search(r'(\d+(?:\.\d+)?)', name)
            num = float(match_num.group(1)) if match_num else float(i + 1)
            
            return {'name': name, 'folder': f"Cap_{num:03g}", 'url': u, 'num': num, 'rules': regras}

        with concurrent.futures.ThreadPoolExecutor(max_workers=10) as executor:
            futures = [executor.submit(process_url, i, u) for i, u in enumerate(urls)]
            for future in concurrent.futures.as_completed(futures):
                res = future.result()
                if res: caps.append(res)
                    
        if not caps:
            return None, None, "Nenhum link com site suportado foi encontrado."
            
        return info, sorted(caps, key=lambda x: x['num']), ("OK" if not mensagens_gui else "\n".join(mensagens_gui))

    def clean_chapter_images(self, chapter_path):
        arquivos = sorted([f for f in os.listdir(chapter_path) if f.lower().endswith(('.jpg', '.png', '.webp', '.jpeg'))])
        
        for arq in arquivos:
            p = os.path.join(chapter_path, arq)
            if os.path.getsize(p) <= 15360:
                try: os.remove(p)
                except: pass
                
        arquivos = sorted([f for f in os.listdir(chapter_path) if f.lower().endswith(('.jpg', '.png', '.webp', '.jpeg'))])
        if len(arquivos) < 5: return 
            
        first_path = os.path.join(chapter_path, arquivos[0])
        second_path = os.path.join(chapter_path, arquivos[1])
        
        last_path = os.path.join(chapter_path, arquivos[-1])
        prev_last_path = os.path.join(chapter_path, arquivos[-2])
        
        try:
            with Image.open(first_path) as img_first, Image.open(second_path) as img_sec:
                colors_first = len(img_first.convert("L").getcolors(maxcolors=100000) or [])
                colors_sec = len(img_sec.convert("L").getcolors(maxcolors=100000) or [])
                if img_first.height != img_sec.height or colors_first < (colors_sec * 0.4):
                    os.remove(first_path)
        except: pass

        try:
            with Image.open(last_path) as img_last, Image.open(prev_last_path) as img_prev:
                colors_last = len(img_last.convert("L").getcolors(maxcolors=100000) or [])
                colors_prev = len(img_prev.convert("L").getcolors(maxcolors=100000) or [])
                if img_last.height != img_prev.height or colors_last < (colors_prev * 0.4):
                    os.remove(last_path)
        except: pass

    def download_queue(self, queue, base_path, format, status_cb, manga_title, options):
        manga_path = os.path.join(base_path, manga_title)
        os.makedirs(manga_path, exist_ok=True)
        
        volumes_dict = {}
        for q in queue:
            vol_assigned = q.get('vol')
            if not vol_assigned:
                vol_assigned = f"__INDIVIDUAL__{q['folder']}"
                
            if vol_assigned not in volumes_dict:
                volumes_dict[vol_assigned] = {'chapters': [], 'cover': q.get('cover'), 'is_individual': vol_assigned.startswith('__INDIVIDUAL__')}
            
            volumes_dict[vol_assigned]['chapters'].append(q)
            if q.get('cover'):
                volumes_dict[vol_assigned]['cover'] = q.get('cover')

        total_chapters = len(queue)
        processed_chapters = 0

        for vol_key, data in volumes_dict.items():
            vol_queue = data['chapters']
            vol_cover = data['cover']
            is_individual = data['is_individual']
            
            real_vol_name = vol_queue[0]['folder'] if is_individual else vol_key
            capa_final = converters.preparar_capa(vol_cover, manga_path, options) if vol_cover else None
            processed_paths = []
            
            for item in vol_queue:
                path = os.path.join(manga_path, item['folder'])
                status_cb(item['gui_id'], f"A Baixar...", processed_chapters / total_chapters)
                
                if not (os.path.exists(path) and len(os.listdir(path)) > 2):
                    os.makedirs(path, exist_ok=True)
                    try:
                        s = BeautifulSoup(self.session.get(item['url']).content, 'html.parser')
                        cont = s.select_one(item['rules']['selectors']['container_imagens'])
                        
                        imgs = (cont if cont else s).select(self.TAG_IMAGEM)
                        urls = [img.get(attr).strip() for img in imgs for attr in self.ATRIBUTOS_POSSIVEIS if img.get(attr)]
                        urls = list(dict.fromkeys(urls)) 
                        
                        with concurrent.futures.ThreadPoolExecutor(max_workers=8) as ex:
                            for idx, u in enumerate(urls, 1):
                                if u.startswith('//'): u = "https:" + u
                                ex.submit(self._save, u, os.path.join(path, f"{idx:04d}.jpg"))
                                
                        self.clean_chapter_images(path)
                    except: pass
                
                processed_paths.append(path)
                processed_chapters += 1
                status_cb(item['gui_id'], "Pronto", processed_chapters / total_chapters)

            output_dest = os.path.join(manga_path, real_vol_name)
            self._convert(format, processed_paths, output_dest, capa_final, options, cover_source=vol_cover)

    def _convert(self, fmt, paths, dest, capa, options, cover_source=None):
        if fmt == 'epub': converters.criar_epub(paths, dest, capa, options, cover_source=cover_source)
        elif fmt == 'pdf': converters.criar_pdf(paths, dest, capa, options, cover_source=cover_source)
        elif fmt == 'cbz': converters.criar_cbz(paths, dest, capa, options, cover_source=cover_source)

    def _save(self, url, path):
        try:
            r = self.session.get(url, timeout=15)
            with open(path, 'wb') as f: f.write(r.content)
            return True
        except: return False

    def convert_local_volumes(self, manga_path, format, status_cb, options):
        try:
            volumes = [d for d in os.listdir(manga_path) if os.path.isdir(os.path.join(manga_path, d))]
            volumes.sort()
            if not volumes:
                status_cb("Nenhuma pasta encontrada.", 1.0)
                return

            for i, vol_name in enumerate(volumes):
                vol_path = os.path.join(manga_path, vol_name)
                status_cb(f"A converter {vol_name}...", i / len(volumes))
                
                subpastas = [os.path.join(vol_path, c) for c in os.listdir(vol_path) if os.path.isdir(os.path.join(vol_path, c))]
                subpastas.sort()
                paths_para_converter = subpastas if subpastas else [vol_path]
                dest = os.path.join(manga_path, vol_name) 
                
                capa_local = None
                for arquivo in os.listdir(vol_path):
                    if arquivo.lower().startswith('cover.') and arquivo.lower().endswith(('.jpg', '.jpeg', '.png', '.webp')):
                        capa_local = os.path.join(vol_path, arquivo)
                        break 
                
                capa_final = converters.preparar_capa(capa_local, manga_path, options) if capa_local else None
                
                self._convert(format, paths_para_converter, dest, capa_final, options, cover_source=capa_local)
            status_cb("Pronto", 1.0)
        except Exception as e:
            status_cb("Erro na conversão", 1.0)

    def clear_cache(self, base_path, manga_title):
        manga_path = os.path.join(base_path, manga_title)
        if os.path.exists(manga_path):
            for item in os.listdir(manga_path):
                item_path = os.path.join(manga_path, item)
                if os.path.isdir(item_path): shutil.rmtree(item_path, onexc=self._force_remove)
                elif "cover_" in item: os.remove(item_path)

    def _force_remove(self, func, path, _):
        os.chmod(path, stat.S_IWRITE)
        func(path)
