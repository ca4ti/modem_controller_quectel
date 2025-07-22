# src/gui/handlers/common_handlers.py
import PySimpleGUI as sg
import threading
import time
import re

# Importações de módulos do projeto. TODAS AGORA ABSOLUTAS a partir de 'src'.
from src.modem.controller import ModemController
from src.utils.threading_utils import run_in_thread, _execute_command, _execute_command_print_result, gui_update_event
from src.utils.serial_ports import get_available_ports
from src.gui.urc_monitor import UrcMonitor

# --- Variáveis Globais de Gerenciamento de Conexão ---
# Estas variáveis atuam como o "estado centralizado" do modem para toda a aplicação.
modem_controller: ModemController = None
connected: bool = False
urc_monitor_instance: UrcMonitor = None
serial_port_lock = threading.Lock() # Lock para sincronizar acesso à porta serial


def _set_connection_state(new_state: bool, new_modem_controller=None, window=None):
    """
    Função auxiliar para centralizar a atualização do estado da conexão.
    Garanto que a variável global 'connected' e 'modem_controller' sejam atualizadas
    e que a GUI seja notificada.
    """
    global connected, modem_controller, urc_monitor_instance

    # Desconecta o modem_controller antigo antes de atribuir um novo ou None
    # Esta parte agora é crucial, pois pode haver uma instância antiga ainda pendurada.
    if modem_controller and modem_controller is not new_modem_controller:
        if modem_controller.serial_port and modem_controller.serial_port.is_open:
            print(f"Fechando conexão anterior na porta {modem_controller.port}...")
            modem_controller.disconnect_modem()
    
    connected = new_state
    modem_controller = new_modem_controller # Pode ser uma nova instância ou None

    if connected:
        print(f"Estado GLOBAL de conexão definido para: CONECTADO na porta {modem_controller.port}")
    else:
        print("Estado GLOBAL de conexão definido para: DESCONECTADO")

    # Notifica a thread principal da GUI para atualizar os botões
    if window:
        gui_update_event(window, '-UPDATE_BUTTON_STATES-', connected)

    # Inicia/Para UrcMonitor com base no novo estado
    if connected and modem_controller:
        if not urc_monitor_instance:
            urc_monitor_instance = UrcMonitor(window, serial_port_lock)
        urc_monitor_instance.start_monitoring(modem_controller)
    elif not connected and urc_monitor_instance:
        urc_monitor_instance.stop_monitoring()
        urc_monitor_instance = None


def handle_connect_event(window, values):
    # Não precisa de 'global' aqui, pois _set_connection_state é quem modifica as globais.
    global connected # Acessa a variável global 'connected' para verificar o estado
    if connected:
        print("Modem já está conectado. Desconecte-o primeiro se quiser mudar de porta.")
        return

    port = values['-PORT-']
    if not port:
        print("Por favor, selecione uma porta serial.")
        return

    try:
        baudrate = int(values['-BAUDRATE-'])
    except ValueError:
        print("Erro: Baudrate inválido. Por favor, insira um número inteiro.")
        return

    def connect_and_test_thread_func():
        temp_connected_state = False
        temp_modem_ctrl_instance = None
        try:
            with serial_port_lock:
                # Cria a instância do ModemController
                temp_modem_ctrl_instance = ModemController(port, baudrate)
                # AGORA CHAMA explicitamente connect_modem()
                if temp_modem_ctrl_instance.connect_modem(): # AQUI ESTÁ A MUDANÇA PRINCIPAL!
                    temp_connected_state = True
                    print(f"Modem conectado e identificado (Quectel) com sucesso na porta {port} na thread de conexão.")
                else:
                    print(f"Falha ao conectar/identificar modem na porta {port}. Desconectando temp.")
                    temp_modem_ctrl_instance.disconnect_modem()
                    temp_modem_ctrl_instance = None # Garante que instância inválida não seja passada.
        except Exception as e:
            print(f"Erro inesperado na thread de conexão (durante ModemController init/test): {e}")
            temp_modem_ctrl_instance = None # Garante que instância inválida não seja passada.
        finally:
            _set_connection_state(temp_connected_state, temp_modem_ctrl_instance, window)

    run_in_thread(connect_and_test_thread_func)


def handle_disconnect_event(window):
    # Não precisa de 'global' aqui, pois _set_connection_state é quem modifica as globais.
    # Apenas solicita a mudança de estado global.
    _set_connection_state(False, None, window)


def handle_refresh_ports_event(window):
    global connected, modem_controller # Acessa as globais para verificar o estado
    print("Atualizando lista de portas seriais...")
    new_ports = get_available_ports()
    gui_update_event(window, '-PORT_UPDATE_EVENT-', new_ports)
    if not new_ports:
        print("Nenhuma porta serial encontrada após a atualização.")
    else:
        print(f"Portas atualizadas: {new_ports}")
        # Verifica se a porta atual ainda está na lista.
        # Acessa as globais diretamente deste módulo.
        if connected and modem_controller and (modem_controller.port not in new_ports):
            print(f"AVISO: A porta atual ({modem_controller.port}) não está mais na lista. Considere reconectar.")


def handle_auto_discover_event(window):
    global connected, modem_controller # Acessa as globais para verificar/mudar o estado

    if connected:
        print("Modem já conectado. Desconectando antes do Auto-Discovery...")
        handle_disconnect_event(window)
        time.sleep(0.1) # Pequena pausa para dar tempo ao _set_connection_state() processar.
        if connected: # Reverifica para ter certeza que desconectou.
            print("Erro ao forçar desconexão antes do auto-discovery. Abortando auto-discovery.")
            return

    def auto_discover_modem_thread_func():
        temp_found_port = None
        temp_modem_ctrl_instance = None
        temp_connected_state = False

        available_ports_for_discovery = get_available_ports()
        gui_update_event(window, '-PORT_UPDATE_EVENT-', available_ports_for_discovery)

        baudrate = 115200

        print("Iniciando Auto-Discovery... Tentando em todas as portas disponíveis.")
        
        for port_to_test in available_ports_for_discovery:
            if "ttyS" in port_to_test:
                continue

            print(f"Tentando porta: {port_to_test}...")
            try:
                # Garante que qualquer instância temporária anterior seja desconectada
                if temp_modem_ctrl_instance:
                    temp_modem_ctrl_instance.disconnect_modem()
                    temp_modem_ctrl_instance = None

                with serial_port_lock: # Garante acesso exclusivo à porta durante o teste
                    temp_modem_ctrl_instance = ModemController(port_to_test, baudrate, timeout=0.5)
                    # AGORA CHAMA explicitamente connect_modem()
                    if temp_modem_ctrl_instance.connect_modem(): # AQUI ESTÁ A MUDANÇA PRINCIPAL!
                        print(f"Modem Quectel encontrado e conectado automaticamente na porta: {port_to_test} na thread de auto-discovery.")
                        temp_found_port = port_to_test
                        temp_connected_state = True
                        break # Encontrou, pode sair do loop
                    else:
                        print(f"Porta {port_to_test} não é um modem Quectel ou falhou ao conectar/identificar. Desconectando temp.")
                        temp_modem_ctrl_instance.disconnect_modem()
                        temp_modem_ctrl_instance = None
            except Exception as e:
                print(f"Erro durante o teste da porta {port_to_test}: {e}")
                temp_modem_ctrl_instance = None # Limpa em caso de erro


        if not temp_found_port:
            print("Auto-Discovery concluído. Nenhum modem Quectel encontrado.")
            _set_connection_state(False, None, window) # Garante que o estado final seja desconectado
        else:
            gui_update_event(window, '-PORT_SELECTION_UPDATE-', temp_found_port) # Atualiza o combobox
            _set_connection_state(temp_connected_state, temp_modem_ctrl_instance, window) # Atualiza o estado global


    run_in_thread(auto_discover_modem_thread_func)


# Estas funções AGORA acessam as variáveis globais **desse próprio módulo** (common_handlers)
# onde modem_controller e connected são de fato globais e atualizadas por _set_connection_state.
def execute_modem_command(func, *args, **kwargs):
    """
    Executa uma função (comando do modem) dentro de uma thread, adquirindo o lock.
    Verifica o estado de conexão ANTES de tentar executar.
    """
    # CORRIGIDO: Remover 'common_handlers.' ao acessar as variáveis globais 'modem_controller' e 'connected'
    # dentro deste próprio módulo.
    global modem_controller, connected # Declarar global para acessar as variáveis deste módulo
    if modem_controller and connected: 
        run_in_thread(lambda: _safe_execute_command(modem_controller, serial_port_lock, func, *args, **kwargs))
    else:
        print("Modem não conectado. Por favor, conecte-se primeiro.")


def execute_modem_command_and_print_result(func, *args, **kwargs):
    """
    Executa uma função (comando do modem que retorna um resultado para ser impresso)
    dentro de uma thread, adquirindo o lock.
    Verifica o estado de conexão ANTES de tentar executar.
    """
    # CORRIGIDO: Remover 'common_handlers.' ao acessar as variáveis globais 'modem_controller' e 'connected'
    # dentro deste próprio módulo.
    global modem_controller, connected # Declarar global para acessar as variáveis deste módulo
    if modem_controller and connected: 
        run_in_thread(lambda: _safe_execute_command_print_result(modem_controller, serial_port_lock, func, *args, **kwargs))
    else:
        print("Modem não conectado. Por favor, conecte-se primeiro.")


def _safe_execute_command(modem_ctrl, lock, func, *args, **kwargs):
    """Função interna para executar um comando do modem de forma segura com lock."""
    with lock:
        _execute_command(func, *args, **kwargs)


def _safe_execute_command_print_result(modem_ctrl, lock, func, *args, **kwargs):
    """Função interna para executar um comando do modem que imprime resultado de forma segura com lock."""
    with lock:
        _execute_command_print_result(func, *args, **kwargs)


def handle_clear_urc_log_event(window):
    """
    Handler para o botão 'Limpar Log URC'. Limpa o conteúdo da área de log de URCs.
    """
    window['-URC_LOG_OUTPUT-'].update('')
    print("Log de URCs limpo na GUI.")
