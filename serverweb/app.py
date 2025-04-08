import os
os.chdir(os.path.dirname(os.path.abspath(__file__)))  # Change le répertoire de travail au dossier du script
from dotenv import load_dotenv
load_dotenv()  # Charge les variables d'environnement depuis .env

from flask import Flask
import json, threading
from services.config_utils import load_config, save_periodically
from routes.web import web_bp
from routes.api import api_bp


if __name__ == '__main__':
    
    app = Flask(__name__)

    
    
    app.secret_key = os.getenv("FLASK_SECRET_KEY")
    
    load_config(False)

    # Enregistrer les routes
    app.register_blueprint(web_bp)
    app.register_blueprint(api_bp, url_prefix='/api')

    # for account in get_accounts().values():
    #     print(str(account))

    # account = NetilionAccount(123,"c8b322d582afd6abf3b1cf8ddf5daf20", "e325642efe0fb9c8292c7e30b94388006e4f4681521fb8cc493f79dcd7790526", "testapi268510@connect", "/2b0/O4SY/Ml9/gUBLzlHUNyq6jUoRg=")

    # response = account.send_request("GET", "assets/1998863/values?include=unit")
    # print(response)
    
    # Lancer la sauvegarde automatique en arrière-plan
    threading.Thread(target=save_periodically, daemon=True).start()
    
    app.run(host='0.0.0.0', port=5000, debug=True)


    



