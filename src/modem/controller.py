# src/modem/controller.py
import serial
import time
import threading
import re
import datetime
import PySimpleGUI as sg 

# Importações de módulos internos do projeto
from src.modem.at_commands import AT_COMMANDS # AGORA IMPORTA DE at_commands.py
from src.utils.threading_utils import gui_update_event 
from src.logger.logger import setup_logger

# Configura o logger para este módulo
logger = setup_logger(__name__)

class ModemController:
    """
    Gerencia a comunicação serial com o modem Quectel, enviando comandos AT
    e processando as respostas.
    """
    def __init__(self, port=None, baudrate=115200, timeout=1):
        self.port = port
        self.baudrate = baudrate
        self.timeout = timeout
        self.serial_port = None
        self.response_buffer = "" # Buffer para armazenar respostas parciais
        self.urc_callback = None # Callback para URCs
        self.response_event = threading.Event() # Evento para sinalizar nova resposta
        self.current_response = "" # Armazena a resposta completa do último comando
        self.response_lock = threading.Lock() # Lock para proteger o acesso a current_response
        self._read_thread = None
        self._stop_read_thread = threading.Event()
        logger.debug(f"ModemController: __init__ para porta {port}, baudrate {baudrate}, timeout {timeout}")

        # Regex para URCs conhecidos (agora como atributo da instância)
        self.urc_patterns = {
            "CMT": r'\+CMT:\s*"(?P<number>[^"]*)","(?P<alpha>[^"]*)","(?P<timestamp>[^"]*)"\r\n(?P<message>[\s\S]*?)(?=\r\n(OK|ERROR|\+CMT:|\+CMTI:|\+QIND:|\+CPIN:|\+QSIMSTAT:|\+CSQ:|\+CREG:|\+CGREG:|\+CEREG:|$))',
            "CMTI": r'\+CMTI:\s*"(?P<mem>[^"]*)",(?P<index>\d+)',
            "RING": r'RING',
            "QIND": r'\+QIND:\s*"(?P<indication>[^"]*)"(?:,\s*(?P<value>[^"]*))?',
            "CPIN": r'\+CPIN:\s*"(?P<status>[^"]*)"',
            "QSIMSTAT": r'\+QSIMSTAT:\s*(?P<enable_stat>\d),(?P<inserted_stat>\d)',
            "CSQ": r'\+CSQ:\s*(?P<rssi>\d+),(?P<ber>\d+)',
            "CREG": r'\+CREG:\s*(\d+),(\d+)(?:,"([0-9A-F]*)","([0-9A-F]*)",(\d*))?',
            "CGREG": r'\+CGREG:\s*(\d+),(\d+)(?:,"([0-9A-F]*)","([0-9A-F]*)",(\d*))?',
            "CEREG": r'\+CEREG:\s*(\d+),(\d+)(?:,"([0-9A-F]*)","([0-9A-F]*)",(\d*)(?:,(\d*),(\d*))?)?',
        }


    def connect_modem(self):
        """
        Tenta conectar ao modem via porta serial com logs extremamente detalhados.
        """
        if self.serial_port and self.serial_port.is_open:
            logger.info(f"ConnectModem: Já conectado à porta {self.port}.")
            return True

        logger.info(f"ConnectModem: Iniciando tentativa de conexão para porta {self.port}...")
        try:
            # Etapa de limpeza: Tenta fechar qualquer resquício de porta
            if self.serial_port:
                if self.serial_port.is_open:
                    logger.debug("ConnectModem: Porta serial estava aberta, tentando fechar antes de reabrir.")
                    self.serial_port.close()
                self.serial_port = None # Limpa a referência antiga
                logger.debug("ConnectModem: Referência de serial_port antiga limpa.")

            time.sleep(0.1) # Pequena pausa para garantir que a porta esteja livre após a limpeza

            logger.debug(f"ConnectModem: Chamando serial.Serial() com port={self.port}, baudrate={self.baudrate}, timeout={self.timeout}, rtscts=False, dsrdtr=False, xonxoff=False.")
            self.serial_port = serial.Serial(
                self.port,
                self.baudrate,
                timeout=self.timeout,
                write_timeout=self.timeout,
                rtscts=False, # Desabilita Request To Send / Clear To Send hardware flow control
                dsrdtr=False, # Desabilita Data Set Ready / Data Terminal Ready hardware flow control
                xonxoff=False # Desabilita software flow control
            )
            logger.debug("ConnectModem: serial.Serial() constructor executado.")

            time.sleep(1) # AJUSTADO: Pausa para estabilização após abertura (aumentado de 0.5s para 1s)

            if self.serial_port.is_open:
                logger.debug(f"ConnectModem: Porta {self.port} confirmada como ABERTA. Tentando configurar DTR/RTS.")
                # Tenta forçar DTR/RTS para um estado conhecido (por vezes é necessário para modems)
                try:
                    # REMOVIDAS/COMENTADAS as linhas de manipulação de DTR/RTS
                    # self.serial_port.setDTR(True) # Data Terminal Ready
                    # self.serial_port.setRTS(True) # Request To Send
                    # time.sleep(0.1) 
                    # self.serial_port.setDTR(False)
                    # self.serial_port.setRTS(False)
                    logger.debug("ConnectModem: DTR/RTS forçados para estado conhecido (ação removida/comentada).")
                except Exception as e:
                    logger.warning(f"ConnectModem: Não foi possível forçar DTR/RTS: {e}")

                logger.info(f"ConnectModem: Porta {self.port} aberta com sucesso. Realizando teste ATI para identificação do modem.")
                
                # Envia ATI e espera a resposta, crucial para o Auto-Discovery
                test_ati_response = self._send_ati_for_discovery()
                
                if test_ati_response and "Quectel" in test_ati_response and "OK" in test_ati_response:
                    logger.info(f"ConnectModem: Modem Quectel identificado na porta {self.port}. Conexão bem-sucedida.")
                    self._start_read_thread() # Inicia a thread de leitura APENAS se o ATI for bem-sucedido.
                    return True
                else:
                    logger.warning(f"ConnectModem: Porta {self.port} aberta, mas modem Quectel NÃO RESPONDEU ATI adequadamente. Resposta: {repr(test_ati_response)}. Fechando porta.")
                    self.disconnect_modem()
                    return False
            else:
                logger.error(f"ConnectModem: FALHA na abertura da porta {self.port}. self.serial_port.is_open é False após o construtor Serial().")
                self.serial_port = None 
                return False
        except serial.SerialException as e:
            logger.error(f"ConnectModem: ERRO CRÍTICO (SerialException) ao abrir/conectar {self.port}: {e}. Verifique se a porta está em uso, desconecte/reconecte o modem ou reinicie o PC. Traceback:", exc_info=True)
            self.serial_port = None
            return False
        except Exception as e:
            logger.error(f"ConnectModem: ERRO INESPERADO ao conectar à porta {self.port}: {e}", exc_info=True) # exc_info=True para traceback completo
            self.serial_port = None
            return False

    def _send_ati_for_discovery(self):
        """
        Envia ATI para testar o modem durante o auto-discovery.
        Usa uma leitura bloqueante direta para este teste específico.
        """
        logger.debug("_send_ati_for_discovery: Enviando ATI...")
        if not self.serial_port or not self.serial_port.is_open:
            logger.warning("_send_ati_for_discovery: Porta não está aberta para enviar ATI.")
            return None

        try:
            self.serial_port.flushInput() # AJUSTADO: Mover esta linha para AQUI (antes de enviar o comando)
            self.serial_port.write(b'ATI\r\n')
            logger.debug("_send_ati_for_discovery: 'ATI\\r\\n' enviado. Limpando buffer de entrada.")
            # self.serial_port.flushInput() # REMOVER esta linha daqui (chamada duplicada)
            response_lines = []
            start_time = time.time()
            
            while time.time() - start_time < 3: # AJUSTADO: Timeout de 2 para 3 segundos
                if self.serial_port.in_waiting > 0:
                    line_bytes = self.serial_port.readline()
                    line = line_bytes.decode('utf-8', errors='ignore').strip()
                    if line:
                        response_lines.append(line)
                        logger.debug(f"_send_ati_for_discovery: Linha lida: {repr(line)}")
                        if "OK" in line or "ERROR" in line: # Encerra leitura ao ver OK/ERROR
                            logger.debug(f"_send_ati_for_discovery: 'OK' ou 'ERROR' detectado, encerrando leitura.")
                            break
                time.sleep(0.01)
            full_response = "\n".join(response_lines)
            logger.debug(f"_send_ati_for_discovery: Resposta ATI completa: {repr(full_response)}")
            return full_response
        except Exception as e:
            logger.warning(f"_send_ati_for_discovery: Erro durante teste ATI para discovery: {e}", exc_info=True)
            return None

    def disconnect_modem(self):
        """
        Desconecta do modem, fechando a porta serial.
        """
        logger.info(f"DisconnectModem: Iniciando desconexão da porta {self.port}.")
        if self.serial_port and self.serial_port.is_open:
            logger.debug("DisconnectModem: Sinalizando para a thread de leitura parar.")
            self._stop_read_thread.set() # Sinaliza para a thread parar
            if self._read_thread and self._read_thread.is_alive():
                logger.debug("DisconnectModem: Aguardando thread de leitura terminar.")
                self._read_thread.join(timeout=2) # Espera a thread terminar
                if self._read_thread.is_alive():
                    logger.warning("DisconnectModem: Thread de leitura não terminou a tempo durante a desconexão.")
            
            try:
                self.serial_port.close()
                logger.info(f"DisconnectModem: Desconectado da porta {self.port}.")
                return True
            except Exception as e:
                logger.error(f"DisconnectModem: Erro ao fechar a porta serial {self.port}: {e}", exc_info=True)
                return False
            finally:
                self.serial_port = None # Garante que a referência é nula
        else:
            logger.info("DisconnectModem: Modem já desconectado ou porta não estava aberta.")
        return False

    def _start_read_thread(self):
        """Inicia a thread para leitura contínua da porta serial."""
        logger.debug("_start_read_thread: Limpando stop_event e iniciando thread.")
        self._stop_read_thread.clear()
        self._read_thread = threading.Thread(target=self._read_serial_data, daemon=True)
        self._read_thread.start()
        logger.debug("Thread de leitura serial iniciada.")

    def _read_serial_data(self):
        """
        Lê dados da porta serial continuamente e processa URCs e respostas.
        """
        logger.debug("_read_serial_data: Thread de leitura serial ativa.")
        while not self._stop_read_thread.is_set():
            try:
                if self.serial_port and self.serial_port.is_open:
                    if self.serial_port.in_waiting > 0:
                        data = self.serial_port.read(self.serial_port.in_waiting).decode('utf-8', errors='ignore')
                        self.response_buffer += data
                        logger.debug(f"_read_serial_data: Dados brutos recebidos: {repr(data)}")
                        
                        # Processa o buffer para URCs e respostas de comandos
                        self._process_buffer()
                time.sleep(0.01) # Pequena pausa para evitar busy-waiting
            except serial.SerialException as e:
                logger.error(f"_read_serial_data: Erro de leitura serial na thread: {e}", exc_info=True)
                break
            except Exception as e:
                logger.error(f"_read_serial_data: Erro inesperado na thread de leitura: {e}", exc_info=True)
                break
        logger.debug("Thread de leitura serial encerrada.")


    def _process_buffer(self):
        """
        Processa o buffer de resposta, priorizando respostas de comando (OK/ERROR)
        e depois URCs.
        """
        # PRIORITY 1: Check for a complete command response (ending in OK/ERROR)
        # This loop ensures we process all complete command responses if they arrive in a chunk.
        command_response_processed = True
        while command_response_processed:
            command_response_processed = False
            if "\r\nOK\r\n" in self.response_buffer or "\r\nERROR\r\n" in self.response_buffer:
                ok_index = self.response_buffer.find("\r\nOK\r\n")
                error_index = self.response_buffer.find("\r\nERROR\r\n")

                if ok_index != -1 and (error_index == -1 or ok_index < error_index):
                    end_index = ok_index + len("\r\nOK\r\n")
                elif error_index != -1 and (ok_index == -1 or error_index < ok_index):
                    end_index = error_index + len("\r\nERROR\r\n")
                else:
                    # Should not happen if OK/ERROR is found but not at proper end
                    break 

                with self.response_lock:
                    self.current_response = self.response_buffer[:end_index].strip()
                    self.response_buffer = self.response_buffer[end_index:] # Remove processed part
                    self.response_event.set() # Signal that a response is available
                logger.debug(f"_process_buffer: Resposta completa de comando processada: {repr(self.current_response)}")
                command_response_processed = True # Continue checking for more full command responses
            else:
                break # No full command response found, proceed to URCs

        # PRIORITY 2: Process remaining buffer for URCs
        # Iterate over lines, as URCs are typically line-based.
        # Use a temporary list of lines to allow removal of processed URCs.
        lines = self.response_buffer.split('\r\n')
        new_response_buffer_lines = []
        urc_processed_in_this_pass = False

        for i, line in enumerate(lines):
            stripped_line = line.strip()
            if not stripped_line: # Skip empty lines
                continue

            found_urc_match = False
            for urc_name, pattern in self.urc_patterns.items(): # Use self.urc_patterns
                match = re.fullmatch(pattern, stripped_line) # Use fullmatch for whole line URCs
                if match:
                    logger.info(f"_process_buffer: URC '{urc_name}' detectado na linha: {stripped_line}")
                    payload = tuple(match.group(name) for name in match.groupdict() if match.group(name) is not None)
                    
                    # Special handling for CMT multi-line URCs: The pattern already captures the message content.
                    if urc_name == "CMT" and len(payload) == 4:
                        # Payload already contains (number, alpha, timestamp, message). No extra readline needed here.
                        pass
                    
                    if self.urc_callback: # Call the URC monitor's handler (if set)
                        logger.debug(f"_process_buffer: Enviando URC '{urc_name}' para callback com payload: {payload}")
                        self.urc_callback(urc_name, payload) # Pass URC name and payload

                    found_urc_match = True
                    urc_processed_in_this_pass = True
                    break # Break from inner for loop, found a URC for this line
            
            if not found_urc_match:
                new_response_buffer_lines.append(line) # Keep line if not identified as a URC

        # Update the main response_buffer with lines not consumed by URC processing.
        # Add back the trailing \r\n if it was present and not all lines were consumed.
        if urc_processed_in_this_pass or len(new_response_buffer_lines) < len(lines): # Only update if something was processed/removed
             self.response_buffer = "\r\n".join(new_response_buffer_lines) + ("\r\n" if self.response_buffer.endswith('\r\n') and new_response_buffer_lines else "")
             logger.debug(f"_process_buffer: Buffer após processar URCs: {repr(self.response_buffer)}")
        
        # If no OK/ERROR was found, and no URC was processed, buffer might be incomplete.
        # This function will be called again when more data arrives.


    def send_at_command(self, command, expected_response="OK", timeout=5):
        """
        Envia um comando AT para o modem e espera por uma resposta específica.
        :param command: O comando AT a ser enviado (ex: "AT+CSQ").
        :param expected_response: A string esperada na resposta para considerar sucesso.
        :param timeout: Tempo limite em segundos para esperar pela resposta.
        :return: A resposta completa do modem ou None se houver timeout/erro.
        """
        logger.debug(f"SendAtCommand: Preparando para enviar comando: {command}")
        if not self.serial_port or not self.serial_port.is_open:
            logger.error("SendAtCommand: Porta serial não está aberta. Não é possível enviar comando.")
            return None

        full_command = command + '\r\n'
        logger.debug(f"SendAtCommand: Enviando: {repr(full_command)}")
        try:
            # Garante que o buffer de resposta está limpo antes de enviar um novo comando
            # E que o evento de resposta esteja limpo
            with self.response_lock:
                self.response_buffer = "" 
                self.current_response = ""
            self.response_event.clear() 

            self.serial_port.flushInput() # AJUSTADO: Mover esta linha para AQUI (antes de enviar o comando)
            self.serial_port.write(full_command.encode('utf-8'))
            logger.debug("SendAtCommand: Comando gravado na porta serial. Esperando resposta.")
            # self.serial_port.flushInput() # REMOVER esta linha daqui (chamada duplicada)
            
            start_time = time.time()
            while (time.time() - start_time) < timeout:
                # O processamento do buffer para URCs e para o OK/ERROR do comando ocorre na thread de leitura.
                # A função _process_buffer, que é chamada pela thread de leitura, é responsável por chamar
                # self.response_event.set() quando uma resposta completa (terminada em OK/ERROR) for encontrada.
                if self.response_event.wait(0.1): # Espera pelo evento com um pequeno timeout
                    with self.response_lock:
                        response = self.current_response
                        self.current_response = "" # Limpa a resposta para o próximo comando
                    
                    logger.debug(f"SendAtCommand: Resposta final recebida: {repr(response)}")
                    if expected_response in response:
                        logger.info(f"SendAtCommand: Comando '{command}' bem-sucedido. Resposta: {response.strip()}")
                        return response.strip()
                    elif "ERROR" in response:
                        logger.warning(f"SendAtCommand: Comando '{command}' resultou em ERRO. Resposta: {response.strip()}")
                        return response.strip()
                    
                    # Se não for a resposta esperada nem ERROR, e não houver mais dados no buffer,
                    # pode ser que um URC tenha consumido a resposta ou algo inesperado.
                    # Limpa o evento para esperar a próxima parte ou URC se o loop continuar.
                    self.response_event.clear() 
            
            logger.warning(f"SendAtCommand: Timeout ({timeout}s) ao esperar resposta para o comando: {command}. Buffer final: {repr(self.response_buffer)}")
            return None

        except serial.SerialException as e:
            logger.error(f"SendAtCommand: Erro serial ao enviar comando '{command}': {e}", exc_info=True)
            return None
        except Exception as e:
            logger.error(f"SendAtCommand: Erro inesperado ao enviar comando '{command}': {e}", exc_info=True)
            return None

    def set_urc_callback(self, callback):
        """Define a função de callback para URCs."""
        self.urc_callback = callback
        logger.debug("URC callback definido.")

    # --- Comandos AT Abstratos ---

    def _send_at_command_and_parse(self, command_name, *args, expected_response="OK", timeout=5):
        """
        Envia um comando AT pré-definido e tenta parsear a resposta.
        :param command_name: Nome do comando no dicionário AT_COMMANDS.
        :param args: Argumentos para formatar o comando.
        :param expected_response: String esperada para sucesso.
        :param timeout: Timeout para a resposta.
        :return: Tupla (sucesso, dados_parseados)
        """
        logger.debug(f"_send_at_command_and_parse: Executando comando abstrato: {command_name} com args: {args}")
        cmd_template = AT_COMMANDS.get(command_name)
        if not cmd_template:
            logger.error(f"_send_at_command_and_parse: Comando '{command_name}' não encontrado no dicionário AT_COMMANDS.")
            return False, None

        try:
            command = cmd_template["command"].format(*args)
        except IndexError:
            logger.error(f"_send_at_command_and_parse: Número incorreto de argumentos para o comando '{command_name}'. Esperado: {cmd_template['command'].count('{')}, Recebido: {len(args)}")
            return False, None

        response = self.send_at_command(command, expected_response=expected_response, timeout=timeout)
        if response and expected_response in response:
            # Se houver um parser definido no AT_COMMANDS, use-o
            if "parser" in cmd_template and callable(cmd_template["parser"]):
                parsed_data = cmd_template["parser"](response)
                logger.debug(f"_send_at_command_and_parse: Comando '{command_name}' parseado com sucesso. Dados: {parsed_data}")
                return True, parsed_data
            logger.debug(f"_send_at_command_and_parse: Comando '{command_name}' bem-sucedido (sem parser).")
            return True, response # Retorna a resposta bruta se não houver parser
        logger.debug(f"_send_at_command_and_parse: Comando '{command_name}' falhou ou resposta inesperada. Resposta bruta: {response}")
        return False, response # Retorna a resposta bruta em caso de falha

    # --- Métodos de Controle Básico ---

    def power_off(self):
        """Desliga o modem."""
        logger.info("PowerOff: Enviando comando de desligamento.")
        success, _ = self._send_at_command_and_parse("POWER_OFF", expected_response="POWERED DOWN", timeout=70) # Timeout maior
        if success:
            logger.info("PowerOff: Modem desligado com sucesso. Aguardando estabilização e desconectando serial.")
            time.sleep(3) 
            self.disconnect_modem() 
        else:
            logger.error("PowerOff: Falha ao desligar o modem.")
        return success

    def reboot(self):
        """Reinicia o modem."""
        logger.info("Reboot: Enviando comando de reinício.")
        success, response = self._send_at_command_and_parse("REBOOT", expected_response="OK", timeout=30)
        if success:
            logger.info("Reboot: Modem reiniciado com sucesso. Reconectando serial...")
            time.sleep(5) # Dar um tempo para o modem reiniciar completamente
            # A reconexão é geralmente tratada pela camada superior (common_handlers/app_main)
            # ou na próxima tentativa de comando.
        else:
            logger.error(f"Reboot: Falha ao reiniciar o modem. Resposta: {response}")
        return success

    def factory_reset(self):
        """Restaura as configurações de fábrica do modem."""
        logger.info("FactoryReset: Enviando comando de reset de fábrica.")
        return self._send_at_command_and_parse("FACTORY_RESET", expected_response="OK")

    def set_urc_output_port(self, port):
        """Define a porta de saída para URCs (Unsolicited Result Codes)."""
        logger.info(f"SetUrcOutputPort: Definindo porta URC para '{port}'.")
        return self._send_at_command_and_parse("SET_URC_OUTPUT_PORT", port, expected_response="OK")

    def get_urc_output_port(self):
        """Lê a porta de saída de URCs."""
        logger.info("GetUrcOutputPort: Lendo porta de saída URC.")
        success, parsed_data = self._send_at_command_and_parse("GET_URC_OUTPUT_PORT", expected_response="+QURCCFG")
        return parsed_data if success else "N/A"

    # --- Métodos de Informação e Status ---

    def get_product_info(self):
        """Obtém informações de identificação do produto (ATI)."""
        logger.info("GetProductInfo: Obtendo informações do produto.")
        success, parsed_data = self._send_at_command_and_parse("PRODUCT_INFO", expected_response="Quectel")
        return parsed_data if success else "N/A"

    def get_imei(self):
        """Obtém o IMEI do modem."""
        logger.info("GetIMEI: Obtendo IMEI.")
        success, parsed_data = self._send_at_command_and_parse("GET_IMEI", expected_response="OK")
        return parsed_data if success else "N/A"

    def get_imsi(self):
        """Obtém o IMSI do SIM."""
        logger.info("GetIMSI: Obtendo IMSI.")
        success, parsed_data = self._send_at_command_and_parse("GET_IMSI", expected_response="OK")
        return parsed_data if success else "N/A"

    def get_iccid(self):
        """Obtém o ICCID do SIM."""
        logger.info("GetICCID: Obtendo ICCID.")
        success, parsed_data = self._send_at_command_and_parse("GET_ICCID", expected_response="+QCCID")
        return parsed_data if success else "N/A"
    
    def get_sim_status(self):
        """Obtém o status de inserção do cartão SIM."""
        logger.info("GetSimStatus: Obtendo status do SIM.")
        success, parsed_data = self._send_at_command_and_parse("GET_SIM_STATUS", expected_response="+QSIMSTAT")
        return parsed_data if success else "N/A"

    def get_battery_status(self):
        """Obtém status de carga e nível da bateria."""
        logger.info("GetBatteryStatus: Obtendo status da bateria.")
        success, parsed_data = self._send_at_command_and_parse("GET_BATTERY_STATUS", expected_response="+CBC")
        return parsed_data if success else "N/A"

    def get_clock(self):
        """Obtém a hora e data do relógio interno do modem."""
        logger.info("GetClock: Obtendo hora e data do modem.")
        success, parsed_data = self._send_at_command_and_parse("GET_CLOCK", expected_response="+CCLK")
        return parsed_data if success else "N/A"

    def get_adc_value(self, channel):
        """Lê o valor de voltagem de um canal ADC."""
        logger.info(f"GetADCValue: Lendo valor do ADC no canal {channel}.")
        success, parsed_data = self._send_at_command_and_parse("GET_ADC_VALUE", channel, expected_response="+QADC")
        return parsed_data if success else "N/A"

    # --- Métodos de Rede e APN ---

    def get_signal_quality(self):
        """Obtém a qualidade do sinal (RSSI e BER)."""
        logger.info("GetSignalQuality: Obtendo qualidade do sinal.")
        success, parsed_data = self._send_at_command_and_parse("GET_SIGNAL_QUALITY", expected_response="+CSQ")
        return parsed_data if success else "N/A"

    def get_network_info(self):
        """Consulta informações da rede (tecnologia, operador, banda)."""
        logger.info("GetNetworkInfo: Obtendo informações da rede.")
        success, parsed_data = self._send_at_command_and_parse("GET_NETWORK_INFO", expected_response="+QNWINFO")
        return parsed_data if success else "N/A"

    def get_network_registration_status(self):
        """Obtém o status de registro na rede."""
        logger.info("GetNetworkRegistrationStatus: Obtendo status de registro na rede.")
        success, parsed_data = self._send_at_command_and_parse("GET_NETWORK_REGISTRATION_STATUS", expected_response="+CREG")
        return parsed_data if success else "N/A"

    def define_apn(self, cid, pdp_type, apn, pdp_addr="", data_comp=0, head_comp=0):
        """Define os parâmetros do contexto PDP (APN)."""
        logger.info(f"DefineAPN: Definindo APN {apn} para CID {cid}.")
        return self._send_at_command_and_parse("DEFINE_APN", cid, pdp_type, apn, pdp_addr, data_comp, head_comp, expected_response="OK")

    def activate_pdp_context(self, cid):
        """Ativa o contexto PDP."""
        logger.info(f"ActivatePDPContext: Ativando PDP CID {cid}.")
        return self._send_at_command_and_parse("ACTIVATE_PDP_CONTEXT", cid, expected_response="OK", timeout=150)

    def deactivate_pdp_context(self, cid):
        """Desativa o contexto PDP."""
        logger.info(f"DeactivatePDPContext: Desativando PDP CID {cid}.")
        return self._send_at_command_and_parse("DEACTIVATE_PDP_CONTEXT", cid, expected_response="OK")

    def get_pdp_address(self, cid):
        """Obtém o endereço IP do contexto PDP."""
        logger.info(f"GetPDPAddress: Obtendo endereço PDP para CID {cid}.")
        success, parsed_data = self._send_at_command_and_parse("GET_PDP_ADDRESS", cid, expected_response="+CGPADDR")
        return parsed_data if success else "N/A"

    def set_network_scan_mode(self, mode, effect=1):
        """Define a preferência de tecnologia de rede (2G/3G/4G)."""
        logger.info(f"SetNetworkScanMode: Definindo modo de varredura para {mode}.")
        return self._send_at_command_and_parse("SET_NETWORK_SCAN_MODE", mode, effect, expected_response="OK")

    def get_network_scan_mode(self):
        """Lê a preferência de tecnologia de rede."""
        logger.info("GetNetworkScanMode: Lendo modo de varredura.")
        success, parsed_data = self._send_at_command_and_parse("GET_NETWORK_SCAN_MODE", expected_response="+QCFG")
        return parsed_data if success else "N/A"

    def set_roaming_service(self, mode, effect=1):
        """Habilita/Desabilita o serviço de roaming."""
        logger.info(f"SetRoamingService: Definindo serviço de roaming para {mode}.")
        return self._send_at_command_and_parse("SET_ROAMING_SERVICE", mode, effect, expected_response="OK")

    def get_roaming_service(self):
        """Lê a configuração de roaming."""
        logger.info("GetRoamingService: Lendo configuração de roaming.")
        success, parsed_data = self._send_at_command_and_parse("GET_ROAMING_SERVICE", expected_response="+QCFG")
        return parsed_data if success else "N/A"

    def set_bands(self, gsm_wcdma_band=None, lte_band=None, td_scdma_band=None):
        """Configura as bandas de frequência preferenciais."""
        logger.info(f"SetBands: Definindo bandas GSM/WCDMA:{gsm_wcdma_band}, LTE:{lte_band}, TDS:{td_scdma_band}.")
        return self._send_at_command_and_parse("SET_BANDS", gsm_wcdma_band, lte_band, td_scdma_band, expected_response="OK")

    def get_bands(self):
        """Lê as configurações de banda atuais."""
        logger.info("GetBands: Lendo configurações de banda.")
        success, parsed_data = self._send_at_command_and_parse("GET_BANDS", expected_response="+QCFG")
        return parsed_data if success else "N/A"

    # --- Métodos de Serviço de Mensagens (SMS) ---

    def send_sms(self, number, message):
        """Envia um SMS para o número especificado."""
        logger.info(f"SendSMS: Enviando SMS para {number}.")
        # Para SMS, precisamos de um tratamento especial para o prompt '>'
        success, response = self._send_at_command_and_parse("SEND_SMS_INIT", number, expected_response=">", timeout=10) # Espera pelo prompt
        if success and ">" in response:
            sms_data = message + '\x1A' # Adiciona CTRL+Z
            sms_success, sms_response = self._send_at_command_and_parse("SEND_SMS_CONTENT", sms_data, expected_response="OK", timeout=30)
            if sms_success:
                match = re.search(r'\+CMGS:\s*(\d+)', sms_response)
                if match:
                    logger.info(f"SendSMS: SMS enviado com sucesso. ID da mensagem: {match.group(1)}")
                    return True, f"SMS enviado. ID: {match.group(1)}"
                else:
                    logger.info(f"SendSMS: SMS enviado, mas ID não encontrado. Resposta: {sms_response}")
                    return True, f"SMS enviado. Resposta: {sms_response}"
            else:
                logger.error(f"SendSMS: Falha ao enviar o conteúdo do SMS ou timeout. Resposta: {sms_response}")
                return False, "Falha ao enviar o conteúdo do SMS."
        else:
            logger.error(f"SendSMS: Falha ao obter prompt '>' para enviar SMS. Resposta: {response}")
            return False, "Falha ao iniciar envio de SMS."

    def read_sms_by_index(self, index):
        """Lê uma mensagem SMS específica pelo índice."""
        logger.info(f"ReadSMSByIndex: Lendo SMS no índice {index}.")
        return self._send_at_command_and_parse("READ_SMS_BY_INDEX", index, expected_response="OK")

    def delete_sms_by_index(self, index):
        """Apaga uma mensagem SMS específica pelo índice."""
        logger.info(f"DeleteSMSByIndex: Apagando SMS no índice {index}.")
        return self._send_at_command_and_parse("DELETE_SMS_BY_INDEX", index, expected_response="OK")

    def read_all_sms(self):
        """Lê todas as mensagens SMS da memória."""
        logger.info("ReadAllSMS: Lendo todas as mensagens SMS (simplificado).")
        return self._send_at_command_and_parse("READ_ALL_SMS", expected_response="OK")

    def delete_all_sms(self):
        """Apaga todas as mensagens SMS da memória."""
        logger.info("DeleteAllSMS: Apagando todas as mensagens SMS.")
        return self._send_at_command_and_parse("DELETE_ALL_SMS", expected_response="OK")

    def read_all_sms_messages(self):
        """
        Lê todas as mensagens SMS armazenadas na memória do modem e as retorna formatadas.
        Retorna uma tupla (sucesso, lista_de_mensagens)
        Cada mensagem é um dicionário com chaves como 'index', 'status', 'number', 'timestamp', 'message'.
        """
        logger.info("ReadAllSMSMessages: Lendo todas as mensagens SMS para Inbox/Outbox.")
        success, raw_response = self._send_at_command_and_parse("READ_ALL_SMS_ADVANCED", expected_response="OK", timeout=60)
        
        if not success or not raw_response:
            logger.error(f"ReadAllSMSMessages: Falha ao ler todas as mensagens SMS. Resposta: {raw_response}")
            return False, []

        messages = []
        message_pattern = re.compile(
            r'\+CMGL:\s*(?P<index>\d+),'
            r'\s*"(?P<status>[^"]*)",'
            r'\s*"(?P<number>[^"]*)",'
            r'(?:\s*"(?P<alpha>[^"]*)",)?' 
            r'\s*"(?P<timestamp>[^"]*)"'
            r'(?:,\s*(?P<tooa>[^,]*))?' 
            r'(?:,\s*(?P<toda>[^,]*))?' 
            r'\r\n(?P<message>(?:.|\n)*?)(?=\r\n\+CMGL:|\r\nOK|\r\nERROR|$)',
            re.MULTILINE
        )

        matches = message_pattern.finditer(raw_response)
        
        for match in matches:
            try:
                msg_dict = match.groupdict()
                message_content = msg_dict['message'].strip()
                
                if message_content.endswith("OK"): message_content = message_content[:-2].strip()
                elif message_content.endswith("ERROR"): message_content = message_content[:-5].strip()

                parsed_timestamp = msg_dict['timestamp']
                try:
                    ts_no_zone = parsed_timestamp.split('+')[0]
                    dt_obj = datetime.datetime.strptime(ts_no_zone, "%y/%m/%d,%H:%M:%S")
                    formatted_timestamp = dt_obj.strftime("%Y-%m-%d %H:%M:%S")
                except ValueError:
                    formatted_timestamp = parsed_timestamp 

                messages.append({
                    'index': int(msg_dict['index']),
                    'status': msg_dict['status'],
                    'number': msg_dict['number'],
                    'timestamp': formatted_timestamp,
                    'message': message_content
                })
            except Exception as e:
                logger.error(f"ReadAllSMSMessages: Erro ao parsear mensagem SMS: {match.group(0)} - Erro: {e}", exc_info=True)
                continue 

        logger.info(f"ReadAllSMSMessages: Total de {len(messages)} mensagens parseadas.")
        return True, messages


    # --- Métodos de Serviço de Chamadas ---

    def dial_call(self, number):
        """Faz uma chamada de voz."""
        logger.info(f"DialCall: Discando para {number}.")
        return self._send_at_command_and_parse("DIAL_CALL", number, expected_response="OK", timeout=90)

    def hangup_call(self):
        """Desliga a chamada atual."""
        logger.info("HangupCall: Desligando chamada.")
        return self._send_at_command_and_parse("HANGUP_CALL", expected_response="OK")

    def answer_call(self):
        """Atende uma chamada recebida."""
        logger.info("AnswerCall: Atendendo chamada.")
        return self._send_at_command_and_parse("ANSWER_CALL", expected_response="OK", timeout=90)

    def get_call_status(self):
        """Verifica o status das chamadas ativas."""
        logger.info("GetCallStatus: Verificando status da chamada.")
        success, parsed_data = self._send_at_command_and_parse("GET_CALL_STATUS", expected_response="+CLCC")
        return parsed_data if success else "N/A"

    # --- Métodos de Controle de Áudio ---

    def set_speaker_volume(self, level):
        """Define o volume do alto-falante (0-5)."""
        logger.info(f"SetSpeakerVolume: Definindo volume do alto-falante para {level}.")
        return self._send_at_command_and_parse("SET_SPEAKER_VOLUME", level, expected_response="OK")

    def mute_microphone(self, mute_on=True):
        """Ativa/desativa o mudo do microfone."""
        mode = 1 if mute_on else 0
        logger.info(f"MuteMicrophone: {'Mutando' if mute_on else 'Desmutando'} microfone.")
        return self._send_at_command_and_parse("MUTE_MICROPHONE", mode, expected_response="OK")

    def set_audio_loop_test(self, enable=True):
        """Ativa/desativa o teste de loopback de áudio."""
        mode = 1 if enable else 0
        logger.info(f"SetAudioLoopTest: {'Ativando' if enable else 'Desativando'} loop de áudio.")
        return self._send_at_command_and_parse("SET_AUDIO_LOOP_TEST", mode, expected_response="OK")

    def set_audio_mode(self, mode):
        """Define o modo de áudio (handset, headset, speaker, UAC)."""
        logger.info(f"SetAudioMode: Definindo modo de áudio para {mode}.")
        return self._send_at_command_and_parse("SET_AUDIO_MODE", mode, expected_response="OK")

    def get_audio_mode(self):
        """Lê o modo de áudio atual."""
        logger.info("GetAudioMode: Lendo modo de áudio.")
        success, parsed_data = self._send_at_command_and_parse("GET_AUDIO_MODE", expected_response="+QAUDMOD")
        return parsed_data if success else "N/A"

    def set_mic_gains(self, txgain, txdgain=None):
        """Define os ganhos do microfone."""
        logger.info(f"SetMicGains: Definindo ganhos do microfone (TxGain:{txgain}, TxDGain:{txdgain}).")
        if txdgain is not None:
            return self._send_at_command_and_parse("SET_MIC_GAINS_FULL", txgain, txdgain, expected_response="OK")
        else:
            return self._send_at_command_and_parse("SET_MIC_GAINS_TXGAIN_ONLY", txgain, expected_response="OK")

    def get_mic_gains(self):
        """Lê os ganhos do microfone."""
        logger.info("GetMicGains: Lendo ganhos do microfone.")
        success, parsed_data = self._send_at_command_and_parse("GET_MIC_GAINS", expected_response="+QMIC")
        return parsed_data if success else "N/A"

    def set_rx_gains(self, rxgain):
        """Define os ganhos de downlink (volume de recepção)."""
        logger.info(f"SetRxGains: Definindo ganhos de RX para {rxgain}.")
        return self._send_at_command_and_parse("SET_RX_GAINS", rxgain, expected_response="OK")

    def get_rx_gains(self):
        """Lê os ganhos de downlink."""
        logger.info("GetRxGains: Lendo ganhos de RX.")
        success, parsed_data = self._send_at_command_and_parse("GET_RX_GAINS", expected_response="+QRXGAIN")
        return parsed_data if success else "N/A"

    def config_dai(self, io_mode, audio_mode, fsync_mode, clock_rate, format_type, sample_rate, num_slots, slot_mapping):
        """Configura a interface de áudio digital (DAI/PCM)."""
        logger.info(f"ConfigDAI: Configurando DAI para I/O {io_mode}.")
        return self._send_at_command_and_parse("CONFIG_DAI", io_mode, audio_mode, fsync_mode, clock_rate, format_type, sample_rate, num_slots, slot_mapping, expected_response="OK")

    def get_digital_audio_interface_config(self):
        """Lê a configuração atual da interface de audio digital (DAI) usando AT+QDAI?."""
        logger.info("GetDigitalAudioInterfaceConfig: Lendo configuração DAI.")
        success, parsed_data = self._send_at_command_and_parse("GET_DAI_CONFIG", expected_response="+QDAI")
        return parsed_data if success else "N/A"

    # --- Métodos de GPS e USB ---

    def enable_gps(self):
        """Ativa o módulo GPS."""
        logger.info("EnableGPS: Ativando GPS.")
        return self._send_at_command_and_parse("ENABLE_GPS", expected_response="OK")

    def disable_gps(self):
        """Desativa o módulo GPS."""
        logger.info("DisableGPS: Desativando GPS.")
        return self._send_at_command_and_parse("DISABLE_GPS", expected_response="OK")

    def get_gps_location(self):
        """Obtém as coordenadas GPS atuais."""
        logger.info("GetGPSLocation: Obtendo localização GPS.")
        success, parsed_data = self._send_at_command_and_parse("GET_GPS_LOCATION", expected_response="+QGPSLOC", timeout=15)
        return parsed_data if success else "N/A"

    def set_gps_outport(self, port):
        """Configura a porta de saída NMEA para dados GPS."""
        logger.info(f"SetGPSOutport: Definindo porta de saída GPS NMEA para '{port}'.")
        return self._send_at_command_and_parse("SET_GPS_OUTPORT", port, expected_response="OK")

    def get_gps_outport(self):
        """Lê a porta de saída NMEA do GPS atual."""
        logger.info("GetGPSOutport: Lendo porta de saída GPS NMEA.")
        success, parsed_data = self._send_at_command_and_parse("GET_GPS_OUTPORT", expected_response="+QCFG")
        return parsed_data if success else "N/A"

    def get_usb_configuration(self):
        """Lê a configuração atual da interface USB (AT+QCFG="USBCFG")."""
        logger.info("GetUSBConfiguration: Lendo configuração USB.")
        success, parsed_data = self._send_at_command_and_parse("GET_USBCFG", expected_response="+QCFG")
        return parsed_data if success else "N/A"

    def enable_voice_over_usb(self, port):
        """Habilita a transferência de dados PCM via USB (Voice over USB)."""
        logger.info(f"EnableVoiceOverUSB: Habilitando Voice over USB na porta {port}.")
        return self._send_at_command_and_parse("ENABLE_VOICE_OVER_USB", port, expected_response="OK")

    def disable_voice_over_usb(self):
        """Desabilita a transferência de dados PCM via USB."""
        logger.info("DisableVoiceOverUSB: Desabilitando Voice over USB.")
        return self._send_at_command_and_parse("DISABLE_VOICE_OVER_USB", expected_response="OK")

    def get_voice_over_usb_status(self):
        """Obtém o status do Voice over USB."""
        logger.info("GetVoiceOverUSBStatus: Obtendo status Voice over USB.")
        success, parsed_data = self._send_at_command_and_parse("GET_VOICE_OVER_USB_STATUS", expected_response="+QPCMV")
        return parsed_data if success else "N/A"

    # --- Método para Sumário do Modem ---
    def get_modem_summary(self) -> str:
        """
        Coleta e retorna um sumário detalhado de várias informações do modem.
        """
        logger.info("Gerando sumário completo do modem...")
        summary_lines = []

        summary_lines.append("--- Sumário do Modem ---")

        # Informações Básicas
        product_info = self.get_product_info()
        summary_lines.append(f"Informações do Produto:\n{product_info}")
        
        imei = self.get_imei()
        summary_lines.append(f"IMEI: {imei}")

        imsi = self.get_imsi()
        summary_lines.append(f"IMSI: {imsi}")

        iccid = self.get_iccid()
        summary_lines.append(f"ICCID: {iccid}")

        sim_status = self.get_sim_status()
        summary_lines.append(f"Status do SIM: {sim_status}")

        battery_status = self.get_battery_status()
        summary_lines.append(f"Status da Bateria: {battery_status}")

        clock = self.get_clock()
        summary_lines.append(f"Hora/Data do Modem: {clock}")

        summary_lines.append("\n--- Status de Rede ---")
        signal_quality = self.get_signal_quality()
        summary_lines.append(f"Qualidade do Sinal: {signal_quality}")

        network_reg_status = self.get_network_registration_status()
        summary_lines.append(f"Status de Registro na Rede: {network_reg_status}")

        network_info = self.get_network_info()
        summary_lines.append(f"Informações da Rede: {network_info}")

        pdp_address = self.get_pdp_address(1) # Tenta CID 1, comum
        summary_lines.append(f"Endereço PDP (CID 1): {pdp_address}")

        scan_mode = self.get_network_scan_mode()
        summary_lines.append(f"Modo de Varredura de Rede: {scan_mode}")

        roaming_service = self.get_roaming_service()
        summary_lines.append(f"Serviço de Roaming: {roaming_service}")

        bands = self.get_bands()
        summary_lines.append(f"Configuração de Bandas: {bands}")

        summary_lines.append("\n--- Status GPS (se aplicável) ---")
        # Pode não ser aplicável a todos os modems/configs
        gps_location = self.get_gps_location()
        summary_lines.append(f"Localização GPS: {gps_location}")

        gps_outport = self.get_gps_outport()
        summary_lines.append(f"Porta de Saída NMEA GPS: {gps_outport}")

        summary_lines.append("\n--- Configurações de Áudio e USB ---")
        audio_mode = self.get_audio_mode()
        summary_lines.append(f"Modo de Áudio: {audio_mode}")

        mic_gains = self.get_mic_gains()
        summary_lines.append(f"Ganhos do Microfone: {mic_gains}")

        rx_gains = self.get_rx_gains()
        summary_lines.append(f"Ganhos de Recepção (Rx): {rx_gains}")

        usb_config = self.get_usb_configuration()
        summary_lines.append(f"Configuração USB: {usb_config}")

        voice_over_usb_status = self.get_voice_over_usb_status()
        summary_lines.append(f"Voice over USB (PCM) Status: {voice_over_usb_status}")


        final_summary = "\n".join(summary_lines)
        logger.info("Sumário do modem gerado com sucesso.")
        return final_summary

    # --- Métodos de Comandos Personalizados ---

    def send_custom_at_command(self, command, expected_response="OK", timeout=5):
        """
        Envia um comando AT personalizado.
        Retorna a resposta bruta do modem.
        """
        logger.info(f"SendCustomATCommand: Enviando comando personalizado: {command}")
        response = self.send_at_command(command, expected_response, timeout)
        return response
