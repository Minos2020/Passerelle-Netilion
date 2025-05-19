import logging
import sys
from colorama import init, Fore, Style

# Initialiser colorama pour les couleurs sur tous les OS
init()

class ColorFormatter(logging.Formatter):
    COLORS = {
        logging.DEBUG: Style.DIM + Fore.WHITE,
        logging.INFO: Style.NORMAL + Fore.WHITE,
        logging.WARNING: Style.BRIGHT + Fore.YELLOW,
        logging.ERROR: Style.BRIGHT + Fore.RED,
        logging.CRITICAL: Style.BRIGHT + Fore.RED + Style.BRIGHT,
    }

    def format(self, record):
        color = self.COLORS.get(record.levelno, Style.RESET_ALL)
        message = super().format(record)
        return f"{color}{message}{Style.RESET_ALL}"

# Format de base
log_format = '[%(asctime)s] %(levelname)s - %(message)s'
date_format = '%Y-%m-%d %H:%M:%S'

# Créer le logger
logger = logging.getLogger("PasserelleLogger")

logger.setLevel(logging.INFO)  # Laisse INFO si tu veux moins de bruit

# Console handler avec couleurs
console_handler = logging.StreamHandler(sys.stdout)
console_handler.setLevel(logging.INFO)
console_handler.setFormatter(ColorFormatter(log_format, date_format))

# File handler (enregistre tous les niveaux dans un fichier)
file_handler = logging.FileHandler("passerelle.log", encoding='utf-8')
file_handler.setLevel(logging.DEBUG)
file_handler.setFormatter(logging.Formatter(log_format, date_format))

# Ajouter les handlers au logger
logger.addHandler(console_handler)
logger.addHandler(file_handler)
