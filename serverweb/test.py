import psutil
import socket
import subprocess
from model import Network, getNetworkSettings


# Tester la fonction
networks = getNetworkSettings()
for network in networks:
    print(network.to_dict())
