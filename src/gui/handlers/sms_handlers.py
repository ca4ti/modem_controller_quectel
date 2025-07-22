# src/gui/handlers/sms_handlers.py
import PySimpleGUI as sg
from src.gui.handlers.common_handlers import execute_modem_command, execute_modem_command_and_print_result
import src.gui.handlers.common_handlers as common_handlers # Importa o módulo para acessar as globais
import threading # Necessário para rodar em thread
import datetime # Para timestamps
import re # Para parsing de mensagens

def handle_send_sms_event(values):
    """Handler para o botão 'Enviar SMS' (AT+CMGS)."""
    number = values['-SMS_NUMBER-'].strip()
    message = values['-SMS_MESSAGE-'].strip()
    if number and message:
        execute_modem_command(common_handlers.modem_controller.send_sms, number, message)
    else:
        print("Por favor, preencha o número e a mensagem do SMS.")

def handle_read_all_sms_event():
    """Handler para o botão 'Ler Todas SMS' (AT+CMGL="ALL")."""
    execute_modem_command_and_print_result(common_handlers.modem_controller.read_all_sms)

def handle_read_sms_by_index_event(values):
    """Handler para o botão 'Ler SMS por Índice' (AT+CMGR)."""
    try:
        index = int(values['-SMS_INDEX-'])
        execute_modem_command_and_print_result(common_handlers.modem_controller.read_sms_at_index, index)
    except ValueError:
        print("Erro: Índice SMS deve ser um número inteiro.")

def handle_delete_all_sms_event():
    """Handler para o botão 'Apagar Todas SMS' (AT+CMGD=1,4)."""
    execute_modem_command(common_handlers.modem_controller.delete_all_sms)

def handle_delete_sms_by_index_event(values):
    """Handler para o botão 'Apagar SMS por Índice' (AT+CMGD)."""
    try:
        index = int(values['-SMS_INDEX-'])
        execute_modem_command(common_handlers.modem_controller.delete_sms_by_index, index)
    except ValueError:
        print("Erro: Índice SMS deve ser um número inteiro.")

# --- NOVA FUNCIONALIDADE: Gerenciamento Avançado de SMS ---

def handle_refresh_sms_inbox_event(window):
    """
    Handler para o botão 'Atualizar Inbox'.
    Lê todas as mensagens SMS e exibe na área de inbox.
    """
    if not common_handlers.modem_controller or not common_handlers.connected:
        print("Modem não conectado. Por favor, conecte-se primeiro para atualizar a inbox.")
        return

    window['-SMS_INBOX_OUTPUT-'].update("Lendo mensagens da caixa de entrada... Por favor, aguarde.")

    def read_inbox_thread():
        # Chama o método do controlador que lê e parseia todos os SMS
        success, messages = common_handlers.modem_controller.read_all_sms_messages()
        
        inbox_display_text = ""
        if success and messages:
            # Filtrar para exibir apenas mensagens recebidas (REC UNREAD, REC READ)
            received_messages = [msg for msg in messages if msg['status'] in ["REC UNREAD", "REC READ"]]
            if received_messages:
                # Exibe as mensagens mais recentes primeiro
                received_messages.sort(key=lambda x: x['timestamp'], reverse=True) 
                for msg in received_messages:
                    inbox_display_text += f"--- Mensagem {msg['index']} ({msg['status']}) ---\n"
                    inbox_display_text += f"De: {msg['number']}\n"
                    inbox_display_text += f"Data: {msg['timestamp']}\n"
                    inbox_display_text += f"Conteúdo: {msg['message']}\n\n"
            else:
                inbox_display_text = "Nenhuma mensagem na caixa de entrada."
        elif success and not messages:
            inbox_display_text = "Nenhuma mensagem na caixa de entrada."
        else:
            inbox_display_text = f"Falha ao ler caixa de entrada: {messages}" # messages aqui conteria a mensagem de erro

        # Atualiza a GUI na thread principal
        window.write_event_value('-UPDATE_SMS_INBOX_OUTPUT-', inbox_display_text)

    # Executa a leitura em uma thread separada para não travar a GUI
    threading.Thread(target=read_inbox_thread, daemon=True).start()

def handle_refresh_sms_outbox_event(window):
    """
    Handler para o botão 'Atualizar Outbox'.
    Lê todas as mensagens SMS e exibe na área de outbox.
    """
    if not common_handlers.modem_controller or not common_handlers.connected:
        print("Modem não conectado. Por favor, conecte-se primeiro para atualizar a outbox.")
        return

    window['-SMS_OUTBOX_OUTPUT-'].update("Lendo mensagens da caixa de saída... Por favor, aguarde.")

    def read_outbox_thread():
        # Chama o método do controlador que lê e parseia todos os SMS
        success, messages = common_handlers.modem_controller.read_all_sms_messages() # Reutiliza a função de leitura geral
        
        outbox_display_text = ""
        if success and messages:
            # Filtrar para exibir apenas mensagens enviadas (STO SENT)
            sent_messages = [msg for msg in messages if msg['status'] == "STO SENT"]
            if sent_messages:
                # Exibe as mensagens mais recentes primeiro
                sent_messages.sort(key=lambda x: x['timestamp'], reverse=True)
                for msg in sent_messages:
                    outbox_display_text += f"--- Mensagem {msg['index']} ({msg['status']}) ---\n"
                    outbox_display_text += f"Para: {msg['number']}\n" # No caso de enviados, o 'number' é o destinatário
                    outbox_display_text += f"Data: {msg['timestamp']}\n"
                    outbox_display_text += f"Conteúdo: {msg['message']}\n\n"
            else:
                outbox_display_text = "Nenhuma mensagem enviada."
        elif success and not messages:
            outbox_display_text = "Nenhuma mensagem enviada."
        else:
            outbox_display_text = f"Falha ao leer caixa de saída: {messages}" # messages aqui conteria a mensagem de erro

        # Atualiza a GUI na thread principal
        window.write_event_value('-UPDATE_SMS_OUTBOX_OUTPUT-', outbox_display_text)

    # Executa a leitura em uma thread separada para não travar a GUI
    threading.Thread(target=read_outbox_thread, daemon=True).start()


def handle_delete_all_sms_advanced_event(window):
    """
    Handler para o botão 'Apagar Todas as Mensagens' na aba avançada.
    """
    if not common_handlers.modem_controller or not common_handlers.connected:
        print("Modem não conectado. Por favor, conecte-se primeiro para apagar mensagens.")
        return
    
    # Confirmação antes de apagar TUDO
    confirm = sg.popup_ok_cancel("Tem certeza que deseja APAGAR TODAS as mensagens SMS do modem?", title="Confirmar Exclusão")
    if confirm == 'OK':
        success, response = common_handlers.modem_controller.delete_all_sms()
        if success:
            sg.popup_timed("Todas as mensagens SMS foram apagadas!", title="Sucesso")
            # Atualiza ambas as caixas após a exclusão
            window.write_event_value('-UPDATE_SMS_INBOX_OUTPUT-', '') # Limpa visualmente
            window.write_event_value('-UPDATE_SMS_OUTBOX_OUTPUT-', '') # Limpa visualmente
        else:
            sg.popup_error(f"Falha ao apagar mensagens SMS: {response}", title="Erro")
    else:
        print("Exclusão de mensagens SMS cancelada.")
