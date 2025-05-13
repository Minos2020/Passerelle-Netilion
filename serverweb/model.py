from __future__ import annotations
from datetime import datetime
import time, requests
from services.network_utils import getNetworkSettings


# from services.encryption_utils import encrypt_data_into_file
import psutil, subprocess, socket, platform, re


token_url = "https://api.netilion.endress.com/oauth/token"
BASE_URL = "https://api.netilion.endress.com/"


class PasserelleNetilion:

    _instance = None  # Singleton

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(PasserelleNetilion, cls).__new__(cls)
            cls._instance.accounts = [] # Dictionnaire {account_id: NetilionAccount}
            cls._instance.bindings = []
            cls._instance.networks = []
            cls._instance.modbus_rate = 60
            cls._instance.username = ""
            cls._instance.password = ""
            cls._instance.encryption = True
            cls._instance.mode = False
        return cls._instance
    
    def to_dict(self):
        """Convertit l'objet en dictionnaire pour la sauvegarde JSON."""
        return {
            "accounts": [acc.to_dict() for acc in self.accounts],
            "bindings": [binding.to_dict() for binding in self.bindings],
            "networks": [network.to_dict() for network in self.networks],
            "modbus_rate": self.modbus_rate,
            "encryption": self.encryption,
            "mode": self.mode,
        }
    
    def to_dict_secured(self):
        """Convertit l'objet en dictionnaire en retirant les informations sensibles."""
        return {
            "accounts": [acc.to_dict_secured() for acc in self.accounts],
            "bindings": [binding.to_dict() for binding in self.bindings],
            "networks": [network.to_dict() for network in self.networks],
            "modbus_rate": self.modbus_rate,
            "encryption": self.encryption,
            "mode": self.mode,
        }

    @classmethod
    def from_dict(cls, data):
        """Charge un objet PasserelleNetilion à partir d'un dictionnaire."""
        instance = cls()
        instance.accounts = [NetilionAccount.from_dict(b) for b in data["accounts"]]
        instance.bindings = [Binding.from_dict(b) for b in data["bindings"]]
        instance.networks = [Network.from_dict(n) for n in data["networks"]]
        instance.modbus_rate = data["modbus_rate"]
        instance.encryption = data["encryption"]
        instance.mode = data["mode"]

        return instance
    
    def get_accounts(self) -> list[NetilionAccount]:
        """Retourne le dictionnaire des comptes Netilion."""
        return self.to_dict()["accounts"]

    def set_accounts(self, new_accounts: list[NetilionAccount]):
        """Met à jour le dictionnaire des comtpes Netilion. (OVERRIDE)"""
        self.accounts = new_accounts

    def add_account(self, new_account: NetilionAccount):
        """
        Ajoute un compte Netilion à la passerelle en lui attribuant un `account_id` unique.
        """
        # Récupère tous les IDs déjà utilisés
        used_ids = {account.account_id for account in self.accounts if account.account_id is not None}

        # Trouve le plus petit entier non utilisé (commençant à 1)
        new_id = 1
        while new_id in used_ids:
            new_id += 1

        new_account.account_id = new_id  # Attribue l'ID
        self.accounts.append(new_account)

    def getAccountByID(self, account_id: int) -> NetilionAccount:
        """Retourne l'objet NetilionAccount correspondant à l'ID donné, ou None si introuvable."""
        return next((account for account in self.accounts if account.account_id == account_id), None)

class Network:
    def __init__(self, ipadress: str, subnetmask: str, gateway: str, description: str = None, internet_access: str = None):
        self.ipadress: str = ipadress
        self.subnetmask: str = subnetmask
        self.gateway: str = gateway
        self.description: str = description

    def to_dict(self):
        return {
            "ipadress": self.ipadress,
            "subnetmask": self.subnetmask,
            "gateway": self.gateway,
            "description": self.description
        }

    @classmethod
    def from_dict(cls, data):
        return cls(
            ipadress=data["ipadress"],
            subnetmask=data["subnetmask"],
            gateway=data["gateway"],
            description=data["description"],
            internet_access=data.get("internet_access", None)
        )

class NetilionAccount:
    def __init__(self, identification: str, email:str, client_id: str, client_secret: str, username: str, password: str, account_id: int=None, changes_to_save=None):
        self.identification: str = identification
        self.email: str = email
        self.account_id: int = account_id
        self.client_id: str = client_id
        self.client_secret: str = client_secret
        self.username: str = username
        self.password: str = password
        self.access_token: str = None
        self.refresh_token: str = None
        self.token_expiry: int = 0  # Timestamp d'expiration du token d'accès
        self.refresh_token_expiry: int = 0 # Timestamp d'expiration du refresh_token
        self.last_connection: datetime = None  # Date/heure de la dernière connexion
        self.assets = []
        self.nodes = []
        self.instrumentations = []
        self.changes_to_save = changes_to_save
        self.storage_quota: int = None
        self.storage_used: int = None
        self.api_call_quota: int = None
        self.api_calls_used: int = None


    def to_dict(self):
        """Convertit l'objet en dictionnaire pour la sérialisation"""
        return {
            "identification": self.identification,
            "email": self.email,
            "account_id": self.account_id,
            "client_id": self.client_id,
            "client_secret": self.client_secret,
            "username": self.username,
            "password": self.password,
            "access_token": self.access_token,
            "refresh_token": self.refresh_token,
            "token_expiry": self.token_expiry,
            "refresh_token_expiry": self.refresh_token_expiry,
            "last_connection": self.last_connection.isoformat() if self.last_connection else None,  # Conversion ISO 8601
            "assets": [asset.to_dict() for asset in self.assets],  # Sérialisation des assets
            "nodes": [node.to_dict() for node in self.nodes],  # Sérialisation des nodes
            "instrumentations": [inst.to_dict() for inst in self.instrumentations],  # Sérialisation des instrumentations
            "storage_quota": self.storage_quota,
            "storage_used": self.storage_used,
            "api_call_quota": self.api_call_quota,
            "api_calls_used": self.api_calls_used
        }
    
    def to_dict_secured(self):
        """Convertit l'objet en dictionnaire pour la sérialisation
        Certaines données sensibles sont omises pour garantir leur
        sécurité"""
        return {
            "identification": self.identification,
            "email": self.email,
            "account_id": self.account_id,
            "client_id": self.client_id,
            # "client_secret": self.client_secret,
            "username": self.username,
            # "password": self.password,
            # "access_token": self.access_token,
            # "refresh_token": self.refresh_token,
            # "token_expiry": self.token_expiry,
            # "refresh_token_expiry": self.refresh_token_expiry,
            "last_connection": self.last_connection.isoformat() if self.last_connection else None,  # Conversion ISO 8601
            "assets": [asset.to_dict() for asset in self.assets],  # Sérialisation des assets
            "nodes": [node.to_dict() for node in self.nodes],  # Sérialisation des nodes
            "instrumentations": [inst.to_dict() for inst in self.instrumentations],  # Sérialisation des instrumentations
            "storage_quota": self.storage_quota,
            "storage_used": self.storage_used,
            "api_call_quota": self.api_call_quota,
            "api_calls_used": self.api_calls_used
        }

    @classmethod
    def from_dict(cls, data):
        """Crée une instance NetilionAuth à partir d'un dictionnaire"""
        instance = cls(
            data["identification"], data["email"], data["client_id"], data["client_secret"], data["username"], data["password"], data["account_id"]
        )
        instance.access_token = data.get("access_token", None)
        instance.refresh_token = data.get("refresh_token", None)
        instance.token_expiry = data.get("token_expiry", 0)
        instance.refresh_token_expiry = data.get("refresh_token_expiry", 0)

        instance.storage_quota = data.get("storage_quota", 0)
        instance.storage_used = data.get("storage_used", 0)
        instance.api_call_quota = data.get("api_call_quota", 0)
        instance.api_calls_used = data.get("api_calls_used", 0)

        # Désérialisation de la date de dernière connexion
        instance.last_connection = datetime.fromisoformat(data.get("last_connection")) if data.get("last_connection") else None

         # Désérialisation des assets, nodes et instrumentations
        instance.assets = [Asset(**asset) for asset in data.get("assets", [])]
        instance.nodes = [Node(**node) for node in data.get("nodes", [])]
        instance.instrumentations = [Instrumentation(**inst) for inst in data.get("instrumentations", [])]
        
        return instance
    
    def update_last_connection(self):
        """Met à jour la date et l'heure de la dernière connexion."""
        self.last_connection = datetime.now()

    def get_last_connection(self) -> str:
        """Retourne la dernière connexion sous forme lisible."""
        return self.last_connection.strftime("%Y-%m-%d %H:%M:%S") if self.last_connection else "Jamais connecté"


    def _request_token(self, grant_type, extra_data=None) -> None:
        """
        Demande un token d'accès OAuth2 (soit initial, soit via refresh).
        """
        print(f"...requesting access token with ({grant_type})...")
        token_data = {
            "grant_type": grant_type,
            "client_id": self.client_id,
            "client_secret": self.client_secret,
        }
        
        if extra_data:
            token_data.update(extra_data)

        response = requests.post(token_url, data=token_data)
        response_data = response.json()

        if response.ok:  # Vérifie si la requête a réussi (statut HTTP 2xx)
            self.update_last_connection()
        
        # print(self.get_last_connection())
        
        if response.status_code == 200:
            print(
                "Access granted with password" if grant_type == "password"
                else "Access granted with refresh token"
            )
            self.access_token = response_data['access_token']
            self.refresh_token = response_data.get('refresh_token', self.refresh_token)
            self.token_expiry = time.time() + response_data.get("expires_in") - 10
            self.refresh_token_expiry = time.time() + 24 * 60 * 60  # 24h
            self.update_last_connection()
            if self.changes_to_save:
                print("Sauvegarde des nouveaux token...")
                self.changes_to_save()
                print([self.access_token, self.refresh_token, self.token_expiry])
        else:
            raise Exception(f"Failed to obtain access token: {response_data}")
        return response


    # def authenticate(self):
    #     """
    #     Authentifie l'utilisateur et stocke le token.
    #     """
    #     response = self._request_token("password", {
    #         "username": self.username,
    #         "password": self.password
    #     })
    #     return response

    def refresh_token_if_needed(self):
        """
        Rafraîchit le token si nécessaire avant un appel API.
        """
        current_time = time.time()
        
        # Si seul le token d'accès est expiré, on rafraîchit le token avec le refresh_token
        if (current_time >= self.token_expiry and current_time < self.refresh_token_expiry):
            print("🔄 Token d'accès expiré ou absent, rafraîchissement en cours...")
            self._request_token("refresh_token", {"refresh_token": self.refresh_token})
        # Sinon, (les 2 tokens sont expirés) on réauthentifie avec les identifiants
        elif current_time >= self.refresh_token_expiry:
            print("🔄 Token d'accès et de refresh expirés ou absents, demande de nouveaux token...")
            self._request_token("password", {
                "username": self.username,
                "password": self.password
            })
        else:
            # print("Token d'accès toujours valide ✅")
            pass
        return

    def get_headersForAuth(self):
        """
        Retourne les headers avec le token à jour.
        """
        self.refresh_token_if_needed()
        return {"Authorization": f"Bearer {self.access_token}"}
    

    def get_node_by_id(self, node_id: int) -> Node | None:
        """Recherche un Node par son ID dans cet account"""
        return next((node for node in self.nodes if node.id == node_id), None)
    
    def get_asset_by_id(self, asset_id: int) -> Asset | None:
        """Recherche un Node par son ID dans cet account"""
        return next((asset for asset in self.assets if asset.id == asset_id), None)
    
    def get_instrumentation_by_id(self, instrumentation_id: int) -> Instrumentation | None:
        """Recherche un Node par son ID dans cet account"""
        return next((instrumentation for instrumentation in self.instrumentations if instrumentation.id == instrumentation_id), None)


    def send_request(self, method, endpoint, data=None, params=None, api_version="v1"):
        """Envoie une requête HTTP à Netilion avec gestion automatique du token."""
        
        # Obtenir les headers avec le token d'authentification
        headers = self.get_headersForAuth()  # Appel de la méthode pour récupérer les headers
        # Ajouter l'en-tête Content-Type
        headers["Content-Type"] = "application/json"
        # print(headers)

        url = f"{BASE_URL}/{api_version}/{endpoint}"
        # print(url)

        response = requests.request(method, url, json=data, params=params, headers=headers)

        if response.status_code == 401:  # Token expiré
            self.refresh_token_if_needed()
            headers["Authorization"] = f"Bearer {self.access_token}"
            headers['accept'] = "application/json"
            response = requests.request(method, url, json=data, params=params, headers=headers)

        
        if not response.ok:  # Si la requête renvoie autre chose que le statut HTTP 2xx
            data = {
                "errorType": "HTTPError",
                "endpoint": endpoint,
                "status_code": response.status_code,
                "message": response.text
            }
            # print(f"HTTPError: endpoint : {endpoint}\nCode : {response.status_code}\n{response.text}")
            # raise Exception(f"HTTPError: {response.status_code} | {response.text}")
            print(data)
            raise Exception(data)

        self.update_last_connection()
        # print(self.get_last_connection())
        return response
        
    def update_nodes(self):
        """Récupère les nodes associés au compte Netilion et les ajoute à l'instance de NetilionAccount."""
        # Endpoint pour récupérer les nodes
        endpoint = "nodes?include=parent.id"
        
        # Utiliser la méthode send_request pour envoyer la requête
        response = self.send_request("GET", endpoint)
        
        if response.status_code == 200:
            data = response.json()
            # pagination = data.get("pagination")
            # if pagination:
            #     print(pagination.get("total_count"))

            fetched_nodes = []
            # Ajouter chaque nœud dans la liste des nodes du compte
            for node_data in data.get('nodes', []):
                node = Node(
                    id=node_data['id'],
                    name=node_data['name'],
                    description=node_data.get('description'),
                    parent_id=node_data.get('parent', {}).get('id', None)  # parent_id est optionnel
                )
                fetched_nodes.append(node)
            self.nodes = fetched_nodes
            if self.changes_to_save:
                # print("Sauvegarde des nouveaux nodes...")
                self.changes_to_save()
            return True
        else:
            print(f"Erreur lors de la récupération des nodes: {response.status_code}")
            raise Exception(f"Erreur lors de la récupération des nodes: {response.status_code}")
        
    def update_assets(self):
        """Récupère les assets associés au compte Netilion et les ajoute à l'instance de NetilionAccount."""
        # Endpoint pour récupérer les nodes
        endpoint = "assets?include=instrumentations%2C%20nodes%2C%20product"
        
        # Utiliser la méthode send_request pour envoyer la requête
        response = self.send_request("GET", endpoint)
        
        if response.status_code == 200:
            data = response.json()
            # pagination = data.get("pagination")
            # if pagination:
            #     print(pagination.get("total_count"))

            fetched_assets = []
            # Ajouter chaque asset dans la liste des assets du compte
            for asset_data in data.get('assets', []):
                asset = Asset(
                    id=asset_data["id"],
                    serial_number=asset_data["serial_number"],
                    description=asset_data.get('description'),
                    product_name=asset_data.get('product').get('name'),
                    parent_id=asset_data.get('parent', {}).get('id', None)
                )
                # Ajouter à chaque asset la liste de ses tags et de ses nodes
                for instrum in asset_data.get('instrumentations', {}).get('items', []):
                    asset.instrumentations.add(instrum["id"])
                for node in asset_data.get('nodes', {}).get('items', []):
                    asset.nodes.add(node["id"])
                fetched_assets.append(asset)
            self.assets = fetched_assets
            if self.changes_to_save:
                # print("Sauvegarde des nouveaux assets...")
                self.changes_to_save()
            return True
        else:
            print(f"Erreur lors de la récupération des assets: {response.status_code}")
            raise Exception(f"Erreur lors de la récupération des assets: {response.status_code}")
    
    def update_instrum(self):
        """Récupère les tags associés au compte Netilion et les ajoute à l'instance de NetilionAccount."""
        # Endpoint pour récupérer les tags
        endpoint = "instrumentations?include=parent%2C%20assets%2C%20nodes"
        
        # Utiliser la méthode send_request pour envoyer la requête
        response = self.send_request("GET", endpoint)
        
        if response.status_code == 200:
            data = response.json()
            # pagination = data.get("pagination")
            # if pagination:
            #     print(pagination.get("total_count"))
            fetched_instrum = []
            # Ajouter chaque nœud dans la liste des nodes du compte
            for instrum_data in data.get('instrumentations', []):
                instrum = Instrumentation(
                    id=instrum_data["id"],
                    tag=instrum_data["tag"],
                    description=instrum_data.get('description'),
                    parent_id=instrum_data.get('parent', {}).get('id', None)
                )
                # Ajouter à chaque tag la liste de ses assets et de ses nodes

                for asset in instrum_data.get('assets', {}).get('items', []):
                    instrum.assets.add(asset["id"])
                for node in instrum_data.get('nodes', {}).get('items', []):
                    instrum.nodes.add(node["id"])
                fetched_instrum.append(instrum)
            self.instrumentations = fetched_instrum
            if self.changes_to_save:
                # print("Sauvegarde des nouveaux tags...")
                self.changes_to_save()
            return True
        else:
            print(f"Erreur lors de la récupération des tags: {response.status_code}")
            raise Exception(f"Erreur lors de la récupération des tags: {response.status_code}")

    def update_quotas(self):
        """Récupère les quotas et limites associées au compte Netilion et les ajoute à l'instance NetilionAccount concernée."""
       
        endpoint1 = "api_subscriptions"
        endpoint2 = "subscriptions" # à rajouter plus tard
        
        # Utiliser la méthode send_request pour envoyer la requête
        response1 = self.send_request("GET", endpoint1)
        # response2 = self.send_request("GET", endpoint2)
        
        if response1.status_code == 200:
            # Normalement, ne retourne qu'une seule souscription API
            subscription = response1.json().get("api_subscriptions")[0]
            
            # pagination = data.get("pagination")
            # if pagination:
            #     print(pagination.get("total_count"))

            # Récupérer les limites et les quotas de la subcription API
            self.api_call_quota = subscription.get("api_call_quota")
            self.api_calls_used = subscription.get("api_calls_used")
            
            
            # # Récupérer les limites et les quotas de la subcription API
            self.storage_quota = subscription.get("storage_quota")
            self.storage_used = subscription.get("storage_used")
            

            
            if self.changes_to_save:
                # print("Sauvegarde des quotas mis à jour...")
                self.changes_to_save()
            return True
        else:
            print(f"Erreur lors de la récupération des quotas: {response1.status_code}")
            raise Exception(f"Erreur lors de la récupération des quotas: {response1.status_code}")
    
    def refresh_all_data(self):
        self.update_nodes()
        self.update_assets()
        self.update_instrum()
        self.update_quotas()
        
    def createNewAsset(self, data):
        print(data)

        endress_product = data['endress_product']
        serial_number = data['serial_number']
        description = data['description']
        product_code = data.get('product_code', None)
        product_name = data.get('product_name', None)
        parent_id = data.get('parent_id', None)
        
        product_id = None
        
        createdAssetID = None
        data = {}

        # Recherche par serial number si produit Endress
        if endress_product:
            endpoint = "endress/product_lookup?serial_number="+serial_number+"&include=order_code"
            response = self.send_request("GET", endpoint)

            if response.status_code == 200:
                data = response.json()
                product_id = data.get("id")

            else:
                print(f"Erreur lors de la recherche du SN: {response.status_code}")
                raise Exception(f"Erreur lors de la recherche du SN: {response.status_code}")
        else:
            # Le produit n'est pas un produit Endress. Dans ce cas, on crée un produit, avec comme tenant
            # un tenant par défaut appelé "username technical_tenant". Si ce tenant n'existe par encore on le crée
            tenant_id = self.getTechnicalTenantID()

            # Un produit doit avoir un "manufacturer" ou "company" donc on en crée une appelée "Random"
            # Si elle existe déjà, on récupère son ID
            company_id = self.getRandomCompanyID(tenant_id)

            # on peut désormais soit créer le produit selon les spécifications de l'utilisateur (product_name, product_code)
            # soit sélectionner un produit générique, qui est créé automatiquement à la création de la compagnie
            
            # Si l'utilisateur ne spécifie rien, on va chercher l'ID du produit générique de code "Unknown" et de nom "unknown product"
            if not product_code and not product_name:
                endpoint = f'companies/{company_id}/products?product_code=Unknown&name=unknown%20product&tenant_id={tenant_id}'
                response = self.send_request("GET", endpoint)
                data = response.json()
                products = data.get("products", [])
                product_id = products[0]["id"]
                print("product_id récupéré : ", product_id)

            # Si l'utilisateur a spécifié un code produit et un nom de produit, alors on crée le nouveau produit  
            else:
                data = {
                    "name" : product_name,
                    "product_code" : product_code,
                    "manufacturer" : {
                        "id" : company_id
                    },
                    "tenant" : {
                        "id" : tenant_id
                    },
                    "status" : {
                        "id" : 1
                    }
                }
                print(data)
                response = self.send_request("POST", "products", data)
                
                if response.status_code == 201:
                    data = response.json()
                    product_id = data.get("id", None)
                    print("Produit créé avec succès : ", product_id)
                else:
                    print(f"Erreur lors de la création du produit : {response.status_code}")
                    raise Exception(f"Erreur lors de la création du produit : {response.status_code}")
        
        
        # Création de l'asset
        data = {
            "description" : description,
            "serial_number" : serial_number,
            "product" : {
                "id" : product_id
            },
            "tenant": {
                "id": tenant_id
            }
        }
        response = self.send_request("POST", "assets", data)
        data = response.json()
        createdAssetID = data.get("id")
        
        if response.status_code == 201:
            if (parent_id):
                endpoint = f'assets/{createdAssetID}/nodes'
                data = {
                    "nodes": [
                        {
                            "id": parent_id
                        }
                    ]
                }
                response = self.send_request("POST", endpoint, data)
                if response.status_code == 204:
                    print("Asset ajouté au noeud.")
                else:
                    print(f"Erreur lors de l'ajout de l'asset au node : {response.status_code}")
                    raise Exception(f"Erreur lors de l'ajout de l'asset au node : {response.status_code}")
            
            # Mise à jour des assets du compte
            self.update_assets()
            
            
            # partage de la propriété du nouvel asset avec le véritable User Netilion (pas le technical user)
            # Cela permet à l'objet d'apparaître dans l'interface Netilion de l'utilisateur
            # # on commence par récupérer l'ID de l'utilisateur réel
            # user_id = None
            # endpoint = f'users/lookup?email={self.email}'
            # response = self.send_request("GET", endpoint)
            # data = response.json()
            # user_id = data.get("id", None)
            
            # if not (response.status_code == 200 and user_id):
            #     print(f"Erreur lors de la récupération de l'id de l'utilisateur: {response.status_code, data}")
            #     raise Exception(f"Erreur lors de la récupération de l'id de l'utilisateur: {response.status_code, data}")
            
            endpoint = 'permissions'
            data = {
                "permission_types": [
                    "can_read",
                    "can_update",
                    "can_delete",
                    "can_permit"
                ],
                "assignable": {
                    "email": self.email,
                    "type": "User"
                },
                "permitable": {
                    "id": createdAssetID,
                    "type": "Asset"
                }
            }
            # On spécifie la version de l'API car l'endpoint utilisé ici appartient à la V2
            response = self.send_request("POST", endpoint, data, api_version="v2")
            data = response.json()
            if not response.status_code == 201:
                print(f"Erreur lors du partage de la propriété de l'asset créé : {response.status_code, data}")
                raise Exception(f"Erreur lors du partage de la propriété de l'asset créé : {response.status_code, data}")

            return createdAssetID
        else:
            raise Exception(f"Erreur lors de la création de l'assset : {response.status_code, data}")

    def getTechnicalTenantID(self) -> int:
        # récupération de l'ID du technical tenant, ou création s'il n'existe pas encore
        tenant_name = f'{self.username.split("@")[0]} Technical tenant'
        endpoint = f'tenants?name={tenant_name}&public=false'
        response = self.send_request("GET", endpoint)
        
        data = response.json()
        print(data)
        tenants = data.get("tenants", [])
        if tenants:
            # le technical tenant existe déjà, on récupère simplement son id
            tenant_id = tenants[0]["id"]
            print("tenant_id récupéré : ", tenant_id)
            return tenant_id
        
        else:
            # on crée le tenant "technical tenant" car il n'existe pas encore
            print("Création du tenant technical tenant")  
            data = {
                "name": tenant_name,
                "description": f'Tenant créé automatiquement par le technical user {self.username} pour le bon fonctionnement de la passerelle Netilion.'
            }
            response = self.send_request("POST", "tenants", data)
            print(response.json())
            if response.status_code == 201:
                data = response.json()
                tenant_id = data.get("id", None)
                print("tenant_id créé : ", tenant_id)

                # On partage le tenant avec le véritable User Netilion (pas le technical user)
                # ce qui permet à l'utilisateur réel d'avoir accès aux collections de ce tenant dans l'interface Netilion
                
                # on commence par récupérer l'id de l'utilisateur à qui on doit partager la ressource
                user_id = None
                endpoint = f'users/lookup?email={self.email}'
                response = self.send_request("GET", endpoint)
                data = response.json()
                user_id = data.get("id", None)
                print(f'user_id for {self.email} : {user_id}')
                if response.status_code == 200 and user_id:
                    # on promeut le user en tant qu'admin du tenant
                    endpoint = f'tenants/{tenant_id}/admins'
                    data = {
                        "admins": [
                            {
                                "id": user_id
                            }
                        ]
                    }
                    response = self.send_request("POST", endpoint, data)
                    if not response.status_code == 204:
                        data = response.json()
                        print(f"Erreur lors de l'ajout de l'utilisateur comme admin du tenant: {response.status_code, data}")
                        raise Exception(f"Erreur lors de l'ajout de l'utilisateur comme admin du tenant: {response.status_code, data}")
                    
                    return tenant_id
                
                else:
                    print(f"Erreur lors de la récupération de l'id de l'utilisateur: {response.status_code, data}")
                    raise Exception(f"Erreur lors de la récupération de l'id de l'utilisateur: {response.status_code, data}")

            else:
                print(f"Erreur lors de la création du technical tenant: {response.status_code, data}")
                raise Exception(f"Erreur lors de la création du technical tenant: {response.status_code, data}")

    def getRandomCompanyID(self, tenant_id) -> int:
        endpoint = f'companies?name=Random&tenant_id={tenant_id}'
        response = self.send_request("GET", endpoint)

        data = response.json()
        companies = data.get("companies", [])
        if companies:
            # le manufacturer / company  existe déjà, on récupère donc simplement son id
            company_id = companies[0]["id"]
            print("company_id récupéré : ", company_id)
            print(companies)
            return company_id
        
        else:
            # on crée la companie "Random" car elle n'existe pas encore
            print("Création d'une compagnie Random")  
            data = {
                "name": "Random",
                "description": f'Compagnie créée automatiquement par le technical user "{self.username}" pour le bon fonctionnement de la passerelle Netilion.',
                "tenant": {
                    "id": tenant_id
                }
            }
            response = self.send_request("POST", "companies", data)
            
            if response.status_code == 201:
                data = response.json()
                company_id = data.get("id", None)
                print("company_id créé : ", company_id)
                
                return company_id
            
            else:
                print(f"Erreur lors de la création de la compagnie: {response.status_code, data}")
                raise Exception(f"Erreur lors de la création de la compagnie: {response.status_code, data}")



    def deleteObject(self, data):
        print(data)
        object_type = data['object_type']
        object_id = data['object_id']

        # Suppression selon le type d''objet
        endpoint = f'{object_type}s/{object_id}'
        
        response = self.send_request("DELETE", endpoint)
        print(response)

        if response.status_code == 204:
            match object_type:
                case "asset":
                    for binding in PasserelleNetilion().bindings:
                        if binding.netilion_binding_id == object_id:
                            binding.netilion_binding_id = None
                            print("suppression du binding")
                    self.update_assets()
                case "instrumentation":
                    self.update_instrum()
                case "node":
                    self.update_nodes()
             
        else:
            print(f"Erreur lors de la suppression : {response.status_code}")
            raise Exception(f"Erreur lors de la suppression : {response.status_code}")
        



class Asset:
    def __init__(self, id: int, serial_number: str, description: str, nodes: set[int]=None, instrumentations: set[int]=None, product_name: int = None, parent_id: int = None):
        self.id: int = id
        self.serial_number: str = serial_number
        self.description: str = description
        self.nodes: set[int] = set(nodes) if nodes else set()
        self.instrumentations: set[int] = set(instrumentations) if instrumentations else set()
        self.product_name: int = product_name
        self.parent_id: int = parent_id
    
    def to_dict(self):
        return {
            "id": self.id,
            "serial_number": self.serial_number,
            "description": self.description,
            "product_name": self.product_name,
            "nodes": list(self.nodes),
            "instrumentations": list(self.instrumentations),
            "parent_id": self.parent_id,
        }

    @classmethod
    def from_dict(cls, data):
        return cls(
            id=data["id"],
            serial_number=data["serial_number"],
            description=data["description"],
            product_name=data.get("product_name", None),
            parent_id=data.get("parent_id", None),
            nodes=set(data.get("nodes", [])),
            instrumentation=set(data.get("instrumentation", []))
        )
    
class Node:
    def __init__(self, id: int, name: str, description: str = None, parent_id:int = None):
        self.id: int = id
        self.name: str = name
        self.description = description
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
            description=data.get("description"),
            parent_id=data.get("parent_id")
        )

class Instrumentation:
    def __init__(self, id: int, tag: str, parent_id: int, description: str = None, assets: set[int] = None, nodes: set[int] = None):
        self.id: int = id
        self.tag: str = tag
        self.description: str = description
        self.parent_id: int = parent_id
        self.assets: set[int] = set(assets) if assets else set()
        self.nodes: set[int] = set(nodes) if nodes else set()

    def to_dict(self):
        return {
            "id": self.id,
            "tag": self.tag,
            "description": self.description,
            "parent_id": self.parent_id,
            "assets": list(self.assets),  # pour rester compatible avec JSON
            "nodes": list(self.nodes), 
        }

    @classmethod
    def from_dict(cls, data):
        return cls(
            id=data["id"],
            tag=data["tag"],
            description=data.get("description", None),
            parent_id=data.get("parent_id", None),
            assets=set(data.get("assets", [])),
            nodes=set(data.get("nodes", [])) 
        )

class Value:
    def __init__(self, timestamp: str, value, status: str):
        self.timestamp: str = timestamp
        self.value = value
        self.status: int = status

    def to_dict(self):
        return {
            "timestamp": self.timestamp,
            "value": self.value,
            "status": self.status
        }

    @classmethod
    def from_dict(cls, data):
        return cls(
            timestamp=data["timestamp"],
            value=data["value"],
            status=data["status"]
        )

class ValueSet:
    def __init__(self, asset: int, key: str, unit_id: int):
        self.asset: int = asset  
        self.key: str = key
        self.unit_id: int = unit_id
        self.values: list[Value] = []

    def to_dict(self):
        return {
            "key": self.key,
            "unit": {
                self.unit_id,
            },
            "data": [value.to_dict() for value in self.values]
        }

    @classmethod
    def from_dict(cls, data):
        instance = cls(
            key=data["key"],
            unit_id=data["unit"]
        )
        instance.values = [Value.from_dict(v) for v in data.get("data", [])]
        return instance

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
    
    # Tester la fonction
    networks = getNetworkSettings()
    for network in networks:
        print(network.to_dict())

    # # Création des objets Binding
    # binding1 = Binding(identification="Math 4", protocol="TCP", slaveadress="192.168.200.23", registeradress="4206", datatype="FLOAT_B", unit_id=1, netilion_account_id=1, netilion_binding_id=2159190)
    # binding2 = Binding(identification="Niveau 3", protocol="TCP", slaveadress="192.168.200.23", registeradress="4204", datatype="FLOAT_B", unit_id=1, netilion_account_id=1, netilion_binding_id=1999331)
    # binding3 = Binding(identification="Niveau 1", protocol="TCP", slaveadress="192.168.200.23", registeradress="4200", datatype="FLOAT_B", unit_id=2, netilion_account_id=2, netilion_binding_id=12)
    # binding4 = Binding(identification="Math 11", protocol="TCP", slaveadress="192.168.200.23", registeradress="4220", datatype="FLOAT_B", unit_id=2, netilion_account_id=2, netilion_binding_id=2163151)

    # # Création des objets Asset
    # asset1 = Asset(id=1999331, serial_number="020202020202", description="Blabla", product_name=1, nodes=[1], instrumentation=[1])
    # asset2 = Asset(id=2159190, serial_number="3022228005", description="Concentrateur de signaux HART", product_name=2, nodes=[2], instrumentation=[2])
    # asset3 = Asset(id=2163151, serial_number="MC042B04484", description="", product_name=3, nodes=[3], instrumentation=[3])
    # asset4 = Asset(id=2163177, serial_number="N7044904428", description="", product_name=4, nodes=[4], instrumentation=[4])

    # # Création des objets Node
    # node1 = Node(id=1, name="Node 1", product_code="Code1")
    # node2 = Node(id=2, name="Node 2", product_code="Code2")
    # node3 = Node(id=3, name="Node 3", product_code="Code3")
    # node4 = Node(id=4, name="Node 4", product_code="Code4")

    # # Création des objets Instrumentation
    # instrumentation1 = Instrumentation(id=1809662, name="Instrumentation 1", description="Test Tag", parent_id=1)
    # instrumentation2 = Instrumentation(id=18096622, name="Instrumentation 2", description="Test Tag 2", parent_id=2)

    # # Création des objets NetilionAccount
    # account1 = NetilionAccount(identification="Compte Malo Forrest", account_id=1, client_id="c8b322d582afd6abf3b1cf8ddf5daf20", client_secret="e325642efe0fb9c8292c7e30b94388006e4f4681521fb8cc493f79dcd7790526", username="testapi268510@connect", password="malo")
    # account1.assets = [asset1, asset2, asset3, asset4]
    # account1.nodes = [node1, node2, node3, node4]
    # account1.instrumentations = [instrumentation1, instrumentation2]

    # account2 = NetilionAccount(identification="Compte Salle Eurêka", account_id=2, client_id="client_id_2", client_secret="client_secret_2", username="username_2", password="password_2")
    # account2.assets = [asset2, asset3]
    # account2.nodes = [node2, node3]
    # account2.instrumentations = [instrumentation2]

    # account3 = NetilionAccount(identification="Patate", account_id=3, client_id="coucou", client_secret="", username="", password="")
    # account4 = NetilionAccount(identification="Raclette", account_id=4, client_id="", client_secret="", username="", password="")

    # # # Création des objets Network
    # # network1 = Network(ipadress="192.168.44.88", subnetmask="255.255.255.0", gateway="192.168.44.1", description="This network configuration will be used to serve the configuration webserver", usage="configuration")
    # # network2 = Network(ipadress="", subnetmask="", gateway="", description="This network configuration will be used to access Netilion and the NTP clock server)", usage="internet")
    # # network3 = Network(ipadress="192.168.200.40", subnetmask="255.255.255.0", gateway="192.168.44.1", description="This network configuration will be used to access devices on the local modbus TCP network (if different than the internet access network)", usage="modbus")

    # # Création de la passerelle Netilion
    # passerelle_netilion = PasserelleNetilion()

    # # Ajout automatique des networks
    # passerelle_netilion.networks.extend(getNetworkSettings())

    # # Ajout des bindings
    # passerelle_netilion.bindings = [binding1, binding2, binding3, binding4]

    # # Ajout des accounts
    # passerelle_netilion.accounts = {
    #     account1.account_id: account1,
    #     account2.account_id: account2,
    #     account3.account_id: account3,
    #     account4.account_id: account4
    # }

    # # Configuration générale
    # passerelle_netilion.modbus_rate = 6
    # passerelle_netilion.username = "admin"
    # passerelle_netilion.password = "malo"

    # # Test de la configuration
    # dataconf = passerelle_netilion.to_dict()
    # print(json.dumps(dataconf, indent=4))

    # with open("serverweb/tempconf.conf", "w") as file:
    #     json.dump(dataconf, file, indent=4)


    # # # --------  Recréation à partir d'une config enregistrée  -------
    # # with open("tempconf.conf", "r") as file:
    # #     dataconf = json.load(file)

    # # passerelle = PasserelleNetilion.from_dict(dataconf)

    # # # Vérification des données recréées
    # # print(json.dumps(passerelle.to_dict(), indent=4))
