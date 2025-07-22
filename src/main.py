# src/main.py
# Ponto de entrada principal da aplicação GUI.

import sys
import os

# Adiciona o diretório raiz do projeto (modem_controller_novo) ao sys.path.
# Isso garante que importações como 'src.gui.app_main' funcionem corretamente.
# 'os.path.dirname(__file__)' obtém o diretório de src/main.py (que é 'src/').
# 'os.path.abspath(os.path.join(..., '..'))' sobe um nível para o diretório raiz (modem_controller_novo/).
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))

if project_root not in sys.path:
    sys.path.insert(0, project_root)

from src.gui.app_main import main as run_gui_app

if __name__ == '__main__':
    # Chama a função principal da interface gráfica
    run_gui_app()
