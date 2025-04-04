import psutil
import socket
import subprocess

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

# Tester la fonction
network_settings = getNetworkSettings()
print(network_settings)
