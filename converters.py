import os
import shutil
import zipfile
import re
from PIL import Image
from pypdf import PdfWriter, PdfReader

def natural_keys(text):
    """Ordenação humana (1, 2, 10...)."""
    return [(int(c) if c.isdigit() else c) for c in re.split(r'(\d+)', text)]

def organizar_volume_pastas(lista_pastas, caminho_volume):
    """Move pastas de capítulos para dentro de uma pasta de volume."""
    try:
        os.makedirs(caminho_volume, exist_ok=True)
        for pasta in lista_pastas:
            nome_cap = os.path.basename(pasta)
            destino = os.path.join(caminho_volume, nome_cap)
            if os.path.exists(destino): shutil.rmtree(destino) # Previne erro se já existir
            shutil.move(pasta, destino)
        return True
    except: return False

def criar_cbz(pastas, destino, capa=None):
    """Cria arquivo Comic Book Zip."""
    try:
        if not destino.endswith('.cbz'): destino += '.cbz'
        
        with zipfile.ZipFile(destino, 'w', zipfile.ZIP_DEFLATED) as zf:
            # Adiciona Capa
            if capa and os.path.exists(capa):
                zf.write(capa, "000_Capa.jpg")
            
            # Adiciona Capítulos
            for i, pasta in enumerate(pastas, 1):
                arquivos = sorted([f for f in os.listdir(pasta) if f.lower().endswith(('jpg','jpeg','png','webp'))], key=natural_keys)
                
                for j, arq in enumerate(arquivos, 1):
                    # Renomeia para C001_P001.jpg para garantir ordem absoluta
                    zf.write(os.path.join(pasta, arq), f"C{i:03d}_P{j:04d}.jpg")
        
        # Limpeza
        for p in pastas: shutil.rmtree(p)
        return True
    except: return False

def criar_pdf(pastas, destino, capa=None):
    """Cria PDF com Marcadores de Capítulo."""
    try:
        if not destino.endswith('.pdf'): destino += '.pdf'
        temp_pdf = destino.replace('.pdf', '_temp.pdf')
        
        lista_imgs = []
        bookmarks = [] # (NumeroPagina, TituloCapitulo)
        pag_atual = 0

        # 1. Processa Capa
        if capa and os.path.exists(capa):
            try:
                img = Image.open(capa).convert('RGB')
                lista_imgs.append(img)
                bookmarks.append((0, "Capa"))
                pag_atual += 1
            except: pass

        # 2. Processa Capítulos
        for pasta in pastas:
            nome_cap = os.path.basename(pasta).replace('_', ' ')
            arquivos = sorted([f for f in os.listdir(pasta) if f.lower().endswith(('jpg','jpeg','png','webp'))], key=natural_keys)
            
            primeira_pag = True
            for arq in arquivos:
                try:
                    img = Image.open(os.path.join(pasta, arq)).convert('RGB')
                    lista_imgs.append(img)
                    
                    if primeira_pag:
                        bookmarks.append((pag_atual, nome_cap))
                        primeira_pag = False
                    pag_atual += 1
                except: pass

        if not lista_imgs: return False

        # 3. Salva PDF Bruto
        lista_imgs[0].save(temp_pdf, save_all=True, append_images=lista_imgs[1:])

        # 4. Adiciona Navegação
        writer = PdfWriter()
        reader = PdfReader(temp_pdf)
        
        for page in reader.pages: writer.add_page(page)
        for p_num, title in bookmarks: writer.add_outline_item(title, p_num)
        
        with open(destino, "wb") as f: writer.write(f)
        
        # Limpeza
        try: 
            reader.close()
            os.remove(temp_pdf)
        except: pass
        for p in pastas: shutil.rmtree(p)
        
        return True
    except Exception as e:
        print(f"Erro PDF: {e}")
        return False