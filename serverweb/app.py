import os
import sys

from dotenv import load_dotenv


import signal
import time
from flask import Flask
from threading import Timer
import threading
from model import PasserelleNetilion, NetilionAccount
from services.config_utils import load_config, save_config
from services.modbus_utils import readAllBindings
from routes.web import web_bp
from routes.api import api_bp
from services.logger_utils import logger
# Change le répertoire de travail au dossier du script
os.chdir(os.path.dirname(os.path.abspath(__file__)))
load_dotenv()  # Charge les variables d'environnement depuis .env

# pour suivre les changements de mode de la passerelle
former_mode = None

# pour indexer les timers actifs en fonction de l'ID du compte associé
# la clé 0 correspond au timer de lecture des registres
active_timers: dict[str, Timer] = {}


def get_active_timers():
    print()
    for key, timer in list(active_timers.items()):
        status = "alive" if timer.is_alive() else "dead"
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
            logger.debug(
                f"[Netilion] Compte {account_id} - Aucun compte fourni pour send_to_netilion, timer non lancé.")
            return

        account_id = account.account_id

        # Vérifie si un timer actif existe déjà et est vivant
        existing = active_timers.get(account_id)
        if existing and not existing.is_alive():
            logger.info(
                f"[Netilion] Compte {account_id} - Timer déjà actif, on ne relance pas.")
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
            logger.debug(
                f"[Netilion] Compte {account_id} - Timer lancé à {time.time()} id={id(timer)}")

            logger.debug(
                f"[Netilion] Compte {account_id} - Nouveau timer send_to_netilion ({timer.interval}s)")
        else:
            logger.debug(
                f"[Netilion] Compte {account_id} - Mode production OFF, ou taux nul : timer send_to_netilion non lancé.")
            pass

    elif timer_type == "read_modbus_tcp":

        # Vérifie si un timer modbus est déjà actif
        existing = active_timers.get("modbus")
        if existing and not existing.is_alive():
            logger.debug(
                "[Modbus] Timer modbus déjà actif, on ne relance pas.")
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
            logger.debug(
                f"[Modbus] Timer lancé à {time.time()} id={id(timer)}")

            logger.debug(f"[Modbus] Nouveau timer modbus ({timer.interval}s)")
        else:
            logger.debug(
                "[Modbus] Mode production inactif : le timer modbus ne redémarre pas.")

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

            logger.debug(
                f"[Sync] Nouveau timer synchronisation journalière  ({timer.interval}s)")
        else:
            logger.debug(
                "[Sync] Mode production inactif : le timer sync ne redémarre pas.")

    # rajouts futurs d'autres timer_type pour gérer d'autres tâches périodiques


def handle_mode_change(changedValues):
    passerelle = PasserelleNetilion()

    if (changedValues):

        for value in changedValues:
            # si int, c'est que c'est l'id d'un compte dont la rate a changé
            if isinstance(value, int):
                account = passerelle.getAccountByID(value)
                set_new_timer("send_to_netilion", account=account)

            # sinon c'est que c'est un valeur globale (mode ou modbus_rate)
            else:
                if value == "mode":
                    if is_production_mode():
                        logger.info("Passage en mode production.")
                        set_new_timer("read_modbus_tcp")
                        for account in passerelle.accounts:
                            set_new_timer("send_to_netilion", account=account)

                        set_new_timer("daily_accounts_sync")

                    else:
                        logger.info(
                            "Passe en mode configuration : annulation des timers en cours.")
                        for key, timer in list(active_timers.items()):
                            timer.cancel()
                            active_timers.pop(key, None)
                            logger.debug(f"Annulation du timer {key}")
                        logger.info("✅ Threads annulés.")

                if value == "modbus_rate":
                    set_new_timer("read_modbus_tcp")


def periodic_check():
    """
    Vérification régulière afin d'arrêter ou relancer des timers
    en fonction des éventuels changements de la configuration
    """
    handle_mode_change(["mode"])

    while not stop_event.is_set():
        handle_mode_change([])
        get_active_timers()
        stop_event.wait(timeout=10)


app = Flask(__name__)
app.secret_key = os.getenv("FLASK_SECRET_KEY")

# Chargement de la configuration au démarrage
load_config(False)

# Enregistrement des routes
app.register_blueprint(web_bp)
app.register_blueprint(api_bp, url_prefix='/api')

# Initialisation des threads et signal handler uniquement dans le processus principal


def start_background_tasks():
    global stop_event
    stop_event = threading.Event()
    thread = threading.Thread(target=periodic_check, daemon=True)
    thread.start()
    logger.critical("  -- DEMARRAGE DE LA PASSERELLE --  ")

    def graceful_shutdown(*args):
        print("⏹️  Arrêt propre en cours...")
        print("Enregistrement de la configuration...")
        save_config(False)
        for timer in active_timers.values():
            timer.cancel()
        print("✅ Threads annulés. Fermeture de Flask...")
        logger.critical("  -- ARRET DE LA PASSERELLE --  ")
        sys.exit(0)

    signal.signal(signal.SIGINT, graceful_shutdown)
    signal.signal(signal.SIGTERM, graceful_shutdown)

# ✅ Gunicorn : il suffit d'importer `app` depuis ce fichier
# Gunicorn exécutera le code ci-dessus, mais pas le bloc `if __name__ == '__main__'`


# ✅ Flask debug : on utilise ce bloc pour développement
if __name__ == '__main__':
    if os.environ.get('WERKZEUG_RUN_MAIN') == 'true':
        start_background_tasks()

    # 🚀 Lancer Flask en mode debug pour développement
    app.run(host='0.0.0.0', port=5000, debug=True)

else:
    # Si importé par un serveur WSGI (Waitress ou Gunicorn), on démarre aussi les tâches
    start_background_tasks()
