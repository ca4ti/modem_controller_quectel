# src/gui/handlers/custom_commands_handlers.py
import PySimpleGUI as sg
# Importações agora absolutas, assumindo que src está no sys.path
from src.gui.handlers.common_handlers import execute_modem_command, execute_modem_command_and_print_result
import src.gui.handlers.common_handlers as common_handlers # Importa o módulo para acessar as globais
from src.utils.threading_utils import gui_update_event
from src.config.commands_data import ALL_MANUAL_COMMANDS

def handle_send_custom_cmd_event(values, window):
    """Handler para o botão 'Enviar Comando Personalizado'."""
    command_to_send = values['-CUSTOM_AT_COMMAND-'].strip()
    expected_resp = values['-EXPECTED_RESPONSE-'].strip()
    try:
        custom_timeout = int(values['-CUSTOM_TIMEOUT-'])
    except ValueError:
        print("Erro: Timeout personalizado deve ser um número inteiro.")
        return
    if command_to_send:
        # CORREÇÃO: Usar execute_modem_command_and_print_result para exibir a resposta
        execute_modem_command_and_print_result(common_handlers.modem_controller.send_custom_at_command, command_to_send, expected_resp, custom_timeout)
        gui_update_event(window, '-CUSTOM_AT_COMMAND_CLEAR-', None) # Dispara evento para limpar o campo na thread principal
    else:
        print("Por favor, digite um comando AT para enviar.")

def handle_command_list_selection_event(window, values):
    """Handler quando um comando é selecionado na lista."""
    if values['-COMMAND_LIST-']:
        selected_item = values['-COMMAND_LIST-'][0]
        command_only = selected_item.split(':')[0].strip()
        window['-CUSTOM_AT_COMMAND-'].update(command_only) # Atualiza o campo de input diretamente

def handle_copy_selected_cmd_event(window, values):
    """Handler para o botão 'Copiar Comando Selecionado'."""
    if values['-COMMAND_LIST-']:
        selected_item = values['-COMMAND_LIST-'][0]
        command_only = selected_item.split(':')[0].strip()
        window['-CUSTOM_AT_COMMAND-'].update(command_only) # Copia para o campo de input

def handle_command_filter_event(window, values):
    """Handler para o campo de filtro de comandos."""
    search_term = values['-COMMAND_FILTER-'].lower()
    filtered_display_list = []
    for cmd_data in ALL_MANUAL_COMMANDS:
        cmd_line = f"{cmd_data['cmd']}: {cmd_data['desc']} (Seção {cmd_data['section']})"
        if search_term in cmd_line.lower():
            filtered_display_list.append(cmd_line)
    window['-COMMAND_LIST-'].update(filtered_display_list)

# Função auxiliar para limpar o campo de comando personalizado (chamada por evento da thread principal)
def clear_custom_command_input(window):
    window['-CUSTOM_AT_COMMAND-'].update('')
