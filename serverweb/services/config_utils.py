import json, time, os, psutil, socket, subprocess
from services.encryption_utils import decrypt_data_from_file, encrypt_data_into_file
from model import PasserelleNetilion

# Chemin du fichier de configuration
CONFIG_PATH = "configuration.conf"
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

def attach_callbacks(passerelle: PasserelleNetilion):
    for account in passerelle.accounts:
        account.changes_to_save = lambda: save_config(False)

# Chargement de la config en mémoire depuis le fichier de sauvegarde
def load_config(encrypted=True):
    """
    Charge la configuration depuis un fichier JSON;
    False = fichier non chiffré
    True = fichier chiffré
    """
    global GLOBAL_CONFIG
    global accounts
    print(f"💾 Chargement de la configuration {"CHIFFREE" if encrypted else "EN CLAIR"}")
    try:
        decrypted_conf = decrypt_data_from_file(CONFIG_PATH, CONFIG_ENCRYPTION_KEY, encrypted)
        dataconf = json.loads(decrypted_conf)

        passerelle = PasserelleNetilion.from_dict(dataconf)
        
        # Les identifiants du webserver sont chargés depuis des variables d'environnement
        passerelle.username = os.getenv('USER_NAME')
        passerelle.password = os.getenv('PASSWORD')
        
        attach_callbacks(passerelle)
        # print(passerelle.to_dict())

        print("✅ Configuration chargée en mémoire !")
    except Exception as e:
        print(f"❌ Erreur lors du chargement de la configuration : {e}")
        passerelle = PasserelleNetilion()
    

# Ecrase la configuration du fichier de sauvegarde avec celle qui est en mémoire
def save_config(encrypted=True):
    global config_modified, last_save_time
    """Sauvegarde la configuration en mémoire vers le fichier JSON."""
    try:
        passerelle = PasserelleNetilion()
        data_to_encrypt = json.dumps(passerelle.to_dict(), indent=4)
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