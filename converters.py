import os
import zipfile
import re
import uuid
from datetime import datetime
from PIL import Image, ImageEnhance, ImageFile
from pypdf import PdfWriter
from cbz.comic import ComicInfo
from cbz.constants import PageType, YesNo, Manga, Format
from cbz.page import PageInfo

# Permite carregar imagens parcialmente corrompidas no download
ImageFile.LOAD_TRUNCATED_IMAGES = True

def natural_keys(text):
    """Ordenação humana para listas (ex: 1, 2, 10)."""
    return [(int(c) if c.isdigit() else c) for c in re.split(r'(\d+)', text)]

def _processar_e_salvar_imagem(img, base_path, fmt, optimize=True, is_cover=False):
    """
    SUPER-FUNÇÃO MODULAR: Centraliza 100% da lógica de otimização para Kindle.
    Trata Auto-Crop, P&B, Contraste, Redimensionamento e Fatiamento de Webtoons.
    """
    
    KINDLE_MAX_WIDTH = 1236      # Largura máxima (Padrão Paperwhite 11: 1236)
    KINDLE_MAX_HEIGHT = 1648     # Altura máxima (Padrão Paperwhite 11: 1648)
    O_JPEG_QUALITY = 85          # Qualidade do JPEG para reduzir o peso do arquivo
    O_CONTRAST_FACTOR = 1.2      # Fator de aumento de contraste
    O_WEBTOON_RATIO = 2.0        # Proporção limite para fatiar webtoons

    if optimize:
        # 1. Auto-Crop: Remove margens brancas inúteis
        gray = img.convert("L")
        bw = gray.point(lambda x: 0 if x > 245 else 255)
        bbox = bw.getbbox()
        if bbox:
            l, u, r, d = bbox
            l = max(0, l - 5)
            u = max(0, u - 5)
            r = min(img.width, r + 5)
            d = min(img.height, d + 5)
            img = img.crop((l, u, r, d))

        width, height = img.size

        # Rotação para EPUB de páginas duplas (ignora se for capa)
        if not is_cover and width > height and fmt == '.epub':
            img = img.rotate(-90, expand=True)
            width, height = img.size

        # 2. Tratamento visual: Escala de cinza e Contraste
        img = img.convert('L')
        enhancer = ImageEnhance.Contrast(img)
        img = enhancer.enhance(O_CONTRAST_FACTOR)
        
        try:
            filtro = Image.Resampling.LANCZOS
        except AttributeError:
            filtro = getattr(Image, 'LANCZOS', getattr(Image, 'ANTIALIAS', 1))

        # 3. Limite máximo de largura proporcional
        if width > KINDLE_MAX_WIDTH:
            ratio = KINDLE_MAX_WIDTH / float(width)
            new_h = int(height * ratio)
            img = img.resize((KINDLE_MAX_WIDTH, new_h), filtro)
            width, height = img.size

        # 4. Se for capa ou imagem normal (não webtoon), guarda direto
        if is_cover or (height / float(width) <= O_WEBTOON_RATIO):
            final_path = f"{base_path}_opt.jpg"
            img.convert('RGB').save(final_path, format='JPEG', quality=O_JPEG_QUALITY, optimize=True, progressive=False)
            return [final_path]

        # 5. Lógica exclusiva para Webtoons (Fatiamento de tiras compridas)
        else:
            paths = []
            chunk_height = int(width * (KINDLE_MAX_HEIGHT / float(KINDLE_MAX_WIDTH)))
            num_parts = (height // chunk_height) + (1 if height % chunk_height > 0 else 0)
            
            for p in range(num_parts):
                top = p * chunk_height
                bottom = min((p + 1) * chunk_height, height)
                
                chunk = img.crop((0, top, width, bottom))
                chunk_path = f"{base_path}_part{p}.jpg"
                chunk.convert('RGB').save(chunk_path, format='JPEG', quality=O_JPEG_QUALITY, optimize=True, progressive=False)
                paths.append(chunk_path)
            return paths
            
    else:
        # Sem otimização: preserva integridade original
        final_path = f"{base_path}.jpg"
        try:
            img.convert('RGB').save(final_path, format='JPEG', quality=95, progressive=False)
            return [final_path]
        except Exception:
            return []


def preparar_capa(caminho_original, pasta_destino, optimize=False):
    """Prepara a capa utilizando a super-função modular."""
    if not caminho_original or not os.path.exists(caminho_original):
        return None
    try:
        dest = os.path.join(pasta_destino, "cover_final")
        with Image.open(caminho_original) as img_aberta:
            if img_aberta.mode in ('RGBA', 'LA') or (img_aberta.mode == 'P' and 'transparency' in img_aberta.info):
                img = img_aberta.convert('RGBA').convert('RGB')
            else:
                img = img_aberta.convert('RGB')

        # Chama a função centralizada indicando que é uma capa (is_cover=True)
        resultados = _processar_e_salvar_imagem(img, dest, fmt='', optimize=optimize, is_cover=True)
        return resultados[0] if resultados else None
    except Exception as e:
        print(f"Erro ao preparar capa: {e}")
        return None


def check_image(full_path, fmt, optimize=False):
    """Processa as páginas dos capítulos utilizando a super-função modular."""
    try:
        with Image.open(full_path) as img_aberta:
            if img_aberta.mode in ('RGBA', 'LA') or (img_aberta.mode == 'P' and 'transparency' in img_aberta.info):
                img = img_aberta.convert('RGBA').convert('RGB')
            else:
                img = img_aberta.convert('RGB')
    except Exception:
        return []

    if img.width < 250 or img.height < 250:
        return []

    base_path, _ = os.path.splitext(full_path)
    
    # Chama a função centralizada para tratar as páginas do mangá
    return _processar_e_salvar_imagem(img, base_path, fmt, optimize=optimize, is_cover=False)


def criar_cbz(pastas, destino, capa=None, optimize=False):
    """Cria arquivo Comic Book Zip com suporte a fatiamento."""
    try:
        fmt='.cbz'
        if not destino.endswith(fmt): destino += fmt
        titulo = os.path.basename(destino).replace(fmt, '')
        pages=[]
        if capa and os.path.exists(capa):
            pages.append(PageInfo.load(path=capa, type=PageType.FRONT_COVER))
            
        for i, pasta in enumerate(pastas, 1):
            arquivos = sorted([f for f in os.listdir(pasta) if f.lower().endswith(('jpg','jpeg','png','webp'))], key=natural_keys)
            for arq in arquivos:
                paths = check_image(os.path.join(pasta, arq), fmt, optimize)
                for p in paths:
                    pages.append(PageInfo.load(path=p, type=PageType.STORY))
                    
        comic = ComicInfo.from_pages(
            pages=pages,
            title=titulo,
            language_iso='pt',
            format=Format.WEB_COMIC,
            black_white=YesNo.NO,
            manga=Manga.YES,
        )
        with open(destino, "wb") as dest:
            dest.write(comic.pack())

        return True
    except: return False


def criar_pdf(pastas, destino, capa=None, optimize=False):
    """Cria PDF com marcadores e suporte a fatiamento."""
    try:
        fmt='.pdf'
        if not destino.endswith(fmt): destino += fmt
        writer = PdfWriter()
        pag_atual = 0
        
        if capa and os.path.exists(capa):
            temp = f"t_c_{uuid.uuid4().hex[:6]}.pdf"
            with Image.open(capa).convert('RGB') as img:
                img.save(temp)
            writer.append(temp)
            writer.add_outline_item("Capa", 0)
            pag_atual += 1
            os.remove(temp)

        for pasta in pastas:
            nome_cap = os.path.basename(pasta).replace('_', ' ')
            arquivos = sorted([f for f in os.listdir(pasta) if f.lower().endswith(('jpg','jpeg','png','webp'))], key=natural_keys)
            inicio_cap = pag_atual
            
            for arq in arquivos:
                paths = check_image(os.path.join(pasta, arq), fmt, optimize)
                for p in paths:
                    temp = f"p_{uuid.uuid4().hex[:6]}.pdf"
                    with Image.open(p).convert('RGB') as img:
                        img.save(temp)
                    writer.append(temp)
                    pag_atual += 1
                    os.remove(temp)
                    
            writer.add_outline_item(nome_cap, inicio_cap)
            
        with open(destino, "wb") as f: writer.write(f)
        return True
    except: return False


def criar_epub(pastas, destino, capa=None, optimize=False):
    """Cria EPUB com suporte à renderização exata das partes fatiadas e originais."""
    try:
        fmt='.epub'
        if not destino.endswith(fmt): destino += fmt
        
        titulo = os.path.basename(destino).replace(fmt, '')
        unique_id = str(uuid.uuid4())
        lang = "pt"
        direction="rtl"
        images_info = [] 
        spine_refs = []  
        toc_items = []   
        image_files_to_write = [] 

        if capa and os.path.exists(capa):
            with Image.open(capa) as img:
                w, h = img.size
            
            page_id = "cover_page"
            img_filename = "cover.jpg"
            images_info.append({"id": "cover_img", "filename": img_filename, "width": w, "height": h, "is_cover": True, "page_id": page_id})
            spine_refs.append(page_id)
            image_files_to_write.append((capa, f"images/{img_filename}"))
            toc_items.append((page_id, "Capa"))

        global_count = 0
        for i, pasta in enumerate(pastas, 1):
            nome_cap = os.path.basename(pasta).replace('_', ' ')
            arquivos = sorted([f for f in os.listdir(pasta) if f.lower().endswith(('jpg','jpeg','png','webp'))], key=natural_keys)
            
            first_page_of_chapter = None
            is_first = True
            
            for arq in arquivos:
                paths = check_image(os.path.join(pasta, arq), fmt, optimize)
                for p in paths:
                    global_count += 1
                    with Image.open(p) as img:
                        w, h = img.size
                    
                    img_id = f"img_{i}_{global_count}"
                    page_id = f"page_{i}_{global_count}"
                    img_filename = f"image_{global_count:04d}.jpg"
                    
                    images_info.append({"id": img_id, "filename": img_filename, "width": w, "height": h, "is_cover": False, "page_id": page_id})
                    spine_refs.append(page_id)
                    image_files_to_write.append((p, f"images/{img_filename}"))
                    
                    if is_first:
                        first_page_of_chapter = page_id
                        is_first = False
                        
            if first_page_of_chapter:
                toc_items.append((first_page_of_chapter, nome_cap))

        with zipfile.ZipFile(destino, 'w', zipfile.ZIP_DEFLATED) as zf:
            zf.writestr("mimetype", "application/epub+zip", compress_type=zipfile.ZIP_STORED)
            
            container_xml = """<?xml version="1.0" encoding="UTF-8"?>
<container version="1.0" xmlns="urn:oasis:names:tc:opendocument:xmlns:container"><rootfiles><rootfile full-path="content.opf" media-type="application/oebps-package+xml"/></rootfiles></container>"""
            zf.writestr("META-INF/container.xml", container_xml)

            css_content = """@charset "utf-8"; body { margin: 0; padding: 0; text-align: center; background-color: white; } @page { margin: 0; padding: 0; } div { margin: 0; padding: 0; width: 100vw; height: 100vh; }"""
            zf.writestr("stylesheet.css", css_content)

            for src, dest in image_files_to_write:
                try:
                    zf.write(src, dest)
                except: pass

            page_template = """<?xml version="1.0" encoding="utf-8"?>
<html xmlns="http://www.w3.org/1999/xhtml" xmlns:epub="http://www.idpf.org/2007/ops">
<head><title>{title}</title><link href="../stylesheet.css" rel="stylesheet" type="text/css"/><meta name="viewport" content="width={w}, height={h}"/></head>
<body style="margin:0;padding:0"><div style="width:100vw;height:100vh;margin:0;padding:0;"><svg xmlns="http://www.w3.org/2000/svg" xmlns:xlink="http://www.w3.org/1999/xlink" version="1.1" width="100%" height="100%" viewBox="0 0 {w} {h}"><image width="{w}" height="{h}" xlink:href="../images/{filename}"/></svg></div></body></html>"""

            for info in images_info:
                zf.writestr(f"pages/{info['page_id']}.xhtml", page_template.format(title=info['page_id'], w=info['width'], h=info['height'], filename=info['filename']))

            navpoints = "".join([f'<navPoint id="navPoint-{idx}" playOrder="{idx}"><navLabel><text>{title}</text></navLabel><content src="pages/{pid}.xhtml"/></navPoint>' for idx, (pid, title) in enumerate(toc_items, 1)])
            zf.writestr("toc.ncx", f"""<?xml version="1.0" encoding="UTF-8"?><ncx xmlns="http://www.daisy.org/z3986/2005/ncx/" version="2005-1"><head><meta name="dtb:uid" content="{unique_id}"/><meta name="dtb:depth" content="1"/><meta name="dtb:totalPageCount" content="0"/><meta name="dtb:maxPageNumber" content="0"/></head><docTitle><text>{titulo}</text></docTitle><navMap>{navpoints}</navMap></ncx>""")

            toc_li = "".join([f'<li><a href="pages/{pid}.xhtml">{title}</a></li>\n' for pid, title in toc_items])
            zf.writestr("toc.xhtml", f"""<?xml version="1.0" encoding="utf-8"?><html xmlns="http://www.w3.org/1999/xhtml" xmlns:epub="http://www.idpf.org/2007/ops"><head><title>TOC</title></head><body><nav epub:type="toc" id="toc"><h1>Índice</h1><ol>{toc_li}</ol></nav></body></html>""")

            manifest_items = '<item id="style" href="stylesheet.css" media-type="text/css"/>\n<item id="ncx" href="toc.ncx" media-type="application/x-dtbncx+xml"/>\n<item id="toc" href="toc.xhtml" media-type="application/xhtml+xml" properties="nav"/>\n'
            for info in images_info:
                manifest_items += f'<item id="{info["id"]}" href="images/{info["filename"]}" media-type="image/jpeg"{' properties="cover-image"' if info["is_cover"] else ''}/>\n<item id="{info["page_id"]}" href="pages/{info["page_id"]}.xhtml" media-type="application/xhtml+xml"/>\n'

            spine_items = "".join([f'<itemref idref="{ref}"/>\n' for ref in spine_refs])
            mod_date = datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%SZ")

            zf.writestr("content.opf", f"""<?xml version="1.0" encoding="UTF-8"?>
<package xmlns="http://www.idpf.org/2007/opf" version="3.0" unique-identifier="BookID" xml:lang="{lang}">
    <metadata xmlns:dc="http://purl.org/dc/elements/1.1/" xmlns:opf="http://www.idpf.org/2007/opf">
        <dc:title>{titulo}</dc:title><dc:language>{lang}</dc:language><dc:identifier id="BookID">{unique_id}</dc:identifier>
        <meta property="dcterms:modified">{mod_date}</meta><meta property="rendition:layout">pre-paginated</meta><meta property="rendition:orientation">auto</meta><meta property="rendition:spread">landscape</meta><meta name="cover" content="cover_img" />
    </metadata>
    <manifest>{manifest_items}</manifest><spine toc="ncx" page-progression-direction={direction}>{spine_items}</spine>
</package>""")

        return True
    except Exception as e:
        print(f"Erro ao criar EPUB: {e}")
        return False
