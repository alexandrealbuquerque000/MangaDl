
import os
from pathlib import Path
import time
import copy
from unidecode import unidecode
from tkinter import Tk
from .preset_data import keys, values
import requests
from msedge.selenium_tools import EdgeOptions, Edge
from webdriver_manager.microsoft import EdgeChromiumDriverManager
import re # Para filtrar a busca de títulos
from bs4 import BeautifulSoup # Para manipular e guardar dados obtidos do site
from flask import session


# Função para obter informações de todas as requisições feitas pelo programa
def getinfo(site, current_server, classinfo=None, extrainfo=None, firstfilter=None, secondfilter=None):


    def by_webdriver(site):
        
        options = EdgeOptions()
        options.use_chromium = True
        options.headless = True
        options.add_experimental_option('excludeSwitches', ['enable-logging'])
        driver = Edge(EdgeChromiumDriverManager(log_level=0, print_first_line=False).install(), options = options)
        driver.get(site)

        if [current_server.Name, current_server.Type] in [['BR Mangás', 'Mangás']]:
            for option in driver.find_elements_by_tag_name('option'):
                if option.text == 'Páginas abertas':
                    option.click()
                    break
        
        return driver
      

    # Função para ajustar URL caso incompleta
    def thirdfilter(url):
        if url!=None and url!='':
            if url.startswith('/'):
                url=current_server.Config['basesite']+url.lstrip('/')

            return url

        return 0


    # Função para verificar a utilização de um comando
    def verifstep(step):
        if step!=None:
            if step=='None':
                step=None
            
            return step

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

    site=thirdfilter(site)
    headers={'User-agent': 'Mozilla/5.0'}
    rqsttime=0
    while True:
        time.sleep(rqsttime)
        try:
            #   Se ficar lento colocar "stream=False"  #
            response = requests.get(site, stream=True, headers=headers)
            if classinfo=='pagescapclass':
                page_text=by_webdriver(site).page_source
            else:
                page_text=response.text

        except requests.RequestException as error: 
            session['Error']=1
            print('\nOcorreu um erro: '+ str(error))
            time.sleep(1.25)

            return -10
        if response.status_code==200:
            if current_server=='Download':

                return response
            firstfilter=verifstep(current_server.Config[firstfilter])
            secondfilter=verifstep(current_server.Config[secondfilter])
            verifclassname=classinfo
            classinfo=verifstep(current_server.Config[classinfo])
            extrainfo=verifstep(current_server.Config[extrainfo])
            
            soup = BeautifulSoup(page_text, 'html.parser')
            if firstfilter!=0:
                soup=soup.find(class_=firstfilter)
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
                        titlesgturl=thirdfilter(get(current_server.Config['titlesgturl']))
                        titlesgtname=get(current_server.Config['titlesgtname'])
                        if current_server.Name=='BR Mangás':
                            titlesgtname=titlesgtname.rsplit('Online', 1)[0]
                        if titlesgturl!=0:
                            titlesgtname=titlesgtname.rstrip('.')
                            titlesgtname=re.sub(r'[:*?"><|/\\]', ' ', titlesgtname).strip()
                            listinfo.append({'Name': titlesgtname, 'URL': titlesgturl})
                    elif verifclassname=='capsnamesandidsclass':
                        capsgturl=thirdfilter(get(current_server.Config['capsgturl']))
                        capsgtname=get(current_server.Config['capsgtname'])
                        if current_server.Name=='See Mangas':
                            capsgtname=capsgtname.replace('Ler ', '', 1)
                        elif current_server.Name=='Golden Mangás':
                            capsgtname=capsgtname.replace('Cap', 'Capítulo', 1)
                        elif current_server.Name=='Kissmanga':
                            capsgtname=capsgtname.split('-\n', 1)[-1]
                        if capsgturl!=0:
                            capsgtname=capsgtname.rstrip('.')
                            capsgtname=re.sub(r'[:*?"><|/\\]', ' ', capsgtname).strip()
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
                        pgsgturl=thirdfilter(get(current_server.Config['pgsgturl']))
                        if current_server.Name=='Kissmanga' and pgsgturl.startswith(current_server.Config['basesite']):
                            pgsgturl=0
                        if pgsgturl!=0:
                            listinfo.append({'URL': pgsgturl})
                    else:
                        listinfo.append([get('text')])
            if current_server.Name=='Mangás Chan' and verifclassname=='pagescapclass':
                listinfo=[{'URL': str(u+1)+'.'+listinfo[-1]['URL'].split('/')[-1].split('.')[-1]} for u in range(int(listinfo[-1]['URL'].split('/')[-1].split('.')[0]))]

            response.close()
            return listinfo

        else:
            if rqsttime<=3:
                rqsttime+=1
                continue

            return -100
  

 # Função para obter determinadas informações de todo o site
def getallinfolinks(Table, Ower_Table, pginf1):

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
        allinfolist=[]
        verifnumwebpages=None
        lastpage=0
        while True:
            lastpage+=1
            site=pginf1.format(lastpage)
            if Table_Name=='contents':
                description=getinfo(site, current_server, 'descriptionclass', 'descriptionextrainfo', 'firstdescriptionfilter', 'seconddescriptionfilter')
                if description!=-10:
                    Update(Ower_Table, description[0])
            numwebpagestest1=getinfo(site, current_server, pginf6, pginf7, pginf8, pginf9)
            if numwebpagestest1==-10:
            
                return -10
            if Table_Name=='titles':
                if numwebpagestest1==-100 or len(numwebpagestest1)==0 or numwebpagestest1==verifnumwebpages:
                    if current_server.Name=='Kissmanga' and numwebpagestest1==-100:
                        continue
                    break
                verifnumwebpages=copy.deepcopy(numwebpagestest1)
            if Table_Name=='subcontents':
                pagenum=0
                for item in numwebpagestest1:
                    if current_server.Type in ['Quadrinhos', 'Mangás']: 
                        typesubcontent='Página'
                    else:
                        typesubcontent='Vídeo'
                    pagenum+=1
                    item.update({'Name': '{}_{}'.format(typesubcontent, pagenum)})
                    if current_server.Name=='Mangás Chan':
                        title=re.sub(r'[.,"\'?:!;]', '', unidecode(Ower_Table.Ower.Name.splitlines()[0])).replace(' ', '-').lower()
                        cap=re.sub(r'[.,"\'?:!;]', '', unidecode(Ower_Table.Name.splitlines()[0])).replace(' ', '-').lower()
                        item.update({'URL': 'https://img.mangaschan.com/uploads/manga-images/{}/{}/{}/{}'.format(title[0],title,cap,item['URL'])})
            Added_Content=add_data(Table, Ower_Table.id, numwebpagestest1)
            allinfolist.extend(Added_Content)
            if Table_Name!='titles':
                break
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

    root = Tk()
    root.geometry('0x0')
    hqpathchoose=('Selecione o diretório da pasta que deseja guardar todos os conteúdos escolhidos: ')
    hqpathstr=hqpathchoose.replace('Selecione', '\nDigite')
    print('\n'+hqpathchoose)
    hqpath = tf.askdirectory(parent=root, initialdir="/",title =hqpathchoose)
    root.destroy()       

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
    if verifpath(content_dir+'.zip', 0)==False:
        getallinfolinks(Subcontents, Table, Table.URL)
        print('\nBaixando: {}\n'.format(Table.Name))   
        for subcontent in Table.Backref:
            subcontent__name=subcontent.Name+'.png'
            subcontent_dir=os.path.join(content_dir, subcontent__name)
            if verifpath(subcontent_dir, 0)==False:
                subcontent_url=subcontent.URL
                print(subcontent_url)
                subcontent_data=getinfo(subcontent_url, 'Download')
                if type(subcontent_data)==int:
                  
                    return -10
                print(subcontent_data)
                with open(subcontent_dir, 'wb') as file:
                    file.write(subcontent_data.content)
                    file.close()
                print(subcontent_dir, end='\n')

    if server_table.Type in ['Quadrinhos', 'Mangás']:
        print('Convertendo {} para .cbz\n'.format(Table.Name))
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
    print('Concluído!')