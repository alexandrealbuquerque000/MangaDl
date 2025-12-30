import os
import zipfile
import re
import uuid
from datetime import datetime
from PIL import Image
from pypdf import PdfWriter

def natural_keys(text):
    """Ordenação humana para listas (ex: 1, 2, 10)."""
    return [(int(c) if c.isdigit() else c) for c in re.split(r'(\d+)', text)]

def preparar_capa(caminho_original, pasta_destino):
    """Normaliza a imagem para ser usada como capa."""
    if not caminho_original or not os.path.exists(caminho_original):
        return None
    try:
        dest = os.path.join(pasta_destino, "cover_final.jpg")
        with Image.open(caminho_original) as img:
            img.convert('RGB').save(dest, "JPEG", quality=95)
        return dest
    except:
        return None

def criar_cbz(pastas, destino, capa=None):
    """Cria arquivo Comic Book Zip (Mantido do original)."""
    try:
        if not destino.endswith('.cbz'): destino += '.cbz'
        with zipfile.ZipFile(destino, 'w', zipfile.ZIP_DEFLATED) as zf:
            if capa and os.path.exists(capa):
                zf.write(capa, "000_Capa.jpg")
            for i, pasta in enumerate(pastas, 1):
                arquivos = sorted([f for f in os.listdir(pasta) if f.lower().endswith(('jpg','jpeg','png','webp'))], key=natural_keys)
                for j, arq in enumerate(arquivos, 1):
                    zf.write(os.path.join(pasta, arq), f"C{i:03d}_P{j:04d}.jpg")
        return True
    except: return False

def criar_pdf(pastas, destino, capa=None):
    """Cria PDF com marcadores (Mantido do original)."""
    try:
        if not destino.endswith('.pdf'): destino += '.pdf'
        writer = PdfWriter()
        pag_atual = 0
        if capa and os.path.exists(capa):
            img = Image.open(capa).convert('RGB')
            temp = f"t_c_{id(destino)}.pdf"
            img.save(temp); writer.append(temp)
            writer.add_outline_item("Capa", 0); pag_atual += 1; os.remove(temp)

        for pasta in pastas:
            nome_cap = os.path.basename(pasta).replace('_', ' ')
            arquivos = sorted([f for f in os.listdir(pasta) if f.lower().endswith(('jpg','jpeg','png','webp'))], key=natural_keys)
            inicio_cap = pag_atual
            for arq in arquivos:
                img = Image.open(os.path.join(pasta, arq)).convert('RGB')
                temp = f"p_{id(arq)}.pdf"
                img.save(temp); writer.append(temp)
                pag_atual += 1; os.remove(temp)
            writer.add_outline_item(nome_cap, inicio_cap)
        with open(destino, "wb") as f: writer.write(f)
        return True
    except: return False

# --- NOVA IMPLEMENTAÇÃO DO CRIAR_EPUB (Lógica do Images_To_ePub) ---

def criar_epub(pastas, destino, capa=None):
    """
    Cria um EPUB usando a estrutura exata do projeto 'Images_To_ePub'.
    Gera o ZIP manualmente para garantir controle total sobre o XML e Layout.
    """
    try:
        if not destino.endswith('.epub'): destino += '.epub'
        
        # Dados gerais
        titulo = os.path.basename(destino).replace('.epub', '')
        unique_id = str(uuid.uuid4())
        lang = "pt"
        
        # Estruturas para armazenar metadados durante o loop
        images_info = [] # Lista de dicionaríos: {id, filename, width, height, is_cover}
        spine_refs = []  # Lista de IDs para o spine
        toc_items = []   # Lista de (id_pagina, titulo) para o índice

        # Lista temporária de arquivos de imagem normalizada
        image_files_to_write = [] # (source_path, internal_path)

        # 1. Processar CAPA (se existir)
        if capa and os.path.exists(capa):
            with Image.open(capa) as img:
                w, h = img.size
            
            img_id = "cover_img"
            page_id = "cover_page"
            img_filename = "cover.jpg"
            
            images_info.append({
                "id": img_id,
                "filename": img_filename,
                "width": w,
                "height": h,
                "is_cover": True,
                "page_id": page_id
            })
            spine_refs.append(page_id)
            image_files_to_write.append((capa, f"images/{img_filename}"))
            # Adiciona ao TOC
            toc_items.append((page_id, "Capa"))

        # 2. Processar IMAGENS DO MANGÁ
        global_count = 0
        for i, pasta in enumerate(pastas, 1):
            nome_cap = os.path.basename(pasta).replace('_', ' ')
            arquivos = sorted([f for f in os.listdir(pasta) if f.lower().endswith(('jpg','jpeg','png','webp'))], key=natural_keys)
            
            first_page_of_chapter = None
            
            for j, arq in enumerate(arquivos, 1):
                global_count += 1
                full_path = os.path.join(pasta, arq)
                
                # Ler dimensões
                try:
                    with Image.open(full_path) as img:
                        w, h = img.size
                except:
                    continue
                
                img_ext = os.path.splitext(arq)[1].lower()
                if img_ext == '.webp': img_ext = '.jpg' # Força jpg se necessário no nome interno
                
                img_id = f"img_{i}_{j}"
                page_id = f"page_{i}_{j}"
                img_filename = f"image_{global_count:04d}{img_ext}"
                
                images_info.append({
                    "id": img_id,
                    "filename": img_filename,
                    "width": w,
                    "height": h,
                    "is_cover": False,
                    "page_id": page_id
                })
                spine_refs.append(page_id)
                image_files_to_write.append((full_path, f"images/{img_filename}"))
                
                if j == 1:
                    first_page_of_chapter = page_id

            if first_page_of_chapter:
                toc_items.append((first_page_of_chapter, nome_cap))

        # --- GERAÇÃO DO ZIP ---
        with zipfile.ZipFile(destino, 'w', zipfile.ZIP_DEFLATED) as zf:
            
            # A. Mimetype (Deve ser o primeiro, sem compressão)
            zf.writestr("mimetype", "application/epub+zip", compress_type=zipfile.ZIP_STORED)
            
            # B. Container XML
            container_xml = """<?xml version="1.0" encoding="UTF-8"?>
<container version="1.0" xmlns="urn:oasis:names:tc:opendocument:xmlns:container">
    <rootfiles>
        <rootfile full-path="content.opf" media-type="application/oebps-package+xml"/>
    </rootfiles>
</container>"""
            zf.writestr("META-INF/container.xml", container_xml)

            # C. Stylesheet (Copiado do stylesheet.css do template)
            css_content = """@charset "utf-8";
body {
    margin: 0;
    padding: 0;
    text-align: center;
    background-color: white;
}
@page {
    margin: 0;
    padding: 0;
}
div {
    margin: 0;
    padding: 0;
    width: 100vw;
    height: 100vh;
}
"""
            zf.writestr("stylesheet.css", css_content)

            # D. Escrever Imagens
            for src, dest in image_files_to_write:
                # Se for webp, converter, senão copiar direto
                try:
                    if src.lower().endswith('.webp'):
                         with Image.open(src) as im:
                            rgb_im = im.convert('RGB')
                            with zf.open(dest, 'w') as f_dest:
                                rgb_im.save(f_dest, format='JPEG', quality=90)
                    else:
                        zf.write(src, dest)
                except:
                    pass

            # E. Escrever Páginas XHTML (Baseado no page.xhtml.jinja2)
            page_template = """<?xml version="1.0" encoding="utf-8"?>
<html xmlns="http://www.w3.org/1999/xhtml" xmlns:epub="http://www.idpf.org/2007/ops">
<head>
    <title>{title}</title>
    <link href="../stylesheet.css" rel="stylesheet" type="text/css"/>
    <meta name="viewport" content="width={w}, height={h}"/>
</head>
<body style="margin:0;padding:0">
    <div style="width:100vw;height:100vh;margin:0;padding:0;">
        <svg xmlns="http://www.w3.org/2000/svg" xmlns:xlink="http://www.w3.org/1999/xlink" version="1.1" width="100%" height="100%" viewBox="0 0 {w} {h}">
            <image width="{w}" height="{h}" xlink:href="../images/{filename}"/>
        </svg>
    </div>
</body>
</html>"""

            for info in images_info:
                content = page_template.format(
                    title=info['page_id'],
                    w=info['width'],
                    h=info['height'],
                    filename=info['filename']
                )
                zf.writestr(f"pages/{info['page_id']}.xhtml", content)

            # F. TOC.ncx (Navegação legado para Kindle antigo)
            navpoints = ""
            for idx, (pid, title) in enumerate(toc_items, 1):
                navpoints += f"""
        <navPoint id="navPoint-{idx}" playOrder="{idx}">
            <navLabel><text>{title}</text></navLabel>
            <content src="pages/{pid}.xhtml"/>
        </navPoint>"""

            toc_ncx = f"""<?xml version="1.0" encoding="UTF-8"?>
<ncx xmlns="http://www.daisy.org/z3986/2005/ncx/" version="2005-1">
    <head>
        <meta name="dtb:uid" content="{unique_id}"/>
        <meta name="dtb:depth" content="1"/>
        <meta name="dtb:totalPageCount" content="0"/>
        <meta name="dtb:maxPageNumber" content="0"/>
    </head>
    <docTitle><text>{titulo}</text></docTitle>
    <navMap>{navpoints}
    </navMap>
</ncx>"""
            zf.writestr("toc.ncx", toc_ncx)

            # G. TOC.xhtml (Navegação EPUB 3)
            toc_li = ""
            for pid, title in toc_items:
                toc_li += f'<li><a href="pages/{pid}.xhtml">{title}</a></li>\n'

            toc_xhtml = f"""<?xml version="1.0" encoding="utf-8"?>
<html xmlns="http://www.w3.org/1999/xhtml" xmlns:epub="http://www.idpf.org/2007/ops">
<head><title>TOC</title></head>
<body>
<nav epub:type="toc" id="toc">
    <h1>Índice</h1>
    <ol>
        {toc_li}
    </ol>
</nav>
</body>
</html>"""
            zf.writestr("toc.xhtml", toc_xhtml)

            # H. Package OPF (O arquivo mestre)
            # Gera a lista de itens do manifesto
            manifest_items = ""
            # Adiciona itens de estilo e toc
            manifest_items += '<item id="style" href="stylesheet.css" media-type="text/css"/>\n'
            manifest_items += '<item id="ncx" href="toc.ncx" media-type="application/x-dtbncx+xml"/>\n'
            manifest_items += '<item id="toc" href="toc.xhtml" media-type="application/xhtml+xml" properties="nav"/>\n'
            
            # Adiciona imagens e paginas
            for info in images_info:
                props = ' properties="cover-image"' if info['is_cover'] else ''
                manifest_items += f'<item id="{info["id"]}" href="images/{info["filename"]}" media-type="image/jpeg"{props}/>\n'
                manifest_items += f'<item id="{info["page_id"]}" href="pages/{info["page_id"]}.xhtml" media-type="application/xhtml+xml"/>\n'

            # Gera o Spine
            spine_items = ""
            for ref in spine_refs:
                spine_items += f'<itemref idref="{ref}"/>\n'

            # Define data de modificação
            mod_date = datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%SZ")

            content_opf = f"""<?xml version="1.0" encoding="UTF-8"?>
<package xmlns="http://www.idpf.org/2007/opf" version="3.0" unique-identifier="BookID" xml:lang="{lang}">
    <metadata xmlns:dc="http://purl.org/dc/elements/1.1/" xmlns:opf="http://www.idpf.org/2007/opf">
        <dc:title>{titulo}</dc:title>
        <dc:language>{lang}</dc:language>
        <dc:identifier id="BookID">{unique_id}</dc:identifier>
        <meta property="dcterms:modified">{mod_date}</meta>
        <meta property="rendition:layout">pre-paginated</meta>
        <meta property="rendition:orientation">auto</meta>
        <meta property="rendition:spread">landscape</meta>
        <meta name="cover" content="cover_img" />
    </metadata>
    <manifest>
        {manifest_items}
    </manifest>
    <spine toc="ncx">
        {spine_items}
    </spine>
</package>"""
            zf.writestr("content.opf", content_opf)

        return True

    except Exception as e:
        print(f"Erro ao criar EPUB: {e}")
        import traceback
        traceback.print_exc()
        return False