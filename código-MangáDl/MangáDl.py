
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
import time # Para fazer o programa esperar um certo tempo para executar determinada ação

# Função para aceitar apenas strings
def leiastr(msg):
    while True:
        print()
        verifstr=str(input(msg).strip().replace(" ", ""))
        if verifstr.isalpha() == False:
            print()
            print("ERRO:""\nDigite apenas letras.")
            continue
        else:
            verifstr=verifstr.lower()

            return verifstr

# Função para perguntar sobre a reinicialização do programa
def askreboot():
    reboot=leiastr('Deseja reiniciar o programa? ')
    if 's' in reboot:

        return 1

    return 0

# Função para ajustar diretório inserido
def inputdir(pdir):
    pdir=input(pdir).strip('"').strip()

    return pdir

# Função para obter o diretório central de destino dos arquivos
def gethqpath(mode):
    global hqpath

    if mode==1:
        root = tkinter.Tk()
        root.geometry('0x0')
        hqpathchoose=('Selecione o diretório da pasta que contém todos os arquivos que deseja manipular: ')
        print('\n'+hqpathchoose)
        hqpath = tf.askdirectory(parent=root, initialdir="/",title =hqpathchoose)
        root.destroy()       
        if hqpath=='':
            print('\nOpção cancelada.\n\nTente novamente')
            hqpath=inputdir('\nDigite o diretório da pasta que contém todos os arquivos que deseja manipular: ')
        while ((Path(hqpath)).is_dir())==False:
            print("\nEsse diretório não existe.\n\nTente novamente.")
            hqpath=inputdir('\nDigite o diretório da pasta que contém todos os arquivos que deseja manipular: ')
    else:
        archpath=inputdir('\nDigite o diretório do arquivo que contém todos os dados necessários para a inicialização do programa: ')
        while True:
            try:
                arquivo=open(archpath, 'r', encoding="utf-8")
            except (FileNotFoundError, PermissionError, OSError):
                askarcherro=leiastr('Arquivo inválido.\n\nDeseja escolher algum outro arquivo? ')
                if 's' in askarcherro:
                    archpath=inputdir('\nDigite o diretório do arquivo que contém todos os dados necessários para o funcionamento do programa: ')
                    continue
                else:
                    askcreatearch=leiastr("Deseja criar um arquivo chamado com os dados para o funcionamento do programa ou prefere utilizar dados temporários coletados em tempo real? ")
                    if 'cr' in askcreatearch:
                        conteúdo, reboot=createarchdata()
                    else:
                        conteúdo, reboot=colectdata()
                    break
            else:
                reboot=1
                conteúdo=arquivo.read()
                conteúdo=convertstrtolist(conteúdo, 'AlêMark', 'minimark')
                break

        return conteúdo, reboot

 # Função para criar arquivo com os dados do site
def createarchdata():
    archpath=inputdir('\nDigite o diretório em que deseja criar esse arquivo: ')
    while ((Path(archpath)).is_dir())==False:
        print("\nEsse diretório não existe.\n\nTente novamente.")
        archpath=inputdir('\nDigite o diretório em que deseja criar esse arquivo: ')
    namearch=inputdir('\nDigite o nome do arquivo: ')
    namearch=namearch+'.txt'
    archpath=archpath+(('\{}').format(namearch))
    arquivo=open(archpath, 'w')
    arquivo.close()
    arquivo=open(archpath, 'w', encoding="utf-8")
    conteúdo, reboot=colectdata()
    formatedconteúdo=convertlisttostr(conteúdo, 'AlêMark', 'minimark')
    arquivo.write(formatedconteúdo)
    arquivo.close()

    return conteúdo, reboot

 # Função para converter a lista de dados em string
def convertlisttostr(listobj, mark1, mark2):
    completestr=mark1
    for str1 in listobj:
        for str2 in str1:
            completestr = completestr + mark2 + str2
        completestr= completestr + mark2 + mark1
   
    return completestr

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

# Função para verificar existência de pasta ou arquivo
def verifpath(dirp, mode):
    if (os.path.exists(dirp))==True:
        if mode==0:

            return 0
    else:
        if mode==0:

            return 1
        os.mkdir(dirp)
    
    return dirp

# Função para realizar os downloads
def startdownloads(alldatarequired, alltitlesandlinks):
    for requireds in range(len(alldatarequired)):
        nametitle=alldatarequired[requireds][0]
        namecaps=alldatarequired[requireds][1]
        listcaps=alldatarequired[requireds][3]
        qntcaps=len(namecaps)
        especifictitlepos=alldatarequired[requireds][2]
        titlefolder=verifpath((hqpath+('\{}').format(nametitle)), 1)
        for cap in sorted(listcaps):
            rightposcap=qntcaps-cap
            namecap=namecaps[rightposcap][0]
            capfolder=verifpath((titlefolder+('\{}').format(namecap)), 1)
            capurl=(alltitlesandlinks[especifictitlepos][1]+(('/{}').format(namecaps[rightposcap][1])))
            pagesurl=getinfo(capurl, None, 'img')
            if pagesurl==-10:

                return -10
            numpage=-1
            for pg in pagesurl:
                numpage=numpage+1
                pgdata=getinfo(pg, None, 'content')
                if pgdata==-10:

                    return -10
                pgdata=(pgdata.content)
                filename=(('Page_{}').format(numpage))
                pagefile=capfolder+(('\{}.png').format(filename))
                if verifpath(pagefile, 0)==1:
                    open(pagefile, 'wb').write(pgdata)
                    os.system('cls')
                    print(('\n{}').format(nametitle))
                    print(('\n{}').format(namecap))
                    print(('\nBaixando página {}...').format(numpage))
            os.system('cls')
            cbzconvert(titlefolder, nametitle, namecap, capfolder)
    os.system('cls')
    print('\nTodos os downloads foram concluídos.')

# Função para converter arquivos em '.cbz'
def cbzconvert(titlefolder, nametitle, namecap, capfolder):

    # Função para compactar os arquivos
    def ziparchs():
        nonlocal titlefolder, nametitle, namecap, capfolder

        # Função para finalizar a compactação e excluir a pasta de origem
        def closehq():
            nonlocal hq, capfolder

            try:
                hq
            except(UnboundLocalError, NameError):
                pass
            else:  
                hq.close()   
            shutil.rmtree(capfolder)
            os.system("cls")
        
        for folder, subfolders, files in os.walk(capfolder):
            listpagefiles=files
            break
        if len(listpagefiles)==0:

            return -10

        print('\nTítulo: '+ nametitle)
        print(("\nCompactando {}...").format(namecap))
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
        print("\nCompactação feita.")

    # Função para renomear extensões de arquivos
    def renameext():
        nonlocal titlefolder, nametitle, namecap

        exttorename='.zip'
        newext='.cbz'
        for folder, subfolders, files in os.walk(titlefolder):
            listzipfiles=files
            break
        for file in listzipfiles:
            os.system("cls")
            print('\nTítulo: '+ nametitle)
            print(("\nConvertendo {} em '.cbz'...").format(namecap))
            if (file.lower()).endswith(exttorename):
                try:
                    os.rename((titlefolder+'\{}').format(file), (titlefolder+'\{}').format((((os.path.splitext(file))[0])+((os.path.splitext(file))[1]).lower()).replace(exttorename, newext)))
                except (FileExistsError):
                    os.rename((titlefolder+'\{}').format(file), (titlefolder+'\{}').format((((os.path.splitext(file))[0])+'_(repeated)'+((os.path.splitext(file))[1]).lower()).replace(exttorename, newext)))
        os.system("cls")

    if ziparchs()!=-10:
        renameext()

    print('\nProcesso concluído com sucesso!')

# Função para obter informações de todas as requisições feitas pelo programa
def getinfo(site, classinfo, extrainfo):

    try:
        response = requests.get(site, stream=True, headers={'User-agent': 'Mozilla/5.0'})
    except requests.RequestException as error: 
        print('\nOcorreu um erro: '+ (str(error)[:str(error).index('(')]))

        return -10

    if extrainfo=='content':

        return response
    if response.status_code==200:
        soup = BeautifulSoup(response.text, 'html.parser')
        allinfo=soup.find_all(extrainfo, class_=classinfo)
        listinfo=[]
        for info in allinfo:
            if classinfo=='manga-block-title-link':
                showprogram()
                print('\nColetando dados...')
                listinfo.append([(info.get('title')), (info.get('href'))])
            elif classinfo=='btn-caps w-button':
                listinfo.append([(info.get('title')), (info.get_text())])
            elif extrainfo=='img':
                listinfo.append((info.get('src')))
            else:
                listinfo.append([info.get_text()])

        return listinfo
    else:
        print('\nOcorreu um erro: '+str(response.status_code))

        return -10

# Função para obter o número de páginas do site
def getnumwebpages():
    numwebpages=getinfo('https://mangahosted.com/mangas', 'pages', None)
    if numwebpages==-10:

        return -10, -10
    numwebpages=numwebpages[0][0]
    numwb=[]
    for wpinfo in numwebpages.split():
        try:
            wbi=int(wpinfo)
        except(ValueError):
            pass
        else:
            numwb.append(wbi)
    if any(testp==None for testp in numwb) or len(numwb)!=2:
        print('\nOcorreu algum erro durante a coleta de informações do website.')

        return -10, -10
    else:

        return numwb[0], numwb[1]

# Função para obter todos os títulos/links do site
def getalltitlesandlinks():
    alltitlesandlinks=[]
    numwebpagestarts, numwebpagesends = getnumwebpages()
    if (numwebpagestarts, numwebpagesends) == (-10, -10):

        return -10
    for pg in range(numwebpagestarts, (numwebpagesends+1)):
        numwbpgsinfo=getinfo((('https://mangahosted.com/mangas/page/{}').format(pg)), 'manga-block-title-link', None)
        if numwbpgsinfo==-10:

            return -10
        alltitlesandlinks.extend(numwbpgsinfo)
    
    return alltitlesandlinks

# Função para obter a informação de qual título foi escolhido
def getespecifictile(alltitlesandlinks):
    asktitle=input('\nDigite o nome do mangá que deseja ler: ').strip().lower()
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

        return -10

# Função para obter informações específicas sobre o título escolhido
def especificinfo(alltitlesandlinks):

    # Função para verificar se outro título será adicionado à lista de downloads
    def askaddmanga():
        nonlocal alldatarequired

        addmangá=leiastr('Deseja procurar por outro mangá e adicioná-lo à lista de downloads? ')
        if 's' in addmangá:

            return 1
        else:
            if len(alldatarequired)==0:
                
                return -10
            else:
                
                return 0

    addmangá=1
    alldatarequired=[]
    
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
            namecaps=getinfo(alltitlesandlinks[especifictitlepos][1], 'btn-caps w-button', None)
            if namecaps==-10:

                return -10
            qntcaps=len(namecaps)
        nametitle=alltitlesandlinks[especifictitlepos][0]
        print(('\n{} possui {} episódios.\n').format(nametitle, qntcaps))
        missingcaps=[]
        for numcap in reversed(range(qntcaps)):
            namecap=namecaps[numcap][0]
            poscap=qntcaps-numcap
            print(('({}) {}.').format(poscap, namecap))
            capfile=(hqpath+('\{}\{}.cbz').format(nametitle, namecap))
            capfiletest=verifpath(capfile, 0)
            if capfiletest==1:
                missingcaps.append(poscap)
        while True:
            listcaps=leiacap(((input('\nDigite os capítulos que deseja baixar: ').lower()).strip()), qntcaps)
            if listcaps==-10:
                ('\nDados inválidos.\nTente novamente.')
                continue
            else:
                if listcaps=='continue':
                    listcaps=copy.deepcopy(missingcaps)
                else:
                    listcaps=list(set(listcaps).intersection(missingcaps))
                break
        datarequired.extend([nametitle, namecaps, especifictitlepos, listcaps])
        alldatarequired.append(datarequired)
        addmangá=askaddmanga()
        if addmangá==1:
            continue
        elif addmangá==0:
            break
        else:
            
            return -10

    if startdownloads(alldatarequired, alltitlesandlinks)==-10:

        return -10

# Função para conferir os capítulos escolhidos para download
def leiacap(caps, qntcaps):

    def read():
        nonlocal caps, qntcaps

        for cp in caps:
            try:
                int(cp) 
            except (ValueError, IndexError):
                caps=caps.replace(cp, ' ')

        capsinfo=[]
        for cap in caps.split():
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
    elif 'c' in caps or 't' in caps:
        listcaps='continue'
    else:
        caps=read()
        if caps==-10 or len(caps)!=1:
            
            return -10
        else:
            listcaps=caps

    return listcaps

# Função para mostrar o nome do programa
def showprogram():
    os.system('cls')
    print('-'*16)
    print(' MangáDl by Alê')
    print('-'*16)

def presetdata():
    showprogram()
    askpreset=leiastr('Deseja coletar os dados atualizados ou prefere utilizar dados já existentes? ')
    if 'ex' in askpreset:
        askpreset=1
        alltitlesandlinks, reboot=gethqpath(0)
    else:
        askpreset=0
        askcreatearch=leiastr("Deseja criar um arquivo chamado 'alldatamangádl.txt' na sua área de trabalho com os dados para o funcionamento do programa ou prefere utilizar dados temporários coletados em tempo real? ")
        if 's' in askcreatearch:
            alltitlesandlinks, reboot=createarchdata()
        else:
            alltitlesandlinks, reboot=colectdata()
    
    return askpreset, alltitlesandlinks, reboot


def colectdata():
    while True:
        os.system('cls')
        alltitlesandlinks=getalltitlesandlinks()
        if alltitlesandlinks==-10:
            reboot=askreboot()
            if reboot==1:
                continue
            break
        reboot=1
        break

    return alltitlesandlinks, reboot

# Função para iniciar o programa
def run():
    askpreset, alltitlesandlinks, reboot=presetdata()
    while reboot==1:
        showprogram()
        gethqpath(1)
        result=especificinfo(alltitlesandlinks)
        reboot=askreboot()
    os.system('cls')
    input('\nObrigado por usar o programa! ;) ')


run()