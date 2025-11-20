# 📚 Manga Downloader

![Python](https://img.shields.io/badge/Python-3.10%2B-blue?style=for-the-badge&logo=python&logoColor=white)
![Selenium](https://img.shields.io/badge/Selenium-4.0%2B-43B02A?style=for-the-badge&logo=selenium&logoColor=white)
![Status](https://img.shields.io/badge/Status-Stable-brightgreen?style=for-the-badge)

<img width="995" height="727" alt="Captura de tela 2025-11-20 175837" src="https://github.com/user-attachments/assets/2983e9ff-78fb-46de-96a5-4dddec6101bd" />

Um gerenciador de downloads de mangá **moderno, modular e furtivo**. Desenvolvido em Python com uma interface gráfica (GUI) elegante usando `CustomTkinter`, este software permite baixar capítulos de sites configuráveis, organizá-los automaticamente e convertê-los para formatos de leitura populares.

O destaque é o seu **Motor Híbrido Inteligente**, que alterna automaticamente entre requisições rápidas (HTTP) e navegação simulada (Edge WebDriver em modo Ghost) para contornar proteções anti-bot (como Cloudflare) e carregar imagens via Lazy Load.

---

## ✨ Funcionalidades Principais

* **👻 Ghost Mode (Stealth):** Se o download rápido falhar, o sistema ativa automaticamente um navegador Microsoft Edge invisível (Headless) para carregar as imagens e contornar bloqueios.
* **🖼️ Interface Moderna:** GUI completa com suporte a Dark Mode, visualização de capa e sinopse antes do download.
* **📚 Organização Flexível:**
    * **Modo Solto:** Baixa capítulos em pastas separadas.
    * **Modo Volume:** Agrupa múltiplos capítulos (ex: 1 ao 10) em um único arquivo de Volume.
* **📄 Multi-Formatos:**
    * **CBZ:** Formato padrão para leitores de HQ/Mangá (CDisplayEx, Tachiyomi).
    * **PDF:** Arquivo único com **Marcadores de Navegação** (Índice interativo por capítulo).
    * **Pasta:** Imagens soltas (`00001.jpg`, `00002.jpg`) organizadas.
* **🎨 Suporte a Capas:** Detecta a capa automaticamente do site ou permite adicionar uma capa personalizada (arquivo local ou link da internet) ao criar volumes.
* **⚙️ Totalmente Configurável:** A lista de sites é controlada por um arquivo `sites.json` externo. Você pode adicionar suporte a qualquer site sem alterar o código fonte.

---

## 🛠️ Instalação e Dependências

### Pré-requisitos
1.  **Python 3.10** ou superior instalado.
2.  Navegador **Microsoft Edge** instalado (o programa usa o motor nativo do Windows).

### Passo a Passo

1.  **Clone o Repositório:**
    ```bash
    git clone [https://github.com/SEU-USUARIO/manga-downloader-pro.git](https://github.com/SEU-USUARIO/manga-downloader-pro.git)
    cd manga-downloader-pro
    ```

2.  **Instale as Bibliotecas:**
    ```bash
    pip install -r requirements.txt
    ```
    *Conteúdo do `requirements.txt`:*
    ```text
    requests
    beautifulsoup4
    selenium
    webdriver-manager
    customtkinter
    pillow
    pypdf
    packaging
    ```

3.  **Execute o Programa:**
    ```bash
    python gui.py
    ```

---

## 📖 Como Usar

1.  **Buscar:** Cole o link da página principal do mangá (ex: `https://site.com/manga/nome-obra`) e clique em **BUSCAR**.
    * *O programa carregará o Título, a Capa e a Sinopse.*
2.  **Selecionar:**
    * Use os checkboxes para escolher capítulos específicos.
    * Use os botões de seleção rápida ("Todos", "Nenhum").
    * Use o botão **Intervalo** (ex: digite `1-20` para marcar automaticamente do 1 ao 20).
3.  **Configurar:**
    * No painel inferior, escolha o **MODO** (Capítulos Soltos ou Agrupar em Volume).
    * Escolha o **FORMATO** final (CBZ, PDF ou Pasta).
    * *(Opcional)* Se escolher "Volume", você pode definir o nome do arquivo e escolher uma capa personalizada.
4.  **Baixar:** Clique em **BAIXAR** e acompanhe o progresso em tempo real na barra lateral.

---

## ⚙️ Adicionando Novos Sites (`sites.json`)

O programa não possui sites "hardcoded". Ele lê as regras de extração do arquivo `sites.json`. Para adicionar suporte a um site novo, basta editar este arquivo.

**Exemplo de Configuração:**

```json
{
    "https://sitemanga": {
        "nome": "MangasFree",
        "selectors": {
            "titulo_manga": "h1.title",
            "capa": "div.cover img",
            "descricao": "div.synopsis p",
            "lista_capitulos": "li.chapter-item",
            "link_capitulo": "a",
            "container_imagens": "div.reading"
            "tag_imagem": "img",
            "atributos_possiveis": ["data-src", "data-lazy-src", "src"]
        },
        "config": {
            "inverter_ordem_capitulos": true
        }
}
