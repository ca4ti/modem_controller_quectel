# src/gui/handlers/info_status_handlers.py
# Importações agora absolutas, assumindo que src está no sys.path
from src.gui.handlers.common_handlers import execute_modem_command_and_print_result
import src.gui.handlers.common_handlers as common_handlers # Importa o módulo para acessar as globais

def handle_get_product_info_event():
    """Handler para o botão 'Info Produto' (ATI)."""
    execute_modem_command_and_print_result(common_handlers.modem_controller.get_product_info)

def handle_get_imei_event():
    """Handler para o botão 'IMEI' (AT+CGSN)."""
    execute_modem_command_and_print_result(common_handlers.modem_controller.get_imei)

def handle_get_imsi_event():
    """Handler para o botão 'IMSI' (AT+CIMI)."""
    execute_modem_command_and_print_result(common_handlers.modem_controller.get_imsi)

def handle_get_iccid_event():
    """Handler para o botão 'ICCID' (AT+QCCID)."""
    execute_modem_command_and_print_result(common_handlers.modem_controller.get_iccid)

def handle_get_sim_status_event():
    """Handler para o botão 'Status SIM' (AT+QSIMSTAT?)."""
    execute_modem_command_and_print_result(common_handlers.modem_controller.get_sim_status)

def handle_get_battery_status_event():
    """Handler para o botão 'Status Bateria' (AT+CBC)."""
    execute_modem_command_and_print_result(common_handlers.modem_controller.get_battery_status)

def handle_get_clock_event():
    """Handler para o botão 'Hora/Data' (AT+CCLK?)."""
    execute_modem_command_and_print_result(common_handlers.modem_controller.get_clock)

def handle_get_adc_value_event(values):
    """Handler para o botão 'Ler ADC' (AT+QADC)."""
    try:
        channel = int(values['-ADC_CHANNEL-'])
        execute_modem_command_and_print_result(common_handlers.modem_controller.get_adc_value, channel)
    except ValueError:
        print("Erro: Canal ADC deve ser um número inteiro (0 ou 1).")
