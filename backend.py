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
        
        # DOC: Cabeçalhos avançados para simular um navegador real e evitar bloqueio anti-bot.
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8',
            'Accept-Language': 'pt-PT,pt;q=0.9,en-US;q=0.8,en;q=0.7'
        })
        
        self.sites = self._load_cfg()
        self.TAG_IMAGEM = "img"
        # DOC: Lista expandida para capturar imagens ocultas por lazy-loading em qualquer site.
        self.ATRIBUTOS_POSSIVEIS = ["data-src", "data-lazy-src", "data-altsrc", "data-v-image", "src"]

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
                if img_first.height != img_sec.height or colors_first < (colors_sec * 0.4): os.remove(first_path)
        except: pass
        try:
            with Image.open(last_path) as img_last, Image.open(prev_last_path) as img_prev:
                colors_last = len(img_last.convert("L").getcolors(maxcolors=100000) or [])
                colors_prev = len(img_prev.convert("L").getcolors(maxcolors=100000) or [])
                if img_last.height != img_prev.height or colors_last < (colors_prev * 0.4): os.remove(last_path)
        except: pass

    def download_queue(self, queue, base_path, format, status_cb, manga_title, options):
        manga_path = os.path.join(base_path, manga_title)
        os.makedirs(manga_path, exist_ok=True)
        
        volumes_dict = {}
        for q in queue:
            vol_assigned = q.get('vol')
            if not vol_assigned: vol_assigned = f"__INDIVIDUAL__{q['folder']}"
            if vol_assigned not in volumes_dict:
                volumes_dict[vol_assigned] = {'chapters': [], 'cover': q.get('cover'), 'is_individual': vol_assigned.startswith('__INDIVIDUAL__')}
            volumes_dict[vol_assigned]['chapters'].append(q)
            if q.get('cover'): volumes_dict[vol_assigned]['cover'] = q.get('cover')

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
                        r_main = self.session.get(item['url'], timeout=15)
                        s = BeautifulSoup(r_main.content, 'html.parser')
                        cont = s.select_one(item['rules']['selectors']['container_imagens'])
                        
                        urls = []
                        hx_url = None
                        
                        # DOC: ESTRATÉGIA 1 - Injeção Dinâmica e HTMX
                        if cont:
                            if cont.has_attr('hx-get'):
                                from urllib.parse import urljoin
                                hx_url = urljoin(item['url'], cont.get('hx-get'))
                            elif "weebcentral.com" in item['url']:
                                hx_url = item['url'].rstrip('/') + '/images'
                            
                            if hx_url:
                                headers_htmx = {'HX-Request': 'true', 'Referer': item['url']}
                                r_dinamico = self.session.get(hx_url, headers=headers_htmx, timeout=15)
                                s_dinamico = BeautifulSoup(r_dinamico.content, 'html.parser')
                                imgs = s_dinamico.select(self.TAG_IMAGEM)
                                
                                for img in imgs:
                                    for attr in self.ATRIBUTOS_POSSIVEIS:
                                        val = img.get(attr)
                                        if val:
                                            urls.append(val.strip())
                                            break
                        
                        # DOC: ESTRATÉGIA 2 - Expressões Regulares para Javascript/JSON
                        if not urls:
                            scripts = s.find_all('script')
                            for script in scripts:
                                if script.string:
                                    texto_limpo = script.string.replace('\\/', '/')
                                    encontrados = re.findall(r'["\'](https?://[^\s<>"\']+?\.(?:jpg|jpeg|png|webp))["\']', texto_limpo, re.IGNORECASE)
                                    if encontrados: urls.extend(encontrados)
                        
                        # DOC: ESTRATÉGIA 3 - Varredura agressiva clássica
                        if not urls:
                            imgs = (cont if cont else s).select(self.TAG_IMAGEM)
                            for img in imgs:
                                for attr in self.ATRIBUTOS_POSSIVEIS:
                                    val = img.get(attr)
                                    if val and val.startswith(('http', '//')):
                                        urls.append(val.strip())
                                        break
                        
                        urls = list(dict.fromkeys(urls)) 
                        urls = ["https:" + u if u.startswith('//') else u for u in urls]
                        
                        # DOC: Envio do URL original para enganar a proteção do servidor final
                        with concurrent.futures.ThreadPoolExecutor(max_workers=8) as ex:
                            for idx, u in enumerate(urls, 1):
                                ex.submit(self._save, u, os.path.join(path, f"{idx:04d}.jpg"), item['url'])
                                
                        self.clean_chapter_images(path)
                    except Exception as e:
                        pass
                
                processed_paths.append(path)
                processed_chapters += 1
                status_cb(item['gui_id'], "Pronto", processed_chapters / total_chapters)

            output_dest = os.path.join(manga_path, real_vol_name)
            self._convert(format, processed_paths, output_dest, capa_final, options, cover_source=vol_cover)

    def _convert(self, fmt, paths, dest, capa, options, cover_source=None):
        if fmt == 'epub': converters.criar_epub(paths, dest, capa, options, cover_source=cover_source)
        elif fmt == 'pdf': converters.criar_pdf(paths, dest, capa, options, cover_source=cover_source)
        elif fmt == 'cbz': converters.criar_cbz(paths, dest, capa, options, cover_source=cover_source)

    def _save(self, url, path, referer_url=None):
        # DOC: Bypass para hotlinking - O servidor exige saber a origem do pedido
        try:
            headers_imagem = {'Referer': referer_url} if referer_url else {}
            r = self.session.get(url, headers=headers_imagem, timeout=15)
            if r.status_code == 200:
                with open(path, 'wb') as f: f.write(r.content)
                return True
            else:
                return False
        except Exception as e: 
            return False

    def convert_local_volumes(self, manga_path, format, status_cb, options):
        try:
            volumes = [d for d in os.listdir(manga_path) if os.path.isdir(os.path.join(manga_path, d))]
            volumes.sort()
            if not volumes: return status_cb("Nenhuma pasta encontrada.", 1.0)
            for i, vol_name in enumerate(volumes):
                vol_path = os.path.join(manga_path, vol_name)
                status_cb(f"A converter {vol_name}...", i / len(volumes))
                subpastas = [os.path.join(vol_path, c) for c in os.listdir(vol_path) if os.path.isdir(os.path.join(vol_path, c))]
                subpastas.sort()
                paths_para_converter = subpastas if subpastas else [vol_path]
                dest = os.path.join(manga_path, vol_name) 
                capa_local = next((os.path.join(vol_path, f) for f in os.listdir(vol_path) if f.lower().startswith('cover.') and f.lower().endswith(('.jpg', '.jpeg', '.png', '.webp'))), None)
                capa_final = converters.preparar_capa(capa_local, manga_path, options) if capa_local else None
                self._convert(format, paths_para_converter, dest, capa_final, options, cover_source=capa_local)
            status_cb("Pronto", 1.0)
        except Exception as e: status_cb("Erro na conversão", 1.0)

    def clear_cache(self, base_path, manga_title):
        manga_path = os.path.join(base_path, manga_title)
        if os.path.exists(manga_path):
            for item in os.listdir(manga_path):
                item_path = os.path.join(manga_path, item)
                # DOC: Reposição da função padrão onerror para evitar erros de remoção forçada
                if os.path.isdir(item_path): shutil.rmtree(item_path, onerror=self._force_remove)
                elif "cover_" in item: os.remove(item_path)

    def _force_remove(self, func, path, _):
        os.chmod(path, stat.S_IWRITE)
        func(path)
