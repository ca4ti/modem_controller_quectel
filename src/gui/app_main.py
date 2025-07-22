# src/gui/app_main.py
import PySimpleGUI as sg
import threading
import datetime
import time
import re
import serial.tools.list_ports # Importar explicitamente aqui para get_available_ports
import json # Importar explicitamente aqui para ALL_MANUAL_COMMANDS
import os # Importar explicitamente aqui para ALL_MANUAL_COMMANDS

# O sys.path já é manipulado em src/main.py. Não precisa de manipulação aqui.

# Importações de módulos do projeto.
# Todas as importações de pacotes internos DEVEM ser absolutas a partir de 'src'.

from src.gui.layout import create_gui_layout
from src.gui.update_gui_elements import update_button_states
from src.gui.urc_monitor import UrcMonitor

from src.modem.controller import ModemController 
from src.config.commands_data import ALL_MANUAL_COMMANDS # Onde ALL_MANUAL_COMMANDS é definido

# Importa todos os handlers específicos de cada aba.
import src.gui.handlers.common_handlers as common_handlers
import src.gui.handlers.basic_control_handlers as basic_control_handlers
import src.gui.handlers.info_status_handlers as info_status_handlers
import src.gui.handlers.network_apn_handlers as network_apn_handlers
import src.gui.handlers.sms_handlers as sms_handlers
import src.gui.handlers.calls_handlers as calls_handlers
import src.gui.handlers.audio_handlers as audio_handlers
import src.gui.handlers.gps_usb_handlers as gps_usb_handlers
import src.gui.handlers.summary_handlers as summary_handlers
import src.gui.handlers.custom_commands_handlers as custom_commands_handlers

# Funções _execute_command, _execute_command_print_result e gui_update_event são do threading_utils.
# get_available_ports é do serial_ports.
# Como elas são usadas no main loop (que é o app_main), precisamos importá-las aqui também.
from src.utils.threading_utils import _execute_command, _execute_command_print_result, gui_update_event
from src.utils.serial_ports import get_available_ports 


def main():
    """
    Função principal que inicializa a GUI e lida com os eventos.
    """
    # As variáveis globais modem_controller, connected
    # são gerenciadas e acessadas via src.gui.handlers.common_handlers.
    # Não precisamos declará-las 'global' aqui, apenas acessá-las via common_handlers.

    available_ports = get_available_ports()
    window = create_gui_layout(available_ports)
    update_button_states(window) 

    # Loop de eventos da GUI
    while True:
        event, values = window.read()

        # Lida com o fechamento da janela
        if event == sg.WIN_CLOSED:
            break

        # Captura da tecla Enter globalmente na janela
        if event == '\r' and common_handlers.connected:
            if window.find_element_with_focus() == window['-CUSTOM_AT_COMMAND-']:
                custom_commands_handlers.handle_send_custom_cmd_event(values, window)
                continue # Evita que o evento seja processado novamente


        # --- Eventos de Conexão/Desconexão ---
        if event == '-CONNECT-':
            common_handlers.handle_connect_event(window, values)
        elif event == '-DISCONNECT-':
            common_handlers.handle_disconnect_event(window)
        elif event == '-UPDATE_BUTTON_STATES-':
            update_button_states(window, values[event]) 
        elif event == '-REFRESH_PORTS-':
            common_handlers.handle_refresh_ports_event(window)
        elif event == '-AUTO_DISCOVER-':
            common_handlers.handle_auto_discover_event(window)
        elif event == '-PORT_UPDATE_EVENT-': 
            window['-PORT-'].update(values=values[event], set_to_index=0 if values[event] else None)
        elif event == '-PORT_SELECTION_UPDATE-': 
            window['-PORT-'].update(value=values[event])
            
        # --- Eventos de URC (Unsolicited Result Code) ---
        elif event.startswith('-URC_'): # Verifica se o evento é um URC (prefixo definido em urc_monitor)
            timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S") # Formato completo para log
            urc_event_key = event # Ex: '-URC_RING-'
            payload = values[urc_event_key] # Payload contém os grupos capturados pelo regex

            urc_log_message = "" # Inicializa a mensagem do log

            # --- Lógica de Pop-ups e Formatação de Log de URCs ---
            if urc_event_key == '-URC_RING-':
                urc_log_message = f"[{timestamp}] Chamada Recebida: RING"
                sg.popup_timed(f"Chamada Recebida!", title="CHAMADA", keep_on_top=True, background_color='yellow', text_color='black')
            elif urc_event_key == '-URC_SMS_RECEIVED-':
                mem, idx = payload
                urc_log_message = f"[{timestamp}] Novo SMS na Memória: '{mem}', Índice {idx}"
                sg.popup_timed(f"Novo SMS recebido!", title="NOVO SMS", keep_on_top=True, background_color='lightblue', text_color='black')
            elif urc_event_key == '-URC_SMS_DIRECT-':
                # payload: ('+8615012345678', '', '13/03/18,17:07:21+32', 'This is a test message.')
                number = payload[0] if len(payload) > 0 else 'N/A'
                content = payload[3] if len(payload) > 3 else 'N/A'
                urc_log_message = f"[{timestamp}] SMS Direto de {number}:\n{content.strip()}"
                sg.popup_scrolled(f"SMS de: {number}\nData/Hora: {payload[2] if len(payload) > 2 else 'N/A'}\n\n{content.strip()}", 
                                  title=f"SMS de {number}", size=(50, 15), keep_on_top=True, background_color='lightgreen', text_color='black')
            elif urc_event_key == '-URC_SIM_STATUS-':
                enable_stat, inserted_stat = payload
                sim_status_desc = {0: "Removido", 1: "Inserido", 2: "Desconhecido"}.get(int(inserted_stat), "Desconhecido")
                urc_log_message = f"[{timestamp}] Status do SIM: {sim_status_desc} (Relatório: {'Habilitado' if enable_stat == '1' else 'Desabilitado'})"
                sg.popup_timed(f"Status do SIM: {sim_status_desc}", title="STATUS SIM", keep_on_top=True, background_color='lightgray', text_color='black')
            elif urc_event_key == '-URC_SIGNAL_QUALITY_CHANGE-':
                rssi, ber = payload
                urc_log_message = f"[{timestamp}] Qualidade do Sinal Alterada: RSSI={rssi}, BER={ber}"
                sg.popup_timed(f"Sinal Alterado: RSSI {rssi}, BER {ber}", title="QUALIDADE SINAL", keep_on_top=True, background_color='lightyellow', text_color='black')
            elif urc_event_key == '-URC_NETWORK_REG_CHANGE-' or urc_event_key == '-URC_NETWORK_REG_EXT_CHANGE-':
                stat_code = int(payload[1]) # O status é sempre o segundo elemento
                stat_desc = {
                    0: "Não registrado, ME não buscando", 1: "Registrado, rede de origem",
                    2: "Não registrado, ME buscando", 3: "Registro negado",
                    4: "Desconhecido", 5: "Registrado, roaming"
                }.get(stat_code, "Desconhecido")
                
                detail_msg = f"Rede: {stat_desc}"
                if len(payload) > 2: # Se for URC estendido, terá mais detalhes
                    lac = payload[2] if len(payload) > 2 else 'N/A'
                    ci = payload[3] if len(payload) > 3 else 'N/A'
                    act = payload[4] if len(payload) > 4 else 'N/A'
                    act_desc = {
                        "0": "GSM", "2": "UTRAN", "3": "GSM W/EGPRS", "4": "UTRAN W/HSDPA",
                        "5": "UTRAN W/HSUPA", "6": "UTRAN W/HSDPA and HSUPA", "7": "E-UTRAN"
                    }.get(act, "N/A")
                    detail_msg += f" (LAC: {lac}, CI: {ci}, Tech: {act_desc})"

                urc_log_message = f"[{timestamp}] Registro Rede: {detail_msg}"
                sg.popup_timed(f"Registro de Rede: {detail_msg}", title="REGISTRO REDE", keep_on_top=True, background_color='lightcoral', text_color='white')
            else:
                urc_log_message = f"[{timestamp}] URC Desconhecido: {urc_event_key}, Payload: {payload}"

            # Adiciona a mensagem formatada ao Multiline de URCs na aba "Logs de URCs"
            window['-URC_LOG_OUTPUT-'].print(urc_log_message, end='\n') 
            # Opcional: manter no log principal para depuração geral também.
            # print(f"URC Evento: {urc_event_key}, Payload: {payload}") 


        # --- Lidar com outros Eventos (Comandos AT) ---
        if common_handlers.connected:
            if event == '-POWER_OFF-':
                common_handlers.execute_modem_command(common_handlers.modem_controller.power_off)
            elif event == '-REBOOT-':
                common_handlers.execute_modem_command(common_handlers.modem_controller.reboot)
            elif event == '-FACTORY_RESET-':
                common_handlers.execute_modem_command(common_handlers.modem_controller.factory_reset)
            
            elif event == '-SET_URC_PORT-':
                port_value = values['-URC_PORT_SET-']
                common_handlers.execute_modem_command(common_handlers.modem_controller.set_urc_output_port, port_value)
            elif event == '-GET_URC_PORT-':
                common_handlers.execute_modem_command_and_print_result(common_handlers.modem_controller.get_urc_output_port)


            elif event == '-GET_PRODUCT_INFO-':
                common_handlers.execute_modem_command_and_print_result(common_handlers.modem_controller.get_product_info)
            elif event == '-GET_IMEI-':
                common_handlers.execute_modem_command_and_print_result(common_handlers.modem_controller.get_imei)
            elif event == '-GET_IMSI-':
                common_handlers.execute_modem_command_and_print_result(common_handlers.modem_controller.get_imsi)
            elif event == '-GET_ICCID-':
                common_handlers.execute_modem_command_and_print_result(common_handlers.modem_controller.get_iccid)
            elif event == '-GET_SIM_STATUS-':
                common_handlers.execute_modem_command_and_print_result(common_handlers.modem_controller.get_sim_status)
            elif event == '-GET_BATTERY_STATUS-':
                common_handlers.execute_modem_command_and_print_result(common_handlers.modem_controller.get_battery_status)
            elif event == '-GET_CLOCK-':
                common_handlers.execute_modem_command_and_print_result(common_handlers.modem_controller.get_clock)
            elif event == '-GET_ADC_VALUE-':
                info_status_handlers.handle_get_adc_value_event(values) # Usando handler específico
            
            elif event == '-GET_SIGNAL_QUALITY-':
                network_apn_handlers.handle_get_signal_quality_event() # Usando handler específico
            elif event == '-GET_NETWORK_INFO-':
                network_apn_handlers.handle_get_network_info_event() # Usando handler específico
            elif event == '-GET_NETWORK_REGISTRATION_STATUS-':
                network_apn_handlers.handle_get_network_registration_status_event() # Usando handler específico
            elif event == '-DEFINE_APN-':
                network_apn_handlers.handle_define_apn_event(values) # Usando handler específico
            elif event == '-ACTIVATE_PDP-':
                network_apn_handlers.handle_activate_pdp_event(values) # Usando handler específico
            elif event == '-DEACTIVATE_PDP-':
                network_apn_handlers.handle_deactivate_pdp_event(values) # Usando handler específico
            elif event == '-GET_PDP_ADDRESS-':
                network_apn_handlers.handle_get_pdp_address_event(values) # Usando handler específico
            elif event == '-SET_SCAN_MODE-':
                network_apn_handlers.handle_set_scan_mode_event(values) # Usando handler específico
            elif event == '-GET_SCAN_MODE-':
                network_apn_handlers.handle_get_scan_mode_event() # Usando handler específico
            elif event == '-SET_ROAMING-':
                network_apn_handlers.handle_set_roaming_event(values) # Usando handler específico
            elif event == '-GET_ROAMING-':
                network_apn_handlers.handle_get_roaming_event() # Usando handler específico
            elif event == '-SET_BANDS-':
                network_apn_handlers.handle_set_bands_event(values) # Usando handler específico
            elif event == '-GET_BANDS-':
                network_apn_handlers.handle_get_bands_event() # Usando handler específico

            elif event == '-SEND_SMS-':
                sms_handlers.handle_send_sms_event(values) # Usando handler específico
            elif event == '-READ_ALL_SMS-':
                sms_handlers.handle_read_all_sms_event() # Usando handler específico
            elif event == '-READ_SMS_BY_INDEX-':
                sms_handlers.handle_read_sms_by_index_event(values) # Usando handler específico
            elif event == '-DELETE_ALL_SMS-':
                sms_handlers.handle_delete_all_sms_event() # Usando handler específico
            elif event == '-DELETE_SMS_BY_INDEX-':
                sms_handlers.handle_delete_sms_by_index_event(values) # Usando handler específico

            # --- Eventos da Aba SMS Avançado ---
            elif event == '-REFRESH_SMS_INBOX-':
                sms_handlers.handle_refresh_sms_inbox_event(window)
            elif event == '-REFRESH_SMS_OUTBOX-':
                sms_handlers.handle_refresh_sms_outbox_event(window)
            elif event == '-DELETE_ALL_SMS_ADVANCED-':
                sms_handlers.handle_delete_all_sms_advanced_event(window)
            # Eventos para atualização de output das caixas de entrada/saída (chamados por write_event_value)
            elif event == '-UPDATE_SMS_INBOX_OUTPUT-':
                window['-SMS_INBOX_OUTPUT-'].update(values[event])
            elif event == '-UPDATE_SMS_OUTBOX_OUTPUT-':
                window['-SMS_OUTBOX_OUTPUT-'].update(values[event])

            elif event == '-DIAL_CALL-':
                calls_handlers.handle_dial_call_event(values) # Usando handler específico
            elif event == '-ANSWER_CALL-':
                calls_handlers.handle_answer_call_event() # Usando handler específico
            elif event == '-HANGUP_CALL-':
                calls_handlers.handle_hangup_call_event() # Usando handler específico
            elif event == '-CALL_STATUS-':
                calls_handlers.handle_get_call_status_event() # Usando handler específico

            elif event == '-SET_VOLUME-':
                audio_handlers.handle_set_volume_event(values) # Usando handler específico
            elif event == '-MUTE_MIC_ON-':
                audio_handlers.handle_mute_mic_on_event() # Usando handler específico
            elif event == '-MUTE_MIC_OFF-':
                audio_handlers.handle_mute_mic_off_event() # Usando handler específico
            elif event == '-LOOP_AUDIO_ON-':
                audio_handlers.handle_loop_audio_on_event() # Usando handler específico
            elif event == '-LOOP_AUDIO_OFF-':
                audio_handlers.handle_disable_audio_loop_test() # Usando handler específico
            elif event == '-SET_AUDIO_MODE-':
                audio_handlers.handle_set_audio_mode_event(values) # Usando handler específico
            elif event == '-GET_AUDIO_MODE-':
                audio_handlers.handle_get_audio_mode_event() # Usando handler específico
            elif event == '-SET_MIC_GAINS-':
                audio_handlers.handle_set_mic_gains_event(values) # Usando handler específico
            elif event == '-GET_MIC_GAINS-':
                audio_handlers.handle_get_mic_gains_event() # Usando handler específico
            elif event == '-SET_RX_GAINS-':
                audio_handlers.handle_set_rx_gains_event(values) # Usando handler específico
            elif event == '-GET_RX_GAINS-':
                audio_handlers.handle_get_rx_gains_event() # Usando handler específico
            elif event == '-CONFIG_DAI-':
                audio_handlers.handle_config_dai_event(values) # Usando handler específico
            
            elif event == '-ENABLE_GPS-':
                gps_usb_handlers.handle_enable_gps_event() # Usando handler específico
            elif event == '-DISABLE_GPS-':
                gps_usb_handlers.handle_disable_gps_event() # Usando handler específico
            elif event == '-GET_GPS_LOCATION-':
                gps_usb_handlers.handle_get_gps_location_event() # Usando handler específico
            elif event == '-SET_GPS_OUTPORT-':
                gps_usb_handlers.handle_set_gps_outport_event(values) # Usando handler específico
            elif event == '-GET_GPS_OUTPORT-':
                gps_usb_handlers.handle_get_gps_outport_event() # Usando handler específico
            elif event == '-GET_USBCFG-':
                gps_usb_handlers.handle_get_usb_configuration_event() # Usando handler específico
            elif event == '-ENABLE_QPCMV-':
                gps_usb_handlers.handle_enable_voice_over_usb_event(values) # Usando handler específico
            elif event == '-DISABLE_QPCMV-':
                gps_usb_handlers.handle_disable_voice_over_usb_event() # Usando handler específico
            elif event == '-GET_QPCMV_STATUS-':
                gps_usb_handlers.handle_get_voice_over_usb_status_event() # Usando handler específico

            elif event == '-GENERATE_SUMMARY-':
                summary_handlers.handle_generate_summary_event(window) # Usando handler específico
            elif event == '-UPDATE_SUMMARY_OUTPUT-':
                summary_handlers.update_summary_output(window, values[event]) # Usando handler específico

            elif event == '-SEND_CUSTOM_CMD-': 
                custom_commands_handlers.handle_send_custom_cmd_event(values, window) # Usando handler específico
            elif event == '-COMMAND_LIST-': 
                custom_commands_handlers.handle_command_list_selection_event(window, values) # Usando handler específico
            elif event == '-COPY_SELECTED_CMD-':
                custom_commands_handlers.handle_copy_selected_cmd_event(window, values) # Usando handler específico
            elif event == '-COMMAND_FILTER-':
                custom_commands_handlers.handle_command_filter_event(window, values) # Usando handler específico
            elif event == '-CUSTOM_AT_COMMAND_CLEAR-':
                custom_commands_handlers.clear_custom_command_input(window) # Usando handler específico
        
        elif event == '-COPY_LOG-':
            log_content = window['-OUTPUT-'].get()
            if log_content:
                sg.clipboard_set(log_content)
                print("Conteúdo do console copiado para a área de transferência.")
            else:
                print("Console vazio. Nada para copiar.")
        elif event == '-SAVE_LOG-':
            log_content = window['-OUTPUT-'].get()
            if log_content:
                timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
                filename = f"modem_log_{timestamp}.txt"
                try:
                    with open(filename, 'w', encoding='utf-8') as f:
                        f.write(log_content)
                    print(f"Log salvo em: {filename}")
                except Exception as e:
                    print(f"Erro ao salvar log: {e}")
            else:
                print("Console vazio. Nada para salvar.")


    # Garante que a porta serial seja fechada ao sair da aplicação
    if common_handlers.modem_controller:
        common_handlers.modem_controller.disconnect_modem()
    if common_handlers.urc_monitor_instance: # NOVO: Garante que o monitor de URCs também pare
        common_handlers.urc_monitor_instance.stop_monitoring()
    window.close() # Fecha a janela PySimpleGUI

# Funções auxiliares _execute_command, _execute_command_print_result e gui_update_event são definidas em utils.threading_utils
# Não são mais definidas aqui.
# A função get_available_ports é definida em utils.serial_ports.

# Ponto de entrada principal do script
if __name__ == '__main__':
    main()
