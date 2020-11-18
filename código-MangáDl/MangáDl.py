
# Alexandre Maia Aquino de Albuquerque

import os # Para 'limpar' o prompt e fazer algumas operações com arquivos
import re # Para filtrar a busca de títulos
import requests # Para acessar os dados da URL
from bs4 import BeautifulSoup # Para manipular e guardar dados obtidos do site
import copy # Para copiar uma lista
import tkinter, tkinter.filedialog as tf # Para abrir o explorador de arquivos
import zipfile # Para compactar os capítulos
from pathlib import Path # Para verificar a existência do diretório
import shutil # Para apagar pastas
import webbrowser # Para abrir arquivo html
import time # Para fazer o programa esperar um certo tempo para executar determinada ação
import threading # Função para criar uma thread
from selenium import webdriver # Função para realizar requisições em sites dinâmicos
from webdriver_manager.chrome import ChromeDriverManager # Função para instalar chromedriver caso inexistente no sistema


 # Função para mostrar o nome do programa
def showprogram(printmode):
    showtext=   [
        ''' 
    ----------------------------------------------------------------------------------------------------------------------------------------------------------------------------- 
      -------------------------------------------------------------------------------------------------------------------------------------------------------------------------                                                                       
                                                 ╔█                           /$$
                                                 █╝                           | $$                           
        ███╗   ███╗ █████╗ ███╗   ██╗ ██████╗  █████╗ ██████╗ ██╗             | $$                        .___  ___.      ___           _______.___________. _______  _______
        ████╗ ████║██╔══██╗████╗  ██║██╔════╝ ██╔══██╗██╔══██╗██║             | $$$$$$$  /$$   /$$        |   \/   |     /   \         /       |           ||   ____||   ____|    
        ██╔████╔██║███████║██╔██╗ ██║██║  ███╗███████║██║  ██║██║             | $$__  $$| $$  | $$        |  \  /  |    /  ^  \       |   (----`---|  |----`|  |__   |  |__ 
        ██║╚██╔╝██║██╔══██║██║╚██╗██║██║   ██║██╔══██║██║  ██║██║             | $$  \ $$| $$  | $$        |  |\/|  |   /  /_\  \       \   \       |  |     |   __|  |   __|
        ██║ ╚═╝ ██║██║  ██║██║ ╚████║╚██████╔╝██║  ██║██████╔╝███████╗        | $$  | $$| $$  | $$        |  |  |  |  /  _____  \  .----)   |      |  |     |  |____ |  |   
        ╚═╝     ╚═╝╚═╝  ╚═╝╚═╝  ╚═══╝ ╚═════╝ ╚═╝  ╚═╝╚═════╝ ╚══════╝        | $$$$$$$/|  $$$$$$         |__|  |__| /__/     \__\ |_______/       |__|     |_______||__|   
                                                                              |_______/  \____ .$$                                                                                   
                                                                                     /$$  |  .$$                                                                                     
                                                                                     | .$$$$$$/                                                                                     
                                                                                      \______/        

      -------------------------------------------------------------------------------------------------------------------------------------------------------------------------- 
    ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------                                                                              
        '''
    ,
        '''
-------------------
 MangáDl by Mastef
-------------------
        '''        ]                                                     
    os.system('cls')
    print(showtext[printmode])

 # Função para configurar o webdriver
def setdriverconf():
    global driverconf

    chrome_options=webdriver.ChromeOptions()
    chrome_options.add_argument('--headless')
    chrome_options.add_experimental_option('excludeSwitches', ['enable-logging'])
    chrome_options.add_argument('--ignore-certificate-errors')
    chrome_options.add_argument('--log-level=3')
    try:
        executable_path=ChromeDriverManager().install()
    except Exception as error:
        print('\nOcorreu um erro: '+ str(error))

        return -10
    driverconf=[chrome_options, executable_path]


 # Função para perguntar sobre a reinicialização do programa
def askreboot():
    reboot=leiastr('Deseja reiniciar o programa? ')
    if 's' in reboot:

        return 1

    return 0


 # Função para guardar as informações necessárias para realizar o Web Scraping
def getdatabaseinfo():
    keys=   [   
                'basesite', 'getsitenumpagesclass', 'getsitenumpagesextrainfo', 'pagesgtnum', 'firstpagesfilter', 'secondpagesfilter',
                'pagessite', 'titlesandlinksclass', 'titlesextrainfo', 'titlesgtname', 'titlesgturl', 'firsttitlesfilter', 'secondtitlesfilter',
                'descriptionclass', 'descriptionextrainfo', 'descriptiontxt', 'firstdescriptionfilter', 'seconddescriptionfilter',
                'addtitleurl', 'numtitlepgsclass', 'numtitlepgsextrainfo', 'titlepgsgtnum', 'firsttitlepgsfilter', 'secondtitlepgsfilter',
                'capsnamesandidsclass', 'capsextrainfo', 'capsgtname', 'capsgturl', 'firstcapfilter', 'secondcapfilter',
                'addcappageeurl', 'numcappgsclass', 'numcappgsextrainfo', 'cappgsgtnum', 'firstcappgsfilter', 'secondcappgsfilter',
                'pagescapclass', 'cappagesextrainfo', 'pgsgturl', 'firstpgscapfilter', 'secondpgscapfilter',
                'contentpagesclass', 'contentpagesextainfo', 'firstcontentfilter', 'secondcontentfilter'
            ]
    database=   {

        'Animes':   {
                        'Animezeira':  [
                                            'https://animezeira.site/', 'None', 'li', 'text', None, 'a',
                                            'https://animezeira.site/animes/page/{}/', 'video-conteudo', 'div', 'title', 'href', None, 'a',
                                            'conteudo', 'div', 'text', None, 'p',
                                            '', None, None, None, None, None,
                                            'None', 'li', 'title', 'href', None, 'a',
                                            '', None, None, None, None, None,
                                            'video-js vjs-default-skin vjs-big-play-centered', 'video', 'src', None, 'source',
                                            None, 'content', None, None
                                        ],
                    },

        # 'Desenhos': {
        #                 '':  [
        #                      ],
        #             },

        'Mangás':   {
                        'Mangá Host':  [
                                            'https://mangahost2.com/', 'pages', 'span', 'text', None, None,
                                            'https://mangahost2.com/mangas/page/{}', 'manga-block-title-link', None, 'title', 'href', None, None,
                                            'paragraph', 'div', 'text', None, 'p',
                                            '', 'page-numbers', 'a', 'text', None, None,
                                            'btn-caps w-button', None, 'title', 'text', None, None,
                                            '', None, None, None, None, None,
                                            'None', 'img', 'src', None, None,
                                            None, 'content', None, None
                                    ],
                        'Mangá Livre':  [
                                            'https://mangalivre.net/', 'None', 'li', 'href', None, 'a',
                                            'https://mangalivre.net/series/index/nome/todos?page={}', 'link-block', 'a', 'title', 'href', None, None,
                                            'series-desc', 'span', 'text', None, None,
                                            '', 'content', None, None, None, None,
                                            '', 'content', None, None, None, None,
                                            '#/!page{}', None, None, None, None, None,
                                            None, 'img', 'src', None, None,
                                            None, 'content', None, None
                                    ],
                    },

        'Quadrinhos':   {
                        'Hq Dragon':  [
                                            'https://hqdragon.com/', 'btn btn-outline-secondary', 'a', 'href', None, None,
                                            'https://hqdragon.com/hqs/{}', 'None', 'a', 'text', 'href', None, None,
                                             'None', 'p', 'text', None, None,
                                            '', None, None, None, None, None,
                                            'None', 'td', 'text', 'href', None, 'a',
                                            '', None, None, None, None, None,
                                            None, 'img', 'src', None, None,
                                            None, 'content', None, None
                                    ],
                        },

        #  'Filmes':   {
        #                  '':   [
        #                        ],
        #              },
       
        # 'Séries':   {
        #                   '':   [
        #                         ],
        #             }
                                        
                }

    return keys, database


 #Função verificadora de números inteiros entre determinados valores
def rdintnrange(msg, qntmáx):
    while True:
        time.sleep(1.25)
        showprogram(1)
        try:
            verifint=int(input(msg).strip().replace(" ", ""))
        except (ValueError, TypeError, IndexError):
            print("\nERRO:\n\nDigite apenas números inteiros.")
            continue
        else:
            if verifint not in range(1, qntmáx+1):
                print(("\nERRO:\n\nDigite apenas números inteiros positivos menores ou iguais a {}.").format(qntmáx))
                continue

            return verifint


 # Função para aceitar apenas strings
def leiastr(msg):
    while True:
        verifstr=input('\n'+msg).strip().replace(" ", "")
        if verifstr.isalpha() == False:
            print("\nERRO:""\n\nDigite apenas letras.")
            continue
        else:
            verifstr=verifstr.lower()

            return verifstr


 # Função para ajustar as configurações do programa para, futuramente, implementar vários sites
def setconfig():
    global totalchoices, confgs


     # Função para criar um menu
    def createmenu(optionslist):
        menumsg=(('\n{}.\n\n    Opções:\n').format(optionslist[0]))
        for option in optionslist[2:]:
            menumsg=menumsg+(('\n    ({}) - {}').format((optionslist[1:].index(option)), option))
        menumsg=menumsg+'\n\n    Escolha um número correspondente {} que deseja acessar: '.format(optionslist[1])

        return menumsg


    keys, database=getdatabaseinfo()
    categorieslist=['Categorias', 'ao tipo de conteúdo']
    categorieslist.extend(list(database.keys()))
    tpcntmsg=createmenu(categorieslist)
    typecontent=rdintnrange(tpcntmsg, len(categorieslist[2:]))
    typecontent=categorieslist[2:][typecontent-1]
    serverslist=['Servidores', 'ao site']
    serverslist.extend(list(database[typecontent].keys()))
    svrmsg=createmenu(serverslist)
    serverchoice=rdintnrange(svrmsg, len(serverslist[2:]))
    serverchoice=serverslist[2:][serverchoice-1]
    values=database[typecontent][serverchoice]
    serverchoice=serverchoice.replace(' ', '')
    showprogram(1)
    linetype=leiastr('Deseja baixar o conteúdo selecionado, visualizá-lo online ou as duas opções ? ')
    if 'on' in linetype:
        linetype='online'
    elif 'du' in linetype:
        linetype='both'        
    else:
        linetype='offline'
    totalchoices=[typecontent, serverchoice, linetype]
    confgs=dict(zip(keys, values))


 # Função para ajustar diretório inserido
def inputdir(pdir):
    while True:
        try:
            pdir=input(pdir).strip('"').strip()
        except (KeyboardInterrupt):
            print('\n\nVocê não pode pressionar "Ctrl+C" pois o sistema reconhece como um comando para fechar o programa.')
            continue
        break

    return pdir


 # Função para obter informações de todas as requisições feitas pelo programa
def getinfo(site, classinfo, extrainfo, firstfilter, secondfilter):


     # Função para realizar webscrapings mais sofisticados em sites dinâmicos
    def newdriver(securityclass, attrget, partialtext):
        try:
            driver = webdriver.Chrome(executable_path=driverconf[1], options=driverconf[0])
            driver.get(site)
        except Exception as error:
            print('\nOcorreu um erro: '+ str(error))
            time.sleep(1.25)

            return -10
        try:
            driver.find_element_by_class_name(securityclass).click()
        except Exception:
            pass
        searchelem=secondfilter
        if searchelem==0:
            searchelem=extrainfo
        try:
            elemtag=driver.find_elements_by_tag_name(searchelem)
        except Exception as error:
            print('\nOcorreu um erro: '+ str(error))
            time.sleep(1.25)

            return -10
        pgcontent=None
        if elemtag!=None:
            for pgcontent in elemtag:
                pgcontent=pgcontent.get_attribute(attrget)
                if pgcontent!=None and partialtext in pgcontent:
                    break
                    
        if pgcontent==None:
            pgcontent=''
        driver.close()

        return pgcontent


     # Função para verificar a utilização de um comando
    def verifstep(step):
        if step!=None:
            if step=='None':
                step=None
            
            return step

        return 0


     # Função para ajustar URL caso incompleta
    def thirdfilter(url):
        if url!=None:
            if '/' in url:
                basesite=confgs['basesite']
                if url.startswith(basesite)==False:
                    url=basesite+(url.lstrip('/'))

                return url

        return 0
 

     # Função para definir o tipo de informação que será extraída da URL
    def get(infofilter):
        nonlocal info

        if infofilter=='text':
            exactinfo=info.get_text()
        else:
            exactinfo=info.get(infofilter)
        if exactinfo==None:
            exactinfo=''

        return exactinfo.strip()


    try:
        response = requests.get(site, stream=True, headers={'User-agent': 'Mozilla/5.0'})
    except requests.RequestException as error: 
        print('\nOcorreu um erro: '+ (str(error)[:str(error).index('(')]))
        time.sleep(1.25)

        return -10
    if response.status_code==200:
        firstfilter=verifstep(confgs[firstfilter])
        secondfilter=verifstep(confgs[secondfilter])
        verifclassname=classinfo
        classinfo=verifstep(confgs[classinfo])
        extrainfo=verifstep(confgs[extrainfo])
        if extrainfo=='content':
            if totalchoices[:2]==['Mangás', 'MangáLivre'] and verifclassname=='capsnamesandidsclass':
                response=[response.json()] 

            return response
        soup = BeautifulSoup(response.text, 'html.parser')
        if firstfilter!=0:
            soup=soup.find(firstfilter)
        if classinfo!=0 and extrainfo!=0:
            allinfo=soup.find_all(extrainfo, class_=classinfo)
        else:
            if classinfo!=0:
                allinfo=soup.find_all(class_=classinfo)
            else:
                allinfo=soup.find_all(extrainfo)
        listinfo=[]
        for info in allinfo:
            if secondfilter!=0:
                info=info.find(secondfilter)
            if info!=None:
                if verifclassname=='titlesandlinksclass':
                    showprogram(1)
                    print('\nColetando dados...')
                    titlesgturl=get(confgs['titlesgturl'])+confgs['addtitleurl']
                    titlesgturl=thirdfilter(titlesgturl)
                    titlesgtname=get(confgs['titlesgtname'])
                    if len(titlesgtname)<=1:
                            titlesgturl=0
                    if titlesgturl!=0:
                        titlesgtname=titlesgtname.strip('\n')
                        titlesgtname=re.sub(r'[^\w]', ' ', titlesgtname).strip()
                        listinfo.append([titlesgtname, titlesgturl])
                elif verifclassname=='capsnamesandidsclass':
                    capsgturl=get(confgs['capsgturl'])+confgs['addcappageeurl']
                    capsgtname=get(confgs['capsgtname'])
                    if len(capsgtname)<=1:
                            capsgturl=0
                    if capsgturl!=0:
                        capsgtname=capsgtname.strip('\n').strip()
                        capsgtname=re.sub(r'[^\w]', ' ', capsgtname).strip()
                        listinfo.append([capsgtname, capsgturl])
                elif verifclassname=='descriptionclass':
                    listinfo.append(get(confgs['descriptiontxt']))
                elif verifclassname=='numtitlepgsclass':
                    listinfo.append(get(confgs['titlepgsgtnum']))
                elif verifclassname=='numcappgsclass':
                    listinfo.append(get(confgs['cappgsgtnum']))
                elif verifclassname=='getsitenumpagesclass':
                    pagesgtnum=get(confgs['pagesgtnum'])
                    if totalchoices[:2]==['Mangás', 'MangáLivre']:
                        if '?page=' not in str(thirdfilter(pagesgtnum)):
                            pagesgtnum=0
                    if pagesgtnum!=0:
                        listinfo.append(pagesgtnum)
                elif verifclassname=='pagescapclass':
                    pgsgturl=get(confgs['pgsgturl'])
                    if totalchoices[:2]==['Mangás', 'MangáLivre']:
                        pgsgturl=confgs['pgsgturl']
                        pgsgturl=newdriver('eighteen-but', pgsgturl, 'https://static2.mangalivre.com/')
                        if pgsgturl==-10:

                            return -10
                    listinfo.append(pgsgturl)
                    if totalchoices[:2]==['Mangás', 'MangáLivre']:
                        break
                else:
                    listinfo.append([get('text')])
        
        return listinfo
    else:
        if totalchoices[:2]!=['', '']:
            if response.status_code in range(400, 450):

                return -100
        print('\nOcorreu um erro: '+str(response.status_code))
        time.sleep(1.25)
    
        return -10


 # Função para extrair números inteiros de um texto
def extractint(strtxt):
    if strtxt!=None:
        for elem in strtxt:
            try:
                int(elem) 
            except (ValueError, IndexError):
                strtxt=strtxt.replace(elem, ' ')
        strtxt=strtxt.split()
    else:
        strtxt=[]

    return strtxt


 # Função para obter determinadas informações de todo o site
def getallinfolinks(pginf1, pginf2, pginf3, pginf4, pginf5, pginf6, pginf7, pginf8, pginf9):


     # Função para obter o número de páginas de uma URL
    def getnumwebpages():  
        if totalchoices[:2]!=['', '']:
            allinfolist=[]
            verifnumwebpages=[]
            if totalchoices[:2]==['Mangás', 'MangáLivre'] and pginf6=='pagescapclass':
                lastpage=-1
            else:
                lastpage=0
            while True:
                lastpage=lastpage+1
                formatedurl=pginf1.format(lastpage)
                numwebpagestest1=getinfo(formatedurl, pginf6, pginf7, pginf8, pginf9)
                if numwebpagestest1==-10:

                    return -10
                if numwebpagestest1==-100 or numwebpagestest1==verifnumwebpages or len(numwebpagestest1)==0:
                    lastpage=allinfolist
                    break
                verifnumwebpages=copy.deepcopy(numwebpagestest1)
                allinfolist.extend(numwebpagestest1)
        else:
            startpage=1
            numwebpages=getinfo((pginf1.format(startpage)), pginf2, pginf3, pginf4, pginf5)
            if numwebpages==-10:

                return -10
            if totalchoices[:2]==['Mangás', 'MangáHost']:
                try:
                    lastpage=int((numwebpages[0].split())[-1])
                except (IndexError, TypeError, ValueError):
                    lastpage=1
            elif len(numwebpages)==0:
                lastpage=1
            else:
                numwbcontrol=[]
                stop=0
                while True:
                    if numwebpages==-10:

                        return -10
                    numwb=[]
                    for wpinfo in numwebpages:
                        wbi=extractint(wpinfo)
                        if len(wbi)==1:
                            numwb.append(int(wbi[0]))
                    for wbictrl in numwbcontrol:
                        if wbictrl==numwb and numwb!=[]:
                            stop=1
                            break
                    if stop==1:
                        break
                    numwbcontrol.append(numwb)  
                    numwebpages=getinfo((pginf1.format(numwb[-1])), pginf2, pginf3, pginf4, pginf5)
                    if numwebpages==-10:

                        return -10
                lastpage=[]
                for pgs in numwbcontrol:
                    lastpage.extend(pgs)
                lastpage=sorted(set(lastpage))[-1]
        
        return lastpage


     # Função para obter as informações de todas as paginas de um determinado link
    def getinfopgs():
        if numwebpagesends==-10:

            return -10
        else:
            allinfolist=[]
            pgrange=range(1, (numwebpagesends+1))
            for pg in pgrange:
                numwbpgsinfo=(pginf1.format(pg))
                numwbpgsinfo=getinfo(numwbpgsinfo, pginf6, pginf7, pginf8, pginf9)
                if numwbpgsinfo==-10:

                    return -10
                allinfolist.extend(numwbpgsinfo)

        return allinfolist


    numwebpagesends = getnumwebpages()
    if numwebpagesends==-10:

        return -10
    if type(numwebpagesends)==list:
        allinfolist=numwebpagesends
    else:
        allinfolist=getinfopgs()
        if allinfolist==-10:

            return -10

    return allinfolist


 # Função para coletar todas as informações dos títulos disponíveis de determinado site
def colectdata(): 
    os.system('cls')
    pagessite=confgs['pagessite']
    alltitlesandlinks=getallinfolinks(pagessite, 'getsitenumpagesclass', 'getsitenumpagesextrainfo', 'firstpagesfilter', 'secondpagesfilter', 'titlesandlinksclass', 'titlesextrainfo', 'firsttitlesfilter', 'secondtitlesfilter')
    if alltitlesandlinks==-10:
        reboot=askreboot()
    else:
        reboot=1

    return alltitlesandlinks, reboot


 # Função para verificar existência de pasta ou arquivo
def verifpath(dirp, mode):
    if (os.path.exists(dirp))==True:
        if mode==0:

            return 0
    else:
        if mode==0:

            return 1
        try:
            os.mkdir(dirp)
        except (FileExistsError):
            pass
    
    return dirp


 # Função para definir identificador do arquivo com os dados do servidor requisitado
def getarchmark():
    mark1=(('Alê{}Mark').format(totalchoices[0]))
    mark2=(('minimark(server={})').format(totalchoices[1]))

    return mark1, mark2


 # Função para converter a lista de dados em string
def convertlisttostr(listobj, mark1, mark2):
    completestr=mark1
    for str1 in listobj:
        for str2 in str1:
            completestr = completestr + mark2 + str2
        completestr= completestr + mark2 + mark1
   
    return completestr


 # Função para criar arquivo com os dados do site
def createarchdata():
    archpath=inputdir('\nDigite o diretório em que deseja criar esse arquivo: ')
    while ((Path(archpath)).is_dir())==False:
        print("\nEsse diretório não existe.\n\nTente novamente.")
        archpath=inputdir('\nDigite o diretório em que deseja criar esse arquivo: ')
    namearch=inputdir('\nDigite o nome do arquivo: ')
    ext='.txt'
    if namearch.endswith(ext)==False:
        namearch=namearch+ext
    if archpath=='':
        archpath=namearch
    else:
        archpath=archpath+(('\{}').format(namearch))
    arquivo=open(archpath, 'w')
    arquivo.close()
    arquivo=open(archpath, 'w', encoding="utf-8")
    conteúdo, reboot=colectdata()
    if conteúdo==-10:

        return -10, reboot
    mark1, mark2 = getarchmark()
    formatedconteúdo=convertlisttostr(conteúdo, mark1, mark2)
    arquivo.write(formatedconteúdo)
    arquivo.close()

    return conteúdo, reboot


 # Função para obter o diretório central de destino dos arquivos
def gethqpath(mode):
    global typecontentdir


     # Função para exibir erro e propor soluções 
    def erroarch(mode):
        if mode==1:
            archerro='Arquivo inválido.'
        else:
            archerro='Esse arquivo não é compatível com o servidor escolhido.'
        askarcherro=leiastr(archerro+'\n\nDeseja escolher algum outro arquivo? ')
        if 's' in askarcherro:
            archpath=inputdir('\nDigite o diretório do arquivo que contém todos os dados do servidor escolhido: ')
            
            return 0, archpath, 0
        else:
            askcreatearch=leiastr("Deseja criar um arquivo com os dados do servidor escolhido ou prefere utilizar dados temporários coletados em tempo real? ")
            if 'cr' in askcreatearch:
                conteúdo, reboot=createarchdata()
            else:
                conteúdo, reboot=colectdata()
            
            return 1, conteúdo, reboot


    if mode==1:  
        showprogram(1)
        root = tkinter.Tk()
        root.geometry('0x0')
        hqpathchoose=('Selecione o diretório da pasta que deseja guardar todos os{}conteúdos escolhidos: ')
        if totalchoices[2]=='online':
            hqpathchoose=hqpathchoose.format(' "checkpoints" dos ')
        else:
            hqpathchoose=hqpathchoose.format(' ')
        hqpathstr=hqpathchoose.replace('Selecione', '\nDigite')
        print('\n'+hqpathchoose)
        hqpath = tf.askdirectory(parent=root, initialdir="/",title =hqpathchoose)
        root.destroy()       
        if hqpath=='':
            print('\nOpção cancelada.\n\nTente novamente')
            hqpath=inputdir(hqpathstr)
        while ((Path(hqpath)).is_dir())==False:
            print("\nEsse diretório não existe.\n\nTente novamente.")
            hqpath=inputdir(hqpathstr)
        typecontentdir=(hqpath+('\{}').format(totalchoices[0]))
        typecontentdir=verifpath(typecontentdir, 1)
    else:
        archpath=inputdir('\nDigite o diretório do arquivo que contém todos os dados do servidor escolhido: ')
        mark1, mark2 = getarchmark()
        while True:
            try:
                arquivo=open(archpath, 'r', encoding="utf-8")
            except (FileNotFoundError, PermissionError, OSError):
                loop, conteúdo, reboot=erroarch(1)
                if loop==0:
                    archpath=conteúdo
                    continue
                else:
                    break
            else:
                reboot=1
                conteúdo=arquivo.read()
                if mark1 not in conteúdo or mark2 not in conteúdo:
                    loop, conteúdo, reboot=erroarch(0)
                    if loop==0:
                        archpath=conteúdo
                        continue
                    else:
                        break
                conteúdo=convertstrtolist(conteúdo, mark1, mark2)
                break

        return conteúdo, reboot


 # Função para verificar a utilização de um arquivo com informações de determinado servidor
def presetdata():
    showprogram(1)
    askpreset=leiastr('Deseja coletar os dados atualizados ou prefere utilizar dados já existentes? ')
    if 'ex' in askpreset:
        askpreset=1
        alltitlesandlinks, reboot=gethqpath(0)
    else:
        askpreset=0
        askcreatearch=leiastr("Deseja criar um arquivo com os dados para o funcionamento do programa ou prefere utilizar dados temporários coletados em tempo real? ")
        if 'cr' in askcreatearch:
            alltitlesandlinks, reboot=createarchdata()
        else:
            alltitlesandlinks, reboot=colectdata()
    
    return alltitlesandlinks, reboot


 # Função para verificar se os dados estão repetidos
def verifcopy(datalist):
    copydatalist=copy.deepcopy(datalist)
    datalist=[]
    testdatastr=''
    for testdatainfo in copydatalist:
        strtestdatainfo=str(testdatainfo)
        testdatastr=testdatastr+strtestdatainfo
        if testdatastr.count(strtestdatainfo)==1:
            datalist.append(copydatalist[(copydatalist.index(testdatainfo))])
    
    return datalist


 # Função para personalizar a informação escrita no arquivo de texto
def txtmsginfo(posmsgs):
    readlist=['ler', 'lendo', 'lido']
    watchlist=['assistir', 'assistindo', 'assistido']
    seelist=['ver', 'vendo', 'visto']
    downloadinglist=['baixar', 'baixando', 'baixado']
    contentypename=totalchoices[0][:-1].lower()
    if contentypename=='série':
        article='a'
    else:
        article='o'
    msglist=[article, contentypename]
    if totalchoices[0]=='Mangás' or totalchoices[0]=='Quadrinhos':
        msglist.extend(['capítulo']+readlist)
    elif totalchoices[0]=='Filmes':
        msglist.extend(['filme']+watchlist)
    elif totalchoices[0]=='Séries':
        msglist.extend(['episódio']+watchlist)
    else:
        msglist.extend(['episódio']+seelist)
    qntmsgs=len(msglist)
    if len(posmsgs)>qntmsgs:
        posmsgs=posmsgs[:qntmsgs]
    wantedsmsgs=[]
    for msgnum in posmsgs:
        wantedsmsgs.append(msglist[msgnum])

    return wantedsmsgs


 # Função para obter a informação de qual título foi escolhido
def getespecifictile(alltitlesandlinks):
    article, txtmsg1, txtmsg2=txtmsginfo((0, 1, 3))
    if totalchoices[2]!='online':
        txtmsg2='baixar'
    asktitlemsg=('\nDigite o nome d{} {} que deseja {}: ').format(article, txtmsg1, txtmsg2)
    asktitle=input(asktitlemsg).strip().lower()
    postitle=-1
    for ft in alltitlesandlinks:
        postitle=postitle+1
        if len(re.findall(asktitle, (ft[0].lower())))!=0:
            titleanswer=leiastr(('Deseja acessar {}? ').format(ft[0]))
            if 's' in titleanswer:
                gotanswer=1
                break
            else:
                gotanswer=0
                pass
        else:
            gotanswer=0

    if gotanswer==1:

        return postitle
    else:
        print('\nTodas as opções acabaram.')
        time.sleep(1.25)

        return -10


 # Função para atualizar o texto de um arquivo existente ou criá-lo caso inexistente
def updatearch(archdir, newlines):
    if verifpath(archdir, 0)==1 or newlines=='None':
        open(archdir, 'w', encoding='utf-8').close()
        newlines==''
        returndir=1
    else:
        returndir=0
    arch=open(archdir, 'r', encoding='utf-8') 
    conteúdo = arch.readlines()
    conteúdo.append(newlines)  
    arch=open(archdir, 'w', encoding='utf-8') 
    arch.writelines(conteúdo)   
    arch.close()
    if returndir==1:

        return archdir


 # Função para conferir os capítulos escolhidos para download
def leiacap(caps, qntcaps):


     # Função para filtrar as informações válidas sobre os números dos capítulos requisitados
    def read():
        nonlocal caps, qntcaps

        caps=extractint(caps)
        capsinfo=[]
        for cap in caps:
            if int(cap) not in range(1, (qntcaps+1)):

                return -10
            else:
                capsinfo.append(int(cap))
        if len(capsinfo)==0:

            return -10
        else:
            
            return capsinfo


    listcaps=[]
    if '-' in caps:
        caps=caps.replace('-', ' ')
        caps=read()
        if caps==-10 or len(caps)!=2:

            return -10
        else:
            for elemcap in range(caps[0], (caps[1]+1)):     
                listcaps.append(elemcap)
    elif ';' in caps:
        caps=caps.replace(';', ' ')
        caps=read()
        if caps==-10:

            return -10
        else:
            for elemcap in caps:
                listcaps.append(elemcap)
    elif 'c' in caps:
        listcaps='continuar'
    elif 't' in caps:
        listcaps='todos'
    else:
        caps=read()
        if caps==-10 or len(caps)!=1:
            
            return -10
        else:
            listcaps=caps

    return listcaps


 # Função para montar o diretório do arquivo que está sendo baixado
def getcontentfiledir(namecap, capfolder, numpage):
    if totalchoices[0]=='Mangás' or totalchoices[0]=='Quadrinhos':
        filename=(('Page_{}').format(numpage))
        pagefile=capfolder+(('\{}.png').format(filename))
    else:
        filename=namecap
        pagefile=capfolder+(('\{}.mp4').format(filename))

    return pagefile


 # Função para carregar continuamente os dados que serão utilizados 
def preloaddata(resetmode, namecap, capfolder, capurl):
    global capsinfolist

    if resetmode==0:
        try:
            capsinfolist
        except (NameError):
            capsinfolist=[]
        pagesurl=getallinfolinks(capurl, 'numcappgsclass', 'numcappgsextrainfo', 'firstcappgsfilter', 'secondcappgsfilter', 'pagescapclass', 'cappagesextrainfo', 'firstpgscapfilter', 'secondpgscapfilter')  
        if pagesurl==10:

            return -10
        pagesurl=verifcopy(pagesurl)
        pgsdatalist=[]
        numpage=-1
        for pgurl in pagesurl:
            numpage=numpage+1
            pgdata=''
            if totalchoices[2]!='online':
                pagefile=getcontentfiledir(namecap, capfolder, numpage)
                if verifpath(pagefile, 0)==1:
                    pgdata=getinfo(pgurl, 'contentpagesclass', 'contentpagesextainfo', 'firstcontentfilter', 'secondcontentfilter')
                    if pagesurl==10:

                        return -10
                    pgdata=pgdata.content
            pgsdatalist.extend([pgurl, pgdata])
        capsinfolist.append(pgsdatalist)
    else:
        capsinfolist=[]


 # Função para controlar as mensagens mostradas pela thread
def printthreadmsg(msgmode):
    if totalchoices[2]=='both':
        if msgmode=='online':
            if threadtrick==-1:
                print("\nTodos os downloads foram finalizados.")
        elif msgmode=='offline':
            if threadtrick==0:
                print("\nPressione 'Enter' para continuar.")
            elif threadtrick==1:
                print("\nTodos os conteúdos foram mostrados.")
        else:
            os.system('cls')
            print("\nTodos os conteúdos foram mostrados.")
            print("\nTodos os downloads foram finalizados.")


 # função para definir e administrar a mensagem mostrada na tela se todas as threads estiverem ativadas e ocorrendo ao mesmo tempo
def updateglobalmsg(newmsg):
    global askcontinueviewing

    askcontinueviewing=newmsg


 # Função para ver o conteúdo online
def onlineview(nametitle, numcap, htmlname, checkpoint, dircapcheckpoint, pagesinfolist, countviewedcaps):
    htmlpart1=(('''
    <!DOCTYPE html>
    <html lang="pt-br">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>%(title1)s-%(title2)s</title>
        <style>
            body{ 
                    background-color: gray; 
                    background-image: url(https://images.wallpaperscraft.com/image/dark_spots_texture_background_50355_1920x1080.jpg);
                    background-size: cover;
                    background-attachment: fixed;   
                }
            h1  {
                    font-size: 55px;
                    font-style: italic;
                    font-variant: small-caps;
                    font-weight: bold;
                    font-family: 'Gill Sans', 'Gill Sans MT', Calibri, 'Trebuchet MS', sans-serif;
                }
            h2  {
                    font-size: 45px;
                    font-style: italic;
                    font-variant: small-caps;
                    font-weight: bold;
                    font-family: Cambria, Cochin, Georgia, Times, 'Times New Roman', serif;
                }
            p   { 
                    font-size: 25px;
                    font-style: normal;
                    font-variant: small-caps;
                    font-weight: normal;
                    font-family: 'Courier New', Courier, monospace;
                    opacity: 0.75; 
                }
        </style>
    </head>
    <body>
        <center>
        <h1>%(title1)s</h1>
        <h2>%(title2)s</h2>''')%{'title1':nametitle, 'title2':htmlname})   
    htmlpart2=('''
    <p>Alemaquirque</p>
        </center>
    </body>
    </html>''')
    os.system('cls')
    printthreadmsg('online')
    print(('\n{}\n\nAbrindo {}').format(nametitle, htmlname))
    folderhtmldir=((typecontentdir+'\{}\Html_File').format(nametitle))
    folderhtmldir=verifpath(folderhtmldir, 1)
    archhtmldir=((folderhtmldir+'\{}.html').format(htmlname))
    tmparchhtmldirtest=verifpath(archhtmldir, 0)
    if tmparchhtmldirtest==1:
        archhtmldir=updatearch(archhtmldir, htmlpart1)
        contentnum=-1
        pagesinfolist=pagesinfolist[::2]
        for site in pagesinfolist:
            contentnum=contentnum+1
            if totalchoices[0]=='Mangás' or totalchoices[0]=='Quadrinhos':
                htmlcodestr=('\n    <img rel="preload" src="{}" alt="{}" />')
                contentname='Page_{}.png'
            else:
                htmlcodestr=('\n    <video poster="https://eskipaper.com/images/nerd-wallpaper-8.jpg" rel="preload" controls="controls" width="640" height="480" src="{}" alt="{}" ></video>')
                contentname='Video_{}.mp4'
            contentname=contentname.format(contentnum)
            htmlcode=(htmlcodestr.format(site, contentname))
            updatearch(archhtmldir, htmlcode)
        updatearch(archhtmldir, htmlpart2)
    webbrowser.open(archhtmldir, new=1, autoraise=True)
    msginfo1, msginfo2, msginfo3=txtmsginfo((2, 5, 4))
    if totalchoices[2]!='both' and checkpoint==1:
        if totalchoices[0]=='Filmes':
            txtmsg=(('\nÚltimo {} {}: {}.').format(msginfo1, msginfo2, nametitle))
        else:
            txtmsg=(('\n{}\n\nÚltimo {} {}: {}.').format(nametitle, msginfo1, msginfo2, numcap))
        updatearch(dircapcheckpoint, 'None')
        updatearch(dircapcheckpoint, txtmsg)
    if countviewedcaps%5==0:
        updateglobalmsg((('Deseja continuar {}? ').format(msginfo3)))
        os.system('cls')
        updateglobalmsg(leiastr(askcontinueviewing))
    else:
        input("\nPressione 'Enter' para continuar.")
    shutil.rmtree(folderhtmldir)
    if 's' not in askcontinueviewing and askcontinueviewing!='0':
        updateglobalmsg('0')
    
        return 0
    updateglobalmsg('0')


 # Função para converter arquivos em '.cbz'
def cbzconvert(titlefolder, nametitle, namecap, capfolder):


     # Função para compactar os arquivos
    def ziparchs():
        nonlocal titlefolder, nametitle, namecap, capfolder


         # Função para finalizar a compactação e excluir a pasta de origem
        def closehq():
            try:
                hq
            except Exception:
                pass
            else:  
                hq.close()   
            shutil.rmtree(capfolder)
        

        for folder, subfolders, files in os.walk(capfolder):
            listpagefiles=files
            break
        if len(listpagefiles)==0:

            return -10
        if askcontinueviewing=='0':
            os.system("cls")
            print('\nTítulo: '+ nametitle)
            print(("\nCompactando {}...").format(namecap))
            printthreadmsg('offline')
        hq = zipfile.ZipFile(capfolder+'.zip', 'w')
        for file in listpagefiles:
            if (file.lower()).endswith('.png'):
                try:
                    hq.write(os.path.join(capfolder, file), os.path.relpath(os.path.join(capfolder,file), capfolder), compress_type = zipfile.ZIP_DEFLATED)
                except (FileNotFoundError):
                    pass
            else:
                try:
                    os.mkdir((titlefolder+'./{} (others_extensions)').format(namecap))
                except OSError:
                    pass
                finally:
                    savefiles=((titlefolder+'./{} (others_extensions)').format(namecap))
                shutil.copy(((folder+'\{}').format(file)), savefiles)
        closehq()
        if askcontinueviewing=='0':
            os.system("cls")
            print("\nCompactação feita.")
            printthreadmsg('offline')


     # Função para renomear extensões de arquivos
    def renameext():
        nonlocal titlefolder, nametitle, namecap

        exttorename='.zip'
        newext='.cbz'
        for folder, subfolders, files in os.walk(titlefolder):
            listzipfiles=files
            break
        if askcontinueviewing=='0':
            os.system("cls")
            print('\nTítulo: '+ nametitle)
            print(("\nConvertendo {} em '.cbz'...").format(namecap))
            printthreadmsg('offline')
        for file in listzipfiles:
            if (file.lower()).endswith(exttorename):
                try:
                    os.rename((titlefolder+'\{}').format(file), (titlefolder+'\{}').format((((os.path.splitext(file))[0])+((os.path.splitext(file))[1]).lower()).replace(exttorename, newext)))
                except (FileExistsError):
                    os.rename((titlefolder+'\{}').format(file), (titlefolder+'\{}').format((((os.path.splitext(file))[0])+'_(repeated)'+((os.path.splitext(file))[1]).lower()).replace(exttorename, newext)))


    if ziparchs()!=-10:
        renameext()
    if askcontinueviewing=='0':
        os.system("cls")
        print('\nProcesso concluído com sucesso!')
        printthreadmsg('offline')

        
 # Função para realizar os downloads
def downloader(titlefolder, nametitle, namecap, capfolder, pagesinfolist):
    pagesinfolist=pagesinfolist[1:][::2]
    numpage=-1
    for pgdata in pagesinfolist:
        numpage=numpage+1
        if pgdata!='':
            pagefile=getcontentfiledir(namecap, capfolder, numpage)
            if askcontinueviewing=='0':
                os.system('cls')
                print(('\n{}').format(nametitle))
                if totalchoices[0]=='Mangás' or totalchoices[0]=='Quadrinhos':
                    print(('\n{}').format(namecap))
                    print(('\nBaixando página {}...').format(numpage))
                else:
                    print(('\nBaixando {}...').format(namecap))
                printthreadmsg('offline')
            open(pagefile, 'wb').write(pgdata)
    if totalchoices[0]=='Mangás' or totalchoices[0]=='Quadrinhos':
        cbzconvert(titlefolder, nametitle, namecap, capfolder)


 # Função para iniciar os processos principais do programa
def startprocess(alldatarequired, alltitlesandlinks, typeprocess):
    loadcouter=-1
    onlineviewer=1
    for requireds in range(len(alldatarequired)):
        if onlineviewer==0:
            break
        nametitle=alldatarequired[requireds][0]
        namecaps=alldatarequired[requireds][1]
        listcaps=alldatarequired[requireds][3]
        checkpoint=alldatarequired[requireds][4]
        dircapcheckpoint=alldatarequired[requireds][5]
        qntcaps=len(namecaps)
        especifictitlepos=alldatarequired[requireds][2]
        countviewedcaps=0
        titlefolder=verifpath((typecontentdir+'\{}').format(nametitle), 1)
        for cap in listcaps:
            loadcouter=loadcouter+1
            if onlineviewer==0:
                break
            rightposcap=cap-1
            namecap=namecaps[rightposcap][0]
            countviewedcaps=countviewedcaps+1
            if typeprocess!='online':
                if totalchoices[0]=='Mangás' or totalchoices[0]=='Quadrinhos':
                    capfolder=(titlefolder+'\{}').format(namecap)
                    if typeprocess!='preload':
                        capfolder=verifpath(capfolder, 1)
                else:
                    capfolder=titlefolder
            if totalchoices[:2]==['Mangás', 'MangáHost']:
                capurl=(alltitlesandlinks[especifictitlepos][1]+(('/{}').format(namecaps[rightposcap][1])))
            else:
                capurl=namecaps[rightposcap][1]
            if typeprocess=='preload':
                if preloaddata(0, namecap, capfolder, capurl)==-10:

                    return -10
            else:
                while True:
                    try:
                        pagesinfolist=capsinfolist[loadcouter]
                    except (IndexError, NameError):
                        continue
                    else:
                        if -10 in pagesinfolist:

                            return -10
                        break
                if typeprocess=='online':
                    onlineviewer=onlineview(nametitle, cap, namecap, checkpoint, dircapcheckpoint, pagesinfolist, countviewedcaps) 
                else:
                    downloads=downloader(titlefolder, nametitle, namecap, capfolder, pagesinfolist)
                    if downloads==-10:

                        return -10
    if typeprocess!='preload':
        endmsg=('\nTodos os {} foram {}.')
        if typeprocess=='online':
            endmsg=endmsg.format('conteúdos', 'mostrados')
        else:
            endmsg=endmsg.format('downloads', 'finalizados')
        if askcontinueviewing=='0':
            os.system('cls')
            print(endmsg)


 # Função para obter informações específicas sobre o título escolhido
def especificinfo(alltitlesandlinks):
    global threadtrick, stoplist


     # Função para verificar se outro título será adicionado à lista de downloads
    def askaddmanga():
        showprogram(1)
        addmangá=('Deseja procurar por outr{0} {1} e adicioná-l{0} à lista de linetype? ').format(article, txtmsg1)
        if totalchoices[2]=='online':
            addmangá=addmangá.replace('linetype', 'reprodução')
        else:
            addmangá=addmangá.replace('linetype', 'downloads')
        addmangá=leiastr(addmangá)
        if 's' in addmangá:

            return 1
        else:
            if len(alldatarequired)==0:
                
                return -10
            else:
                
                return 0


    threadtrick=0
    updateglobalmsg('0')
    addmangá=1
    alldatarequired=[]
    article, txtmsg1=txtmsginfo((0, 1))
    while addmangá==1:
        datarequired=[]
        especifictitlepos=getespecifictile(alltitlesandlinks)
        if especifictitlepos==-10:
            addmangá=askaddmanga()
            if addmangá==1:
                continue
            elif addmangá==0:
                break
            else:
                
                return -10
        else:
            nametitle=alltitlesandlinks[especifictitlepos][0]
            titleurl=alltitlesandlinks[especifictitlepos][1]
            description=getinfo((titleurl.format('1')), 'descriptionclass', 'descriptionextrainfo', 'firstdescriptionfilter', 'seconddescriptionfilter')
            if description==-10:
                description=''
            if totalchoices[:2]==['Mangás', 'MangáLivre']:
                titleurl='https://mangalivre.net/series/chapters_list.json?page={}&id_serie='+titleurl.split('/')[-1]
            namecaps=getallinfolinks(titleurl, 'numtitlepgsclass', 'numtitlepgsextrainfo', 'firsttitlepgsfilter', 'secondtitlepgsfilter', 'capsnamesandidsclass', 'capsextrainfo', 'firstcapfilter', 'secondcapfilter')     
            if namecaps==-10:

                return -10
            if totalchoices[:2]==['Mangás', 'MangáLivre']:
                namecapscopy=copy.deepcopy(namecaps)
                namecaps=[]
                for fixcaps1 in namecapscopy:
                    fixcaps1=fixcaps1['chapters']
                    if fixcaps1!=False:
                        for fixcaps2 in fixcaps1:
                            partialnamecaps=[]
                            namecap='Capítulo {}'.format(fixcaps2['number'])
                            secondname=fixcaps2['chapter_name']
                            if secondname!=None and len(secondname)>0:
                                namecap='{} - {}'.format(namecap, secondname)
                            partialnamecaps.append(namecap.strip())
                            for fixcaps3 in fixcaps2['releases'].values():
                                capurl=confgs['basesite']+fixcaps3['link']+confgs['addcappageeurl']
                                partialnamecaps.append(capurl.strip())
                                if len(partialnamecaps)!=0:
                                    namecaps.append(partialnamecaps)
                                break
            namecaps=verifcopy(namecaps)
            if totalchoices[:2]==['Animes', 'Animezeira']:
                namecaps=namecaps[1:]
            if totalchoices[:2]==['Mangás', 'MangáHost'] or totalchoices[:2]==['Mangás', 'MangáLivre']:
                namecaps.reverse()
            qntcaps=len(namecaps)
        showprogram(1)
        print('\n'+nametitle)
        if totalchoices[:2]==['Mangás', 'MangáLivre']:
            print('\n'+description[1].strip())
        else:
            for dscrpt in description:
                if '.' in dscrpt:
                    print('\n'+dscrpt.strip())
                    break
        txrmsg2=txtmsginfo((2, ))[0]+'s'
        print(('\n{} possui {} {}.\n').format(nametitle, qntcaps, txrmsg2))
        allcaps=list(range(1, (qntcaps+1)))
        missingcaps=[]
        for numcap in range(qntcaps):
            namecap=namecaps[numcap][0]
            poscap=numcap+1
            print(('({}) {}.').format(poscap, namecap))
            if totalchoices[0]=='Mangás' or totalchoices[0]=='Quadrinhos':
                capfilezip=(typecontentdir+('\{}\{}.zip').format(nametitle, namecap))
                capfilecbz=(typecontentdir+('\{}\{}.cbz').format(nametitle, namecap))
                capfiletest1=verifpath(capfilecbz, 0)
            else:
                capfilemp4=(typecontentdir+('\{}\{}.mp4').format(nametitle, namecap))
                capfiletest1=verifpath(capfilemp4, 0)
            if capfiletest1==1:
                if totalchoices[0]=='Mangás' or totalchoices[0]=='Quadrinhos':
                    capfiletest2=verifpath(capfilezip, 0)
                    if capfiletest2==0:
                        try:
                            testzipfile=zipfile.ZipFile(capfilezip)
                        except (zipfile.error):
                            os.remove(capfilezip)
                            capfiletest2=1 
                        else:
                            if testzipfile.testzip()!=None:
                                    os.remove(capfilezip)
                                    capfiletest2=1 
                    if capfiletest2==0:
                        os.rename(capfilezip, capfilecbz)
                    else:
                        missingcaps.append(poscap)
                else:
                    missingcaps.append(poscap)
        if totalchoices[2]=='online':
            if totalchoices[0]=='Filmes':
                checkpointname='lastmoviewatched_(checkpoint).txt'
            else:
                checkpointname=nametitle+'_(checkpoint).txt'
            dircapcheckpoint=verifpath((typecontentdir+'\Checkpoints'), 1)
            dircapcheckpoint=(dircapcheckpoint+('\{}').format(checkpointname))
            checkpointarchtest=verifpath(dircapcheckpoint, 0)
            if checkpointarchtest==1:
                updatearch(dircapcheckpoint, '')
            else:
                cheackpointarch=open(dircapcheckpoint, 'r')
                conteúdo=cheackpointarch.read()
                try:
                    missingcaps=(list(range((int(((conteúdo.split())[-1]).replace('.', ''))+1), (qntcaps+1))))
                except (IndexError, ValueError):
                    missingcaps=copy.deepcopy(allcaps)
        else:
            dircapcheckpoint='0'
        if qntcaps!=0:
            while True:
                listcaps=('\nDigite os {} que deseja linetype: ').format(txrmsg2)
                txrmsg3=txtmsginfo((3, ))[0]
                if totalchoices[2]=='online':
                    listcaps=listcaps.replace('linetype', (('{} online').format(txrmsg3)))
                else:
                    listcaps=listcaps.replace('linetype', 'baixar')
                listcaps=leiacap(((input(listcaps).lower()).strip()), qntcaps)
                if listcaps==-10:
                    print('\nDados inválidos.\n\nTente novamente.')
                    continue
                else:
                    checkpoint=0
                    if listcaps=='continuar':
                        checkpoint=1
                        listcaps=copy.deepcopy(missingcaps)
                        if totalchoices[2]=='online':
                            if len(missingcaps)==0:
                                restartckpt=leiastr('Conteúdo finalizado.\n\nDeseja reiniciar seu "checkpoint"? ')
                                if 's' in restartckpt:
                                    listcaps=copy.deepcopy(allcaps)
                    elif listcaps=='todos':
                        if totalchoices[2]=='online':
                            listcaps=copy.deepcopy(allcaps)
                        else:
                            listcaps=copy.deepcopy(missingcaps)
                    else:
                        listcaps=list(set(listcaps).intersection(missingcaps))
                    listcaps=sorted(listcaps)
                    break
            datarequired.extend([nametitle, namecaps, especifictitlepos, listcaps, checkpoint, dircapcheckpoint])
            alldatarequired.append(datarequired)
        addmangá=askaddmanga()
        if addmangá==1:
            continue
        elif addmangá==0:
            break
        else:
            
            return -10
    totalqntcaps=0
    for requireds in alldatarequired:
        totalqntcaps=totalqntcaps+len(requireds[3])
    stoplist=[]
    stoplist.append(threadtrick)
    preloaddata(1, 0, 0, 0)
    try:
        preloadthread=threading.Thread(target=startprocess, args=(alldatarequired, alltitlesandlinks, 'preload'), daemon=True)
        preloadthread.start() 
    except (threading.ThreadError):
        pass
    time.sleep(1.25)
    if totalchoices[2]=='both':
        try:
            threadtoview=threading.Thread(target=startprocess, args=(alldatarequired, alltitlesandlinks, 'online'), daemon=True)
            threadtodownload=threading.Thread(target=startprocess, args=(alldatarequired, alltitlesandlinks, 'offline'), daemon=True)
            threadtoview.start()
            threadtodownload.start()
        except (threading.ThreadError):
            pass
    else:
        try:
            threadchoice=threading.Thread(target=startprocess, args=(alldatarequired, alltitlesandlinks, totalchoices[2]), daemon=True)
            threadchoice.start()
        except (threading.ThreadError):
            pass
    while True:
        if totalchoices[2]=='both':
            if threadtoview.is_alive()==False and 1 not in stoplist:
                threadtrick=1
                stoplist.append(threadtrick)
            if threadtodownload.is_alive()==False and -1 not in stoplist:
                threadtrick=-1
                stoplist.append(threadtrick)
                if 1 not in stoplist:
                    print("\nPressione 'Enter' para continuar.")
        else:
            if threadchoice.is_alive()==False:
                stoplist=[-1, 0, 1]
        if preloadthread.is_alive()==False and len(capsinfolist)!=totalqntcaps:
            stoplist=[-1, 0, 1]
            print("\nOcorreu um erro no sistema")
        if len(stoplist)==3:
            if totalchoices[2]=='both':
                printthreadmsg('finish')
            break
    preloaddata(1, 0, 0, 0)


 # Função para converter a string de dados em lista
def convertstrtolist(strobj, mark1, mark2):
    strobj=strobj.split(mark2)
    tamstrobj=len(strobj)
    completelist=[]
    buildlist=[]
    strcount=0
    countloop=0
    for list1 in strobj:
        countloop=countloop+1
        if list1==mark1:
            strcount=0
            buildlist=[]
            pass
        else:
            strcount=strcount+1
            buildlist.append(list1)
        if strcount==0 and countloop!=tamstrobj:
            completelist.append(buildlist)
  
    return completelist


 # Função para iniciar o programa
def run():
    reboot=1
    while reboot==1:
        showprogram(0)
        time.sleep(1.25)
        showprogram(1)
        if setdriverconf()==-10:
            reboot=askreboot()
        else:
            setconfig()
            alltitlesandlinks, reboot=presetdata()
            if reboot==1 and alltitlesandlinks!=-10:
                gethqpath(1)
                alltitlesandlinks=verifcopy(alltitlesandlinks)
                especificinfo(alltitlesandlinks)
                reboot=askreboot()
    os.system('cls')
    input('\nObrigado por usar o programa! ;) ')


if __name__=='__main__':
    run()