# src/gui/urc_monitor.py
import threading
import time
import re
import serial # Manter import para serial.SerialException

from src.utils.threading_utils import gui_update_event # Importação AGORA absoluta, garantida.

class UrcMonitor:
    """
    Monitora e despacha Unsolicited Result Codes (URCs) recebidos do ModemController.
    Não lê diretamente da porta serial, mas processa dados que lhe são passados.
    """

    def __init__(self, window, serial_port_lock):
        """
        Inicializa o monitor de URCs.
        :param window: A janela PySimpleGUI para enviar eventos.
        :param serial_port_lock: Um threading.Lock (não usado para leitura direta aqui, mas mantido por compatibilidade/possíveis futuros usos).
        """
        self.window = window
        self.serial_port_lock = serial_port_lock # Manter referência ao lock
        self.is_monitoring = False
        self.modem_controller = None # Referência ao ModemController para registrar callback
        self.stop_event_for_future_use = threading.Event() # Manter para consistência futura, mas não usado para loop de leitura aqui
        
        print("UrcMonitor inicializado.")
    
    def start_monitoring(self, modem_controller_instance):
        """
        Inicia o monitoramento de URCs registrando este monitor como callback no ModemController.
        :param modem_controller_instance: A instância ativa de ModemController.
        """
        if self.is_monitoring:
            print("Monitoramento de URCs já está ativo.")
            return

        self.modem_controller = modem_controller_instance
        # O ModemController agora encaminhará os URCs para este método.
        self.modem_controller.set_urc_callback(self.process_urc_data_from_controller)
        self.is_monitoring = True
        print("Monitoramento de URCs iniciado (ModemController encaminha dados).")

    def stop_monitoring(self):
        """
        Para o monitoramento de URCs, desregistrando este monitor como callback.
        """
        if self.is_monitoring and self.modem_controller:
            print("Solicitando parada do monitoramento de URCs...")
            self.modem_controller.set_urc_callback(None) # Desregistra o callback
            self.modem_controller = None
            self.is_monitoring = False
            print("Monitoramento de URCs parado.")
        elif not self.is_monitoring:
            print("Monitoramento de URCs já está parado.")
        else: # is_monitoring is True but modem_controller is None - state inconsistency
            print("Estado inconsistente do URC Monitor. Forçando reset.")
            self.modem_controller = None
            self.is_monitoring = False

    def process_urc_data_from_controller(self, urc_name: str, payload: tuple):
        """
        Recebe e processa dados de URCs que são encaminhados pelo ModemController.
        Esta função é o callback do ModemController.
        """
        timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        urc_log_message = ""

        # --- Lógica de Pop-ups e Formatação de Log de URCs ---
        if urc_name == "RING":
            urc_log_message = f"[{timestamp}] Chamada Recebida: RING"
            sg.popup_timed(f"Chamada Recebida!", title="CHAMADA", keep_on_top=True, background_color='yellow', text_color='black')
        elif urc_name == "CMTI":
            mem, idx = payload
            urc_log_message = f"[{timestamp}] Novo SMS na Memória: '{mem}', Índice {idx}"
            sg.popup_timed(f"Novo SMS recebido!", title="NOVO SMS", keep_on_top=True, background_color='lightblue', text_color='black')
        elif urc_name == "CMT":
            # payload: (number, alpha, timestamp_str, message_content)
            number = payload[0] if len(payload) > 0 else 'N/A'
            timestamp_str = payload[2] if len(payload) > 2 else 'N/A'
            content = payload[3] if len(payload) > 3 else 'N/A'
            urc_log_message = f"[{timestamp}] SMS Direto de {number} ({timestamp_str}):\n{content.strip()}"
            sg.popup_scrolled(f"SMS de: {number}\nData/Hora: {timestamp_str}\n\n{content.strip()}", 
                              title=f"SMS de {number}", size=(50, 15), keep_on_top=True, background_color='lightgreen', text_color='black')
        elif urc_name == "QSIMSTAT":
            enable_stat, inserted_stat = payload
            sim_status_desc = {0: "Removido", 1: "Inserido", 2: "Desconhecido"}.get(int(inserted_stat), "Desconhecido")
            urc_log_message = f"[{timestamp}] Status do SIM: {sim_status_desc} (Relatório: {'Habilitado' if enable_stat == '1' else 'Desabilitado'})"
            sg.popup_timed(f"Status do SIM: {sim_status_desc}", title="STATUS SIM", keep_on_top=True, background_color='lightgray', text_color='black')
        elif urc_name == "CSQ":
            rssi, ber = payload
            urc_log_message = f"[{timestamp}] Qualidade do Sinal Alterada: RSSI={rssi}, BER={ber}"
            sg.popup_timed(f"Sinal Alterado: RSSI {rssi}, BER {ber}", title="QUALIDADE SINAL", keep_on_top=True, background_color='lightyellow', text_color='black')
        elif urc_name == "CREG" or urc_name == "CGREG" or urc_name == "CEREG":
            stat_code = int(payload[1]) # O status é sempre o segundo elemento
            stat_desc = {
                0: "Não registrado, ME não buscando", 1: "Registrado, rede de origem",
                2: "Não registrado, ME buscando", 3: "Registro negado",
                4: "Desconhecido", 5: "Registrado, roaming"
            }.get(stat_code, "Desconhecido")
            
            detail_msg = f"Rede {urc_name}: {stat_desc}"
            # Lógica para CREG/CGREG/CEREG estendido, se houver campos adicionais
            if len(payload) > 2: 
                lac_tac = payload[2] if len(payload) > 2 else 'N/A'
                ci = payload[3] if len(payload) > 3 else 'N/A'
                act_code = payload[4] if len(payload) > 4 else 'N/A'
                act_desc = {
                    "0": "GSM", "2": "UTRAN", "3": "GSM W/EGPRS", "4": "UTRAN W/HSDPA",
                    "5": "UTRAN W/HSUPA", "6": "UTRAN W/HSDPA and HSUPA", "7": "E-UTRAN"
                }.get(act_code, "N/A")
                detail_msg += f" (LAC/TAC: {lac_tac}, CI: {ci}, Tech: {act_desc})"
            
            urc_log_message = f"[{timestamp}] Registro Rede: {detail_msg}"
            sg.popup_timed(f"Registro de Rede: {detail_msg}", title="REGISTRO REDE", keep_on_top=True, background_color='lightcoral', text_color='white')
        else:
            urc_log_message = f"[{timestamp}] URC Desconhecido: {urc_name}, Payload: {payload}"

        # Adiciona a mensagem formatada ao Multiline de URCs na aba "Logs de URCs"
        # O evento é enviado para a thread principal da GUI
        gui_update_event(self.window, '-URC_LOG_OUTPUT_APPEND-', urc_log_message + '\n')
