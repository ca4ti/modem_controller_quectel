# src/modem/modem_commands.py
import re
import logging

logger = logging.getLogger(__name__)

# --- Funções de Parsing para Respostas de Comandos AT ---

def parse_ati_response(response: str) -> dict:
    """
    Parses the ATI response to extract modem information.
    Example:
    ATI
    Quectel
    EC25
    Revision: EC25AUFAR06A03M4G
    OK
    """
    info = {}
    lines = response.strip().split('\n')
    for line in lines:
        if "Quectel" in line:
            info['Manufacturer'] = line.strip()
        elif "EC" in line and "Revision" not in line:
            info['Model'] = line.strip()
        elif "Revision" in line:
            info['Revision'] = line.split(':', 1)[1].strip()
    return info

def parse_csq_response(response: str) -> dict:
    """
    Parses the AT+CSQ response to extract signal quality (RSSI and BER).
    Example: +CSQ: 18,99
    """
    match = re.search(r'\+CSQ:\s*(\d+),(\d+)', response)
    if match:
        rssi_val = int(match.group(1))
        ber_val = int(match.group(2))

        # Convert RSSI value to dBm
        if rssi_val == 0:
            rssi_dbm = -113 # dBm or less
        elif rssi_val == 1:
            rssi_dbm = -111 # dBm
        elif 2 <= rssi_val <= 30:
            rssi_dbm = -113 + (rssi_val * 2) # dBm
        elif rssi_val == 31:
            rssi_dbm = -51 # dBm or greater
        elif rssi_val == 99:
            rssi_dbm = "Not detectable"
        else:
            rssi_dbm = "Unknown"

        # Interpret BER value
        if ber_val >= 0 and ber_val <= 7:
            ber_interpretation = f"{ber_val} (0.16% to 12.8%)"
        elif ber_val == 99:
            ber_interpretation = "Not detectable"
        else:
            ber_interpretation = f"{ber_val} (Unknown)"

        return {
            "RSSI": rssi_dbm,
            "BER": ber_interpretation
        }
    return {"RSSI": "N/A", "BER": "N/A"}


def parse_creg_response(response: str) -> dict:
    """
    Parses the AT+CREG? response to extract network registration status.
    Example: +CREG: 0,1
    """
    match = re.search(r'\+CREG:\s*(\d+),(\d+)', response)
    if match:
        n = int(match.group(1)) # Not used in current interpretation but kept for completeness
        stat = int(match.group(2))

        status_map = {
            0: "Not registered, ME is not currently searching a new operator to register to",
            1: "Registered, home network",
            2: "Not registered, but ME is currently searching a new operator to register to",
            3: "Registration denied",
            4: "Unknown (e.g. out of GERAN/UTRAN/E-UTRAN coverage)",
            5: "Registered, roaming",
            6: "Registered for 'SMS only', home network (applicable only when PS is not active)",
            7: "Registered for 'SMS only', roaming (applicable only when PS is not active)",
            8: "Registered for 'CSFB not preferred', home network (applicable only when PS is not active)",
            9: "Registered for 'CSFB not preferred', roaming (applicable only when PS is not active)"
        }
        return {"Network Registration Status": status_map.get(stat, "Unknown Status")}
    return {"Network Registration Status": "N/A"}

def parse_qnwinfo_response(response: str) -> dict:
    """
    Parses the AT+QNWINFO response to extract network information.
    Example: +QNWINFO: "FDD LTE","22288","LTE BAND 3",1650
    """
    match = re.search(r'\+QNWINFO:\s*"([^"]*)","([^"]*)","([^"]*)",(\d+)', response)
    if match:
        tech = match.group(1)
        mccmnc = match.group(2)
        band = match.group(3)
        channel = match.group(4)
        return {
            "Technology": tech,
            "Operator (MCCMNC)": mccmnc,
            "Band": band,
            "Channel": channel
        }
    return {
        "Technology": "N/A",
        "Operator (MCCMNC)": "N/A",
        "Band": "N/A",
        "Channel": "N/A"
    }

def parse_qeng_response(response: str) -> dict:
    """
    Parses the AT+QENG="servingcell" response for detailed serving cell info.
    This parser is more complex due to varying formats.
    Example (LTE): +QENG: "servingcell","LTE","FDD",222,88,3004001,137,3,1650,20,3,3,-101,-14,-72,13,5,12,-
    """
    info = {}
    # Clean the response to ensure it's a single line for easier regex matching
    response = response.replace('\r', '').replace('\n', '')

    # Regex for LTE serving cell
    match_lte = re.search(r'\+QENG:\s*"servingcell","LTE","(FDD|TDD)",(\d+),(\d+),([\da-fA-F]+),(\d+),(\d+),(\d+),(\d+),(\d+),(\d+),(-?\d+),(-?\d+),(-?\d+),(-?\d+),(-?\d+),(-?\d+),(.+)', response)
    if match_lte:
        info["Cell Type"] = "Serving Cell"
        info["Network Type"] = "LTE"
        info["Duplex Mode"] = match_lte.group(1)
        info["MCC"] = match_lte.group(2)
        info["MNC"] = match_lte.group(3)
        info["Cell ID"] = match_lte.group(4)
        info["Physical Cell ID"] = match_lte.group(5)
        info["Band"] = match_lte.group(6)
        info["EARFCN"] = match_lte.group(7)
        info["Bandwidth"] = match_lte.group(8)
        info["UL Bandwidth"] = match_lte.group(9)
        info["DL Bandwidth"] = match_lte.group(10)
        info["RSSI"] = match_lte.group(11)
        info["RSRP"] = match_lte.group(12)
        info["RSRQ"] = match_lte.group(13)
        info["SNR"] = match_lte.group(14)
        info["TX Power"] = match_lte.group(15)
        info["Timing Advance"] = match_lte.group(16)
        info["DRX Cycle"] = match_lte.group(17) # This might be the last group, depending on firmware
        return info

    # Add parsers for other network types (GSM, WCDMA) if needed
    # Example for GSM: +QENG: "servingcell","GPRS","GSM",222,88,1234,123,34,56,78,90,123,456
    match_gsm = re.search(r'\+QENG:\s*"servingcell","(GPRS|EDGE|GSM)",(\d+),(\d+),([\da-fA-F]+),(\d+),(\d+),(\d+),(\d+),(\d+),(\d+),(\d+)', response)
    if match_gsm:
        info["Cell Type"] = "Serving Cell"
        info["Network Type"] = match_gsm.group(1)
        info["MCC"] = match_gsm.group(2)
        info["MNC"] = match_gsm.group(3)
        info["LAC"] = match_gsm.group(4) # Location Area Code
        info["Cell ID"] = match_gsm.group(5)
        info["BSIC"] = match_gsm.group(6) # Base Station Identity Code
        info["Channel"] = match_gsm.group(7)
        info["RxQual"] = match_gsm.group(8)
        info["RxLev"] = match_gsm.group(9)
        info["TxPower"] = match_gsm.group(10)
        info["Timing Advance"] = match_gsm.group(11)
        return info

    logger.warning(f"No QENG parser matched for response: {response}")
    return {"Serving Cell Info": "N/A"}


def parse_qeng_neighbor_response(response: str) -> dict:
    """
    Parses AT+QENG="neighbourcell" response.
    Example (LTE): +QENG: "neighbourcell","LTE",222,88,137,3,1650,20,-105,-15,-78
    """
    neighbor_cells = []
    # Split response by lines and process each line that starts with +QENG: "neighbourcell"
    lines = response.strip().split('\n')
    for line in lines:
        if line.startswith('+QENG: "neighbourcell"'):
            # Clean the line to ensure it's a single line for easier regex matching
            line = line.replace('\r', '')

            # Regex for LTE neighbor cell
            match_lte = re.search(r'\+QENG:\s*"neighbourcell","LTE",(\d+),(\d+),(\d+),(\d+),(\d+),(\d+),(-?\d+),(-?\d+),(-?\d+)', line)
            if match_lte:
                neighbor_cells.append({
                    "Network Type": "LTE",
                    "MCC": match_lte.group(1),
                    "MNC": match_lte.group(2),
                    "Physical Cell ID": match_lte.group(3),
                    "Band": match_lte.group(4),
                    "EARFCN": match_lte.group(5),
                    "Bandwidth": match_lte.group(6),
                    "RSRP": match_lte.group(7),
                    "RSRQ": match_lte.group(8),
                    "SNR": match_lte.group(9)
                })
                continue # Move to next line

            # Add parsers for other network types (GSM, WCDMA) if needed
            # Example for GSM: +QENG: "neighbourcell","GSM",222,88,1234,123,34,56,78,90,123,456
            match_gsm = re.search(r'\+QENG:\s*"neighbourcell","GSM",(\d+),(\d+),([\da-fA-F]+),(\d+),(\d+),(\d+),(\d+),(\d+)', line)
            if match_gsm:
                neighbor_cells.append({
                    "Network Type": "GSM",
                    "MCC": match_gsm.group(1),
                    "MNC": match_gsm.group(2),
                    "LAC": match_gsm.group(3),
                    "Cell ID": match_gsm.group(4),
                    "BSIC": match_gsm.group(5),
                    "Channel": match_gsm.group(6),
                    "RxLev": match_gsm.group(7),
                    "RxQual": match_gsm.group(8)
                })
                continue

            logger.warning(f"No QENG neighbourcell parser matched for line: {line}")

    if not neighbor_cells:
        return {"Neighbor Cells": "N/A"}
    return {"Neighbor Cells": neighbor_cells}


def parse_qgmr_response(response: str) -> dict:
    """
    Parses the AT+QGMR response to extract firmware version.
    Example: EC25AUFAR06A03M4G
    """
    # The firmware version is often the first non-empty line after the command echo.
    lines = response.strip().split('\n')
    for line in lines:
        line = line.strip()
        if line and not line.startswith('AT') and not line.startswith('OK') and not line.startswith('ERROR'):
            return {"Firmware Version": line}
    return {"Firmware Version": "N/A"}

def parse_qgmi_response(response: str) -> dict:
    """
    Parses the AT+QGMI response to extract manufacturer information.
    Example: Quectel
    """
    lines = response.strip().split('\n')
    for line in lines:
        line = line.strip()
        if line and not line.startswith('AT') and not line.startswith('OK') and not line.startswith('ERROR'):
            return {"Manufacturer": line}
    return {"Manufacturer": "N/A"}

def parse_qgsn_response(response: str) -> dict:
    """
    Parses the AT+QGSN response to extract IMEI.
    Example: 86xxxxxxxxxxxxxxx
    """
    match = re.search(r'^\s*(\d{15,16})\s*$', response, re.MULTILINE)
    if match:
        return {"IMEI": match.group(1)}
    return {"IMEI": "N/A"}

def parse_qccid_response(response: str) -> dict:
    """
    Parses the AT+QCCID response to extract ICCID.
    Example: +QCCID: 89xxxxxxxxxxxxxxxxxxx
    """
    match = re.search(r'\+QCCID:\s*(\d+)', response)
    if match:
        return {"ICCID": match.group(1)}
    return {"ICCID": "N/A"}

def parse_qsimstat_response(response: str) -> dict:
    """
    Parses the AT+QSIMSTAT? response to get SIM card status.
    Example: +QSIMSTAT: 1,1
    """
    match = re.search(r'\+QSIMSTAT:\s*(\d),(\d)', response)
    if match:
        status_map = {
            0: "Not detected",
            1: "Detected"
        }
        # The second digit usually indicates the status after detection (e.g., 0=not ready, 1=ready)
        sim_status = status_map.get(int(match.group(2)), "Unknown")
        return {"SIM Status": sim_status}
    return {"SIM Status": "N/A"}

def parse_cpin_response(response: str) -> dict:
    """
    Parses the AT+CPIN? response to get SIM PIN status.
    Example: +CPIN: READY
    """
    match = re.search(r'\+CPIN:\s*(\w+)', response)
    if match:
        return {"PIN Status": match.group(1)}
    return {"PIN Status": "N/A"}

def parse_qcfg_urc_response(response: str) -> dict:
    """
    Parses the AT+QCFG="urc/ri/ring" response.
    Example: +QCFG: "urc/ri/ring",1
    """
    match = re.search(r'\+QCFG:\s*"urc/ri/ring",(\d)', response)
    if match:
        status = "Enabled" if match.group(1) == "1" else "Disabled"
        return {"URC Ring Indication": status}
    return {"URC Ring Indication": "N/A"}

def parse_qcfg_urc_port_response(response: str) -> dict:
    """
    Parses the AT+QCFG="urc/port" response.
    Example: +QCFG: "urc/port","usbat"
    """
    match = re.search(r'\+QCFG:\s*"urc/port","([^"]+)"', response)
    if match:
        return {"URC Port": match.group(1)}
    return {"URC Port": "N/A"}

def parse_qcfg_urc_all_response(response: str) -> dict:
    """
    Parses the AT+QCFG="urc/all" response.
    Example: +QCFG: "urc/all",1
    """
    match = re.search(r'\+QCFG:\s*"urc/all",(\d)', response)
    if match:
        status = "Enabled" if match.group(1) == "1" else "Disabled"
        return {"All URCs Enabled": status}
    return {"All URCs Enabled": "N/A"}

def parse_qcfg_urc_baud_response(response: str) -> dict:
    """
    Parses the AT+QCFG="urc/baud" response.
    Example: +QCFG: "urc/baud",115200
    """
    match = re.search(r'\+QCFG:\s*"urc/baud",(\d+)', response)
    if match:
        return {"URC Baudrate": int(match.group(1))}
    return {"URC Baudrate": "N/A"}

def parse_qcfg_urc_data_response(response: str) -> dict:
    """
    Parses the AT+QCFG="urc/data" response.
    Example: +QCFG: "urc/data",1
    """
    match = re.search(r'\+QCFG:\s*"urc/data",(\d)', response)
    if match:
        status = "Enabled" if match.group(1) == "1" else "Disabled"
        return {"URC Data Indication": status}
    return {"URC Data Indication": "N/A"}

def parse_qcfg_urc_psm_response(response: str) -> dict:
    """
    Parses the AT+QCFG="urc/psm" response.
    Example: +QCFG: "urc/psm",1
    """
    match = re.search(r'\+QCFG:\s*"urc/psm",(\d)', response)
    if match:
        status = "Enabled" if match.group(1) == "1" else "Disabled"
        return {"URC PSM Indication": status}
    return {"URC PSM Indication": "N/A"}

def parse_qcfg_urc_power_response(response: str) -> dict:
    """
    Parses the AT+QCFG="urc/poweron" and "urc/poweroff" responses.
    Example: +QCFG: "urc/poweron",1
    """
    match = re.search(r'\+QCFG:\s*"urc/(poweron|poweroff)",(\d)', response)
    if match:
        type_urc = match.group(1)
        status = "Enabled" if match.group(2) == "1" else "Disabled"
        return {f"URC {type_urc.capitalize()} Indication": status}
    return {f"URC Power Indication": "N/A"} # Generic fallback

def parse_qcfg_urc_wakeup_response(response: str) -> dict:
    """
    Parses the AT+QCFG="urc/wakeup" response.
    Example: +QCFG: "urc/wakeup",1
    """
    match = re.search(r'\+QCFG:\s*"urc/wakeup",(\d)', response)
    if match:
        status = "Enabled" if match.group(1) == "1" else "Disabled"
        return {"URC Wakeup Indication": status}
    return {"URC Wakeup Indication": "N/A"}

def parse_qcfg_urc_csq_response(response: str) -> dict:
    """
    Parses the AT+QCFG="urc/csq" response.
    Example: +QCFG: "urc/csq",1,5
    """
    match = re.search(r'\+QCFG:\s*"urc/csq",(\d),(\d)', response)
    if match:
        status = "Enabled" if match.group(1) == "1" else "Disabled"
        interval = int(match.group(2))
        return {"URC CSQ Indication": status, "CSQ Report Interval": f"{interval}s"}
    return {"URC CSQ Indication": "N/A", "CSQ Report Interval": "N/A"}

# --- Dicionário de Comandos AT e seus Parsers ---
# Mapeia o nome abstrato do comando para o comando AT real e sua função de parsing.
MODEM_COMMANDS = {
    # Informações Básicas do Modem
    "GET_MODEM_INFO": {"command": "ATI", "parser": parse_ati_response},
    "GET_FIRMWARE_VERSION": {"command": "AT+QGMR", "parser": parse_qgmr_response},
    "GET_MANUFACTURER_INFO": {"command": "AT+QGMI", "parser": parse_qgmi_response},
    "GET_IMEI": {"command": "AT+CGSN", "parser": parse_qgsn_response},
    "GET_ICCID": {"command": "AT+QCCID", "parser": parse_qccid_response},

    # Status da Rede e Sinal
    "GET_SIGNAL_QUALITY": {"command": "AT+CSQ", "parser": parse_csq_response},
    "GET_NETWORK_REGISTRATION_STATUS": {"command": "AT+CREG?", "parser": parse_creg_response},
    "GET_NETWORK_INFO": {"command": "AT+QNWINFO", "parser": parse_qnwinfo_response},
    "GET_SERVING_CELL_INFO": {"command": 'AT+QENG="servingcell"', "parser": parse_qeng_response},
    "GET_NEIGHBOR_CELL_INFO": {"command": 'AT+QENG="neighbourcell"', "parser": parse_qeng_neighbor_response},

    # Status do SIM
    "GET_SIM_STATUS": {"command": "AT+QSIMSTAT?", "parser": parse_qsimstat_response},
    "GET_PIN_STATUS": {"command": "AT+CPIN?", "parser": parse_cpin_response},

    # Configurações URC (Unsolicited Result Codes)
    "GET_URC_RI_RING_STATUS": {"command": 'AT+QCFG="urc/ri/ring"', "parser": parse_qcfg_urc_response},
    "SET_URC_RI_RING_ENABLE": {"command": 'AT+QCFG="urc/ri/ring",1', "parser": None},
    "SET_URC_RI_RING_DISABLE": {"command": 'AT+QCFG="urc/ri/ring",0', "parser": None},

    "GET_URC_PORT_STATUS": {"command": 'AT+QCFG="urc/port"', "parser": parse_qcfg_urc_port_response},
    "SET_URC_PORT_USBAT": {"command": 'AT+QCFG="urc/port","usbat"', "parser": None},
    "SET_URC_PORT_USBMODEM": {"command": 'AT+QCFG="urc/port","usbmodem"', "parser": None},

    "GET_URC_ALL_STATUS": {"command": 'AT+QCFG="urc/all"', "parser": parse_qcfg_urc_all_response},
    "SET_URC_ALL_ENABLE": {"command": 'AT+QCFG="urc/all",1', "parser": None},
    "SET_URC_ALL_DISABLE": {"command": 'AT+QCFG="urc/all",0', "parser": None},

    "GET_URC_BAUD_STATUS": {"command": 'AT+QCFG="urc/baud"', "parser": parse_qcfg_urc_baud_response},
    "SET_URC_BAUD_CUSTOM": {"command_template": 'AT+QCFG="urc/baud",{}', "parser": None}, # Requires baudrate arg

    "GET_URC_DATA_STATUS": {"command": 'AT+QCFG="urc/data"', "parser": parse_qcfg_urc_data_response},
    "SET_URC_DATA_ENABLE": {"command": 'AT+QCFG="urc/data",1', "parser": None},
    "SET_URC_DATA_DISABLE": {"command": 'AT+QCFG="urc/data",0', "parser": None},

    "GET_URC_PSM_STATUS": {"command": 'AT+QCFG="urc/psm"', "parser": parse_qcfg_urc_psm_response},
    "SET_URC_PSM_ENABLE": {"command": 'AT+QCFG="urc/psm",1', "parser": None},
    "SET_URC_PSM_DISABLE": {"command": 'AT+QCFG="urc/psm",0', "parser": None},

    "GET_URC_POWER_STATUS_ON": {"command": 'AT+QCFG="urc/poweron"', "parser": parse_qcfg_urc_power_response},
    "GET_URC_POWER_STATUS_OFF": {"command": 'AT+QCFG="urc/poweroff"', "parser": parse_qcfg_urc_power_response},
    "SET_URC_POWER_ON_ENABLE": {"command": 'AT+QCFG="urc/poweron",1', "parser": None},
    "SET_URC_POWER_ON_DISABLE": {"command": 'AT+QCFG="urc/poweron",0', "parser": None},
    "SET_URC_POWER_OFF_ENABLE": {"command": 'AT+QCFG="urc/poweroff",1', "parser": None},
    "SET_URC_POWER_OFF_DISABLE": {"command": 'AT+QCFG="urc/poweroff",0', "parser": None},

    "GET_URC_WAKEUP_STATUS": {"command": 'AT+QCFG="urc/wakeup"', "parser": parse_qcfg_urc_wakeup_response},
    "SET_URC_WAKEUP_ENABLE": {"command": 'AT+QCFG="urc/wakeup",1', "parser": None},
    "SET_URC_WAKEUP_DISABLE": {"command": 'AT+QCFG="urc/wakeup",0', "parser": None},

    "GET_URC_CSQ_STATUS": {"command": 'AT+QCFG="urc/csq"', "parser": parse_qcfg_urc_csq_response},
    "SET_URC_CSQ_ENABLE": {"command_template": 'AT+QCFG="urc/csq",1,{}', "parser": None}, # Requires interval arg
    "SET_URC_CSQ_DISABLE": {"command": 'AT+QCFG="urc/csq",0,0', "parser": None},

    # Outros comandos úteis (adicionar conforme necessário)
    "REBOOT_MODEM": {"command": "AT+CFUN=1,1", "parser": None}, # Full functionality, reset
    "GET_LOCAL_TIME": {"command": "AT+CCLK?", "parser": None}, # Example, parser needed
    "SET_LOCAL_TIME": {"command_template": 'AT+CCLK="{}"', "parser": None}, # Example, parser needed
    "GET_IP_ADDRESS": {"command": "AT+QIACT?", "parser": None}, # Example, parser needed
    "ACTIVATE_PDP_CONTEXT": {"command": "AT+QIACT=1", "parser": None}, # Example, parser needed
    "DEACTIVATE_PDP_CONTEXT": {"command": "AT+QIDEACT=1", "parser": None}, # Example, parser needed
}
