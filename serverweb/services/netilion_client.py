from services.netilion_utils import*
import requests

class Asset:
    def __init__(self, id: int, serial_number: str, description: str, product_id: int, nodes: list[int], instrumentation: list[int]):
        self.id: int = id
        self.serial_number: str = serial_number
        self.description: str = description
        self.product_id: int = product_id
        self.nodes: list[int] = nodes
        self.instrumentation: list[int] = instrumentation

class Node:
    def __init__(self, id: int, name: str, product_code: str):
        self.id: int = id
        self.name: str = name
        self.product_code: str = product_code

class Instrumentation:
    def __init__(self, id: int, name: str, description: str, parent_id: int):
        self.id: int = id
        self.name: str = name
        self.description: str = description
        self.parent_id: int = parent_id

class Value:
    def __init__(self, id: int, name: str, description: str, parent_id: int):
        self.id: int = id
        self.name: str = name
        self.description: str = description
        self.parent_id: int = parent_id

class Binding:
    def __init__(self, identification: int, protocol: str, slaveadress: str, registeradress: str,
                 datatype: str, unit_id: int, netilion_account_id: str, netilion_binding_id: str):
        self.identification: int = identification
        self.protocol: str = protocol
        self.slaveadress: str = slaveadress
        self.registeradress: str = registeradress
        self.datatype: str = datatype
        self.unit_id: int = unit_id
        self.netilion_account_id: str = netilion_account_id
        self.netilion_binding_id: str = netilion_binding_id


if __name__ == '__main__':
    # # # Chargement des comptes depuis la configuration JSON
    # # load_accounts()

    # # Choisir un compte Netilion (ex: ID "1")
    # account_id = "1"

    # # for account in accounts.values():
    # #     print(str(account))

    # # Récupérer les headers authentifiés
    # headers = get_headers(account_id)

    # time.sleep(1)
    # print(str(accounts.get(account_id)))
    # time.sleep(1)

    # # # Faire une requête avec le bon compte
    # # api_url = "https://api.netilion.endress.com/v1/api_keys"
    # # response = requests.get(api_url, headers=headers)

    # # print(response.json())  # Résultat de l'API

    # headers2 = get_headers(account_id)

    # time.sleep(1)
    # print(str(accounts.get(account_id)))
    # time.sleep(1)

    # print(headers)
    # print(headers2)
    pass
