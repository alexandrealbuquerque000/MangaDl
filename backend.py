import os, re, json, requests, shutil, concurrent.futures, stat
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

    def _load_cfg(self):
        try:
            with open(self.config_path, 'r', encoding='utf-8') as f: return json.load(f)
        except: return {}

    def get_preview_img(self, url):
        try:
            r = self.session.get(url, timeout=10)
            return Image.open(BytesIO(r.content))
        except: return None

    def analyze(self, url):
        url = url.strip()
        regras = next((v for k, v in self.sites.items() if k in url), None)
        if not regras: return None, None, "Site não suportado."
        try:
            r = self.session.get(url, timeout=10)
            soup = BeautifulSoup(r.content, 'html.parser')
            info = {'title': 'Manga', 'cover': None}
            t_el = soup.select_one(regras['selectors']['titulo_manga'])
            if t_el: info['title'] = re.sub(r'[<>:"/\\|?*]', '', t_el.get_text(strip=True))
            c_el = soup.select_one(regras['selectors'].get('capa', 'img'))
            if c_el: 
                src = c_el.get('data-src') or c_el.get('src')
                if src: info['cover'] = src if src.startswith('http') else "https:" + src
            caps = []
            els = soup.select(regras['selectors']['lista_capitulos'])
            for el in els:
                a = el if el.name == 'a' else el.select_one('a')
                if a and a.get('href'):
                    href = a['href']
                    if not href.startswith('http'): href = "https://" + url.split('/')[2] + href
                    name = a.get_text(strip=True)
                    match = re.search(r'(\d+)', name)
                    num = float(match.group(1)) if match else 0.0
                    caps.append({'name': name, 'folder': f"Cap_{num:03g}", 'url': href, 'num': num, 'rules': regras})
            return info, sorted(caps, key=lambda x: x['num']), "OK"
        except: return None, None, "Falha na análise."

    def download_queue(self, queue, base_path, mode, format, vol_name, cover_input, status_cb, manga_title):
        manga_path = os.path.join(base_path, manga_title)
        os.makedirs(manga_path, exist_ok=True)
        
        capa_final = None
        if mode == 'volume': # Capa apenas em volume agrupado
            capa_final = converters.preparar_capa(cover_input, manga_path)
            if not capa_final and queue[0].get('cover'):
                try:
                    r = self.session.get(queue[0]['cover'])
                    capa_final = os.path.join(manga_path, "web_cover.jpg")
                    with open(capa_final, 'wb') as f: f.write(r.content)
                except: pass

        processed = []
        for i, item in enumerate(queue):
            path = os.path.join(manga_path, item['folder'])
            status_cb(item['gui_id'], "Baixando...", i / len(queue))
            if not (os.path.exists(path) and len(os.listdir(path)) > 2):
                os.makedirs(path, exist_ok=True)
                try:
                    s = BeautifulSoup(self.session.get(item['url']).content, 'html.parser')
                    cont = s.select_one(item['rules']['selectors']['container_imagens'])
                    imgs = (cont if cont else s).select(item['rules']['selectors']['tag_imagem'])
                    urls = [i.get(attr) for i in imgs for attr in item['rules']['selectors']['atributos_possiveis'] if i.get(attr)]
                    urls = [u.strip() if u.startswith('http') else "https:"+u.strip() for u in urls]
                    with concurrent.futures.ThreadPoolExecutor(max_workers=8) as ex:
                        for idx, u in enumerate(list(dict.fromkeys(urls)), 1):
                            ex.submit(self._save, u, os.path.join(path, f"{idx:04d}.jpg"))
                except: pass
            
            processed.append(path)
            if mode == 'single':
                self._convert(format, [path], os.path.join(manga_path, item['folder']), None)
            status_cb(item['gui_id'], "Pronto", (i + 1) / len(queue))

        if mode == 'volume':
            self._convert(format, processed, os.path.join(manga_path, vol_name), capa_final)

    def _convert(self, fmt, paths, dest, capa):
        if fmt == 'epub': converters.criar_epub(paths, dest, capa)
        elif fmt == 'pdf': converters.criar_pdf(paths, dest, capa)
        elif fmt == 'cbz': converters.criar_cbz(paths, dest, capa)

    def _save(self, url, path):
        try:
            r = self.session.get(url, timeout=15)
            with open(path, 'wb') as f: f.write(r.content)
            return True
        except: return False

    def clear_cache(self, base_path, manga_title):
        """Limpa pastas e ficheiros temporários."""
        manga_path = os.path.join(base_path, manga_title)
        if os.path.exists(manga_path):
            for item in os.listdir(manga_path):
                item_path = os.path.join(manga_path, item)
                if os.path.isdir(item_path):
                    shutil.rmtree(item_path, onexc=self._force_remove)
                elif "cover_final" in item or "web_cover" in item: # Remove capas temporárias
                    os.remove(item_path)

    def _force_remove(self, func, path, _):
        os.chmod(path, stat.S_IWRITE)
        func(path)