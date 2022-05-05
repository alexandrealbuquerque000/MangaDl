from flask import Blueprint, redirect, render_template, url_for, request
from flask_login import login_required, current_user

views = Blueprint('views', __name__)

@views.route('/', methods=['GET', 'POST'])
@login_required
def home():
    if request.method == 'POST':
        
        return redirect(url_for('auth.search'))
    
    return render_template("home.html", user=current_user)

