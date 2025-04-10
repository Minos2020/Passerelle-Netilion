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

# # print(account.to_dict())
# if account.update_nodes():
#     [print(node.to_dict()) for node in account.nodes]

# # print(account.to_dict())
# if account.update_assets():
#     [print(asset.to_dict()) for asset in account.assets]
    
# if account.update_instrum():
#     [print(instrum.to_dict()) for instrum in account.instrumentations]
    
if account.update_quotas():
    print(account.api_call_quota)
    print(account.api_calls_used)