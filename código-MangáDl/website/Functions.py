
import os
from pathlib import Path
import time
import copy
from .preset_data import keys, values
import requests
# from selenium.webdriver import Edge
from msedge.selenium_tools import EdgeOptions, Edge
from selenium.webdriver.edge.service import Service
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.edge.options import Options
from webdriver_manager.microsoft import EdgeChromiumDriverManager
import re # Para filtrar a busca de títulos
from bs4 import BeautifulSoup # Para manipular e guardar dados obtidos do site
from flask import session

# Função para obter informações de todas as requisições feitas pelo programa
def getinfo(site, current_server, classinfo, extrainfo, firstfilter, secondfilter):


    def by_webdriver(site):
        
        options = EdgeOptions()
        options.use_chromium = True
        options.headless = False
        options.add_experimental_option('excludeSwitches', ['enable-logging'])
        driver = Edge(EdgeChromiumDriverManager(log_level=0, print_first_line=False).install(), options = options)
        driver.get(site)
        
        return driver
      

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
                basesite=current_server.Config['basesite']
                if all(url.startswith(index)==False for index in ['http', basesite]):
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

    '''
    
    PÁGINA 30 DO MANGÁ HOST ESTÁ DANDO ERRO, CONFERIR DPS ERRO 403
    #####################
    #####################
    '''

    rqsttime=0
    while True:
        time.sleep(rqsttime)
        try:
            site=thirdfilter(site)
            print(site)
            ### se ficar lento bota dtream=False###3

            if classinfo=='pagescapclass':
                response = by_webdriver(site)
                page_text=response.page_source
            else:
                response = requests.get(site, stream=True, headers={'User-agent': 'Mozilla/5.0'})
                page_text=response.text
            # response = requests.get(site, headers={'User-agent': 'Mozilla/5.0'})
        except requests.RequestException as error: 
            # seterrormsg('\nOcorreu um erro: '+ str(error))
            # time.sleep(1.25)

            return -10
        if requests.get(site, stream=True, headers={'User-agent': 'Mozilla/5.0'}).status_code==200:
            firstfilter=verifstep(current_server.Config[firstfilter])
            secondfilter=verifstep(current_server.Config[secondfilter])
            verifclassname=classinfo
            if verifclassname=='contentpagesclass':

                return response
            classinfo=verifstep(current_server.Config[classinfo])
            extrainfo=verifstep(current_server.Config[extrainfo])
            
            soup = BeautifulSoup(page_text, 'html.parser')
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
            temp=0
            print(allinfo)
            for info in allinfo:
                if secondfilter!=0:
                    info=info.find(secondfilter)
                if info!=None:
                    if verifclassname=='titlesandlinksclass':
                        titlesgturl=get(current_server.Config['titlesgturl'])+current_server.Config['addtitleurl']
                        titlesgturl=thirdfilter(titlesgturl)
                        titlesgtname=get(current_server.Config['titlesgtname'])
                        if len(titlesgtname)<=1:
                                titlesgturl=0
                        if titlesgturl!=0:
                            titlesgtname=titlesgtname.strip('\n')
                            titlesgtname=re.sub(r'[:*?"><|/\\]', ' ', titlesgtname).strip()
                            listinfo.append({'Name': titlesgtname, 'URL': titlesgturl})
                    elif verifclassname=='capsnamesandidsclass':
                        capsgturl=get(current_server.Config['capsgturl'])+current_server.Config['addcappageeurl']
                        capsgtname=get(current_server.Config['capsgtname'])
                        if len(capsgtname)<=1:
                                capsgturl=0
                        if capsgturl!=0:
                            capsgtname=capsgtname.strip('\n').strip()
                            capsgtname=re.sub(r'[:*?"><|/\\]', ' ', capsgtname).strip()
                            if [current_server.Name, current_server.Type] in [['Animes Online GG', 'Animes'], ['Animes Online', 'Animes']]:
                                if capsgtname=='Episódio 1':
                                    temp+=1
                                capsgtname='Temp {} - {}'.format(temp, capsgtname)
                            if [current_server.Name, current_server.Type]==['Mangá Host', 'Mangás']:
                                capsgturl=site+'/{}'.format(capsgturl)
                            listinfo.append({'Name': capsgtname, 'URL': capsgturl})
                    elif verifclassname=='descriptionclass':
                        description=get(current_server.Config['descriptiontxt'])
                        if type(description)==list:
                            description=description[0]
                        listinfo.append({'Description': description.strip('\n')})
                    elif verifclassname=='numtitlepgsclass':
                        listinfo.append(get(current_server.Config['titlepgsgtnum']))
                    elif verifclassname=='numcappgsclass':
                        listinfo.append(get(current_server.Config['cappgsgtnum']))
                    elif verifclassname=='pagescapclass':
                        pgsgturl=get(current_server.Config['pgsgturl'])
                        listinfo.append({'URL': pgsgturl})
                    else:
                        listinfo.append([get('text')])
        
            return listinfo

        elif response.status_code in range(401, 451):
            session['Error']=1
            if rqsttime<=3:
                rqsttime+=0.25
                continue

            return -100
        else:
            print('\nOcorreu um erro: '+str(response.status_code))
            time.sleep(1.25)
        
            return -10

 # Função para obter determinadas informações de todo o site
def getallinfolinks(Table, Ower_Table, pginf1):

    
    allinfolist=[]
    verifnumwebpages=[]
    Table_Name=Table.__tablename__
    current_server=Ower_Table
    if Ower_Table == None:
        for Type in values.items():
            ContentList=[]
            for Name in Type[1].items():
                Config=dict(zip(keys, Name[1]))
                Added_Content=add_data(Table, None, [{'Name': Name[0], 'Type': Type[0], 'Config':Config}])
                ContentList.extend(Added_Content)
            DelDescendants(Table, {'Type': Type[0]}, ContentList)
    else:
        while True:
            if current_server.__tablename__!='servers':
                current_server=current_server.Ower
            else:
                if Table_Name=='titles':
                    site_keys=('titlesandlinksclass', 'titlesextrainfo', 'firsttitlesfilter', 'secondtitlesfilter')
                elif Table_Name=='contents':
                    site_keys=('capsnamesandidsclass', 'capsextrainfo', 'firstcapfilter', 'secondcapfilter')
                else:
                    site_keys=('pagescapclass', 'cappagesextrainfo', 'firstpgscapfilter', 'secondpgscapfilter')
                pginf6, pginf7, pginf8, pginf9=site_keys
                break
        lastpage=0
        pagenum=-1
        while True:
            lastpage+=1
            site=pginf1.format(lastpage)
            if lastpage==1 and pginf6=='capsnamesandidsclass':
                description=getinfo(site, current_server, 'descriptionclass', 'descriptionextrainfo', 'firstdescriptionfilter', 'seconddescriptionfilter')
                if description!=-10:
                    Update(Ower_Table, description[0])
            numwebpagestest1=getinfo(site, current_server, pginf6, pginf7, pginf8, pginf9)
            print('result')
            print((numwebpagestest1))
            if numwebpagestest1==-10:
            
                return -10
            if numwebpagestest1==-100 or numwebpagestest1==verifnumwebpages or len(numwebpagestest1)==0:
                if [current_server.Name, current_server.Type] in [['Mangá Host', 'Mangás'], ['Animes Zone', 'Animes']] and numwebpagestest1==-100:
                    continue
                break
            verifnumwebpages=copy.deepcopy(numwebpagestest1)
            if pginf6=='pagescapclass':
                for item in numwebpagestest1:
                    if current_server.Type in ['Quadrinhos', 'Mangás']: 
                        typesubcontent='Página'
                    else:
                        typesubcontent='Vídeo'
                    pagenum+=1
                    item.update({'Name': '{}_{}'.format(typesubcontent, pagenum)})
            Added_Content=add_data(Table, Ower_Table.id, numwebpagestest1)
            allinfolist.extend(Added_Content)
        DelDescendants(Table, {'Ower_id': Ower_Table.id}, allinfolist)
    
def Update(Table_Query, New_Content):
    from . import db
    
    Table=Table_Query.__table__
    Query_Dict=Table_Query.__dict__
    update_dict={}
    
    for key, value in New_Content.items():
        if Query_Dict.get(key)!=value:
            update_dict.update({key: value})
    if len(update_dict)!=0:
        db.session.execute(db.update(Table).where(Table.c.id==Table_Query.id).values(**update_dict))
        db.session.commit() 

def Get_ExactTable(Table, filters, order_by=None):

    return Table.query.order_by(order_by).filter_by(**filters)

def GetRefList(Table):
    RefList=[]
    for Ref in Table:
        try:
            Backref=Ref.Backref
        except AttributeError:
            pass
        else:
            if Backref.count()!=0:
                RefList.append(Backref)
    return RefList

def DelDescendants(Table, filters, save_list):
    from . import db

    Del_Table=Get_ExactTable(Table, filters).filter(~(Table.id.in_(save_list)))
    DelList=[Del_Table]
    TempRef=GetRefList(Del_Table)
    while True:
        DelList.extend(TempRef)
        VerifRefList=[]
        for RefElem in TempRef:
            RefList=GetRefList(RefElem)
            if len(RefList)!=0:
                VerifRefList.extend(RefList)
        if len(VerifRefList)==0:
            break
        TempRef=VerifRefList.copy()
    DelList.reverse()
    for ItemToDel in DelList:
        for ElemToDel in ItemToDel:
            db.session.delete(ElemToDel)
            db.session.commit()

def add_data(Table, Ower_id, ContentList):

    from . import db
    
    Table_Name=Table.__tablename__
    Added_Content=[]
    for dbcontent in ContentList:
        if Table_Name=='users':
            queryinfo=Table.query.filter((Table.Name==dbcontent['Name']) & (Table.Password==dbcontent['Password']))
        elif Table_Name=='servers':
            queryinfo=Table.query.filter((Table.Name==dbcontent['Name']) & (Table.Type==dbcontent['Type']))
        else:
            queryinfo=Table.query.filter(((Table.Name==dbcontent['Name']) | (Table.URL==dbcontent['URL'])) & (Table.Ower_id==Ower_id))
        if len(queryinfo.all())==0:
            if Ower_id!=None:
                dbcontent.update({'Ower_id': Ower_id})

                
            # TA DANDO ESSE ERROOOOOOO sqlalchemy.exc.OperationalError: (sqlite3.OperationalError) attempt to write a readonly database



            db.session.execute(db.insert(Table).values(**dbcontent))
            db.session.commit()
            queryinfo=queryinfo.first()
        else:
            queryinfo=queryinfo.first()
            Update(queryinfo, dbcontent)

        Added_Content.append(queryinfo.id)

    return Added_Content


    
 # Função para verificar existência de pasta ou arquivo
def verifpath(dirp, mode):
    if (os.path.exists(dirp))==True:
        if mode==0:

            return True
    else:
        if mode==0:

            return False
        else:
            os.mkdir(dirp)
        
    return dirp

# Função para obter o diretório central de destino dos arquivos
def gethqpath():


    # root = tkinter.Tk()
    # root.geometry('0x0')
    hqpathchoose=('Selecione o diretório da pasta que deseja guardar todos os conteúdos escolhidos: ')
    hqpathstr=hqpathchoose.replace('Selecione', '\nDigite')
    # print('\n'+hqpathchoose)
    # hqpath = tf.askdirectory(parent=root, initialdir="/",title =hqpathchoose)
    # root.destroy()       


    hqpath=os.getcwd()
    if hqpath=='':
        print('\nOpção cancelada.\n\nTente novamente')
        hqpath=input(hqpathstr)
    while ((Path(hqpath)).is_dir())==False:
        print("\nEsse diretório não existe.\n\nTente novamente.")
        hqpath=input(hqpathstr)
    
    return hqpath








# Função para carregar continuamente os dados que serão utilizados 
def downloader(Table, dir):
    from .models import Subcontents

    title_table=Table.Ower
    server_table=title_table.Ower
    title_dir=verifpath(os.path.join(verifpath(os.path.join(dir, server_table.Type), 1), title_table.Name), 1)
    if any(file for file in os.listdir(title_dir) if file.endswith('.cbz') and os.path.splitext(file)[0]==Table.Name):

        return None



    if not session.get('Downloads'):
        session['Downloads']={}
    session['Downloads'].update({Table.Name:True})

    content_dir=verifpath(os.path.join(title_dir, Table.Name), 1)
    getallinfolinks(Subcontents, Table, Table.URL)
    print('Baixando'+Table.Name)   
    print(content_dir)
    for subcontent in Table.Backref:
        subcontent__name=subcontent.Name+'.png'
        subcontent_dir=os.path.join(content_dir, subcontent__name)
        if verifpath(subcontent_dir, 0)==False:
            subcontent_url=subcontent.URL
            print(subcontent_url)
            subcontent_data=getinfo(subcontent_url, server_table, 'contentpagesclass', 'contentpagesextainfo', 'firstcontentfilter', 'secondcontentfilter')
            if subcontent_data==-10:
                input('erro!')
            print(subcontent_data)
            with open(subcontent_dir, 'wb') as file:
                file.write(subcontent_data.content)
                file.close()
            print(subcontent_dir)
    if server_table.Type in ['Quadrinhos', 'Mangás']:
        cbzconvert(content_dir)
    session['Downloads'].update({Table.Name:False})
 # Função para converter arquivos em '.cbz'
def cbzconvert(content_dir):

    from pathlib import Path
    import zipfile
    import shutil
    titlefolder=Path(content_dir).parent
     # Função para compactar os arquivos
    def ziparchs():
        
        nonlocal content_dir,titlefolder

         # Função para finalizar a compactação e excluir a pasta de origem
        def closehq():
            try:
                hq
            except Exception:
                pass
            else:  
                hq.close()   
            shutil.rmtree(content_dir)

        listpagefiles=[file for file in os.listdir(content_dir) if file.endswith('.png')==True]

        if len(listpagefiles)==0:

            return -10
        hq = zipfile.ZipFile(content_dir+'.zip', 'w')
        for file in listpagefiles:
            hq.write(os.path.join(content_dir, file), os.path.relpath(os.path.join(content_dir,file), content_dir), compress_type = zipfile.ZIP_DEFLATED)
        closehq()


     # Função para renomear extensões de arquivos
    def renameext():
        nonlocal titlefolder, content_dir

        exttorename='.zip'
        newext='.cbz'
        listzipfiles=[file for file in os.listdir(titlefolder) if file.endswith(exttorename)==True]
        for file in listzipfiles:
            if (file.lower()).endswith(exttorename):
                os.rename(os.path.join(titlefolder,file), os.path.join(titlefolder, os.path.splitext(file)[0]+os.path.splitext(file)[1].lower().replace(exttorename, newext)))

    verifzip=True
    if verifpath(content_dir+'.zip', 0)==False:
        verifzip=ziparchs()
    if verifzip!=-10:
        renameext()
    print('done')