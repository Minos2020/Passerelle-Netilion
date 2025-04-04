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
    
    def to_dict(self):
        return {
            "id": self.id,
            "serial_number": self.serial_number,
            "description": self.description,
            "product_id": self.product_id,
            "nodes": self.nodes,
            "instrumentation": self.instrumentation
        }

    @classmethod
    def from_dict(cls, data):
        return cls(
            id=data["id"],
            serial_number=data["serial_number"],
            description=data["description"],
            product_id=data["product_id"],
            nodes=data["nodes"],
            instrumentation=data["instrumentation"]
        )
    
class Node:
    def __init__(self, id: int, name: str, product_code: str):
        self.id: int = id
        self.name: str = name
        self.product_code: str = product_code
    
    def to_dict(self):
        return {
            "id": self.id,
            "name": self.name,
            "product_code": self.product_code
        }

    @classmethod
    def from_dict(cls, data):
        return cls(
            id=data["id"],
            name=data["name"],
            product_code=data["product_code"]
        )

class Instrumentation:
    def __init__(self, id: int, name: str, description: str, parent_id: int):
        self.id: int = id
        self.name: str = name
        self.description: str = description
        self.parent_id: int = parent_id

    def to_dict(self):
        return {
            "id": self.id,
            "name": self.name,
            "description": self.description,
            "parent_id": self.parent_id
        }

    @classmethod
    def from_dict(cls, data):
        return cls(
            id=data["id"],
            name=data["name"],
            description=data["description"],
            parent_id=data["parent_id"]
        )

class Value:
    def __init__(self, id: int, name: str, description: str, parent_id: int):
        self.id: int = id
        self.name: str = name
        self.description: str = description
        self.parent_id: int = parent_id

    def to_dict(self):
        return {
            "id": self.id,
            "name": self.name,
            "description": self.description,
            "parent_id": self.parent_id
        }

    @classmethod
    def from_dict(cls, data):
        return cls(
            id=data["id"],
            name=data["name"],
            description=data["description"],
            parent_id=data["parent_id"]
        )

class Binding:
    def __init__(self, identification: str, protocol: str, slaveadress: str, registeradress: str,
                 datatype: str, unit_id: int, netilion_account_id: int, netilion_binding_id: int):
        self.identification: str = identification
        self.protocol: str = protocol
        self.slaveadress: str = slaveadress
        self.registeradress: str = registeradress
        self.datatype: str = datatype
        self.unit_id: int = unit_id
        self.netilion_account_id: int = netilion_account_id
        self.netilion_binding_id: int = netilion_binding_id

    def to_dict(self):
        """Convertit l'objet en dictionnaire pour la sérialisation JSON."""
        return {
            "identification": self.identification,
            "protocol": self.protocol,
            "slaveadress": self.slaveadress,
            "registeradress": self.registeradress,
            "datatype": self.datatype,
            "unit_id": self.unit_id,
            "netilion_account_id": self.netilion_account_id,
            "netilion_binding_id": self.netilion_binding_id
        }

    @classmethod
    def from_dict(cls, data):
        """Crée une instance de Binding à partir d'un dictionnaire."""
        return cls(
            identification=data["identification"],
            protocol=data["protocol"],
            slaveadress=data["slaveadress"],
            registeradress=data["registeradress"],
            datatype=data["datatype"],
            unit_id=data["unit_id"],
            netilion_account_id=data["netilion_account_id"],
            netilion_binding_id=data["netilion_binding_id"]
        )


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
