import logging

# Configuration de base du logger
logging.basicConfig(
    level=logging.INFO,
    format='[%(asctime)s] %(levelname)s - %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S',
)

logger = logging.getLogger("PasserelleLogger")

# logger.setLevel(logging.DEBUG)