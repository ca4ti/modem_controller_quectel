# src/gui/layout.py
import PySimpleGUI as sg
from src.config.commands_data import ALL_MANUAL_COMMANDS # Importa a lista de comandos do manual

def create_gui_layout(modem_ports):
    """
    Cria o layout da interface gráfica principal usando PySimpleGUI com abas.
    :param modem_ports: Lista de strings com as portas seriais disponíveis.
    :return: Objeto PySimpleGUI.Window configurado.
    """
    sg.theme('LightBlue3') # Tema visual da janela

    # --- Aba: Conexão e Controle Básico ---
    tab_connection_control_layout = [
        [sg.Frame('Conexão Serial', [
            [sg.Text('Porta Serial:'), 
             sg.Combo(values=modem_ports, default_value=modem_ports[0] if modem_ports else '', key='-PORT-', enable_events=True, readonly=True, tooltip='Selecione a porta serial do modem.'),
             sg.Button('Atualizar Portas', key='-REFRESH_PORTS-', tooltip='Atualiza a lista de portas seriais disponíveis.'),
             sg.Button('Auto-Discover', key='-AUTO_DISCOVER-', tooltip='Tenta encontrar e conectar-se ao modem automaticamente em todas as portas disponíveis.')],
            [sg.Text('Baudrate:'), sg.Input(default_text='115200', size=(10,1), key='-BAUDRATE-', tooltip='Taxa de transmissão da comunicação serial.')],
            [sg.Button('Conectar', key='-CONNECT-', tooltip='Estabelece conexão com o modem.'), sg.Button('Desconectar', key='-DISCONNECT-', disabled=True, tooltip='Fecha a conexão com o modem.')]
        ])],
        [sg.Frame('Controle Básico do Modem', [
            [sg.Button('Desligar Modem', key='-POWER_OFF-', disabled=True, tooltip='Desliga o modem de forma segura (AT+QPOWD).'),
             sg.Button('Ligar Modem (Hardware)', key='-POWER_ON-', disabled=True, tooltip='Ligar o modem geralmente requer ação física (botão/pino PWRKEY). Este botão é um lembrete visual.')],
            [sg.Button('Reiniciar Modem', key='-REBOOT-', disabled=True, tooltip='Reinicia o modem para funcionalidade total (AT+CFUN=1,1).'),
             sg.Button('Resetar Fábrica', key='-FACTORY_RESET-', disabled=True, tooltip='Restaura as configurações padrão de fábrica (AT&F).')]
        ]),
        sg.Frame('Configuração de Portas / URCs', [ 
            [sg.Text('Porta de Saída de URCs:'), sg.Combo(values=["usbat", "usbmodem", "uart1"], default_value="usbat", key='-URC_PORT_SET-', size=(10,1), readonly=True, tooltip='Define a porta para onde os URCs (Unsolicited Result Codes) serão enviados.')],
            [sg.Button('Definir Porta URC', key='-SET_URC_PORT-', disabled=True, tooltip='Configura a porta de saída para URCs (AT+QURCCFG="urcport").'),
             sg.Button('Ler Porta URC', key='-GET_URC_PORT-', disabled=True, tooltip='Lê a porta de saída de URCs atual.')]
        ])]
    ]

    # --- Aba: Informações e Status do Modem ---
    tab_info_status_layout = [
        [sg.Button('Info Produto', key='-GET_PRODUCT_INFO-', disabled=True, tooltip='Obtém informações de identificação do produto (ATI).'),
         sg.Button('IMEI', key='-GET_IMEI-', disabled=True, tooltip='Obtém o International Mobile Equipment Identity (IMEI) do modem (AT+CGSN).'),
         sg.Button('IMSI', key='-GET_IMSI-', disabled=True, tooltip='Obtém o International Mobile Subscriber Identity (IMSI) do SIM (AT+CIMI).'),
         sg.Button('ICCID', key='-GET_ICCID-', disabled=True, tooltip='Obtém o Integrated Circuit Card Identifier (ICCID) do SIM (AT+QCCID).'),
         sg.Button('Status SIM', key='-GET_SIM_STATUS-', disabled=True, tooltip='Obtém o status de inserção do cartão SIM (AT+QSIMSTAT?).')], 
        [sg.Button('Status Bateria', key='-GET_BATTERY_STATUS-', disabled=True, tooltip='Obtém status de carga e nível da bateria (AT+CBC).'),
         sg.Button('Hora/Data', key='-GET_CLOCK-', disabled=True, tooltip='Obtém a hora e data do relógio interno do modem (AT+CCLK).')],
        [sg.Text('ADC Canal:'), sg.Combo(values=[0, 1], default_value=0, key='-ADC_CHANNEL-', size=(5,1), readonly=True, tooltip='Selecione o canal ADC para leitura.'),
         sg.Button('Ler ADC', key='-GET_ADC_VALUE-', disabled=True, tooltip='Lê o valor de voltagem de um canal ADC (AT+QADC).')]
    ]

    # --- Aba: Rede e APN ---
    tab_network_apn_layout = [
        [sg.Button('Qualidade Sinal', key='-GET_SIGNAL_QUALITY-', disabled=True, tooltip='Obtém a qualidade do sinal (RSSI e BER) (AT+CSQ).'),
         sg.Button('Info Rede', key='-GET_NETWORK_INFO-', disabled=True, tooltip='Consulta informações da rede (tecnologia, operador, banda) (AT+QNWINFO).'),
         sg.Button('Status Registro', key='-GET_NETWORK_REGISTRATION_STATUS-', disabled=True, tooltip='Obtém o status de registro na rede (AT+CREG?).')],
        [sg.Frame('Configurar APN (PDP Context)', [
            [sg.Text('CID:'), sg.Input(default_text='1', size=(3,1), key='-APN_CID-', tooltip='PDP Context Identifier (1-255).')],
            [sg.Text('PDP Type:'), sg.Combo(values=['IP', 'PPP', 'IPV6', 'IPV4V6'], default_value='IP', key='-APN_PDP_TYPE-', readonly=True, tooltip='Tipo de protocolo de dados de pacote.')],
            [sg.Text('APN:'), sg.Input(key='-APN_NAME-', size=(20,1), tooltip='Access Point Name fornecido pela operadora.')],
            [sg.Text('PDP Addr (opc):'), sg.Input(key='-APN_PDP_ADDR-', size=(15,1), tooltip='Endereço IP estático, se houver (opcional).')],
            [sg.Text('Data Comp:'), sg.Combo(values=[0, 1], default_value=0, key='-APN_DATA_COMP-', readonly=True, tooltip='Compressão de dados (0=Off, 1=On).')],
            [sg.Text('Head Comp:'), sg.Combo(values=[0, 1], default_value=0, key='-APN_HEAD_COMP-', readonly=True, tooltip='Compressão de cabeçalho (0=Off, 1=On).')],
            [sg.Button('Definir APN', key='-DEFINE_APN-', disabled=True, tooltip='Define os parâmetros do contexto PDP (AT+CGDCONT).'),
             sg.Button('Ativar PDP', key='-ACTIVATE_PDP-', disabled=True, tooltip='Ativa o contexto PDP (AT+CGACT).'),
             sg.Button('Desativar PDP', key='-DEACTIVATE_PDP-', disabled=True, tooltip='Desativa o contexto PDP (AT+CGACT).'),
             sg.Button('Endereço PDP', key='-GET_PDP_ADDRESS-', disabled=True, tooltip='Obtém o endereço IP do contexto PDP (AT+CGPADDR).')]
        ])],
        [sg.Frame('Configurar Frequência e Roaming', [ 
            [sg.Text('Modo Varredura (Freq):'), sg.Combo(values=['0 (Auto)', '1 (2G Only)', '2 (3G Only)', '3 (4G Only)'], default_value='0 (Auto)', key='-SCAN_MODE_SET-', size=(15,1), readonly=True, tooltip='Define a preferência de tecnologia de rede (AT+QCFG="nwscanmode").')],
            [sg.Text('Efeito (0=Reboot, 1=Imediato):'), sg.Combo(values=[0, 1], default_value=1, key='-FREQ_EFFECT-', readonly=True, tooltip='Define quando a configuração de frequência terá efeito.')],
            [sg.Button('Definir Modo Varredura', key='-SET_SCAN_MODE-', disabled=True, tooltip='Configura a preferência de frequência.'),
             sg.Button('Ler Modo Varredura', key='-GET_SCAN_MODE-', disabled=True, tooltip='Lê a preferência de frequência atual.')],
            [sg.HorizontalSeparator()],
            [sg.Text('Serviço de Roaming:'), sg.Combo(values=['0 (Disable)', '1 (Enable)', '255 (AUTO)'], default_value='1 (Enable)', key='-ROAM_MODE_SET-', size=(15,1), readonly=True, tooltip='Habilita/Desabilita o serviço de roaming (AT+QCFG="roamservice").')],
            [sg.Text('Efeito (0=Reboot, 1=Imediato):'), sg.Combo(values=[0, 1], default_value=1, key='-ROAM_EFFECT-', readonly=True, tooltip='Define quando a configuração de roaming terá efeito.')],
            [sg.Button('Definir Roaming', key='-SET_ROAMING-', disabled=True, tooltip='Configura o serviço de roaming.'),
             sg.Button('Ler Roaming', key='-GET_ROAMING-', disabled=True, tooltip='Lê a configuração de roaming atual.')],
            [sg.HorizontalSeparator()],
            [sg.Text('Bandas GSM/WCDMA (Hex):'), sg.Input(default_text='00000000', size=(10,1), key='-BAND_GSM_WCDMA-', tooltip='Valor hexadecimal para bandas GSM/WCDMA. Use "00000000" para não alterar.')],
            [sg.Text('LTE (Hex):'), sg.Input(default_text='0x40000000', size=(10,1), key='-BAND_LTE-', tooltip='Valor hexadecimal para bandas LTE. Use "0x40000000" para não alterar.')],
            [sg.Text('TD-SCDMA (Hex):'), sg.Input(default_text='0x40000000', size=(10,1), key='-BAND_TDSCDMA-', tooltip='Valor hexadecimal para bandas TD-SCDMA. Use "0x40000000" para não alterar.')],
            [sg.Button('Definir Bandas', key='-SET_BANDS-', disabled=True, tooltip='Configura as bandas de frequência preferenciais (AT+QCFG="band").'),
             sg.Button('Ler Bandas', key='-GET_BANDS-', disabled=True, tooltip='Lê as configurações de banda atuais (AT+QCFG="band"?).')]
        ])]
    ]

    # --- Aba: Serviço de Mensagens (SMS) ---
    tab_sms_layout = [
        # Linha para inserir os números de telefone para envio, agora permitindo múltiplos
        [sg.Text('Número(s) Destino:'), sg.Input(key='-SMS_NUMBER-', size=(40,1), tooltip='Número(s) de telefone para enviar SMS (separe com vírgulas para múltiplos).')],
        [sg.Text('Mensagem:'), sg.Input(key='-SMS_MESSAGE-', size=(40,1), tooltip='Conteúdo da mensagem SMS.')],
        [sg.Button('Enviar SMS', key='-SEND_SMS-', disabled=True, tooltip='Envia um SMS (AT+CMGS).')],
        [sg.Text('Índice SMS:'), sg.Input(key='-SMS_INDEX-', size=(5,1), tooltip='Índice da mensagem na memória para leitura/deleção.'),
         sg.Button('Ler SMS por Índice', key='-READ_SMS_BY_INDEX-', disabled=True, tooltip='Lê uma mensagem SMS específica pelo índice (AT+CMGR).'),
         sg.Button('Apagar SMS por Índice', key='-DELETE_SMS_BY_INDEX-', disabled=True, tooltip='Apaga uma mensagem SMS específica pelo índice (AT+CMGD).')],
        [sg.Button('Ler Todas SMS', key='-READ_ALL_SMS-', disabled=True, tooltip='Lê todas as mensagens SMS da memória (AT+CMGL="ALL").'),
         sg.Button('Apagar Todas SMS', key='-DELETE_ALL_SMS-', disabled=True, tooltip='Apaga todas as mensagens SMS da memória (AT+CMGD=1,4).')]
    ]

    # --- Aba: Serviço de Chamadas ---
    tab_calls_layout = [
        [sg.Text('Número para Chamada:'), sg.Input(key='-CALL_NUMBER-', size=(20,1), tooltip='Número de telefone para fazer uma chamada.')],
        [sg.Button('Fazer Chamada', key='-DIAL_CALL-', disabled=True, tooltip='Inicia uma chamada de voz (ATD).'),
         sg.Button('Desligar Chamada', key='-HANGUP_CALL-', disabled=True, tooltip='Desliga a chamada atual (ATH).')],
        [sg.Button('Atender Chamada', key='-ANSWER_CALL-', disabled=True, tooltip='Atende uma chamada recebida (ATA).'),
         sg.Button('Status Chamada', key='-CALL_STATUS-', disabled=True, tooltip='Verifica o status das chamadas ativas (AT+CLCC).')]
    ]

    # --- Aba: Controle de Áudio ---
    tab_audio_layout = [
        [sg.Text('Volume Alto-falante (0-5):'), sg.Slider(range=(0, 5), default_value=3, orientation='h', key='-VOLUME-', disabled=True, enable_events=True, tooltip='Define o volume do alto-falante (AT+CLVL).')],
        [sg.Button('Definir Volume', key='-SET_VOLUME-', disabled=True, tooltip='Aplica o volume selecionado.')],
        [sg.Button('Mutar Microfone', key='-MUTE_MIC_ON-', disabled=True, tooltip='Ativa o mudo do microfone (AT+CMUT=1).'),
         sg.Button('Desmutar Microfone', key='-MUTE_MIC_OFF-', disabled=True, tooltip='Desativa o mudo do microfone (AT+CMUT=0).')],
        [sg.Button('Ativar Loop Áudio', key='-LOOP_AUDIO_ON-', disabled=True, tooltip='Ativa o teste de loopback de áudio (AT+QAUDLOOP=1).'),
         sg.Button('Desativar Loop Áudio', key='-LOOP_AUDIO_OFF-', disabled=True, tooltip='Desativa o teste de loopback de áudio (AT+QAUDLOOP=0).')],
        [sg.Text('Modo Áudio:'), sg.Combo(values=[0, 1, 2, 3], default_value=0, key='-AUDIO_MODE_SET-', size=(10,1), readonly=True, tooltip='0=Handset, 1=Headset, 2=Speaker, 3=UAC/Voice over USB.'),
         sg.Button('Definir Modo Áudio', key='-SET_AUDIO_MODE-', disabled=True, tooltip='Define o modo de áudio (AT+QAUDMOD).'),
         sg.Button('Ler Modo Áudio', key='-GET_AUDIO_MODE-', disabled=True, tooltip='Lê o modo de áudio atual.')],
        [sg.Text('TxGain (Mic):'), sg.Input(default_text='20000', size=(8,1), key='-MIC_TXGAIN-', tooltip='Ganho do codec de uplink (0-65535).'),
         sg.Text('TxDGain (Mic, opc):'), sg.Input(default_text='', size=(8,1), key='-MIC_TXDGAIN-', tooltip='Ganho digital de uplink (0-65535), opcional.'),
         sg.Button('Definir Ganhos Mic', key='-SET_MIC_GAINS-', disabled=True, tooltip='Define os ganhos do microfone (AT+QMIC).'),
         sg.Button('Ler Ganhos Mic', key='-GET_MIC_GAINS-', disabled=True, tooltip='Lê os ganhos do microfone.')],
        [sg.Text('RxGain (Volume Downlink):'), sg.Input(default_text='20577', size=(8,1), key='-RX_GAIN-', tooltip='Ganho digital de downlink (0-65535).'),
         sg.Button('Definir Ganhos Rx', key='-SET_RX_GAINS-', disabled=True, tooltip='Define os ganhos de downlink (AT+QRXGAIN).'),
         sg.Button('Ler Ganhos Rx', key='-GET_RX_GAINS-', disabled=True, tooltip='Lê os ganhos de downlink.')],
        [sg.Frame('Configuração DAI (Interface de Áudio Digital - PCM)', [
            [sg.Text('Modo I/O:'), sg.Combo(values=[1, 2, 3, 5], default_value=1, key='-DAI_IO-', size=(5,1), readonly=True, tooltip='1=PCM custom, 2=NAU8814, 3=ALC5616, 5=TLV320AIC3104.')],
            [sg.Text('Modo Áudio (DAI):'), sg.Combo(values=[0, 1], default_value=0, key='-DAI_MODE-', size=(5,1), readonly=True, tooltip='0=Master, 1=Slave (Relevante para Modo I/O 1).')],
            [sg.Text('FSYNC:'), sg.Combo(values=[0, 1], default_value=0, key='-DAI_FSYNC-', size=(5,1), readonly=True, tooltip='0=Short-sync, 1=Long-sync (Relevante para Modo I/O 1).')],
            [sg.Text('Clock:'), sg.Combo(values=[0, 1, 2, 3, 4, 5], default_value=4, key='-DAI_CLOCK-', size=(5,1), readonly=True, tooltip='Frequência do clock (0=128K, ..., 5=4096K) (Relevante para Modo I/O 1).')],
            [sg.Text('Formato:'), sg.Combo(values=[0], default_value=0, key='-DAI_FORMAT-', size=(5,1), readonly=True, tooltip='Apenas 0=16-bit linear suportado para PCM custom (Relevante para Modo I/O 1).')],
            [sg.Text('Sample Rate:'), sg.Combo(values=[0, 1], default_value=0, key='-DAI_SAMPLE-', size=(5,1), readonly=True, tooltip='0=8K, 1=16K (Relevante para Modo I/O 1).')],
            [sg.Text('Num Slots:'), sg.Input(default_text='1', size=(3,1), key='-DAI_NUM_SLOTS-', tooltip='Número de slots (geralmente 1).')],
            [sg.Text('Slot Mapping:'), sg.Input(default_text='1', size=(3,1), key='-DAI_SLOT_MAP-', tooltip='Mapeamento de slots (1-16).')],
            [sg.Button('Configurar DAI', key='-CONFIG_DAI-', disabled=True, tooltip='Configura a interface de áudio digital (AT+QDAI). Requer reinício do modem para efeito total.')]
        ])]
    ]

    # --- Nova Aba: GPS & Interfaces USB ---
    tab_gps_usb_layout = [
        [sg.Frame('Controle GPS', [
            [sg.Button('Ativar GPS', key='-ENABLE_GPS-', disabled=True, tooltip='Ativa o módulo GPS (AT+QGPS=1).'),
             sg.Button('Desativar GPS', key='-DISABLE_GPS-', disabled=True, tooltip='Desativa o módulo GPS (AT+QGPS=0).')],
            [sg.Button('Obter Localização GPS', key='-GET_GPS_LOCATION-', disabled=True, tooltip='Obtém as coordenadas GPS atuais (AT+QGPSLOC?).')],
            [sg.Text('Saída NMEA GPS:'), sg.Combo(values=["usbnmea", "uartnmea", "none"], default_value="usbnmea", key='-GPS_OUTPORT_SET-', size=(10,1), readonly=True, tooltip='Configura a porta de saída NMEA para dados GPS.')],
            [sg.Button('Definir Saída GPS NMEA', key='-SET_GPS_OUTPORT-', disabled=True, tooltip='Configura a porta de saída NMEA do GPS (AT+QGPSCFG="outport").'),
             sg.Button('Ler Saída GPS NMEA', key='-GET_GPS_OUTPORT-', disabled=True, tooltip='Lê a porta de saída NMEA do GPS atual.')]
        ])],
        [sg.Frame('Configuração de Interfaces USB Avançada', [
            [sg.Text('AVISO: A configuração incorreta de USBCFG pode tornar o modem inacessível via USB.', text_color='red')],
            [sg.Text('Consulte o manual para parâmetros de USBCFG antes de usar comandos personalizados para escrita.', text_color='red')],
            [sg.Button('Ler Configuração USB', key='-GET_USBCFG-', disabled=True, tooltip='Lê a configuração atual da interface USB (AT+QCFG="USBCFG").')],
            [sg.HorizontalSeparator()],
            [sg.Text('Voice over USB (PCM data transfer):')],
            [sg.Text('Porta PCM:'), sg.Combo(values=[0, 1], default_value=0, key='-QPCMV_PORT-', size=(5,1), readonly=True, tooltip='0=USB NMEA, 1=UART.')],
            [sg.Button('Habilitar Voice over USB', key='-ENABLE_QPCMV-', disabled=True, tooltip='Habilita a transferência de dados PCM via USB (AT+QPCMV=1).'),
             sg.Button('Desabilitar Voice over USB', key='-DISABLE_QPCMV-', disabled=True, tooltip='Desabilita a transferência de dados PCM via USB (AT+QPCMV=0).'),
             sg.Button('Status Voice over USB', key='-GET_QPCMV_STATUS-', disabled=True, tooltip='Obtém o status do Voice over USB (AT+QPCMV?).')],
            [sg.Text('Nota: Roteamento para ALSA/PulseAudio no Linux requer configuração do SO.')]
        ])]
    ]

    # --- Nova Aba: Sumário do Modem ---
    tab_summary_layout = [
        [sg.Button('Gerar Sumário do Modem', key='-GENERATE_SUMMARY-', disabled=True, tooltip='Coleta e exibe um sumário completo de todos os status e informações do modem.')],
        [sg.Multiline(size=(100, 30), font='Courier 10', disabled=True, background_color='lightgray', key='-MODEM_SUMMARY_OUTPUT-')] # Saída para o sumário
    ]

    # --- Aba: Comandos Personalizados ---
    commands_list_column = [
        [sg.Text('Buscar Comando:', font='_ 11'), sg.Input(size=(40, 1), enable_events=True, key='-COMMAND_FILTER-', tooltip='Digite para filtrar a lista de comandos.')],
        [sg.Listbox(values=[f"{cmd['cmd']}: {cmd['desc']} (Seção {cmd['section']})" for cmd in ALL_MANUAL_COMMANDS],
                    size=(60, 20), enable_events=True, key='-COMMAND_LIST-',
                    tooltip='Lista de comandos AT do manual. Clique para copiar para a entrada.')],
        [sg.Button('Copiar Comando Selecionado', key='-COPY_SELECTED_CMD-', disabled=True, tooltip='Copia o comando selecionado da lista para a área de entrada.')]
    ]

    custom_command_input_column = [
        [sg.Text('Comando AT Personalizado:', font='_ 11')],
        [sg.Input(key='-CUSTOM_AT_COMMAND-', size=(50,1), enable_events=True, tooltip='Digite seu comando AT aqui (ex: AT+CSQ, AT+QCFG="band",...).')],
        [sg.Text('Resposta Esperada (opcional, padrão "OK"):'), sg.Input(default_text='OK', key='-EXPECTED_RESPONSE-', size=(15,1), tooltip='Texto que a resposta do modem deve conter para ser considerada sucesso.')],
        [sg.Text('Timeout (segundos, padrão 5):'), sg.Input(default_text='5', size=(8,1), key='-CUSTOM_TIMEOUT-', tooltip='Tempo máximo para esperar a resposta do modem.')],
        [sg.Button('Enviar Comando Personalizado', key='-SEND_CUSTOM_CMD-', disabled=True, tooltip='Envia o comando AT digitado para o modem.')]
    ]

    tab_custom_commands_layout = [
        [sg.Column(commands_list_column), sg.VSeperator(), sg.Column(custom_command_input_column)]
    ]

    # --- Aba para Logs de URCs ---
    tab_urc_log_layout = [
        [sg.Multiline(size=(100, 30), font='Courier 10', disabled=True, background_color='lightgray', key='-URC_LOG_OUTPUT-')],
        [sg.Button('Limpar Log URC', key='-CLEAR_URC_LOG-', tooltip='Limpa o conteúdo do log de URCs.')]
    ]

    # --- NOVO: Aba para SMS Avançado (Caixa de Entrada/Saída) ---
    tab_advanced_sms_layout = [
        # Linha para inserir os números de telefone para envio, agora permitindo múltiplos
        [sg.Text('Número(s) Destino:'), sg.Input(key='-SMS_NUMBER-', size=(40,1), tooltip='Número(s) de telefone para enviar SMS (separe com vírgulas para múltiplos).')],
        [sg.Text('Mensagem:'), sg.Input(key='-SMS_MESSAGE-', size=(40,1), tooltip='Conteúdo da mensagem SMS.')],
        [sg.Button('Enviar SMS', key='-SEND_SMS-', disabled=True, tooltip='Envia um SMS (AT+CMGS).')], # Este botão é o envio SIMPLES
        [sg.HorizontalSeparator()],
        [sg.Text('Caixa de Entrada de SMS (Últimas Mensagens)'), sg.Push(), sg.Button('Atualizar Inbox', key='-REFRESH_SMS_INBOX-', disabled=True, tooltip='Lê e atualiza a caixa de entrada de SMS.')],
        [sg.Multiline(size=(100, 15), font='Courier 10', disabled=True, background_color='lightgray', key='-SMS_INBOX_OUTPUT-')],
        [sg.HorizontalSeparator()],
        [sg.Text('Caixa de Saída de SMS (Histórico de Envios)'), sg.Push(), sg.Button('Atualizar Outbox', key='-REFRESH_SMS_OUTBOX-', disabled=True, tooltip='Lê e atualiza o histórico de SMS enviados.')],
        [sg.Multiline(size=(100, 15), font='Courier 10', disabled=True, background_color='lightgray', key='-SMS_OUTBOX_OUTPUT-')],
        [sg.HorizontalSeparator()],
        [sg.Button('Limpar Todas as Mensagens', key='-DELETE_ALL_SMS_ADVANCED-', disabled=True, tooltip='Apaga todas as mensagens SMS da memória do modem.')]
    ]


    # --- Criação do Grupo de Abas ---
    tab_group_layout = [
        [sg.TabGroup([
            [sg.Tab('Conexão e Básico', tab_connection_control_layout, key='-TAB_CONN_BASIC-')],
            [sg.Tab('Info e Status', tab_info_status_layout, key='-TAB_INFO_STATUS-')],
            [sg.Tab('Rede e APN', tab_network_apn_layout, key='-TAB_NETWORK_APN-')],
            [sg.Tab('SMS', tab_sms_layout, key='-TAB_SMS-')],
            [sg.Tab('Chamadas', tab_calls_layout, key='-TAB_CALLS-')],
            [sg.Tab('Áudio', tab_audio_layout, key='-TAB_AUDIO-')],
            [sg.Tab('GPS & Interfaces USB', tab_gps_usb_layout, key='-TAB_GPS_USB-')], 
            [sg.Tab('Sumário do Modem', tab_summary_layout, key='-TAB_SUMMARY-')], 
            [sg.Tab('Comandos Personalizados', tab_custom_commands_layout, key='-TAB_CUSTOM_CMDS-')],
            [sg.Tab('Logs de URCs', tab_urc_log_layout, key='-TAB_URC_LOG-')],
            [sg.Tab('SMS Avançado', tab_advanced_sms_layout, key='-TAB_ADVANCED_SMS-')] # Nova aba adicionada
        ], key='-TAB_GROUP-', expand_x=True, expand_y=True)]
    ]

    # --- Layout Principal da Janela ---
    layout = [
        [tab_group_layout], # Adiciona o grupo de abas
        [sg.HorizontalSeparator()], # Separador visual
        # Botões de controle de log da saída
        [sg.Button('Copiar Log', key='-COPY_LOG-', tooltip='Copia o conteúdo do console para a área de transferência.'), 
         sg.Button('Salvar Log', key='-SAVE_LOG-', tooltip='Salva o conteúdo do console em um arquivo de texto.')], 
        [sg.Output(size=(100, 25), font='Courier 10', key='-OUTPUT-', tooltip='Saída de comandos e respostas do modem.')] 
    ]
    return sg.Window('Quectel EC25 - Painel de Controle', layout, finalize=True, resizable=True, return_keyboard_events=True)
