import json, time, os, psutil, socket, subprocess
from services.encryption_utils import decrypt_data_from_file, encrypt_data_into_file
from services.netilion_utils import*

# Chemin du fichier de configuration
CONFIG_PATH = "config.conf"
SAVE_INTERVAL = 60  # secondes

CONFIG_ENCRYPTION_KEY = os.getenv("CONFIG_ENCRYPTION_KEY")

# Stockage de la configuration en mémoire
GLOBAL_CONFIG = {}
config_modified = False
last_save_time = time.time()

def get_config() -> dict:
    return GLOBAL_CONFIG

def set_config(new_config: dict):
    global GLOBAL_CONFIG
    GLOBAL_CONFIG = new_config

# Chargement de la config en mémoire depuis le fichier de sauvegarde
def load_config():
    """Charge la configuration depuis un fichier JSON chiffré."""
    global GLOBAL_CONFIG
    global accounts
    try:
        decrypted_json = decrypt_data_from_file(CONFIG_PATH, CONFIG_ENCRYPTION_KEY)
        GLOBAL_CONFIG = json.loads(decrypted_json)
        netilion_data = GLOBAL_CONFIG["netilion"]["accounts"]
        accounts = {acc['credentials']['account_id']: NetilionAccount.from_dict(acc['credentials']) for acc in netilion_data}
        set_accounts(accounts)
        # print ("Après chargement")
        # for account in accounts.values():
        #     print(str(account))
        print("✅ Configuration chargée en mémoire !")
    except Exception as e:
        print(f"❌ Erreur lors du chargement de la configuration : {e}")
        GLOBAL_CONFIG = {}
    

# Ecrase la configuration du fichier de sauvegarde avec celle qui est en mémoire
def save_config(encrypted=True):
    global config_modified, last_save_time
    """Sauvegarde la configuration en mémoire vers le fichier JSON."""
    try:
        data_to_encrypt = json.dumps(GLOBAL_CONFIG, indent=4)
        encrypt_data_into_file(data_to_encrypt.encode(), CONFIG_PATH, CONFIG_ENCRYPTION_KEY, encrypted)
        print("💾 Configuration mise à jour !")
        config_modified = False
        last_save_time = time.time()
    except Exception as e:
        raise Exception(f"Erreur inattendue lors de l'enregistrement de la configuration : {e}") from e

# Sauvegarde la config toutes les xx secondes, si elle a été modifiée entre temps
def save_periodically():
    """Thread de sauvegarde automatique de la configuration."""
    global config_modified, last_save_time
    while True:
        time.sleep(5)  # Vérifie toutes les 5 secondes
        if config_modified and time.time() - last_save_time > SAVE_INTERVAL:
            save_config()


# Chargement du fichier JSON et accès aux valeurs
def get_config_value(key):
    temp = GLOBAL_CONFIG
    return find_nested_key(temp, key)

# trouver une clé imbriquée dans un fichier json (dict)
def find_nested_key(data, key):
    """
    Recherche récursivement une clé dans un dictionnaire JSON imbriqué.
    Renvoie la valeur associée à la première occurrence trouvée.
    """
    if isinstance(data, dict):  
        if key in data:
            return data[key]
        for value in data.values():
            result = find_nested_key(value, key)
            if result is not None:
                return result
    elif isinstance(data, list):
        for item in data:
            result = find_nested_key(item, key)
            if result is not None:
                return result
    return None


# Modifier la valeur d'un clé dans le JSON de config
def set_config_value(key, value):
    """
    Modifie la valeur d'une clé spécifique dans la variable 'config'.
    Si la clé existe dans le JSON imbriqué, elle est mise à jour.
    Si la clé n'existe pas, aucune modification n'est effectuée.
    """
    global config_modified
    try:
        # Trouver et modifier la clé si elle existe
        if update_nested_key(GLOBAL_CONFIG, key, value):
            config_modified = True  # Marque la config comme modifiée


            save_config(False)  #A ENLEVER ENSUITE
            # lorsqu'un bouton écraser config sera implémenté


            
            return True  # Modification réussie
        else:
            print("⚠ Clé non trouvée dans la variable 'config'.")
            return False  # Clé non trouvée

    except Exception as e:
        print(f"❌ Erreur lors de la modification du fichier JSON : {e}")
        return False

def update_nested_key(data, key, new_value):
    """
    Met à jour récursivement une clé dans un dictionnaire JSON imbriqué.
    Renvoie True si la clé a été trouvée et mise à jour, sinon False.
    """
    if isinstance(data, dict):
        if key in data:
            data[key] = new_value
            return True
        for sub_key in data:
            if update_nested_key(data[sub_key], key, new_value):
                return True

    elif isinstance(data, list):
        for item in data:
            if update_nested_key(item, key, new_value):
                return True

    return False


def get_element_from_array(array, key, value):
    """
    Recherche un élément dans un tableau JSON où `key == value`.
    Supporte les comparaisons entre chaînes et nombres.
    Retourne l'élément trouvé ou None s'il n'existe pas.
    """
    if not isinstance(array, list):
        print("⚠ Le tableau parcouru n'existe pas ou n'est pas un tableau.")
        return None

    for element in array:
        if isinstance(element, dict) and key in element:
            element_value = element[key]
            if (isinstance(element_value, int) and element_value == int(value)) or \
               (isinstance(element_value, str) and element_value == value):
                return element  # ✅ Élément trouvé !

    print("⚠ Aucun élément trouvé.")
    return None

def getNetworkSettings():
    """
    Récupère les configurations réseau de l'ordinateur.
    Ne retourne que les interfaces Ethernet et Wi-Fi.
    """
    network_settings = {}
    valid_interfaces = ["eno1", "enp4s0", "wlp2s0"]  # Liste des préfixes des interfaces Ethernet et Wi-Fi

    # Récupère toutes les interfaces réseau disponibles
    for interface, addrs in psutil.net_if_addrs().items():
        # Filtre les interfaces Ethernet (eth, en) et Wi-Fi (wlan)
        if any(interface.startswith(prefix) for prefix in valid_interfaces):
            # Initialiser les champs pour cette interface
            ip_address = None
            subnet_mask = None
            gateway = None

            for addr in addrs:
                try:
                    # On vérifie si l'adresse est de type IPv4 (pas IPv6)
                    if addr.family == socket.AF_INET:  # Utilisation de socket.AF_INET
                        ip_address = addr.address
                        subnet_mask = addr.netmask
                except AttributeError as e:
                    print(f"Erreur lors de l'accès à addr.family : {e}")

            # Maintenant, obtenons la passerelle et DHCP
            if ip_address:
                # Utilisation de "ip route" pour obtenir la passerelle par défaut
                try:
                    route_output = subprocess.check_output(["ip", "route"]).decode("utf-8")
                    for line in route_output.splitlines():
                        if "default via" in line:
                            # Vérifie si la ligne correspond à l'interface actuelle
                            if interface in line:
                                gateway = line.split()[2]  # La passerelle par défaut est après "default via"
                except subprocess.CalledProcessError as e:
                    print(f"Erreur lors de la récupération de la passerelle : {e}")
                    gateway = 'N/A'

                # Ajouter cette configuration au dictionnaire
                network_settings[interface] = {
                    "IP Address": ip_address,
                    "Subnet Mask": subnet_mask,
                    "Gateway": gateway if gateway else 'N/A',
                }

    return network_settings


if __name__ == '__main__':

    # load_dotenv()
    # CONFIG_ENCRYPTION_KEY = os.getenv("CONFIG_ENCRYPTION_KEY")
    
    # encrypt_file(CONFIG_PATH, CONFIG_ENCRYPTION_KEY)

    # print ("Avant chargement")
    # for account in accounts.values():
    #     print(str(account))

    # load_config()

    # print ("Après chargement")
    # for account in accounts.values():
    #   print(str(account))
    pass