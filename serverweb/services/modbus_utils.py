from services.config_utils import*
import struct
import json
from pymodbus.client import ModbusTcpClient #, ModbusSerialClient
from datetime import datetime
from services.locker_utils import file_lock
from services.logger_utils import logger

# Index des datatypes et du nombre de registres associé
counts = {
    "INT16": 1,
    "UINT16": 1,
    "INT32_B": 2,
    "INT32_L": 2,
    "UINT32_B": 2,
    "UINT32_L": 2,
    "FLOAT_B": 2,
    "FLOAT_L": 2,
    "DOUBLE_B": 4,
    "DOUBLE_L": 4
}

def read_registers(client, slave_address, register_address, datatype):
    """ Lire un registre Modbus sur x registres  """
    try:
        if isinstance(client, ModbusTcpClient):
            #print(datatype)
            #print("Count : " + str(counts[datatype]))
            result = client.read_holding_registers(int(register_address), count=counts[datatype])
        # elif isinstance(client, ModbusSerialClient):
        #     result = client.read_holding_registers(register_address, count, unit=slave_address)
        else:
            raise ValueError("Client Modbus invalide.")
        
        if result.isError():
            logger.error(f"Erreur lecture registre {register_address} sur l'esclave {slave_address}")
            return None
        else:
            # Conversion du registre en float32 si nécessaire
            data = result.registers  # Par exemple, pour 1 registre de 16 bits
            return convert_modbus_data(data, datatype)
    except Exception as e:
        logger.error(f"Erreur lecture registre Modbus: {e}")
        return None

def modbus_tcp_client(ip, port=502):
    """ Création du client Modbus TCP """
    return ModbusTcpClient(ip, port=port, timeout=2)

# def modbus_rtu_client(port, baudrate=19200, parity="N", stopbits=1):
#     """ Création du client Modbus RTU """
#     client = ModbusSerialClient(port=port, baudrate=baudrate, parity=parity, stopbits=stopbits)
#     client.connect()
#     return client

def convert_modbus_data(data, datatype):
    """
    Convertit une réponse Modbus brute en fonction du type de donnée spécifié.
    
    - `data` : liste de valeurs brutes renvoyées par Modbus (ex: [0x41C8, 0x0000] pour un float).
    - `datatype` : type de donnée attendu ("INT16", "UINT16", "INT32_B", "FLOAT_L", etc.).
    """
    raw_bytes = b''.join([val.to_bytes(2, byteorder='big') for val in data])

    if datatype == "INT16":
        return struct.unpack(">h", raw_bytes)[0]
    elif datatype == "UINT16":
        return struct.unpack(">H", raw_bytes)[0]
    elif datatype == "INT32_B":
        return struct.unpack(">i", raw_bytes)[0]
    elif datatype == "INT32_L":
        return struct.unpack("<i", raw_bytes)[0]
    elif datatype == "UINT32_B":
        return struct.unpack(">I", raw_bytes)[0]
    elif datatype == "UINT32_L":
        return struct.unpack("<I", raw_bytes)[0]
    elif datatype == "FLOAT_B":
        return struct.unpack(">f", raw_bytes)[0]
    elif datatype == "FLOAT_L":
        return struct.unpack("<f", raw_bytes)[0]
    elif datatype == "DOUBLE_B":
        return struct.unpack(">d", raw_bytes)[0]
    elif datatype == "DOUBLE_L":
        return struct.unpack("<d", raw_bytes)[0]
    else:
        raise ValueError(f"Type de donnée inconnu : {datatype}")


def get_current_time():
    """ Récupère l'heure actuelle sous forme ISO 8601 """
    return datetime.now().strftime("%Y-%m-%dT%H:%M:%S.%fZ")


def store_data_to_json(binding, new_data_entry):
    asset_id = str(binding.netilion_asset_id)
    filename = os.path.join("data", f"{binding.netilion_account_id}.json")

    # On crée le dossier "data" si jamais il n'existe pas / plus
    os.makedirs("data", exist_ok=True)
    
    with file_lock:
        # On lit les données du fichier (obligatoire pour pouvoir y ajouter les nouvelles)
        if os.path.exists(filename):
            try:
                with open(filename, "r", encoding="utf-8") as f:
                    all_data = json.load(f)
            except json.JSONDecodeError:
                logger.error(f"Fichier JSON corrompu : {filename}. Écrasement avec un dictionnaire vide.")
                all_data = {}
        else:
            all_data = {}
        
        # On crée une nouvelle clé avec l'asset_id si elle n'existe pas
        if asset_id not in all_data:
            all_data[asset_id] = []

        # Chercher si une entrée avec la même clé (asset_id) existe déjà
        found = False
        for entry in all_data[asset_id]:
            if entry["key"] == binding.key and entry["group"] == binding.group:
                # Créer un champ "data" si inexistant
                if "data" not in entry:
                    entry["data"] = []

                # Ajouter le nouveau lot dans "data"
                entry["data"].append(new_data_entry)
                found = True
                break

        # Si pas trouvé, on ajoute une nouvelle entrée
        if not found:
            all_data[asset_id].append(
                {
                    "key": binding.key,
                    "group": binding.group,
                    "unit": {"id": binding.unit_id},
                    "data": [new_data_entry]
                }
            )

        # Sauvegarder dans le fichier
        with open(filename, "w", encoding="utf-8") as f:
            json.dump(all_data, f, indent=2)


def readAllBindings():
                
        if PasserelleNetilion().mode != "production":
            return
        
        logger.info("[Modbus] - lecture des données...")

        for binding in PasserelleNetilion().bindings:
            
            if not binding.protocol == "TCP":    
                logger.warning(f"[Modbus] Binding \"{binding.identification}\" : protocole inconnu ou non pris en charge")
                continue
            
            
            value = None
            client = None

            try:
                client = modbus_tcp_client(binding.slaveadress)
                if not client.connect():
                    raise ConnectionError(f"Connexion échouée vers {binding.slaveadress}")
                
                value = read_registers(client, binding.slaveadress, binding.registeradress, binding.datatype)
            
            except Exception as e:
                logger.error(f"[Modbus] Binding {binding.identification} : {e}")
            
            finally:
                if client:
                    client.close()

            if value is not None:
                timestamp = get_current_time()
                data_entry = {
                    "status": "good",
                    "value": value,
                    "timestamp": timestamp
                }
                store_data_to_json(binding, data_entry)
                logger.debug(f"[Modbus] Donnée enregistrée pour {binding.identification}: {value} à {timestamp}")
            
            # client.close()  # Fermer la connexion après chaque lecture

        # print("Fait")
        


if __name__ == "__main__":
    pass
