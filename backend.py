import os
import re
import time
import json
import requests
import logging
import concurrent.futures
from bs4 import BeautifulSoup
from io import BytesIO
from PIL import Image

# Selenium
from selenium import webdriver
from selenium.webdriver.edge.service import Service
from selenium.webdriver.edge.options import Options

# Importamos o manager apenas dentro do try/except para não quebrar se falhar
try:
    from webdriver_manager.microsoft import EdgeChromiumDriverManager
except ImportError:
    EdgeChromiumDriverManager = None

import converters

os.environ['WDM_SSL_VERIFY'] = '0'
logging.getLogger('WDM').setLevel(logging.NOTSET)

class Engine:
    def __init__(self, config_filename="sites.json"):
        import sys # Importante para detectar se é .exe
        
        # Lógica inteligente para descobrir a pasta
        if getattr(sys, 'frozen', False):
            # Se estiver rodando como EXECUTÁVEL (.exe)
            self.root_dir = os.path.dirname(sys.executable)
        else:
            # Se estiver rodando como PYTHON (.py)
            self.root_dir = os.path.dirname(os.path.abspath(__file__))
            
        self.config_path = os.path.join(self.root_dir, config_filename)
        self.stop = False
        self.driver = None
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) Chrome/120.0.0.0 Safari/537.36',
            'Referer': 'https://google.com'
        })
        self.sites = self._load_cfg()

    def _load_cfg(self):
        if not os.path.exists(self.config_path): return {}
        try:
            with open(self.config_path, 'r', encoding='utf-8') as f: return json.load(f)
        except: return {}

    def get_sites_list(self):
        if not self.sites: return ["sites.json não encontrado"]
        return [f"{v.get('nome','?')} ({k})" for k, v in self.sites.items()]

    def _init_driver(self):
        if self.driver: return True
        
        print("Tentando iniciar motor gráfico...")
        
        opts = Options()
        # Tenta rodar invisível. Se der erro, comente a linha abaixo para ver o navegador
        opts.add_argument("--headless=new") 
        opts.add_argument("--disable-gpu")
        opts.add_argument("--log-level=3")
        opts.add_argument("--no-sandbox")
        opts.add_experimental_option('excludeSwitches', ['enable-logging'])

        # TENTATIVA 1: Método Nativo (Selenium 4.6+)
        # Tenta usar o Edge instalado sem baixar nada
        try:
            self.driver = webdriver.Edge(options=opts)
            return True
        except Exception as e1:
            print(f"Método nativo falhou ({e1}). Tentando método de download...")

        # TENTATIVA 2: Webdriver Manager (Só executa se o nativo falhar)
        if EdgeChromiumDriverManager:
            try:
                s = Service(EdgeChromiumDriverManager().install())
                self.driver = webdriver.Edge(service=s, options=opts)
                return True
            except Exception as e2:
                print(f"Método de download falhou: {e2}")
        
        print("ERRO FATAL: Não foi possível iniciar o Edge.")
        return False

    def download_cover(self, url_or_path, dest_folder):
        if not url_or_path: return None
        url_or_path = url_or_path.strip().strip('"')
        dest = os.path.join(dest_folder, "cover.jpg")
        if os.path.exists(url_or_path):
            try: shutil.copy(url_or_path, dest); return dest
            except: return None
        elif url_or_path.startswith('http'):
            try:
                r = self.session.get(url_or_path, timeout=15)
                if r.status_code == 200:
                    with open(dest, 'wb') as f: f.write(r.content)
                    return dest
            except: pass
        return None

    def analyze(self, url):
        url = url.strip()
        if not url.startswith('http'): url = 'https://' + url
        
        regras = None
        for k, v in self.sites.items():
            if k in url: regras = v; break
        
        if not regras: return None, None, "Site não suportado."

        # 1. Requests
        soup = None
        try:
            r = self.session.get(url, timeout=10)
            if r.status_code == 200: soup = BeautifulSoup(r.content, 'html.parser')
        except: pass

        # 2. Selenium
        if not soup:
            if self._init_driver():
                try:
                    self.driver.get(url)
                    time.sleep(3)
                    soup = BeautifulSoup(self.driver.page_source, 'html.parser')
                except: pass
        
        if not soup: return None, None, "Erro de conexão."

        info = {}
        try: info['title'] = re.sub(r'[<>:"/\\|?*]', '', soup.select_one(regras['selectors']['titulo_manga']).get_text(strip=True))
        except: info['title'] = "Manga"
        
        try: 
            img = soup.select_one(regras['selectors'].get('capa', 'img'))
            if img:
                info['cover'] = img.get('data-src') or img.get('src')
                if info['cover'] and info['cover'].startswith('//'): info['cover'] = 'https:' + info['cover']
        except: info['cover'] = None

        try:
            d = soup.select_one(regras['selectors'].get('descricao', 'body'))
            info['desc'] = d.get_text(separator='\n', strip=True) if d else ""
        except: info['desc'] = ""

        caps = []
        els = soup.select(regras['selectors']['lista_capitulos'])
        if not els: els = soup.find_all('a', href=True)

        for el in els:
            a = el if el.name == 'a' else el.select_one(regras['selectors']['link_capitulo'])
            if a and a.get('href'):
                href = a.get('href')
                if not any(c.isdigit() for c in href): continue
                if href.startswith('/'): 
                    p = urlparse(url)
                    href = f'{p.scheme}://{p.netloc}{href}'
                name = a.get_text(strip=True)
                match = re.search(r'(\d+([.,]\d+)?)', name)
                if not match: match = re.search(r'(\d+)', href)
                num = float(match.group(1).replace(',', '.')) if match else 0.0
                fmt = f"{int(num):03d}" if num.is_integer() else f"{num:05.1f}"
                caps.append({'name': name, 'folder': f"Cap_{fmt}", 'url': href, 'num': num, 'rules': regras})
        
        seen = set(); u_caps = []
        for c in caps:
            if c['url'] not in seen: u_caps.append(c); seen.add(c['url'])
        
        if regras.get('config', {}).get('inverter_ordem_capitulos', False):
             u_caps.sort(key=lambda x: x['num'])
        else:
             u_caps.sort(key=lambda x: x['num'])
        return info, u_caps, "OK"

    def baixar_imagem_ram(self, url):
        try: return Image.open(BytesIO(self.session.get(url, timeout=10).content))
        except: return None

    def download_queue(self, queue, base_path, mode, format, vol_name, cover_input, status_cb):
        self.stop = False
        manga_path = os.path.join(base_path, queue[0]['title'])
        os.makedirs(manga_path, exist_ok=True)

        cover_path = self.download_cover(cover_input, manga_path)
        if not cover_path and 'cover' in queue[0] and queue[0]['cover']:
             cover_path = self.download_cover(queue[0]['cover'], manga_path)
        
        processed = []
        for item in queue:
            if self.stop: break
            status_cb(item['gui_id'], "Baixando...", "working")
            path = os.path.join(manga_path, item['folder'])
            processed.append(path)
            
            if os.path.exists(path) and len(os.listdir(path)) > 2:
                status_cb(item['gui_id'], "Cache", "done"); continue
            
            os.makedirs(path, exist_ok=True)
            urls = []
            try:
                s = BeautifulSoup(self.session.get(item['url'], timeout=10).content, 'html.parser')
                urls = self._parse(s, item['rules'])
            except: pass

            if not urls:
                status_cb(item['gui_id'], "Ghost Mode...", "working")
                if self._init_driver():
                    try:
                        self.driver.get(item['url'])
                        h = self.driver.execute_script("return document.body.scrollHeight")
                        for p in range(0, h, 1500): self.driver.execute_script(f"window.scrollTo(0, {p});"); time.sleep(0.1)
                        time.sleep(1)
                        urls = self._parse(BeautifulSoup(self.driver.page_source, 'html.parser'), item['rules'])
                    except: pass

            if not urls:
                status_cb(item['gui_id'], "Falha", "error")
                try: os.rmdir(path); processed.remove(path)
                except: pass
                continue

            with concurrent.futures.ThreadPoolExecutor(max_workers=5) as ex:
                futs = []
                for i, u in enumerate(urls, 1):
                    ext = u.split('.')[-1].split('?')[0]
                    if len(ext) > 4: ext = 'jpg'
                    futs.append(ex.submit(self._save, u, os.path.join(path, f"{i:05d}.{ext}")))
                cnt = sum(1 for f in concurrent.futures.as_completed(futs) if f.result())
            
            if cnt > 0: status_cb(item['gui_id'], "OK", "done")
            else: 
                status_cb(item['gui_id'], "Erro", "error")
                try: os.rmdir(path); processed.remove(path)
                except: pass

            if mode == 'single' and format != 'folder':
                dest = os.path.join(manga_path, item['folder'])
                if format == 'cbz': converters.criar_cbz([path], dest)
                elif format == 'pdf': converters.criar_pdf([path], dest)

        if mode == 'volume' and processed:
            dest = os.path.join(manga_path, vol_name)
            if format == 'cbz': converters.criar_cbz(processed, dest, cover_path)
            elif format == 'pdf': converters.criar_pdf(processed, dest, cover_path)
            elif format == 'folder': converters.organizar_volume_pastas(processed, dest)
        
        if cover_path: 
            try: os.remove(cover_path)
            except: pass
        self.quit()

    def _parse(self, soup, rules):
        if not soup: return []
        c = soup.select_one(rules['selectors']['container_imagens'])
        base = c if c else soup
        imgs = base.select(rules['selectors']['tag_imagem'])
        urls = []
        for i in imgs:
            l = None
            for a in rules['selectors']['atributos_possiveis']:
                v = i.get(a)
                if v and len(v) > 10 and "data:" not in v: l = v.strip(); break
            if l: urls.append(l if l.startswith('http') else 'https:'+l)
        return list(dict.fromkeys(urls))

    def _save(self, url, path):
        try:
            r = self.session.get(url, timeout=15)
            if len(r.content) < 4000: return False
            with open(path, 'wb') as f: f.write(r.content)
            return True
        except: return False

    def quit(self):
        if self.driver:
            try: self.driver.quit()
            except: pass
        self.driver = None