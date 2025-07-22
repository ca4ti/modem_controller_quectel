# src/gui/handlers/network_apn_handlers.py
# Importações agora absolutas, assumindo que src está no sys.path
from src.gui.handlers.common_handlers import execute_modem_command, execute_modem_command_and_print_result
import src.gui.handlers.common_handlers as common_handlers # Importa o módulo para acessar as globais

def handle_get_signal_quality_event():
    """Handler para o botão 'Qualidade Sinal' (AT+CSQ)."""
    execute_modem_command_and_print_result(common_handlers.modem_controller.get_signal_quality)

def handle_get_network_info_event():
    """Handler para o botão 'Info Rede' (AT+QNWINFO)."""
    execute_modem_command_and_print_result(common_handlers.modem_controller.get_network_info)

def handle_get_network_registration_status_event():
    """Handler para o botão 'Status Registro' (AT+CREG?)."""
    execute_modem_command_and_print_result(common_handlers.modem_controller.get_network_registration_status)

def handle_define_apn_event(values):
    """Handler para o botão 'Definir APN' (AT+CGDCONT)."""
    try:
        cid = int(values['-APN_CID-'])
        pdp_type = values['-APN_PDP_TYPE-']
        apn_name = values['-APN_NAME-']
        pdp_addr = values['-APN_PDP_ADDR-'].strip()
        data_comp = int(values['-APN_DATA_COMP-'])
        head_comp = int(values['-APN_HEAD_COMP-'])
        execute_modem_command(common_handlers.modem_controller.define_apn, cid, pdp_type, apn_name, pdp_addr, data_comp, head_comp)
    except ValueError:
        print("Erro: Verifique os valores de configuração APN (CID, compressões devem ser números inteiros).")

def handle_activate_pdp_event(values):
    """Handler para o botão 'Ativar PDP' (AT+CGACT)."""
    try:
        cid = int(values['-APN_CID-'])
        execute_modem_command(common_handlers.modem_controller.activate_pdp_context, cid)
    except ValueError:
        print("Erro: CID deve ser um número inteiro para ativar o PDP.")

def handle_deactivate_pdp_event(values):
    """Handler para o botão 'Desativar PDP' (AT+CGACT)."""
    try:
        cid = int(values['-APN_CID-'])
        execute_modem_command(common_handlers.modem_controller.deactivate_pdp_context, cid)
    except ValueError:
        print("Erro: CID deve ser um número inteiro para desativar o PDP.")

def handle_get_pdp_address_event(values):
    """Handler para o botão 'Endereço PDP' (AT+CGPADDR)."""
    try:
        cid_str = values['-APN_CID-'].strip()
        cid = int(cid_str) if cid_str.isdigit() else None
        execute_modem_command_and_print_result(common_handlers.modem_controller.get_pdp_address, cid)
    except ValueError:
        print("Erro: CID PDP deve ser um número inteiro ou vazio para todos.")

def handle_set_scan_mode_event(values):
    """Handler para o botão 'Definir Modo Varredura' (AT+QCFG="nwscanmode")."""
    scanmode_str = values['-SCAN_MODE_SET-'].split(' ')[0]
    try:
        scanmode = int(scanmode_str)
        effect = int(values['-FREQ_EFFECT-'])
        execute_modem_command(common_handlers.modem_controller.set_network_scan_mode, scanmode, effect)
    except ValueError:
        print("Erro: Modo de varredura ou efeito inválido. Selecione um valor numérico válido.")

def handle_get_scan_mode_event():
    """Handler para o botão 'Ler Modo Varredura' (AT+QCFG="nwscanmode")."""
    execute_modem_command_and_print_result(common_handlers.modem_controller.get_network_scan_mode)

def handle_set_roaming_event(values):
    """Handler para o botão 'Definir Roaming' (AT+QCFG="roamservice")."""
    roammode_str = values['-ROAM_MODE_SET-'].split(' ')[0]
    try:
        roammode = int(roammode_str)
        effect = int(values['-ROAM_EFFECT-'])
        execute_modem_command(common_handlers.modem_controller.set_roaming_service, roammode, effect)
    except ValueError:
        print("Erro: Modo de roaming ou efeito inválido. Selecione um valor numérico válido.")

def handle_get_roaming_event():
    """Handler para o botão 'Ler Roaming' (AT+QCFG="roamservice")."""
    execute_modem_command_and_print_result(common_handlers.modem_controller.get_roaming_service)

def handle_set_bands_event(values):
    """Handler para o botão 'Definir Bandas' (AT+QCFG="band")."""
    try:
        gsm_wcdma_band = values['-BAND_GSM_WCDMA-'].strip()
        lte_band = values['-BAND_LTE-'].strip()
        tdscdma_band = values['-BAND_TDSCDMA-'].strip()
        effect = int(values['-FREQ_EFFECT-']) # Reutiliza o campo 'Efeito' da seção de frequência
        execute_modem_command(common_handlers.modem_controller.set_band_configuration, gsm_wcdma_band, lte_band, tdscdma_band, effect)
    except ValueError:
        print("Erro: Verifique os valores hexadecimais das bandas e o efeito (deve ser 0 ou 1).")

def handle_get_bands_event():
    """Handler para o botão 'Ler Bandas' (AT+QCFG="band"?)."""
    execute_modem_command_and_print_result(common_handlers.modem_controller.get_band_configuration)
