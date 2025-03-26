from flask import Flask
import json, threading
from dotenv import load_dotenv
import os
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

    load_config()

    # print ("Après chargement")
    # for account in accounts.values():
    #     print(str(account))
    
    app = Flask(__name__)

    # Enregistrer les routes
    app.register_blueprint(web_bp)
    app.register_blueprint(api_bp, url_prefix='/api')

    load_dotenv()  # Charge les variables d'environnement depuis .env
    app.secret_key = os.getenv("FLASK_SECRET_KEY")


    
    # Lancer la sauvegarde automatique en arrière-plan
    threading.Thread(target=save_periodically, daemon=True).start()
    
    app.run(host='0.0.0.0', port=5000, debug=True)

