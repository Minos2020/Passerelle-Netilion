from services.netilion_utils import*
from services.netilion_client import*
# from services.config_utils import getNetworkSettings
# from services.encryption_utils import encrypt_data_into_file
import requests, json, time, os, psutil, subprocess, socket, platform, re


class PasserelleNetilion:

    _instance = None  # Singleton

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(PasserelleNetilion, cls).__new__(cls)
            cls._instance.accounts = {} # Dictionnaire {account_id: NetilionAccount}
            cls._instance.bindings = []
            cls._instance.networks = []
            cls._instance.modbus_rate = 60
            cls._instance.username = ""
            cls._instance.password = ""
            cls._instance.encryption = True
        return cls._instance
    
    def to_dict(self):
        """Convertit l'objet en dictionnaire pour la sauvegarde JSON."""
        return {
            "accounts": [acc.to_dict() for acc in self.accounts.values()],
            "bindings": [binding.to_dict() for binding in self.bindings],  # Si Binding a une méthode to_dict()
            "networks": [network.to_dict() for network in self.networks],  # Si Network a une méthode to_dict()
            "modbus_rate": self.modbus_rate,
            "username": self.username,
            "password": self.password,
            "encryption": self.encryption,
        }

    @classmethod
    def from_dict(cls, data):
        """Charge un objet PasserelleNetilion à partir d'un dictionnaire."""
        instance = cls()
        instance.accounts = {
            acc_data["account_id"]: NetilionAccount.from_dict(acc_data)
            for acc_data in data["accounts"]
        }
        instance.bindings = [Binding.from_dict(b) for b in data["bindings"]]  # Si Binding a une méthode from_dict()
        instance.networks = [Network.from_dict(n) for n in data["networks"]]  # Si Network a une méthode from_dict()
        instance.modbus_rate = data["modbus_rate"]
        instance.username = data["username"]
        instance.password = data["password"]
        instance.encryption = data["encryption"]

        return instance

class Network:
    def __init__(self, ipadress: str, subnetmask: str, gateway: str, description: str = None, internet_access: str = None):
        self.ipadress: str = ipadress
        self.subnetmask: str = subnetmask
        self.gateway: str = gateway
        self.description: str = description
        self.internet_access: str = internet_access

    def to_dict(self):
        return {
            "ipadress": self.ipadress,
            "subnetmask": self.subnetmask,
            "gateway": self.gateway,
            "description": self.description,
            "internet_access": self.internet_access
        }

    @classmethod
    def from_dict(cls, data):
        return cls(
            ipadress=data["ipadress"],
            subnetmask=data["subnetmask"],
            gateway=data["gateway"],
            description=data["description"],
            internet_access=data.get("internet_access", None)
        )

def getNetworkSettings() -> list:
    networks = []
    system = platform.system()

    # Interfaces actives uniquement
    for interface, stats in psutil.net_if_stats().items():
        if not stats.isup:
            continue  # interface inactive

        addrs = psutil.net_if_addrs().get(interface, [])
        ip_address = None
        subnet_mask = None
        gateway = None

        for addr in addrs:
            if addr.family == socket.AF_INET:
                ip = addr.address
                if ip.startswith("169.254") or ip.startswith("127."):
                    continue  # ignore APIPA et loopback
                ip_address = ip
                subnet_mask = addr.netmask

        if not ip_address:
            continue  # rien d'intéressant

        # Récupérer la gateway
        if system == "Linux":
            try:
                route_output = subprocess.check_output(["ip", "route"], encoding="utf-8")
                for line in route_output.splitlines():
                    if "default via" in line and interface in line:
                        gateway = line.split()[2]
                        break
            except subprocess.CalledProcessError:
                pass

        elif system == "Windows":
            try:
                route_output = subprocess.check_output(
                    ["route", "print", "-4"],
                    encoding="cp1252"
                )
                capture = False
                for line in route_output.splitlines():
                    line = line.strip()
                    if line.startswith("IPv4 Route Table"):
                        capture = True
                        continue
                    if capture and line == "":
                        break  # fin de table

                    # Cherche la ligne avec 0.0.0.0 comme destination (passerelle par défaut)
                    if line.startswith("0.0.0.0"):
                        parts = re.split(r"\s+", line)
                        if len(parts) >= 5:
                            gw_candidate = parts[2]
                            iface_ip = parts[3]
                            if iface_ip == ip_address:
                                gateway = gw_candidate
                                break
            except subprocess.CalledProcessError:
                pass

        # Test de connectivité réseau (ping vers 8.8.8.8)
        internet_access = False
        try:
            if system == "Linux":
                # Commande ping sous Linux (utilise "-c" pour spécifier le nombre de paquets)
                subprocess.check_call(["ping", "-c", "1", "8.8.8.8"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            elif system == "Windows":
                # Commande ping sous Windows (utilise "-n" pour spécifier le nombre de paquets)
                subprocess.check_call(["ping", "-n", "1", "8.8.8.8"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            internet_access = True
        except subprocess.CalledProcessError as e:
            print(f"Ping échoué pour l'interface {interface}. Erreur: {e}")
            internet_access = False

        # Créer et ajouter l'objet
        networks.append(Network(
            ipadress=ip_address,
            subnetmask=subnet_mask,
            gateway=gateway or 'N/A',
            description=interface,
            internet_access=internet_access
        ))

    return networks

if __name__ == '__main__':
    
    # Tester la fonction
    networks = getNetworkSettings()
    for network in networks:
        print(network.to_dict())

    # # Création des objets Binding
    # binding1 = Binding(identification="Math 4", protocol="TCP", slaveadress="192.168.200.23", registeradress="4206", datatype="FLOAT_B", unit_id=1, netilion_account_id=1, netilion_binding_id=2159190)
    # binding2 = Binding(identification="Niveau 3", protocol="TCP", slaveadress="192.168.200.23", registeradress="4204", datatype="FLOAT_B", unit_id=1, netilion_account_id=1, netilion_binding_id=1999331)
    # binding3 = Binding(identification="Niveau 1", protocol="TCP", slaveadress="192.168.200.23", registeradress="4200", datatype="FLOAT_B", unit_id=2, netilion_account_id=2, netilion_binding_id=12)
    # binding4 = Binding(identification="Math 11", protocol="TCP", slaveadress="192.168.200.23", registeradress="4220", datatype="FLOAT_B", unit_id=2, netilion_account_id=2, netilion_binding_id=2163151)

    # # Création des objets Asset
    # asset1 = Asset(id=1999331, serial_number="020202020202", description="Blabla", product_id=1, nodes=[1], instrumentation=[1])
    # asset2 = Asset(id=2159190, serial_number="3022228005", description="Concentrateur de signaux HART", product_id=2, nodes=[2], instrumentation=[2])
    # asset3 = Asset(id=2163151, serial_number="MC042B04484", description="", product_id=3, nodes=[3], instrumentation=[3])
    # asset4 = Asset(id=2163177, serial_number="N7044904428", description="", product_id=4, nodes=[4], instrumentation=[4])

    # # Création des objets Node
    # node1 = Node(id=1, name="Node 1", product_code="Code1")
    # node2 = Node(id=2, name="Node 2", product_code="Code2")
    # node3 = Node(id=3, name="Node 3", product_code="Code3")
    # node4 = Node(id=4, name="Node 4", product_code="Code4")

    # # Création des objets Instrumentation
    # instrumentation1 = Instrumentation(id=1809662, name="Instrumentation 1", description="Test Tag", parent_id=1)
    # instrumentation2 = Instrumentation(id=18096622, name="Instrumentation 2", description="Test Tag 2", parent_id=2)

    # # Création des objets NetilionAccount
    # account1 = NetilionAccount(identification="Compte Malo Forrest", account_id=1, client_id="c8b322d582afd6abf3b1cf8ddf5daf20", client_secret="e325642efe0fb9c8292c7e30b94388006e4f4681521fb8cc493f79dcd7790526", username="testapi268510@connect", password="malo")
    # account1.assets = [asset1, asset2, asset3, asset4]
    # account1.nodes = [node1, node2, node3, node4]
    # account1.instrumentations = [instrumentation1, instrumentation2]

    # account2 = NetilionAccount(identification="Compte Salle Eurêka", account_id=2, client_id="client_id_2", client_secret="client_secret_2", username="username_2", password="password_2")
    # account2.assets = [asset2, asset3]
    # account2.nodes = [node2, node3]
    # account2.instrumentations = [instrumentation2]

    # account3 = NetilionAccount(identification="Patate", account_id=3, client_id="coucou", client_secret="", username="", password="")
    # account4 = NetilionAccount(identification="Raclette", account_id=4, client_id="", client_secret="", username="", password="")

    # # # Création des objets Network
    # # network1 = Network(ipadress="192.168.44.88", subnetmask="255.255.255.0", gateway="192.168.44.1", description="This network configuration will be used to serve the configuration webserver", usage="configuration")
    # # network2 = Network(ipadress="", subnetmask="", gateway="", description="This network configuration will be used to access Netilion and the NTP clock server)", usage="internet")
    # # network3 = Network(ipadress="192.168.200.40", subnetmask="255.255.255.0", gateway="192.168.44.1", description="This network configuration will be used to access devices on the local modbus TCP network (if different than the internet access network)", usage="modbus")

    # # Création de la passerelle Netilion
    # passerelle_netilion = PasserelleNetilion()

    # # Ajout automatique des networks
    # passerelle_netilion.networks.extend(getNetworkSettings())

    # # Ajout des bindings
    # passerelle_netilion.bindings = [binding1, binding2, binding3, binding4]

    # # Ajout des accounts
    # passerelle_netilion.accounts = {
    #     account1.account_id: account1,
    #     account2.account_id: account2,
    #     account3.account_id: account3,
    #     account4.account_id: account4
    # }

    # # Configuration générale
    # passerelle_netilion.modbus_rate = 6
    # passerelle_netilion.username = "admin"
    # passerelle_netilion.password = "malo"

    # # Test de la configuration
    # dataconf = passerelle_netilion.to_dict()
    # print(json.dumps(dataconf, indent=4))

    # with open("serverweb/tempconf.conf", "w") as file:
    #     json.dump(dataconf, file, indent=4)


    # # # --------  Recréation à partir d'une config enregistrée  -------
    # # with open("tempconf.conf", "r") as file:
    # #     dataconf = json.load(file)

    # # passerelle = PasserelleNetilion.from_dict(dataconf)

    # # # Vérification des données recréées
    # # print(json.dumps(passerelle.to_dict(), indent=4))
