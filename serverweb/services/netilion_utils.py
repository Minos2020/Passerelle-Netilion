import requests, os, time, json
from services.config_utils import*
from services.encryption_utils import*
from services.netilion_client import Asset, Instrumentation, Node

accounts: dict[int, "NetilionAccount"] = {}


token_url = "https://api.netilion.endress.com/oauth/token"
BASE_URL = "https://api.netilion.endress.com/v1"

class NetilionAccount:
    def __init__(self, account_id: int, client_id: str, client_secret: str, username: str, password: str):
        self.account_id: int = account_id
        self.client_id: str = client_id
        self.client_secret: str = client_secret
        self.username: str = username
        self.password: str = password
        self.access_token: str = None
        self.refresh_token: str = None
        self.token_expiry: int = 0  # Timestamp d'expiration
        self.assets = list["Asset"]
        self.nodes = list["Node"]
        self.instrumentations = list["Instrumentation"]

    def __str__(self):
        """Permet de faire un print(str(instance)) pour voir les informations voulues"""
        return (
        f"\nAcc ID : {self.account_id}, Client ID: {self.client_id}\n"
        f"Acces token : {self.access_token if self.access_token is not None else 'Pas d\'access token'},\n"
        f"Refresh token : {self.refresh_token if self.refresh_token is not None else 'Pas de refresh token'},\n"
        f"{'Expiration token dans ' + str(int(self.token_expiry - time.time())) + ' secondes' if time.time() < self.token_expiry else ('Pas d\'access token' if not self.access_token else 'Token expiré')}"
    )

    def to_dict(self):
        """Convertit l'objet en dictionnaire pour la sérialisation"""
        return {
            "account_id": self.account_id,
            "client_id": self.client_id,
            "client_secret": self.client_secret,
            "username": self.username,
            "password": self.password,
            "access_token": self.access_token,
            "refresh_token": self.refresh_token,
            "token_expiry": self.token_expiry,
            "assets": [asset.__dict__ for asset in self.assets],  # Sérialisation des assets
            "nodes": [node.__dict__ for node in self.nodes],  # Sérialisation des nodes
            "instrumentations": [inst.__dict__ for inst in self.instrumentations]  # Sérialisation des instrumentations
        }

    @classmethod
    def from_dict(cls, data):
        """Crée une instance NetilionAuth à partir d'un dictionnaire"""
        instance = cls(
            data["account_id"], data["client_id"], data["client_secret"], data["username"], data["password"]
        )
        instance.access_token = data.get("access_token", None)
        instance.refresh_token = data.get("refresh_token", None)
        instance.token_expiry = data.get("token_expiry", 0)

         # Désérialisation des assets, nodes et instrumentations
        instance.assets = [Asset(**asset) for asset in data.get("assets", [])]
        instance.nodes = [Node(**node) for node in data.get("nodes", [])]
        instance.instrumentations = [Instrumentation(**inst) for inst in data.get("instrumentations", [])]
        
        return instance
    

    def _request_token(self, grant_type, extra_data=None) -> None:
        """
        Demande un token d'accès OAuth2 (soit initial, soit via refresh).
        """
        print(f"...requesting access token ({grant_type})...")
        token_data = {
            "grant_type": grant_type,
            "client_id": self.client_id,
            "client_secret": self.client_secret,
        }
        if extra_data:
            token_data.update(extra_data)

        response = requests.post(token_url, data=token_data)
        response_data = response.json()

        if response.status_code == 200:
            print(
                "Access granted with password" if grant_type == "password"
                else "Access granted with refresh token"
            )
            self.access_token = response_data['access_token']
            self.refresh_token = response_data.get('refresh_token', self.refresh_token)
            self.token_expiry = time.time() + response_data.get("expires_in", 660) - 10
        else:
            raise Exception(f"Failed to obtain access token: {response_data}")


    def authenticate(self):
        """
        Authentifie l'utilisateur et stocke le token.
        """
        self._request_token("password", {
            "username": self.username,
            "password": self.password
        })

    def refresh_token_if_needed(self):
        """
        Rafraîchit le token si nécessaire avant un appel API.
        """
        if self.access_token is None or time.time() >= self.token_expiry:
            print("🔄 Token expiré ou absent, rafraîchissement en cours...")
            # Si le refresh_token existe, on rafraîchit le token sans redemander les credentials.
            if self.refresh_token:
                self._request_token("refresh_token", {"refresh_token": self.refresh_token})
            else:
                self.authenticate()  # Sinon, on réauthentifie avec les identifiants
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
        return next((asset for asset in self.nodes if asset.id == asset_id), None)
    
    def get_instrumentation_by_id(self, instrumentation_id: int) -> Instrumentation | None:
        """Recherche un Node par son ID dans cet account"""
        return next((instrumentation for instrumentation in self.instrumentations if instrumentation.id == instrumentation_id), None)


    def send_request(self, method, endpoint, data=None, params=None):
        """Envoie une requête HTTP à Netilion avec gestion automatique du token."""
        
        # Obtenir les headers avec le token d'authentification
        headers = self.get_headersForAuth()  # Appel de la méthode pour récupérer les headers
        # Ajouter l'en-tête Content-Type
        headers["Content-Type"] = "application/json"
        # print(headers)

        url = f"{BASE_URL}/{endpoint}"
        # print(url)

        response = requests.request(method, url, json=data, params=params, headers=headers)
        if response.status_code == 401:  # Token expiré
            self.refresh_access_token()
            headers["Authorization"] = f"Bearer {self.access_token}"
            headers['accept'] = "application/json"
            response = requests.request(method, url, json=data, params=params, headers=headers)

        response.raise_for_status()  # Lève une exception en cas d'erreur HTTP
        return response



def get_accounts() -> dict[int, NetilionAccount]:
    """Retourne le dictionnaire des comptes Netilion."""
    return accounts

def set_accounts(new_accounts: dict[int, NetilionAccount]):
    """Met à jour le dictionnaire des comtpes Netilion. (OVERRIDE)"""
    global accounts
    accounts = new_accounts

def getAccountByID(account_id):
    """Récupère l'instance NetilionAuth associée à un compte donné."""
    return accounts.get(account_id)

def get_headers(account_id):
    """Récupère les headers d'un compte spécifique."""
    account = getAccountByID(account_id)
    if account:
        return account.get_headersForAuth()
    else:
        raise ValueError(f"Aucun compte trouvé pour l'ID {account_id}")
    
def fetch_all_units():
    """ Récupère toutes les unités de Netilion et les actualise le fichier units.json
        Cette fonction n'est pas faite pour être exécutée régulièrement, mais plutôt
        pour réactualise la base de donnée en cas de rajout d'unités par Endress Hauser
    """
    units = []
    page = 1
    per_page = 300  # Nombre maximum d'éléments par page
    
    while True:
        endpoint = f"units?page={page}&per_page={per_page}"
        
        response = accounts["1"].send_request("GET", endpoint)
        # print(response)

        if response.status_code != 200:
            print(f"Erreur {response.status_code} lors de la récupération des unités : {response.text}")
            break

        data = response.json()
        units.extend(data["units"])

        # Vérifie s'il y a encore des pages à récupérer
        if "pagination" in data and data["pagination"].get("next"):
            page += 1
        else:
            break

    # Sauvegarde dans un fichier JSON
    with open("units.json", "w", encoding="utf-8") as f:
        json.dump(units, f, indent=4, ensure_ascii=False)

    print(f"✅ {len(units)} unités enregistrées dans {"units.json"}")

# Exemple d'utilisation :
# auth_token = "ton_token_access"  # Remplace ceci par ton token valide
# fetch_all_units(auth_token)


if __name__ == '__main__':
    
    load_dotenv()
    
    

    # save_accounts_to_file()
    
    # print ("Après chargement")
    # for account in accounts.values():
    #     print(str(account))