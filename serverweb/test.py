import psutil
import socket
import subprocess
from dotenv import load_dotenv
from model import PasserelleNetilion, NetilionAccount

from services.config_utils import load_config

# Tester la fonction
import os
os.chdir(os.path.dirname(os.path.abspath(__file__)))  # Change le répertoire de travail au dossier du script
from dotenv import load_dotenv
load_dotenv()  # Charge les variables d'environnement depuis .env

load_config(False)

account: NetilionAccount = PasserelleNetilion().getAccountByID(1)

if account.fetch_nodes():
    print(account.nodes)
