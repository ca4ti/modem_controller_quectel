# src/logger/logger.py
import logging
import os
import datetime

def setup_logger(name, log_file=None, level=logging.DEBUG):
    """
    Configura um logger para o módulo especificado.
    Se log_file não for fornecido, ele loga apenas no console.
    """
    if log_file is None:
        # Define um nome de arquivo de log padrão com timestamp
        log_dir = "logs"
        if not os.path.exists(log_dir):
            os.makedirs(log_dir)
        timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        log_file = os.path.join(log_dir, f"modem_controller_{timestamp}.log")

    formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')

    handler = logging.FileHandler(log_file, encoding='utf-8')
    handler.setFormatter(formatter)

    console_handler = logging.StreamHandler()
    console_handler.setFormatter(formatter)

    logger = logging.getLogger(name)
    logger.setLevel(level)

    # Evita adicionar múltiplos handlers se o logger já tiver um
    if not logger.handlers:
        logger.addHandler(handler)
        logger.addHandler(console_handler) # Adiciona também para saída no console

    return logger
