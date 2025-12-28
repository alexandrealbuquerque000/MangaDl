import os
import shutil
import zipfile
import re
from PIL import Image
from pypdf import PdfWriter
from ebooklib import epub

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
    """Cria arquivo Comic Book Zip."""
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
    """Cria PDF com marcadores de capítulo para navegação rápida."""
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

def criar_epub(pastas, destino, capa=None):
    """Cria EPUB com TOC funcional apenas nos metadados."""
    try:
        if not destino.endswith('.epub'): destino += '.epub'
        book = epub.EpubBook()
        titulo = os.path.basename(destino).replace('.epub', '')
        book.set_title(titulo)
        book.set_language('pt')

        if capa and os.path.exists(capa):
            with open(capa, 'rb') as f:
                book.set_cover("cover.jpg", f.read())

        book.spine = ['cover']
        toc_links = []

        for i, pasta in enumerate(pastas, 1):
            nome_cap = os.path.basename(pasta).replace('_', ' ')
            arquivos = sorted([f for f in os.listdir(pasta) if f.lower().endswith(('jpg','jpeg','png','webp'))], key=natural_keys)
            
            primeira_pag_cap = None
            for j, arq in enumerate(arquivos, 1):
                img_path = os.path.join(pasta, arq)
                with Image.open(img_path) as img:
                    w, h = img.size
                    style = "width:100vw; height:100vh; object-fit:contain;" if w > h else "width:100%;"

                internal_img = f"images/i_{i}_{j}.jpg"
                with open(img_path, 'rb') as f:
                    book.add_item(epub.EpubItem(uid=f"img_{i}_{j}", file_name=internal_img, content=f.read()))

                html_item = epub.EpubHtml(title=f"P{j}", file_name=f"p_{i}_{j}.xhtml", 
                                         content=f'<html><body style="margin:0;padding:0;background:#000;display:flex;justify-content:center;align-items:center;"><img src="{internal_img}" style="{style}"/></body></html>')
                book.add_item(html_item)
                book.spine.append(html_item)
                
                if j == 1: primeira_pag_cap = html_item

            if primeira_pag_cap:
                toc_links.append(epub.Link(primeira_pag_cap.file_name, nome_cap, f"cap_{i}"))

        book.toc = tuple(toc_links)
        book.add_item(epub.EpubNav()) # Navegação invisível no spine
        book.add_item(epub.EpubNcx()) # Compatibilidade
        epub.write_epub(destino, book)
        return True
    except: return False