from netilion_auth import*
import requests

# Chargement des comptes depuis la configuration JSON
load_accounts()

# Choisir un compte Netilion (ex: ID "1")
account_id = "1"


# for account in accounts.values():
#     print(str(account))


# Récupérer les headers authentifiés
headers = get_headers(account_id)

time.sleep(1)
print(str(accounts.get(account_id)))
time.sleep(1)

# # Faire une requête avec le bon compte
# api_url = "https://api.netilion.endress.com/v1/api_keys"
# response = requests.get(api_url, headers=headers)

# print(response.json())  # Résultat de l'API

headers2 = get_headers(account_id)

time.sleep(1)
print(str(accounts.get(account_id)))
time.sleep(1)

print(headers)
print(headers2)

