# src/config/commands_data.py
import json
import os
import sys

# Ajusta o caminho para ser absoluto a partir da raiz do projeto.
# 'os.path.abspath(__file__)' dá o caminho absoluto para este arquivo (src/config/commands_data.py).
# 'os.path.dirname(...)' dá o diretório deste arquivo (src/config/).
# 'os.path.join(..., '..', '..')' sobe dois níveis para a raiz do projeto (modem_controller_final/).
# E então desce para 'resources/at_commands.json'.
COMMANDS_JSON_FILE = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', 'resources', 'at_commands.json'))

def load_manual_commands():
    """
    Carrega os comandos AT do arquivo JSON.
    :return: Uma lista de dicionários com os comandos, ou uma lista vazia se houver erro.
    """
    try:
        with open(COMMANDS_JSON_FILE, 'r', encoding='utf-8') as f:
            commands = json.load(f)
        return commands
    except FileNotFoundError:
        print(f"Erro: O arquivo '{COMMANDS_JSON_FILE}' não foi encontrado.")
        print("Por favor, verifique se 'at_commands.json' está na pasta 'resources' na raiz do seu projeto.")
        return []
    except json.JSONDecodeError as e:
        print(f"Erro ao decodificar JSON do arquivo '{COMMANDS_JSON_FILE}': {e}")
        print("Por favor, verifique a sintaxe do arquivo 'at_commands.json'.")
        return []

# Carregar os comandos na inicialização do script
ALL_MANUAL_COMMANDS = load_manual_commands()
