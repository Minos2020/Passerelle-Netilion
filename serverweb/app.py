import os
os.chdir(os.path.dirname(os.path.abspath(__file__)))  # Change le répertoire de travail au dossier du script
from dotenv import load_dotenv
load_dotenv()  # Charge les variables d'environnement depuis .env

from flask import Flask
import json, threading
from services.config_utils import load_config, save_periodically
from services.netilion_auth import accounts
from routes.web import web_bp
from routes.api import api_bp


if __name__ == '__main__':
    
    # # Charger la configuration au démarrage
    # print ("Avant chargement")
    # for account in accounts.values():
    #     print(type(account))
    #     print(str(account))

    

    # print ("Après chargement")
    # for account in accounts.values():
    #     print(str(account))
    
    app = Flask(__name__)

    
    
    app.secret_key = os.getenv("FLASK_SECRET_KEY")
    
    load_config()

# Enregistrer les routes
    app.register_blueprint(web_bp)
    app.register_blueprint(api_bp, url_prefix='/api')

    
    # Lancer la sauvegarde automatique en arrière-plan
    threading.Thread(target=save_periodically, daemon=True).start()
    
    app.run(host='0.0.0.0', port=5000, debug=True)

