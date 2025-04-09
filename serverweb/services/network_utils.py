import psutil, subprocess, platform, socket, re

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
        
        from model import Network
        # Créer et ajouter l'objet
        networks.append(Network(
            ipadress=ip_address,
            subnetmask=subnet_mask,
            gateway=gateway or 'N/A',
            description=interface
        ))

    return networks