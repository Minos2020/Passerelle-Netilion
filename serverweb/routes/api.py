from flask import Blueprint, jsonify, request
import json
from services.config_utils import*
from services.modbus_utils import*

api_bp = Blueprint('api', __name__)

# -------------  GESTION CONFIG  ------------

@api_bp.route('/get_config', methods=['GET'])
def get_config():
    return jsonify(GLOBAL_CONFIG)

@api_bp.route('/load_config', methods=['POST'])
def load_config():
    if (
        set_config_value("bindings", find_nested_key(request.json, "bindings")) and
        set_config_value("netilion", find_nested_key(request.json, "netilion")) and
        set_config_value("credentials", find_nested_key(request.json, "credentials")) and
        set_config_value("modbus", find_nested_key(request.json, "modbus")) and
        set_config_value("networks", find_nested_key(request.json, "networks"))
    ):
        return jsonify({"status": "success"})
    else:
        print("❌ Problème lors de l'enregistrement.\nRetour à la configuration originale.")
        return jsonify({"status": "error"})


# -------------  BINDINGS ------------

@api_bp.route('/get_bindings', methods=['GET'])
def get_bindings():
    bindings = get_config_value('bindings')
    return jsonify(bindings)

@api_bp.route('/save_bindings', methods=['POST'])
def save_bindings():
    if set_config_value("bindings", request.json):
        return jsonify({"status": "success"})
    else:
        print("❌ Problème lors de l'enregistrement")
        return jsonify({"status": "error"})
    


# -------------  MODBUS ------------

@api_bp.route('/get_modbus_config', methods=['GET'])
def get_modbus_config():
    netilion_config = get_config_value('modbus')
    return jsonify(netilion_config)

@api_bp.route('/save_modbus_config', methods=['POST'])
def save_modbus_config():
    if set_config_value("modbus", request.json):
        return jsonify({"status": "success"})
    else:
        print("❌ Problème lors de l'enregistrement")
        return jsonify({"status": "error"})

@api_bp.route('/modbus_test', methods=['POST'])
def modbus_test():
    binding = request.json
    if binding["protocol"]!="TCP":
        return jsonify({"status": "error", "type": "Protocole non géré"})
    try:
        try:
            client = modbus_tcp_client(binding["slaveadress"])
            if not client.connect():  # Vérifie si la connexion est bien établie
                raise ConnectionError(f"Impossible de se connecter à {binding['slaveadress']}:502")
        except Exception as conn_err:
            return jsonify({"status": "error", "type": str(conn_err)})
        
        try:
            valeur = read_register(client, binding["slaveadress"], binding["registeradress"], binding["datatype"])
        except Exception as read_err:
            return jsonify({"status": "error", "type": f"Erreur de lecture Modbus : {str(read_err)}"})
        
        client.close()  # Fermer la connexion après chaque lecture  
        
        # print(valeur)
        if valeur != None:
            return jsonify({"status": "success", "value": round(valeur, 3)})
        else:
            return jsonify({"status": "error", "type": "Valeur non lue"})
            
    except Exception as e:
        print(f"❌ Problème lors de la lecture: {e}")
        return jsonify({"status": "error", "type": str(e)})

    
# -------------  NETWORKS ------------

@api_bp.route('/get_networks_config', methods=['GET'])
def get_networks_config():
    networks_config = get_config_value('networks')
    return jsonify(networks_config)

@api_bp.route('/save_networks_config', methods=['POST'])
def save_networks_config():
    if set_config_value("networks", request.json):
        return jsonify({"status": "success"})
    else:
        print("❌ Problème lors de l'enregistrement")
        return jsonify({"status": "error"})
    


# -------------  NETILION ------------

@api_bp.route('/get_netilion_config', methods=['GET'])
def get_netilion_config():
    netilion_config = get_config_value('accounts')
    return jsonify(netilion_config)

@api_bp.route('/save_netilion_config', methods=['POST'])
def save_netilion_config():
    if set_config_value("accounts", request.json):
        return jsonify({"status": "success"})
    else:
        print("❌ Problème lors de l'enregistrement")
        return jsonify({"status": "error"})
