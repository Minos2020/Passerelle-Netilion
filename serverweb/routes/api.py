from flask import Blueprint, jsonify, request, session
from functools import wraps
from services.modbus_utils import*
from services.config_utils import*
from services.encryption_utils import*
import services.network_utils as network_utils
from model import PasserelleNetilion, Binding, NetilionAccount


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
                        <h2>⛔ Accès refusé</h2>
                        <p style="margin-bottom: 50px;">Vous devez être authentifié pour accéder à cette ressource.</p>
                        <a href='/login'><button>Page de connexion</button></a>
                    </div>
                </body>
            </html>
            """, 403  # 403 = Forbidden (Accès refusé)
        return f(*args, **kwargs)  # Exécute la fonction originale si l'utilisateur est authentifié
    return decorated_function

# -------------  GESTION CONFIG  ------------

# Renvoie la config dans un JSON
@api_bp.route('/get_config', methods=['GET'])
@login_required  # 🔒 Protège cette route
def get_config_as_JSON():
    ans = PasserelleNetilion().to_dict_secured()

    return jsonify(ans)

# Récupère la config pour générer un fichier téléchargeable depuis l'interface web
@api_bp.route('/get_config_file', methods=['GET'])
@login_required  # 🔒 Protège cette route
def get_config_encrypted():
    # print(type(passerelle.to_dict()["encryption"]))
    # print(passerelle.to_dict()["encryption"])
    save_config(PasserelleNetilion().encryption)
    with open(CONFIG_PATH, "rb") as f:
            data = f.read()
    return data

# Charge un fichier de configuration depuis l'interface web
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
    bindings = PasserelleNetilion().to_dict()["bindings"]
    return jsonify(bindings)

@api_bp.route('/save_bindings', methods=['POST'])
@login_required  # 🔒 Protège cette route
def save_bindings():
    try:
        PasserelleNetilion().bindings = [Binding.from_dict(b) for b in request.json]


        save_config(PasserelleNetilion().encryption) # A ENLEVER


        return jsonify({"status": "success"})
    except Exception as e:
        print("❌ Erreur dans save_bindings:", e)
        return jsonify({"status": "error", "message": str(e)})
    


# -------------  MODBUS ------------

@api_bp.route('/get_general_config', methods=['GET'])
@login_required  # 🔒 Protège cette route
def get_general_config():
    response = {
        "modbus_rate": PasserelleNetilion().to_dict()["modbus_rate"]
    }
    return jsonify(response)

@api_bp.route('/save_general_config', methods=['POST'])
@login_required  # 🔒 Protège cette route
def save_general_config():
    try:
        PasserelleNetilion().modbus_rate = request.json["modbus_rate"]


        save_config(PasserelleNetilion().encryption) # A ENLEVER (False pour ne pas chiffrer les données)


        return jsonify({"status": "success"})
    except Exception as e:
        print("❌ Erreur dans save_general_config:", e)
        return jsonify({"status": "error", "message": str(e)})

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
    networks = network_utils.getNetworkSettings()
    networks_dict = [net.to_dict() for net in networks]
    return jsonify(networks_dict)

@api_bp.route('/save_networks_config', methods=['POST'])
@login_required  # 🔒 Protège cette route
def save_networks_config():
    if set_config_value("networks", request.json):
        return jsonify({"status": "success"})
    else:
        print("❌ Problème lors de l'enregistrement")
        return jsonify({"status": "error"})
    


# -------------  NETILION ------------

@api_bp.route('/get_accounts', methods=['GET'])
@login_required  # 🔒 Protège cette route
def get_accounts():
    passerelle = PasserelleNetilion()
    accounts = passerelle.to_dict_secured()["accounts"]
    return jsonify(accounts)

@api_bp.route('/save_accounts', methods=['POST'])
@login_required  # 🔒 Protège cette route
def save_netilion_config():
    try:
        passerelle = PasserelleNetilion()
        updated_accounts = []  # Contiendra les comptes à conserver après mise à jour

        for acc_dict in request.json:
            if 'isNew' in acc_dict:
                # Nouveau compte → crée l'objet sans ID, puis utilise add_account
                account = NetilionAccount(
                    identification=acc_dict["identification"],
                    client_id=acc_dict["client_id"],
                    client_secret=acc_dict["client_secret"],
                    username=acc_dict["username"],
                    password=acc_dict["password"],
                    changes_to_save=lambda: save_config(PasserelleNetilion().encryption)
                )
                passerelle.add_account(account)
                
            else:
                # Compte existant → on récupère le compte et on met à jour uniquement les infos qui ont changé
                account = passerelle.getAccountByID(acc_dict["account_id"])
                
                client_id = acc_dict["client_id"] if "client_id" in acc_dict.get("hasChanged", []) else account.client_id
                client_secret = acc_dict["client_secret"] if "client_secret" in acc_dict.get("hasChanged", []) else account.client_secret
                username = acc_dict["username"] if "username" in acc_dict.get("hasChanged", []) else account.username
                password = acc_dict["password"] if "password" in acc_dict.get("hasChanged", []) else account.password
                
                account.identification=acc_dict["identification"]
                account.client_id=client_id
                account.client_secret=client_secret
                account.username=username
                account.password=password
            updated_accounts.append(account)
        
        # Ne conserver que les comptes mis à jour ou ajoutés
        passerelle.accounts = updated_accounts
        save_config(False)

        return jsonify({"status": "success"})
    except Exception as e:
        print("❌ Erreur dans save_accounts:", e)
        return jsonify({"status": "error", "message": str(e)})
    

@api_bp.route('/test_account_connection',  methods=['POST'])
@login_required  # 🔒 Protège cette route
def test_account_connection():
    try:
        data = request.json
        
        if data.get('isNew'):
            tested_account = NetilionAccount(
                "tested_account",
                data["client_id"],
                data["client_secret"],
                data["username"],
                data["password"]
            )
            print("Compte temporairement créé pour le test car nouveau ou modifié.")
            
        else:
            saved_account = PasserelleNetilion().getAccountByID(data["account_id"])
            # Reconstitue un compte à partir des infos modifiées + les anciennes si pas modifiées
            client_id = data["client_id"] if "client_id" in data.get("hasChanged", []) else saved_account.client_id
            client_secret = data["client_secret"] if "client_secret" in data.get("hasChanged", []) else saved_account.client_secret
            username = data["username"] if "username" in data.get("hasChanged", []) else saved_account.username
            password = data["password"] if "password" in data.get("hasChanged", []) else saved_account.password
            
            tested_account = NetilionAccount(
                "tested_account",
                client_id,
                client_secret,
                username,
                password
            )
        
        tested_account._request_token("password", {"username": tested_account.username, "password": tested_account.password})
        
        return jsonify({"success": True, "last_connection": tested_account.get_last_connection()})
    
    except Exception as e:
        return jsonify({"success": False, "error": str(e)})
    

@api_bp.route('/get_last_connection',  methods=['POST'])
@login_required  # 🔒 Protège cette route
def get_last_connection():
    data = request.json
    account = PasserelleNetilion().getAccountByID(data["account_id"])
    if not account:    
        return jsonify({"success": False, "error": "no account found"})
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

@api_bp.route('/refresh_netilion_account',  methods=['POST'])
@login_required  # 🔒 Protège cette route
def refresh_netilion_account():
    data = request.json
    account = PasserelleNetilion().getAccountByID(data["account_id"])
    if not account:    
            return jsonify({"success": False, "error": "no account found"}), 404
    try:
        account.refresh_all_data()
        return jsonify({"success": True, "account": account.to_dict()})
    except Exception as e:
        account.authenticate()
        return jsonify({"success": False, "error": str(e)})