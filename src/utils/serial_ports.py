# src/utils/serial_ports.py
import serial.tools.list_ports
import re

def get_available_ports():
    """
    Retorna uma lista de strings com os nomes das portas seriais disponíveis no sistema.
    :return: Lista de strings (ex: ['COM1', '/dev/ttyUSB0']).
    """
    try:
        ports = [port.device for port in serial.tools.list_ports.comports()]
        if not ports:
            print("Nenhuma porta serial encontrada no sistema. Verifique a conexão do modem e os drivers.")
        # Ordenar as portas para consistência, priorizando ttyUSBx sobre ttySx
        # Regex para extrair número de portas, para evitar erro se não houver número após 'USB' ou 'ttyS'
        usb_ports = sorted([p for p in ports if 'USB' in p], key=lambda x: int(re.search(r'\d+', x).group()) if re.search(r'\d+', x) else 9999) 
        tty_ports = sorted([p for p in ports if 'ttyS' in p], key=lambda x: int(re.search(r'\d+', x).group()) if re.search(r'\d+', x) else 9999) 
        return usb_ports + tty_ports
    except Exception as e:
        print(f"Erro ao listar portas seriais: {e}")
        return []
