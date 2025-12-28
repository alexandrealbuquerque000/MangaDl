# 📚 Manga Downloader
<img width="1091" height="871" alt="image" src="https://github.com/user-attachments/assets/23dab9d7-661f-4c52-b0d8-3f2d6aad4817" />

O **Manga Downloader** é uma ferramenta de desktop poderosa e intuitiva projetada para automatizar o download e a conversão de mangás. O seu diferencial reside na criação de ficheiros otimizados para leitura digital, garantindo que o seu conteúdo favorito esteja pronto para o Kindle, Kobo ou Tablets com a melhor qualidade possível.

---

## ✨ Funcionalidades Premium

### 🚀 Performance e Automação

* **Download Multi-threaded:** Utiliza processamento paralelo para descarregar capítulos em tempo recorde.
* **Seleção em Massa:** Ferramentas para selecionar todos os capítulos ou definir intervalos específicos (ex: Cap. 10 ao 50) com um único clique.
* **Gestão de Cache Inteligente:** O programa limpa automaticamente as pastas de imagens temporárias ao fechar, mantendo apenas os seus ficheiros finais.

### 📖 Experiência de Leitura Superior

* **EPUB com TOC Semântico:** O índice de capítulos é integrado nos metadados. Navegue entre capítulos pelo menu do seu e-reader sem páginas de sumário físicas a estorvar.
* **Páginas Duplas Otimizadas:** Deteta automaticamente imagens horizontais e aplica um ajuste visual para que caibam perfeitamente no ecrã sem cortes.
* **PDF com Marcadores:** Navegação rápida por capítulos também disponível no formato PDF.

### 🎨 Interface Moderna

* **Preview em Tempo Real:** Veja a capa do mangá antes de iniciar o download.
* **Barra de Progresso Global:** Acompanhe a evolução do download e da conversão de forma visual e clara.
* **Customização de Capa:** Adicione a sua própria arte para personalizar os volumes finais.

---

## 🛠️ Tecnologias Utilizadas

* **Linguagem:** Python 3.10+
* **Interface:** [CustomTkinter](https://github.com/TomSchimansky/CustomTkinter)
* **Processamento de Imagem:** [Pillow (PIL)](https://www.google.com/search?q=https://python-pillow.org/)
* **Documentos Digitais:** [EbookLib](https://github.com/aerkalov/ebooklib) e [PyPDF](https://pypdf.readthedocs.io/)
* **Web Scraping:** [BeautifulSoup4](https://www.crummy.com/software/BeautifulSoup/) e [Requests](https://requests.readthedocs.io/)

---

## 🚀 Como Utilizar

### Pré-requisitos

Certifique-se de que tem o Python instalado no seu sistema.

1. **Clone o Repositório:**
```bash
git clone https://github.com/seu-usuario/manga-downloader-ultra.git
cd manga-downloader-ultra

```


2. **Instale as Dependências:**
```bash
pip install -r requirements.txt

```


3. **Execute o Programa:**
```bash
python gui.py

```
---

## ⚙️ Arquitetura do Sistema

* `gui.py`: Gestão da interface e interação com o utilizador.
* `backend.py`: Lógica de download, análise de sites e gestão de cache.
* `converters.py`: Processamento de imagem e criação técnica de EPUB/PDF/CBZ.
* `sites.json`: Base de dados de seletores CSS para suporte a múltiplos sites.

---

## ⚖️ Aviso Legal

Este software foi desenvolvido estritamente para fins educacionais e de estudo. O utilizador é o único responsável pelo conteúdo descarregue. Recomendamos sempre o apoio oficial aos criadores de conteúdo e plataformas licenciadas.
