import os, sys
os.chdir(os.path.dirname(os.path.abspath(__file__)))  # Change le répertoire de travail au dossier du script
from dotenv import load_dotenv
load_dotenv()  # Charge les variables d'environnement depuis .env

import signal, time
from flask import Flask
from threading import Timer
import threading
from model import PasserelleNetilion, NetilionAccount
from services.config_utils import load_config, save_config
from services.modbus_utils import readAllBindings
from routes.web import web_bp
from routes.api import api_bp
from services.logger_utils import logger


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
            print(f"{key} [{timer.interval}s] ({status})   ", end="")
        
        # logger.debug(f' id={id(timer)}')
        # if status == 'alive':
        #     active_timers.pop(key)
    print("\n")


def is_production_mode() -> bool:
    return PasserelleNetilion().mode == "production"

def set_new_timer(timer_type: str, **kwargs):
    passerelle = PasserelleNetilion()
    
    if timer_type == "send_to_netilion":
        account: NetilionAccount = kwargs.get("account")
        if not account:
            logger.debug("[Netilion] Aucun compte fourni pour send_to_netilion, timer non lancé.")
            return
        
        account_id = account.account_id
        
        # Vérifie si un timer actif existe déjà et est vivant
        existing = active_timers.get(account_id)
        if existing and not existing.is_alive():
            logger.info(f"[Netilion] Timer déjà actif pour {account_id}, on ne relance pas.")
            return
        
        # Suppression de l'ancien timer s'il existe
        former_timer = active_timers.pop(account_id, None)
        if former_timer:
            former_timer.cancel()
        
        if account.netilion_rate != 0 and is_production_mode():
            account.send_data_to_netilion()

            # Remet un timer pour le prochain cycle
            timer = threading.Timer(
                account.netilion_rate * 60,     # on change les minutes en secondes
                set_new_timer,
                args=["send_to_netilion"],
                kwargs={"account": account}
            )
            timer.start()
            active_timers[account_id] = timer
            logger.debug(f"[Netilion] Compte {account_id} - Timer lancé à {time.time()} id={id(timer)}")

            logger.info(f"[Netilion] Nouveau timer send_to_netilion Compte ({account_id})")
        else:
            logger.debug(f"[Netilion] Mode production OFF, ou taux nul pour {account_id} : timer send_to_netilion non lancé.")
            pass

    elif timer_type == "read_modbus_tcp":
        
        # Vérifie si un timer modbus est déjà actif
        existing = active_timers.get("modbus")
        if existing and not existing.is_alive():
            logger.debug("[Modbus] Timer modbus déjà actif, on ne relance pas.")
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
            logger.debug(f"[Modbus] Timer lancé à {time.time()} id={id(timer)}")

            logger.info("[Modbus] Nouveau timer modbus")
        else:
            logger.debug("[Modbus] Mode production inactif : le timer modbus ne redémarre pas.")
    
    
    elif timer_type == "daily_accounts_sync":
        
        # Vérifie si un timer sync est déjà actif
        existing = active_timers.get("daily_accounts_sync")
        if existing and not existing.is_alive():
            logger.debug("[Sync] Timer sync déjà actif, on ne relance pas.")
            return
        
        # Suppression de l'ancien timer s'il existe
        former_timer = active_timers.pop("daily_accounts_sync", None)
        if former_timer:
            former_timer.cancel()

        if is_production_mode():
            for account in passerelle.accounts:
                account.refresh_all_data()
            save_config(False)
            
            # Remet un timer pour le prochain cycle
            timer = threading.Timer(
                60*60*24,       # toutes les 24h
                set_new_timer,
                args=["daily_accounts_sync"]
            )
            timer.start()
            active_timers["daily_accounts_sync"] = timer
            logger.debug(f"[Sync] Timer lancé à {time.time()} id={id(timer)}")

            logger.info("[Sync] Nouveau timer synchronisation journalière")
        else:
            logger.debug("[Sync] Mode production inactif : le timer sync ne redémarre pas.")

    # rajouts futurs d'autres timer_type pour gérer d'autres tâches périodiques


def handle_mode_change(changedValues):
    global former_mode
    passerelle = PasserelleNetilion()

    current_mode = passerelle.mode
    if current_mode == former_mode and not changedValues:
        # Rien n’a changé, on ne touche à rien
        return
    
    former_mode = current_mode

    if is_production_mode():
        if "mode" in changedValues:
            logger.info("Passage en mode production.")
        set_new_timer("read_modbus_tcp")
        for account in passerelle.accounts:
            set_new_timer("send_to_netilion", account=account)
        
        set_new_timer("daily_accounts_sync")

    else:
        if "mode" in changedValues:
            logger.info("Passe en mode configuration : annulation des timers en cours.")
            for key, timer in list(active_timers.items()):
                timer.cancel()
                active_timers.pop(key, None)
                logger.debug(f"Annulation du timer {key}")
            logger.info("✅ Threads annulés.")


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
            logger.info("⏹️  Arrêt propre en cours...")
            logger.info("Enregistrement de la configuration...")
            save_config(False)
            for timer in active_timers.values():
                timer.cancel()
            logger.info("✅ Threads annulés. Fermeture de Flask...")
            sys.exit(0)  # Force l’arrêt sans laisser Flask traîner
        
        # Gère le Ctrl+C (SIGINT)
        signal.signal(signal.SIGINT, graceful_shutdown)
        signal.signal(signal.SIGTERM, graceful_shutdown)

    

    app.run(host='0.0.0.0', port=5000, debug=True) 


    



