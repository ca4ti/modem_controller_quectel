# src/gui/handlers/summary_handlers.py
import PySimpleGUI as sg
import threading
# Importações agora absolutas, assumindo que src está no sys.path
from src.gui.handlers.common_handlers import execute_modem_command, execute_modem_command_and_print_result
import src.gui.handlers.common_handlers as common_handlers # Importa o módulo para acessar as globais
from src.utils.threading_utils import run_in_thread, gui_update_event

def handle_generate_summary_event(window):
    """Handler para o botão 'Gerar Sumário do Modem'."""
    if common_handlers.modem_controller: # Acessa a global do módulo common_handlers
        window['-MODEM_SUMMARY_OUTPUT-'].update("Gerando sumário... Por favor, aguarde.")
        
        def generate_summary_thread_internal():
            try:
                # O método get_modem_summary no ModemController já envia os comandos com lock
                summary_text = common_handlers.modem_controller.get_modem_summary() # Usa a global correta
                gui_update_event(window, '-UPDATE_SUMMARY_OUTPUT-', summary_text) # Envia o resultado de volta para a GUI
            except Exception as e:
                error_msg = f"Erro ao gerar sumário: {e}"
                print(error_msg)
                gui_update_event(window, '-UPDATE_SUMMARY_OUTPUT-', error_msg)
        
        run_in_thread(generate_summary_thread_internal)
    else:
        print("Modem não conectado. Por favor, conecte-se primeiro.")

# A função update_summary_output não é um handler de evento PySimpleGUI diretamente,
# mas uma função auxiliar para ser chamada quando a thread retorna o resultado.
# Ela será importada em app_main.py e chamada quando '-UPDATE_SUMMARY_OUTPUT-' for disparado.
def update_summary_output(window, text):
    """Atualiza o campo de saída do sumário do modem na GUI."""
    window['-MODEM_SUMMARY_OUTPUT-'].update(text)
