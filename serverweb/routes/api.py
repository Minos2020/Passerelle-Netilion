from flask import Blueprint, jsonify, request, session
from functools import wraps
from services.modbus_utils import*
from services.config_utils import*
from services.encryption_utils import*
from services.netilion_utils import NetilionAccount, getAccountByID

api_bp = Blueprint('api', __name__)


# ------------  DECORATEUR LOGIN  -----------

# Permet de restraindre l'accès aux différentes pages
def login_required(f):
    @wraps(f)  # Garde les métadonnées de la fonction originale
    def decorated_function(*args, **kwargs):
        if 'authenticated' not in session:
            return """
            <!DOCTYPE html>
            <html>            
                <head>
                    <title>Accès refusé</title>
                    <style>
                        body { font-family: Arial, sans-serif; text-align: center; padding: 50px; }
                        .container { max-width: 400px; margin: auto; padding: 20px; border: 1px solid #ddd; border-radius: 10px; background: #f9f9f9; }
                        button { background-color: #007BFF; color: white; border: none; padding: 10px 20px; font-size: 16px; border-radius: 5px; cursor: pointer; }
                        button:hover { background-color: #0056b3; }
                    </style>
                </head>
                <body>
                    <div class="container">
                        <h2>⛔ Access denied</h2>
                        <p style="margin-bottom: 50px;">You must be authenticated to access this ressource.</p>
                        <a href='/login'><button>Login page</button></a>
                    </div>
                </body>
            </html>
            """, 403  # 403 = Forbidden (Accès refusé)
        return f(*args, **kwargs)  # Exécute la fonction originale si l'utilisateur est authentifié
    return decorated_function

# -------------  GESTION CONFIG  ------------

@api_bp.route('/get_config', methods=['GET'])
@login_required  # 🔒 Protège cette route
def get_config_as_JSON():
    return jsonify(get_config())

@api_bp.route('/get_config_file', methods=['GET'])
@login_required  # 🔒 Protège cette route
def get_config_encrypted():
    save_config()
    with open(CONFIG_PATH, "rb") as f:
            encrypted_data = f.read()
    return encrypted_data

@api_bp.route('/load_config_file', methods=['POST'])
@login_required  # 🔒 Protège cette route
def load_config_encrypted():
    try:
        # Déchiffrer les données reçues
        decrypted_data = decrypt_data(request.data, CONFIG_ENCRYPTION_KEY)
        
        # Vérifier si le contenu est bien un JSON valide
        json_data = json.loads(decrypted_data)  # Déclenche une erreur si invalide
        
        # Sauvegarder les données chiffrées dans le fichier (on garde les données en clair en mémoire)
        with open(CONFIG_PATH, "wb") as f:
            f.write(request.data)  # Stockage chiffré
        load_config()
        print("✅ Configuration mise à jour avec succès !")
        
        return jsonify({"status": "success"})

    except json.JSONDecodeError:
        print("❌ Erreur : le fichier déchiffré n'est pas un JSON valide.")
        return jsonify({"status": "error", "message": "Fichier de configuration invalide."})

    except Exception as e:
        print(f"❌ Erreur inattendue : {e}")
        return jsonify({"status": "error", "message": str(e)})


# -------------  BINDINGS ------------

@api_bp.route('/get_bindings', methods=['GET'])
@login_required  # 🔒 Protège cette route
def get_bindings():
    bindings = get_config_value('bindings')
    return jsonify(bindings)

@api_bp.route('/save_bindings', methods=['POST'])
@login_required  # 🔒 Protège cette route
def save_bindings():
    if set_config_value("bindings", request.json):
        return jsonify({"status": "success"})
    else:
        print("❌ Problème lors de l'enregistrement")
        return jsonify({"status": "error"})
    


# -------------  MODBUS ------------

@api_bp.route('/get_modbus_config', methods=['GET'])
@login_required  # 🔒 Protège cette route
def get_modbus_config():
    netilion_config = get_config_value('modbus')
    return jsonify(netilion_config)

@api_bp.route('/save_modbus_config', methods=['POST'])
@login_required  # 🔒 Protège cette route
def save_modbus_config():
    if set_config_value("modbus", request.json):
        return jsonify({"status": "success"})
    else:
        print("❌ Problème lors de l'enregistrement")
        return jsonify({"status": "error"})

@api_bp.route('/modbus_test', methods=['POST'])
@login_required  # 🔒 Protège cette route
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
            valeur = read_registers(client, binding["slaveadress"], binding["registeradress"], binding["datatype"])
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
@login_required  # 🔒 Protège cette route
def get_networks_config():
    networks_config = get_config_value('networks')
    return jsonify(networks_config)

@api_bp.route('/save_networks_config', methods=['POST'])
@login_required  # 🔒 Protège cette route
def save_networks_config():
    if set_config_value("networks", request.json):
        return jsonify({"status": "success"})
    else:
        print("❌ Problème lors de l'enregistrement")
        return jsonify({"status": "error"})
    


# -------------  NETILION ------------

@api_bp.route('/get_netilion_config', methods=['GET'])
@login_required  # 🔒 Protège cette route
def get_netilion_config():
    netilion_config = get_config_value('accounts')
    return jsonify(netilion_config)

@api_bp.route('/save_netilion_config', methods=['POST'])
@login_required  # 🔒 Protège cette route
def save_netilion_config():
    if set_config_value("accounts", request.json):
        return jsonify({"status": "success"})
    else:
        print("❌ Problème lors de l'enregistrement")
        return jsonify({"status": "error"})

@api_bp.route('/test_netilion_connection',  methods=['POST'])
@login_required  # 🔒 Protège cette route
def test_netilion_connection():
    try:
        data = request.json
        tested_account = NetilionAccount(
            data["account_id"],
            data["client_id"],
            data["client_secret"],
            data["username"],
            data["password"]
        )
        tested_account._request_token("password", {"username": tested_account.username, "password": tested_account.password})
        
        return jsonify({"success": True, "last_connection": tested_account.get_last_connection()})
    
    except Exception as e:
        return jsonify({"success": False, "error": str(e)})
    

@api_bp.route('/get_last_connection',  methods=['POST'])
@login_required  # 🔒 Protège cette route
def get_last_connection():
    data = request.json
    account = getAccountByID(data["account_id"])
    if not account:    
        return jsonify({"success": False, "error": str(e)})
    else:
        return jsonify({"success": True, "last_connection": account.get_last_connection()})
    
@api_bp.route('/get_units',  methods=['GET'])
@login_required  # 🔒 Protège cette route
def get_units():
    try:
        with open("units.json", "r", encoding="utf-8") as f:
            units = json.load(f)  # Charger le JSON

    except (json.JSONDecodeError, FileNotFoundError):
        units = []  # Retourne une liste vide si le fichier est corrompu ou absent

    return jsonify(units)