import os
import re
import json
import requests
import shutil
import concurrent.futures
import stat
from bs4 import BeautifulSoup
from PIL import Image
from io import BytesIO
from src.core.config import get_root_dir, CONFIG_FILENAME
from src.core.logger import logger
from src.converters.manga_converter import MangaConverter

class MangaEngine:
    """
    Core engine responsible for handling network requests, HTML parsing,
    chapter analysis, and managing the download and processing queue.
    """
    def __init__(self, config_filename=CONFIG_FILENAME):
        self.root_dir = get_root_dir()
        self.config_path = os.path.join(self.root_dir, config_filename)
        if not os.path.exists(self.config_path):
            # Fallback relative path check
            alt_path = os.path.join(os.path.dirname(self.root_dir), config_filename)
            if os.path.exists(alt_path):
                self.config_path = alt_path

        self.session = requests.Session()
        
        # DOC: Advanced headers to simulate a real browser and avoid anti-bot blocks.
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8',
            'Accept-Language': 'pt-PT,pt;q=0.9,en-US;q=0.8,en;q=0.7'
        })
        
        self.sites = self._load_configuration()
        self.IMAGE_TAG = "img"
        # DOC: Expanded attribute list to capture lazy-loaded images across any website.
        self.POSSIBLE_ATTRIBUTES = ["data-src", "data-lazy-src", "data-altsrc", "data-v-image", "src"]
        logger.info("MangaEngine initialized successfully.")

    def _load_configuration(self):
        try:
            with open(self.config_path, 'r', encoding='utf-8') as f: 
                return json.load(f)
        except Exception as e:
            logger.error(f"Failed to load configuration file {self.config_path}: {e}")
            return {}

    def get_preview_image(self, url):
        try:
            response = self.session.get(url, timeout=10)
            return Image.open(BytesIO(response.content))
        except Exception as e:
            logger.warning(f"Could not fetch preview image from {url}: {e}")
            return None

    def analyze_links(self, urls, manga_title):
        info = {'title': manga_title}
        gui_messages = []
        domain_rules = {}
        
        unique_domains = {}
        for u in urls:
            u = u.strip()
            if not u: 
                continue
            domain = u.split('/')[2] if '//' in u else u.split('/')[0]
            domain = domain.replace('www.', '')
            if domain not in unique_domains: 
                unique_domains[domain] = u

        for domain, u in unique_domains.items():
            rules = None
            for k, v in self.sites.items():
                clean_key = k.replace('https://', '').replace('http://', '').replace('www.', '')
                if clean_key in domain or clean_key in u:
                    rules = v
                    break

            if not rules:
                try:
                    response = self.session.get(u, timeout=10)
                    soup = BeautifulSoup(response.content, 'html.parser')
                    found = False
                    for site_key, site_data in self.sites.items():
                        sel_container = site_data['selectors'].get('container_imagens')
                        sel_name = site_data['selectors'].get('nome_capitulo', 'title') 
                        
                        if sel_container:
                            container = soup.select_one(sel_container)
                            if container and container.select(self.IMAGE_TAG):
                                rules = {'selectors': {'container_imagens': sel_container, 'nome_capitulo': sel_name}}
                                msg = f"✅ Site '{domain}' auto-detected successfully!"
                                gui_messages.append(msg)
                                logger.info(msg)
                                domain_rules[domain] = rules
                                found = True
                                break
                    if not found:
                        domain_rules[domain] = None
                except Exception as e:
                    logger.error(f"Error auto-detecting rules for domain {domain}: {e}")
                    domain_rules[domain] = None
            else:
                domain_rules[domain] = rules

        chapters = []
        def process_single_url(i, u):
            u = u.strip()
            if not u: 
                return None
            domain = u.split('/')[2] if '//' in u else u.split('/')[0]
            domain = domain.replace('www.', '')
            rules = domain_rules.get(domain)
            if not rules: 
                return None 
            
            name = None
            sel_name = rules['selectors'].get('nome_capitulo', 'title')
            try:
                response = self.session.get(u, timeout=5)
                soup = BeautifulSoup(response.content, 'html.parser')
                name_element = soup.select_one(sel_name)
                if name_element: 
                    name = name_element.get_text(strip=True)
            except Exception: 
                pass
            
            if not name:
                match = re.search(r'(?:capitulo|cap|c|-)(\d+(?:\.\d+)?)', u.lower())
                num = float(match.group(1)) if match else float(i + 1)
                name = f"Chapter {num:03g}"
                
            match_num = re.search(r'(\d+(?:\.\d+)?)', name)
            num = float(match_num.group(1)) if match_num else float(i + 1)
            
            return {'name': name, 'folder': f"Cap_{num:03g}", 'url': u, 'num': num, 'rules': rules}

        with concurrent.futures.ThreadPoolExecutor(max_workers=10) as executor:
            futures = [executor.submit(process_single_url, i, u) for i, u in enumerate(urls)]
            for future in concurrent.futures.as_completed(futures):
                res = future.result()
                if res: 
                    chapters.append(res)
                    
        if not chapters:
            logger.warning("No supported website links were found during analysis.")
            return None, None, "No supported website links were found."
            
        return info, sorted(chapters, key=lambda x: x['num']), ("OK" if not gui_messages else "".join(gui_messages))

    def clean_chapter_images(self, chapter_path):
        files = sorted([f for f in os.listdir(chapter_path) if f.lower().endswith(('.jpg', '.png', '.webp', '.jpeg'))])
        for file_name in files:
            p = os.path.join(chapter_path, file_name)
            if os.path.getsize(p) <= 15360:
                try: 
                    os.remove(p)
                except Exception: 
                    pass
                
        files = sorted([f for f in os.listdir(chapter_path) if f.lower().endswith(('.jpg', '.png', '.webp', '.jpeg'))])
        if len(files) < 5: 
            return 
            
        first_path = os.path.join(chapter_path, files[0])
        second_path = os.path.join(chapter_path, files[1])
        last_path = os.path.join(chapter_path, files[-1])
        prev_last_path = os.path.join(chapter_path, files[-2])
        
        try:
            with Image.open(first_path) as img_first, Image.open(second_path) as img_sec:
                colors_first = len(img_first.convert("L").getcolors(maxcolors=100000) or [])
                colors_sec = len(img_sec.convert("L").getcolors(maxcolors=100000) or [])
                if img_first.height != img_sec.height or colors_first < (colors_sec * 0.4): 
                    os.remove(first_path)
        except Exception: 
            pass
        try:
            with Image.open(last_path) as img_last, Image.open(prev_last_path) as img_prev:
                colors_last = len(img_last.convert("L").getcolors(maxcolors=100000) or [])
                colors_prev = len(img_prev.convert("L").getcolors(maxcolors=100000) or [])
                if img_last.height != img_prev.height or colors_last < (colors_prev * 0.4): 
                    os.remove(last_path)
        except Exception: 
            pass

    def download_queue(self, queue, base_path, format_type, status_callback, manga_title, options):
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
            final_cover = MangaConverter.prepare_cover(vol_cover, manga_path, options) if vol_cover else None
            processed_paths = []
            
            for item in vol_queue:
                path = os.path.join(manga_path, item['folder'])
                status_callback(item['gui_id'], f"Downloading...", processed_chapters / total_chapters)
                
                if not (os.path.exists(path) and len(os.listdir(path)) > 2):
                    os.makedirs(path, exist_ok=True)
                    try:
                        r_main = self.session.get(item['url'], timeout=15)
                        soup = BeautifulSoup(r_main.content, 'html.parser')
                        container = soup.select_one(item['rules']['selectors']['container_imagens'])
                        
                        urls = []
                        hx_url = None
                        
                        # DOC: STRATEGY 1 - Dynamic Injection & HTMX
                        if container:
                            if container.has_attr('hx-get'):
                                from urllib.parse import urljoin
                                hx_url = urljoin(item['url'], container.get('hx-get'))
                            elif "weebcentral.com" in item['url']:
                                hx_url = item['url'].rstrip('/') + '/images'
                            
                            if hx_url:
                                htmx_headers = {'HX-Request': 'true', 'Referer': item['url']}
                                r_dynamic = self.session.get(hx_url, headers=htmx_headers, timeout=15)
                                soup_dynamic = BeautifulSoup(r_dynamic.content, 'html.parser')
                                imgs = soup_dynamic.select(self.IMAGE_TAG)
                                
                                for img in imgs:
                                    for attr in self.POSSIBLE_ATTRIBUTES:
                                        val = img.get(attr)
                                        if val:
                                            urls.append(val.strip())
                                            break
                        
                        # DOC: STRATEGY 2 - Regular Expressions for Javascript/JSON
                        if not urls:
                            scripts = soup.find_all('script')
                            for script in scripts:
                                if script.string:
                                    clean_text = script.string.replace('\/', '/')
                                    found = re.findall(r"""["'](https?://[^\s<>"']+?\.(?:jpg|jpeg|png|webp))["']""", clean_text, re.IGNORECASE)
                                    if found: 
                                        urls.extend(found)
                        
                        # DOC: STRATEGY 3 - Classic aggressive scan
                        if not urls:
                            imgs = (container if container else soup).select(self.IMAGE_TAG)
                            for img in imgs:
                                for attr in self.POSSIBLE_ATTRIBUTES:
                                    val = img.get(attr)
                                    if val and val.startswith(('http', '//')):
                                        urls.append(val.strip())
                                        break
                        
                        urls = list(dict.fromkeys(urls)) 
                        urls = ["https:" + u if u.startswith('//') else u for u in urls]
                        
                        # DOC: Send original URL to bypass destination server protection
                        with concurrent.futures.ThreadPoolExecutor(max_workers=8) as ex:
                            for idx, u in enumerate(urls, 1):
                                ex.submit(self._save_image_file, u, os.path.join(path, f"{idx:04d}.jpg"), item['url'])
                                
                        self.clean_chapter_images(path)
                    except Exception as e:
                        logger.error(f"Error downloading chapter {item['url']}: {e}")
                
                processed_paths.append(path)
                processed_chapters += 1
                status_callback(item['gui_id'], "Ready", processed_chapters / total_chapters)

            output_destination = os.path.join(manga_path, real_vol_name)
            self._convert_format(format_type, processed_paths, output_destination, final_cover, options, cover_source=vol_cover)

    def _convert_format(self, fmt, paths, dest, cover, options, cover_source=None):
        if fmt == 'epub': 
            MangaConverter.create_epub(paths, dest, cover, options, cover_source=cover_source)
        elif fmt == 'pdf': 
            MangaConverter.create_pdf(paths, dest, cover, options, cover_source=cover_source)
        elif fmt == 'cbz': 
            MangaConverter.create_cbz(paths, dest, cover, options, cover_source=cover_source)

    def _save_image_file(self, url, path, referer_url=None):
        # DOC: Hotlinking bypass - Server requires knowing the request origin
        try:
            image_headers = {'Referer': referer_url} if referer_url else {}
            response = self.session.get(url, headers=image_headers, timeout=15)
            if response.status_code == 200:
                with open(path, 'wb') as f: 
                    f.write(response.content)
                return True
            else:
                return False
        except Exception as e: 
            logger.debug(f"Failed to save image from {url}: {e}")
            return False

    def convert_local_volumes(self, manga_path, format_type, status_callback, options):
        try:
            volumes = [d for d in os.listdir(manga_path) if os.path.isdir(os.path.join(manga_path, d))]
            volumes.sort()
            if not volumes: 
                return status_callback("No folders found.", 1.0)
            for i, vol_name in enumerate(volumes):
                vol_path = os.path.join(manga_path, vol_name)
                status_callback(f"Converting {vol_name}...", i / len(volumes))
                subfolders = [os.path.join(vol_path, c) for c in os.listdir(vol_path) if os.path.isdir(os.path.join(vol_path, c))]
                subfolders.sort()
                paths_to_convert = subfolders if subfolders else [vol_path]
                dest = os.path.join(manga_path, vol_name) 
                local_cover = next((os.path.join(vol_path, f) for f in os.listdir(vol_path) if f.lower().startswith('cover.') and f.lower().endswith(('.jpg', '.jpeg', '.png', '.webp'))), None)
                final_cover = MangaConverter.prepare_cover(local_cover, manga_path, options) if local_cover else None
                self._convert_format(format_type, paths_to_convert, dest, final_cover, options, cover_source=local_cover)
            status_callback("Ready", 1.0)
        except Exception as e:
            logger.error(f"Error during local volume conversion: {e}")
            status_callback("Conversion Error", 1.0)

    def clear_cache(self, base_path, manga_title):
        manga_path = os.path.join(base_path, manga_title)
        if os.path.exists(manga_path):
            for item in os.listdir(manga_path):
                item_path = os.path.join(manga_path, item)
                if os.path.isdir(item_path): 
                    shutil.rmtree(item_path, onerror=self._force_remove)
                elif "cover_" in item: 
                    os.remove(item_path)

    def _force_remove(self, func, path, _):
        os.chmod(path, stat.S_IWRITE)
        func(path)
