from flask import Blueprint, render_template, request, redirect, url_for, session
from services.config_utils import*

# Suppose que nous avons un fichier de configuration où les identifiants sont stockés
# Par exemple : config.json

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
def overview():
    # Vérifier si l'utilisateur est authentifié
    if 'authenticated' not in session:
        return redirect(url_for('web.login'))  # Rediriger vers la page de connexion si non authentifié
    return render_template('overview.html')  # Afficher la page d'aperçu si authentifié

@web_bp.route('/')
def home():
    # Vérifier si l'utilisateur est authentifié
    if 'authenticated' not in session:
        return redirect(url_for('web.login'))  # Rediriger vers la page de connexion si non authentifié
    return redirect(url_for('web.overview'))  # Rediriger vers la page d'aperçu si authentifié


@web_bp.route('/networks')
def networks():
    if 'authenticated' not in session:
        return redirect(url_for('web.login'))
    return render_template('networks.html')

@web_bp.route('/modbus')
def modbus():
    if 'authenticated' not in session:
        return redirect(url_for('web.login'))
    return render_template('modbus.html')

@web_bp.route('/netilion')
def netilion():
    if 'authenticated' not in session:
        return redirect(url_for('web.login'))
    return render_template('netilion.html')

@web_bp.route('/bindings')
def bindings():
    if 'authenticated' not in session:
        return redirect(url_for('web.login'))
    return render_template('bindings.html')

@web_bp.route('/misc')
def misc():
    if 'authenticated' not in session:
        return redirect(url_for('web.login'))
    return render_template('misc.html')
