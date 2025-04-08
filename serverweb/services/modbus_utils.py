from services.config_utils import*
import struct
import time
import json
from flask import  jsonify
from pymodbus.client import ModbusTcpClient #, ModbusSerialClient
from datetime import datetime

# Paramètres de configuration (doivent être extraits de ton fichier config.json)
MODBUS_CONFIG = get_config_value('modbus')

BINDINGS = get_config_value('bindings')

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
            print(f"Erreur lecture registre {register_address} sur l'esclave {slave_address}.")
            return None
        else:
            # Conversion du registre en float32 si nécessaire
            data = result.registers  # Par exemple, pour 1 registre de 16 bits
            return convert_modbus_data(data, datatype)
    except Exception as e:
        print(f"Erreur lecture registre Modbus: {e}")
        return None

def modbus_tcp_client(ip, port=502):
    """ Création du client Modbus TCP """
    client = ModbusTcpClient(ip, port=port)
    client.connect()
    return client

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

def store_data_to_json(data, filename="modbus_data.json"):
    """ Enregistre les données dans un fichier JSON """
    try:
        with open(filename, "a") as f:
            json.dump(data, f)
            f.write("\n")  # Ajouter un saut de ligne entre les entrées
    except Exception as e:
        print(f"Erreur lors de l'enregistrement des données dans le fichier JSON: {e}")
    



if __name__ == "__main__":
    # Exemple d'utilisation de modbus_tcp_client ou modbus_rtu_client selon le type de protocole
    while (True):
        for binding in BINDINGS:
            if binding["protocol"] == "TCP":
                client = modbus_tcp_client(binding["slaveadress"])
            # elif binding["protocol"] == "RTU":
            #     client = modbus_rtu_client("/dev/ttyUSB0")  # Exemple de port série
            else:
                print(f"Protocole inconnu pour l'identification {binding['identification']}")
                continue

            valeur = read_registers(client, binding["slaveadress"], binding["registeradress"], binding["datatype"])

            if valeur is not None:
                timestamp = get_current_time()
                data = {
                    "identification": binding["identification"],
                    "value": valeur,
                    "timestamp": timestamp
                }
                store_data_to_json(data)
                print(f"Donnée enregistrée pour {binding['identification']}: {valeur} à {timestamp}")
            
            client.close()  # Fermer la connexion après chaque lecture
        
        time.sleep(int(MODBUS_CONFIG["rate"]))  # Attendre avant de lire le prochain registre
