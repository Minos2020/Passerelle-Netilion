from cryptography.fernet import Fernet
from services.config_utils import*
import os, traceback, json
from dotenv import load_dotenv, set_key

# Fonction pour générer une clé de chiffrement si nécessaire
def generate_key() -> str:
    key = Fernet.generate_key()
    print("Clé générée : " + key.decode())
    return key.decode()  # toujours décoder les clés avant de les stocker

# Chiffrer un fichier JSON
def encrypt_file(file_name: str, key: str):
    with open(file_name, "rb") as f:
        file_data = f.read()
    fernet = Fernet(key)
    encrypted_data = fernet.encrypt(file_data)
    with open(file_name, "wb") as f:
        f.write(encrypted_data)

# Déchiffrer un fichier JSON
def decrypt_file(file_name: str, key: str):
    """Déchiffrer un fichier JSON"""
    with open(file_name, "rb") as f:
        encrypted_data = f.read()
    fernet = Fernet(key)
    decrypted_data = fernet.decrypt(encrypted_data)
    with open(file_name, "wb") as f:
        f.write(decrypted_data)
    print(decrypted_data.decode())

# Retourner les données contenues dans un fichier chiffré
def decrypt_data_from_file(file_name: str, key: str) -> str:
    try:
        with open(file_name, "rb") as f:
            encrypted_data = f.read()
        fernet = Fernet(key)
        decrypted_data = fernet.decrypt(encrypted_data)
        return decrypted_data.decode()
    except IOError as e:
        print(f"Problème d'accès au fichier de configuration : {e}")
        raise IOError(f"Problème d'accès au fichier de configuration : {e}") from e
    except Exception as e:
        print(f'Erreur lors du déchiffrement des données : {e}')
        traceback.print_exc()
        raise Exception(f'Erreur lors du déchiffrement des données.{str(e)}') from e

def decrypt_data(data, key: str) -> str:
    try:
        fernet = Fernet(key)
        decrypted_data = fernet.decrypt(data)
        return decrypted_data.decode()
    except Exception as e:
        print(f'Erreur lors du déchiffrement des données : {e}')
        traceback.print_exc()
        raise Exception(f'Erreur lors du déchiffrement des données') from e

def encrypt_data_into_file(data: json, file_name: str, key: str):
    try:
        fernet = Fernet(key)
        encrypted_data = fernet.encrypt(data)
        with open(file_name, "wb") as f:
            f.write(encrypted_data)
    except Exception as e:
            print(f'Erreur lors du chiffrement des données : {e}')
            traceback.print_exc()
            raise Exception(f'Erreur lors du chiffrement des données') from e

# Si ce fichier est directement run
if __name__ == '__main__':
    # Créer une nouvelle variable dans .env
    # set_key(".env", "CONFIG_ENCRYPTION_KEY", generate_key())

    # Charge les variables de .env dans les variables d'environnement
    # load_dotenv()

    # # Récupération de la clé de chiffrement dans les variables d'environnement
    key = os.getenv('CONFIG_ENCRYPTION_KEY')
    
    # if key is None:
    #     raise ValueError("La clé de chiffrement n'est pas définie dans les variables d'environnement.")

    # encrypt_file("Blablabla.txt", key)

    encrypt_file("config.conf", key)
    # decrypt_file("config.conf", key)
    # decrypt_data("config.conf", key)

    # key = os.getenv("NETILION_ENCRYPTION_KEY")

    # print(decrypt_data("config.conf", key))