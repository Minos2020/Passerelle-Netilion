import os
os.chdir(os.path.dirname(os.path.abspath(__file__)))  # Change le répertoire de travail au dossier du script
from dotenv import load_dotenv
load_dotenv()  # Charge les variables d'environnement depuis .env

import signal
from flask import Flask
from threading import Timer
import threading
from model import PasserelleNetilion, NetilionAccount
from services.config_utils import load_config, save_periodically
from services.modbus_utils import readAllBindings
from routes.web import web_bp
from routes.api import api_bp

# pour suivre les changements de mode de la passerelle
former_mode = ""

# pour indexer les timers actifs en fonction de l'ID du compte associé
# la clé 0 correspond au timer de lecture des registres
active_timers: dict[str, Timer] = {}

def get_active_timers():
    
    if any (list(active_timers.items())):
        print()

        for key, timer in list(active_timers.items()):
            if isinstance(key, int):
                print(key, " [", timer.interval, "s] ", end="   ", sep="")
            else:
                print(key, " [", timer.interval, "s] ", end=" ", sep="")
        
        print("\n")

def relay_function(mode: str, **kwargs):
    if mode == "send_to_netilion":
        account = kwargs.get("account")
        if account:
            if account.netilion_rate != 0:
                account.send_data_to_netilion()
                
                # Suppression de l'ancien timer
                former_timer = active_timers.pop(account.account_id, None)
                if former_timer: former_timer.cancel()
                
                # Remet un timer pour le prochain cycle
                timer = threading.Timer(
                    account.netilion_rate*10,
                    relay_function,
                    kwargs={"mode": "send_to_netilion",
                            "account": account
                    }
                )
                timer.start()
                active_timers[account.account_id] = timer
                # set_next_data_batch(account)
    
    elif mode == "read_modbus_tcp":
        
        readAllBindings()
        passerelle = PasserelleNetilion()
        
        # Suppression de l'ancien timer
        former_timer = active_timers.pop("modbus", None)
        if former_timer: former_timer.cancel()
        
        # Remet un timer pour le prochain cycle
        timer = threading.Timer(
            passerelle.modbus_rate,
            relay_function,
            kwargs={"mode": "read_modbus_tcp"
            }
        )
        timer.start()
        active_timers["modbus"] = timer

    # rajout futur d'autre mode pour gérer d'autres tâches périodiques

def periodic_check():
    """
    Vérification régulière afin d'arrêter ou relancer des timers
    en fonction des éventuels changements de la configuration
    """
    global former_mode
    modeHasChanged = False
    passerelle = PasserelleNetilion()
    
    # [print(key, end=", ") for key in active_timers.keys()]
    # print()
    get_active_timers()

    if passerelle.mode != former_mode:
        modeHasChanged = True
    
    if (passerelle.mode == "production"):
        if modeHasChanged:
            
            print("Passage en mode production.")
        
            # Lancement d'1 timer par compte pour l'envoi régulier des données
            for account in passerelle.accounts:
                relay_function("send_to_netilion", account=account)
            
            # Timer pour le cycle de lectures des données terrain
            relay_function("read_modbus_tcp")

    else:
        # Arrêt propre des timers si jamais la passerelle est passée en mode configuration
        if modeHasChanged:
            print("Passe en mode configuration : annulation des timers en cours.")
            for key, timer in list(active_timers.items()):
                timer.cancel()
                active_timers.pop(key, None)
            print("✅ Threads annulés.")
    
    former_mode = passerelle.mode
    
    # Replanifie la vérification dans 10 secondes
    threading.Timer(10, periodic_check).start()


# Permet de terminer proprement tous les timers qui ont été lancés avant de fermer le programme
def graceful_shutdown(*args):
    print("\n⏹️  Arrêt propre en cours...")
    for timer in active_timers.values():
        timer.cancel()
    print("✅ Threads annulés. Fermeture de Flask...")
    os._exit(0)  # Force l’arrêt sans laisser Flask traîner


if __name__ == '__main__':
    
    app = Flask(__name__)

    
    
    app.secret_key = os.getenv("FLASK_SECRET_KEY")
    
    load_config(False)

    # Enregistrer les routes
    app.register_blueprint(web_bp)
    app.register_blueprint(api_bp, url_prefix='/api')

    
    # Pour éviter le double lancement des threads à cause du mode debug !!
    if os.environ.get('WERKZEUG_RUN_MAIN') == 'true':
        periodic_check()

        # Gère le Ctrl+C (SIGINT)
        signal.signal(signal.SIGINT, graceful_shutdown)
        signal.signal(signal.SIGTERM, graceful_shutdown)

    

    app.run(host='0.0.0.0', port=5000, debug=True) 


    



