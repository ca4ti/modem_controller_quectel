# src/modem/at_commands.py
import re # Certifique-se que 're' está importado aqui

# --- Funções de Parsing para Respostas de Comandos AT ---

# Função auxiliar para extrair a linha de dados relevante
def _extract_data_line(response: str, prefix: str) -> str:
    """Extrai a linha de dados relevante de uma resposta que pode conter eco de comando e OK."""
    lines = response.strip().split('\n')
    for line in lines:
        if line.strip().startswith(prefix):
            return line.strip()
    return "" # Retorna string vazia se a linha não for encontrada

def parse_product_info_response(response: str) -> str:
    """Parses ATI response for product info."""
    lines = response.strip().split('\n')
    info_lines = [line for line in lines if ("Quectel" in line or "EC" in line or "Revision" in line) and not line.strip().startswith("ATI")]
    return "\n".join(info_lines) if info_lines else "N/A"

def parse_imei_response(response: str) -> str:
    """Parses AT+CGSN response for IMEI."""
    lines = response.strip().split('\n')
    for line in lines:
        line = line.strip()
        # Procura por uma linha que contenha APENAS 15 ou 16 dígitos
        if re.fullmatch(r'\d{15,16}', line): 
            return line
    return "N/A"

def parse_imsi_response(response: str) -> str:
    """Parses AT+CIMI response for IMSI."""
    lines = response.strip().split('\n')
    for line in lines:
        line = line.strip()
        # Procura por uma linha que contenha APENAS dígitos, com 14 ou mais caracteres
        if re.fullmatch(r'\d{14,}', line): 
            return line
    return "N/A"

def parse_iccid_response(response: str) -> str:
    """Parses AT+QCCID response for ICCID."""
    data_line = _extract_data_line(response, "+QCCID:")
    match = re.search(r'\+QCCID:\s*(\d+)', data_line)
    return match.group(1) if match else "N/A"

def parse_sim_status_response(response: str) -> str:
    """Parses AT+QSIMSTAT? response for SIM status."""
    data_line = _extract_data_line(response, "+QSIMSTAT:")
    match = re.search(r'\+QSIMSTAT:\s*(\d+),(\d+)', data_line)
    if match:
        enable_status = int(match.group(1)) 
        inserted_status = int(match.group(2)) 
        enable_desc = {0: "Relatório Desabilitado", 1: "Relatório Habilitado"}.get(enable_status, "Desconhecido")
        inserted_desc = {0: "Removido", 1: "Inserido", 2: "Desconhecido (Pré-inicialização)"}.get(inserted_status, "Desconhecido")
        return f"Status Relatório: {enable_desc}, SIM: {inserted_desc}"
    return "N/A"

def parse_battery_status_response(response: str) -> str:
    """Parses AT+CBC response for battery status."""
    data_line = _extract_data_line(response, "+CBC:")
    match = re.search(r'\+CBC:\s*(\d+),(\d+),(\d+)', data_line)
    if match:
        bcs = int(match.group(1)) 
        bcl = int(match.group(2)) 
        voltage = int(match.group(3)) 
        bcs_desc = {0: "Não carregando", 1: "Carregando", 2: "Carga finalizada"}.get(bcs, "Desconhecido")
        return f"Status Carga: {bcs_desc}, Nível: {bcl}%, Voltagem: {voltage}mV"
    return "N/A"

def parse_clock_response(response: str) -> str:
    """Parses AT+CCLK? response for clock."""
    data_line = _extract_data_line(response, "+CCLK:")
    match = re.search(r'\+CCLK:\s*"([^"]+)"', data_line)
    return match.group(1) if match else "N/A"

def parse_adc_value_response(response: str) -> str:
    """Parses AT+QADC response for ADC value."""
    data_line = _extract_data_line(response, "+QADC:")
    match = re.search(r'\+QADC:\s*(\d+),(\d+)', data_line)
    if match:
        status = int(match.group(1)) 
        value = int(match.group(2)) 
        return f"Valor ADC: {value}mV (Status: {'Sucesso' if status == 1 else 'Falha'})"
    return "N/A"

def parse_signal_quality_response(response: str) -> str:
    """Parses AT+CSQ response for signal quality."""
    data_line = _extract_data_line(response, "+CSQ:")
    match = re.search(r'\+CSQ:\s*(\d+),(\d+)', data_line)
    if match:
        rssi_val = int(match.group(1))
        ber_val = int(match.group(2))
        
        rssi_dbm = ""
        if 0 <= rssi_val <= 30: rssi_dbm = f"{-113 + (rssi_val * 2)} dBm"
        elif rssi_val == 31: rssi_dbm = "-51 dBm or greater"
        elif rssi_val == 99: rssi_dbm = "Not known or not detectable"
        elif 100 <= rssi_val <= 190: rssi_dbm = f"{-116 + rssi_val} dBm" # Extended range for TD-SCDMA RSCP
        elif rssi_val == 191: rssi_dbm = "-25 dBm or greater"
        elif rssi_val == 199: rssi_dbm = "Not known or not detectable"
        else: rssi_dbm = "Valor fora do range esperado"

        ber_info = f"{ber_val} (RXQUAL conforme 3GPP TS 45.008)" 
        if ber_val == 99: ber_info = "Não conhecido ou não detectável" 
        
        return f"RSSI: {rssi_val} ({rssi_dbm}), BER: {ber_info}"
    return "N/A"

def parse_network_info_response(response: str) -> str:
    """Parses AT+QNWINFO response for network information."""
    data_line = _extract_data_line(response, "+QNWINFO:")
    match = re.search(r'\+QNWINFO:\s*"([^"]*)","([^"]*)","([^"]*)",(\d+)', data_line)
    if match:
        act, oper, band, channel = match.groups()
        return f"Tecnologia: {act}, Operador (MCCMNC): {oper}, Banda: {band}, Canal: {channel}"
    return "N/A"

def parse_network_reg_status_response(response: str) -> str:
    """Parses AT+CREG? response for network registration status."""
    data_line = _extract_data_line(response, "+CREG:")
    match = re.search(r'\+CREG:\s*(\d+),(\d+)(?:,"([0-9A-F]*)","([0-9A-F]*)",(\d*))?', data_line)
    if match:
        n, stat = int(match.group(1)), int(match.group(2))
        
        n_desc = {
            0: "URC Desabilitado", 1: "URC Habilitado: +CREG: <stat>", 
            2: "URC Habilitado com info de localização: +CREG: <stat>[,<lac>,<ci>[,<Act>]]"
        }.get(n, "Desconhecido")
        
        stat_desc = {
            0: "Não registrado, ME não buscando", 1: "Registrado, rede de origem",
            2: "Não registrado, ME buscando", 3: "Registro negado",
            4: "Desconhecido", 5: "Registrado, roaming"
        }.get(stat, "Desconhecido")

        full_status = f"Modo URC: {n_desc}, Status Registro: {stat_desc}"

        if n == 2 and match.group(3): # Verifica se LAC/CI/Act estão presentes para o modo 2
            lac = match.group(3) if match.group(3) else 'N/A'
            ci = match.group(4) if match.group(4) else 'N/A'
            act_code = match.group(5) if match.group(5) else '' 
            act_desc = { "0": "GSM", "2": "UTRAN", "3": "GSM W/EGPRS", "4": "UTRAN W/HSDPA",
                         "5": "UTRAN W/HSUPA", "6": "UTRAN W/HSDPA and HSUPA", "7": "E-UTRAN"
                       }.get(act_code, "N/A")
            full_status += f", LAC: {lac}, Cell ID: {ci}, Tecnologia de Acesso: {act_desc}"
        return full_status
    return "N/A"

def parse_pdp_address_response(response: str) -> str:
    """Parses AT+CGPADDR response for PDP address."""
    addresses = []
    # Itera sobre as linhas da resposta bruta
    for line in response.strip().split('\n'):
        # Procura por linhas que começam com "+CGPADDR:"
        if line.startswith('+CGPADDR:'):
            match = re.search(r'\+CGPADDR:\s*(\d+),"([^"]+)"', line)
            if match:
                addresses.append(f"CID {match.group(1)}: {match.group(2)}")
    return "\n".join(addresses) if addresses else "Nenhum endereço PDP encontrado ou contexto inativo."

def parse_network_scan_mode_response(response: str) -> str:
    """Parses AT+QCFG="nwscanmode" response."""
    data_line = _extract_data_line(response, '+QCFG: "nwscanmode"')
    match = re.search(r'\+QCFG:\s*"nwscanmode",(\d+)', data_line)
    if match:
        mode = int(match.group(1))
        mode_desc = {
            0: "Auto (LTE/WCDMA/TD-SCDMA/GSM)", 1: "GSM only (2G)",
            2: "WCDMA only (3G)", 3: "LTE only (4G)"
        }.get(mode, "Desconhecido")
        return f"Modo de Varredura de Rede: {mode_desc} ({mode})"
    return "N/A"

def parse_roaming_service_response(response: str) -> str:
    """Parses AT+QCFG="roamservice" response."""
    data_line = _extract_data_line(response, '+QCFG: "roamservice"')
    match = re.search(r'\+QCFG:\s*"roamservice",(\d+)', data_line)
    if match:
        mode = int(match.group(1))
        mode_desc = {0: "Desabilitado", 1: "Habilitado", 255: "Automático"}.get(mode, "Desconhecido")
        return f"Serviço de Roaming: {mode_desc} ({mode})"
    return "N/A"

def parse_band_config_response(response: str) -> str:
    """Parses AT+QCFG="band" response."""
    data_line = _extract_data_line(response, '+QCFG: "band"')
    match = re.search(r'\+QCFG:\s*"band",([^,]+),([^,]+),([^,]+)', data_line)
    if match:
        gsm_wcdma_band, lte_band, tds_scdma_band = match.groups()
        return f"GSM/WCDMA: {gsm_wcdma_band}, LTE: {lte_band}, TD-SCDMA: {tds_scdma_band}"
    return "N/A"

def parse_calls_status_response(response: str) -> str:
    """Parses AT+CLCC response for call status."""
    calls = []
    for line in response.strip().split('\n'):
        if line.startswith('+CLCC:'):
            match = re.search(r'\+CLCC:\s*(\d+),(\d+),(\d+),(\d+),(\d+)(?:,"([^"]*)",(\d+))?', line)
            if match:
                call_id = match.group(1)
                direction = "MO" if match.group(2) == '0' else "MT"
                state_code = int(match.group(3))
                mode_code = int(match.group(4))
                
                state_map = {0: 'Active', 1: 'Held', 2: 'Dialing', 3: 'Alerting', 4: 'Incoming', 5: 'Waiting'}
                mode_map = {0: 'Voice', 1: 'Data', 2: 'FAX'}
                
                call_state = state_map.get(state_code, 'Unknown')
                bearer_mode = mode_map.get(mode_code, 'Unknown')
                
                number = match.group(6) if match.group(6) else 'N/A'
                
                calls.append(f"ID: {call_id}, Dir: {direction}, Estado: {call_state}, Modo: {bearer_mode}, Número: {number}")
    return "\n".join(calls) if calls else "Nenhuma chamada ativa."

def parse_audio_mode_response(response: str) -> str:
    """Parses AT+QAUDMOD? response."""
    data_line = _extract_data_line(response, "+QAUDMOD:")
    match = re.search(r'\+QAUDMOD:\s*(\d+)', data_line)
    if match:
        mode_code = int(match.group(1)) 
        mode_desc = {
            0: "Handset", 1: "Headset", 2: "Speaker", 3: "UAC (USB Audio Class)" 
        }.get(mode_code, "Desconhecido")
        return f"Modo de Áudio: {mode_desc}"
    return "N/A"

def parse_mic_gains_response(response: str) -> str:
    """Parses AT+QMIC? response."""
    data_line = _extract_data_line(response, "+QMIC:")
    match = re.search(r'\+QMIC:\s*(\d+),(\d+)', data_line)
    if match:
        txgain = int(match.group(1)) 
        txdgain = int(match.group(2)) 
        return f"TxGain (Codec): {txgain}, TxDGain (Digital): {txdgain}"
    return "N/A"

def parse_rx_gains_response(response: str) -> str:
    """Parses AT+QRXGAIN? response."""
    data_line = _extract_data_line(response, "+QRXGAIN:")
    match = re.search(r'\+QRXGAIN:\s*(\d+)', data_line)
    if match:
        rxgain = int(match.group(1)) 
        return f"RxGain (Digital Downlink): {rxgain}"
    return "N/A"

def parse_dai_config_response(response: str) -> str:
    """Parses AT+QDAI? response."""
    data_line = _extract_data_line(response, "+QDAI:")
    match = re.search(r'\+QDAI:\s*(\d+)(?:,(\d+),(\d+),(\d+),(\d+),(\d+),(\d+),(\d+))?', data_line)
    if match:
        io_mode = match.group(1) 
        if io_mode == '1' and match.group(2): 
            audio_mode = match.group(2) 
            fsync = match.group(3) 
            clock = match.group(4) 
            audio_format = match.group(5) 
            sample = match.group(6) 
            num_slots = match.group(7) 
            slot_mapping = match.group(8) 

            clock_desc = {'0': '128K', '1': '256K', '2': '512K', '3': '1024K','4': '2048K', '5': '4096K'}.get(clock, 'Desconhecido')
            format_desc = {'0': '16-bit linear', '1': '8-bit a-law', '2': '8-bit u-law'}.get(audio_format, 'Desconhecido')
            sample_desc = {'0': '8K', '1': '16K'}.get(sample, 'Desconhecido')

            return (f"Modo I/O: {io_mode} (PCM Personalizado), Modo Áudio: {'Mestre' if audio_mode == '0' else 'Escravo'}, "
                    f"FSYNC: {'Primário' if fsync == '0' else 'Auxiliar'}, Clock: {clock_desc}, Formato: {format_desc}, "
                    f"Sample Rate: {sample_desc}, Num Slots: {num_slots}, Slot Mapping: {slot_mapping}")
        else: 
            io_mode_desc = {
                '2': 'Analog (NAU8814)', '3': 'Analog (ALC5616 - Default)', '5': 'Analog (TLV320AIC3104)'
            }.get(io_mode, f"Modo I/O: {io_mode} (Genérico/Codec)")
            return f"Configuração DAI: {io_mode_desc}"
    return "N/A"

def parse_gps_location_response(response: str) -> str:
    """Parses AT+QGPSLOC? response."""
    data_line = _extract_data_line(response, "+QGPSLOC:")
    match = re.search(r'\+QGPSLOC:\s*([^,]+),([^,]+),([^,]+),([^,]+),([^,]+),([^,]+),', data_line)
    if match:
        latitude = match.group(1)
        longitude = match.group(2)
        altitude = match.group(3)
        speed = match.group(4)
        timestamp = match.group(6) 
        return (f"Localização GPS: Lat={latitude}, Lon={longitude}, Alt={altitude}m, "
                f"Velocidade={speed}km/h, Tempo={timestamp}")
    return "N/A (Sem dados GPS ou GPS não ativo)"

def parse_gps_outport_response(response: str) -> str:
    """Parses AT+QGPSCFG="outport" response."""
    data_line = _extract_data_line(response, '+QGPSCFG: "outport"')
    match = re.search(r'\+QGPSCFG:\s*"outport","([^"]+)"', data_line)
    return f"Porta de Saída GPS NMEA: {match.group(1)}" if match else "N/A"

def parse_usb_config_response(response: str) -> str:
    """Parses AT+QCFG="USBCFG" response."""
    data_line = _extract_data_line(response, '+QCFG: "USBCFG"')
    return data_line if data_line else "N/A"

def parse_voice_over_usb_status_response(response: str) -> str:
    """Parses AT+QPCMV? response."""
    data_line = _extract_data_line(response, "+QPCMV:")
    match = re.search(r'\+QPCMV:\s*(\d+),(\d+)', data_line)
    if match:
        enable_status = int(match.group(1))
        port = int(match.group(2))
        status_desc = {0: "Desabilitado", 1: "Habilitado"}.get(enable_status, "Desconhecido")
        port_desc = {0: "USB NMEA", 1: "UART"}.get(port, "Desconhecido")
        return f"Voice over USB (PCM): {status_desc} na porta {port_desc}"
    return "N/A"

def parse_urc_output_port_response(response: str) -> str:
    """Parses AT+QURCCFG="urcport" response."""
    data_line = _extract_data_line(response, '+QURCCFG: "urcport"')
    match = re.search(r'\+QURCCFG:\s*"urcport","([^"]+)"', data_line)
    return f"Porta de Saída de URCs: {match.group(1)}" if match else "N/A"

# --- Dicionário de Comandos AT e seus Parsers ---
# Mapeia o nome abstrato do comando para o comando AT real e sua função de parsing.
# IMPORTANTE: Este dicionário deve ser definido APÓS TODAS as funções de parsing.
AT_COMMANDS = {
    # Comandos de Controle Básico
    "POWER_OFF": {"command": "AT+QPOWD=1", "expected_response": "POWERED DOWN"},
    "REBOOT": {"command": "AT+CFUN=1,1", "expected_response": "OK"},
    "FACTORY_RESET": {"command": "AT&F", "expected_response": "OK"},
    "SET_URC_OUTPUT_PORT": {"command": 'AT+QURCCFG="urcport","{}"', "expected_response": "OK"},
    "GET_URC_OUTPUT_PORT": {"command": 'AT+QURCCFG="urcport"', "expected_response": "+QURCCFG", "parser": parse_urc_output_port_response},

    # Comandos de Informação e Status
    "PRODUCT_INFO": {"command": "ATI", "expected_response": "Quectel", "parser": parse_product_info_response},
    "GET_IMEI": {"command": "AT+CGSN", "expected_response": "OK", "parser": parse_imei_response},
    "GET_IMSI": {"command": "AT+CIMI", "expected_response": "OK", "parser": parse_imsi_response},
    "GET_ICCID": {"command": "AT+QCCID", "expected_response": "+QCCID", "parser": parse_iccid_response},
    "GET_SIM_STATUS": {"command": "AT+QSIMSTAT?", "expected_response": "+QSIMSTAT", "parser": parse_sim_status_response},
    "GET_BATTERY_STATUS": {"command": "AT+CBC", "expected_response": "+CBC", "parser": parse_battery_status_response},
    "GET_CLOCK": {"command": "AT+CCLK?", "expected_response": "+CCLK", "parser": parse_clock_response},
    "GET_ADC_VALUE": {"command": "AT+QADC={}", "expected_response": "+QADC", "parser": parse_adc_value_response},

    # Comandos de Rede e APN
    "GET_SIGNAL_QUALITY": {"command": "AT+CSQ", "expected_response": "+CSQ", "parser": parse_signal_quality_response},
    "GET_NETWORK_INFO": {"command": "AT+QNWINFO", "expected_response": "+QNWINFO", "parser": parse_network_info_response},
    "GET_NETWORK_REGISTRATION_STATUS": {"command": "AT+CREG?", "expected_response": "+CREG", "parser": parse_network_reg_status_response},
    "DEFINE_APN": {"command": 'AT+CGDCONT={},"{}","{}"', "expected_response": "OK"}, # CID, PDP_Type, APN
    "ACTIVATE_PDP_CONTEXT": {"command": "AT+CGACT=1,{}", "expected_response": "OK"}, # CID
    "DEACTIVATE_PDP_CONTEXT": {"command": "AT+CGACT=0,{}", "expected_response": "OK"}, # CID
    "GET_PDP_ADDRESS": {"command": "AT+CGPADDR={}", "expected_response": "+CGPADDR", "parser": parse_pdp_address_response}, # CID
    "SET_NETWORK_SCAN_MODE": {"command": 'AT+QCFG="nwscanmode",{},{}', "expected_response": "OK"}, # mode, effect
    "GET_NETWORK_SCAN_MODE": {"command": 'AT+QCFG="nwscanmode"', "expected_response": "+QCFG", "parser": parse_network_scan_mode_response},
    "SET_ROAMING_SERVICE": {"command": 'AT+QCFG="roamservice",{},{}', "expected_response": "OK"}, # mode, effect
    "GET_ROAMING_SERVICE": {"command": 'AT+QCFG="roamservice"', "expected_response": "+QCFG", "parser": parse_roaming_service_response},
    "SET_BANDS": {"command": 'AT+QCFG="band","{}","{}","{}",{}', "expected_response": "OK"}, # bandval, ltebandval, tdsbandval, effect
    "GET_BANDS": {"command": 'AT+QCFG="band"', "expected_response": "+QCFG", "parser": parse_band_config_response},

    # Comandos de SMS
    "SEND_SMS_INIT": {"command": 'AT+CMGS="{}"', "expected_response": ">"}, # Number, expects prompt
    "SEND_SMS_CONTENT": {"command": '{}\x1A', "expected_response": "OK"}, # Message + CTRL+Z
    "READ_ALL_SMS_ADVANCED": {"command": 'AT+CMGL="ALL"', "expected_response": "OK"}, # Para a função de SMS avançado
    "READ_SMS_BY_INDEX": {"command": "AT+CMGR={}", "expected_response": "OK"},
    "DELETE_SMS_BY_INDEX": {"command": "AT+CMGD={}", "expected_response": "OK"},
    "DELETE_ALL_SMS": {"command": "AT+CMGD=1,4", "expected_response": "OK"}, # Apaga todas as mensagens

    # Comandos de Chamada
    "DIAL_CALL": {"command": "ATD{};", "expected_response": "OK"},
    "HANGUP_CALL": {"command": "ATH", "expected_response": "OK"},
    "ANSWER_CALL": {"command": "ATA", "expected_response": "OK"},
    "GET_CALL_STATUS": {"command": "AT+CLCC", "expected_response": "+CLCC", "parser": parse_calls_status_response},

    # Comandos de Áudio
    "SET_SPEAKER_VOLUME": {"command": "AT+CLVL={}", "expected_response": "OK"},
    "MUTE_MICROPHONE": {"command": "AT+CMUT={}", "expected_response": "OK"}, # 0=desmuta, 1=muta
    "SET_AUDIO_LOOP_TEST": {"command": "AT+QAUDLOOP={}", "expected_response": "OK"}, # 0=off, 1=on
    "SET_AUDIO_MODE": {"command": "AT+QAUDMOD={}", "expected_response": "OK"},
    "GET_AUDIO_MODE": {"command": "AT+QAUDMOD?", "expected_response": "+QAUDMOD", "parser": parse_audio_mode_response},
    "SET_MIC_GAINS_FULL": {"command": "AT+QMIC={},{}", "expected_response": "OK"}, # txgain, txdgain
    "SET_MIC_GAINS_TXGAIN_ONLY": {"command": "AT+QMIC={}", "expected_response": "OK"}, # txgain
    "GET_MIC_GAINS": {"command": "AT+QMIC?", "expected_response": "+QMIC", "parser": parse_mic_gains_response},
    "SET_RX_GAINS": {"command": "AT+QRXGAIN={}", "expected_response": "OK"},
    "GET_RX_GAINS": {"command": "AT+QRXGAIN?", "expected_response": "+QRXGAIN", "parser": parse_rx_gains_response},
    "CONFIG_DAI": {"command": "AT+QDAI={},{},{},{},{},{},{},{}", "expected_response": "OK"}, # io, mode, fsync, clock, format, sample, num_slots, slot_mapping
    "GET_DAI_CONFIG": {"command": "AT+QDAI?", "expected_response": "+QDAI", "parser": parse_dai_config_response},

    # Comandos de GPS e USB
    "ENABLE_GPS": {"command": "AT+QGPS=1", "expected_response": "OK"},
    "DISABLE_GPS": {"command": "AT+QGPS=0", "expected_response": "OK"},
    "GET_GPS_LOCATION": {"command": "AT+QGPSLOC?", "expected_response": "+QGPSLOC", "parser": parse_gps_location_response},
    "SET_GPS_OUTPORT": {"command": 'AT+QGPSCFG="outport","{}"', "expected_response": "OK"},
    "GET_GPS_OUTPORT": {"command": 'AT+QGPSCFG="outport"', "expected_response": "+QGPSCFG", "parser": parse_gps_outport_response},
    "GET_USBCFG": {"command": 'AT+QCFG="USBCFG"', "expected_response": "+QCFG", "parser": parse_usb_config_response},
    "ENABLE_VOICE_OVER_USB": {"command": "AT+QPCMV=1,{}", "expected_response": "OK"},
    "DISABLE_VOICE_OVER_USB": {"command": "AT+QPCMV=0", "expected_response": "OK"},
    "GET_VOICE_OVER_USB_STATUS": {"command": "AT+QPCMV?", "expected_response": "+QPCMV", "parser": parse_voice_over_usb_status_response},
}
