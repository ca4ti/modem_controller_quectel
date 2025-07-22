# src/gui/handlers/gps_usb_handlers.py
# Importações agora absolutas, assumindo que src está no sys.path
from src.gui.handlers.common_handlers import execute_modem_command, execute_modem_command_and_print_result
import src.gui.handlers.common_handlers as common_handlers # Importa o módulo para acessar as globais

def handle_enable_gps_event():
    """Handler para o botão 'Ativar GPS' (AT+QGPS=1)."""
    execute_modem_command(common_handlers.modem_controller.enable_gps)

def handle_disable_gps_event():
    """Handler para o botão 'Desativar GPS' (AT+QGPS=0)."""
    execute_modem_command(common_handlers.modem_controller.disable_gps)

def handle_get_gps_location_event():
    """Handler para o botão 'Obter Localização GPS' (AT+QGPSLOC?)."""
    execute_modem_command_and_print_result(common_handlers.modem_controller.get_gps_location)

def handle_set_gps_outport_event(values):
    """Handler para o botão 'Definir Saída GPS NMEA' (AT+QGPSCFG="outport")."""
    outport_value = values['-GPS_OUTPORT_SET-']
    execute_modem_command(common_handlers.modem_controller.set_gps_outport, outport_value)

def handle_get_gps_outport_event():
    """Handler para o botão 'Ler Saída GPS NMEA' (AT+QGPSCFG="outport"?)."""
    execute_modem_command_and_print_result(common_handlers.modem_controller.get_gps_outport)

def handle_get_usb_configuration_event():
    """Handler para o botão 'Ler Configuração USB' (AT+QCFG="USBCFG"?)."""
    execute_modem_command_and_print_result(common_handlers.modem_controller.get_usb_configuration)

def handle_enable_voice_over_usb_event(values):
    """Handler para o botão 'Habilitar Voice over USB' (AT+QPCMV=1)."""
    try:
        port_pcmv = int(values['-QPCMV_PORT-'])
        execute_modem_command(common_handlers.modem_controller.enable_voice_over_usb, port_pcmv)
    except ValueError:
        print("Erro: Porta PCM para Voice over USB inválida. Use 0 (USB NMEA) ou 1 (UART).")

def handle_disable_voice_over_usb_event():
    """Handler para o botão 'Desabilitar Voice over USB' (AT+QPCMV=0)."""
    execute_modem_command(common_handlers.modem_controller.disable_voice_over_usb)

def handle_get_voice_over_usb_status_event():
    """Handler para o botão 'Status Voice over USB' (AT+QPCMV?)."""
    execute_modem_command_and_print_result(common_handlers.modem_controller.get_voice_over_usb_status)
