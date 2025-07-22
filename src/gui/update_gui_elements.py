# src/gui/update_gui_elements.py
import PySimpleGUI as sg

# Variável global para rastrear o estado da conexão
connected = False # Esta variável será atualizada pelo common_handlers

def update_button_states(window, connected_status_from_thread=None):
    """
    Atualiza o estado (habilitado/desabilitado) de todos os botões da GUI
    com base no estado da conexão do modem.
    :param window: O objeto da janela PySimpleGUI.
    :param connected_status_from_thread: Opcional. Booleano indicando se o modem está conectado,
                                          usado quando a chamada vem de uma thread para atualizar a GUI.
    """
    global connected # Acessa a variável global 'connected'

    # Se a chamada veio da thread de conexão, atualiza o estado global 'connected'
    if connected_status_from_thread is not None:
        connected = connected_status_from_thread

    window['-CONNECT-'].update(disabled=connected)
    window['-DISCONNECT-'].update(disabled=not connected)

    # Lista de todos os botões que dependem do estado da conexão
    control_buttons = [
        # Conexão e Básico
        '-POWER_OFF-', '-REBOOT-', '-FACTORY_RESET-',
        '-SET_URC_PORT-', '-GET_URC_PORT-',
        # Informações e Status do Modem
        '-GET_PRODUCT_INFO-', '-GET_IMEI-', '-GET_IMSI-', '-GET_ICCID-',
        '-GET_BATTERY_STATUS-', '-GET_CLOCK-', '-GET_ADC_VALUE-',
        '-GET_SIM_STATUS-',
        # Rede e APN
        '-GET_SIGNAL_QUALITY-', '-GET_NETWORK_INFO-', '-GET_NETWORK_REGISTRATION_STATUS-',
        '-DEFINE_APN-', '-ACTIVATE_PDP-', '-DEACTIVATE_PDP-', '-GET_PDP_ADDRESS-',
        '-SET_BANDS-', '-GET_BANDS-',
        '-SET_SCAN_MODE-', '-GET_SCAN_MODE-',
        '-SET_ROAMING-', '-GET_ROAMING-',
        # SMS
        '-SEND_SMS-', '-READ_SMS_BY_INDEX-', '-DELETE_SMS_BY_INDEX-',
        '-READ_ALL_SMS-', '-DELETE_ALL_SMS-',
        # Chamadas
        '-DIAL_CALL-', '-HANGUP_CALL-', '-ANSWER_CALL-', '-CALL_STATUS-',
        # Áudio
        '-SET_VOLUME-', '-MUTE_MIC_ON-', '-MUTE_MIC_OFF-',
        '-LOOP_AUDIO_ON-', '-LOOP_AUDIO_OFF-', '-SET_AUDIO_MODE-', '-GET_AUDIO_MODE-',
        '-SET_MIC_GAINS-', '-GET_MIC_GAINS-', '-SET_RX_GAINS-', '-GET_RX_GAINS-',
        '-CONFIG_DAI-',
        # GPS & Interfaces USB
        '-ENABLE_GPS-', '-DISABLE_GPS-', '-GET_GPS_LOCATION-',
        '-SET_GPS_OUTPORT-', '-GET_GPS_OUTPORT-',
        '-GET_USBCFG-',
        '-ENABLE_QPCMV-', '-DISABLE_QPCMV-', '-GET_QPCMV_STATUS-',
        # Sumário do Modem
        '-GENERATE_SUMMARY-',
        # Comandos Personalizados
        '-SEND_CUSTOM_CMD-',
    ]
    for button_key in control_buttons:
        window[button_key].update(disabled=not connected)

    # O botão "Ligar Modem (Hardware)" é um lembrete visual e não um comando direto
    window['-POWER_ON-'].update(disabled=connected)

    # Habilitar/desabilitar botão de cópia de comando personalizado
    window['-COPY_SELECTED_CMD-'].update(disabled=not connected)

    # Botão Auto-Discover
    window['-AUTO_DISCOVER-'].update(disabled=connected)

    # Botões de log (Copiar/Salvar) sempre devem estar habilitados para que o usuário possa salvar a saída atual
    window['-COPY_LOG-'].update(disabled=False)
    window['-SAVE_LOG-'].update(disabled=False)
