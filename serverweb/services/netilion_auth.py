import requests
import time
from config_utils import*

accounts = {}

token_url = "https://api.netilion.endress.com/oauth/token"

class NetilionAuth:
    def __init__(self, account_id: int, client_id: str, client_secret: str, username: str, password: str):
        self.account_id: int = account_id
        self.client_id: str = client_id
        self.client_secret: str = client_secret
        self.username: str = username
        self.password: str = password
        self.access_token: str = None
        self.refresh_token: str = None
        self.token_expiry: int = 0  # Timestamp d'expiration

    def __str__(self):
        return (
        f"\nID : {self.account_id},\n"
        f"Acces token : {self.access_token if self.access_token is not None else 'Pas d\'access token'},\n"
        f"Refresh token : {self.refresh_token if self.refresh_token is not None else 'Pas de refresh token'},\n"
        f"{'Expiration token dans ' + str(int(self.token_expiry - time.time())) + ' secondes' if time.time() < self.token_expiry else ('Pas d\'access token' if not self.access_token else 'Token expiré')}"
    )


    def _request_token(self, grant_type, extra_data=None):
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

def load_accounts():
    """Charge la configuration et initialise les comptes Netilion."""
    NETILION_CONFIG = get_config_value("netilion")

    for account in NETILION_CONFIG.get("accounts", []):
        if account["id"] in accounts:
            continue  # Si le compte est déjà chargé, on l'ignore
        credentials = account["credentials"]
        if credentials["client_id"] and credentials["client_secret"]:
            accounts[account["id"]] = NetilionAuth(
                account_id=account["id"],
                client_id=credentials["client_id"],
                client_secret=credentials["client_secret"],
                username=credentials["username"],
                password=credentials["pass"]
            )
            print(f"✅ Compte chargé : {account['identification']} (ID {account['id']})")
        else:
            print(f"⚠️ Compte ignoré : {account['identification']} (ID {account['id']}) - Pas d'identifiants fournis")

def get_account(account_id):
    # print(self.accounts)
    """Récupère l'instance NetilionAuth associée à un compte donné."""
    return accounts.get(account_id)

def get_headers(account_id):
    """Récupère les headers d'un compte spécifique."""
    account = get_account(account_id)
    if account:
        return account.get_headersForAuth()
    else:
        raise ValueError(f"Aucun compte trouvé pour l'ID {account_id}")