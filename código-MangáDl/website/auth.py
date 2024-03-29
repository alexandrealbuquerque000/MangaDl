from .Functions import Get_ExactTable, add_data
from flask import Blueprint, render_template, request, flash, session, redirect, url_for
from werkzeug.security import generate_password_hash, check_password_hash
from .models import Titles, Users, Servers, Contents, Subcontents
from .Functions import  getallinfolinks, downloader, gethqpath
from . import db
import os
from flask_login import login_user, login_required, logout_user, current_user

auth = Blueprint('auth', __name__)

# @auth.route('/error', methods=['GET', 'POST'])
# def error():
#     return session.pop('error')


@auth.route('/downloads')
@login_required
def downloads():
    
    return render_template('downloads.html', user=current_user, Teste=session.get('Downloads'))


@auth.route('/refresh', methods=['GET', 'POST'])
@login_required
def refresh():
    Servers_List=Get_ExactTable(Servers)
    getallinfolinks(Servers, None, None)
    if request.method == 'POST':
        for server in request.form.getlist('search', type=Servers.query.get):
           
            getallinfolinks(Titles, server, server.Config['pagessite'])
    return render_template('refresh.html', user=current_user, Servers_List=Servers_List)

@auth.route('/search', methods=['GET', 'POST'])
@login_required
def search():
    Servers_List=Get_ExactTable(Servers)
    Favorites = current_user.Favorites
    if request.method == 'POST':
        Title=request.form.get('search', type=Titles.query.get)
       
        if Title == None:
            flash('Nenhuma opção foi selecionada.', category='error')
        else:
    
            return redirect(url_for('auth.title', Servidor=Title.Ower.Name, Title=Title.Name))
    
    return render_template('search.html', user=current_user, Servers_List=Servers_List, Favorites=Favorites)

@auth.route('/<Servidor>/<Title>', methods=['GET', 'POST'])
@login_required
def title(Servidor, Title):

    server_table=Get_ExactTable(Servers, {'Name':Servidor}).first()
    title_table = Get_ExactTable(Titles, {'Name':Title, 'Ower': server_table}).first()
    Favorites = current_user.Favorites
    Last_Access = current_user.Checkpoints.filter_by(Ower=title_table).first()
    if request.method == 'POST':
        favorito=request.form.get('check_box', type=bool, default=False)
        if title_table in Favorites:
            Favorites.remove(title_table)
            db.session.commit()
        if favorito:
            Favorites.append(title_table)
            db.session.commit()
        contents=request.form.getlist('search', type=Contents.query.get)
        baixar=request.form.get('switcher', type=bool)
        if baixar:   
            downloader(contents, gethqpath())
        else:
            return redirect(url_for('auth.content', Servidor=server_table.Name, Title=title_table.Name, Content=contents[0].Name)) 
    else:
        if title_table==None:

            return redirect(url_for('auth.search'))
        titleurl=title_table.URL
        getallinfolinks(Contents, title_table, titleurl)
    
    return render_template('title.html', user=current_user, Title=title_table, Favorites=Favorites, Last_Access=Last_Access)


@auth.route('/<Servidor>/<Title>/<Content>', methods=['GET', 'POST'])
@login_required
def content(Servidor, Title, Content):
    
    server_table=Get_ExactTable(Servers, {'Name':Servidor}).first()
    title_table = Get_ExactTable(Titles, {'Name':Title, 'Ower': server_table}).first()
    title_page=url_for('auth.title', Servidor=server_table.Name, Title=title_table.Name)
    contents=title_table.Backref.all()
    content_table = Get_ExactTable(Contents, {'Name':Content, 'Ower': title_table}, 'Name').first()
    if content_table==None:

        return redirect(url_for('auth.title', Servidor=Servidor, Title=Title))
    content_index=contents.index(content_table)
    previous_content=next_content=None
    if content_index>0:
        previous_content=url_for('auth.content', Servidor=server_table.Name, Title=title_table.Name, Content=contents[content_index-1].Name)
    if content_index<len(contents)-1:
        next_content=url_for('auth.content', Servidor=server_table.Name, Title=title_table.Name, Content=contents[content_index+1].Name)
    getallinfolinks(Subcontents, content_table, content_table.URL)
    for checkpoint in current_user.Checkpoints.filter_by(Ower=title_table):
        current_user.Checkpoints.remove(checkpoint)
        db.session.commit()
    current_user.Checkpoints.append(content_table)
    db.session.commit()

    return render_template('content.html', user=current_user, Content=content_table, previous_content=previous_content, next_content=next_content, title_page=title_page)

@auth.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        Username = request.form.get('username')
        password = request.form.get('password')
        dict_info={'Name': Username}
        user = Get_ExactTable(Users, dict_info).first()
        if user:
            if check_password_hash(user.Password, password):
                flash('logged in successfully!', category='success')
                login_user(user, remember=True)
                
                return redirect(url_for('views.home'))
            else:
                flash('wrong password!', category='error')
        else:
            flash('User dont exist!', category='error')
    
    return render_template('login.html', user=current_user)

@auth.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('auth.login'))

@auth.route('/sign-up', methods=['GET', 'POST'])
def sign_up():
    if request.method == 'POST':
        Username = request.form.get('username')
        password = request.form.get('password')
        password_check = request.form.get('password_check')
        dict_info={'Name': Username}
        if Get_ExactTable(Users, dict_info).first():
            flash('User already exists!', category='error')
        elif password != password_check:
            flash('Passwords don`t match.', category='error')
        else:
            dict_info.update({'Password': generate_password_hash(password_check, method='pbkdf2:sha256')})
            add_data(Users, None, [dict_info])
            flash('Account created!', category='success') 
            login_user(Get_ExactTable(Users, dict_info).one(), remember=True)

            return redirect(url_for('views.home'))
    return render_template('sign_up.html', user=current_user)