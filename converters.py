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

# DOC: Permite o carregamento de imagens truncadas ou parcialmente corrompidas
ImageFile.LOAD_TRUNCATED_IMAGES = True

def natural_keys(text):
    return [(int(c) if c.isdigit() else c) for c in re.split(r'(\d+)', text)]

def _cleanup_temp_images(pastas, capa_temp=None):
    # DOC: Limpa ficheiros temporários criados durante o processamento
    for pasta in pastas:
        if not os.path.exists(pasta): continue
        for f in os.listdir(pasta):
            if '_opt' in f.lower() or '_part' in f.lower():
                try: os.remove(os.path.join(pasta, f))
                except: pass
    if capa_temp and os.path.exists(capa_temp):
        try: os.remove(capa_temp)
        except: pass

def opt_auto_crop(img):
    """Varredura otimizada para remover bordas brancas/acinzentadas, focando especialmente na parte inferior."""
    gray = img.convert("L")
    width, height = img.size
    pixels = gray.load()

    bg_thresh = 240

    u = 0
    for y in range(height):
        has_content = False
        for x in range(width):
            if pixels[x, y] < bg_thresh:
                has_content = True
                break
        if has_content:
            u = y
            break

    d = height - 1
    for y in range(height - 1, -1, -1):
        has_content = False
        for x in range(width):
            if pixels[x, y] < bg_thresh:
                has_content = True
                break
        if has_content:
            d = y
            break

    l = 0
    for x in range(width):
        has_content = False
        for y in range(u, d + 1):
            if pixels[x, y] < bg_thresh:
                has_content = True
                break
        if has_content:
            l = x
            break

    r = width - 1
    for x in range(width - 1, -1, -1):
        has_content = False
        for y in range(u, d + 1):
            if pixels[x, y] < bg_thresh:
                has_content = True
                break
        if has_content:
            r = x
            break

    padding = 4
    l = max(0, l - padding)
    u = max(0, u - padding)
    r = min(width, r + padding)
    d = min(height, d + padding)

    if (r - l) > (width * 0.4) and (d - u) > (height * 0.4):
        img = img.crop((l, u, r, d))

    return img

def opt_grayscale(img):
    return img.convert('L')

def opt_contrast(img, factor=1.2):
    enhancer = ImageEnhance.Contrast(img)
    return enhancer.enhance(factor)

def opt_fill_screen(img, target_width, target_height):
    # Redimensiona a imagem forçando-a a preencher exatamente a largura e altura do alvo, alterando a proporção para eliminar quaisquer margens.
    if not target_width or not target_height: return img
    # Define o filtro de alta qualidade para o redimensionamento
    try:
        filtro = Image.Resampling.LANCZOS
    except AttributeError:
        filtro = getattr(Image, 'LANCZOS', getattr(Image, 'ANTIALIAS', 1))
    # Força o redimensionamento ignorando a proporção original para preencher a tela toda
    return img.resize((target_width, target_height), filtro)

def opt_resize(img, max_width, max_height):
    # DOC: Redimensionamento simples, respeitando as proporções originais
    if not max_width or not max_height: return img
    if img.width > max_width:
        ratio = max_width / float(img.width)
        new_h = int(img.height * ratio)
        try: filtro = Image.Resampling.LANCZOS
        except AttributeError: filtro = getattr(Image, 'LANCZOS', getattr(Image, 'ANTIALIAS', 1))
        img = img.resize((max_width, new_h), filtro)
    return img

def _processar_e_salvar_imagem(img, base_path, fmt, options=None, is_cover=False):
    # DOC: Função central de processamento - a lógica de 'stretch' foi totalmente removida
    if options is None: options = {}

    KINDLE_MAX_WIDTH = int(options.get('width', 0))
    KINDLE_MAX_HEIGHT = int(options.get('height', 0))
    O_JPEG_QUALITY = int(options.get('quality', 85))
    O_WEBTOON_RATIO = 2.0

    if options.get('autocrop', False):
        img = opt_auto_crop(img)

    images_to_process = []
    dp_mode = options.get('double_page_mode', 'Dividir')

    # DOC: Lógica de tratamento de páginas duplas
    if not is_cover and img.width > img.height * 1.15:
        if dp_mode == "Dividir":
            w_half = img.width // 2
            left_half = img.crop((0, 0, w_half, img.height))
            right_half = img.crop((w_half, 0, img.width, img.height))
            images_to_process = [right_half, left_half] if options.get('rtl', True) else [left_half, right_half]
        elif dp_mode == "Rotacionar":
            img = img.rotate(-90, expand=True)
            images_to_process = [img]
        else:
            images_to_process = [img]
    else:
        images_to_process = [img]

    final_paths = []
    # DOC: Processa as partes geradas da imagem
    for idx, sub_img in enumerate(images_to_process):
        if options.get('grayscale', False):
            sub_img = opt_grayscale(sub_img)
        if options.get('contrast', False):
            sub_img = opt_contrast(sub_img, factor=options.get('contrast_factor', 1.2))

        # Redimensionamento é aplicado, mantendo ou não a proporção, dependendo da flag 'fill_screen'
        if KINDLE_MAX_WIDTH > 0 and KINDLE_MAX_HEIGHT > 0:
            if options.get('fill_screen', False):
                sub_img = opt_fill_screen(img, KINDLE_MAX_WIDTH, KINDLE_MAX_HEIGHT)
            else:
                sub_img = opt_resize(sub_img, KINDLE_MAX_WIDTH, KINDLE_MAX_HEIGHT)
#

        sub_base = f"{base_path}_{idx}" if len(images_to_process) > 1 else base_path

        if is_cover or KINDLE_MAX_WIDTH == 0 or (sub_img.height / float(sub_img.width) <= O_WEBTOON_RATIO):
            final_path = f"{sub_base}_opt.jpg"
            sub_img.convert('RGB').save(final_path, format='JPEG', quality=O_JPEG_QUALITY, optimize=True, progressive=False)
            final_paths.append(final_path)
        else:
            chunk_height = int(sub_img.width * (KINDLE_MAX_HEIGHT / float(KINDLE_MAX_WIDTH)))
            num_parts = (sub_img.height // chunk_height) + (1 if sub_img.height % chunk_height > 0 else 0)

            for p in range(num_parts):
                top = p * chunk_height
                bottom = min((p + 1) * chunk_height, sub_img.height)
                chunk = sub_img.crop((0, top, sub_img.width, bottom))
                chunk_path = f"{sub_base}_part{p}.jpg"
                chunk.convert('RGB').save(chunk_path, format='JPEG', quality=O_JPEG_QUALITY, optimize=True, progressive=False)
                final_paths.append(chunk_path)

    return final_paths

def preparar_capa(caminho_original, pasta_destino, options=None):
    if not caminho_original or not os.path.exists(caminho_original):
        return None
    try:
        dest = os.path.join(pasta_destino, f"cover_{uuid.uuid4().hex[:6]}")
        with Image.open(caminho_original) as img_aberta:
            img = img_aberta.convert('RGB')
        resultados = _processar_e_salvar_imagem(img, dest, fmt='', options=options, is_cover=True)
        return resultados[0] if resultados else None
    except Exception as e:
        return None

def check_image(full_path, fmt, options=None, is_cover=False):
    # DOC: Adicionámos o parâmetro "is_cover" para podermos proteger a primeira página do mangá
    try:
        with Image.open(full_path) as img_aberta:
            img = img_aberta.convert('RGB')
    except Exception:
        return []

    if img.width < 100 or img.height < 100:
        return []

    base_path, _ = os.path.splitext(full_path)
    # DOC: Passamos a flag "is_cover" para o processador, impedindo que a imagem seja dividida ao meio
    return _processar_e_salvar_imagem(img, base_path, fmt, options=options, is_cover=is_cover)

def criar_cbz(pastas, destino, capa=None, options=None, cover_source=None):
    try:
        fmt='.cbz'
        if not destino.endswith(fmt): destino += fmt
        titulo = os.path.basename(destino).replace(fmt, '')
        pages=[]
        if capa and os.path.exists(capa):
            pages.append(PageInfo.load(path=capa, type=PageType.FRONT_COVER))

        abs_cover_source = os.path.abspath(cover_source) if cover_source and os.path.exists(cover_source) else None

        for i, pasta in enumerate(pastas, 1):
            arquivos = sorted([f for f in os.listdir(pasta) if f.lower().endswith(('jpg','jpeg','png','webp')) and not ('_opt' in f.lower() or '_part' in f.lower())], key=natural_keys)
            for arq in arquivos:
                full_img_path = os.path.join(pasta, arq)
                if abs_cover_source and os.path.abspath(full_img_path) == abs_cover_source:
                    continue
                paths = check_image(full_img_path, fmt, options)
                for p in paths:
                    pages.append(PageInfo.load(path=p, type=PageType.STORY))

        comic = ComicInfo.from_pages(pages=pages, title=titulo, language_iso='pt', format=Format.WEB_COMIC, black_white=YesNo.NO, manga=Manga.YES)
        with open(destino, "wb") as dest:
            dest.write(comic.pack())
        return True
    except:
        return False
    finally:
        _cleanup_temp_images(pastas, capa)

def criar_pdf(pastas, destino, capa=None, options=None, cover_source=None):
    try:
        fmt='.pdf'
        if not destino.endswith(fmt): destino += fmt
        writer = PdfWriter()
        pag_atual = 0

        if capa and os.path.exists(capa):
            temp = f"t_c_{uuid.uuid4().hex[:6]}.pdf"
            with Image.open(capa).convert('RGB') as img: img.save(temp)
            writer.append(temp)
            writer.add_outline_item("Capa", 0)
            pag_atual += 1
            os.remove(temp)

        abs_cover_source = os.path.abspath(cover_source) if cover_source and os.path.exists(cover_source) else None

        for pasta in pastas:
            nome_cap = os.path.basename(pasta).replace('_', ' ')
            arquivos = sorted([f for f in os.listdir(pasta) if f.lower().endswith(('jpg','jpeg','png','webp')) and not ('_opt' in f.lower() or '_part' in f.lower())], key=natural_keys)
            inicio_cap = pag_atual

            for arq in arquivos:
                full_img_path = os.path.join(pasta, arq)
                if abs_cover_source and os.path.abspath(full_img_path) == abs_cover_source:
                    continue
                paths = check_image(full_img_path, fmt, options)
                for p in paths:
                    temp = f"p_{uuid.uuid4().hex[:6]}.pdf"
                    with Image.open(p).convert('RGB') as img: img.save(temp)
                    writer.append(temp)
                    pag_atual += 1
                    os.remove(temp)

            writer.add_outline_item(nome_cap, inicio_cap)

        with open(destino, "wb") as f: writer.write(f)
        return True
    except:
        return False
    finally:
        _cleanup_temp_images(pastas, capa)


def criar_epub(pastas, destino, capa=None, options=None, cover_source=None):
    if options is None: options = {}
    try:
        fmt='.epub'
        if not destino.endswith(fmt): destino += fmt
        titulo = os.path.basename(destino).replace(fmt, '')
        unique_id = str(uuid.uuid4())
        lang = "pt"

        # DOC: Regras essenciais para ativar o motor de mangá no Kindle
        is_rtl = options.get('rtl', True)
        direction = "rtl" if is_rtl else "ltr"
        writing_mode = "horizontal-rl" if is_rtl else "horizontal-lr"

        images_info, spine_refs, toc_items, image_files_to_write = [], [], [], []

        if capa and os.path.exists(capa):
            with Image.open(capa) as img: w, h = img.size
            page_id = "cover_page"
            img_filename = "cover.jpg"
            images_info.append({"id": "cover_img", "filename": img_filename, "width": w, "height": h, "is_cover": True, "page_id": page_id})
            spine_refs.append(page_id)
            image_files_to_write.append((capa, f"images/{img_filename}"))
            toc_items.append((page_id, "Capa"))

        abs_cover_source = os.path.abspath(cover_source) if cover_source and os.path.exists(cover_source) else None
        global_count = 0

        for i, pasta in enumerate(pastas, 1):
            nome_cap = os.path.basename(pasta).replace('_', ' ')
            arquivos = sorted([f for f in os.listdir(pasta) if f.lower().endswith(('jpg','jpeg','png','webp')) and not ('_opt' in f.lower() or '_part' in f.lower())], key=natural_keys)

            first_page_of_chapter = None
            is_first = True

            for arq in arquivos:
                full_img_path = os.path.join(pasta, arq)
                if abs_cover_source and os.path.abspath(full_img_path) == abs_cover_source:
                    continue

                # DOC: Prevenção de corte na capa. Se não houver capa explícita,
                # a primeiríssima imagem do mangá é declarada como capa para não ser fatiada.
                is_first_image_of_book = (global_count == 0 and not capa)

                # DOC: A nova flag é passada aqui
                paths = check_image(full_img_path, fmt, options, is_cover=is_first_image_of_book)

                for p in paths:
                    global_count += 1
                    with Image.open(p) as img: w, h = img.size
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
            zf.writestr("META-INF/container.xml", '<?xml version="1.0" encoding="UTF-8"?><container version="1.0" xmlns="urn:oasis:names:tc:opendocument:xmlns:container"><rootfiles><rootfile full-path="content.opf" media-type="application/oebps-package+xml"/></rootfiles></container>')

            zf.writestr("stylesheet.css", '@charset "utf-8"; body { margin: 0; padding: 0; background-color: #000000; text-align: center; } div { margin: 0; padding: 0; display: block; } img { width: 100%; height: 100%; display: block; margin: 0; padding: 0; }')

            for src, dest in image_files_to_write:
                try: zf.write(src, dest)
                except: pass

            # DOC: Template HTML atualizado com a tag VIEWPORT, essencial para o "Cortar Margens" do Kindle mapear o tamanho do ecrã
            page_template = '''<?xml version="1.0" encoding="UTF-8"?>
<html xmlns="http://www.w3.org/1999/xhtml" xmlns:epub="http://www.idpf.org/2007/ops">
<head>
<title>{title}</title>
<meta name="viewport" content="width={width}, height={height}"/>
<link href="../stylesheet.css" rel="stylesheet" type="text/css"/>
</head>
<body>
<div>
    <img src="../images/{filename}" alt="{title}" />
</div>
</body>
</html>'''

            for info in images_info:
                zf.writestr(f"pages/{info['page_id']}.xhtml", page_template.format(
                    title=info['page_id'],
                    filename=info['filename'],
                    width=info['width'],      # Passa a largura calculada para o HTML
                    height=info['height']     # Passa a altura calculada para o HTML
                ))

            navpoints = "".join([f'<navPoint id="navPoint-{idx}" playOrder="{idx}"><navLabel><text>{title}</text></navLabel><content src="pages/{pid}.xhtml"/></navPoint>' for idx, (pid, title) in enumerate(toc_items, 1)])
            zf.writestr("toc.ncx", f'<?xml version="1.0" encoding="UTF-8"?><ncx xmlns="http://www.daisy.org/z3986/2005/ncx/" version="2005-1"><head><meta name="dtb:uid" content="urn:uuid:{unique_id}"/></head><docTitle><text>{titulo}</text></docTitle><navMap>{navpoints}</navMap></ncx>')

            toc_li = "".join([f'<li><a href="pages/{pid}.xhtml">{title}</a></li>\n' for pid, title in toc_items])
            zf.writestr("toc.xhtml", f'<?xml version="1.0" encoding="UTF-8"?>\n<html xmlns="http://www.w3.org/1999/xhtml" xmlns:epub="http://www.idpf.org/2007/ops"><head><title>Índice</title></head><body><nav epub:type="toc" id="toc"><ol>{toc_li}</ol></nav></body></html>')

            manifest_items = '<item id="style" href="stylesheet.css" media-type="text/css"/>\n<item id="ncx" href="toc.ncx" media-type="application/x-dtbncx+xml"/>\n<item id="toc" href="toc.xhtml" media-type="application/xhtml+xml" properties="nav"/>\n'
            for info in images_info:
                cover_prop = ' properties="cover-image"' if info.get("is_cover") else ''
                manifest_items += f'<item id="{info["id"]}" href="images/{info["filename"]}" media-type="image/jpeg"{cover_prop}/>\n<item id="{info["page_id"]}" href="pages/{info["page_id"]}.xhtml" media-type="application/xhtml+xml"/>\n'

            spine_items = "".join([f'<itemref idref="{ref}"/>\n' for ref in spine_refs])

            data_hora_atual = datetime.utcnow().strftime('%Y-%m-%dT%H:%M:%SZ')

            # DOC: Adicionámos book-type, zero-gutter e zero-margin ao content.opf
            opf_content = f'''<?xml version="1.0" encoding="UTF-8"?>
<package xmlns="http://www.idpf.org/2007/opf" version="3.0" unique-identifier="BookID">
<metadata xmlns:dc="http://purl.org/dc/elements/1.1/" xmlns:dcterms="http://purl.org/dc/terms/">
    <dc:title>{titulo}</dc:title>
    <dc:language>{lang}</dc:language>
    <dc:identifier id="BookID">urn:uuid:{unique_id}</dc:identifier>
    <meta property="dcterms:modified">{data_hora_atual}</meta>
    <meta name="cover" content="cover_img"/>

    <meta name="book-type" content="comic"/>
    <meta name="zero-gutter" content="true"/>
    <meta name="zero-margin" content="true"/>
    <meta name="primary-writing-mode" content="{writing_mode}"/>
    <meta name="RegionMagnification" content="true"/>

    <meta property="rendition:layout">pre-paginated</meta>
    <meta property="rendition:auto">portrait</meta>
    <meta property="rendition:spread">none</meta>
</metadata>
<manifest>
    {manifest_items}
</manifest>
<spine toc="ncx" page-progression-direction="{direction}">
    {spine_items}
</spine>
</package>'''
            zf.writestr("content.opf", opf_content)
        return True
    except:
        return False
    finally:
        _cleanup_temp_images(pastas, capa)
