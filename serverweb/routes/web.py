from flask import Blueprint, render_template, request, redirect, url_for, session
from services.config_utils import*
from routes.api import login_required

# Suppose que nous avons un fichier de configuration où les identifiants sont stockés
# Par exemple : config.conf

# Définition du Blueprint
web_bp = Blueprint('web', __name__)




@web_bp.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        # Récupérer les informations du formulaire
        username = request.form['username']
        password = request.form['password']
        
        # Vérification des identifiants (ici tu peux les valider contre un fichier JSON, base de données, etc.)
        stored_username = get_config_value('username')
        stored_password = get_config_value('password')
        
        if username == stored_username and password == stored_password:
            session['authenticated'] = True  # Enregistrer dans la session que l'utilisateur est authentifié
            return redirect(url_for('web.overview'))  # Rediriger vers la page d'accueil (overview)
        else:
            return render_template('login.html', error="Identifiants incorrects.")
    
    return render_template('login.html')

@web_bp.route('/logout')
def logout():
        session.clear()  # Supprime la session
        return redirect(url_for('web.login'))  # Rediriger vers la page d'accueil (overview)
      

@web_bp.route('/overview')
@login_required  # 🔒 Protège cette route
def overview():
    return render_template('overview.html')

@web_bp.route('/')
@login_required  # 🔒 Protège cette route
def home():
    return redirect(url_for('web.overview')) 


@web_bp.route('/networks')
@login_required  # 🔒 Protège cette route
def networks():
    return render_template('networks.html')

@web_bp.route('/modbus')
@login_required  # 🔒 Protège cette route
def modbus():
    return render_template('modbus.html')

@web_bp.route('/netilion')
@login_required  # 🔒 Protège cette route
def netilion():
    return render_template('netilion.html')

@web_bp.route('/bindings')
@login_required  # 🔒 Protège cette route
def bindings():
    return render_template('bindings.html')

@web_bp.route('/misc')
@login_required  # 🔒 Protège cette route
def misc():
    return render_template('misc.html')
