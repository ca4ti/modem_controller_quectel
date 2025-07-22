# src/gui/handlers/calls_handlers.py
# Importações agora absolutas, assumindo que src está no sys.path
from src.gui.handlers.common_handlers import execute_modem_command, execute_modem_command_and_print_result
import src.gui.handlers.common_handlers as common_handlers # Importa o módulo para acessar as globais

def handle_dial_call_event(values):
    """Handler para o botão 'Fazer Chamada' (ATD)."""
    number = values['-CALL_NUMBER-'].strip()
    if number:
        execute_modem_command(common_handlers.modem_controller.dial_call, number)
    else:
        print("Por favor, preencha o número para a chamada.")

def handle_answer_call_event():
    """Handler para o botão 'Atender Chamada' (ATA)."""
    execute_modem_command(common_handlers.modem_controller.answer_call)

def handle_hangup_call_event():
    """Handler para o botão 'Desligar Chamada' (ATH)."""
    execute_modem_command(common_handlers.modem_controller.hangup_call)

def handle_get_call_status_event():
    """Handler para o botão 'Status Chamada' (AT+CLCC)."""
    execute_modem_command_and_print_result(common_handlers.modem_controller.get_call_status)
