import os, sys
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
former_mode = None

# pour indexer les timers actifs en fonction de l'ID du compte associé
# la clé 0 correspond au timer de lecture des registres
active_timers: dict[str, Timer] = {}

def get_active_timers():
    print()
    for key, timer in list(active_timers.items()):
        status = "alive"  if timer.is_alive() else "dead"
        if isinstance(key, int):
            print(f"{key} [{timer.interval}s] ({status})   ", end="")
        else:
            print(f"{key} [{timer.interval}s] ({status}) ", end="")
        if status == 'alive':
            active_timers.pop(key)
    print("\n")


def is_production_mode() -> bool:
    return PasserelleNetilion().mode == "production"

def set_new_timer(type: str, **kwargs):
    if type == "send_to_netilion":
        account: NetilionAccount = kwargs.get("account")
        if not account:
            # print("[DEBUG] Aucun compte fourni pour send_to_netilion, timer non lancé.")
            return
        
        account_id = account.account_id
        
        # Vérifie si un timer actif existe déjà et est vivant
        existing = active_timers.get(account_id)
        if existing and existing.is_alive():
            # print(f"[DEBUG] Timer déjà actif pour {account_id}, on ne relance pas.")
            return
        
        # Suppression de l'ancien timer s'il existe
        former_timer = active_timers.pop(account_id, None)
        if former_timer:
            former_timer.cancel()
        
        if account.netilion_rate != 0 and is_production_mode():
            account.send_data_to_netilion()

            # Remet un timer pour le prochain cycle
            timer = threading.Timer(
                account.netilion_rate * 10,
                set_new_timer,
                args=["send_to_netilion"],
                kwargs={"account": account}
            )
            timer.start()
            active_timers[account_id] = timer
            # print(f"[DEBUG] Lancement du timer pour send_to_netilion ({account_id})")
        else:
            # print(f"[DEBUG] Mode configuration ou taux nul pour {account_id} : timer send_to_netilion non lancé.")
            pass

    elif type == "read_modbus_tcp":
        passerelle = PasserelleNetilion()
        
        # Vérifie si un timer modbus est déjà actif
        existing = active_timers.get("modbus")
        if existing and existing.is_alive():
            # print("[DEBUG] Timer modbus déjà actif, on ne relance pas.")
            return
        
        # Suppression de l'ancien timer s'il existe
        former_timer = active_timers.pop("modbus", None)
        if former_timer:
            former_timer.cancel()
        
        if is_production_mode():
            readAllBindings()

            # Remet un timer pour le prochain cycle
            timer = threading.Timer(
                passerelle.modbus_rate,
                set_new_timer,
                args=["read_modbus_tcp"]
            )
            timer.start()
            active_timers["modbus"] = timer

            # print("[DEBUG] Lancement du timer pour read_modbus_tcp (modbus)")
        else:
            # print("[DEBUG] Mode configuration actif : le timer modbus ne redémarre pas.")
            pass
    
    # rajouts futurs d'autres types pour gérer d'autres tâches périodiques


def handle_mode_change(changedValues):
    global former_mode
    passerelle = PasserelleNetilion()

    current_mode = passerelle.mode
    if current_mode == former_mode and not changedValues:
        # Rien n’a changé, on ne touche à rien
        return
    last_mode = current_mode

    if is_production_mode():
        if "mode" in changedValues:
            print("Passage en mode production.")
        for account in passerelle.accounts:
            set_new_timer("send_to_netilion", account=account)
        set_new_timer("read_modbus_tcp")

    else:
        if "mode" in changedValues:
            print("Passe en mode configuration : annulation des timers en cours.")
            for key, timer in list(active_timers.items()):
                timer.cancel()
                active_timers.pop(key, None)
                print(f"[DEBUG] Annulation du timer {key}")
            print("✅ Threads annulés.")


def periodic_check():
    """
    Vérification régulière afin d'arrêter ou relancer des timers
    en fonction des éventuels changements de la configuration
    """
    while not stop_event.is_set():
        handle_mode_change([]) 
        get_active_timers()
        stop_event.wait(timeout=10)




if __name__ == '__main__':
    
    app = Flask(__name__)

    
    
    app.secret_key = os.getenv("FLASK_SECRET_KEY")
    
    load_config(False)

    # Enregistrer les routes
    app.register_blueprint(web_bp)
    app.register_blueprint(api_bp, url_prefix='/api')

    
    # Pour éviter le double lancement des threads à cause du mode debug !!
    if os.environ.get('WERKZEUG_RUN_MAIN') == 'true':
        
        stop_event = threading.Event()
        thread = threading.Thread(target=periodic_check, daemon=True)
        thread.start()


        # Permet de terminer proprement tous les timers qui ont été lancés avant de fermer le programme
        def graceful_shutdown(*args):
            print("\n⏹️  Arrêt propre en cours...")
            for timer in active_timers.values():
                timer.cancel()
            print("✅ Threads annulés. Fermeture de Flask...")
            sys.exit(0)  # Force l’arrêt sans laisser Flask traîner
        
        # Gère le Ctrl+C (SIGINT)
        signal.signal(signal.SIGINT, graceful_shutdown)
        signal.signal(signal.SIGTERM, graceful_shutdown)

    

    app.run(host='0.0.0.0', port=5000, debug=True) 


    



