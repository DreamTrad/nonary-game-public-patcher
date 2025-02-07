import logging

logging.basicConfig(
    level=logging.INFO,  # Niveau de journalisation (DEBUG, INFO, WARNING, ERROR, CRITICAL)
    format="%(asctime)s - %(levelname)s - %(message)s",  # Format des messages de log
    filename="patch_log.log",  # Nom du fichier de log
    filemode="w",  # Mode d'écriture du fichier ('w' pour écrire à chaque fois)
)