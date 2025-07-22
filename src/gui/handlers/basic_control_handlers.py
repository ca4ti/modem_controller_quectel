# src/gui/handlers/basic_control_handlers.py
# Importações agora absolutas, assumindo que src está no sys.path
from src.gui.handlers.common_handlers import execute_modem_command, execute_modem_command_and_print_result
import src.gui.handlers.common_handlers as common_handlers # Importa o módulo para acessar as globais

def handle_power_off_event():
    """Handler para o botão 'Desligar Modem'."""
    execute_modem_command(common_handlers.modem_controller.power_off)

def handle_reboot_event():
    """Handler para o botão 'Reiniciar Modem'."""
    execute_modem_command(common_handlers.modem_controller.reboot)

def handle_factory_reset_event():
    """Handler para o botão 'Resetar Fábrica'."""
    execute_modem_command(common_handlers.modem_controller.factory_reset)

def handle_set_urc_port_event(values):
    """Handler para o botão 'Definir Porta URC'."""
    port_value = values['-URC_PORT_SET-']
    execute_modem_command(common_handlers.modem_controller.set_urc_output_port, port_value)

def handle_get_urc_port_event():
    """Handler para o botão 'Ler Porta URC'."""
    execute_modem_command_and_print_result(common_handlers.modem_controller.get_urc_output_port)
